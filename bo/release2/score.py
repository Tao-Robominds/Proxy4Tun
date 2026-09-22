#!/usr/bin/env python3
"""Score a run with the frozen release-2 four-feature proxy.

Loads only configs/proxy/four_feature.json. Bands:
  flag    score < 0.5
  refine  0.5 <= score <= 0.7
  accept  score > 0.7
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from bo.paths import REPO_ROOT
from bo.release2.measure import measure_run

MODEL_PATH = REPO_ROOT / "configs" / "proxy" / "four_feature.json"


def load_model(path: Path | None = None) -> dict[str, Any]:
    path = Path(path) if path is not None else MODEL_PATH
    return json.loads(path.read_text(encoding="utf-8"))


def band(score: float) -> str:
    if score < 0.5:
        return "flag"
    if score <= 0.7:
        return "refine"
    return "accept"


def score_measurements(measurements: dict[str, float], model: dict[str, Any] | None = None) -> dict[str, Any]:
    model = model or load_model()
    features = list(model["features"])
    x = np.asarray([float(measurements[name]) for name in features], dtype=float)
    mu = np.asarray(model["mu"], dtype=float)
    sigma = np.asarray(model["sigma"], dtype=float)
    sigma = np.where(np.abs(sigma) < 1e-8, 1.0, sigma)
    raw = float(model["intercept"] + np.dot(model["w"], (x - mu) / sigma))
    clipped = float(min(1.0, max(0.0, raw)))
    return {
        "score_raw": raw,
        "score": clipped,
        "band": band(clipped),
        "features": {name: float(measurements[name]) for name in features},
    }


def score_run(run_dir: Path, subset: str, params_dir: Path, *, log_text: str = "") -> dict[str, Any]:
    measured = measure_run(run_dir, subset, params_dir, log_text=log_text)
    scored = score_measurements(measured["measurements"])
    scored["finite"] = measured["finite"]
    return scored
