"""Stage 1: tunnel centre-line extraction and cylindrical unrolling.

Extracted from Algorithm 1 in the three notebooks. Plotting cells remain in the
original notebooks; all data artifacts needed to reproduce those plots are
persisted here.
"""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

import numpy as np
import pandas as pd

from ..config import GeometryConfig, Stage1Config
from ..io import ensure_output_dir, save_dataframe, save_pickle
from ..state import StageState


RAW_COLUMNS = ["x", "y", "z", "intensity", "segment", "ring"]


def load_point_cloud(path: str | Path) -> pd.DataFrame:
    path = Path(path)
    if path.suffix.lower() == ".csv":
        df = pd.read_csv(path)
    else:
        values = np.loadtxt(path)
        if values.ndim != 2 or values.shape[1] < 3:
            raise ValueError("Point cloud must be a two-dimensional array with >=3 columns")
        columns = RAW_COLUMNS[: values.shape[1]]
        df = pd.DataFrame(values[:, : len(columns)], columns=columns)
    for column in ("segment", "ring"):
        if column in df:
            df[column] = df[column].astype(int)
    return df


def determine_direction(points_xyz: np.ndarray, reverse: bool = False) -> tuple[np.ndarray, np.ndarray]:
    """Notebook min-bounding-rectangle direction estimator."""

    from shapely.geometry import MultiPoint

    rectangle = MultiPoint(points_xyz[:, :2]).minimum_rotated_rectangle
    vertices = np.asarray(rectangle.exterior.coords)[:4]
    edge_lengths = np.linalg.norm(np.roll(vertices, -1, axis=0) - vertices, axis=1)
    # Midpoints of the two opposite short edges define the long tunnel axis.
    short = int(np.argmin(edge_lengths))
    opposite = (short + 2) % 4
    p1 = (vertices[short] + vertices[(short + 1) % 4]) / 2
    p2 = (vertices[opposite] + vertices[(opposite + 1) % 4]) / 2
    z = float(np.median(points_xyz[:, 2]))
    center1, center2 = np.r_[p1, z], np.r_[p2, z]
    if reverse:
        center1, center2 = center2, center1
    return center1, center2


def generate_slices(
    points_xyz: np.ndarray,
    center1: np.ndarray,
    center2: np.ndarray,
    ring_pitch_m: float,
    half_thickness_m: float,
    ring_count_multiplier: int = 1,
) -> tuple[np.ndarray, list[np.ndarray], int]:
    axis = center2 - center1
    length = float(np.linalg.norm(axis))
    normal = axis / length
    base_count = max(2, int(round(length / ring_pitch_m)))
    ring_count = max(2, base_count * ring_count_multiplier)
    origins = np.linspace(center1, center2, ring_count)
    signed = points_xyz @ normal
    slices = [
        points_xyz[np.abs(signed - float(origin @ normal)) <= half_thickness_m]
        for origin in origins
    ]
    return origins, slices, ring_count


