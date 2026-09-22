"""Ten manuscript measurements for a completed release-2 run.

PQ: unfold_residual, orient_agreement, denoise_retained_ratio, depth_nan_ratio.
SC: ring_count_error (|N_det - N_exp|, unnormalised), boundary_explained_edge@25,
correspondence_f1@15, chamfer_sym_px, sam_fill_rate, phase_incoherence_deg.

N_exp comes from engineering metadata. N_det is the stage-1 slice count
(the same count the detector uses as ring_count). No proxy scoring.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

from bo.runtime.features import compute_phase_feature, stage1_evidence_features
from bo.runtime.intrinsics import extract_intrinsics
from bo.runtime.metadata import expected_rings
from bo.sc_general.features import all_features
from bo.sc_general.label_map import build_label_map
from bo.sc_general.replay import find_ring_count, replay_run

MEASUREMENT_KEYS: tuple[str, ...] = (
    "unfold_residual",
    "orient_agreement",
    "denoise_retained_ratio",
    "depth_nan_ratio",
    "ring_count_error",
    "boundary_explained_edge@25",
    "correspondence_f1@15",
    "chamfer_sym_px",
    "sam_fill_rate",
    "phase_incoherence_deg",
)


def measurements_finite(values: dict[str, float]) -> bool:
    for key in MEASUREMENT_KEYS:
        try:
            if not math.isfinite(float(values[key])):
                return False
        except (KeyError, TypeError, ValueError):
            return False
    return True


def measure_run(
    run_dir: Path,
    subset: str,
    params_dir: Path,
    *,
    log_text: str = "",
) -> dict[str, Any]:
    """Return the ten measurements plus ring-count diagnostics."""
    run_dir = Path(run_dir)
    params_dir = Path(params_dir)
    n_exp = expected_rings(subset)
    metrics = extract_intrinsics(
        run_dir,
        params_dir=params_dir,
        log_text=log_text,
        expected_rings=n_exp,
    )
    metrics.update(compute_phase_feature(run_dir))
    metrics.update(stage1_evidence_features(metrics, params_dir=params_dir))

    n_det, n_det_source = find_ring_count(run_dir)
    lines = replay_run(
        run_dir,
        params_dir=params_dir,
        ring_count=n_det,
        write_shadow=False,
    )
    label_map = build_label_map(run_dir, params_dir=params_dir)
    sc = all_features(lines, label_map, ring_count=n_det)

    values = {
        "unfold_residual": float(metrics.get("unfold_residual", float("nan"))),
        "orient_agreement": float(metrics.get("orient_agreement", float("nan"))),
        "denoise_retained_ratio": float(metrics.get("denoise_retained_ratio", float("nan"))),
        "depth_nan_ratio": float(metrics.get("depth_nan_ratio", float("nan"))),
        "ring_count_error": float(abs(int(n_det) - int(n_exp))),
        "boundary_explained_edge@25": float(sc.get("boundary_explained_edge@25", float("nan"))),
        "correspondence_f1@15": float(sc.get("correspondence_f1@15", float("nan"))),
        "chamfer_sym_px": float(sc.get("chamfer_sym_px", float("nan"))),
        "sam_fill_rate": float(metrics.get("sam_fill_rate", float("nan"))),
        "phase_incoherence_deg": float(metrics.get("phase_incoherence_deg", float("nan"))),
    }
    return {
        "measurements": values,
        "finite": measurements_finite(values),
        "expected_rings": int(n_exp),
        "ring_count": int(n_det),
        "ring_count_source": n_det_source,
    }
