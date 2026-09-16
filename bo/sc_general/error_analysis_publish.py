#!/usr/bin/env python3
"""Error analysis for paper/revision/main_claude.tex (Results, "Error analysis").

Reads only frozen tables and executed run directories:
  * data/sc-general/stage2/holdout_scores.csv          (54 stress-test runs)
  * exports/sc-general-random-evaluation/panel_all_arms.csv (22-case panel, 4 arms)
  * bo/sc_general/models.json                          (frozen four-feature proxy)
  * data/refinement/<arm>/<subset>/round{1,2,3}/{reflection_record.json,
    offline_gt.json,only_label.csv}                    (264 executed candidates)
  * <stress-run dir>/{only_label.csv,unwrapped.csv}    (per-point labels, frame)

Writes only under paper/revision/figs/:
  * error_maps.pdf              per-point error maps (unfolded surface)
  * error_analysis_numbers.json every number quoted in the section

Point-level outcomes follow R4Tun's convention: correct; FN (lining point predicted
background); FP (background point predicted lining); swap (lining point given the
wrong lining class). Fractions are of all points in the subset.
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
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch

REPO = Path(__file__).resolve().parents[2]
HOLDOUT = REPO / "data" / "sc-general" / "stage2" / "holdout_scores.csv"
PANEL = REPO / "exports" / "sc-general-random-evaluation" / "panel_all_arms.csv"
MODELS = REPO / "bo" / "sc_general" / "models.json"
REFINE = REPO / "data" / "refinement"
OUT = REPO / "paper" / "revision" / "figs"

ARMS = ("fable_fresh", "gpt56", "gemini38", "random")
ARM_LABEL = {
    "fable_fresh": "Fable 5.1",
    "gpt56": "GPT-5.6",
    "gemini38": "Gemini 3.8",
    "random": "Random",
}
OUTCOMES = ("correct", "FN", "FP", "swap")


def composition(only_label: Path) -> np.ndarray:
    d = pd.read_csv(only_label, usecols=["gt_labels", "pred_labels"])
    g = d["gt_labels"].to_numpy()
    q = d["pred_labels"].to_numpy()
    n = len(g)
    return np.array(
        [
            (g == q).sum(),
            ((g > 0) & (q == 0)).sum(),
            ((g == 0) & (q > 0)).sum(),
            ((g > 0) & (q > 0) & (g != q)).sum(),
        ],
        dtype=float,
    ) / n


def outcome_codes(only_label: Path) -> np.ndarray:
    d = pd.read_csv(only_label, usecols=["gt_labels", "pred_labels"])
    g = d["gt_labels"].to_numpy()
    q = d["pred_labels"].to_numpy()
    code = np.zeros(len(g), dtype=np.int8)  # 0 correct
    code[(g > 0) & (q == 0)] = 1  # FN
    code[(g == 0) & (q > 0)] = 2  # FP
    code[(g > 0) & (q > 0) & (g != q)] = 3  # swap
    return code


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    h = pd.read_csv(HOLDOUT)
    panel = pd.read_csv(PANEL)
    pkg = json.loads(MODELS.read_text())["model"]
    feats = pkg["features"]
    mu = np.asarray(pkg["scaler_mean"])
    sc = np.asarray(pkg["scaler_scale"])
    w = np.asarray(pkg["coef"])
    numbers: dict = {}

    # ---- 1. proxy error structure on the 54 stress runs ---------------------
    h["signed_err"] = h["proxy"] - h["mIoU"]
    by_kind = h.groupby("config_kind")["signed_err"].agg(["mean", "std"]).round(3)
    by_kind_fam = h.groupby(["config_kind", "family"])["signed_err"].mean().round(3)
    numbers["signed_error_by_kind"] = by_kind.to_dict()
    numbers["signed_error_by_kind_family"] = {f"{k}/{f}": v for (k, f), v in by_kind_fam.items()}
    numbers["feature_means_by_kind"] = h.groupby("config_kind")[feats].mean().round(3).to_dict()
    Z = (h[feats].to_numpy() - mu) / sc
    contrib = pd.DataFrame(Z * w, columns=feats)
    contrib["subset"] = h["subset"].values
    contrib["kind"] = h["config_kind"].values
    alarms = h[(h["config_kind"] == "anchor") & (h["proxy"] < 0.5)]["subset"].tolist()
    numbers["reference_alarms"] = {
        s: {
            "proxy": round(float(h[(h.subset == s) & (h.config_kind == "anchor")]["proxy"].iloc[0]), 3),
            "mIoU": round(float(h[(h.subset == s) & (h.config_kind == "anchor")]["mIoU"].iloc[0]), 3),
            "contrib": contrib[(contrib.subset == s) & (contrib.kind == "anchor")][feats].round(3).iloc[0].to_dict(),
            "raw": h[(h.subset == s) & (h.config_kind == "anchor")][feats].round(3).iloc[0].to_dict(),
        }
        for s in alarms
    }
    ref_contrib_mean = contrib[contrib.kind == "anchor"][feats].mean().round(3).to_dict()
    numbers["reference_mean_contrib"] = ref_contrib_mean
    numbers["reference_corr_f1_by_family"] = (
        h[h.config_kind == "anchor"].groupby("family")["correspondence_f1@15"].mean().round(3).to_dict()
    )

    # ---- 2. point-level error composition -----------------------------------
    pathmap = {(r.subset, r.config_kind): Path(r.path) for r in h.itertuples()}
    comp_ref = np.mean([composition(pathmap[(s, "anchor")] / "only_label.csv") for s in h.subset.unique()], axis=0)
    comp_bad = np.mean([composition(pathmap[(s, "bad")] / "only_label.csv") for s in h.subset.unique()], axis=0)
    cases = sorted(panel["subset"].unique())
    fam = panel.drop_duplicates("subset").set_index("subset")["family"]
    rows = []
    start_comp = {}
    for s in cases:
        start_comp[s] = composition(pathmap[(s, "anchor")] / "only_label.csv")
        rows.append(dict(subset=s, arm="start", family=fam[s], **dict(zip(OUTCOMES, start_comp[s]))))
        for arm in ARMS:
            r = panel[(panel.subset == s) & (panel.arm == arm)].iloc[0]
            if r.selected_round == "anchor":
                c = start_comp[s]
            else:
                c = composition(REFINE / arm / s / r.selected_round / "only_label.csv")
            rows.append(dict(subset=s, arm=arm, family=fam[s], **dict(zip(OUTCOMES, c))))
    comp = pd.DataFrame(rows)
    numbers["composition"] = {
        "degraded_27": dict(zip(OUTCOMES, np.round(comp_bad, 3))),
        "reference_27": dict(zip(OUTCOMES, np.round(comp_ref, 3))),
        "panel_22": {a: comp[comp.arm == a][list(OUTCOMES)].mean().round(3).to_dict() for a in ("start",) + ARMS},
        "panel_22_by_family": {
            f"{f}/{a}": comp[(comp.arm == a) & (comp.family == f)][list(OUTCOMES)].mean().round(3).to_dict()
            for f in ("staggered", "continuous", "complex")
            for a in ("start",) + ARMS
        },
    }

    # ---- 3. selector errors over the 264 candidates -------------------------
    ref = h[h.config_kind == "anchor"].set_index("subset")
    cand = []
    for s in cases:
        for arm in ARMS:
            for rd in ("round1", "round2", "round3"):
                d = REFINE / arm / s / rd
                rec = json.loads((d / "reflection_record.json").read_text())
                gt = json.loads((d / "offline_gt.json").read_text())
                row = dict(subset=s, arm=arm, round=rd, proxy=rec["proxy_scaled"], mIoU=gt["perf_mIoU"])
                row["dproxy"] = rec["proxy_scaled"] - ref.loc[s, "proxy"]
                row["dgt"] = gt["perf_mIoU"] - ref.loc[s, "mIoU"]
                for j, k in enumerate(feats):
                    row["dc_" + k] = (rec["features"][k] - ref.loc[s, k]) / sc[j] * w[j]
                cand.append(row)
    cand = pd.DataFrame(cand)
    adm = cand[cand.dproxy > 0].copy()
    adm["gt_up"] = adm.dgt > 0
    rej = cand[cand.dproxy <= 0]
    numbers["candidates"] = {
        "n_total": int(len(cand)),
        "n_admissible": int(len(adm)),
        "admissible_precision": round(float(adm.gt_up.mean()), 3),
        "n_rejected": int(len(rej)),
        "rejected_gt_up_fraction": round(float((rej.dgt > 0).mean()), 3),
        "rejected_mean_dgt": round(float(rej.dgt.mean()), 3),
        "admissible_mean_abs_contrib_change": adm[["dc_" + k for k in feats]].abs().mean().round(4).to_dict(),
        "admissible_top_feature_counts": adm[["dc_" + k for k in feats]].idxmax(axis=1).value_counts().to_dict(),
    }
    bins = [(0.0, 0.01), (0.01, 0.02), (0.02, 0.05), (0.05, 1.0)]
    numbers["precision_by_dproxy"] = {}
    for lo, hi in bins:
        sub = adm[(adm.dproxy > lo) & (adm.dproxy <= hi)]
        numbers["precision_by_dproxy"][f"({lo},{hi}]"] = dict(
            n=int(len(sub)), precision=round(float(sub.gt_up.mean()), 3), mean_dgt=round(float(sub.dgt.mean()), 3)
        )
    numbers["precision_by_arm"] = {
        a: dict(
            n=int((adm.arm == a).sum()),
            precision=round(float(adm[adm.arm == a].gt_up.mean()), 3),
            n_gt_002=int(((adm.arm == a) & (adm.dproxy > 0.02)).sum()),
            precision_gt_002=round(float(adm[(adm.arm == a) & (adm.dproxy > 0.02)].gt_up.mean()), 3),
        )
        for a in ARMS
    }
    delta_rows = []
    for r in adm.itertuples():
        c = composition(REFINE / r.arm / r.subset / r.round / "only_label.csv") - start_comp[r.subset]
        delta_rows.append(dict(gt_up=r.gt_up, **dict(zip(["d_" + o for o in OUTCOMES], c))))
    dr = pd.DataFrame(delta_rows)
    numbers["admissible_composition_delta"] = {
        str(k): v for k, v in dr.groupby("gt_up").mean().round(4).T.to_dict().items()
    }

    # ---- 4. error-map figure -------------------------------------------------
    def frame(subset: str) -> tuple[np.ndarray, np.ndarray]:
        u = pd.read_csv(pathmap[(subset, "anchor")] / "unwrapped.csv", usecols=["theta", "h"])
        return u["theta"].to_numpy(), u["h"].to_numpy()

    def raster(theta, hh, code, cell=0.03):
        tb = np.arange(theta.min(), theta.max() + cell, cell)
        hb = np.arange(hh.min(), hh.max() + cell, cell)
        counts = np.stack(
            [np.histogram2d(hh[code == k], theta[code == k], bins=[hb, tb])[0] for k in range(4)]
        )
        total = counts.sum(0)
        err = counts[1:]
        img = np.full(total.shape, -1, dtype=int)  # -1 empty
        filled = total > 0
        img[filled] = 0
        err_frac = err.sum(0) / np.maximum(total, 1)
        dominant = err.argmax(0) + 1
        show = filled & (err_frac >= 0.3)
        img[show] = dominant[show]
        return img, (tb[0], tb[-1], hb[0], hb[-1])

    def rec_for(arm, subset, rd):
        d = REFINE / arm / subset / rd
        rec = json.loads((d / "reflection_record.json").read_text())
        gt = json.loads((d / "offline_gt.json").read_text())
        return d / "only_label.csv", rec["proxy_scaled"], gt["perf_mIoU"]

    def stress(subset, kind):
        r = h[(h.subset == subset) & (h.config_kind == kind)].iloc[0]
        return Path(r.path) / "only_label.csv", float(r.proxy), float(r.mIoU)

    sel15 = panel[(panel.subset == "1-5") & (panel.arm == "fable_fresh")].iloc[0].selected_round
    sel14 = panel[(panel.subset == "1-4") & (panel.arm == "fable_fresh")].iloc[0].selected_round
    # Prefer showing a non-selected round for 1-4 when available.
    alt14 = "round1" if sel14 != "round1" else ("round2" if sel14 != "round2" else "round3")
    panels = [
        ("1-5", "Degraded overlay (paired test)") + stress("1-5", "bad"),
        ("1-5", "Reference run (= refinement start)") + stress("1-5", "anchor"),
        (
            "1-5",
            f"Fable 5.1 selected ({sel15[0].upper()}{sel15[-1]})",
        )
        + rec_for("fable_fresh", "1-5", sel15),
        ("1-4", "Reference run (= refinement start)") + stress("1-4", "anchor"),
        ("1-4", f"Fable 5.1 {alt14[0].upper()}{alt14[-1]}, not selected")
        + rec_for("fable_fresh", "1-4", alt14),
        (
            "1-4",
            f"Fable 5.1 selected ({sel14[0].upper()}{sel14[-1]})",
        )
        + rec_for("fable_fresh", "1-4", sel14),
    ]
    cmap = ListedColormap(["#FFFFFF", "#D9D9D9", "#2C73D2", "#F39C12", "#C0392B"])
    fig, axes = plt.subplots(2, 3, figsize=(15.0, 6.4), sharex=False, sharey=False)
    frames = {s: frame(s) for s in ("1-5", "1-4")}
    tags = "abcdef"
    comp_txt = {}
    for ax, tag, (subset, title, path, proxy, gt) in zip(axes.ravel(), tags, panels):
        theta, hh = frames[subset]
        code = outcome_codes(path)
        img, ext = raster(theta, hh, code)
        ax.imshow(img + 1, cmap=cmap, vmin=0, vmax=4, origin="lower", extent=ext, aspect="equal",
                  interpolation="nearest")
        c = np.bincount(code, minlength=4) / len(code)
        comp_txt[f"{tag}"] = dict(subset=subset, title=title, proxy=round(proxy, 3), mIoU=round(gt, 3),
                                  **dict(zip(OUTCOMES, np.round(c, 3))))
        ax.set_title(f"({tag}) {subset}: {title}\n"
                     rf"$\hat y$ = {proxy:.3f}, GT mIoU = {gt:.3f}; FN {100*c[1]:.0f}%, swap {100*c[3]:.0f}%",
                     fontsize=9.5)
        ax.set_xlabel("Circumferential position (m)", fontsize=9)
        ax.set_ylabel("Axial position (m)", fontsize=9)
        ax.tick_params(labelsize=8)
    handles = [Patch(color="#D9D9D9", label="Correct"), Patch(color="#2C73D2", label="False negative (lining → background)"),
               Patch(color="#F39C12", label="False positive (background → lining)"),
               Patch(color="#C0392B", label="Class swap (wrong lining block)")]
    fig.legend(handles=handles, loc="lower center", ncol=4, frameon=False, fontsize=9, bbox_to_anchor=(0.5, -0.01))
    fig.tight_layout(rect=(0, 0.04, 1, 1), h_pad=1.6)
    fig.savefig(OUT / "error_maps.pdf", bbox_inches="tight")
    plt.close(fig)
    numbers["error_map_panels"] = comp_txt

    (OUT / "error_analysis_numbers.json").write_text(json.dumps(numbers, indent=2))
    print(json.dumps(numbers, indent=2))
    print(f"wrote {OUT / 'error_maps.pdf'}")


if __name__ == "__main__":
    sys.exit(main())
