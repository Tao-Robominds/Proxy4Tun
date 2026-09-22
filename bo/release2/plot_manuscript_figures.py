#!/usr/bin/env python3
"""Manuscript figures for paper/Proxy4Tun/main.tex.

Proxy calibration/holdout still use frozen data/release2/.
Self-refinement figures use the merged 27-case panel
(data/release2.1/analysis/), which combines Release 2 (15) and
Release 2.1 (12). Never writes into data/release2/.
"""

from __future__ import annotations

import csv
import json
import statistics as st
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D
from scipy import stats

REPO = Path(__file__).resolve().parents[2]
R2 = REPO / "data" / "release2"
R21 = REPO / "data" / "release2.1"
OUT = REPO / "paper" / "Proxy4Tun" / "figs"
R2_15 = {
    "1-1",
    "1-3",
    "1-5",
    "3-3",
    "3-4",
    "3-6",
    "3-7",
    "3-8",
    "3-9",
    "3-10",
    "4-1",
    "4-2",
    "4-3",
    "4-4",
    "5-5",
}

FAMILY_COLORS = {"staggered": "#2C73D2", "continuous": "#44BBA4", "complex": "#E67E22"}
FAMILY_ORDER = ("staggered", "continuous", "complex")
ARM_ORDER = ("fable", "gemini38", "gpt56_medium", "random")
ARM_LABEL = {
    "fable": "Fable",
    "gemini38": "Gemini 3.8",
    "gpt56_medium": "GPT-5.6 med.",
    "random": "Random",
}
ARM_COLORS = {
    "fable": "#1F77B4",
    "gemini38": "#11A579",
    "gpt56_medium": "#7F3C8D",
    "random": "#8C8C8C",
}


def _style() -> None:
    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["DejaVu Sans", "sans-serif"],
            "font.size": 11,
            "axes.labelsize": 12,
            "axes.titlesize": 12,
            "legend.fontsize": 8.5,
            "xtick.labelsize": 10,
            "ytick.labelsize": 10,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "pdf.fonttype": 42,
        }
    )


def _load_pkg() -> dict:
    return json.loads((R2 / "proxy" / "four_feature.json").read_text())


def _frozen_score(rows: list[dict], pkg: dict) -> np.ndarray:
    feats = pkg["features"]
    mu = np.asarray(pkg["mu"], dtype=float)
    sigma = np.asarray(pkg["sigma"], dtype=float)
    w = np.asarray(pkg["w"], dtype=float)
    X = np.array([[float(r[f]) for f in feats] for r in rows], dtype=float)
    return np.clip(pkg["intercept"] + ((X - mu) / sigma) @ w, 0.0, 1.0)


