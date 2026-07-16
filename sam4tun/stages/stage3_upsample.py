"""Stage 3: geometry-guided surface/joint upsampling and 2-D projection."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

import numpy as np
import pandas as pd

from ..config import GeometryConfig, Stage3Config
from ..io import ensure_output_dir, save_array, save_dataframe, save_depth_png
from ..state import StageState


def compute_curvature(df: pd.DataFrame, neighbors: int = 20) -> pd.DataFrame:
    from scipy.spatial import cKDTree

    result = df.copy()
    points = result[["x", "y", "z"]].to_numpy(float)
    k = min(neighbors + 1, len(points))
    if k < 4:
        result["curvature"] = 0.0
        return result
    indices = cKDTree(points).query(points, k=k)[1]
    curvature = np.zeros(len(points))
    for i, row in enumerate(indices):
        covariance = np.cov(points[np.atleast_1d(row)[1:]].T)
        eigenvalues = np.linalg.eigvalsh(covariance)
        curvature[i] = eigenvalues[0] / max(float(eigenvalues.sum()), 1e-12)
    result["curvature"] = curvature
    return result


def enhance_segment_surface(
    df: pd.DataFrame,
    target_distance: float,
    config: Stage3Config,
) -> pd.DataFrame:
    from scipy.spatial import cKDTree

    plane = df[["h", "theta"]].to_numpy(float)
    values = df[["h", "theta", "r", "curvature", "intensity"]].to_numpy(float)
    k = min(config.curvature_neighbors + 1, len(df))
    if k < 2:
        return df.iloc[0:0].copy()
    distances, indices = cKDTree(plane).query(plane, k=k)
    low, high = config.midpoint_distance_range
    new_rows = []
    for i in range(len(df)):
        for distance, j in zip(np.atleast_1d(distances[i])[1:], np.atleast_1d(indices[i])[1:]):
            if (
                low * target_distance <= distance <= high * target_distance
                and abs(values[i, 3] - values[j, 3]) <= config.curvature_threshold
            ):
                new_rows.append((values[i] + values[j]) / 2)
    if not new_rows:
        return df.iloc[0:0].copy()
    candidates = np.unique(np.round(np.asarray(new_rows), decimals=8), axis=0)
    minimum = config.radius_filter_factor * target_distance
    keep = cKDTree(plane).query(candidates[:, :2], k=1)[0] >= minimum
    candidates = candidates[keep]
    result = pd.DataFrame(
        candidates, columns=["h", "theta", "r", "curvature", "intensity"]
    )
    # Interpolated points intentionally have no original pixel->point mapping.
    result["point_index"] = -1
    result["pred"] = config.surface_interpolated_marker
    return result


def run_surface_upsampling(
    candidates: pd.DataFrame, config: Stage3Config
) -> pd.DataFrame:
    all_points = candidates.copy()
    for target in config.target_distance_schedule_m:
        additions = enhance_segment_surface(all_points, target, config)
        all_points = pd.concat([all_points, additions], ignore_index=True, sort=False)
    return all_points


def _high_density_bounds(
    h: np.ndarray,
    ring_count: int,
    ring_pitch_m: float,
    ring_range: tuple[int, int],
) -> tuple[float, float]:
    left = float(np.min(h) + ring_pitch_m * ring_range[0])
    right = float(np.max(h) - ring_pitch_m * max(0, ring_count - ring_range[1]))
    centre = (left + right) / 2
    half_width = max(abs(right - left) / 2, ring_pitch_m / 2)
    return centre - half_width, centre + half_width


def enhance_joint_points(
    df: pd.DataFrame,
    ring_count: int,
    ring_pitch_m: float,
    config: Stage3Config,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    from scipy.spatial import cKDTree

    plane = df[["h", "theta"]].to_numpy(float)
    radius = df["r"].to_numpy(float)
    k = min(config.joint_neighbors, len(df))
    if k < 2:
        return df.iloc[0:0].copy(), df.iloc[0:0].copy()
    _, neighbors = cKDTree(plane).query(plane, k=k)
    local_mean = np.array(
        [np.mean(radius[np.atleast_1d(row)[1:]]) for row in neighbors]
    )
    difference = radius - local_mean
    low_h, high_h = _high_density_bounds(
        df["h"].to_numpy(), ring_count, ring_pitch_m, config.high_density_ring_range
    )
    high_density = df["h"].between(low_h, high_h).to_numpy()
    threshold = np.where(
        high_density, config.depth_threshold_high_m, config.depth_threshold_low_m
    )
    meaningful = df.loc[difference > threshold].copy()
    if config.joint_curvature_min is not None:
        meaningful = meaningful[
            meaningful["curvature"] >= config.joint_curvature_min
        ].copy()
    if not config.interpolate_joints or len(meaningful) < 2:
        return meaningful, meaningful.iloc[0:0].copy()

    joint_plane = meaningful[["h", "theta"]].to_numpy(float)
    tree = cKDTree(joint_plane)
    pairs = tree.query_pairs(config.interpolation_radius_m)
    rows = []
    numeric = meaningful[["h", "theta", "r", "intensity"]].to_numpy(float)
    for i, j in pairs:
        distance = np.linalg.norm(joint_plane[i] - joint_plane[j])
        if distance <= config.resolution_m_per_px:
            continue
        for alpha in np.linspace(0, 1, config.interpolation_count + 2)[1:-1]:
            rows.append((1 - alpha) * numeric[i] + alpha * numeric[j])
    if not rows:
        return meaningful, meaningful.iloc[0:0].copy()
    interpolated = pd.DataFrame(rows, columns=["h", "theta", "r", "intensity"])
    interpolated = interpolated.drop_duplicates(["h", "theta"])
    interpolated["point_index"] = -1
    interpolated["pred"] = config.surface_interpolated_marker
    return meaningful, interpolated


def project_to_depth_map(
    surface: pd.DataFrame,
    joints: pd.DataFrame,
    config: Stage3Config,
    *,
    outlier_only: bool = False,
) -> tuple[np.ndarray, pd.DataFrame, dict[str, float]]:
    from scipy.ndimage import distance_transform_edt, maximum_filter

    combined = pd.concat([surface, joints], ignore_index=True)
    x_min, x_max = float(combined["h"].min()), float(combined["h"].max())
    y_min, y_max = float(combined["theta"].min()), float(combined["theta"].max())
    resolution = config.resolution_m_per_px
    width = max(1, int(np.ceil((x_max - x_min) / resolution)) + 1)
    height = max(1, int(np.ceil((y_max - y_min) / resolution)) + 1)
    depth = np.full((height, width), np.nan, dtype=np.float32)
    mapping_rows: list[tuple[int, int, int]] = []

    def place(frame: pd.DataFrame, record_mapping: bool) -> None:
        x = np.clip(((frame["h"] - x_min) / resolution).astype(int), 0, width - 1)
        y = np.clip(((frame["theta"] - y_min) / resolution).astype(int), 0, height - 1)
        for row_pos, (pixel_x, pixel_y, value) in enumerate(
            zip(x, y, frame["r"].to_numpy())
        ):
            depth[pixel_y, pixel_x] = value
            if record_mapping:
                marker = int(frame.iloc[row_pos]["pred"])
                point_index = int(frame.iloc[row_pos]["point_index"])
                if (
                    point_index >= 0
                    and marker not in config.mapping_excluded_markers
                ):
                    mapping_rows.append((pixel_x, pixel_y, point_index))

    if not outlier_only:
        place(surface, True)
    place(joints, False)
    if not outlier_only and config.projection_window > 1:
        occupied = ~np.isnan(depth)
        near = maximum_filter(
            occupied.astype(np.uint8), size=config.projection_window
        ).astype(bool)
        _, nearest = distance_transform_edt(~occupied, return_indices=True)
        fill = ~occupied & near
        depth[fill] = depth[nearest[0][fill], nearest[1][fill]]
    mapping = pd.DataFrame(
        mapping_rows, columns=["pixel_x", "pixel_y", "point_index"]
    ).drop_duplicates()
    transform = {
        "h_min": x_min,
        "theta_min": y_min,
        "resolution": resolution,
        "width": width,
        "height": height,
    }
    return depth, mapping, transform


def run_stage3(
    upstream_manifest: str | Path,
    output_dir: str | Path,
    geometry: GeometryConfig,
    config: Stage3Config,
    profile: str,
) -> Path:
    upstream_manifest = Path(upstream_manifest)
    upstream = StageState.read(upstream_manifest)
    output_dir = ensure_output_dir(output_dir)
    df = pd.read_csv(upstream.require("denoised_point_cloud", upstream_manifest))
    if "point_index" not in df:
        df["point_index"] = np.arange(len(df))
    ring_count = int(upstream.parameters["ring_count"])
    candidates = compute_curvature(
        df[df["pred"] != 0], config.curvature_neighbors
    )
    enhanced_surface = run_surface_upsampling(candidates, config)
    meaningful, interpolated = enhance_joint_points(
        candidates, ring_count, geometry.ring_pitch_m, config
    )
    enhanced_joint = pd.concat(
        [meaningful, interpolated], ignore_index=True, sort=False
    )
    df.loc[df["point_index"].isin(meaningful["point_index"]), "pred"] = 0
    projection_surface = (
        enhanced_surface
        if config.projection_uses_surface_upsampling
        else candidates
    )
    depth_map, mapping, transform = project_to_depth_map(
        projection_surface, enhanced_joint, config
    )

    filtered_path = save_dataframe(df, output_dir / "filtered_point_cloud.csv")
    surface_path = save_dataframe(
        enhanced_surface, output_dir / "enhanced_segment_cloud.csv"
    )
    joint_path = save_dataframe(
        enhanced_joint, output_dir / "enhanced_joint_cloud.csv"
    )
    mapping_path = save_dataframe(mapping, output_dir / "pixel_to_point.csv")
    depth_path = save_array(depth_map, output_dir / "depth_map.npy")
    depth_png = save_depth_png(
        depth_map,
        output_dir / "depth_map.png",
        vmin=config.depth_threshold_low_m + min(df["r"]),
        vmax=max(df["r"]),
    )
    transform_path = output_dir / "projection_transform.json"
    import json

    transform_path.write_text(json.dumps(transform, indent=2), encoding="utf-8")
    hole_ratio = float(np.isnan(depth_map).mean())
    state = StageState(
        3,
        "upsample",
        "completed",
        profile,
        {
            "stage": asdict(config),
            "geometry": asdict(geometry),
            "ring_count": ring_count,
            "projection_transform": transform,
        },
        metrics={
            "surface_point_count": len(enhanced_surface),
            "joint_point_count": len(enhanced_joint),
            "depth_map_shape": list(depth_map.shape),
            "depth_map_hole_ratio": hole_ratio,
        },
        upstream_manifest=str(upstream_manifest),
    )
    state.add_artifact("filtered_point_cloud", filtered_path.name, "text/csv")
    state.add_artifact("enhanced_segment_cloud", surface_path.name, "text/csv")
    state.add_artifact("enhanced_joint_cloud", joint_path.name, "text/csv")
    state.add_artifact("depth_map", depth_path.name, "application/x-npy")
    state.add_artifact("depth_map_png", depth_png.name, "image/png")
    state.add_artifact("pixel_to_point", mapping_path.name, "text/csv")
    state.add_artifact("projection_transform", transform_path.name, "application/json")
    return state.write(output_dir / "manifest.json")
