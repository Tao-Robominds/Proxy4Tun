#!/usr/bin/env python3
"""Merge reused v2 artifact-complete trials with new full-pipeline trials.

Produces bo-full-stage/training_table.csv with exactly 40 rows per family
anchor (2-1, 3-1, 5-1), plus provenance columns.
"""

from __future__ import annotations

import json
import math
import re
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))
from bo.paths import REPO_ROOT, ELEGANT_DATA, ELEGANT_PKG, FULL_STAGE_DATA, FULL_STAGE_PKG
from bo.elegant.features import (
    ANCHOR_PARAMS,
    CANDIDATE,
    TRAIN_ANCHORS,
    extract_lean,
    features_complete,
    family_of_subset,
)
from bo.unified.pipeline import parse_performance

OUT = FULL_STAGE_PKG / "training_table.csv"
STAGE1 = FULL_STAGE_PKG / "stage1_features.json"
V2_TABLE = ELEGANT_PKG / "family" / "training_table_v2.csv"
V2_DATA = ELEGANT_DATA
FULL_DATA = FULL_STAGE_DATA

# Cap reused 3-1 rows so we leave room for >=10 stage-1-varied trials.
REUSE_CAP = {"2-1": 14, "3-1": 30, "5-1": 21}
TARGET_N = 40


def _apply_stage1(row: dict[str, Any], stage1: dict[str, Any], case: str) -> dict[str, Any]:
    s1 = stage1.get(case, {})
    if s1.get("status") == "ok":
        row["unfold_residual"] = float(s1.get("unfold_residual", 0.0))
        row["orient_agreement"] = float(s1.get("orient_agreement", 0.0))
        row["recentre_residual_max_cm"] = float(s1.get("recentre_residual_max_cm", float("nan")))
        row["orient_axis_corr"] = float(s1.get("orient_axis_corr", float("nan")))
    else:
        row.setdefault("unfold_residual", 0.0)
        row.setdefault("orient_agreement", 0.0)
    return row


def collect_reused(stage1: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Return (kept rows, excluded-for-balance rows)."""
    kept: list[dict[str, Any]] = []
    excluded: list[dict[str, Any]] = []
    v2 = pd.read_csv(V2_TABLE)

    for case in TRAIN_ANCHORS:
        case_rows = v2[v2["case"] == case].copy()
        # Prefer anchor row first, then by trial_id
        case_rows["_is_anchor"] = case_rows["trial_id"].astype(str).str.endswith("-anchor")
        case_rows = case_rows.sort_values(["_is_anchor", "trial_id"], ascending=[False, True])
        cap = REUSE_CAP[case]
        for i, (_, r) in enumerate(case_rows.iterrows()):
            run_path = None
            # Resolve artifact path
            if str(r["source"]) == "data/anchors":
                run_path = REPO_ROOT / "data" / "anchors" / case
            else:
                man = V2_DATA / f"{case}-trials" / "manifest.json"
                if man.exists():
                    trials = json.loads(man.read_text())["trials"]
                    match = next((t for t in trials if t["trial_id"] == r["trial_id"]), None)
                    if match:
                        run_path = REPO_ROOT / match["path"]
            metrics: dict[str, Any] = {}
            if run_path and run_path.exists():
                metrics = extract_lean(run_path, params_dir=ANCHOR_PARAMS[case])
            row = {
                "source": "reuse_v2",
                "case": case,
                "family": family_of_subset(case),
                "trial_id": str(r["trial_id"]),
                "mIoU": float(r["mIoU"]),
                "stage1_varied": False,
                "path": str(run_path.relative_to(REPO_ROOT)) if run_path else "",
            }
            for k in CANDIDATE:
                if k in metrics and metrics[k] == metrics[k]:
                    row[k] = float(metrics[k])
                elif k in r and pd.notna(r[k]):
                    row[k] = float(r[k])
                else:
                    row[k] = float("nan")
            row = _apply_stage1(row, stage1, case)
            # Recompute orientation from artifacts when possible (overrides stage1 log)
            if run_path and (run_path / "unwrapped.csv").exists():
                m2 = extract_lean(run_path, params_dir=ANCHOR_PARAMS[case])
                if m2.get("orient_agreement") == m2.get("orient_agreement"):
                    row["orient_agreement"] = float(m2["orient_agreement"])
                if m2.get("orient_axis_corr") == m2.get("orient_axis_corr"):
                    row["orient_axis_corr"] = float(m2["orient_axis_corr"])
            if i < cap:
                kept.append(row)
            else:
                excluded.append({**row, "exclude_reason": "balance_for_stage1_spread"})
    return kept, excluded


def collect_new() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for case in TRAIN_ANCHORS:
        man_path = FULL_DATA / f"{case}-trials" / "manifest.json"
        if not man_path.exists():
            continue
        man = json.loads(man_path.read_text(encoding="utf-8"))
        for t in man.get("trials", []):
            if t.get("status") != "ok" or t.get("mIoU") is None:
                continue
            run_dir = REPO_ROOT / t["path"]
            log_path = FULL_DATA / f"{case}-trials" / "logs" / f"{t['trial_id']}.log"
            log_text = log_path.read_text(encoding="utf-8") if log_path.exists() else ""
            metrics = extract_lean(
                run_dir,
                params_dir=ANCHOR_PARAMS[case],
                log_text=log_text,
            )
            if not features_complete(metrics, CANDIDATE):
                print(f"WARN incomplete new trial {t['trial_id']}")
                continue
            row = {
                "source": "bo-full-stage",
                "case": case,
                "family": family_of_subset(case),
                "trial_id": t["trial_id"],
                "mIoU": float(t["mIoU"]),
                "stage1_varied": bool(t.get("stage1_varied", True)),
                "path": t["path"],
                **{k: float(metrics[k]) for k in CANDIDATE},
                "recentre_residual_max_cm": float(
                    metrics.get("recentre_residual_max_cm", float("nan"))
                ),
                "orient_axis_corr": float(metrics.get("orient_axis_corr", float("nan"))),
            }
            rows.append(row)
    return rows


def main() -> None:
    if not STAGE1.exists():
        raise SystemExit(f"Missing {STAGE1}; run backfill_stage1.py --train-only first")
    stage1 = json.loads(STAGE1.read_text(encoding="utf-8"))
    reused, excluded = collect_reused(stage1)
    new_rows = collect_new()

    # Cap new rows per case to fill to TARGET_N
    by_case_new: dict[str, list[dict[str, Any]]] = {c: [] for c in TRAIN_ANCHORS}
    for r in new_rows:
        by_case_new[r["case"]].append(r)

    final: list[dict[str, Any]] = []
    summary = {}
    reused_by = {}
    for r in reused:
        reused_by.setdefault(r["case"], []).append(r)

    for case in TRAIN_ANCHORS:
        rlist = reused_by.get(case, [])
        nlist = by_case_new.get(case, [])
        need = TARGET_N - len(rlist)
        take = nlist[: max(0, need)]
        final.extend(rlist)
        final.extend(take)
        summary[case] = {
            "reused": len(rlist),
            "new": len(take),
            "total": len(rlist) + len(take),
            "new_available": len(nlist),
        }

    df = pd.DataFrame(final)
    df = df.drop_duplicates(subset=["trial_id"], keep="last").reset_index(drop=True)
    df.to_csv(OUT, index=False)

    excl_path = FULL_STAGE_PKG / "excluded_for_balance.json"
    excl_path.write_text(json.dumps(excluded, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    print(f"Wrote {OUT} n={len(df)}")
    print(df.groupby("case").size().to_string())


if __name__ == "__main__":
    main()
