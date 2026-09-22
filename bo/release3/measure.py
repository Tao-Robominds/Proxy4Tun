"""Eleven measurements for a release-3 run (ten release-2 + rotation candidates).

The original ten keys are unchanged. Rotation candidates are appended and never
alter the existing values.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

from bo.release2.measure import MEASUREMENT_KEYS as BASE_KEYS
from bo.release2.measure import measure_run as measure_run_base
from bo.release3.rotation_features import compute_rotation_features

ROTATION_KEYS: tuple[str, ...] = (
    "key_block_mismatch",
    "rotation_advantage",
    "rotation_gap",
    "key_observability",
)
MEASUREMENT_KEYS: tuple[str, ...] = BASE_KEYS + ROTATION_KEYS


def measurements_finite(values: dict[str, float], *, require_rotation: bool = True) -> bool:
    keys = MEASUREMENT_KEYS if require_rotation else BASE_KEYS
    for key in keys:
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
    base = measure_run_base(run_dir, subset, params_dir, log_text=log_text)
    rot = compute_rotation_features(run_dir, params_dir=params_dir, subset=subset)
    values = dict(base["measurements"])
    values.update(rot)
    return {
        "measurements": values,
        "finite": measurements_finite(values),
        "expected_rings": base["expected_rings"],
        "ring_count": base["ring_count"],
        "ring_count_source": base["ring_count_source"],
    }
