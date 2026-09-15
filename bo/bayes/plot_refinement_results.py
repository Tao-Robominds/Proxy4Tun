#!/usr/bin/env python3
"""Native vector refinement_results.pdf: (a) scatter (b) n=9 bars (c) n=27 bars."""

from __future__ import annotations

import csv
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))
from bo.paths import FULL_STAGE_PKG, MANUSCRIPT_FIGS, NOTEBOOK_PKG

OUT = MANUSCRIPT_FIGS
HOLDOUT = FULL_STAGE_PKG / "holdout_scores.csv"
NOTEBOOK = NOTEBOOK_PKG / "scores.csv"

FAMILY_COLORS = {
    "staggered": "#2C73D2",
    "continuous": "#44BBA4",
    "complex": "#E67E22",
}
FAMILY_OF = {"1": "staggered", "2": "staggered", "3": "continuous", "4": "complex", "5": "complex"}

# subset: (proxy_before, mIoU_before, proxy_after, mIoU_after) — Fable PoC
# Audited Fable PoC selections (bo-proxy-scale/selections/*); 4-3 uses cursor2_s1.
DATA = {
    "3-4": (0.574, 0.622, 0.5965, 0.631),
    "3-2": (0.600, 0.631, 0.7750, 0.719),
    "3-5": (0.620, 0.588, 0.620, 0.588),  # monotone accept: keep anchor
    "4-4": (0.623, 0.347, 0.6247, 0.700),
    "4-3": (0.630, 0.516, 0.6402, 0.544),
    "4-1": (0.652, 0.635, 0.6623, 0.659),
    "1-4": (0.661, 0.556, 0.6708, 0.786),
    "1-5": (0.675, 0.549, 0.6848, 0.782),
    "2-2": (0.692, 0.673, 0.7029, 0.668),
}
CANDIDATES = {k: (v[1], v[3]) for k, v in DATA.items()}

FAITHFUL_COLOR = "#C5C9CE"
BEFORE_COLOR = "#E8D48B"
AFTER_COLOR = "#44BBA4"
N_BOOT = 5000
SEED = 42


def _style() -> None:
    plt.rcParams.update(
        {
            "font.family": "Lato",
            "font.sans-serif": ["Lato", "DejaVu Sans", "sans-serif"],
            "font.size": 11,
            "axes.labelsize": 12,
            "axes.titlesize": 12,
            "legend.fontsize": 9,
            "xtick.labelsize": 10,
            "ytick.labelsize": 10,
            "axes.spines.top": False,
            "axes.spines.right": False,
        }
    )


def bootstrap_ci(values: np.ndarray, n_boot: int = N_BOOT, seed: int = SEED):
    rng = np.random.default_rng(seed)
    n = len(values)
    means = np.array([np.mean(values[rng.integers(0, n, size=n)]) for _ in range(n_boot)])
    return np.percentile(means, 2.5), np.percentile(means, 97.5)


def panel_a(ax) -> None:
    lims = [-0.05, 1.05]
    ax.hlines(0.5, lims[0], 0.3, color="#FF0000", ls="--", lw=0.9, zorder=7)
    ax.vlines(0.3, lims[0], 0.5, color="#FF0000", ls="--", lw=0.9, zorder=7)
    ax.hlines(0.5, 0.3, 0.7, color="#F1C40F", ls="--", lw=0.9, zorder=7)
    ax.hlines(0.7, 0.3, 0.7, color="#F1C40F", ls="--", lw=0.9, zorder=7)
    ax.vlines(0.3, 0.5, 0.7, color="#F1C40F", ls="--", lw=0.9, zorder=7)
    ax.vlines(0.7, 0.5, 0.7, color="#F1C40F", ls="--", lw=0.9, zorder=7)
    for subset, (p0, m0, p1, m1) in DATA.items():
        color = FAMILY_COLORS[FAMILY_OF[subset.split("-")[0]]]
        ax.annotate(
            "",
            xy=(m1, p1),
            xytext=(m0, p0),
            arrowprops=dict(arrowstyle="->", color="#888888", lw=0.8),
            zorder=2,
        )
        ax.scatter([m0], [p0], facecolors="none", edgecolors=color, s=42, linewidths=1.2, zorder=3)
        ax.scatter([m1], [p1], c=color, s=36, edgecolors="white", linewidths=0.3, zorder=4)
    ax.set_xlim(lims)
    ax.set_ylim(lims)
    ax.set_xlabel("GT mIoU")
    ax.set_ylabel(r"Proxy $\hat{y}$")
    ax.set_title("(a) Nine candidates: before → after")
    ax.set_aspect("equal", adjustable="box")
    fam = [
        Line2D([0], [0], marker="o", color="w", markerfacecolor=FAMILY_COLORS[f], markersize=6, label=f.capitalize())
        for f in ("staggered", "continuous", "complex")
    ]
    mark = [
        Line2D([0], [0], marker="o", color="w", markerfacecolor="none", markeredgecolor="#333", markersize=6, label="Before"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor="#333", markersize=6, label="After"),
    ]
    leg1 = ax.legend(handles=fam, frameon=False, loc="upper left", fontsize=8)
    ax.add_artist(leg1)
    ax.legend(handles=mark, frameon=False, loc="lower right", fontsize=8)


