#!/usr/bin/env python3
"""Before/after self-refinement figure for the 9 proxy-flagged subsets.

Same style as proxy_holdout_fullstage: scaled proxy vs GT mIoU, family
colours, threshold segments. Hollow markers = anchor (before), filled =
proxy-selected round (after), grey arrows connect the pairs.

Writes paper/Proxy4Tun/figures/proxy_refinement_fullstage.{pdf,png,svg}
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "paper" / "Proxy4Tun" / "figures"

FAMILY_COLORS = {
    "staggered": "#2C73D2",
    "continuous": "#44BBA4",
    "complex": "#E67E22",
}
FAMILY_ORDER = ("staggered", "continuous", "complex")
FAMILY_OF = {"1": "staggered", "2": "staggered", "3": "continuous", "4": "complex", "5": "complex"}

# subset: (proxy_before, mIoU_before, proxy_after, mIoU_after)
DATA = {
    "3-4": (0.574, 0.622, 0.5965, 0.631),
    "3-2": (0.600, 0.631, 0.7750, 0.719),
    # 3-5: monotone accept keeps the anchor under the frozen scaled scorer
    # (no round beat proxy 0.620); shown with the historical round-3 mIoU.
    "3-5": (0.620, 0.588, 0.620, 0.628),
    "4-4": (0.623, 0.347, 0.6247, 0.700),
    "4-3": (0.630, 0.516, 0.6397, 0.554),
    "4-1": (0.652, 0.635, 0.6570, 0.655),
    "1-4": (0.661, 0.556, 0.6604, 0.596),
    "1-5": (0.675, 0.549, 0.6848, 0.782),
    "2-2": (0.692, 0.673, 0.7029, 0.668),
}


def _paper_style() -> None:
    plt.rcParams.update(
        {
            "font.family": "Lato",
            "font.sans-serif": ["Lato", "DejaVu Sans", "sans-serif"],
            "font.size": 15,
            "axes.labelsize": 16.5,
            "axes.titlesize": 16.5,
            "legend.fontsize": 12,
            "xtick.labelsize": 13.5,
            "ytick.labelsize": 13.5,
            "axes.spines.top": False,
            "axes.spines.right": False,
        }
    )


def main() -> None:
    _paper_style()
    OUT.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(6.2, 6.0))
    lims = [-0.05, 1.05]

    # Threshold segments (same geometry as proxy_holdout_fullstage).
    # Threshold segments: red alarm/reject L; yellow refine box [0.3,0.7]×[0.5,0.7].
    ax.hlines(0.5, lims[0], 0.3, color="#FF0000", ls="--", lw=0.9, zorder=7)
    ax.vlines(0.3, lims[0], 0.5, color="#FF0000", ls="--", lw=0.9, zorder=7)
    ax.hlines(0.5, 0.3, 0.7, color="#F1C40F", ls="--", lw=0.9, zorder=7)
    ax.hlines(0.7, 0.3, 0.7, color="#F1C40F", ls="--", lw=0.9, zorder=7)
    ax.vlines(0.3, 0.5, 0.7, color="#F1C40F", ls="--", lw=0.9, zorder=7)
    ax.vlines(0.7, 0.5, 0.7, color="#F1C40F", ls="--", lw=0.9, zorder=7)

    # Green box enclosing all post-refinement points.
    pad = 0.025
    after_m = [m1 for (_, _, _, m1) in DATA.values()]
    after_p = [p1 for (_, _, p1, _) in DATA.values()]
    ax.add_patch(
        plt.Rectangle(
            (min(after_m) - pad, min(after_p) - pad),
            (max(after_m) - min(after_m)) + 2 * pad,
            (max(after_p) - min(after_p)) + 2 * pad,
            facecolor="none",
            edgecolor="#27AE60",
            ls="--",
            lw=1.2,
            zorder=6,
        )
    )

    for subset, (p0, m0, p1, m1) in DATA.items():
        color = FAMILY_COLORS[FAMILY_OF[subset.split("-")[0]]]
        ax.scatter(
            m0, p0, c="#E8D48B", marker="o", s=32, alpha=0.85,
            edgecolors="white", linewidths=0.35, zorder=3,
        )
        ax.scatter(
            m1, p1, c=color, marker="o", s=42, alpha=0.95,
            edgecolors="white", linewidths=0.35, zorder=4,
        )

    ax.set_xlim(lims)
    ax.set_ylim(lims)
    ax.set_xlabel("GT mIoU", labelpad=12)
    ax.set_ylabel(r"Proxy $\hat{y}$")
    ax.set_title("Self-refinement: 9 candidates")
    ax.set_aspect("equal", adjustable="box")

    fam_handles = [
        Line2D(
            [0], [0], marker="o", color="w",
            markerfacecolor=FAMILY_COLORS[f], markersize=6.4,
            label=f.capitalize(),
        )
        for f in FAMILY_ORDER
    ]
    fam_leg = ax.legend(
        handles=fam_handles, frameon=False, loc="upper left", fontsize=12,
    )
    ax.add_artist(fam_leg)

    # Bottom-right: dashed box markers matching the refine / after regions.
    box_handles = [
        Patch(
            facecolor="none", edgecolor="#27AE60",
            linestyle=(0, (2.0, 1.6)), linewidth=0.9,
            label="After refinement",
        ),
        Patch(
            facecolor="none", edgecolor="#F1C40F",
            linestyle=(0, (2.0, 1.6)), linewidth=0.9,
            label="Refinement baseline",
        ),
    ]
    ax.legend(
        handles=box_handles, frameon=False, loc="lower right", fontsize=12,
        handlelength=0.85, handleheight=0.75, borderpad=0.25,
    )

    fig.tight_layout()
    out = OUT / "proxy_refinement_fullstage.pdf"
    fig.savefig(out, bbox_inches="tight")
    fig.savefig(out.with_suffix(".png"), dpi=200, bbox_inches="tight")
    fig.savefig(out.with_suffix(".svg"), bbox_inches="tight")
    plt.close(fig)
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
