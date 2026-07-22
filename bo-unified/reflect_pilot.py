#!/usr/bin/env python3
"""Manual reflection pilot: apply an overlay and score proxy + mIoU.

Used by the in-IDE reflective-agent pilot (Cursor agent acts as the LLM).

Default: copy frozen stage-1 from the holdout anchor and replay stages 2-6.
With --full: run stages 1-6 (allows unfolding overlays when residual is high).

Usage:
  ./venv/bin/python bo-unified/reflect_pilot.py --subset 4-4 --round 1 \
      --overlay-json '{"detecting": {"hough_threshold_oblique": 35}}'
  ./venv/bin/python bo-unified/reflect_pilot.py --subset 4-3 --round 1 --full \
      --overlay-json '{"unfolding": {"random_seed": 1}}'
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np

REPO_ROOT = Path(__file__).resolve().parent.parent
BO_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BO_DIR))

from intrinsics import extract_intrinsics, write_intrinsics  # noqa: E402
from param_io import load_anchor_params, load_family_params, materialize_run_params  # noqa: E402
from pipeline import DATA_ROOT, copy_checkpoint, parse_performance, run_stages  # noqa: E402
from spaces import holdout_case_config  # noqa: E402

MODELS_PATH = BO_DIR / "family" / "models.json"
REFLECT_ROOT = REPO_ROOT / "data" / "reflect"


def proxy_score(family: str, metrics: dict[str, Any]) -> float:
    models = json.loads(MODELS_PATH.read_text(encoding="utf-8"))
    model = models["families"][family]["model"]
    feats = model["features"]
    x = np.array([float(metrics.get(f, float("nan"))) for f in feats])
    mean = np.array(model["scaler_mean"])
    scale = np.array(model["scaler_scale"])
    z = (x - mean) / scale
    return float(np.dot(z, np.array(model["coef"])) + model["intercept"])


def run_round(
    subset: str,
    round_id: int,
    overlay: dict[str, dict[str, Any]],
    arm: str,
    *,
    full: bool = False,
) -> dict[str, Any]:
    cfg = holdout_case_config(subset)
    family = cfg["family"]
    input_txt = REPO_ROOT / cfg["input_txt"]

    anchor_run = DATA_ROOT / f"{subset}-family-proxy" / "runs" / f"{subset}-anchor"
    anchor_params = DATA_ROOT / f"{subset}-family-proxy" / "params" / f"{subset}-anchor"
    if not full and not (anchor_run / "state.pkl").exists():
        raise FileNotFoundError(f"Missing anchor stage-1 checkpoint at {anchor_run}")

    # Unfolding overlays require a full 1–6 rerun.
    if overlay.get("unfolding") and not full:
        full = True

    out_root = REFLECT_ROOT / subset / arm
    run_id = f"round{round_id}"
    run_dir = out_root / run_id
    params_root = out_root / "params"
    logs_root = out_root / "logs"
    for d in (out_root, params_root, logs_root):
        d.mkdir(parents=True, exist_ok=True)

    base = load_anchor_params(anchor_params)
    family_params = load_family_params(anchor_params)
    params_dir = materialize_run_params(
        params_root / run_id, base, overlay, family_params=family_params
    )

    if run_dir.exists():
        shutil.rmtree(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)

    start_stage = 1 if full else 2
    if not full:
        copy_checkpoint(anchor_run, run_dir)

    log_path = logs_root / f"{run_id}.log"
    status = "ok"
    log_text = ""
    elapsed = 0.0
    try:
        log_text, elapsed = run_stages(
            run_id=run_id,
            params_dir=params_dir,
            input_txt=input_txt,
            out_root=out_root,
            log_path=log_path,
            start_stage=start_stage,
            end_stage=6,
        )
    except RuntimeError as exc:
        status = "failed"
        print(f"FAILED: {exc}", file=sys.stderr)
        if log_path.exists():
            log_text = log_path.read_text(encoding="utf-8")

    perf = parse_performance(run_dir / "evaluation" / "performance.md")
    metrics = extract_intrinsics(
        run_dir,
        params_dir=params_dir,
        log_text=log_text,
        expected_rings=int(cfg["expected_rings"]),
    )
    metrics.update({f"perf_{k}": v for k, v in perf.items()})
    write_intrinsics(run_dir, metrics)

    score = proxy_score(family, metrics)
    rec = {
        "subset": subset,
        "arm": arm,
        "round": round_id,
        "status": status,
        "full_pipeline": full,
        "start_stage": start_stage,
        "overlay": overlay,
        "proxy_score": score,
        "mIoU": perf.get("mIoU"),
        "perf": perf,
        "intrinsics": {k: v for k, v in metrics.items() if not k.startswith("tier")},
        "elapsed_s": elapsed,
        "output_dir": str(run_dir),
        "log_path": str(log_path),
        "finished_at": datetime.now().isoformat(),
    }
    rec_path = run_dir / "reflection_record.json"
    rec_path.write_text(json.dumps(rec, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                k: rec[k]
                for k in (
                    "subset",
                    "round",
                    "status",
                    "full_pipeline",
                    "proxy_score",
                    "mIoU",
                    "elapsed_s",
                    "output_dir",
                )
            },
            indent=2,
        )
    )
    return rec


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--subset", required=True)
    p.add_argument("--round", type=int, required=True)
    p.add_argument("--overlay-json", required=True, help="JSON dict stage -> {param: value}")
    p.add_argument("--arm", default="cursor")
    p.add_argument(
        "--full",
        action="store_true",
        help="Run stages 1–6 (required for unfolding overlays; auto-enabled if overlay has unfolding)",
    )
    p.add_argument("--score-anchor", action="store_true", help="Only print anchor proxy score")
    args = p.parse_args()

    if args.score_anchor:
        cfg = holdout_case_config(args.subset)
        anchor_run = DATA_ROOT / f"{args.subset}-family-proxy" / "runs" / f"{args.subset}-anchor"
        metrics = json.loads((anchor_run / "intrinsics.json").read_text(encoding="utf-8"))
        print(json.dumps({"anchor_proxy": proxy_score(cfg["family"], metrics), "anchor_mIoU": metrics.get("perf_mIoU")}))
        return

    overlay = json.loads(args.overlay_json)
    run_round(args.subset, args.round, overlay, args.arm, full=args.full)


if __name__ == "__main__":
    main()
