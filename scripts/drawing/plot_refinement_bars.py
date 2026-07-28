#!/usr/bin/env python3
"""Mean-mIoU bar chart for the self-refinement campaign.

Left group (n=27): anchor-faithful (notebook-mode) / before / after.
Right group (n=9): before / after for the refined candidates only.

Canvas matches proxy_refinement_fullstage (6.2 x 6.0, Lato).
Writes paper/Proxy4Tun/figures/proxy_refinement_bars.{pdf,png,svg}
"""
from __future__ import annotations

import csv
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "paper" / "Proxy4Tun" / "figures"
HOLDOUT = REPO / "bo-full-stage" / "holdout_scores.csv"
NOTEBOOK = REPO / "bo-notebook-direct" / "scores.csv"

# Match ablation_bar_with_nollm.pdf palette for the adapted / refined bars.
FAITHFUL_COLOR = "#9AA0A6"  # grey — static notebook / anchor-faithful
BEFORE_COLOR = "#2C73D2"    # Opus blue — unified Bayesian-anchor
AFTER_COLOR = "#44BBA4"     # Gemini teal — after refinement
N_BOOT = 10_000
SEED = 42

# subset: (mIoU_before, mIoU_after) — campaign table (3-5 held at anchor proxy,
# after-mIoU from its historical best round).
CANDIDATES = {
    "3-4": (0.622, 0.631),
    "3-2": (0.631, 0.719),
    "3-5": (0.588, 0.628),
    "4-4": (0.347, 0.700),
    "4-3": (0.516, 0.554),
    "4-1": (0.635, 0.655),
    "1-4": (0.556, 0.596),
    "1-5": (0.549, 0.782),
    "2-2": (0.673, 0.668),
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


def bootstrap_ci(values: np.ndarray, n_boot: int = N_BOOT, seed: int = SEED):
    rng = np.random.default_rng(seed)
    n = len(values)
    means = np.array([np.mean(values[rng.integers(0, n, size=n)]) for _ in range(n_boot)])
    return np.percentile(means, 2.5), np.percentile(means, 97.5)


def _draw_bars(ax, center: float, series: list[tuple[np.ndarray, str, str]], bar_width: float):
    """Draw equal-width bars centered on `center`. Returns legend handles info."""
    n = len(series)
    # Even offsets: ..., -1, 0, +1, ... scaled by bar_width
    offsets = (np.arange(n) - (n - 1) / 2.0) * bar_width
    for j, (vals, color, name) in enumerate(series):
        m = float(np.mean(vals))
        lo, hi = bootstrap_ci(vals)
        xpos = center + offsets[j]
        ax.bar(
            xpos, m, bar_width * 0.92,
            yerr=[[m - lo], [hi - m]],
            capsize=3,
            color=color, alpha=0.85,
            edgecolor="white", linewidth=0.5,
            error_kw={"linewidth": 0.8, "capthick": 0.8},
            label=name,
        )
        ax.text(
            xpos, hi + 0.012,
            f"{m:.3f}",
            ha="center", va="bottom", fontsize=11, color="#333333",
        )


def main() -> None:
    _paper_style()
    OUT.mkdir(parents=True, exist_ok=True)

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
    # Same subset order as the unified panel.
    panel_keys = sorted(anchors)
    panel_faithful = np.array([notebook[s] for s in panel_keys])
    panel_before = np.array([anchors[s] for s in panel_keys])
    panel_after = np.array(
        [CANDIDATES[s][1] if s in CANDIDATES else anchors[s] for s in panel_keys]
    )
    cand_before = np.array([v[0] for v in CANDIDATES.values()])
    cand_after = np.array([v[1] for v in CANDIDATES.values()])

    fig, ax = plt.subplots(figsize=(6.2, 6.0))
    bar_width = 0.22
    # First group shifted further left; right group held — gap ~1.8 bar widths.
    left_half = 1.5 * bar_width
    right_half = 1.0 * bar_width
    gap = 0.40
    centers = np.array([-0.28, -0.28 + left_half + gap + right_half])

    _draw_bars(
        ax,
        centers[0],
        [
            (panel_faithful, FAITHFUL_COLOR, "Anchor-faithful"),
            (panel_before, BEFORE_COLOR, "Anchor-Bayesian (before refinement)"),
            (panel_after, AFTER_COLOR, "After refinement"),
        ],
        bar_width,
    )
    _draw_bars(
        ax,
        centers[1],
        [
            (cand_before, BEFORE_COLOR, "Anchor-Bayesian (before refinement)"),
            (cand_after, AFTER_COLOR, "After refinement"),
        ],
        bar_width,
    )

    # Deduplicate legend (right group reuses before/after colours).
    handles, labels = ax.get_legend_handles_labels()
    seen: dict[str, object] = {}
    for h, lab in zip(handles, labels):
        if lab not in seen:
            seen[lab] = h
    ax.legend(seen.values(), seen.keys(), frameon=False, loc="upper left", fontsize=11)

    ax.set_xticks(centers)
    ax.set_xticklabels(
        ["All holdout subsets\n($n=27$)", "Refined candidates\n($n=9$)"]
    )
    ax.set_ylabel("Mean mIoU")
    ax.set_ylim(0, 1.0)
    # Pad equally so the two-group block sits in the middle of the canvas.
    block_lo = centers[0] - left_half
    block_hi = centers[1] + right_half
    pad = 0.28
    mid = 0.5 * (block_lo + block_hi)
    half = 0.5 * (block_hi - block_lo) + pad
    ax.set_xlim(mid - half, mid + half)
    ax.set_title("Overall performance: mean mIoU")
    fig.tight_layout()
    out = OUT / "proxy_refinement_bars.pdf"
    fig.savefig(out, bbox_inches="tight")
    fig.savefig(out.with_suffix(".png"), dpi=200, bbox_inches="tight")
    fig.savefig(out.with_suffix(".svg"), bbox_inches="tight")
    plt.close(fig)
    print(f"Wrote {out}")
    print(
        f"panel faithful={panel_faithful.mean():.3f} "
        f"before={panel_before.mean():.3f} after={panel_after.mean():.3f}; "
        f"cand before={cand_before.mean():.3f} after={cand_after.mean():.3f}"
    )


if __name__ == "__main__":
    main()
