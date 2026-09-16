#!/usr/bin/env python3
"""Result figures for paper/revision/main_claude.tex.

Reads the frozen sc-general tables (four-feature proxy, 54-run stress test,
22-case four-arm refinement panel) and writes two vector PDFs:

* figs/ablation_results.pdf   (a) calibration scatter, (b) holdout scatter
* figs/refinement_results.pdf (a) selected mIoU by arm, (b) selector policies,
                              (c) per-case gain vs starting GT mIoU

Read-only with respect to data/; writes only under paper/revision/figs/.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from scipy import stats
from sklearn.linear_model import RidgeCV
from sklearn.preprocessing import StandardScaler

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

STAGE2 = REPO / "data" / "sc-general" / "stage2"
TRAIN = STAGE2 / "training_table.csv"
HOLDOUT = STAGE2 / "holdout_scores.csv"
MODELS = REPO / "bo" / "sc_general" / "models.json"
RANDOM_EXPORT = REPO / "exports" / "sc-general-random-evaluation"
PANEL = RANDOM_EXPORT / "panel_all_arms.csv"
POLICIES = RANDOM_EXPORT / "selector_policies.csv"
BOOT = RANDOM_EXPORT / "cluster_bootstrap.json"
OUT = REPO / "paper" / "revision" / "figs"

FAMILY_COLORS = {"staggered": "#2C73D2", "continuous": "#44BBA4", "complex": "#E67E22"}
FAMILY_ORDER = ("staggered", "continuous", "complex")
ARM_ORDER = ("fable_fresh", "gpt56", "gemini38", "random")
ARM_LABEL = {
    "fable_fresh": "Fable 5.1",
    "gpt56": "GPT-5.6",
    "gemini38": "Gemini 3.8",
    "random": "Random",
}
ARM_COLORS = {
    "fable_fresh": "#1F77B4",
    "gpt56": "#7F3C8D",
    "gemini38": "#11A579",
    "random": "#8C8C8C",
}

PQ4 = ["depth_nan_ratio", "denoise_retained_ratio", "unfold_residual", "orient_agreement"]
SC6 = [
    "correspondence_f1@15",
    "boundary_explained_edge@25",
    "chamfer_sym_px",
    "sam_fill_rate",
    "phase_incoherence_deg",
    "ring_count_error",
]


def _style() -> None:
    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Lato", "DejaVu Sans", "sans-serif"],
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


def _ridge_pred(df: pd.DataFrame, feats: list[str]) -> np.ndarray:
    sc = StandardScaler().fit(df[feats])
    m = RidgeCV(alphas=np.logspace(-3, 3, 25)).fit(sc.transform(df[feats]), df["mIoU"])
    return m.predict(sc.transform(df[feats]))


def _frozen_pred(df: pd.DataFrame, pkg: dict) -> np.ndarray:
    m = pkg["model"]
    X = df[m["features"]].astype(float).to_numpy()
    z = (X - np.asarray(m["scaler_mean"])) / np.asarray(m["scaler_scale"])
    # Unclipped, matching the reported calibration/holdout metrics (no evaluation
    # prediction fell outside [0, 1]).
    return z @ np.asarray(m["coef"]) + m["intercept"]


def _trend(ax, x, y, **kw) -> None:
    s, b = np.polyfit(x, y, 1)
    xs = np.linspace(0.0, 1.0, 50)
    ax.plot(xs, s * xs + b, **kw)


def fig_ablation() -> None:
    pkg = json.loads(MODELS.read_text())
    tr = pd.read_csv(TRAIN)
    ho = pd.read_csv(HOLDOUT)
    lean = pkg["model"]["features"]

    fig, (ax_a, ax_b) = plt.subplots(1, 2, figsize=(11.0, 4.6))

    # (a) calibration ------------------------------------------------------
    tr["proxy"] = _frozen_pred(tr, pkg)
    for fam in FAMILY_ORDER:
        sub = tr[tr["family"] == fam]
        ax_a.scatter(sub["mIoU"], sub["proxy"], s=26, c=FAMILY_COLORS[fam], alpha=0.9,
                     edgecolors="white", linewidths=0.3, label=fam.capitalize(), zorder=3)
    variants = {
        "PQ only (4)": (_ridge_pred(tr, PQ4), {"color": "#7F8C8D", "ls": ":", "lw": 1.6}),
        "SC only (6)": (_ridge_pred(tr, SC6), {"color": "#8E44AD", "ls": ":", "lw": 1.6}),
        "Combined (10)": (_ridge_pred(tr, PQ4 + SC6), {"color": "#2980B9", "ls": "--", "lw": 1.6}),
        "Compact (4), frozen": (tr["proxy"].to_numpy(), {"color": "#1A1A1A", "ls": "-", "lw": 1.4}),
    }
    handles = []
    for name, (pred, kw) in variants.items():
        _trend(ax_a, tr["mIoU"].to_numpy(), pred, zorder=2, **kw)
        handles.append(Line2D([0], [0], label=name, **kw))
    mae = float(np.mean(np.abs(tr["proxy"] - tr["mIoU"])))
    rho = float(stats.spearmanr(tr["proxy"], tr["mIoU"]).correlation)
    ax_a.plot([0, 1], [0, 1], color="0.75", lw=0.8, zorder=1)
    ax_a.set_xlim(-0.02, 1.02); ax_a.set_ylim(-0.02, 1.02)
    ax_a.set_xlabel("GT mIoU"); ax_a.set_ylabel(r"Proxy $\hat{y}$")
    ax_a.set_title("Calibration: 120 trials, 3 development subsets")
    ax_a.text(0.02, 0.97, f"Compact model\nMAE = {mae:.3f}\nSpearman = {rho:.3f}",
              transform=ax_a.transAxes, va="top", fontsize=9)
    leg1 = ax_a.legend(loc="lower right", frameon=False, title="Family")
    ax_a.add_artist(leg1)
    ax_a.legend(handles=handles, loc="upper left", bbox_to_anchor=(0.0, 0.80), frameon=False,
                title="Ridge fit (trend)")

    # (b) holdout ----------------------------------------------------------
    ho["proxy"] = _frozen_pred(ho, pkg)
    ax_b.axhspan(0.5, 0.7, color="#F1C40F", alpha=0.18, zorder=0)
    ax_b.axhline(0.5, color="#C0392B", ls="--", lw=1.0, zorder=1)
    ax_b.axhline(0.7, color="#7F8C8D", ls=":", lw=1.0, zorder=1)
    for fam in FAMILY_ORDER:
        sub = ho[ho["family"] == fam]
        ref = sub[sub["config_kind"] == "anchor"]
        deg = sub[sub["config_kind"] == "bad"]
        ax_b.scatter(ref["mIoU"], ref["proxy"], s=34, c=FAMILY_COLORS[fam], marker="o",
                     edgecolors="white", linewidths=0.3, zorder=3)
        ax_b.scatter(deg["mIoU"], deg["proxy"], s=34, c=FAMILY_COLORS[fam], marker="x",
                     linewidths=1.2, zorder=3)
    mae = float(np.mean(np.abs(ho["proxy"] - ho["mIoU"])))
    rho = float(stats.spearmanr(ho["proxy"], ho["mIoU"]).correlation)
    ax_b.plot([0, 1], [0, 1], color="0.75", lw=0.8, zorder=1)
    ax_b.set_xlim(-0.02, 1.02); ax_b.set_ylim(-0.02, 1.02)
    ax_b.set_xlabel("GT mIoU"); ax_b.set_ylabel(r"Proxy $\hat{y}$")
    ax_b.set_title("Frozen proxy on 54 held-out runs (27 subsets)")
    ax_b.text(0.02, 0.97, f"MAE = {mae:.3f}\nSpearman = {rho:.3f}\n27/27 pairs ranked",
              transform=ax_b.transAxes, va="top", fontsize=9)
    ax_b.text(0.30, 0.605, "refine band $[0.5,0.7)$:\n22 admitted starts", transform=ax_b.transData,
              ha="left", va="center", fontsize=8.5, color="#7D6608")
    ax_b.text(0.30, 0.475, r"alarm $\hat{y}<0.5$", transform=ax_b.transData, ha="left",
              va="top", fontsize=8.5, color="#C0392B")
    fam_handles = [Line2D([0], [0], marker="o", ls="", color=FAMILY_COLORS[f], label=f.capitalize())
                   for f in FAMILY_ORDER]
    kind_handles = [Line2D([0], [0], marker="o", ls="", color="0.3", label="Reference run"),
                    Line2D([0], [0], marker="x", ls="", color="0.3", label="Degraded run")]
    leg = ax_b.legend(handles=fam_handles, loc="lower right", frameon=False, title="Family")
    ax_b.add_artist(leg)
    ax_b.legend(handles=kind_handles, loc="center right", bbox_to_anchor=(1.0, 0.33), frameon=False)

    for ax, tag in ((ax_a, "(a)"), (ax_b, "(b)")):
        ax.text(0.5, -0.2, tag, transform=ax.transAxes, ha="center", fontsize=11)
    fig.tight_layout(w_pad=2.5)
    fig.savefig(OUT / "ablation_results.pdf", bbox_inches="tight")
    plt.close(fig)


def fig_refinement() -> None:
    panel = pd.read_csv(PANEL)
    pol = pd.read_csv(POLICIES).set_index("arm")
    boot = json.loads(BOOT.read_text())["per_arm"]
    start = float(panel["anchor_mIoU"].groupby(panel["subset"]).first().mean())

    fig, (ax_a, ax_b, ax_c) = plt.subplots(1, 3, figsize=(14.5, 4.4),
                                           gridspec_kw={"width_ratios": [1.0, 1.35, 1.25]})

    # (a) selected mIoU by arm with cluster-bootstrap CI on the gain -------
    xs = np.arange(len(ARM_ORDER) + 1)
    means = [start] + [float(panel[panel.arm == a]["selected_mIoU"].mean()) for a in ARM_ORDER]
    colors = ["#BDC3C7"] + [ARM_COLORS[a] for a in ARM_ORDER]
    ax_a.bar(xs, means, color=colors, width=0.62, zorder=2)
    for i, a in enumerate(ARM_ORDER, start=1):
        lo, hi = boot[a]["ci95"]
        d = boot[a]["mean_delta"]
        ax_a.errorbar(i, means[i], yerr=[[d - lo], [hi - d]], fmt="none", ecolor="0.2",
                      elinewidth=1.0, capsize=3, zorder=3)
        ax_a.text(i, means[i] + (hi - d) + 0.006, f"{means[i]:.3f}", ha="center", fontsize=8.5)
    ax_a.text(0, means[0] + 0.006, f"{means[0]:.3f}", ha="center", fontsize=8.5)
    ax_a.axhline(start, color="0.4", ls=":", lw=0.9, zorder=1)
    ax_a.set_xticks(xs); ax_a.set_xticklabels(["Start"] + [ARM_LABEL[a] for a in ARM_ORDER],
                                              rotation=20, ha="right")
    ax_a.set_ylim(0.60, 0.86); ax_a.set_ylabel("Mean mIoU (22 admitted cases)")
    ax_a.set_title("Selected output by proposal arm")

    # (b) selector policies -------------------------------------------------
    policies = [("policy_random_round", "Random round"), ("policy_round1", "Round 1"),
                ("policy_monotone_accept", "Proxy selector"), ("policy_oracle", "GT oracle")]
    pcolors = ["#D5D8DC", "#AEB6BF", "#2C3E50", "#F5B041"]
    w = 0.19
    for j, (col, lab) in enumerate(policies):
        vals = [float(pol.loc[a, col]) for a in ARM_ORDER]
        ax_b.bar(np.arange(len(ARM_ORDER)) + (j - 1.5) * w, vals, width=w, color=pcolors[j],
                 label=lab, zorder=2, edgecolor="white", linewidth=0.4)
    ax_b.axhline(start, color="#C0392B", ls="--", lw=1.0, zorder=3)
    ax_b.text(3.44, start + 0.006, f"start\n{start:.3f}", color="#C0392B", fontsize=8.5,
              ha="left", va="bottom")
    ax_b.set_xlim(-0.55, 3.95)
    ax_b.set_xticks(np.arange(len(ARM_ORDER))); ax_b.set_xticklabels([ARM_LABEL[a] for a in ARM_ORDER])
    ax_b.set_ylim(0.45, 0.95); ax_b.set_ylabel("Mean mIoU (22 cases)")
    ax_b.set_title("Same candidates, different selection policy")
    ax_b.legend(loc="upper left", frameon=False, ncol=2)

    # (c) per-case gain vs starting GT mIoU ---------------------------------
    rng = np.random.default_rng(0)
    for a in ARM_ORDER:
        sub = panel[panel.arm == a]
        jitter = rng.uniform(-0.006, 0.006, size=len(sub))
        ax_c.scatter(sub["anchor_mIoU"] + jitter, sub["delta_mIoU"], s=30, color=ARM_COLORS[a],
                     alpha=0.85, edgecolors="white", linewidths=0.3, label=ARM_LABEL[a], zorder=3)
    ax_c.axhline(0.0, color="0.4", lw=0.9, zorder=1)
    ax_c.axvline(0.7, color="#7F8C8D", ls=":", lw=1.0, zorder=1)
    ax_c.text(0.705, 0.36, "start GT mIoU = 0.7", va="top", ha="left", fontsize=8.5,
              color="#7F8C8D")
    ax_c.set_xlabel("Starting GT mIoU"); ax_c.set_ylabel(r"$\Delta$ mIoU (selected $-$ start)")
    ax_c.set_title("Where the gain occurs")
    ax_c.set_xlim(0.50, 0.90); ax_c.set_ylim(-0.15, 0.37)
    ax_c.legend(loc="upper right", frameon=False)

    for ax, tag in ((ax_a, "(a)"), (ax_b, "(b)"), (ax_c, "(c)")):
        ax.text(0.5, -0.24, tag, transform=ax.transAxes, ha="center", fontsize=11)
    fig.tight_layout(w_pad=2.0)
    fig.savefig(OUT / "refinement_results.pdf", bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    _style()
    OUT.mkdir(parents=True, exist_ok=True)
    fig_ablation()
    fig_refinement()
    print(f"wrote {OUT / 'ablation_results.pdf'}")
    print(f"wrote {OUT / 'refinement_results.pdf'}")


if __name__ == "__main__":
    main()
