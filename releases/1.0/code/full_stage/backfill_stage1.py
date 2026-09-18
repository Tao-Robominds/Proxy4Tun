#!/usr/bin/env python3
"""Stage-1-only residual backfill for reused training + holdout subsets.

One stage-1 run per subset (anchor unfolding params). Residual is a property of
subset + stage-1 params; orientation is recomputed from unwrapped.csv.
Writes data/bo-full-stage/stage1-logs/<subset>/ and stage1_features.json.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))
from bo.paths import REPO_ROOT, FULL_STAGE_DATA, FULL_STAGE_PKG
from bo.unified.param_io import load_anchor_params, load_family_params, materialize_run_params
from bo.unified.pipeline import run_stages
from bo.unified.spaces import CASE_CONFIG, FAMILY_HOLDOUT_SUBSETS, family_of_subset, sibling_anchor_case
from bo.unified.intrinsics import (
    compute_orient_axis,
    parse_tier0_from_log,
)
from bo.elegant.features import ANCHOR_PARAMS, HOLDOUT_SUBSETS, TRAIN_ANCHORS, family_of_subset as fam_of

DATA_ROOT = FULL_STAGE_DATA
OUT_JSON = FULL_STAGE_PKG / "stage1_features.json"


def all_subsets() -> list[str]:
    subs = list(TRAIN_ANCHORS)
    for fam_subs in HOLDOUT_SUBSETS.values():
        for s in fam_subs:
            if s not in subs:
                subs.append(s)
    return sorted(subs)


def params_for_subset(subset: str) -> Path:
    if subset in ANCHOR_PARAMS:
        return ANCHOR_PARAMS[subset]
    sibling = sibling_anchor_case(subset)
    return ANCHOR_PARAMS[sibling]


def input_txt_for(subset: str) -> Path:
    return REPO_ROOT / "data" / "subsets" / f"{subset}.txt"


def run_stage1(subset: str, *, force: bool = False) -> dict[str, Any]:
    out_root = DATA_ROOT / "stage1-logs"
    run_dir = out_root / subset
    params_root = out_root / "params" / subset
    log_path = out_root / "logs" / f"{subset}.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    feat_cache = OUT_JSON
    if feat_cache.exists() and not force:
        cache = json.loads(feat_cache.read_text(encoding="utf-8"))
        if subset in cache and cache[subset].get("status") == "ok":
            print(f"Skip cached {subset}: residual={cache[subset].get('recentre_residual_max_cm')}")
            return cache[subset]

    params_src = params_for_subset(subset)
    base = load_anchor_params(params_src)
    family_params = load_family_params(params_src)
    # Always enable residual recentre so the Evidence feature is measurable.
    overlay = {"unfolding": {"residual_recentre": True}}
    params_dir = materialize_run_params(
        params_root, base, overlay, family_params=family_params
    )

    if run_dir.exists():
        shutil.rmtree(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)

    status = "ok"
    log_text = ""
    elapsed = 0.0
    try:
        log_text, elapsed = run_stages(
            run_id=subset,
            params_dir=params_dir,
            input_txt=input_txt_for(subset),
            out_root=out_root,
            log_path=log_path,
            start_stage=1,
            end_stage=1,
        )
    except RuntimeError as exc:
        print(f"FAILED stage1 {subset}: {exc}")
        status = "failed"
        if log_path.exists():
            log_text = log_path.read_text(encoding="utf-8")

    tier0 = parse_tier0_from_log(log_text)
    axis = compute_orient_axis(run_dir, None)
    resid = float(tier0.get("recentre_residual_max_cm", float("nan")))
    corr = float(axis.get("orient_axis_corr", float("nan")))
    agreement = abs(corr) if corr == corr else float("nan")

    import math

    unfold = float(math.log1p(resid)) if resid == resid and resid >= 0 else float("nan")

    rec = {
        "subset": subset,
        "status": status,
        "elapsed_s": elapsed,
        "recentre_residual_max_cm": resid,
        "unfold_residual": unfold,
        "orient_axis_corr": corr,
        "orient_agreement": agreement,
        "orient_invariant_ok": float(axis.get("orient_invariant_ok", float("nan"))),
        "path": str(run_dir.relative_to(REPO_ROOT)),
        "created_at": datetime.now().isoformat(),
    }

    cache: dict[str, Any] = {}
    if feat_cache.exists():
        cache = json.loads(feat_cache.read_text(encoding="utf-8"))
    cache[subset] = rec
    feat_cache.write_text(json.dumps(cache, indent=2) + "\n", encoding="utf-8")
    print(
        f"stage1 {subset}: status={status} residual_cm={resid} "
        f"orient_agreement={agreement} elapsed={elapsed:.1f}s"
    )
    return rec


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--subset", type=str, default=None)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--train-only", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    if args.subset:
        subs = [args.subset]
    elif args.train_only:
        subs = list(TRAIN_ANCHORS)
    elif args.all:
        subs = all_subsets()
    else:
        parser.error("Provide --subset, --train-only, or --all")

    for s in subs:
        if not input_txt_for(s).exists():
            print(f"WARN skip missing input {s}")
            continue
        run_stage1(s, force=args.force)


if __name__ == "__main__":
    main()
