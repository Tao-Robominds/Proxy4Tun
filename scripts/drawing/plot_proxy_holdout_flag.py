#!/usr/bin/env python3
"""Holdout scatter highlighting low-mIoU flagging with proxy v2.

Sibling-anchor (circles) vs known-bad (crosses). Horizontal alarm threshold
shows that low-GT runs are flagged while anchors stay above the cut.

Reads:
  bo-elegant/family/holdout_scores_v2.csv
  bo-elegant/family/models_v2.json

Writes:
  paper/Proxy4Tun/figures/proxy_holdout_flag.{pdf,png,svg}
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

REPO = Path(__file__).resolve().parents[2]
HOLDOUT = REPO / "bo-elegant" / "family" / "holdout_scores_v2.csv"
MODELS = REPO / "bo-elegant" / "family" / "models_v2.json"
OUT = REPO / "paper" / "Proxy4Tun" / "figures"

FAMILY_COLORS = {
    "staggered": "#2C73D2",
    "continuous": "#44BBA4",
    "complex": "#E67E22",
}
FAMILY_LABELS = {
    "staggered": "Staggered",
    "continuous": "Continuous",
    "complex": "Complex",
}
FAMILY_ORDER = ("staggered", "continuous", "complex")


def _style() -> None:
    plt.rcParams.update(
        {
            "font.family": "serif",
            "font.size": 10,
            "axes.labelsize": 11,
            "axes.titlesize": 11,
            "legend.fontsize": 8,
            "xtick.labelsize": 9,
            "ytick.labelsize": 9,
            "axes.spines.top": False,
            "axes.spines.right": False,
        }
    )


def main() -> None:
    _style()
    hs = pd.read_csv(HOLDOUT)
    hs = hs[hs["status"] == "ok"].copy()
    models = json.loads(MODELS.read_text(encoding="utf-8"))
    alarm = float(models["alarm_threshold"])

    anchors = hs[hs["config_kind"] == "anchor"]
    bads = hs[hs["config_kind"] == "bad"]

    # Flagging stats (proxy below alarm)
    tp = int(((bads["proxy_v2"] <= alarm)).sum())
    fn = int(((bads["proxy_v2"] > alarm)).sum())
    fp = int(((anchors["proxy_v2"] <= alarm)).sum())
    tn = int(((anchors["proxy_v2"] > alarm)).sum())
    n_bad, n_anchor = len(bads), len(anchors)

    fig, ax = plt.subplots(figsize=(5.4, 5.0))
    lims = [-0.2, 1.05]

    # Flagged region (proxy ≤ alarm)
    ax.axhspan(lims[0], alarm, color="#E74C3C", alpha=0.08, zorder=0)
    ax.axhline(
        alarm,
        color="#E74C3C",
        ls="--",
        lw=1.2,
        alpha=0.9,
        zorder=1,
        label=f"Alarm $\\tau$ = {alarm:.3f}",
    )
    ax.plot(lims, lims, ls=":", color="gray", lw=0.9, alpha=0.6, zorder=1)

    for fam in FAMILY_ORDER:
        a = anchors[anchors["family"] == fam]
        b = bads[bads["family"] == fam]
        ax.scatter(
            a["mIoU"],
            a["proxy_v2"],
            c=FAMILY_COLORS[fam],
            marker="o",
            s=48,
            alpha=0.9,
            edgecolors="white",
            linewidths=0.4,
            zorder=3,
            label=FAMILY_LABELS[fam],
        )
        ax.scatter(
            b["mIoU"],
            b["proxy_v2"],
            c=FAMILY_COLORS[fam],
            marker="X",
            s=52,
            alpha=0.85,
            linewidths=0.8,
            zorder=4,
        )

    ax.set_xlim(lims)
    ax.set_ylim(lims)
    ax.set_xlabel("GT mIoU")
    ax.set_ylabel(r"Proxy $\hat{y}$")
    ax.set_title("Holdout: proxy flags low-mIoU runs")
    ax.set_aspect("equal", adjustable="box")

    fam_handles = [
        Line2D(
            [0],
            [0],
            marker="o",
            color="w",
            markerfacecolor=FAMILY_COLORS[f],
            markersize=7,
            label=FAMILY_LABELS[f],
        )
        for f in FAMILY_ORDER
    ]
    kind_handles = [
        Line2D([0], [0], marker="o", color="gray", linestyle="None", markersize=7, label="Sibling-anchor"),
        Line2D([0], [0], marker="X", color="gray", linestyle="None", markersize=7, label="Known-bad"),
        Line2D([0], [0], color="#E74C3C", ls="--", lw=1.2, label=f"Alarm $\\tau$ = {alarm:.3f}"),
        Patch(facecolor="#E74C3C", alpha=0.15, edgecolor="none", label="Flagged ($\\hat{y}\\leq\\tau$)"),
    ]
    leg1 = ax.legend(handles=fam_handles, frameon=False, loc="lower right", fontsize=7)
    ax.add_artist(leg1)
    ax.legend(handles=kind_handles, frameon=False, loc="upper left", fontsize=7)

    ax.text(
        0.98,
        0.02,
        f"Low-mIoU flagged: {tp}/{n_bad}\n"
        f"Anchor false alarms: {fp}/{n_anchor}\n"
        f"$n$ = {len(hs)}",
        transform=ax.transAxes,
        va="bottom",
        ha="right",
        fontsize=8,
        bbox=dict(boxstyle="round,pad=0.3", facecolor="white", edgecolor="#cccccc", alpha=0.92),
    )

    fig.tight_layout()
    OUT.mkdir(parents=True, exist_ok=True)
    out = OUT / "proxy_holdout_flag.pdf"
    fig.savefig(out, bbox_inches="tight")
    fig.savefig(out.with_suffix(".png"), dpi=200, bbox_inches="tight")
    fig.savefig(out.with_suffix(".svg"), bbox_inches="tight")
    plt.close(fig)
    print(f"Wrote {out}")
    print(f"Wrote {out.with_suffix('.png')}")
    print(f"Wrote {out.with_suffix('.svg')}")
    print(f"TP={tp} FN={fn} FP={fp} TN={tn} alarm={alarm:.3f}")


if __name__ == "__main__":
    main()
