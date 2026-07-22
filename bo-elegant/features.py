"""Lean Evidence + Coherence feature taxonomy for bo-elegant.

v1 kept det_real_detection_ratio; v2 drops it (regime-confounded under
uniform_k_snap on continuous) and adds regime-neutral detection-quality
signals from k_row_gate.json + phase_check.

Evidence  — artifact / depth-map quality
Coherence — detection + segmentation result form (regime-neutral)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "bo-unified"))

from intrinsics import extract_intrinsics  # noqa: E402
from phase_check import phase_coherence  # noqa: E402

# v2 candidate lean set. Mini-ablation may prune further.
EVIDENCE: tuple[str, ...] = (
    "depth_nan_ratio",
    "denoise_retained_ratio",
)

COHERENCE: tuple[str, ...] = (
    "sam_fill_rate",
    "sam_ontology_divergence",
    "det_row_residual_px",
    "det_row_gated",
    "det_row_y_std",
    "phase_incoherence_deg",
)

CANDIDATE: tuple[str, ...] = EVIDENCE + COHERENCE

# Diagnostic only — not in lean candidate (regime-confounded on t3 snap).
DIAGNOSTIC: tuple[str, ...] = (
    "det_real_detection_ratio",
    "det_fallback_ratio",
    "sam_ring_completeness",
)

DROPPED: dict[str, str] = {
    "det_real_detection_ratio": (
        "regime-confounded under uniform_k_snap: healthy continuous runs "
        "rewrite Types to propagated so ratio=0 even when k_row_gate proves "
        "real anchors; docks every continuous holdout by ~0.18 proxy points"
    ),
    "depth_outlier_ratio": "permutation-control failure of full B2 (family-conditional)",
    "det_fallback_ratio": "exact complement of det_real_detection_ratio; keep diagnostic only",
    "det_midpoint_ratio": "regime-constant / near-zero coef in pooled model",
    "det_n_points": "regime-constant / near-zero coef",
    "det_ring_count_error": "near-zero coef everywhere",
    "det_x_spacing_cv": "near-zero coef everywhere",
    "det_y_std": "sentinel 0 under all-propagated Types; replaced by det_row_y_std",
    "sam_segment_size_cv": "near-zero coef everywhere",
    "sam_ring_completeness": "redundant with sam_fill_rate in v1 ablation",
}

FEATURE_SETS: dict[str, tuple[str, ...]] = {
    "Evidence": EVIDENCE,
    "Coherence": COHERENCE,
    "Evidence+Coherence": CANDIDATE,
}

# Default SAM4Tun K-row design pattern (px). Used when params omit k_row_pattern.
DEFAULT_K_ROW_PATTERN: tuple[float, ...] = (1123.0, 1553.0)

ANCHOR_PARAMS: dict[str, Path] = {
    "1-1": REPO_ROOT / "anchors" / "unified" / "params" / "1-1",
    "2-1": REPO_ROOT / "anchors" / "unified" / "params" / "2-1",
    "3-1": REPO_ROOT / "anchors" / "unified" / "params" / "3-1-1",
    "4-1": REPO_ROOT / "anchors" / "unified" / "params" / "4-1",
    "5-1": REPO_ROOT / "anchors" / "unified" / "params" / "5-1",
}

FAMILY_OF: dict[str, str] = {
    "1": "staggered",
    "2": "staggered",
    "3": "continuous",
    "4": "complex",
    "5": "complex",
}

FAMILY_ANCHOR: dict[str, str] = {
    "staggered": "2-1",
    "continuous": "3-1",
    "complex": "5-1",
}

TRAIN_ANCHORS: tuple[str, ...] = ("2-1", "3-1", "5-1")

HOLDOUT_SUBSETS: dict[str, tuple[str, ...]] = {
    "staggered": ("1-1", "1-2", "1-3", "1-4", "1-5", "2-2", "2-3", "2-4", "2-5"),
    "continuous": ("3-2", "3-3", "3-4", "3-5", "3-6", "3-7", "3-8", "3-9", "3-10"),
    "complex": ("4-1", "4-2", "4-3", "4-4", "4-5", "5-2", "5-3", "5-4", "5-5"),
}


def family_of_subset(subset: str) -> str:
    return FAMILY_OF[subset.split("-")[0]]


def _load_k_row_pattern(params_dir: Path | None) -> list[float]:
    if params_dir is None:
        return list(DEFAULT_K_ROW_PATTERN)
    path = Path(params_dir) / "parameters_detecting.json"
    if not path.exists():
        return list(DEFAULT_K_ROW_PATTERN)
    data = json.loads(path.read_text(encoding="utf-8"))
    raw = data.get("k_row_pattern")
    if raw:
        return [float(v) for v in raw]
    return list(DEFAULT_K_ROW_PATTERN)


def compute_row_features(
    run_dir: Path, *, params_dir: Path | None = None
) -> dict[str, float]:
    """K-row residual / scatter, gate-conditional.

    ``det_row_residual_px`` is only meaningful when ``k_row_gate.json`` exists
    (continuous ``uniform_k_snap`` verification). On ungated families the raw
    design-pattern distance confounds strategy with quality, so residual is
    zeroed and ``det_row_gated=0`` lets the model ignore it.
    """
    run_dir = Path(run_dir)
    out = {
        "det_row_residual_px": 0.0,
        "det_row_gated": 0.0,
        "det_row_y_std": 0.0,
    }
    gate_path = run_dir / "k_row_gate.json"
    if gate_path.exists():
        gate = json.loads(gate_path.read_text(encoding="utf-8"))
        out["det_row_gated"] = 1.0
        if gate.get("distance_px") is not None:
            out["det_row_residual_px"] = float(np.log1p(float(gate["distance_px"])))
        if gate.get("anchor_y_std") is not None:
            out["det_row_y_std"] = float(gate["anchor_y_std"])
        return out

    # Ungated fallback: within-row Y std from prompt CSV only (no residual).
    points = run_dir / "initial_points.csv"
    if not points.exists():
        return out
    df = pd.read_csv(points)
    if df.empty or "Y" not in df.columns:
        return out
    ys = df["Y"].to_numpy(dtype=float)
    ys = ys[np.isfinite(ys)]
    if ys.size == 0:
        return out
    pattern = np.asarray(_load_k_row_pattern(params_dir), dtype=float)
    assigns = np.argmin(np.abs(ys[:, None] - pattern[None, :]), axis=1)
    stds = []
    for i in range(len(pattern)):
        cluster = ys[assigns == i]
        if cluster.size >= 2:
            stds.append(float(np.std(cluster)))
    out["det_row_y_std"] = float(np.mean(stds)) if stds else 0.0
    return out


# Sentinel when phase cannot be scored (empty/failed segmentation, or
# irregular complex stagger). High = incoherent; healthy runs score 1–4°.
PHASE_UNSCORABLE_DEG = 90.0


def compute_phase_feature(run_dir: Path) -> dict[str, float]:
    """phase_incoherence_deg from phase_check; NaN-safe sentinel if unscorable."""
    run_dir = Path(run_dir)
    out = {"phase_incoherence_deg": PHASE_UNSCORABLE_DEG}
    if not (run_dir / "final.csv").exists():
        return out
    try:
        res = phase_coherence(run_dir)
        score = res.get("phase_incoherence_deg")
        if score is not None and np.isfinite(float(score)):
            out["phase_incoherence_deg"] = float(score)
    except Exception:  # noqa: BLE001
        pass
    return out


def lean_vector(
    metrics: dict[str, Any], features: tuple[str, ...] | list[str] = CANDIDATE
) -> dict[str, float]:
    out: dict[str, float] = {}
    for k in features:
        v = metrics.get(k, float("nan"))
        try:
            fv = float(v)
            out[k] = fv if np.isfinite(fv) else float("nan")
        except (TypeError, ValueError):
            out[k] = float("nan")
    return out


def extract_lean(
    run_dir: Path,
    *,
    params_dir: Path | None = None,
    expected_rings: int = 10,
) -> dict[str, Any]:
    """Compute full intrinsics + regime-neutral features, project to lean keys."""
    run_dir = Path(run_dir)
    metrics = extract_intrinsics(
        run_dir,
        params_dir=params_dir,
        expected_rings=expected_rings,
    )
    metrics.update(compute_row_features(run_dir, params_dir=params_dir))
    metrics.update(compute_phase_feature(run_dir))
    lean = lean_vector(metrics)
    lean["orient_h_ring_corr"] = float(metrics.get("orient_h_ring_corr", float("nan")))
    lean["orient_invariant_ok"] = float(metrics.get("orient_invariant_ok", float("nan")))
    # Diagnostics kept for reports / ontology, not for the lean model.
    for k in DIAGNOSTIC:
        lean[k] = float(metrics.get(k, float("nan")))
    return lean


def load_metrics_from_run(run_dir: Path) -> dict[str, Any] | None:
    """Prefer existing intrinsics.json; else None (caller may recompute)."""
    path = Path(run_dir) / "intrinsics.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def features_complete(
    metrics: dict[str, Any], features: tuple[str, ...] | list[str] = CANDIDATE
) -> bool:
    for k in features:
        v = metrics.get(k)
        try:
            if v is None or not np.isfinite(float(v)):
                return False
        except (TypeError, ValueError):
            return False
    return True