def fig_ablation() -> None:
    pkg = _load_pkg()
    train = list(csv.DictReader((R2 / "calibration" / "records" / "training_table.csv").open()))
    pairs = list(csv.DictReader((R2 / "degradation" / "records" / "pairs.csv").open()))
    for r in train:
        r["family"] = r["family"]
        r["mIoU"] = float(r["gt_miou"])
    pred_tr = _frozen_score(train, pkg)
    y_tr = np.array([r["mIoU"] for r in train])

    fig, (ax_a, ax_b) = plt.subplots(1, 2, figsize=(11.0, 4.6))

    for fam in FAMILY_ORDER:
        idx = [i for i, r in enumerate(train) if r["family"] == fam]
        ax_a.scatter(
            y_tr[idx],
            pred_tr[idx],
            s=26,
            c=FAMILY_COLORS[fam],
            alpha=0.9,
            edgecolors="white",
            linewidths=0.3,
            label=fam.capitalize(),
            zorder=3,
        )
    ax_a.plot([0, 1], [0, 1], color="0.75", lw=0.8, zorder=1)
    mae = float(np.mean(np.abs(pred_tr - y_tr)))
    rho = float(stats.spearmanr(pred_tr, y_tr).correlation)
    ax_a.set_xlim(-0.02, 1.02)
    ax_a.set_ylim(-0.02, 1.02)
    ax_a.set_xlabel("GT mIoU")
    ax_a.set_ylabel(r"Proxy $\hat{y}$")
    ax_a.set_title("Calibration: 120 trials, 3 development subsets")
    ax_a.text(
        0.02,
        0.97,
        f"Four-feature model\nMAE = {mae:.3f}\nSpearman = {rho:.3f}",
        transform=ax_a.transAxes,
        va="top",
        fontsize=9,
    )
    ax_a.legend(loc="lower right", frameon=False, title="Family")

    # Holdout: reference vs degraded paired ranking
    ax_b.axhspan(0.5, 0.7, color="#F1C40F", alpha=0.15, zorder=0)
    ax_b.axhline(0.5, color="#C0392B", ls="--", lw=1.0, zorder=1)
    ax_b.axhline(0.7, color="#7F8C8D", ls=":", lw=1.0, zorder=1)
    by_sub: dict[str, dict] = {}
    for r in pairs:
        by_sub.setdefault(r["subset"], {})[r["arm"]] = r
    for subset, arms in by_sub.items():
        fam = arms["reference"]["family"]
        xr = float(arms["reference"]["gt_miou"])
        yr = float(arms["reference"]["score"])
        xd = float(arms["degraded"]["gt_miou"])
        yd = float(arms["degraded"]["score"])
        ax_b.plot([xr, xd], [yr, yd], color=FAMILY_COLORS[fam], lw=0.6, alpha=0.35, zorder=2)
        ax_b.scatter(xr, yr, s=34, c=FAMILY_COLORS[fam], marker="o", edgecolors="white", linewidths=0.3, zorder=3)
        ax_b.scatter(xd, yd, s=34, c=FAMILY_COLORS[fam], marker="x", linewidths=1.2, zorder=3)
    y_all = np.array([float(r["gt_miou"]) for r in pairs])
    p_all = np.array([float(r["score"]) for r in pairs])
    mae_h = float(np.mean(np.abs(p_all - y_all)))
    rho_h = float(stats.spearmanr(p_all, y_all).correlation)
    ax_b.plot([0, 1], [0, 1], color="0.75", lw=0.8, zorder=1)
    ax_b.set_xlim(-0.02, 1.02)
    ax_b.set_ylim(-0.02, 1.02)
    ax_b.set_xlabel("GT mIoU")
    ax_b.set_ylabel(r"Proxy $\hat{y}$")
    ax_b.set_title("Frozen proxy on 54 held-out runs (27 pairs)")
    ax_b.text(
        0.02,
        0.97,
        f"MAE = {mae_h:.3f}\nSpearman = {rho_h:.3f}\n27/27 pairs ranked",
        transform=ax_b.transAxes,
        va="top",
        fontsize=9,
    )
    ax_b.text(
        0.28,
        0.60,
        "proxy refine band\n$[0.5,0.7]$",
        transform=ax_b.transData,
        ha="left",
        va="center",
        fontsize=8.5,
        color="#7D6608",
    )
    fam_handles = [
        Line2D([0], [0], marker="o", ls="", color=FAMILY_COLORS[f], label=f.capitalize()) for f in FAMILY_ORDER
    ]
    kind_handles = [
        Line2D([0], [0], marker="o", ls="", color="0.3", label="Reference"),
        Line2D([0], [0], marker="x", ls="", color="0.3", label="Degraded"),
    ]
    leg = ax_b.legend(handles=fam_handles, loc="lower right", frameon=False, title="Family")
    ax_b.add_artist(leg)
    ax_b.legend(handles=kind_handles, loc="center right", bbox_to_anchor=(1.0, 0.33), frameon=False)

    for ax, tag in ((ax_a, "(a)"), (ax_b, "(b)")):
        ax.text(0.5, -0.20, tag, transform=ax.transAxes, ha="center", fontsize=11)
    fig.tight_layout(w_pad=2.5)
    fig.savefig(OUT / "ablation_results.pdf", bbox_inches="tight")
    plt.close(fig)


