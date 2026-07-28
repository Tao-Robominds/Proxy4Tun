#!/usr/bin/env python3
"""Score any completed pipeline run with the frozen pooled lean proxy.

Usage:
  ./venv/bin/python bo-full-stage/score_run.py data/reflect/3-4/cursor3/round1 --subset 3-4
  ./venv/bin/python bo-full-stage/score_run.py --subset 3-4 --anchor
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(OUT_DIR))
sys.path.insert(0, str(REPO_ROOT / "bo-elegant"))
sys.path.insert(0, str(REPO_ROOT / "bo-unified"))

from features import ANCHOR_PARAMS, CANDIDATE, extract_lean  # noqa: E402
from spaces import sibling_anchor_case  # noqa: E402
from train_proxy import predict  # noqa: E402

MODELS = OUT_DIR / "models.json"
STAGE1 = OUT_DIR / "stage1_features.json"


def _params_for(subset: str) -> Path:
    if subset in ANCHOR_PARAMS:
        return ANCHOR_PARAMS[subset]
    return ANCHOR_PARAMS[sibling_anchor_case(subset)]


def _anchor_run_dir(subset: str) -> Path:
    candidates = [
        REPO_ROOT / "data" / "bo-unified" / f"{subset}-family-proxy" / "runs" / f"{subset}-anchor",
        REPO_ROOT / "data" / "bo-elegant" / f"{subset}-holdout" / "runs" / f"{subset}-anchor",
        REPO_ROOT / "data" / "anchors" / subset,
    ]
    for c in candidates:
        if (c / "final.csv").exists() or (c / "state.pkl").exists():
            return c
    raise FileNotFoundError(f"No anchor run found for {subset}; tried {candidates}")


def score_run(
    run_dir: Path,
    subset: str,
    *,
    model: dict[str, Any] | None = None,
    stage1: dict[str, Any] | None = None,
    log_text: str = "",
) -> dict[str, Any]:
    models = json.loads(MODELS.read_text(encoding="utf-8")) if model is None else None
    model = model or models["model"]
    alarm_thr = float((models or json.loads(MODELS.read_text(encoding="utf-8")))["alarm_threshold"])
    stage1 = stage1 if stage1 is not None else (
        json.loads(STAGE1.read_text(encoding="utf-8")) if STAGE1.exists() else {}
    )

    params = _params_for(subset)
    metrics = extract_lean(run_dir, params_dir=params, log_text=log_text)
    s1 = stage1.get(subset, {})
    if s1.get("status") == "ok":
        # Backfill stage-1 residual/orientation only when the run itself lacks them
        # (frozen stage-1 checkpoints often omit residual from later-stage logs).
        if not math.isfinite(float(metrics.get("recentre_residual_max_cm", float("nan")))):
            metrics["recentre_residual_max_cm"] = float(
                s1.get("recentre_residual_max_cm", float("nan"))
            )
            metrics["unfold_residual"] = float(s1.get("unfold_residual", 0.0))
        if not math.isfinite(float(metrics.get("orient_axis_corr", float("nan")))):
            if "orient_axis_corr" in s1:
                metrics["orient_axis_corr"] = float(s1["orient_axis_corr"])
                metrics["orient_agreement"] = abs(float(s1["orient_axis_corr"]))


    feat = {k: float(metrics.get(k, 0.0) or 0.0) for k in CANDIDATE}
    for k, v in list(feat.items()):
        if not math.isfinite(v):
            feat[k] = 0.0
    proxy = float(predict(model, pd.DataFrame([feat]))[0])

    # Optional GT mIoU from evaluation/performance.md or intrinsics
    miou = metrics.get("perf_mIoU")
    if miou is None:
        perf_path = run_dir / "evaluation" / "performance.md"
        if perf_path.exists():
            import re

            m = re.search(r"Mean IoU \(mIoU\):\s*([\d.]+)", perf_path.read_text(encoding="utf-8"))
            if m:
                miou = float(m.group(1))
    if miou is None and (run_dir / "intrinsics.json").exists():
        intr = json.loads((run_dir / "intrinsics.json").read_text(encoding="utf-8"))
        miou = intr.get("perf_mIoU")

    resid = float(metrics.get("recentre_residual_max_cm", float("nan")))
    corr = float(metrics.get("orient_axis_corr", float("nan")))
    return {
        "subset": subset,
        "run_dir": str(run_dir),
        "proxy": proxy,
        "alarm": proxy <= alarm_thr,
        "alarm_threshold": alarm_thr,
        "mIoU": float(miou) if miou is not None and math.isfinite(float(miou)) else None,
        "features": feat,
        "recentre_residual_max_cm": resid if math.isfinite(resid) else None,
        "orient_axis_corr": corr if math.isfinite(corr) else None,
    }


def main() -> None:
    p = argparse.ArgumentParser(description="Score a run with frozen pooled lean proxy")
    p.add_argument("run_dir", nargs="?", type=Path, default=None)
    p.add_argument("--subset", required=True)
    p.add_argument("--anchor", action="store_true", help="Score the holdout/family anchor run")
    args = p.parse_args()

    if args.anchor:
        run_dir = _anchor_run_dir(args.subset)
    elif args.run_dir is not None:
        run_dir = args.run_dir
    else:
        p.error("Provide run_dir or --anchor")

    out = score_run(run_dir, args.subset)
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
