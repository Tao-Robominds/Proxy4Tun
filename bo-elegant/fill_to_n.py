#!/usr/bin/env python3
"""Top up bo-elegant train anchors to N successful trials each.

Uses archived rows in family/training_table.csv plus new Sobol trials under
data/bo-elegant/<case>-trials/ (never writes data/anchors, data/bo, data/baseline).

Failed overlays are skipped; the loop continues until each case has N ok rows
in the training table (or max-attempts is hit).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
BO_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BO_DIR))
sys.path.insert(0, str(REPO_ROOT / "bo-unified"))

from features import TRAIN_ANCHORS  # noqa: E402
from run_trials import _sobol_overlays, run_trial  # noqa: E402
from spaces import CASE_CONFIG  # noqa: E402
from intrinsics import extract_intrinsics, TIER1_KEYS  # noqa: E402

TRAIN_CSV = BO_DIR / "family" / "training_table.csv"
V1_FEATS = [
    "depth_nan_ratio",
    "denoise_retained_ratio",
    "det_real_detection_ratio",
    "sam_fill_rate",
    "sam_ring_completeness",
    "sam_ontology_divergence",
]


def _family_code(case: str) -> str:
    return CASE_CONFIG[case]["family"]


def _max_trial_index(case: str) -> int:
    man_path = REPO_ROOT / "data" / "bo-elegant" / f"{case}-trials" / "manifest.json"
    if not man_path.exists():
        return -1
    man = json.loads(man_path.read_text(encoding="utf-8"))
    idxs = []
    for t in man.get("trials", []):
        tid = str(t.get("trial_id", ""))
        if "-t" in tid:
            suffix = tid.rsplit("-t", 1)[-1]
            if suffix.isdigit():
                idxs.append(int(suffix))
    return max(idxs) if idxs else -1


def _row_from_trial(case: str, rec: dict[str, Any]) -> dict[str, Any] | None:
    if rec.get("status") != "ok" or rec.get("mIoU") is None:
        return None
    run_dir = REPO_ROOT / rec["path"]
    params_dir = REPO_ROOT / "data" / "bo-elegant" / f"{case}-trials" / "params" / rec["trial_id"]
    metrics = extract_intrinsics(
        run_dir,
        params_dir=params_dir if params_dir.exists() else None,
        expected_rings=int(CASE_CONFIG[case]["expected_rings"]),
    )
    row = {
        "case": case,
        "family": _family_code(case),
        "mIoU": float(rec["mIoU"]),
        "trial_id": rec["trial_id"],
        "source": "bo-elegant-fill",
    }
    for k in V1_FEATS:
        if k not in metrics or metrics[k] is None:
            print(f"WARN incomplete features for {rec['trial_id']}: missing {k}")
            return None
        row[k] = float(metrics[k])
    return row


def _load_table() -> pd.DataFrame:
    if TRAIN_CSV.exists():
        return pd.read_csv(TRAIN_CSV)
    return pd.DataFrame(columns=V1_FEATS + ["mIoU", "case", "family"])


def fill_case(case: str, target: int, *, seed: int, max_attempts: int) -> pd.DataFrame:
    df = _load_table()
    # Drop prior fill rows for this case so re-runs are idempotent on archived base
    # Keep archived + any fill; we only append new unique trial_ids.
    have = int((df["case"] == case).sum())
    print(f"{case}: currently {have}/{target} in {TRAIN_CSV.name}")
    if have >= target:
        return df

    need = target - have
    attempts = 0
    added = 0
    next_idx = _max_trial_index(case) + 1
    # Generate a large Sobol pool with a distinct seed so we don't replay crashy overlays.
    pool = _sobol_overlays(case, max(max_attempts, need * 3), seed=seed)
    pool_i = 0

    while added < need and attempts < max_attempts:
        if pool_i >= len(pool):
            # extend pool with a new seed
            seed += 17
            pool = _sobol_overlays(case, max_attempts, seed=seed)
            pool_i = 0
        overlay = pool[pool_i]
        pool_i += 1
        trial_id = f"{case}-t{next_idx:03d}"
        next_idx += 1
        attempts += 1
        rec = run_trial(case, trial_id, overlay, acquisition="sobol_fill", force=False)
        row = _row_from_trial(case, rec)
        if row is None:
            print(f"  skip failed/incomplete {trial_id} ({added}/{need} added)")
            continue
        df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
        # Persist after each success
        cols = [c for c in ["depth_nan_ratio", "denoise_retained_ratio", "det_real_detection_ratio",
                            "sam_fill_rate", "sam_ring_completeness", "sam_ontology_divergence",
                            "mIoU", "case", "family"] if c in df.columns]
        # Keep optional provenance cols if present
        for extra in ("trial_id", "source"):
            if extra in df.columns and extra not in cols:
                cols.append(extra)
        df[cols].to_csv(TRAIN_CSV, index=False)
        added += 1
        have = int((df["case"] == case).sum())
        print(f"  added {trial_id} mIoU={row['mIoU']:.3f} -> {have}/{target}")

    have = int((df["case"] == case).sum())
    if have < target:
        raise RuntimeError(f"{case}: only reached {have}/{target} after {attempts} attempts")
    return df


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--target", type=int, default=40)
    p.add_argument("--cases", nargs="+", default=list(TRAIN_ANCHORS))
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--max-attempts", type=int, default=30, help="Per-case attempt cap")
    p.add_argument("--one", action="store_true", help="Single-instance proof: one fill trial on first short case")
    args = p.parse_args()

    df = _load_table()
    short = [c for c in args.cases if int((df["case"] == c).sum()) < args.target]
    if not short:
        print(f"All cases already at {args.target}.")
        print(df.groupby("case").size().to_string())
        return

    if args.one:
        case = short[0]
        print(f"SINGLE-INSTANCE GATE: one fill trial on {case}")
        before = int((df["case"] == case).sum())
        fill_case(case, before + 1, seed=args.seed, max_attempts=args.max_attempts)
        df = _load_table()
        after = int((df["case"] == case).sum())
        print(
            f"GATE RESULT case={case} before={before} after={after} "
            f"pass={after == before + 1}"
        )
        if after != before + 1:
            raise SystemExit(1)
        return

    for i, case in enumerate(short):
        fill_case(case, args.target, seed=args.seed + 100 * i, max_attempts=args.max_attempts)

    df = _load_table()
    print("Final counts:")
    print(df.groupby(["family", "case"]).size().to_string())
    print(f"Total n={len(df)} -> {TRAIN_CSV}")


if __name__ == "__main__":
    main()