def _arm_means() -> dict:
    nums = json.loads((R21 / "analysis" / "numbers.json").read_text())
    out = {"start": nums["merged27_fable"]["mean_start"]}
    for arm in ARM_ORDER:
        out[arm] = nums[f"merged27_{arm}"]
    out["policies"] = _merged_policies()
    return out


def _sel_path(arm: str, subset: str) -> Path:
    root = R2 if subset in R2_15 else R21
    return root / "refinement" / "records" / "selections" / arm / f"{subset}.json"


def _merged_policies() -> dict[str, dict[str, float]]:
    panel = list(csv.DictReader((R21 / "analysis" / "panel_merged_27.csv").open()))
    subsets = sorted({r["subset"] for r in panel})
    policies: dict[str, dict[str, float]] = {}
    for arm in ARM_ORDER:
        start, round1, monotone, oracle = [], [], [], []
        for subset in subsets:
            sel = json.loads(_sel_path(arm, subset).read_text())
            cands = [c for c in sel["candidates"] if c.get("valid")]
            start.append(float(cands[0]["gt_miou"]))
            r1 = [c for c in cands if c["name"] == "round1"]
            round1.append(float(r1[0]["gt_miou"]) if r1 else float(cands[0]["gt_miou"]))
            monotone.append(float(sel["selected"]["gt_miou"]))
            oracle.append(max(float(c["gt_miou"]) for c in cands))
        policies[arm] = {
            "start": float(np.mean(start)),
            "round1": float(np.mean(round1)),
            "monotone": float(np.mean(monotone)),
            "oracle": float(np.mean(oracle)),
        }
    return policies


def _proposal_deltas() -> dict[str, list[float]]:
    starts: dict[str, float] = {}
    with (R21 / "analysis" / "panel_merged_27.csv").open() as f:
        for r in csv.DictReader(f):
            starts[r["subset"]] = float(r["start_miou"])
    out: dict[str, list[float]] = {a: [] for a in ARM_ORDER}
    for path in (
        R2 / "refinement" / "records" / "candidates.csv",
        R21 / "refinement" / "records" / "candidates.csv",
    ):
        with path.open() as f:
            for r in csv.DictReader(f):
                if r["valid"] != "True" or r["subset"] not in starts:
                    continue
                out[r["arm"]].append(float(r["gt_miou"]) - starts[r["subset"]])
    return out


