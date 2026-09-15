"""Rebuild the 2-D segmentation label map of a frozen run on the depth-map grid.

Two routes:

* ``from_results_pkl``  - exact stage-5 composition (``5_sam.py`` 746-773) from
  the per-block SAM crops when ``results.pkl`` is populated (staggered and
  continuous runs).
* ``from_only_label``   - rasterise the reprojected per-point labels
  (``only_label.csv`` via ``pixel_to_point.pkl``) and fill small gaps by
  nearest-neighbour. This is the only route for the complex family, whose
  labels come from the geometric tiler (``results.pkl`` is empty), and it is
  what the GT evaluation actually scores, so it is the reference.

Both return ``LabelMap`` with ``label`` (0 = unassigned, >0 block label),
``ring`` (-1 = unknown) and ``known`` (pixels with direct evidence).
"""

from __future__ import annotations

import json
import pickle
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import cv2
import numpy as np
import pandas as pd
from scipy import ndimage

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))
from bo.sc_general.replay import find_params_dir, load_json  # noqa: E402

UNKNOWN_RING = -1


@dataclass
class LabelMap:
    label: np.ndarray  # int, 0 = background/unassigned, -1 = unknown (no evidence)
    ring: np.ndarray  # int, -1 unknown
    known: np.ndarray  # bool, pixels with direct evidence before fill
    source: str
    block_to_label: dict[str, int]
    segment_order: list[str]
    fill_dist_px: float
    coverage_known: float  # fraction of grid pixels with direct evidence
    coverage_filled: float  # fraction after fill

    @property
    def label_to_block(self) -> dict[int, str]:
        return {v: k for k, v in self.block_to_label.items()}


# --------------------------------------------------------------------------- #
def load_sam_config(run_dir: Path, params_dir: Path | None = None) -> dict[str, Any]:
    params_dir = Path(params_dir) if params_dir else find_params_dir(run_dir)
    return load_json(params_dir / "parameters_sam.json")


def block_to_label_from_config(cfg: dict[str, Any]) -> tuple[dict[str, int], list[str]]:
    spr = int(cfg.get("segment_per_ring", 6))
    default = ["K", "B1"] + [f"A{i + 1}" for i in range(spr - 3)] + ["B2"]
    order = list(cfg.get("segment_order") or default)
    if "segment_order" in cfg and cfg.get("use_original_label_distributions"):
        b2l = {name: i + 1 for i, name in enumerate(order)}
    else:
        b2l = {name: i + 1 for i, name in enumerate(default)}
    return b2l, order


def depth_shape(run_dir: Path) -> tuple[int, int]:
    dm = np.load(Path(run_dir) / "depth_map.npy", mmap_mode="r")
    return int(dm.shape[0]), int(dm.shape[1])


# --------------------------------------------------------------------------- #
def _restore_logits(logits: np.ndarray, shape: tuple[int, int]) -> np.ndarray:
    """Approximate SAM ResizeLongestSide: scale 256x256 so the longest side
    equals max(h, w), then crop to (h, w). Bilinear."""
    h, w = shape
    target = max(h, w)
    resized = cv2.resize(logits.astype(np.float32), (target, target), interpolation=cv2.INTER_LINEAR)
    return resized[:h, :w]


def from_results_pkl(run_dir: Path, shape: tuple[int, int], b2l: dict[str, int]) -> tuple[np.ndarray, np.ndarray, list[float]] | None:
    path = Path(run_dir) / "results.pkl"
    if not path.exists():
        return None
    with path.open("rb") as fh:
        results = pickle.load(fh)
    if not results:
        return None
    H, W = shape
    logits_map = np.full((H, W), -np.inf, dtype=np.float32)
    label_map = np.zeros((H, W), dtype=np.int16)
    ring_map = np.full((H, W), UNKNOWN_RING, dtype=np.int16)
    scores: list[float] = []
    for ring_index, ring in enumerate(results):
        for item in ring:
            mask = np.asarray(item["mask"][0], dtype=bool)
            logits = np.asarray(item["logit"], dtype=np.float32)
            block = item["block"]
            if "score" in item:
                scores.append(float(np.asarray(item["score"]).ravel()[0]))
            sx, sy = map(int, item["left_top"])
            ey, ex = sy + mask.shape[0], sx + mask.shape[1]
            csy, csx = max(0, sy), max(0, sx)
            cey, cex = min(H, ey), min(W, ex)
            if cey <= csy or cex <= csx:
                continue
            new_logits = _restore_logits(logits, mask.shape)
            # crop to the valid window (original raises on mismatch; here we clip)
            my0, mx0 = csy - sy, csx - sx
            my1, mx1 = my0 + (cey - csy), mx0 + (cex - csx)
            m = mask[my0:my1, mx0:mx1]
            nl = new_logits[my0:my1, mx0:mx1]
            cur = logits_map[csy:cey, csx:cex]
            upd = (nl > cur) & m
            cur[upd] = nl[upd]
            label_map[csy:cey, csx:cex][upd] = b2l[block]
            ring_map[csy:cey, csx:cex][upd] = ring_index
    # Same remap the pipeline applies before reprojection (fix_ring), so ring ids
    # agree with only_label.csv::pred_rings.
    rc = len(results)
    assigned = ring_map >= 0
    ring_map[assigned] = (ring_map[assigned] + 1) % rc
    return label_map, ring_map, scores


