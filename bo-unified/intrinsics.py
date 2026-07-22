"""GT-free intrinsic metrics from pipeline artifacts.

Tier 0 — gate invariants (stage-1; gate whether the Tier-1 proxy applies):
  orient_h_ring_corr, recentre_residual_max (from log if available)

Tier 1 — proxy features (denoising / detection / SAM):
  Provenance-aware: regularity metrics use real detections only.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

REAL_TYPES = frozenset({"midpoint", "positive_slope", "negative_slope", "horizontal"})
FALLBACK_TYPES = frozenset({"assume", "propagated", "default"})

TIER0_KEYS = (
    "orient_h_ring_corr",
    "orient_invariant_ok",
    "recentre_residual_max_cm",
)

TIER1_KEYS = (
    "denoise_retained_ratio",
    "depth_nan_ratio",
    "depth_outlier_ratio",
    "det_midpoint_ratio",
    "det_real_detection_ratio",
    "det_fallback_ratio",
    "det_x_spacing_cv",
    "det_y_std",
    "det_ring_count_error",
    "det_n_points",
    "sam_fill_rate",
    "sam_ring_completeness",
    "sam_segment_size_cv",
    "sam_ontology_divergence",
)

CANON_INVARIANT_RE = re.compile(
    r"Canonical invariant:\s*corr\(h,\s*ring\)\s*=\s*([+-]?\d+(?:\.\d+)?)"
)
RECENTRE_RE = re.compile(
    r"Residual recentre:.*?max\s*=\s*([+-]?\d+(?:\.\d+)?)\s*cm",
    re.IGNORECASE,
)


def _safe_cv(values: np.ndarray) -> float:
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]
    if values.size < 2:
        return float("nan")
    mean = float(np.mean(values))
    if abs(mean) < 1e-12:
        return float("nan")
    return float(np.std(values) / abs(mean))


def parse_tier0_from_log(log_text: str, h_ring_sign: int | None = None) -> dict[str, float]:
    out: dict[str, float] = {
        "orient_h_ring_corr": float("nan"),
        "orient_invariant_ok": float("nan"),
        "recentre_residual_max_cm": float("nan"),
    }
    m = CANON_INVARIANT_RE.search(log_text or "")
    if m:
        corr = float(m.group(1))
        out["orient_h_ring_corr"] = corr
        if h_ring_sign is not None:
            out["orient_invariant_ok"] = float(
                (np.sign(corr) == np.sign(h_ring_sign)) and abs(corr) > 0.5
            )
        else:
            out["orient_invariant_ok"] = float(abs(corr) > 0.5)
    m = RECENTRE_RE.search(log_text or "")
    if m:
        out["recentre_residual_max_cm"] = float(m.group(1))
    return out


def compute_orient_from_unwrapped(
    run_dir: Path, h_ring_sign: int | None = None
) -> dict[str, float]:
    path = Path(run_dir) / "unwrapped.csv"
    out: dict[str, float] = {
        "orient_h_ring_corr": float("nan"),
        "orient_invariant_ok": float("nan"),
        "recentre_residual_max_cm": float("nan"),
    }
    if not path.exists():
        return out
    df = pd.read_csv(path, usecols=["h", "ring"])
    corr = float(df["h"].corr(df["ring"]))
    out["orient_h_ring_corr"] = corr
    if h_ring_sign is not None and np.isfinite(corr):
        out["orient_invariant_ok"] = float(
            (np.sign(corr) == np.sign(h_ring_sign)) and abs(corr) > 0.5
        )
    elif np.isfinite(corr):
        out["orient_invariant_ok"] = float(abs(corr) > 0.5)
    return out


def compute_denoise_enhancing(run_dir: Path) -> dict[str, float]:
    run_dir = Path(run_dir)
    out = {
        "denoise_retained_ratio": float("nan"),
        "depth_nan_ratio": float("nan"),
        "depth_outlier_ratio": float("nan"),
    }
    den = run_dir / "denoised.csv"
    if den.exists():
        pred = pd.read_csv(den, usecols=["pred"])["pred"].to_numpy()
        out["denoise_retained_ratio"] = float(np.mean(pred != 0))
    dm_path = run_dir / "depth_map.npy"
    if dm_path.exists():
        dm = np.load(dm_path)
        out["depth_nan_ratio"] = float(np.isnan(dm).mean())
    do_path = run_dir / "depth_map_outlier.npy"
    if do_path.exists():
        do = np.load(do_path)
        # Outlier maps store r-values at outlier pixels and NaN elsewhere.
        if do.dtype == bool:
            out["depth_outlier_ratio"] = float(do.mean())
        else:
            out["depth_outlier_ratio"] = float(np.mean(np.isfinite(do)))
    return out


def compute_detection(
    run_dir: Path, expected_rings: int = 10
) -> dict[str, float]:
    run_dir = Path(run_dir)
    out = {
        "det_midpoint_ratio": float("nan"),
        "det_real_detection_ratio": float("nan"),
        "det_fallback_ratio": float("nan"),
        "det_x_spacing_cv": float("nan"),
        "det_y_std": float("nan"),
        "det_ring_count_error": float("nan"),
        "det_n_points": float("nan"),
    }
    path = run_dir / "initial_points.csv"
    if not path.exists():
        return out
    df = pd.read_csv(path)
    if df.empty or "Type" not in df.columns:
        return out
    types = df["Type"].astype(str).str.strip().str.lower()
    n = len(types)
    out["det_n_points"] = float(n)
    out["det_midpoint_ratio"] = float((types == "midpoint").mean())
    out["det_real_detection_ratio"] = float(types.isin(REAL_TYPES).mean())
    out["det_fallback_ratio"] = float(types.isin(FALLBACK_TYPES).mean())
    out["det_ring_count_error"] = float(abs(n - expected_rings) / max(expected_rings, 1))

    real = df.loc[types.isin(REAL_TYPES)].copy()
    # Provenance-aware: regularity only over real detections. When none exist
    # (e.g. T3 uniform_k_snap -> all propagated), emit defined sentinels so the
    # feature vector stays complete; det_fallback_ratio carries the regime signal.
    if len(real) >= 2 and "X" in real.columns:
        xs = np.sort(real["X"].to_numpy(dtype=float))
        gaps = np.diff(xs)
        out["det_x_spacing_cv"] = _safe_cv(gaps)
        if not np.isfinite(out["det_x_spacing_cv"]):
            out["det_x_spacing_cv"] = 0.0
    else:
        out["det_x_spacing_cv"] = 0.0
    if len(real) >= 2 and "Y" in real.columns:
        out["det_y_std"] = float(np.std(real["Y"].to_numpy(dtype=float)))
    else:
        out["det_y_std"] = 0.0
    return out


def compute_sam(
    run_dir: Path,
    *,
    segment_order: list[str] | None = None,
    ring_completeness_threshold: float = 0.5,
) -> dict[str, float]:
    run_dir = Path(run_dir)
    out = {
        "sam_fill_rate": float("nan"),
        "sam_ring_completeness": float("nan"),
        "sam_segment_size_cv": float("nan"),
        "sam_ontology_divergence": float("nan"),
    }
    path = run_dir / "only_label.csv"
    if not path.exists():
        return out
    # Prefer pred columns only (GT-free). Fall back if column names differ.
    usecols = None
    peek = pd.read_csv(path, nrows=0)
    cols = list(peek.columns)
    want = [c for c in ("pred_labels", "pred_rings") if c in cols]
    if want:
        usecols = want
    df = pd.read_csv(path, usecols=usecols)
    if "pred_labels" not in df.columns:
        return out
    labels = df["pred_labels"].to_numpy()
    out["sam_fill_rate"] = float(np.mean(labels > 0))

    if "pred_rings" not in df.columns:
        return out
    rings = df["pred_rings"].to_numpy()
    # Ignore background-only / invalid ring ids (<=0)
    valid = rings > 0
    if not valid.any():
        return out
    ring_ids = np.unique(rings[valid])
    coverages = []
    sizes = []
    for rid in ring_ids:
        mask = rings == rid
        coverages.append(float(np.mean(labels[mask] > 0)))
        # segment sizes for non-background classes within ring
        lab = labels[mask]
        for c in np.unique(lab):
            if c <= 0:
                continue
            sizes.append(float(np.sum(lab == c)))
    out["sam_ring_completeness"] = float(
        np.mean(np.asarray(coverages) >= ring_completeness_threshold)
    )
    out["sam_segment_size_cv"] = _safe_cv(np.asarray(sizes, dtype=float))

    # Ontology: expect roughly equal mass for each non-background class in segment_order
    n_seg = len(segment_order) if segment_order else int(max(int(labels.max()), 0))
    if n_seg <= 0:
        return out
    # Class ids 1..n_seg map to segment_order order
    hist = np.zeros(n_seg, dtype=float)
    for c in range(1, n_seg + 1):
        hist[c - 1] = float(np.sum(labels == c))
    total = hist.sum()
    if total <= 0:
        out["sam_ontology_divergence"] = 1.0
        return out
    p = hist / total
    q = np.full(n_seg, 1.0 / n_seg)
    # Total variation distance in [0, 1]
    out["sam_ontology_divergence"] = float(0.5 * np.abs(p - q).sum())
    return out


def load_segment_order(params_dir: Path | None) -> list[str] | None:
    if params_dir is None:
        return None
    path = Path(params_dir) / "parameters_sam.json"
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    order = data.get("segment_order")
    return list(order) if order else None


def load_h_ring_sign(params_dir: Path | None) -> int | None:
    if params_dir is None:
        return None
    path = Path(params_dir) / "parameters_unfolding.json"
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    if "h_ring_sign" not in data:
        return None
    return int(data["h_ring_sign"])


def extract_intrinsics(
    run_dir: Path,
    *,
    params_dir: Path | None = None,
    log_text: str = "",
    expected_rings: int = 10,
    ring_completeness_threshold: float = 0.5,
) -> dict[str, Any]:
    """Compute all Tier-0 + Tier-1 metrics for a run directory."""
    run_dir = Path(run_dir)
    h_sign = load_h_ring_sign(params_dir)
    segment_order = load_segment_order(params_dir)

    tier0 = parse_tier0_from_log(log_text, h_sign)
    # Prefer artifact-derived corr when available (works without logs)
    from_csv = compute_orient_from_unwrapped(run_dir, h_sign)
    if np.isfinite(from_csv["orient_h_ring_corr"]):
        tier0["orient_h_ring_corr"] = from_csv["orient_h_ring_corr"]
        tier0["orient_invariant_ok"] = from_csv["orient_invariant_ok"]
    # Keep recentre from log if present; CSV does not store it

    metrics: dict[str, Any] = {}
    metrics.update(tier0)
    metrics.update(compute_denoise_enhancing(run_dir))
    metrics.update(compute_detection(run_dir, expected_rings=expected_rings))
    metrics.update(
        compute_sam(
            run_dir,
            segment_order=segment_order,
            ring_completeness_threshold=ring_completeness_threshold,
        )
    )
    metrics["tier0_keys"] = list(TIER0_KEYS)
    metrics["tier1_keys"] = list(TIER1_KEYS)
    return metrics


def write_intrinsics(run_dir: Path, metrics: dict[str, Any]) -> Path:
    path = Path(run_dir) / "intrinsics.json"
    # JSON-serialize without numpy types
    payload = {}
    for k, v in metrics.items():
        if isinstance(v, (list, dict, str, bool)) or v is None:
            payload[k] = v
        elif isinstance(v, (int, np.integer)):
            payload[k] = int(v)
        else:
            try:
                fv = float(v)
                payload[k] = None if not np.isfinite(fv) else fv
            except (TypeError, ValueError):
                payload[k] = v
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def tier1_vector(metrics: dict[str, Any]) -> dict[str, float]:
    return {k: float(metrics.get(k, float("nan"))) for k in TIER1_KEYS}


def has_complete_tier1(metrics: dict[str, Any]) -> bool:
    for k in TIER1_KEYS:
        v = metrics.get(k)
        try:
            if v is None or not np.isfinite(float(v)):
                return False
        except (TypeError, ValueError):
            return False
    return True


def verify_anchors(
    repo_root: Path,
    cases: tuple[str, ...] = ("1-1", "3-1-1", "5-1"),
) -> dict[str, Any]:
    """Read-only verification against frozen data/anchors/<case>/ trees."""
    repo_root = Path(repo_root)
    case_params = {
        "1-1": repo_root / "anchors" / "t1&2" / "1-1",
        "2-1": repo_root / "anchors" / "t1&2" / "2-1",
        "3-1-1": repo_root / "anchors" / "t3" / "3-1-1",
        "4-1": repo_root / "anchors" / "t4&5" / "4-1",
        "5-1": repo_root / "anchors" / "t4&5" / "5-1",
    }
    results: dict[str, Any] = {}
    for case in cases:
        run_dir = repo_root / "data" / "anchors" / case
        params = case_params[case]
        log_path = repo_root / "logs" / f"{case}-canonical.log"
        log_text = log_path.read_text(encoding="utf-8") if log_path.exists() else ""
        metrics = extract_intrinsics(run_dir, params_dir=params, log_text=log_text)
        results[case] = {
            "complete_tier1": has_complete_tier1(metrics),
            "orient_invariant_ok": metrics.get("orient_invariant_ok"),
            "metrics": {k: metrics.get(k) for k in (*TIER0_KEYS, *TIER1_KEYS)},
        }
    return results


if __name__ == "__main__":
    import pprint
    import sys

    root = Path(__file__).resolve().parent.parent
    report = verify_anchors(root)
    pprint.pp(report)
    ok = all(v["complete_tier1"] and v["orient_invariant_ok"] == 1.0 for v in report.values())
    sys.exit(0 if ok else 1)