def fig_refinement() -> None:
    data = _arm_means()
    start = float(data["start"])
    deltas = _proposal_deltas()

    fig, (ax_a, ax_b, ax_c) = plt.subplots(
        1, 3, figsize=(14.5, 4.5), gridspec_kw={"width_ratios": [1.05, 1.25, 1.15]}
    )

    # (a) high-bar selected means
    labels = ["Reference"] + [ARM_LABEL[a] for a in ARM_ORDER]
    means = [start] + [float(data[a]["mean_selected"]) for a in ARM_ORDER]
    colors = ["#BDC3C7"] + [ARM_COLORS[a] for a in ARM_ORDER]
    xs = np.arange(len(labels))
    ax_a.bar(xs, means, color=colors, width=0.62, zorder=2)
    ax_a.axhline(start, color="0.35", ls=":", lw=1.0, zorder=1)
    for i, a in enumerate(ARM_ORDER, start=1):
        d = float(data[a]["mean_delta"])
        lo, hi = data[a]["bootstrap"]["ci95"]
        ax_a.errorbar(
            i,
            means[i],
            yerr=[[max(0.0, d - lo)], [max(0.0, hi - d)]],
            fmt="none",
            ecolor="0.2",
            elinewidth=1.0,
            capsize=3,
            zorder=3,
        )
        ax_a.text(i, means[i] + 0.010, f"{means[i]:.3f}", ha="center", fontsize=8.5)
    ax_a.text(0, means[0] + 0.010, f"{means[0]:.3f}", ha="center", fontsize=8.5)
    ax_a.set_xticks(xs)
    ax_a.set_xticklabels(labels, rotation=18, ha="right")
    ax_a.set_ylim(0.70, 0.82)
    ax_a.set_ylabel("Mean GT mIoU (27 references)")
    ax_a.set_title("High-bar reference vs selected outputs")

    # (b) selection policies
    policies = [("round1", "Round 1"), ("monotone", "Proxy selector"), ("oracle", "GT oracle")]
    pcolors = ["#AEB6BF", "#2C3E50", "#F5B041"]
    w = 0.22
    for j, (key, lab) in enumerate(policies):
        vals = [float(data["policies"][a][key]) for a in ARM_ORDER]
        ax_b.bar(
            np.arange(len(ARM_ORDER)) + (j - 1) * w,
            vals,
            width=w,
            color=pcolors[j],
            label=lab,
            zorder=2,
            edgecolor="white",
            linewidth=0.4,
        )
    ax_b.axhline(start, color="#C0392B", ls="--", lw=1.0, zorder=3)
    ax_b.text(3.35, start + 0.004, f"reference\n{start:.3f}", color="#C0392B", fontsize=8.5, ha="left", va="bottom")
    ax_b.set_xticks(np.arange(len(ARM_ORDER)))
    ax_b.set_xticklabels([ARM_LABEL[a] for a in ARM_ORDER], rotation=18, ha="right")
    ax_b.set_ylim(0.45, 0.85)
    ax_b.set_ylabel("Mean GT mIoU")
    ax_b.set_title("Same candidates, different selection")
    ax_b.legend(loc="lower left", frameon=False)

    # (c) proposal safety: fraction of large drops
    drop = [sum(d < -0.05 for d in deltas[a]) / len(deltas[a]) for a in ARM_ORDER]
    stds = [st.pstdev(deltas[a]) for a in ARM_ORDER]
    nprop = len(deltas["fable"])
    ax_c.bar(np.arange(len(ARM_ORDER)), drop, color=[ARM_COLORS[a] for a in ARM_ORDER], width=0.62, zorder=2)
    for i, (p, s) in enumerate(zip(drop, stds)):
        ax_c.text(i, p + 0.02, f"{100 * p:.0f}%\n(σ={s:.2f})", ha="center", va="bottom", fontsize=8)
    ax_c.set_xticks(np.arange(len(ARM_ORDER)))
    ax_c.set_xticklabels([ARM_LABEL[a] for a in ARM_ORDER], rotation=18, ha="right")
    ax_c.set_ylim(0.0, 0.95)
    ax_c.set_ylabel(r"Share of proposals with $\Delta$mIoU $<-0.05$")
    ax_c.set_title(f"Proposal safety (~{nprop} proposals / arm)")

    for ax, tag in ((ax_a, "(a)"), (ax_b, "(b)"), (ax_c, "(c)")):
        ax.text(0.5, -0.24, tag, transform=ax.transAxes, ha="center", fontsize=11)
    fig.tight_layout(w_pad=2.0)
    fig.savefig(OUT / "refinement_results.pdf", bbox_inches="tight")
    plt.close(fig)


def fig_verification() -> None:
    """Compact protocol schematic: reference start → 3 rounds → proxy select."""
    fig, ax = plt.subplots(figsize=(10.5, 3.2))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 3)
    ax.axis("off")
    boxes = [
        (0.4, 1.0, 2.0, 1.2, "Family-specific\nreference start\n(all 27 holdouts)"),
        (3.0, 1.0, 2.2, 1.2, "Three proposal\nrounds\n(LLM or random)"),
        (5.8, 1.0, 2.0, 1.2, "Frozen four-feature\nproxy scores\neach candidate"),
        (8.3, 1.0, 1.5, 1.2, "Retain max\nproxy\n(+0.01 tie)"),
    ]
    for x, y, w, h, text in boxes:
        ax.add_patch(
            plt.Rectangle((x, y), w, h, fill=True, facecolor="#F7F9FC", edgecolor="#2C3E50", linewidth=1.2)
        )
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=9)
    for x0, x1 in ((2.4, 3.0), (5.2, 5.8), (7.8, 8.3)):
        ax.annotate("", xy=(x1, 1.6), xytext=(x0, 1.6), arrowprops=dict(arrowstyle="->", color="#2C3E50", lw=1.4))
    ax.set_title("Proxy-guided self-refinement against a high reference bar", fontsize=12, pad=8)
    fig.tight_layout()
    fig.savefig(OUT / "verification.pdf", bbox_inches="tight")
    plt.close(fig)


