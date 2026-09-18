"""Post-hoc analysis for ablation study results."""

from __future__ import annotations

import csv
import json
import statistics
from pathlib import Path
from typing import Any

from design import FACTOR_MAP, FRACTIONAL_7F_RES4


def load_results_csv(path: Path) -> list[dict[str, str]]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def metric_float(row: dict[str, str], key: str) -> float | None:
    val = row.get(key, "")
    if val in ("", None):
        return None
    return float(val)


def fractional_effects(results: list[dict[str, str]], high_miou: float) -> list[dict[str, Any]]:
    """Estimate main effects from 7-factor fractional design."""
    rows_by_id = {r["run_id"]: r for r in results}
    effects: list[dict[str, Any]] = []
    for factor in FACTOR_MAP:
        high_vals: list[float] = []
        low_vals: list[float] = []
        for i, design_row in enumerate(FRACTIONAL_7F_RES4):
            rid = f"p3_ff7_{i:02d}"
            r = rows_by_id.get(rid)
            if not r:
                continue
            miou = metric_float(r, "mIoU")
            if miou is None:
                continue
            if design_row[factor] == +1:
                high_vals.append(miou)
            else:
                low_vals.append(miou)
        if high_vals and low_vals:
            effect = statistics.mean(high_vals) - statistics.mean(low_vals)
            effects.append({
                "factor": factor,
                "param": FACTOR_MAP[factor][1],
                "stage": FACTOR_MAP[factor][0],
                "effect_mIoU": effect,
                "n_high": len(high_vals),
                "n_low": len(low_vals),
            })
    effects.sort(key=lambda x: abs(x["effect_mIoU"]), reverse=True)
    return effects


def confirmation_stats(results: list[dict[str, str]], prefix: str, key: str = "mIoU") -> dict[str, Any]:
    vals: list[float] = []
    for r in results:
        if r["run_id"].startswith(prefix):
            v = metric_float(r, key)
            if v is not None:
                vals.append(v)
    if not vals:
        return {}
    return {
        "n": len(vals),
        "median": statistics.median(vals),
        "mean": statistics.mean(vals),
        "stdev": statistics.pstdev(vals) if len(vals) > 1 else 0.0,
        "min": min(vals),
        "max": max(vals),
    }


def build_summary(study_root: Path) -> dict[str, Any]:
    results = load_results_csv(study_root / "results.csv")
    by_id = {r["run_id"]: r for r in results}
    high_miou = metric_float(by_id["anchor_high"], "mIoU") or 0.0

    p2_ranking: list[dict[str, Any]] = []
    for r in results:
        if not r["run_id"].startswith("p2_"):
            continue
        miou = metric_float(r, "mIoU")
        if miou is None:
            continue
        p2_ranking.append({
            "factor": r["run_id"].replace("p2_", "", 1),
            "mIoU": miou,
            "delta_mIoU": miou - high_miou,
            "mAP": metric_float(r, "mAP"),
            "delta_mAP": (metric_float(r, "mAP") or 0) - (metric_float(by_id["anchor_high"], "mAP") or 0),
        })
    p2_ranking.sort(key=lambda x: abs(x["delta_mIoU"]), reverse=True)

    return {
        "high_miou": high_miou,
        "low_miou": metric_float(by_id.get("anchor_low", {}), "mIoU"),
        "fractional_effects": fractional_effects(results, high_miou),
        "p2_ranking": p2_ranking,
        "confirm_high": confirmation_stats(results, "p4_confirm_high"),
        "confirm_low": confirmation_stats(results, "p4_confirm_low"),
        "confirm_depth_high": confirmation_stats(results, "p4_confirm_enhance_depth_threshold_high"),
        "confirm_depth_low": confirmation_stats(results, "p4_confirm_enhance_depth_threshold_low"),
    }
