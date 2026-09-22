"""Template-free label-rotation features for Release 3.

Uses predicted labels and ring ids from ``final.csv`` plus the fixed design
widths in ``parameters_sam.json``. Stage-4 joint lines (when available) feed
the observability flag only. Mask-template geometry is never used as evidence.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from bo.runtime.metadata import family_of
from bo.sc_general.label_map import block_to_label_from_config, load_sam_config
from bo.sc_general.replay import find_params_dir, replay_run

MIN_PTS = 40
JOINT_TOL_M = 0.15


def _design_width_m(block: str, cfg: dict[str, Any]) -> float:
    k = float(cfg["K_height"]) / 1000.0
    ab = float(cfg["AB_height"]) / 1000.0
    return k if block == "K" else ab


def _circular_width(theta: np.ndarray) -> float:
    """Arc length of a contiguous block along unwrapped theta (metres)."""
    if len(theta) < 2:
        return 0.0
    t = np.sort(theta.astype(float))
    span = float(t[-1] - t[0])
    if len(t) < 4:
        return span
    gaps = np.diff(t)
    max_gap = float(gaps.max())
    # Wrap cut: one large interior gap relative to the rest.
    if max_gap > 0.3 * max(span, 1e-6) and max_gap > 3.0 * float(np.median(gaps)):
        return float(span - max_gap)
    return span


def _segments_for_ring(
    ring_df: pd.DataFrame,
    b2l: dict[str, int],
    order: list[str],
) -> list[dict[str, Any]] | None:
    """Ordered contiguous lining segments along theta for one ring."""
    blocks = ring_df[ring_df["pred"] > 0]
    if len(blocks) < MIN_PTS:
        return None
    # Sort by theta and walk label runs.
    order_idx = {name: i for i, name in enumerate(order)}
    l2b = {v: k for k, v in b2l.items()}
    sorted_df = blocks.sort_values("theta")
    labels = sorted_df["pred"].to_numpy(dtype=int)
    thetas = sorted_df["theta"].to_numpy(dtype=float)
    runs: list[dict[str, Any]] = []
    start = 0
    for i in range(1, len(labels) + 1):
        if i == len(labels) or labels[i] != labels[start]:
            lab = int(labels[start])
            block = l2b.get(lab)
            if block is None:
                start = i
                continue
            seg_theta = thetas[start:i]
            runs.append(
                {
                    "label": lab,
                    "block": block,
                    "order_index": order_idx.get(block, -1),
                    "n": int(len(seg_theta)),
                    "width": _circular_width(seg_theta),
                    "theta_mean": float(np.mean(seg_theta)),
                    "theta_min": float(seg_theta.min()),
                    "theta_max": float(seg_theta.max()),
                }
            )
            start = i
    # Merge wrap-around if first and last share the same label.
    if len(runs) >= 2 and runs[0]["label"] == runs[-1]["label"]:
        a, b = runs[0], runs[-1]
        merged = {
            "label": a["label"],
            "block": a["block"],
            "order_index": a["order_index"],
            "n": a["n"] + b["n"],
            "width": a["width"] + b["width"],
            "theta_mean": 0.5 * (a["theta_mean"] + b["theta_mean"]),
            "theta_min": min(a["theta_min"], b["theta_min"]),
            "theta_max": max(a["theta_max"], b["theta_max"]),
        }
        runs = [merged] + runs[1:-1]
    # Keep the largest run per block name (handles fragmented labels).
    best: dict[str, dict[str, Any]] = {}
    for r in runs:
        prev = best.get(r["block"])
        if prev is None or r["n"] > prev["n"]:
            best[r["block"]] = r
    if len(best) < 3:
        return None
    ordered = sorted(best.values(), key=lambda r: r["theta_mean"])
    return ordered


def _mismatch_for_assignment(
    segments: list[dict[str, Any]],
    order: list[str],
    shift: int,
    cfg: dict[str, Any],
) -> float:
    """Mean relative width error under cyclic label assignment."""
    ab = float(cfg["AB_height"]) / 1000.0
    if ab <= 0:
        return float("nan")
    n = len(order)
    if not segments:
        return float("nan")
    # Align: map ordered segments onto the cyclic order by nearest count.
    # Use the n largest segments if more, or all if fewer.
    segs = sorted(segments, key=lambda s: -s["n"])[:n]
    segs = sorted(segs, key=lambda s: s["theta_mean"])
    if len(segs) < 3:
        return float("nan")
    errs = []
    for i, seg in enumerate(segs):
        block = order[(i + shift) % n]
        design = _design_width_m(block, cfg)
        errs.append(abs(seg["width"] - design) / ab)
    return float(np.mean(errs))


def _current_shift(segments: list[dict[str, Any]], order: list[str]) -> int:
    """Infer which cyclic shift best matches the current labels."""
    n = len(order)
    segs = sorted(segments, key=lambda s: -s["n"])[:n]
    segs = sorted(segs, key=lambda s: s["theta_mean"])
    if not segs:
        return 0
    # Prefer alignment that places the current K segment on order index 0.
    k_segs = [s for s in segs if s["block"] == "K"]
    if k_segs:
        k_pos = segs.index(max(k_segs, key=lambda s: s["n"]))
        # order[0] should be K; shift such that (k_pos + shift) % n == 0 => shift = -k_pos
        return (-k_pos) % n
    # Fall back: maximise name agreement.
    best_s, best_hits = 0, -1
    for s in range(n):
        hits = sum(1 for i, seg in enumerate(segs) if order[(i + s) % n] == seg["block"])
        if hits > best_hits:
            best_hits, best_s = hits, s
    return best_s


def _joint_ys_m(run_dir: Path, params_dir: Path, resolution: float) -> np.ndarray:
    """Approximate joint y positions in metres of arc (depth-map y * resolution)."""
    try:
        ls = replay_run(run_dir, params_dir=params_dir, write_shadow=False, keep_maps=False)
    except Exception:  # noqa: BLE001
        return np.zeros(0, dtype=float)
    segs = ls.joint_segments()
    if len(segs) == 0:
        return np.zeros(0, dtype=float)
    # Depth map y is the circumferential axis; convert with resolution (m/px).
    ys = []
    for x1, y1, x2, y2 in segs:
        ys.append(0.5 * (float(y1) + float(y2)) * resolution)
    return np.asarray(ys, dtype=float)


def compute_rotation_features(
    run_dir: Path,
    *,
    params_dir: Path | None = None,
    subset: str | None = None,
) -> dict[str, float]:
    """Return key_block_mismatch, rotation_advantage, rotation_gap, key_observability."""
    run_dir = Path(run_dir)
    params_dir = Path(params_dir) if params_dir else find_params_dir(run_dir)
    cfg = load_sam_config(run_dir, params_dir=params_dir)
    b2l, order = block_to_label_from_config(cfg)
    ab = float(cfg["AB_height"]) / 1000.0
    resolution = float((cfg.get("processing") or {}).get("resolution", 0.005))

    final_path = run_dir / "final.csv"
    if not final_path.exists():
        return {
            "key_block_mismatch": float("nan"),
            "rotation_advantage": float("nan"),
            "rotation_gap": float("nan"),
            "key_observability": float("nan"),
        }
    df = pd.read_csv(final_path, usecols=["theta", "pred", "pred_ring"])
    joint_ys = _joint_ys_m(run_dir, params_dir, resolution)

    ring_mismatches = []
    ring_advantages = []
    ring_gaps = []
    obs_flags = []
    weights = []

    for ring, ring_df in df.groupby("pred_ring"):
        segs = _segments_for_ring(ring_df, b2l, order)
        if segs is None:
            continue
        n = len(order)
        cur = _current_shift(segs, order)
        errors = [_mismatch_for_assignment(segs, order, s, cfg) for s in range(n)]
        errors = [e for e in errors if math.isfinite(e)]
        if not errors:
            continue
        e_cur = _mismatch_for_assignment(segs, order, cur, cfg)
        e_best = min(errors)
        sorted_e = sorted(errors)
        gap = float(sorted_e[1] - sorted_e[0]) if len(sorted_e) >= 2 else 0.0
        adv = float(e_cur - e_best) if math.isfinite(e_cur) else float("nan")

        k_segs = [s for s in segs if s["block"] == "K"]
        if k_segs:
            kseg = max(k_segs, key=lambda s: s["n"])
            km = abs(kseg["width"] - _design_width_m("K", cfg)) / ab
            # Observability: enough points and at least one joint near either edge.
            near = 0
            if len(joint_ys):
                for edge in (kseg["theta_min"], kseg["theta_max"]):
                    if float(np.min(np.abs(joint_ys - edge))) <= JOINT_TOL_M:
                        near += 1
            observable = 1.0 if (kseg["n"] >= MIN_PTS and (near >= 1 or len(joint_ys) == 0)) else 0.0
        else:
            km = 1.0
            observable = 0.0

        w = float(len(ring_df[ring_df["pred"] > 0]))
        ring_mismatches.append(km)
        ring_advantages.append(adv if math.isfinite(adv) else 0.0)
        ring_gaps.append(gap)
        obs_flags.append(observable)
        weights.append(w)

    if not weights:
        return {
            "key_block_mismatch": float("nan"),
            "rotation_advantage": float("nan"),
            "rotation_gap": float("nan"),
            "key_observability": float("nan"),
        }
    w = np.asarray(weights, dtype=float)
    w = w / w.sum()
    return {
        "key_block_mismatch": float(np.dot(w, np.asarray(ring_mismatches))),
        "rotation_advantage": float(np.dot(w, np.asarray(ring_advantages))),
        "rotation_gap": float(np.dot(w, np.asarray(ring_gaps))),
        "key_observability": float(np.mean(obs_flags)),
    }


def shift_labels_cyclic(
    labels: np.ndarray,
    *,
    shift: int,
    n_classes: int,
) -> np.ndarray:
    """Cyclically shift positive lining labels; background 0 unchanged.

    Labels are assumed 1..n_classes in segment_order index order.
    """
    out = labels.copy()
    pos = out > 0
    # Map label id -> 0-based index, shift, map back.
    idx = out[pos] - 1
    idx = (idx + int(shift)) % int(n_classes)
    out[pos] = idx + 1
    return out