def fig_rotation_limit() -> None:
    """Bar chart of residual swap fractions + 1-5 score/mIoU contrast."""
    nums = json.loads((R2 / "analysis" / "numbers.json").read_text())
    gpt = json.loads((R2 / "analysis" / "gpt56_medium_rerun" / "numbers.json").read_text())["gpt56_medium"]
    start_swap = nums["errors_fable"]["start_fractions"]["swap"]
    sel = {
        "Reference": start_swap,
        "Fable": nums["errors_fable"]["selected_fractions"]["swap"],
        "Gemini 3.8": nums["errors_gemini38"]["selected_fractions"]["swap"],
        "GPT-5.6 med.": gpt["point_error"]["selected"]["swap"],
        "Random": nums["errors_random"]["selected_fractions"]["swap"],
    }

    fig, (ax_a, ax_b) = plt.subplots(1, 2, figsize=(11.0, 4.2))
    names = list(sel.keys())
    vals = list(sel.values())
    colors = ["#BDC3C7", ARM_COLORS["fable"], ARM_COLORS["gemini38"], ARM_COLORS["gpt56_medium"], ARM_COLORS["random"]]
    ax_a.bar(np.arange(len(names)), vals, color=colors, width=0.65)
    ax_a.set_xticks(np.arange(len(names)))
    ax_a.set_xticklabels(names, rotation=18, ha="right")
    ax_a.set_ylabel("Class-swap fraction")
    ax_a.set_title("Residual label-swap error (illustrative mid-band panel)")
    ax_a.set_ylim(0.0, 0.08)
    for i, v in enumerate(vals):
        ax_a.text(i, v + 0.002, f"{v:.3f}", ha="center", fontsize=8.5)

    # 1-5 diagnostic: GT mIoU vs proxy for start and LLM selected
    cases = [
        ("Start", 0.676, 0.641, 24.2),
        ("Fable sel.", 0.884, 0.673, 14.1),
        ("Gemini sel.", 0.888, 0.676, 13.8),
    ]
    xs = np.arange(len(cases))
    w = 0.28
    ax_b.bar(xs - w / 2, [c[1] for c in cases], width=w, color="#2C73D2", label="GT mIoU")
    ax_b.bar(xs + w / 2, [c[2] for c in cases], width=w, color="#E67E22", label=r"Proxy $\hat{y}$")
    for i, c in enumerate(cases):
        ax_b.text(i, max(c[1], c[2]) + 0.03, f"phase {c[3]:.1f}°", ha="center", fontsize=8)
    ax_b.set_xticks(xs)
    ax_b.set_xticklabels([c[0] for c in cases])
    ax_b.set_ylim(0.5, 1.05)
    ax_b.set_ylabel("Score")
    ax_b.set_title("Case 1-5: large mIoU change, modest proxy change")
    ax_b.legend(frameon=False, loc="upper left")

    for ax, tag in ((ax_a, "(a)"), (ax_b, "(b)")):
        ax.text(0.5, -0.22, tag, transform=ax.transAxes, ha="center", fontsize=11)
    fig.tight_layout(w_pad=2.4)
    fig.savefig(OUT / "error_rotation.pdf", bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    _style()
    OUT.mkdir(parents=True, exist_ok=True)
    fig_ablation()
    fig_refinement()
    fig_verification()
    fig_rotation_limit()
    print(f"wrote {OUT / 'ablation_results.pdf'}")
    print(f"wrote {OUT / 'refinement_results.pdf'}")
    print(f"wrote {OUT / 'verification.pdf'}")
    print(f"wrote {OUT / 'error_rotation.pdf'}")


if __name__ == "__main__":
    main()
