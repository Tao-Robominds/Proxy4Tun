"""Deterministic offline replay of the stage-4 line detector.

Port of ``anchors/unified/4_detection.py`` (lines 95-495) as pure functions.
Inputs are the frozen run artefacts (``depth_map_outlier.npy``) and the run's
own ``parameters_detecting.json``; outputs are typed line geometry instead of
the ``detected_lines.png`` visualisation. Nothing is written into the run dir.

OpenCV ``HoughLinesP`` seeds its internal RNG with a constant, so the replay is
bit-identical to the original run given the same inputs and parameters; the
gate verifies this against the stored ``initial_points.csv``.
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import cv2
import numpy as np
import pandas as pd

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))
from bo.elegant.features import ANCHOR_PARAMS  # noqa: E402

DEFAULT_RING_COUNT = 10
SHADOW_ROOT = _REPO / "data" / "sc-general" / "replay"


# --------------------------------------------------------------------------- #
# Parameter discovery
# --------------------------------------------------------------------------- #
def find_params_dir(run_dir: Path) -> Path:
    """Locate the per-run parameter directory for a frozen run.

    Layouts:
      <campaign>/runs/<run_id>/            -> <campaign>/params/<run_id>/
      <campaign>/round{N}/                  -> <campaign>/params/round{N}/ or <campaign>/params/
      data/anchors/<case>/                  -> anchors/unified/params/<case>/ (3-1 -> 3-1-1)
    """
    run_dir = Path(run_dir).resolve()
    if run_dir.parent.name == "runs":
        cand = run_dir.parent.parent / "params" / run_dir.name
        if cand.is_dir():
            return cand
    if run_dir.name.startswith("round"):
        for cand in (run_dir.parent / "params" / run_dir.name, run_dir.parent / "params"):
            if (cand / "parameters_detecting.json").exists():
                return cand
    if run_dir.parent.name == "anchors":
        case = run_dir.name
        if case in ANCHOR_PARAMS:
            return ANCHOR_PARAMS[case]
    # Last resort: params sitting next to the run
    if (run_dir / "parameters_detecting.json").exists():
        return run_dir
    raise FileNotFoundError(f"No parameters dir found for run {run_dir}")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


_SLICED_RE = re.compile(r"Number of sliced clouds:\s*(\d+)")


def find_log(run_dir: Path) -> Path | None:
    run_dir = Path(run_dir).resolve()
    cands = []
    if run_dir.parent.name == "runs":
        cands.append(run_dir.parent.parent / "logs" / f"{run_dir.name}.log")
    if run_dir.name.startswith("round"):
        cands += [run_dir.parent / "logs" / f"{run_dir.name}.log",
                  run_dir.parent / "logs" / f"{run_dir.parent.name}-{run_dir.name}.log"]
    cands += [run_dir / "pipeline.log", run_dir / f"{run_dir.name}.log"]
    for c in cands:
        if c.exists():
            return c
    logs = run_dir.parent / "logs"
    if logs.is_dir():
        hits = sorted(logs.glob(f"*{run_dir.name}*.log"))
        if hits:
            return hits[0]
    return None


def find_ring_count(run_dir: Path, *, allow_state: bool = True) -> tuple[int, str]:
    """Run's ring_count (stage-1 ``len(slicing_cloud)``), GT-free.

    Order: stage-1 log line -> state.pkl (slow, ~1 GB) -> default 10.
    """
    run_dir = Path(run_dir)
    log = find_log(run_dir)
    if log is not None:
        m = _SLICED_RE.search(log.read_text(encoding="utf-8", errors="ignore"))
        if m:
            return int(m.group(1)), f"log:{log}"
    if allow_state and (run_dir / "state.pkl").exists():
        import pickle

        with (run_dir / "state.pkl").open("rb") as fh:
            state = pickle.load(fh)
        rc = state.get("ring_count")
        if rc is not None:
            return int(rc), "state.pkl"
    return DEFAULT_RING_COUNT, "default"


# --------------------------------------------------------------------------- #
# Geometry containers
# --------------------------------------------------------------------------- #
@dataclass
class LineSet:
    """Typed detector output in depth-map pixel coordinates (x = along tunnel, y = circumference)."""

    shape: tuple[int, int]
    # HoughLinesP segments (x1, y1, x2, y2), already angle-filtered
    oblique_pos: np.ndarray = field(default_factory=lambda: np.zeros((0, 4)))
    oblique_neg: np.ndarray = field(default_factory=lambda: np.zeros((0, 4)))
    horizontal: np.ndarray = field(default_factory=lambda: np.zeros((0, 4)))
    # Raw (unfiltered by angle) segments, for diagnostics
    n_raw_oblique: int = 0
    n_raw_horizontal: int = 0
    # Merged near-vertical HoughLines as x positions (ring boundaries)
    vertical_x: np.ndarray = field(default_factory=lambda: np.zeros(0))
    # Ring-centre lines used for prompting: x positions + real flag
    mid_x: np.ndarray = field(default_factory=lambda: np.zeros(0))
    mid_real: np.ndarray = field(default_factory=lambda: np.zeros(0, dtype=bool))
    avg_ring_px: float = float("nan")
    vertical_fallback: bool = False
    # Edge evidence used by the detector
    binary: np.ndarray | None = None
    dilated: np.ndarray | None = None
    # Prompt points as produced by the detector logic
    prompts: pd.DataFrame | None = None
    ring_count: int = DEFAULT_RING_COUNT
    ring_count_source: str = "default"

    def joint_segments(self) -> np.ndarray:
        parts = [a for a in (self.oblique_pos, self.oblique_neg, self.horizontal) if len(a)]
        return np.vstack(parts) if parts else np.zeros((0, 4))

    def to_json(self) -> dict[str, Any]:
        return {
            "shape": list(self.shape),
            "oblique_pos": self.oblique_pos.tolist(),
            "oblique_neg": self.oblique_neg.tolist(),
            "horizontal": self.horizontal.tolist(),
            "n_raw_oblique": self.n_raw_oblique,
            "n_raw_horizontal": self.n_raw_horizontal,
            "vertical_x": self.vertical_x.tolist(),
            "mid_x": self.mid_x.tolist(),
            "mid_real": self.mid_real.astype(int).tolist(),
            "avg_ring_px": self.avg_ring_px,
            "vertical_fallback": self.vertical_fallback,
            "prompts": None if self.prompts is None else self.prompts.to_dict(orient="records"),
        }


# --------------------------------------------------------------------------- #
# Stage-4 port
# --------------------------------------------------------------------------- #
def _seg(line: np.ndarray) -> tuple[int, int, int, int]:
    x1, y1, x2, y2 = (int(v) for v in line)
    return x1, y1, x2, y2


def replay_lines(
    depth_map_outlier: np.ndarray,
    params: dict[str, Any],
    *,
    ring_count: int = DEFAULT_RING_COUNT,
    keep_maps: bool = True,
) -> LineSet:
    """Lines 95-333 of 4_detection.py, returning geometry instead of a PNG."""
    p = params
    binary_map = np.where(np.isnan(depth_map_outlier), 0, 255).astype(np.uint8)
    _, binary_image = cv2.threshold(binary_map, p["binary_threshold"], 255, cv2.THRESH_BINARY)
    kernel = np.ones(tuple(p["morphological_kernel_size"]), np.uint8)
    dilated = cv2.dilate(binary_image, kernel, iterations=p["dilation_iterations"])
    L, W = binary_map.shape

    lines_oblique = cv2.HoughLinesP(
        dilated, 1, np.pi / 180, p["hough_threshold_oblique"],
        minLineLength=p["minLineLength_oblique"], maxLineGap=p["maxLineGap_oblique"],
    )
    lines_horizontal = cv2.HoughLinesP(
        dilated, 1, np.pi / 180, p["hough_threshold_horizontal"],
        minLineLength=p["minLineLength_horizontal"], maxLineGap=p["maxLineGap_horizontal"],
    )
    lines_vertical = cv2.HoughLines(dilated, 1, np.pi / 180, p["hough_threshold_vertical"])

    resolution = float(p["resolution"])
    vertical_rho_mode = p.get("vertical_rho_mode", "max")
    vertical_rho_spacing_mm = float(p.get("vertical_rho_spacing_mm", 1200))
    vertical_rho_min_factor = float(p.get("vertical_rho_min_factor", 0.0))
    vertical_rho_max_factor = float(p.get("vertical_rho_max_factor", 5.0))
    if lines_vertical is not None:
        rho = lines_vertical[:, 0, 0]
        scale = vertical_rho_spacing_mm / (resolution * 1000)
        if vertical_rho_mode == "w2_offset_band":
            lo = W / 2 + vertical_rho_min_factor * scale
            hi = W / 2 + vertical_rho_max_factor * scale
            filtered = lines_vertical[(rho >= lo) & (rho <= hi)]
            if len(filtered):
                lines_vertical = filtered
        elif vertical_rho_mode == "band":
            lo = vertical_rho_min_factor * scale
            hi = vertical_rho_max_factor * scale
            filtered = lines_vertical[(rho >= lo) & (rho <= hi)]
            if len(filtered):
                lines_vertical = filtered
        else:
            lines_vertical = lines_vertical[rho <= (vertical_rho_max_factor * scale)]

    out = LineSet(shape=(L, W))
    if keep_maps:
        out.binary = binary_image
        out.dilated = dilated

    pos_rng = p["angle_range_oblique_positive"]
    neg_rng = p["angle_range_oblique_negative"]
    pos, neg, hor = [], [], []
    if lines_oblique is not None:
        out.n_raw_oblique = len(lines_oblique)
        for line in lines_oblique:
            x1, y1, x2, y2 = line[0]
            x1, x2, y1, y2 = (x2, x1, y2, y1) if x1 > x2 else (x1, x2, y1, y2)
            angle = np.degrees(np.arctan2(-(y2 - y1), x2 - x1))
            if pos_rng[0] <= angle <= pos_rng[1]:
                pos.append((x1, y1, x2, y2))
            elif neg_rng[0] <= angle <= neg_rng[1]:
                neg.append((x1, y1, x2, y2))
    if lines_horizontal is not None:
        out.n_raw_horizontal = len(lines_horizontal)
        for line in lines_horizontal:
            x1, y1, x2, y2 = line[0]
            angle = np.degrees(np.arctan2(y2 - y1, x2 - x1))
            if -1 <= angle <= 1:
                hor.append((x1, y1, x2, y2))
    out.oblique_pos = np.asarray(pos, dtype=float).reshape(-1, 4)
    out.oblique_neg = np.asarray(neg, dtype=float).reshape(-1, 4)
    out.horizontal = np.asarray(hor, dtype=float).reshape(-1, 4)

    # Merge close vertical lines (rho, theta) -- exact port incl. running average
    merged_lines: list[tuple[float, float]] = []
    all_mid_lines: list[tuple[float, float]] = []
    threshold_distance = p["merge_distance"]
    avg_distance = float("nan")
    mid_real_x: list[float] = []
    if lines_vertical is not None:
        lv = lines_vertical[:, 0]
        for rho1, theta1 in lv:
            if -0.5 * np.pi / 180 <= abs(theta1) <= 0.5 * np.pi / 180:
                x1, y1 = rho1 * np.cos(theta1), rho1 * np.sin(theta1)
                is_merged = False
                for j, (rho2, theta2) in enumerate(merged_lines):
                    x2, y2 = rho2 * np.cos(theta2), rho2 * np.sin(theta2)
                    if np.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2) < threshold_distance:
                        merged_lines[j] = ((rho1 + rho2) / 2, (theta1 + theta2) / 2)
                        is_merged = True
                        break
                if not is_merged:
                    merged_lines.append((float(rho1), float(theta1)))
        merged_lines.sort(key=lambda line: line[0])

        mid_lines = []
        for i in range(len(merged_lines) - 1):
            rho1, theta1 = merged_lines[i]
            rho2, theta2 = merged_lines[i + 1]
            mid_lines.append(((rho1 + rho2) / 2, (theta1 + theta2) / 2))

        distances = []
        for i in range(len(mid_lines) - 1):
            rho1, theta1 = mid_lines[i]
            rho2, theta2 = mid_lines[i + 1]
            x1, y1 = rho1 * np.cos(theta1), rho1 * np.sin(theta1)
            x2, y2 = rho2 * np.cos(theta2), rho2 * np.sin(theta2)
            distances.append(np.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2))
        avg_distance_detected = np.mean(distances) if distances else 0
        avg_distance_designed = W / ring_count
        ring_px = p["ring_spacing_constant"] / resolution
        if abs(avg_distance_detected - ring_px) <= abs(avg_distance_designed - ring_px):
            avg_distance = avg_distance_detected
        else:
            avg_distance = avg_distance_designed

        all_mid_lines = mid_lines.copy()
        mid_real_x = [r * np.cos(t) for r, t in mid_lines]
        if mid_lines:
            leftmost_rho, leftmost_theta = mid_lines[0]
            a, b = np.cos(leftmost_theta), np.sin(leftmost_theta)
            x0 = a * leftmost_rho
            while x0 >= 0:
                all_mid_lines.append((x0, leftmost_theta))
                x0 -= avg_distance
            rightmost_rho, rightmost_theta = mid_lines[-1]
            a, b = np.cos(rightmost_theta), np.sin(rightmost_theta)
            x0 = a * rightmost_rho
            while x0 <= W:
                all_mid_lines.append((x0, rightmost_theta))
                x0 += avg_distance
        all_mid_lines = sorted(list(set(all_mid_lines)), key=lambda line: line[0])

    if lines_vertical is None or len(all_mid_lines) == 0:
        out.vertical_fallback = True
        all_mid_lines = []
        block_width = W / ring_count
        for i in range(ring_count):
            all_mid_lines.append(((i + 0.5) * block_width, 0))
        avg_distance = block_width
        mid_real_x = []

    out.vertical_x = np.asarray([r * np.cos(t) for r, t in merged_lines], dtype=float)
    out.mid_x = np.asarray([m[0] for m in all_mid_lines], dtype=float)
    # NOTE: the original stores (rho, theta) for detected mids but (x0, theta) for
    # propagated ones; with theta ~ 0 both are x positions. Mark "real" as those
    # equal (within 1e-6) to a detected mid-line x.
    real_x = np.asarray(mid_real_x, dtype=float)
    out.mid_real = np.array(
        [bool(len(real_x)) and bool(np.min(np.abs(real_x - x)) < 1e-6) for x in out.mid_x],
        dtype=bool,
    )
    out.avg_ring_px = float(avg_distance)
    out.prompts = replay_prompts(out, params, all_mid_lines)
    return out


# --------------------------------------------------------------------------- #
# Prompt-point logic (lines 340-495 + uniform_k_snap 497-579)
# --------------------------------------------------------------------------- #
def _line_segment_vertical_intersection(vertical_x, segment):
    x1, y1, x2, y2 = segment
    if x1 == x2:
        return None
    if min(x1, x2) <= vertical_x <= max(x1, x2):
        t = (vertical_x - x1) / (x2 - x1)
        return (vertical_x, y1 + t * (y2 - y1))
    return None


def _merge_close_points(points, threshold=6):
    points = np.array(points)
    if len(points) == 0:
        return np.array([])
    if len(points) == 1:
        return points
    merged = []
    while len(points) > 0:
        p0 = points[0]
        close = np.linalg.norm(points - p0, axis=1) < threshold
        merged.append(np.mean(points[close], axis=0))
        points = points[~close]
    return np.array(merged)


def _midpoint(p1, p2):
    return ((p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2)


def _check_distance_pattern(points, k, ab, tolerance=10):
    points = sorted(points, key=lambda q: q[0])
    for i in range(len(points) - 1):
        for j in range(i + 1, len(points)):
            d = np.linalg.norm(np.array(points[i]) - np.array(points[j]))
            if any(abs(d - (k + m * ab)) < tolerance for m in [2, 4]):
                return _midpoint(points[i], points[j])
    return None


def replay_prompts(ls: LineSet, params: dict[str, Any], all_mid_lines) -> pd.DataFrame:
    p = params
    L, _ = ls.shape
    resolution = float(p["resolution"])
    K_height = float(p.get("K_height", 1079.92))
    AB_height = float(p.get("AB_height", 3239.77))
    pattern_tolerance = float(p.get("pattern_tolerance", 50))
    prompt_logic = p.get("prompt_logic", "t12_pattern")
    uniform_k_snap = bool(p.get("uniform_k_snap", False))
    k_row_pattern = [float(v) for v in p.get("k_row_pattern", [1123.0, 1553.0])]
    k_row_tolerance = float(p.get("k_row_tolerance", 200.0))
    k_row_action = str(p.get("k_row_action", "snap")).lower()

    K_px = K_height / (1000 * resolution)
    AB_px = AB_height / (1000 * resolution)
    pos_lines = [(s,) for s in ls.oblique_pos]
    neg_lines = [(s,) for s in ls.oblique_neg]
    hor_lines = [(s,) for s in ls.horizontal]
    adjusted: list[tuple[str, tuple[float, float]]] = []

    if prompt_logic == "t3_inherit":
        for vertical_x, _ in all_mid_lines:
            ip, ineg, ih = [], [], []
            for seg in pos_lines:
                q = _line_segment_vertical_intersection(vertical_x, seg[0])
                if q:
                    ip.append(q)
            for seg in neg_lines:
                q = _line_segment_vertical_intersection(vertical_x, seg[0])
                if q:
                    ineg.append(q)
            mp, mn = _merge_close_points(ip), _merge_close_points(ineg)
            cur_type = cur_y = None
            if len(mp) > 0 and len(mn) > 0:
                cur_y = _midpoint(mp[0], mn[0])[1]
                cur_type = "midpoint"
            elif len(mp) > 0:
                cur_y = mp[0][1] - 0.5 * K_px
                cur_type = "positive_slope"
            elif len(mn) > 0:
                cur_y = mn[0][1] + 0.5 * K_px
                cur_type = "negative_slope"
            else:
                for seg in hor_lines:
                    q = _line_segment_vertical_intersection(vertical_x, seg[0])
                    if q:
                        ih.append(q)
                mh = _merge_close_points(ih)
                if len(mh) > 0:
                    min_y = min(mh, key=lambda x: x[1])[1]
                    max_y = max(mh, key=lambda x: x[1])[1]
                    cur_y = (min_y + max_y) / 2
                    cur_type = "horizontal"
                elif adjusted:
                    cur_y = adjusted[-1][1][1]
                    cur_type = "assume"
                else:
                    cur_y = L * 0.5
                    cur_type = "assume"
            if adjusted and cur_type != "assume":
                last_y = adjusted[-1][1][1]
                if abs(cur_y - last_y) / max(abs(last_y), 1e-6) > 0.1:
                    cur_y = last_y
                    cur_type = "assume"
            adjusted.append((cur_type, (vertical_x, cur_y)))
    else:
        for vertical_x, _ in all_mid_lines:
            ip, ineg, ih = [], [], []
            for seg in pos_lines:
                q = _line_segment_vertical_intersection(vertical_x, seg[0])
                if q:
                    ip.append(q)
            for seg in neg_lines:
                q = _line_segment_vertical_intersection(vertical_x, seg[0])
                if q:
                    ineg.append(q)
            mp, mn = _merge_close_points(ip), _merge_close_points(ineg)
            if len(mp) > 0 and len(mn) > 0:
                adjusted.append(("midpoint", _midpoint(mp[0], mn[0])))
            elif len(mp) > 0:
                adjusted.append(("positive_slope", (mp[0][0], mp[0][1] + 0.5 * K_px)))
            elif len(mn) > 0:
                adjusted.append(("negative_slope", (mn[0][0], mn[0][1] - 0.5 * K_px)))
            else:
                for seg in hor_lines:
                    q = _line_segment_vertical_intersection(vertical_x, seg[0])
                    if q:
                        ih.append(q)
                mh = _merge_close_points(ih)
                pm = _check_distance_pattern(mh, K_px, AB_px, tolerance=pattern_tolerance)
                if pm:
                    adjusted.append(("horizontal", pm))
                else:
                    assumed_y = None
                    if adjusted:
                        last_y = adjusted[-1][1][1]
                        if 1035 <= last_y <= 1265:
                            assumed_y = last_y + 431.87
                        elif 1422 <= last_y <= 1738:
                            assumed_y = last_y - 431.87
                        elif len(adjusted) > 1:
                            second_last = adjusted[-2][1][1]
                            if 1035 <= second_last <= 1265 or 1422 <= second_last <= 1738:
                                assumed_y = second_last
                    if assumed_y is None:
                        ring_idx = len(adjusted)
                        assumed_y = 1123.0 if ring_idx % 2 == 0 else 1553.0
                    adjusted.append(("assume", (vertical_x, assumed_y)))

    if uniform_k_snap:
        anchor_types = {"midpoint", "horizontal", "positive_slope", "negative_slope"}
        anchor_ys = [pt[1] for label, pt in adjusted if label in anchor_types]
        if anchor_ys:
            y_star = float(np.median(anchor_ys))
            nearest = float(min(k_row_pattern, key=lambda r: abs(r - y_star)))
            if abs(y_star - nearest) > k_row_tolerance and k_row_action == "snap":
                y_star = nearest
            adjusted = [("propagated", (pt[0], y_star)) for _, pt in adjusted]

    df = pd.DataFrame(adjusted, columns=["Type", "Coordinates"])
    df["X"] = df["Coordinates"].apply(lambda c: c[0])
    df["Y"] = df["Coordinates"].apply(lambda c: c[1])
    df = df.drop(columns=["Coordinates"]).sort_values(by="X").reset_index(drop=True)
    return df


# --------------------------------------------------------------------------- #
# Run-level convenience
# --------------------------------------------------------------------------- #
def replay_run(
    run_dir: Path,
    *,
    params_dir: Path | None = None,
    ring_count: int | None = None,
    keep_maps: bool = True,
    write_shadow: bool = True,
    shadow_root: Path = SHADOW_ROOT,
) -> LineSet:
    run_dir = Path(run_dir)
    params_dir = Path(params_dir) if params_dir else find_params_dir(run_dir)
    params = load_json(params_dir / "parameters_detecting.json")
    rc_source = "arg"
    if ring_count is None:
        ring_count, rc_source = find_ring_count(run_dir)
    dmo = np.load(run_dir / "depth_map_outlier.npy")
    ls = replay_lines(dmo, params, ring_count=ring_count, keep_maps=keep_maps)
    ls.ring_count = ring_count
    ls.ring_count_source = rc_source
    if write_shadow:
        shadow = shadow_root / run_dir.name
        shadow.mkdir(parents=True, exist_ok=True)
        payload = ls.to_json()
        payload["ring_count"] = ring_count
        payload["ring_count_source"] = rc_source
        payload["params_dir"] = str(params_dir)
        (shadow / "detected_lines.json").write_text(
            json.dumps(payload, indent=1) + "\n", encoding="utf-8"
        )
    return ls


def compare_prompts(replayed: pd.DataFrame, stored: pd.DataFrame) -> dict[str, Any]:
    """Row-wise agreement between replayed prompt points and initial_points.csv."""
    if len(replayed) != len(stored):
        return {"n_replayed": len(replayed), "n_stored": len(stored), "match": False,
                "max_dx": float("nan"), "max_dy": float("nan"), "type_match": 0.0}
    r = replayed.sort_values("X").reset_index(drop=True)
    s = stored.sort_values("X").reset_index(drop=True)
    dx = np.abs(r["X"].to_numpy(float) - s["X"].to_numpy(float))
    dy = np.abs(r["Y"].to_numpy(float) - s["Y"].to_numpy(float))
    type_match = float(np.mean(r["Type"].to_numpy() == s["Type"].to_numpy()))
    return {
        "n_replayed": len(r), "n_stored": len(s),
        "max_dx": float(dx.max()), "max_dy": float(dy.max()),
        "type_match": type_match,
        "match": bool(dx.max() <= 1.0 and dy.max() <= 1.0 and type_match == 1.0),
    }


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("run_dir")
    ap.add_argument("--params-dir", default=None)
    ap.add_argument("--no-shadow", action="store_true")
    args = ap.parse_args()
    ls = replay_run(Path(args.run_dir), params_dir=args.params_dir, write_shadow=not args.no_shadow)
    stored = pd.read_csv(Path(args.run_dir) / "initial_points.csv")
    print(json.dumps({
        "n_oblique_pos": len(ls.oblique_pos), "n_oblique_neg": len(ls.oblique_neg),
        "n_horizontal": len(ls.horizontal), "n_vertical": len(ls.vertical_x),
        "n_mid": len(ls.mid_x), "n_mid_real": int(ls.mid_real.sum()),
        "vertical_fallback": ls.vertical_fallback, "avg_ring_px": ls.avg_ring_px,
        "prompt_compare": compare_prompts(ls.prompts, stored),
    }, indent=2))