# --------------------------------------------------------------------------- #
def _pixel_to_point_df(run_dir: Path) -> pd.DataFrame:
    with (Path(run_dir) / "pixel_to_point.pkl").open("rb") as fh:
        p2p = pickle.load(fh)
    if isinstance(p2p, pd.DataFrame):
        return p2p
    return pd.DataFrame(p2p)


def from_only_label(run_dir: Path, shape: tuple[int, int]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Sparse raster of the reprojected labels on the depth-map grid."""
    H, W = shape
    ol = pd.read_csv(Path(run_dir) / "only_label.csv", usecols=["pred_labels", "pred_rings"])
    p2p = _pixel_to_point_df(run_dir)
    y = p2p["pixel_y"].to_numpy(np.int64)
    x = p2p["pixel_x"].to_numpy(np.int64)
    idx = p2p["index"].to_numpy(np.int64)
    ok = (y >= 0) & (y < H) & (x >= 0) & (x < W) & (idx >= 0) & (idx < len(ol))
    y, x, idx = y[ok], x[ok], idx[ok]
    lab = ol["pred_labels"].to_numpy(np.int64)[idx]
    rng = ol["pred_rings"].to_numpy(np.int64)[idx]
    label = np.full((H, W), -1, dtype=np.int16)
    ring = np.full((H, W), UNKNOWN_RING, dtype=np.int16)
    # If several points share a pixel, the last write wins (consistent with
    # the pipeline's own pixel->point mapping being one-to-many but label-uniform).
    label[y, x] = lab
    ring[y, x] = rng
    known = label >= 0
    return label, ring, known


def fill_nearest(label: np.ndarray, ring: np.ndarray, known: np.ndarray, max_dist: float) -> tuple[np.ndarray, np.ndarray]:
    """Nearest-neighbour fill of unknown pixels within ``max_dist`` of evidence."""
    dist, (iy, ix) = ndimage.distance_transform_edt(~known, return_indices=True)
    fill = (~known) & (dist <= max_dist)
    out_l = label.copy()
    out_r = ring.copy()
    out_l[fill] = label[iy[fill], ix[fill]]
    out_r[fill] = ring[iy[fill], ix[fill]]
    return out_l, out_r


# --------------------------------------------------------------------------- #
def build_label_map(
    run_dir: Path,
    *,
    params_dir: Path | None = None,
    prefer: str = "auto",
    fill_dist_px: float = 25.0,
) -> LabelMap:
    """``prefer`` in {"auto", "results", "only_label"}."""
    run_dir = Path(run_dir)
    cfg = load_sam_config(run_dir, params_dir)
    b2l, order = block_to_label_from_config(cfg)
    shape = depth_shape(run_dir)

    if prefer in ("auto", "results"):
        res = from_results_pkl(run_dir, shape, b2l)
        if res is not None:
            label, ring, _scores = res
            known = label > 0
            return LabelMap(
                label=label, ring=ring, known=known, source="results.pkl",
                block_to_label=b2l, segment_order=order, fill_dist_px=0.0,
                coverage_known=float(known.mean()), coverage_filled=float(known.mean()),
            )
        if prefer == "results":
            raise FileNotFoundError(f"results.pkl empty/missing for {run_dir}")

    label, ring, known = from_only_label(run_dir, shape)
    cov_known = float(known.mean())
    if fill_dist_px > 0:
        label, ring = fill_nearest(label, ring, known, fill_dist_px)
    filled = label >= 0
    return LabelMap(
        label=label, ring=ring, known=known, source="only_label.csv",
        block_to_label=b2l, segment_order=order, fill_dist_px=fill_dist_px,
        coverage_known=cov_known, coverage_filled=float(filled.mean()),
    )


def sam_scores(run_dir: Path) -> list[float]:
    path = Path(run_dir) / "results.pkl"
    if not path.exists():
        return []
    with path.open("rb") as fh:
        results = pickle.load(fh)
    out = []
    for ring in results or []:
        for item in ring:
            if "score" in item:
                out.append(float(np.asarray(item["score"]).ravel()[0]))
    return out


def compare_routes(run_dir: Path, params_dir: Path | None = None) -> dict[str, Any]:
    """Agreement of the results.pkl composition with the reprojected labels at
    evidence pixels (the reprojection is what GT scoring sees)."""
    run_dir = Path(run_dir)
    dense = build_label_map(run_dir, params_dir=params_dir, prefer="results")
    sparse = build_label_map(run_dir, params_dir=params_dir, prefer="only_label", fill_dist_px=0)
    k = sparse.known
    agree = dense.label[k] == sparse.label[k]
    # boundary agreement: distance from dense block boundaries to sparse-derived ones
    return {
        "n_known": int(k.sum()),
        "label_agreement": float(agree.mean()),
        "label_agreement_nonbg": float((dense.label[k] == sparse.label[k])[sparse.label[k] > 0].mean()),
        "ring_agreement": float((dense.ring[k] == sparse.ring[k]).mean()),
    }


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir")
    ap.add_argument("--compare", action="store_true")
    args = ap.parse_args()
    if args.compare:
        print(json.dumps(compare_routes(Path(args.run_dir)), indent=2))
    else:
        lm = build_label_map(Path(args.run_dir))
        print(lm.source, lm.label.shape, "known", round(lm.coverage_known, 4), "filled", round(lm.coverage_filled, 4),
              "labels", np.unique(lm.label[lm.label >= 0]).tolist(), "rings", np.unique(lm.ring[lm.ring >= 0]).tolist())
