"""Overlay PNG: depth map + label-map boundaries + typed joint lines, with matched
(within delta) vs unmatched pixels coloured, for eyeballing correspondence."""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))
from bo.sc_general.features import block_boundaries, edt, raster_segments  # noqa: E402
from bo.sc_general.label_map import LabelMap  # noqa: E402
from bo.sc_general.replay import LineSet  # noqa: E402


def render_overlay(run_dir: Path, ls: LineSet, lm: LabelMap, out_png: Path, *, delta: int = 15,
                   title: str = "", downsample: int = 2) -> None:
    depth = np.load(Path(run_dir) / "depth_map.npy")
    H, W = depth.shape
    bnd = block_boundaries(lm)
    bb_y = bnd["bb_y"]
    obl = np.vstack([ls.oblique_pos, ls.oblique_neg]) if (len(ls.oblique_pos) + len(ls.oblique_neg)) else np.zeros((0, 4))
    r_obl = raster_segments(obl, (H, W)) if len(obl) else np.zeros((H, W), bool)
    r_hor = raster_segments(ls.horizontal, (H, W)) if len(ls.horizontal) else np.zeros((H, W), bool)
    r_all = r_obl | r_hor
    d_bnd = edt(bb_y)
    d_line = edt(r_all)

    # thicken for visibility
    import cv2

    k = np.ones((5, 5), np.uint8)
    def th(m):
        return cv2.dilate(m.astype(np.uint8), k, iterations=1).astype(bool)

    bnd_ok = th(bb_y & (d_line <= delta))
    bnd_bad = th(bb_y & (d_line > delta))
    line_ok = th(r_all & (d_bnd <= delta))
    line_bad = th(r_all & (d_bnd > delta))

    fig, axes = plt.subplots(1, 2, figsize=(14, 14 * H / W / 2 + 1))
    s = slice(None, None, downsample)
    vmin, vmax = np.nanpercentile(depth, [2, 98])
    for ax in axes:
        ax.imshow(depth[s, s], cmap="gray", vmin=vmin, vmax=vmax)
        ax.set_xticks([]); ax.set_yticks([])

    # left: label map + boundaries coloured by support
    lab = np.where(lm.label > 0, lm.label, np.nan)
    axes[0].imshow(lab[s, s], cmap="tab10", alpha=0.35, vmin=0, vmax=9, interpolation="nearest")
    rgba = np.zeros((*bb_y[s, s].shape, 4))
    rgba[bnd_ok[s, s]] = (0.0, 1.0, 0.0, 1.0)
    rgba[bnd_bad[s, s]] = (1.0, 0.0, 0.0, 1.0)
    axes[0].imshow(rgba, interpolation="nearest")
    axes[0].set_title(f"label boundaries: green = within {delta}px of a line, red = unsupported")

    # right: lines coloured by whether a boundary explains them
    rgba = np.zeros((*bb_y[s, s].shape, 4))
    rgba[line_ok[s, s]] = (0.0, 1.0, 1.0, 1.0)
    rgba[line_bad[s, s]] = (1.0, 0.5, 0.0, 1.0)
    axes[1].imshow(rgba, interpolation="nearest")
    if ls.prompts is not None and not ls.prompts.empty:
        real = ~ls.prompts["Type"].isin(["assume", "propagated"])
        axes[1].scatter(ls.prompts["X"][real] / downsample, ls.prompts["Y"][real] / downsample, s=30, c="yellow", marker="*")
        axes[1].scatter(ls.prompts["X"][~real] / downsample, ls.prompts["Y"][~real] / downsample, s=30, c="magenta", marker="x")
    axes[1].set_title(f"joint lines: cyan = explained by a boundary, orange = not; * real prompt, x assumed")
    fig.suptitle(title or str(run_dir))
    fig.tight_layout()
    out_png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_png, dpi=110)
    plt.close(fig)
