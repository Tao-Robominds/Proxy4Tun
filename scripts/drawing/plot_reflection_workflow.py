#!/usr/bin/env python3
"""Reflection-loop workflow figure grounded in the logged cursor2 campaign.

Top panel: six-step flowchart (triage -> observe -> diagnose -> remediate ->
select -> verify) with the <=3-round loop and the explicit GT boundary --
GT mIoU is only revealed at the final verification step.

Bottom panel: per-subset outcome from data/reflect/campaign_cursor2.md,
anchor mIoU vs the mIoU of the round selected purely by proxy.

Writes:
  paper/Proxy4Tun/figures/reflection_workflow.{pdf,png,svg}
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "paper" / "Proxy4Tun" / "figures"

# Campaign results (data/reflect/campaign_cursor2.md, selection = best proxy of 3 rounds)
RESULTS = [
    # subset, family, anchor mIoU, best-proxy-round mIoU
    ("4-4", "complex", 0.347, 0.700),
    ("4-3", "complex", 0.516, 0.508),
    ("1-5", "staggered", 0.549, 0.782),
    ("1-4", "staggered", 0.556, 0.596),
    ("3-5", "continuous", 0.588, 0.628),
]

FAMILY_COLORS = {
    "staggered": "#2C73D2",
    "continuous": "#44BBA4",
    "complex": "#E67E22",
}

GT_FREE_FACE = "#EAF2FB"
GT_FREE_EDGE = "#2C73D2"
GT_FACE = "#FDEDEC"
GT_EDGE = "#E74C3C"

STEPS = [
    (
        "1. Triage",
        "Score every held-out run\nwith the frozen proxy;\npick the low-proxy tail\n(5 weakest anchors)",
        "gtfree",
    ),
    (
        "2. Observe",
        "Inspect GT-free intrinsics\n+ stage artifacts\n(depth map, detection,\nsegmentation)",
        "gtfree",
    ),
    (
        "3. Diagnose",
        "Match symptoms to\nontology failure modes\n+ experience priors",
        "gtfree",
    ),
    (
        "4. Remediate",
        "Coordinated multi-stage\nparameter overlay;\nre-run stages 2\u20136",
        "gtfree",
    ),
    (
        "5. Select",
        "Re-score with the proxy;\nkeep the best of\n\u22643 rounds by proxy",
        "gtfree",
    ),
    (
        "6. Verify",
        "Reveal GT mIoU,\nbefore vs after\n(reporting only):\n4/5 improve, mean +0.13",
        "gt",
    ),
]


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


def draw_flow(ax: plt.Axes) -> None:
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 30)
    ax.axis("off")

    n = len(STEPS)
    box_w, box_h = 14.2, 15.0
    gap = (100 - n * box_w) / (n + 1)
    y0 = 9.0

    centers = []
    for i, (title, body, kind) in enumerate(STEPS):
        x = gap + i * (box_w + gap)
        face, edge = (GT_FACE, GT_EDGE) if kind == "gt" else (GT_FREE_FACE, GT_FREE_EDGE)
        ax.add_patch(
            FancyBboxPatch(
                (x, y0),
                box_w,
                box_h,
                boxstyle="round,pad=0.6",
                facecolor=face,
                edgecolor=edge,
                linewidth=1.1,
                zorder=2,
            )
        )
        cx = x + box_w / 2
        ax.text(cx, y0 + box_h - 1.6, title, ha="center", va="top", fontsize=9.5, fontweight="bold", zorder=3)
        ax.text(cx, y0 + box_h - 5.4, body, ha="center", va="top", fontsize=6.4, zorder=3)
        centers.append((cx, x, x + box_w))

    for i in range(n - 1):
        ax.add_patch(
            FancyArrowPatch(
                (centers[i][2] + 0.7, y0 + box_h / 2),
                (centers[i + 1][1] - 0.7, y0 + box_h / 2),
                arrowstyle="-|>",
                mutation_scale=11,
                color="#555555",
                lw=1.1,
                zorder=1,
            )
        )

    # Loop: select -> diagnose (next round within the budget)
    ax.add_patch(
        FancyArrowPatch(
            (centers[4][0], y0 - 0.9),
            (centers[2][0], y0 - 0.9),
            arrowstyle="-|>",
            mutation_scale=11,
            color="#7f8c8d",
            lw=1.1,
            ls="--",
            connectionstyle="arc3,rad=-0.32",
            zorder=1,
        )
    )
    ax.text(
        (centers[2][0] + centers[4][0]) / 2,
        y0 - 6.4,
        "next round (budget \u2264 3)",
        ha="center",
        va="center",
        fontsize=7.5,
        color="#7f8c8d",
        bbox=dict(boxstyle="round,pad=0.15", facecolor="white", edgecolor="none"),
        zorder=4,
    )

    # GT boundary between select and verify
    xb = (centers[4][2] + centers[5][1]) / 2
    ax.plot([xb, xb], [2.5, 28.5], color=GT_EDGE, ls=":", lw=1.4, zorder=1)
    ax.text(xb - 1.2, 27.8, "GT-free (proxy only)", ha="right", va="top", fontsize=8, color=GT_FREE_EDGE)
    ax.text(xb + 1.2, 27.8, "GT revealed", ha="left", va="top", fontsize=8, color=GT_EDGE)


def draw_results(ax: plt.Axes) -> None:
    n = len(RESULTS)
    xs = np.arange(n)
    w = 0.36
    for i, (subset, fam, before, after) in enumerate(RESULTS):
        c = FAMILY_COLORS[fam]
        ax.bar(i - w / 2, before, w, color=c, alpha=0.35, edgecolor=c, linewidth=0.8, zorder=2)
        ax.bar(i + w / 2, after, w, color=c, alpha=0.95, edgecolor="white", linewidth=0.4, zorder=2)
        d = after - before
        ax.text(
            i,
            max(before, after) + 0.025,
            f"{d:+.3f}",
            ha="center",
            va="bottom",
            fontsize=8,
            color="#27AE60" if d > 0 else GT_EDGE,
        )
    ax.set_xticks(xs)
    ax.set_xticklabels([r[0] for r in RESULTS])
    ax.set_ylim(0, 1.0)
    ax.set_ylabel("GT mIoU")
    ax.set_xlabel("Reflected subset (5 weakest held-out anchors)")
    ax.set_title("Outcome: anchor vs proxy-selected round", fontsize=10, pad=24)

    from matplotlib.patches import Patch

    handles = [
        Patch(facecolor="gray", alpha=0.35, edgecolor="gray", label="Anchor (before)"),
        Patch(facecolor="gray", alpha=0.95, label="Best round by proxy (after)"),
    ] + [Patch(facecolor=FAMILY_COLORS[f], label=f.capitalize()) for f in ("staggered", "continuous", "complex")]
    ax.legend(
        handles=handles,
        frameon=False,
        loc="lower center",
        bbox_to_anchor=(0.5, 1.02),
        fontsize=7,
        ncol=5,
        columnspacing=1.0,
        handlelength=1.4,
    )


def main() -> None:
    _style()
    fig = plt.figure(figsize=(9.6, 6.0))
    gs = fig.add_gridspec(2, 1, height_ratios=[1.0, 1.15], hspace=0.32)
    ax_flow = fig.add_subplot(gs[0])
    ax_res = fig.add_subplot(gs[1])

    draw_flow(ax_flow)
    ax_flow.set_title("Reflection loop on flagged holdout runs (budget: 3 rounds, stages 2\u20136)", fontsize=11)
    draw_results(ax_res)

    OUT.mkdir(parents=True, exist_ok=True)
    out = OUT / "reflection_workflow.pdf"
    fig.savefig(out, bbox_inches="tight")
    fig.savefig(out.with_suffix(".png"), dpi=200, bbox_inches="tight")
    fig.savefig(out.with_suffix(".svg"), bbox_inches="tight")
    plt.close(fig)
    print(f"Wrote {out}")
    print(f"Wrote {out.with_suffix('.png')}")
    print(f"Wrote {out.with_suffix('.svg')}")


if __name__ == "__main__":
    main()
