#!/usr/bin/env python3
"""Family-aggregated holdout bars: GT mIoU vs proxy_v2 (ablation-bar style).

One bar group per family (n=9 sibling-anchor subsets). GT bars have no error
bars; proxy bars show standard error of the mean (SEM = std / sqrt(n)).

Style matched to methods/papers plot_ablation_bar_with_rules.py /
paper/Proxy4Tun/figures/ablation_bar_with_nollm.pdf.

Reads:
  bo-elegant/family/holdout_scores_v2.csv

Writes:
  paper/Proxy4Tun/figures/proxy_holdout_family.{pdf,png,svg}
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
HOLDOUT = REPO / "bo-elegant" / "family" / "holdout_scores_v2.csv"
OUT = REPO / "paper" / "Proxy4Tun" / "figures"

FAMILY_ORDER = ("staggered", "continuous", "complex")
FAMILY_LABELS = {
    "staggered": "Staggered",
    "continuous": "Continuous",
    "complex": "Complex",
}
# Same palette as ablation_bar LLM / accent colours
GT_COLOR = "#2C73D2"
PROXY_COLOR = "#E8871E"


def _fmt_val(m: float) -> str:
    return f".{int(round(m * 1000)):03d}" if m < 1 else f"{m:.3f}"


def main() -> None:
    hs = pd.read_csv(HOLDOUT)
    anchors = hs[(hs["status"] == "ok") & (hs["config_kind"] == "anchor")].copy()
    if "proxy_v2" not in anchors.columns:
        raise KeyError("Missing proxy_v2; run bo-elegant/score_holdouts_v2.py first")

    gt_means, proxy_means, proxy_sems, n_per = [], [], [], []
    for fam in FAMILY_ORDER:
        sub = anchors[anchors["family"] == fam]
        gt = sub["mIoU"].astype(float).to_numpy()
        pr = sub["proxy_v2"].astype(float).to_numpy()
        n = len(sub)
        gt_means.append(float(np.mean(gt)))
        proxy_means.append(float(np.mean(pr)))
        # Standard error of the mean, not score std
        sd = float(np.std(pr, ddof=1)) if n > 1 else 0.0
        proxy_sems.append(sd / np.sqrt(n) if n > 0 else 0.0)
        n_per.append(n)

    gt_means = np.asarray(gt_means)
    proxy_means = np.asarray(proxy_means)
    proxy_sems = np.asarray(proxy_sems)

    fig, ax = plt.subplots(figsize=(7.2, 5.0))
    bar_width = 0.32
    x = np.arange(len(FAMILY_ORDER))

    bars_gt = ax.bar(
        x - bar_width / 2,
        gt_means,
        bar_width,
        color=GT_COLOR,
        alpha=0.85,
        edgecolor="white",
        linewidth=0.5,
        label="GT mIoU",
        zorder=2,
    )
    bars_pr = ax.bar(
        x + bar_width / 2,
        proxy_means,
        bar_width,
        yerr=proxy_sems,
        capsize=3,
        color=PROXY_COLOR,
        alpha=0.85,
        edgecolor="white",
        linewidth=0.5,
        error_kw={"linewidth": 0.8, "capthick": 0.8},
        label=r"Proxy $\hat{y}$",
        zorder=2,
    )

    for bar, m_val in zip(bars_gt, gt_means):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            m_val + 0.006,
            _fmt_val(m_val),
            ha="center",
            va="bottom",
            fontsize=8,
            color="#333333",
            rotation=90,
        )
    for bar, m_val, err in zip(bars_pr, proxy_means, proxy_sems):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            m_val + err + 0.006,
            _fmt_val(m_val),
            ha="center",
            va="bottom",
            fontsize=8,
            color="#333333",
            rotation=90,
        )

    ax.set_xticks(x)
    ax.set_xticklabels(
        [f"{FAMILY_LABELS[f]}\n($n={n}$)" for f, n in zip(FAMILY_ORDER, n_per)],
        fontsize=11,
    )
    ax.set_ylabel("Mean score", fontsize=12)
    ax.set_xlabel("Lining family", fontsize=12)
    ax.tick_params(axis="y", labelsize=11)
    ax.set_ylim(0, 1.05)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.legend(fontsize=10, loc="upper right", framealpha=0.85, edgecolor="none")
    ax.set_title("Holdout sibling-anchor: GT mIoU vs proxy (v2)", fontsize=13, fontweight="bold")

    fig.tight_layout()
    OUT.mkdir(parents=True, exist_ok=True)
    out = OUT / "proxy_holdout_family.pdf"
    fig.savefig(out, bbox_inches="tight", dpi=300)
    fig.savefig(out.with_suffix(".png"), dpi=300, bbox_inches="tight")
    fig.savefig(out.with_suffix(".svg"), bbox_inches="tight")
    plt.close(fig)
    print(f"Saved {out}")
    print(f"Saved {out.with_suffix('.png')}")
    print(f"Saved {out.with_suffix('.svg')}")
    for fam, g, p, s in zip(FAMILY_ORDER, gt_means, proxy_means, proxy_sems):
        print(f"  {fam}: GT={g:.3f}  proxy={p:.3f}±{s:.3f} (SEM)")


if __name__ == "__main__":
    main()
