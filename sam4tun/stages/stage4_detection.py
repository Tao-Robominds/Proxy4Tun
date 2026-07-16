"""Stage 4: joint-line detection and prompt-centre generation."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

import numpy as np
import pandas as pd

from ..config import GeometryConfig, Stage4Config
from ..io import ensure_output_dir, save_array, save_dataframe
from ..state import StageState


def _joint_map(
    joints: pd.DataFrame, transform: dict[str, float]
) -> np.ndarray:
    height, width = int(transform["height"]), int(transform["width"])
    resolution = float(transform["resolution"])
    result = np.full((height, width), np.nan, dtype=np.float32)
    x = ((joints["h"] - transform["h_min"]) / resolution).astype(int)
    y = ((joints["theta"] - transform["theta_min"]) / resolution).astype(int)
    valid = (x >= 0) & (x < width) & (y >= 0) & (y < height)
    result[y[valid], x[valid]] = joints.loc[valid, "r"]
    return result


def _vertical_roi(
    width: int,
    resolution: float,
    ring_pitch_m: float,
    config: Stage4Config,
) -> tuple[float, float]:
    pitch = config.coverage.pitch_override_m or ring_pitch_m
    start = config.coverage.start_ring * pitch / resolution
    end = config.coverage.end_ring * pitch / resolution
    if config.coverage.anchor == "center":
        return width / 2 + start, width / 2 + end
    # `left` and notebook `absolute` are both measured from image x=0;
    # their semantic distinction is retained in the manifest.
    return start, end


def _merge_verticals(values: list[float], threshold: float) -> list[float]:
    if not values:
        return []
    values = sorted(values)
    groups = [[values[0]]]
    for value in values[1:]:
        if value - np.mean(groups[-1]) < threshold:
            groups[-1].append(value)
        else:
            groups.append([value])
    return [float(np.mean(group)) for group in groups]


def _line_intersection(vertical_x: float, line: np.ndarray) -> tuple[float, float] | None:
    x1, y1, x2, y2 = map(float, line)
    if x1 == x2 or not min(x1, x2) <= vertical_x <= max(x1, x2):
        return None
    ratio = (vertical_x - x1) / (x2 - x1)
    return vertical_x, y1 + ratio * (y2 - y1)


def _merge_points(points: list[tuple[float, float]], distance: float) -> list[np.ndarray]:
    remaining = [np.asarray(point, dtype=float) for point in points]
    merged = []
    while remaining:
        seed = remaining.pop(0)
        close, far = [seed], []
        for point in remaining:
            (close if np.linalg.norm(point - seed) < distance else far).append(point)
        merged.append(np.mean(close, axis=0))
        remaining = far
    return merged


def _distance_pattern_midpoint(
    points: list[np.ndarray], key_px: float, regular_px: float, tolerance: float
) -> np.ndarray | None:
    for i, first in enumerate(points):
        for second in points[i + 1 :]:
            distance = float(np.linalg.norm(first - second))
            if any(
                abs(distance - (key_px + multiplier * regular_px)) < tolerance
                for multiplier in (2, 4)
            ):
                return (first + second) / 2
    return None


def detect_lines(
    dilated: np.ndarray,
    config: Stage4Config,
    geometry: GeometryConfig,
    resolution: float,
) -> dict[str, list]:
    import cv2

    hough = config.hough
    oblique = cv2.HoughLinesP(
        dilated,
        1,
        np.pi / 180,
        hough.oblique_threshold,
        minLineLength=hough.oblique_min_length_px,
        maxLineGap=hough.oblique_max_gap_px,
    )
    horizontal = cv2.HoughLinesP(
        dilated,
        1,
        np.pi / 180,
        hough.horizontal_threshold,
        minLineLength=hough.horizontal_min_length_px,
        maxLineGap=hough.horizontal_max_gap_px,
    )
    vertical = cv2.HoughLines(
        dilated, 1, np.pi / 180, hough.vertical_threshold
    )
    positive, negative, horizontals = [], [], []
    for row in ([] if oblique is None else oblique[:, 0]):
        x1, y1, x2, y2 = row
        if x1 > x2:
            x1, y1, x2, y2 = x2, y2, x1, y1
        angle = float(np.degrees(np.arctan2(-(y2 - y1), x2 - x1)))
        if hough.positive_angle_deg[0] <= angle <= hough.positive_angle_deg[1]:
            positive.append(np.array([x1, y1, x2, y2]))
        elif hough.negative_angle_deg[0] <= angle <= hough.negative_angle_deg[1]:
            negative.append(np.array([x1, y1, x2, y2]))
    for row in ([] if horizontal is None else horizontal[:, 0]):
        x1, y1, x2, y2 = row
        angle = float(np.degrees(np.arctan2(y2 - y1, x2 - x1)))
        if abs(angle) <= 1:
            horizontals.append(np.asarray(row))
    roi_low, roi_high = _vertical_roi(
        dilated.shape[1], resolution, geometry.ring_pitch_m, config
    )
    vertical_x = []
    for row in ([] if vertical is None else vertical[:, 0]):
        rho, theta = map(float, row)
        if (
            abs(np.degrees(theta)) <= config.vertical_angle_tolerance_deg
            and roi_low <= rho <= roi_high
        ):
            vertical_x.append(rho)
    return {
        "positive": positive,
        "negative": negative,
        "horizontal": horizontals,
        "vertical": _merge_verticals(
            vertical_x, config.vertical_merge_distance_px
        ),
    }


def build_ring_centres(
    verticals: list[float], width: int, ring_count: int, pitch_px: float
) -> list[float]:
    if len(verticals) >= 2:
        centres = [(left + right) / 2 for left, right in zip(verticals, verticals[1:])]
        detected = float(np.median(np.diff(centres))) if len(centres) > 1 else pitch_px
        designed = width / max(ring_count, 1)
        step = detected if abs(detected - pitch_px) <= abs(designed - pitch_px) else designed
        seed = centres[0]
    elif len(verticals) == 1:
        step, seed = pitch_px, verticals[0] + pitch_px / 2
    else:
        step, seed = pitch_px, pitch_px / 2
    left = np.arange(seed, -step, -step)
    right = np.arange(seed + step, width + step, step)
    return sorted({round(float(x), 6) for x in np.r_[left, right] if 0 <= x < width})


def prompt_centres(
    ring_centres: list[float],
    lines: dict[str, list],
    image_height: int,
    geometry: GeometryConfig,
    resolution: float,
    config: Stage4Config,
) -> pd.DataFrame:
    key_px = geometry.key_height_mm / (1000 * resolution)
    regular_px = geometry.regular_height_mm / (1000 * resolution)
    rows = []
    previous_y: float | None = None
    for x in ring_centres:
        positive = _merge_points(
            [p for line in lines["positive"] if (p := _line_intersection(x, line))],
            config.intersection_merge_distance_px,
        )
        negative = _merge_points(
            [p for line in lines["negative"] if (p := _line_intersection(x, line))],
            config.intersection_merge_distance_px,
        )
        if positive and negative:
            y = float((positive[0][1] + negative[0][1]) / 2)
            source = "midpoint"
        elif positive:
            y, source = float(positive[0][1] - key_px / 2), "positive_slope"
        elif negative:
            y, source = float(negative[0][1] + key_px / 2), "negative_slope"
        else:
            horizontal = _merge_points(
                [p for line in lines["horizontal"] if (p := _line_intersection(x, line))],
                config.intersection_merge_distance_px,
            )
            pattern = _distance_pattern_midpoint(
                horizontal, key_px, regular_px, config.pattern_tolerance_px
            )
            if config.fallback == "geometry_pattern" and pattern is not None:
                y, source = float(pattern[1]), "horizontal"
            elif config.fallback == "previous_prompt" and previous_y is not None:
                y, source = previous_y, "previous_prompt"
            else:
                y, source = image_height / 2, "image_center"
        y = float(np.clip(y, 0, image_height - 1))
        previous_y = y
        rows.append((source, x, y))
    return pd.DataFrame(rows, columns=["Type", "X", "Y"]).sort_values("X")


def run_stage4(
    upstream_manifest: str | Path,
    output_dir: str | Path,
    geometry: GeometryConfig,
    config: Stage4Config,
    profile: str,
) -> Path:
    import cv2

    upstream_manifest = Path(upstream_manifest)
    upstream = StageState.read(upstream_manifest)
    output_dir = ensure_output_dir(output_dir)
    surface = pd.read_csv(
        upstream.require("enhanced_segment_cloud", upstream_manifest)
    )
    joints = pd.read_csv(upstream.require("enhanced_joint_cloud", upstream_manifest))
    if config.intensity_max is not None:
        joints = joints[joints["intensity"] <= config.intensity_max]
    transform = upstream.parameters["projection_transform"]
    outlier_map = _joint_map(joints, transform)
    binary = np.where(np.isnan(outlier_map), 0, 255).astype(np.uint8)
    _, binary = cv2.threshold(
        binary, config.binary_threshold, 255, cv2.THRESH_BINARY
    )
    kernel = np.ones((config.dilation_kernel, config.dilation_kernel), np.uint8)
    dilated = cv2.dilate(binary, kernel, iterations=config.dilation_iterations)
    lines = detect_lines(
        dilated, config, geometry, float(transform["resolution"])
    )
    ring_count = int(upstream.parameters["ring_count"])
    pitch_px = geometry.ring_pitch_m / float(transform["resolution"])
    centres = build_ring_centres(
        lines["vertical"], dilated.shape[1], ring_count, pitch_px
    )
    prompts = prompt_centres(
        centres,
        lines,
        dilated.shape[0],
        geometry,
        float(transform["resolution"]),
        config,
    )
    line_rows = [
        (kind, *map(float, line))
        for kind in ("positive", "negative", "horizontal")
        for line in lines[kind]
    ] + [("vertical", float(x), 0.0, float(x), float(dilated.shape[0])) for x in lines["vertical"]]
    lines_df = pd.DataFrame(line_rows, columns=["type", "x1", "y1", "x2", "y2"])

    outlier_path = save_array(outlier_map, output_dir / "outlier_depth_map.npy")
    binary_path = output_dir / "dilated_edges.png"
    cv2.imwrite(str(binary_path), dilated)
    prompts_path = save_dataframe(prompts, output_dir / "initial_points.csv")
    lines_path = save_dataframe(lines_df, output_dir / "detected_lines.csv")
    state = StageState(
        4,
        "detection",
        "completed",
        profile,
        {
            "stage": asdict(config),
            "geometry": asdict(geometry),
            "ring_count": ring_count,
        },
        metrics={
            "vertical_line_count": len(lines["vertical"]),
            "oblique_line_count": len(lines["positive"]) + len(lines["negative"]),
            "prompt_count": len(prompts),
            "assumed_prompt_ratio": float(
                prompts["Type"].isin(["previous_prompt", "image_center"]).mean()
            ),
        },
        upstream_manifest=str(upstream_manifest),
    )
    state.add_artifact("outlier_depth_map", outlier_path.name, "application/x-npy")
    state.add_artifact("dilated_edges", binary_path.name, "image/png")
    state.add_artifact("detected_lines", lines_path.name, "text/csv")
    state.add_artifact("prompt_centres", prompts_path.name, "text/csv")
    return state.write(output_dir / "manifest.json")
