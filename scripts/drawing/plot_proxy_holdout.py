#!/usr/bin/env python3
"""Holdout figure (panel a only): GT mIoU vs proxy_v2 with family mean lines.

Sibling-anchor runs only. Three family subplots with paired bars and
horizontal dashed mean lines for GT mIoU and proxy (ablation-bar style).

Reads:
  bo-elegant/family/holdout_scores_v2.csv

Writes:
  paper/Proxy4Tun/figures/proxy_holdout.{pdf,png,svg}
"""
from __future__ import annotations

import re
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
FAMILY_TITLES = {
    "staggered": "Staggered",
    "continuous": "Continuous",
    "complex": "Complex",
}
GT_COLOR = "#2C73D2"
PROXY_COLOR = "#E8871E"


def _style() -> None:
    plt.rcParams.update(
        {
            "font.family": "serif",
            "font.size": 9,
            "axes.labelsize": 10,
            "axes.titlesize": 11,
            "legend.fontsize": 8,
            "xtick.labelsize": 8,
            "ytick.labelsize": 8,
            "axes.spines.top": False,
            "axes.spines.right": False,
        }
    )


def _subset_key(s: str) -> tuple[int, int]:
    m = re.match(r"(\d+)-(\d+)$", str(s))
    return (int(m.group(1)), int(m.group(2))) if m else (999, 999)


def plot_holdout(hs: pd.DataFrame) -> Path:
    anchors = hs[(hs["status"] == "ok") & (hs["config_kind"] == "anchor")].copy()
    if "proxy_v2" not in anchors.columns:
        raise KeyError("holdout_scores_v2.csv missing proxy_v2; rescore with score_holdouts_v2.py")
    anchors["_sk"] = anchors["subset"].map(_subset_key)
    anchors = anchors.sort_values(["family", "_sk"]).reset_index(drop=True)

    fig, axes = plt.subplots(1, 3, figsize=(11.0, 3.8), sharey=True)
    w = 0.38

    for i, fam in enumerate(FAMILY_ORDER):
        ax = axes[i]
        sub = anchors[anchors["family"] == fam].reset_index(drop=True)
        x = np.arange(len(sub))
        gt = sub["mIoU"].astype(float).to_numpy()
        proxy = sub["proxy_v2"].astype(float).to_numpy()
        gt_mean = float(np.mean(gt))
        proxy_mean = float(np.mean(proxy))

        ax.bar(x - w / 2, gt, w, color=GT_COLOR, label="GT mIoU", zorder=2)
        ax.bar(x + w / 2, proxy, w, color=PROXY_COLOR, label=r"Proxy $\hat{y}$", zorder=2)

        # Family-mean horizontal lines (ablation_bar style)
        ax.axhline(
            y=gt_mean,
            color=GT_COLOR,
            linestyle="--",
            linewidth=1.0,
            alpha=0.75,
            zorder=3,
            label=f"GT mean = {gt_mean:.3f}",
        )
        ax.axhline(
            y=proxy_mean,
            color=PROXY_COLOR,
            linestyle="-.",
            linewidth=1.0,
            alpha=0.75,
            zorder=3,
            label=f"Proxy mean = {proxy_mean:.3f}",
        )

        ax.set_xticks(x)
        ax.set_xticklabels(sub["subset"].tolist(), rotation=45, ha="right")
        ax.set_ylim(0, 1.05)
        ax.set_title(FAMILY_TITLES[fam])
        if i == 0:
            ax.set_ylabel("Score")
        ax.legend(frameon=False, loc="lower left", fontsize=7)

    fig.suptitle(
        "Holdout sibling-anchor: GT mIoU vs proxy (v2)",
        fontsize=12,
        y=1.02,
    )
    fig.tight_layout()

    OUT.mkdir(parents=True, exist_ok=True)
    out = OUT / "proxy_holdout.pdf"
    fig.savefig(out, bbox_inches="tight")
    fig.savefig(out.with_suffix(".png"), dpi=200, bbox_inches="tight")
    fig.savefig(out.with_suffix(".svg"), bbox_inches="tight")
    plt.close(fig)
    return out


def main() -> None:
    _style()
    hs = pd.read_csv(HOLDOUT)
    path = plot_holdout(hs)
    print(f"Wrote {path}")
    print(f"Wrote {path.with_suffix('.png')}")
    print(f"Wrote {path.with_suffix('.svg')}")


if __name__ == "__main__":
    main()