def _plane_basis(normal: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    normal = normal / np.linalg.norm(normal)
    seed = np.array([0.0, 0.0, 1.0])
    if abs(float(seed @ normal)) > 0.95:
        seed = np.array([0.0, 1.0, 0.0])
    u = np.cross(normal, seed)
    u /= np.linalg.norm(u)
    v = np.cross(normal, u)
    return u, v


def project_to_plane(
    points: np.ndarray, origin: np.ndarray, normal: np.ndarray
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    u, v = _plane_basis(normal)
    relative = points - origin
    return np.column_stack((relative @ u, relative @ v)), u, v


def filter_cross_section(points_2d: np.ndarray, config: Stage1Config) -> np.ndarray:
    if len(points_2d) == 0 or config.obstruction == "none":
        return points_2d
    if config.obstruction == "railway_bottom":
        ceiling = float(np.max(points_2d[:, 1]))
        return points_2d[np.abs(points_2d[:, 1] - ceiling) <= config.railway_keep_height_m]
    # The T4/T5 notebook removes a circular top service-tube region.
    top = points_2d[np.argsort(points_2d[:, 1])[-min(10, len(points_2d)) :]]
    centre = np.mean(top, axis=0)
    distance = np.linalg.norm(points_2d - centre, axis=1)
    return points_2d[distance >= config.service_tube_exclusion_radius_m]


def fit_ellipse_ransac(
    points: np.ndarray, config: Stage1Config, rng: np.random.Generator
) -> tuple[tuple[float, float], tuple[float, float], float, float]:
    import cv2

    if len(points) < 5:
        raise ValueError("At least five section points are required for ellipse fitting")
    best: tuple | None = None
    best_mask: np.ndarray | None = None
    sample_size = max(5, min(len(points), int(len(points) * 0.1)))
    for _ in range(config.ellipse_ransac_iterations):
        sample = points[rng.choice(len(points), sample_size, replace=False)].astype(np.float32)
        ellipse = cv2.fitEllipse(sample)
        (cx, cy), (major, minor), angle = ellipse
        theta = np.deg2rad(angle)
        cos_t, sin_t = np.cos(theta), np.sin(theta)
        x = (points[:, 0] - cx) * cos_t + (points[:, 1] - cy) * sin_t
        y = -(points[:, 0] - cx) * sin_t + (points[:, 1] - cy) * cos_t
        residual = np.abs((x / max(major / 2, 1e-8)) ** 2 + (y / max(minor / 2, 1e-8)) ** 2 - 1)
        mask = residual <= config.ellipse_ransac_threshold_m
        if best_mask is None or int(mask.sum()) > int(best_mask.sum()):
            best, best_mask = ellipse, mask
    assert best is not None and best_mask is not None
    required = max(5, int(config.ellipse_ransac_inlier_fraction * len(points)))
    if config.ellipse_refine and int(best_mask.sum()) >= required:
        best = cv2.fitEllipse(points[best_mask].astype(np.float32))
    residual_score = 1.0 - float(best_mask.mean())
    return best[0], best[1], float(best[2]), residual_score


def fit_centre_curve(
    centres: np.ndarray, degree: int
) -> tuple[np.ndarray, list]:
    from sklearn.linear_model import LinearRegression, RANSACRegressor
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import PolynomialFeatures

    t = np.arange(len(centres), dtype=float)[:, None]
    models = []
    fitted = []
    for coordinate in centres.T:
        model = make_pipeline(
            PolynomialFeatures(degree=degree, include_bias=False),
            RANSACRegressor(estimator=LinearRegression(), random_state=0),
        )
        model.fit(t, coordinate)
        models.append(model)
        fitted.append(model.predict(t))
    return np.column_stack(fitted), models


def sample_curve(models: list, count: int, ring_count: int) -> tuple[np.ndarray, np.ndarray]:
    t = np.linspace(0, ring_count - 1, count)[:, None]
    points = np.column_stack([model.predict(t) for model in models])
    derivative = np.gradient(points, axis=0)
    derivative /= np.maximum(np.linalg.norm(derivative, axis=1, keepdims=True), 1e-12)
    return points, derivative


def unroll_points(
    points_xyz: np.ndarray,
    curve_points: np.ndarray,
    tangents: np.ndarray,
    diameter_m: float,
) -> np.ndarray:
    from scipy.spatial import cKDTree

    nearest = cKDTree(curve_points).query(points_xyz, k=1)[1]
    centre = curve_points[nearest]
    tangent = tangents[nearest]
    radial_vector = points_xyz - centre
    r = np.linalg.norm(radial_vector, axis=1)
    z_axis = np.array([0.0, 0.0, 1.0])
    reference = z_axis - (tangent @ z_axis)[:, None] * tangent
    bad = np.linalg.norm(reference, axis=1) < 1e-8
    reference[bad] = np.array([0.0, 1.0, 0.0])
    reference /= np.linalg.norm(reference, axis=1, keepdims=True)
    side = np.cross(tangent, reference)
    angle_deg = np.degrees(
        np.arctan2(np.sum(radial_vector * side, axis=1), np.sum(radial_vector * reference, axis=1))
    )
    theta = angle_deg * (np.pi * diameter_m / 360.0)
    arc = np.r_[0.0, np.cumsum(np.linalg.norm(np.diff(curve_points, axis=0), axis=1))]
    h = arc[nearest]
    return np.column_stack((r, theta, h))


def run_stage1(
    input_path: str | Path,
    output_dir: str | Path,
    geometry: GeometryConfig,
    config: Stage1Config,
    profile: str,
) -> Path:
    output_dir = ensure_output_dir(output_dir)
    df = load_point_cloud(input_path)
    df.insert(0, "point_index", np.arange(len(df), dtype=int))
    points = df[["x", "y", "z"]].to_numpy(float)
    center1, center2 = determine_direction(points, config.reverse_direction)
    origins, slices, ring_count = generate_slices(
        points,
        center1,
        center2,
        geometry.ring_pitch_m,
        config.slice_half_thickness_m,
        config.ring_count_multiplier,
    )
    normal = (center2 - center1) / np.linalg.norm(center2 - center1)
    rng = np.random.default_rng(0)
    centres, ellipse_rows = [], []
    filtered_sections = []
    for index, (origin, section) in enumerate(zip(origins, slices)):
        projected, u, v = project_to_plane(section, origin, normal)
        filtered = filter_cross_section(projected, config)
        filtered_sections.append(filtered)
        try:
            centre_2d, axes, angle, residual = fit_ellipse_ransac(filtered, config, rng)
        except ValueError:
            # Keep the pipeline resumable on sparse end slices.
            centre_2d = tuple(np.median(projected, axis=0)) if len(projected) else (0.0, 0.0)
            axes, angle, residual = (np.nan, np.nan), np.nan, 1.0
        centre_3d = origin + centre_2d[0] * u + centre_2d[1] * v
        centres.append(centre_3d)
        ellipse_rows.append((index, *centre_2d, *axes, angle, residual))
    centres_array = np.asarray(centres)
    fitted_centres, models = fit_centre_curve(centres_array, config.curve_degree)
    sample_count = max(ring_count * config.curve_sample_factor, ring_count)
    curve_points, tangents = sample_curve(models, sample_count, ring_count)
    cylindrical = unroll_points(points, curve_points, tangents, geometry.diameter_m)
    df[["r", "theta", "h"]] = cylindrical

    raw_path = save_dataframe(
        df[["point_index", *RAW_COLUMNS]], output_dir / "raw_point_cloud.csv"
    )
    unwrapped_path = save_dataframe(df, output_dir / "unwrapped_point_cloud.csv")
    ellipse_path = save_dataframe(
        pd.DataFrame(
            ellipse_rows,
            columns=["slice", "centre_u", "centre_v", "axis_1", "axis_2", "angle", "residual"],
        ),
        output_dir / "ellipse_fits.csv",
    )
    np.savez(
        output_dir / "centreline.npz",
        center1=center1,
        center2=center2,
        origins=origins,
        ellipse_centres=centres_array,
        fitted_centres=fitted_centres,
        curve_points=curve_points,
        tangents=tangents,
        ring_count=ring_count,
    )
    slices_path = save_pickle(
        {"slices_3d": slices, "filtered_sections_2d": filtered_sections},
        output_dir / "slices.pkl",
    )
    state = StageState(
        1,
        "centreline",
        "completed",
        profile,
        {"geometry": asdict(geometry), "stage": asdict(config), "ring_count": ring_count},
        metrics={
            "point_count": len(df),
            "ring_count": ring_count,
            "mean_ellipse_residual": float(np.nanmean([row[-1] for row in ellipse_rows])),
        },
    )
    state.add_artifact("raw_point_cloud", raw_path.name, "text/csv")
    state.add_artifact("unwrapped_point_cloud", unwrapped_path.name, "text/csv")
    state.add_artifact("ellipse_fits", ellipse_path.name, "text/csv")
    state.add_artifact("centreline", "centreline.npz", "application/x-npz")
    state.add_artifact("slices", slices_path.name, "application/x-python-pickle")
    return state.write(output_dir / "manifest.json")
