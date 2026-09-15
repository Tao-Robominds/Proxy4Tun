"""Generic structure-coherence candidates from the line <-> label-map correspondence.

All features are GT-free and layout-free: they use the run's own replayed
detector geometry (``replay.LineSet``), its label map (``label_map.LabelMap``),
and the segment count / cyclic ``segment_order`` from the run's SAM config.
No K-row pattern, no family reference statistics.

Conventions: depth-map grid, ``x`` along the tunnel axis (rings), ``y`` around
the circumference. Joint lines (oblique K-joints, horizontal block joints) are
near-horizontal in this frame and are matched against label transitions along
``y``; ring boundaries are transitions along ``x``.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Iterable

import cv2
import numpy as np
from scipy import ndimage

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))
from bo.sc_general.label_map import LabelMap  # noqa: E402
from bo.sc_general.replay import LineSet  # noqa: E402

DELTAS: tuple[int, ...] = (8, 15, 25)
CHAMFER_CAP_PX = 200.0
MIN_COMPONENT_PX = 50
MIN_BLOCK_AREA_PX = 200


# --------------------------------------------------------------------------- #
# Geometry helpers
# --------------------------------------------------------------------------- #
def raster_segments(segs: np.ndarray, shape: tuple[int, int]) -> np.ndarray:
    canvas = np.zeros(shape, dtype=np.uint8)
    for x1, y1, x2, y2 in np.asarray(segs).reshape(-1, 4):
        cv2.line(canvas, (int(round(x1)), int(round(y1))), (int(round(x2)), int(round(y2))), 1, 1)
    return canvas.astype(bool)


def block_boundaries(lm: LabelMap) -> dict[str, np.ndarray]:
    """Boolean masks of label transitions.

    ``bb_y``: block-block transition along y within the same ring (both labels > 0,
              different) - circumferential joints.
    ``bb_x``: block-block transition along x - ring boundaries / vertical joints.
    ``bg_y``: block-background transition along y (mask edge against unassigned).
    """
    lab = lm.label
    rng = lm.ring
    valid = lab >= 0
    H, W = lab.shape
    bb_y = np.zeros((H, W), dtype=bool)
    bb_x = np.zeros((H, W), dtype=bool)
    bg_y = np.zeros((H, W), dtype=bool)
    a, b = lab[:-1, :], lab[1:, :]
    va, vb = valid[:-1, :], valid[1:, :]
    same_ring = rng[:-1, :] == rng[1:, :]
    diff = (a != b) & va & vb
    bb_y[:-1, :] = diff & (a > 0) & (b > 0) & same_ring
    bg_y[:-1, :] = diff & ((a == 0) ^ (b == 0))
    a, b = lab[:, :-1], lab[:, 1:]
    va, vb = valid[:, :-1], valid[:, 1:]
    diff = (a != b) & va & vb
    bb_x[:, :-1] = diff & (a > 0) & (b > 0)
    return {"bb_y": bb_y, "bb_x": bb_x, "bg_y": bg_y}


def edt(mask: np.ndarray) -> np.ndarray:
    """Distance (px) from each pixel to the nearest True pixel of ``mask``."""
    if not mask.any():
        return np.full(mask.shape, np.inf, dtype=np.float32)
    return ndimage.distance_transform_edt(~mask).astype(np.float32)


def _frac_within(dist: np.ndarray, at: np.ndarray, delta: float) -> float:
    if not at.any():
        return float("nan")
    return float(np.mean(dist[at] <= delta))


def _hm(a: float, b: float) -> float:
    if not (np.isfinite(a) and np.isfinite(b)) or (a + b) <= 0:
        return 0.0
    return float(2 * a * b / (a + b))


# --------------------------------------------------------------------------- #
# Correspondence features
# --------------------------------------------------------------------------- #
def correspondence_features(ls: LineSet, lm: LabelMap, deltas: Iterable[int] = DELTAS) -> dict[str, float]:
    shape = lm.label.shape
    out: dict[str, float] = {}
    bnd = block_boundaries(lm)
    bb_y = bnd["bb_y"]
    n_bnd = int(bb_y.sum())

    obl = np.vstack([ls.oblique_pos, ls.oblique_neg]) if (len(ls.oblique_pos) + len(ls.oblique_neg)) else np.zeros((0, 4))
    hor = ls.horizontal
    r_obl = raster_segments(obl, shape) if len(obl) else np.zeros(shape, bool)
    r_hor = raster_segments(hor, shape) if len(hor) else np.zeros(shape, bool)
    r_all = r_obl | r_hor
    n_line = int(r_all.sum())

    out["n_oblique_lines"] = float(len(obl))
    out["n_horizontal_lines"] = float(len(hor))
    out["line_px"] = float(n_line)
    out["boundary_px"] = float(n_bnd)
    out["boundary_bg_px"] = float(bnd["bg_y"].sum())
    out["boundary_ring_px"] = float(bnd["bb_x"].sum())

    d_bnd = edt(bb_y)  # distance to nearest joint boundary
    d_line = edt(r_all)  # distance to nearest joint line
    edge = ls.dilated.astype(bool) if ls.dilated is not None else None
    d_edge = edt(edge) if edge is not None else None

    for d in deltas:
        le_all = _frac_within(d_bnd, r_all, d)
        le_obl = _frac_within(d_bnd, r_obl, d)
        le_hor = _frac_within(d_bnd, r_hor, d)
        be_line = _frac_within(d_line, bb_y, d)
        be_edge = _frac_within(d_edge, bb_y, d) if d_edge is not None else float("nan")
        # no lines -> nothing is explained (0), not NaN: absence of evidence is a failure signal
        le_all0 = 0.0 if not np.isfinite(le_all) else le_all
        be_line0 = 0.0 if not np.isfinite(be_line) else be_line
        out[f"line_explained@{d}"] = le_all0
        out[f"line_explained_obl@{d}"] = 0.0 if not np.isfinite(le_obl) else le_obl
        out[f"line_explained_hor@{d}"] = 0.0 if not np.isfinite(le_hor) else le_hor
        out[f"boundary_explained_line@{d}"] = be_line0
        out[f"boundary_explained_edge@{d}"] = 0.0 if not np.isfinite(be_edge) else be_edge
        out[f"correspondence_f1@{d}"] = _hm(le_all0, be_line0)

    # Delta-free: symmetric Chamfer (capped) between line pixels and joint boundaries
    if n_line and n_bnd:
        c1 = float(np.mean(np.minimum(d_bnd[r_all], CHAMFER_CAP_PX)))
        c2 = float(np.mean(np.minimum(d_line[bb_y], CHAMFER_CAP_PX)))
        out["chamfer_line_to_bnd_px"] = c1
        out["chamfer_bnd_to_line_px"] = c2
        out["chamfer_sym_px"] = 0.5 * (c1 + c2)
        out["chamfer_median_line_to_bnd_px"] = float(np.median(np.minimum(d_bnd[r_all], CHAMFER_CAP_PX)))
    else:
        out["chamfer_line_to_bnd_px"] = CHAMFER_CAP_PX
        out["chamfer_bnd_to_line_px"] = CHAMFER_CAP_PX
        out["chamfer_sym_px"] = CHAMFER_CAP_PX
        out["chamfer_median_line_to_bnd_px"] = CHAMFER_CAP_PX

    # Boundary support by raw edge evidence, delta-free
    if d_edge is not None and n_bnd:
        out["bnd_edge_dist_mean_px"] = float(np.mean(np.minimum(d_edge[bb_y], CHAMFER_CAP_PX)))
    else:
        out["bnd_edge_dist_mean_px"] = CHAMFER_CAP_PX

    out.update(prompt_features(ls, lm))
    out.update(transition_validity(lm, bb_y))
    return out


def prompt_features(ls: LineSet, lm: LabelMap) -> dict[str, float]:
    """Does the K mask contain the prompt that generated it?"""
    out = {"prompt_k_hit": float("nan"), "prompt_k_hit_real": float("nan"), "prompt_real_frac": float("nan"),
           "prompt_block_hit": float("nan")}
    if ls.prompts is None or ls.prompts.empty:
        return out
    k_label = lm.block_to_label.get("K", 1)
    H, W = lm.label.shape
    xs = np.clip(np.round(ls.prompts["X"].to_numpy(float)).astype(int), 0, W - 1)
    ys = np.clip(np.round(ls.prompts["Y"].to_numpy(float)).astype(int), 0, H - 1)
    labs = lm.label[ys, xs]
    real = ~ls.prompts["Type"].isin(["assume", "propagated"]).to_numpy()
    out["prompt_k_hit"] = float(np.mean(labs == k_label))
    out["prompt_block_hit"] = float(np.mean(labs > 0))
    out["prompt_real_frac"] = float(np.mean(real))
    out["prompt_k_hit_real"] = float(np.mean(labs[real] == k_label)) if real.any() else 0.0
    return out


def transition_validity(lm: LabelMap, bb_y: np.ndarray) -> dict[str, float]:
    """Fraction of joint-boundary pixels whose two labels are cyclic neighbours
    in segment_order (order only; no positions)."""
    order = lm.segment_order
    b2l = lm.block_to_label
    n = len(order)
    valid_pairs = set()
    for i, name in enumerate(order):
        nxt = order[(i + 1) % n]
        a, b = b2l.get(name), b2l.get(nxt)
        if a is not None and b is not None:
            valid_pairs.add((a, b))
            valid_pairs.add((b, a))
    ys, xs = np.nonzero(bb_y)
    if len(ys) == 0:
        return {"transition_valid_frac": 0.0, "transition_pairs": 0.0}
    a = lm.label[ys, xs]
    b = lm.label[ys + 1, xs]
    ok = np.fromiter(((int(u), int(v)) in valid_pairs for u, v in zip(a, b)), dtype=bool, count=len(a))
    # distinct label pairs seen (order-insensitive)
    pairs = {tuple(sorted((int(u), int(v)))) for u, v in zip(a, b)}
    return {"transition_valid_frac": float(ok.mean()), "transition_pairs": float(len(pairs))}


# --------------------------------------------------------------------------- #
# Label-map regularity (no line input)
# --------------------------------------------------------------------------- #
def regularity_features(lm: LabelMap, ring_count: int) -> dict[str, float]:
    lab, ring = lm.label, lm.ring
    C = len(lm.segment_order)
    labels = sorted(v for v in lm.block_to_label.values())
    out: dict[str, float] = {}

    completeness, frag, rect, heights = [], [], [], []
    ring_ids = [int(r) for r in np.unique(ring[ring >= 0])]
    # crop every per-ring operation to the ring's bounding box
    ring_slices = ndimage.find_objects(np.where(ring >= 0, ring + 1, 0).astype(np.int32))
    for r in ring_ids:
        sl = ring_slices[r] if r < len(ring_slices) else None
        if sl is None:
            continue
        rl, rr = lab[sl], ring[sl]
        rmask = rr == r
        cols = np.nonzero(rmask.any(axis=0))[0]
        if cols.size == 0:
            continue
        ring_w = float(cols.max() - cols.min() + 1)
        present = 0
        hvec = []
        for l in labels:
            m = rmask & (rl == l)
            area = int(m.sum())
            if area < MIN_BLOCK_AREA_PX:
                hvec.append(0.0)
                continue
            present += 1
            n_cc, cc = cv2.connectedComponents(m.astype(np.uint8), connectivity=8)
            sizes = np.bincount(cc.ravel())[1:]
            n_big = int(np.sum(sizes >= MIN_COMPONENT_PX))
            frag.append(max(n_big - 1, 0))
            ys, xs = np.nonzero(m)
            bbox = float((ys.max() - ys.min() + 1) * (xs.max() - xs.min() + 1))
            rect.append(area / bbox if bbox > 0 else 0.0)
            hvec.append(area / ring_w)  # effective circumferential height
        completeness.append(present / C)
        heights.append(sorted(hvec))

    out["ring_label_completeness"] = float(np.mean([c == 1.0 for c in completeness])) if completeness else 0.0
    out["ring_label_presence"] = float(np.mean(completeness)) if completeness else 0.0
    out["mask_fragmentation"] = float(np.mean(frag)) if frag else float("nan")
    out["mask_rectangularity"] = float(np.mean(rect)) if rect else 0.0
    if len(heights) >= 2:
        Hm = np.asarray(heights, dtype=float)
        mu = Hm.mean(axis=0)
        sd = Hm.std(axis=0)
        cv = np.where(mu > 0, sd / np.maximum(mu, 1e-9), 0.0)
        out["block_height_dispersion"] = float(np.mean(cv))
    else:
        out["block_height_dispersion"] = float("nan")
    out["n_rings_labelled"] = float(len(ring_ids))
    out["rings_expected"] = float(ring_count)

    # boundary straightness of joint boundaries
    bb_y = block_boundaries(lm)["bb_y"]
    out["boundary_straightness_px"] = boundary_straightness(bb_y)
    return out


def boundary_straightness(bb_y: np.ndarray, min_len: int = 60) -> float:
    """Length-weighted RMS perpendicular residual of each joint-boundary
    component to its best-fit line (vectorised via per-component 2x2 covariance)."""
    if not bb_y.any():
        return float("nan")
    # join 1-px gaps so an oblique staircase forms one component
    k = np.ones((3, 3), np.uint8)
    thick = cv2.dilate(bb_y.astype(np.uint8), k, iterations=1)
    n, cc = cv2.connectedComponents(thick, connectivity=8)
    ys, xs = np.nonzero(bb_y)
    ids = cc[ys, xs].astype(np.int64)
    cnt = np.bincount(ids, minlength=n).astype(float)
    sx = np.bincount(ids, weights=xs, minlength=n)
    sy = np.bincount(ids, weights=ys, minlength=n)
    sxx = np.bincount(ids, weights=xs.astype(float) ** 2, minlength=n)
    syy = np.bincount(ids, weights=ys.astype(float) ** 2, minlength=n)
    sxy = np.bincount(ids, weights=xs.astype(float) * ys, minlength=n)
    keep = cnt >= min_len
    keep[0] = False
    if not keep.any():
        return float("nan")
    c = cnt[keep]
    mx, my = sx[keep] / c, sy[keep] / c
    vxx = sxx[keep] / c - mx ** 2
    vyy = syy[keep] / c - my ** 2
    vxy = sxy[keep] / c - mx * my
    # smallest eigenvalue of the 2x2 covariance = mean squared perpendicular residual
    tr = vxx + vyy
    det = vxx * vyy - vxy ** 2
    lam_min = np.maximum(tr / 2 - np.sqrt(np.maximum(tr ** 2 / 4 - det, 0.0)), 0.0)
    rms = np.sqrt(lam_min)
    return float(np.average(rms, weights=c))


# --------------------------------------------------------------------------- #
def all_features(ls: LineSet, lm: LabelMap, *, ring_count: int, sam_scores: list[float] | None = None,
                 deltas: Iterable[int] = DELTAS) -> dict[str, Any]:
    out: dict[str, Any] = {}
    out.update(correspondence_features(ls, lm, deltas))
    out.update(regularity_features(lm, ring_count))
    if sam_scores:
        s = np.asarray(sam_scores, float)
        out["sam_score_mean"] = float(s.mean())
        out["sam_score_min"] = float(s.min())
        out["sam_score_p10"] = float(np.percentile(s, 10))
    else:
        out["sam_score_mean"] = float("nan")
        out["sam_score_min"] = float("nan")
        out["sam_score_p10"] = float("nan")
    out["labelmap_source"] = lm.source
    out["labelmap_coverage_known"] = lm.coverage_known
    out["labelmap_coverage_filled"] = lm.coverage_filled
    out["vertical_fallback"] = float(ls.vertical_fallback)
    return out
