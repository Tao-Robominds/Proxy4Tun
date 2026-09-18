#!/usr/bin/env python3
"""Redraw the three legacy Google-Slides concept figures for main_claude.tex.

Writes (aspect ratios match the previous PDFs):
  paper/Proxy4Tun/figs/position.pdf   (711 x 403 pt)
  paper/Proxy4Tun/figs/intrinsics.pdf (702 x 240 pt)
  paper/Proxy4Tun/figs/b-p.pdf        (700 x 287 pt)

Thumbnails come from read-only BO/anchor artefacts under data/bo/ and
scripts/3d/ (never writes into anchors/).
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch, Rectangle
from PIL import Image

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "paper" / "Proxy4Tun" / "figs"
ANCHOR = REPO / "data" / "bo" / "unified" / "5-2-family-proxy" / "runs" / "5-2-anchor"
QL = REPO / "scripts" / "3d" / "5-1_quality_levels.png"

PT = 1 / 72.0  # inches per point


def _style() -> None:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 9,
            "axes.titlesize": 10,
            "axes.labelsize": 9,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )


def _box(ax, xy, w, h, *, fc="#F7F9FC", ec="#2C3E50", lw=1.2, r=0.02):
    ax.add_patch(
        FancyBboxPatch(
            xy,
            w,
            h,
            boxstyle=f"round,pad={r}",
            facecolor=fc,
            edgecolor=ec,
            linewidth=lw,
            mutation_aspect=0.4,
        )
    )


def _arrow(ax, p0, p1, *, color="#2C3E50", lw=1.4):
    ax.add_patch(
        FancyArrowPatch(
            p0,
            p1,
            arrowstyle="-|>",
            mutation_scale=12,
            linewidth=lw,
            color=color,
            shrinkA=2,
            shrinkB=2,
        )
    )


def _load_rgb(path: Path) -> np.ndarray:
    return np.asarray(Image.open(path).convert("RGB"))


def draw_position(path: Path) -> None:
    """2x2 deployment adaptability vs deployment QC."""
    fig = plt.figure(figsize=(711 * PT, 403 * PT), dpi=150)
    ax = fig.add_axes([0.08, 0.10, 0.88, 0.82])
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.set_xticks([])
    ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(False)

    # Axes
    ax.annotate(
        "",
        xy=(98, 8),
        xytext=(8, 8),
        arrowprops=dict(arrowstyle="-|>", color="#34495E", lw=1.5),
    )
    ax.annotate(
        "",
        xy=(8, 98),
        xytext=(8, 8),
        arrowprops=dict(arrowstyle="-|>", color="#34495E", lw=1.5),
    )
    ax.text(53, 2.5, "Deployment QC", ha="center", va="center", fontsize=11, color="#2C3E50")
    ax.text(
        2.2,
        53,
        "Deployment adaptability",
        ha="center",
        va="center",
        fontsize=11,
        color="#2C3E50",
        rotation=90,
    )
    ax.text(18, 5.5, "Weak", ha="center", fontsize=8, color="#7F8C8D")
    ax.text(82, 5.5, "Strong", ha="center", fontsize=8, color="#7F8C8D")
    ax.text(5.5, 18, "Low", ha="center", va="center", fontsize=8, color="#7F8C8D", rotation=90)
    ax.text(5.5, 82, "High", ha="center", va="center", fontsize=8, color="#7F8C8D", rotation=90)

    # Quadrant guides
    ax.plot([8, 98], [53, 53], ls="--", color="#BDC3C7", lw=1.0)
    ax.plot([53, 53], [8, 98], ls="--", color="#BDC3C7", lw=1.0)

    cells = [
        # (x, y, title, qc, adapt, highlight)
        (
            12,
            58,
            "Foundation-model pipelines",
            "Heuristic checks",
            "Parameter re-tuning",
            False,
        ),
        (
            58,
            58,
            "Proxy4Tun",
            "Intrinsic proxy score",
            "Proxy-guided refinement",
            True,
        ),
        (
            12,
            14,
            "Supervised deep-learning",
            "Implicit confidence",
            "Labels and re-training",
            False,
        ),
        (
            58,
            14,
            "Engineer-designed rules",
            "Explicit thresholds",
            "Rule re-design",
            False,
        ),
    ]
    for x, y, title, qc, adapt, hi in cells:
        fc = "#E8F6EF" if hi else "#F8F9F9"
        ec = "#1E8449" if hi else "#566573"
        _box(ax, (x, y), 36, 34, fc=fc, ec=ec, lw=1.8 if hi else 1.1, r=0.03)
        ax.text(
            x + 18,
            y + 28,
            title,
            ha="center",
            va="center",
            fontsize=10,
            fontweight="bold",
            color="#1E8449" if hi else "#1C2833",
        )
        # QC badge
        ax.add_patch(Circle((x + 4.5, y + 18.5), 1.6, facecolor="#1E8449", edgecolor="none"))
        ax.text(x + 4.5, y + 18.5, "QC", ha="center", va="center", fontsize=5.5, color="white", fontweight="bold")
        ax.text(x + 8, y + 18.5, qc, ha="left", va="center", fontsize=8.5, color="#1C2833")
        # Adapt marker
        ax.add_patch(Circle((x + 4.5, y + 9.5), 1.6, facecolor="#2874A6", edgecolor="none"))
        ax.text(x + 4.5, y + 9.5, "A", ha="center", va="center", fontsize=6, color="white", fontweight="bold")
        ax.text(x + 8, y + 9.5, adapt, ha="left", va="center", fontsize=8.5, color="#1C2833")

    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, bbox_inches=None)
    fig.savefig(path.with_suffix(".png"), dpi=160, bbox_inches=None)
    plt.close(fig)


def draw_intrinsics(path: Path) -> None:
    """(a) pipeline (b) measurements (c) ridge proxy."""
    fig = plt.figure(figsize=(702 * PT, 240 * PT), dpi=150)
    ax = fig.add_axes([0.02, 0.06, 0.96, 0.88])
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 30)
    ax.axis("off")

    depth = _load_rgb(ANCHOR / "depth_map_viridis.png")
    lines = _load_rgb(ANCHOR / "detected_lines.png")
    seg = _load_rgb(ANCHOR / "segmentation_results.png")

    # (a) Parameterised pipeline
    _box(ax, (1.5, 4), 32, 22, fc="#EEF5FB", ec="#1A5276", lw=1.3)
    ax.text(17.5, 24.2, "(a) Parameterised pipeline", ha="center", fontsize=9, fontweight="bold", color="#1A5276")
    thumbs = [(depth, "3D→2D\nprojection"), (lines, "2D\nsegmentation"), (seg, "2D→3D\nre-projection")]
    for i, (img, lab) in enumerate(thumbs):
        x0 = 3.2 + i * 10.0
        ax.imshow(img, extent=(x0, x0 + 8.2, 11.5, 21.5), aspect="auto", zorder=2)
        ax.add_patch(Rectangle((x0, 11.5), 8.2, 10.0, fill=False, ec="#1A5276", lw=0.7, zorder=3))
        ax.text(x0 + 4.1, 9.2, lab, ha="center", va="center", fontsize=6.5, color="#1C2833")
        if i < 2:
            _arrow(ax, (x0 + 8.4, 16.5), (x0 + 9.8, 16.5))
    ax.text(17.5, 5.8, "Bayesian exploration of parameters", ha="center", fontsize=7, color="#5D6D7E")

    _arrow(ax, (34.2, 15), (37.5, 15))

    # (b) Intrinsic measurements
    _box(ax, (38, 4), 28, 22, fc="#F5EEF8", ec="#6C3483", lw=1.3)
    ax.text(52, 24.2, "(b) Intrinsic measurements", ha="center", fontsize=9, fontweight="bold", color="#6C3483")
    pq = [
        "depth NaN ratio",
        "ring-count error",
    ]
    sc = [
        "joint correspondence",
        "SAM fill rate",
    ]
    ax.text(45.5, 20.5, "PQ (preprocessing)", ha="center", fontsize=7.5, fontweight="bold", color="#1A5276")
    for i, t in enumerate(pq):
        _box(ax, (40.0, 16.6 - i * 3.4), 11, 2.8, fc="#D6EAF8", ec="#2874A6", lw=0.8, r=0.04)
        ax.text(45.5, 18.0 - i * 3.4, t, ha="center", va="center", fontsize=6.5)
    ax.text(58.5, 20.5, "SC (structure)", ha="center", fontsize=7.5, fontweight="bold", color="#117A65")
    for i, t in enumerate(sc):
        _box(ax, (53.0, 16.6 - i * 3.4), 11, 2.8, fc="#D5F5E3", ec="#117A65", lw=0.8, r=0.04)
        ax.text(58.5, 18.0 - i * 3.4, t, ha="center", va="center", fontsize=6.5)
    ax.text(52, 6.0, "four frozen deployment measurements", ha="center", fontsize=6.5, color="#5D6D7E")

    _arrow(ax, (66.5, 15), (69.5, 15))

    # (c) Proxy training
    _box(ax, (70, 4), 28, 22, fc="#FEF9E7", ec="#B7950B", lw=1.3)
    ax.text(84, 24.2, "(c) Proxy training", ha="center", fontsize=9, fontweight="bold", color="#9A7D0A")
    # scatter + ridge line
    rng = np.random.default_rng(0)
    xs = np.linspace(0.15, 0.9, 40)
    ys = 0.08 + 0.85 * xs + rng.normal(0, 0.05, size=xs.size)
    ax.scatter(72.5 + xs * 12, 8.5 + ys * 12, s=8, c="#2874A6", alpha=0.75, zorder=2)
    ax.plot([72.5 + 0.15 * 12, 72.5 + 0.9 * 12], [8.5 + 0.2 * 12, 8.5 + 0.85 * 12], color="#C0392B", lw=1.4, zorder=3)
    ax.text(78.5, 21.2, "Ridge regression", ha="center", fontsize=7.5, color="#1C2833")
    ax.text(90.5, 15.5, "Proxy ≈ mIoU", ha="center", va="center", fontsize=9, fontweight="bold", color="#1C2833")
    ax.text(84, 5.8, "frozen before evaluation", ha="center", fontsize=6.5, color="#5D6D7E")

    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, bbox_inches=None)
    fig.savefig(path.with_suffix(".png"), dpi=160, bbox_inches=None)
    plt.close(fig)


def draw_bp(path: Path) -> None:
    """(a) calibration sampling (b) proxy ablations as reported."""
    fig = plt.figure(figsize=(700 * PT, 287 * PT), dpi=150)
    ax = fig.add_axes([0.02, 0.06, 0.96, 0.88])
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 36)
    ax.axis("off")

    # (a)
    _box(ax, (1.5, 3), 48, 30, fc="#EEF5FB", ec="#1A5276", lw=1.3)
    ax.text(25.5, 31.2, "(a) Bayesian exploration", ha="center", fontsize=10, fontweight="bold", color="#1A5276")
    ax.text(25.5, 28.6, "40 valid trials / family  ·  32 Sobol + 8 GP-uncertainty", ha="center", fontsize=7, color="#5D6D7E")

    # Use three crops from the quality-levels composite if present; else anchor thumbs.
    if QL.exists():
        ql = _load_rgb(QL)
        h, w = ql.shape[:2]
        # Approximate three row crops from the 3-row figure (skip title band ~8%).
        top = int(0.10 * h)
        usable = h - top
        row_h = usable // 3
        # Left half is depth maps.
        crops = []
        labels = ["mIoU 0.82", "mIoU 0.55", "mIoU 0.04"]
        for i in range(3):
            y0 = top + i * row_h
            y1 = y0 + int(0.85 * row_h)
            x0 = int(0.18 * w)
            x1 = int(0.48 * w)
            crops.append(ql[y0:y1, x0:x1])
    else:
        crops = [
            _load_rgb(ANCHOR / "depth_map_viridis.png"),
            _load_rgb(ANCHOR / "detected_lines.png"),
            _load_rgb(ANCHOR / "segmentation_results.png"),
        ]
        labels = ["high", "mid", "low"]

    for i, (img, lab) in enumerate(zip(crops, labels)):
        x0 = 4.5 + i * 14.5
        ax.imshow(img, extent=(x0, x0 + 12.5, 8.5, 26.5), aspect="auto", zorder=2)
        ax.add_patch(Rectangle((x0, 8.5), 12.5, 18.0, fill=False, ec="#1A5276", lw=0.8, zorder=3))
        ax.text(x0 + 6.25, 6.5, lab, ha="center", fontsize=8, color="#1C2833")
    ax.text(25.5, 4.2, "same development scan; parameter variation only", ha="center", fontsize=6.5, color="#5D6D7E")

    _arrow(ax, (50.2, 18), (54.0, 18), lw=1.6)
    ax.text(52.1, 20.2, "trains", ha="center", fontsize=7, color="#5D6D7E")

    # (b)
    _box(ax, (54.5, 3), 44, 30, fc="#FEF9E7", ec="#B7950B", lw=1.3)
    ax.text(76.5, 31.2, "(b) Proxy ablations", ha="center", fontsize=10, fontweight="bold", color="#9A7D0A")

    rows = [
        ("PQ-only", 0.224, 0.72),
        ("SC-only", 0.140, 0.81),
        ("PQ+SC (10)", 0.197, 0.79),
        ("Compact-4", 0.112, 0.83),
    ]
    ax.text(58.5, 27.5, "feature set", ha="left", fontsize=7, color="#5D6D7E")
    ax.text(78.0, 27.5, "LOFO MAE", ha="center", fontsize=7, color="#5D6D7E")
    ax.text(90.5, 27.5, "ρ", ha="center", fontsize=7, color="#5D6D7E")
    for i, (name, mae, rho) in enumerate(rows):
        y = 23.5 - i * 4.6
        fc = "#D5F5E3" if name == "Compact-4" else "#FCF3CF"
        ec = "#117A65" if name == "Compact-4" else "#B7950B"
        lw = 1.1 if name == "Compact-4" else 0.8
        _box(ax, (57.0, y - 1.5), 39.5, 3.6, fc=fc, ec=ec, lw=lw, r=0.03)
        ax.text(58.5, y + 0.3, name, ha="left", va="center", fontsize=8.5, fontweight="bold" if name == "Compact-4" else "normal")
        ax.text(78.0, y + 0.3, f"{mae:.3f}", ha="center", va="center", fontsize=8.5)
        ax.text(90.5, y + 0.3, f"{rho:.2f}", ha="center", va="center", fontsize=8.5)
    ax.text(
        76.5,
        4.4,
        "deployed: Compact-4  (depth NaN, ring-count, correspondence, fill)",
        ha="center",
        fontsize=6.5,
        color="#1C2833",
    )

    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, bbox_inches=None)
    fig.savefig(path.with_suffix(".png"), dpi=160, bbox_inches=None)
    plt.close(fig)


def main() -> None:
    _style()
    OUT.mkdir(parents=True, exist_ok=True)
    draw_position(OUT / "position.pdf")
    draw_intrinsics(OUT / "intrinsics.pdf")
    draw_bp(OUT / "b-p.pdf")
    print(f"wrote {OUT}/{{position,intrinsics,b-p}}.{{pdf,png}}")


if __name__ == "__main__":
    main()