def _bar_group(ax, center, series, bar_width):
    n = len(series)
    offsets = (np.arange(n) - (n - 1) / 2.0) * bar_width
    for j, (vals, color, name) in enumerate(series):
        m = float(np.mean(vals))
        lo, hi = bootstrap_ci(vals)
        xpos = center + offsets[j]
        ax.bar(
            xpos,
            m,
            bar_width * 0.92,
            yerr=[[m - lo], [hi - m]],
            capsize=2.5,
            color=color,
            alpha=0.85,
            edgecolor="white",
            linewidth=0.5,
            error_kw={"linewidth": 0.7, "capthick": 0.7},
            label=name,
        )
        ax.text(xpos, hi + 0.015, f"{m:.3f}", ha="center", va="bottom", fontsize=9, color="#333")


def panel_bc(ax_b, ax_c) -> None:
    anchors = {
        r["subset"]: float(r["mIoU"])
        for r in csv.DictReader(HOLDOUT.open())
        if r["config_kind"] == "anchor"
    }
    notebook = {
        r["subset"]: float(r["notebook_mIoU"])
        for r in csv.DictReader(NOTEBOOK.open())
        if r["notebook_mIoU"] not in (None, "")
    }
    panel_keys = sorted(anchors)
    panel_faithful = np.array([notebook[s] for s in panel_keys])
    panel_before = np.array([anchors[s] for s in panel_keys])
    panel_after = np.array([CANDIDATES[s][1] if s in CANDIDATES else anchors[s] for s in panel_keys])
    cand_before = np.array([v[0] for v in CANDIDATES.values()])
    cand_after = np.array([v[1] for v in CANDIDATES.values()])

    bw = 0.28
    _bar_group(
        ax_b,
        0.0,
        [
            (cand_before, BEFORE_COLOR, "Unified family anchor"),
            (cand_after, AFTER_COLOR, "Self-refinement"),
        ],
        bw,
    )
    ax_b.set_xticks([0.0])
    ax_b.set_xticklabels(["Refined candidates\n($n=9$)"])
    ax_b.set_ylabel("Mean mIoU")
    ax_b.set_ylim(0, 1.0)
    ax_b.set_xlim(-0.55, 0.55)
    ax_b.set_title("(b) Nine-case mean mIoU")
    ax_b.legend(frameon=False, loc="upper left", fontsize=8)

    bw2 = 0.22
    _bar_group(
        ax_c,
        0.0,
        [
            (panel_faithful, FAITHFUL_COLOR, "Notebook expert"),
            (panel_before, BEFORE_COLOR, "Unified family anchor"),
            (panel_after, AFTER_COLOR, "Self-refinement"),
        ],
        bw2,
    )
    ax_c.set_xticks([0.0])
    ax_c.set_xticklabels(["All holdouts\n($n=27$)"])
    ax_c.set_ylim(0, 1.0)
    ax_c.set_xlim(-0.55, 0.55)
    ax_c.set_title("(c) Overall panel mean mIoU")
    ax_c.legend(frameon=False, loc="upper left", fontsize=8)
    print(
        f"n9 {cand_before.mean():.3f}->{cand_after.mean():.3f}; "
        f"n27 {panel_faithful.mean():.3f}/{panel_before.mean():.3f}/{panel_after.mean():.3f}"
    )


def main() -> None:
    _style()
    OUT.mkdir(parents=True, exist_ok=True)
    fig = plt.figure(figsize=(12.6, 4.4))
    gs = fig.add_gridspec(1, 3, width_ratios=[1.15, 0.9, 0.95], wspace=0.28)
    ax_a = fig.add_subplot(gs[0, 0])
    ax_b = fig.add_subplot(gs[0, 1])
    ax_c = fig.add_subplot(gs[0, 2])
    panel_a(ax_a)
    panel_bc(ax_b, ax_c)
    out = OUT / "refinement_results.pdf"
    fig.savefig(out, bbox_inches="tight")
    fig.savefig(out.with_suffix(".png"), dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
