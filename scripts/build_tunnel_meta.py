#!/usr/bin/env python3
"""Derive one drive-direction vector per parent tunnel.

This is the only place the Seg2Tunnel ring-index column is read for
orientation. The output, data/subsets/tunnel_meta.json, is project metadata:
stages 1-5 consume the vector and do not read the ring column.

Direction convention matches the former canonical_orientation rule. For each
subset, short-edge centres of the XY bounding rectangle define a candidate
axis; the axis is flipped so that its projection correlates with the ring
index with the family sign (h_ring_sign +1 staggered/complex, -1 continuous).
That unit vector is the direction along which unfolded h must increase.

Subsets of one parent tunnel do not always share a coordinate frame (only
tunnel 3, cut from one scan, agrees). The file therefore stores one vector
per subset. A tunnel-level vector is written only when every pair agrees
(dot product >= 0.95).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from scipy.spatial import ConvexHull
from shapely.geometry import Polygon

REPO = Path(__file__).resolve().parents[1]
SUBSETS = REPO / "data" / "subsets"
OUT = SUBSETS / "tunnel_meta.json"

# Family frame: sign of corr(axis, ring) after which h increases the right way.
# Taken from anchors/unified/params/{2-1,3-1-1,5-1} h_ring_sign.
H_RING_SIGN = {"1": 1, "2": 1, "3": -1, "4": 1, "5": 1}
GEOMETRY = {
    "1": {"inner_diameter_m": 5.5, "ring_length_m": 1.2},
    "2": {"inner_diameter_m": 5.5, "ring_length_m": 1.2},
    "3": {"inner_diameter_m": 5.9, "ring_length_m": 1.2},
    "4": {"inner_diameter_m": 7.5, "ring_length_m": 1.8},
    "5": {"inner_diameter_m": 7.5, "ring_length_m": 1.8},
}
MIN_DOT = 0.95
MAX_POINTS = 120_000


def _load_xy_ring(path: Path) -> tuple[np.ndarray, np.ndarray, int]:
    """Stride-sample x, y, ring. Returns (xy, ring, stride)."""
    n = 0
    with path.open("rb") as fh:
        for _ in fh:
            n += 1
    stride = max(1, n // MAX_POINTS)
    xs: list[float] = []
    ys: list[float] = []
    rings: list[float] = []
    with path.open("rb") as fh:
        for i, line in enumerate(fh):
            if i % stride:
                continue
            parts = line.split()
            xs.append(float(parts[0]))
            ys.append(float(parts[1]))
            rings.append(float(parts[5]))
    xy = np.column_stack((xs, ys))
    return xy, np.asarray(rings, dtype=float), stride


def _short_edge_centers(xy: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    hull = ConvexHull(xy)
    poly = Polygon(xy[hull.vertices])
    rect = np.array(poly.minimum_rotated_rectangle.exterior.coords)[:-1]
    edges = [float(np.linalg.norm(rect[i] - rect[(i + 1) % 4])) for i in range(4)]
    i = int(np.argmin(edges))
    c1 = (rect[i] + rect[(i + 1) % 4]) / 2
    c2 = (rect[(i + 2) % 4] + rect[(i + 3) % 4]) / 2
    return c1, c2


def drive_direction(xy: np.ndarray, ring: np.ndarray, h_ring_sign: int) -> np.ndarray:
    """Unit XY direction along which unfolded h must increase."""
    c1, c2 = _short_edge_centers(xy)
    axis = c2 - c1
    proj = (xy - c1) @ axis
    corr = float(np.corrcoef(proj, ring)[0, 1])
    if not np.isfinite(corr):
        raise RuntimeError(f"non-finite ring correlation (sign {h_ring_sign})")
    if corr * h_ring_sign < 0:
        axis = -axis
    norm = float(np.linalg.norm(axis))
    if norm == 0:
        raise RuntimeError("zero axis")
    return axis / norm


def main() -> None:
    by_tunnel: dict[str, list[tuple[str, np.ndarray]]] = {}
    for meta_path in sorted(SUBSETS.glob("*_rings_meta.json")):
        subset = json.loads(meta_path.read_text(encoding="utf-8"))["tunnel_id"]
        txt = SUBSETS / f"{subset}.txt"
        if not txt.exists():
            raise SystemExit(f"missing point cloud for {subset}")
        tunnel = subset.split("-")[0]
        print(f"reading {subset} ...", flush=True)
        xy, ring, stride = _load_xy_ring(txt)
        vec = drive_direction(xy, ring, H_RING_SIGN[tunnel])
        print(f"  {subset}: n={len(ring)} stride={stride} dir=({vec[0]:+.4f},{vec[1]:+.4f})", flush=True)
        by_tunnel.setdefault(tunnel, []).append((subset, vec))

    out: dict[str, dict] = {}
    for tunnel in sorted(by_tunnel, key=int):
        items = by_tunnel[tunnel]
        vecs = np.stack([v for _, v in items])
        dots = vecs @ vecs.T
        iu = np.triu_indices(len(items), k=1)
        min_dot = float(dots[iu].min()) if len(items) > 1 else 1.0
        shared = min_dot >= MIN_DOT
        if shared:
            mean = vecs.mean(axis=0)
            mean = mean / np.linalg.norm(mean)
        else:
            mean = None
        geom = GEOMETRY[tunnel]
        subsets = {
            sid: [round(float(v[0]), 8), round(float(v[1]), 8)]
            for sid, v in items
        }
        out[tunnel] = {
            "h_axis_direction_xy": (
                [round(float(mean[0]), 8), round(float(mean[1]), 8)] if mean is not None else None
            ),
            "frame": "shared" if shared else "per-subset",
            "ring_length_m": geom["ring_length_m"],
            "inner_diameter_m": geom["inner_diameter_m"],
            "n_subsets": len(items),
            "min_pairwise_dot": round(min_dot, 6),
            "subsets": subsets,
            "source": (
                "Derived once from the Seg2Tunnel ring-index column using "
                "stage-1 short-edge centres and "
                f"h_ring_sign={H_RING_SIGN[tunnel]:+d}. "
                + (
                    "Subsets share a frame; h_axis_direction_xy is their mean."
                    if shared
                    else (
                        "Subset headings disagree, so each subset keeps its own "
                        "vector (h_axis_direction_xy is null)."
                    )
                )
                + " Thereafter these vectors are project metadata; stages 1-5 "
                "do not read the ring column."
            ),
        }
        print(
            f"tunnel {tunnel}: frame={out[tunnel]['frame']} "
            f"min_dot={min_dot:.4f} n={len(items)}"
        )

    OUT.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    sys.exit(main() or 0)
