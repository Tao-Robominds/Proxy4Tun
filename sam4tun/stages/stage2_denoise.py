"""Stage 2: local point-density-difference denoising."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

import numpy as np
import pandas as pd

from ..config import Stage2Config
from ..io import ensure_output_dir, save_dataframe
from ..state import StageState


def _smooth(values: np.ndarray, size: int) -> np.ndarray:
    from scipy.ndimage import uniform_filter1d

    return uniform_filter1d(values.astype(float), size=max(1, size), mode="nearest")


def density_cutoff(
    theta: np.ndarray,
    radius: np.ndarray,
    theta_bins: np.ndarray,
    radius_bins: np.ndarray,
    baseline: float,
    gradient_threshold: float,
    smoothing_bins: int,
    cutoff_offset: float,
) -> tuple[np.ndarray, np.ndarray]:
    """Find the radial density drop for each circumferential bin."""

    counts, _, _ = np.histogram2d(theta, radius, bins=(theta_bins, radius_bins))
    cutoffs = np.full(len(theta_bins) - 1, baseline, dtype=float)
    radius_centres = (radius_bins[:-1] + radius_bins[1:]) / 2
    for row_index, row in enumerate(counts):
        smooth = _smooth(row, smoothing_bins)
        if not np.any(smooth):
            continue
        peak = int(np.argmax(smooth))
        scale = max(float(np.max(smooth)), 1e-6)
        gradient = np.diff(smooth) / scale
        candidates = np.flatnonzero(gradient[peak:] < -gradient_threshold)
        index = peak + int(candidates[0]) if len(candidates) else peak
        cutoffs[row_index] = radius_centres[min(index, len(radius_centres) - 1)] + cutoff_offset
    return counts, cutoffs


def denoise_point_cloud(
    df: pd.DataFrame, ring_count: int, config: Stage2Config
) -> tuple[pd.DataFrame, pd.DataFrame]:
    required = {"h", "theta", "r"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Stage 2 input is missing columns: {sorted(missing)}")
    result = df.copy()
    result["pred"] = config.lining_marker
    radial = result["r"].between(*config.radial_range_m, inclusive="both")
    angular = pd.Series(True, index=result.index)
    if config.angular_range_m is not None:
        # Corrects the T3 notebook typo: the upper comparison is theta, not r.
        angular = result["theta"].between(*config.angular_range_m, inclusive="both")
    candidate_mask = radial & angular
    result.loc[~candidate_mask, "pred"] = 0

    candidates = result.loc[candidate_mask]
    if candidates.empty:
        return result, pd.DataFrame(
            columns=["h_bin", "theta_low", "theta_high", "radius_cutoff"]
        )
    h_bins = np.linspace(
        float(candidates["h"].min()),
        float(candidates["h"].max()) + np.finfo(float).eps,
        max(2, ring_count * config.h_bins_per_ring + 1),
    )
    theta_bins = np.arange(
        float(candidates["theta"].min()),
        float(candidates["theta"].max()) + config.theta_step_m,
        config.theta_step_m,
    )
    radius_bins = np.arange(
        config.radial_range_m[0],
        config.radial_range_m[1] + config.radius_step_m,
        config.radius_step_m,
    )
    cutoff_rows: list[tuple[int, float, float, float]] = []
    for h_index in range(len(h_bins) - 1):
        in_h = candidates["h"].between(h_bins[h_index], h_bins[h_index + 1], inclusive="left")
        subset = candidates.loc[in_h]
        if subset.empty:
            continue
        _, cutoffs = density_cutoff(
            subset["theta"].to_numpy(),
            subset["r"].to_numpy(),
            theta_bins,
            radius_bins,
            config.radial_range_m[0],
            config.gradient_threshold,
            config.density_smoothing_bins,
            config.cutoff_offset_m,
        )
        theta_index = np.clip(
            np.digitize(subset["theta"], theta_bins) - 1, 0, len(cutoffs) - 1
        )
        # Points beyond the local radial density discontinuity are background.
        rejected = subset["r"].to_numpy() > cutoffs[theta_index]
        result.loc[subset.index[rejected], "pred"] = 0
        cutoff_rows.extend(
            (h_index, theta_bins[i], theta_bins[i + 1], float(value))
            for i, value in enumerate(cutoffs)
        )
    cutoff_df = pd.DataFrame(
        cutoff_rows, columns=["h_bin", "theta_low", "theta_high", "radius_cutoff"]
    )
    return result, cutoff_df


def run_stage2(
    upstream_manifest: str | Path,
    output_dir: str | Path,
    config: Stage2Config,
    profile: str,
) -> Path:
    upstream_manifest = Path(upstream_manifest).resolve()
    upstream = StageState.read(upstream_manifest)
    output_dir = ensure_output_dir(output_dir)
    df = pd.read_csv(upstream.require("unwrapped_point_cloud", upstream_manifest))
    ring_count = int(upstream.parameters["ring_count"])
    denoised, cutoffs = denoise_point_cloud(df, ring_count, config)
    output = save_dataframe(denoised, output_dir / "denoised_point_cloud.csv")
    candidates = save_dataframe(
        denoised[denoised["pred"] != 0], output_dir / "lining_candidates.csv"
    )
    cutoff_path = save_dataframe(cutoffs, output_dir / "density_cutoffs.csv")
    retained = float((denoised["pred"] != 0).mean())
    state = StageState(
        2,
        "denoise",
        "completed",
        profile,
        {"stage": asdict(config), "ring_count": ring_count},
        metrics={
            "point_count": len(denoised),
            "retained_count": int((denoised["pred"] != 0).sum()),
            "retained_ratio": retained,
        },
        upstream_manifest=str(upstream_manifest),
    )
    state.add_artifact("denoised_point_cloud", output.name, "text/csv")
    state.add_artifact("lining_candidates", candidates.name, "text/csv")
    state.add_artifact("density_cutoffs", cutoff_path.name, "text/csv")
    return state.write(output_dir / "manifest.json")
