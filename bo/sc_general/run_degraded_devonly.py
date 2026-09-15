#!/usr/bin/env python3
"""Run degraded overlays selected from development-only calibration trials.

Writes under data/<subset>-degraded-devonly/ (never data/bo/, data/anchors/).
Overlays come from bo/sc_general/degraded_overlays_devonly.json.
"""

from __future__ import annotations

import argparse
import json
import math
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from bo.paths import REPO_ROOT  # noqa: E402
from bo.sc_general.build_tables import process_run  # noqa: E402
from bo.unified.intrinsics import extract_intrinsics, has_complete_tier1, write_intrinsics  # noqa: E402
from bo.unified.param_io import load_anchor_params, load_family_params, materialize_run_params  # noqa: E402
from bo.unified.pipeline import parse_performance, run_stages  # noqa: E402
from bo.unified.spaces import (  # noqa: E402
    CASE_CONFIG,
    all_holdout_subsets,
    family_of_subset,
    holdout_case_config,
)

OVERLAYS_PATH = Path(__file__).resolve().parent / "degraded_overlays_devonly.json"
EVIDENCE_DIR = REPO_ROOT / "data" / "sc-general" / "stage2_devonly"
DATA_ROOT = REPO_ROOT / "data"

# Evaluation subsets that appear in the 54-run holdout but are not in
# all_holdout_subsets() (those three share the elegant holdout paths today).
EXTRA_EVAL_SUBSETS = ("1-1", "3-2", "4-1")
DEV_GATE_SUBSETS = ("2-1", "3-1", "5-1")
FAMILY_LABEL = {"t1&2": "staggered", "t3": "continuous", "t4&5": "complex"}
LEAN4 = (
    "correspondence_f1@15",
    "sam_fill_rate",
    "ring_count_error",
    "depth_nan_ratio",
)


def load_overlays() -> dict[str, Any]:
    return json.loads(OVERLAYS_PATH.read_text(encoding="utf-8"))


def study_root(subset: str) -> Path:
    return (DATA_ROOT / f"{subset}-degraded-devonly").resolve()


def case_config_for(subset: str) -> dict[str, Any]:
    if subset in CASE_CONFIG:
        cfg = dict(CASE_CONFIG[subset])
        cfg["subset"] = subset
        cfg["sibling"] = subset
        return cfg
    return holdout_case_config(subset)


def all_eval_subsets() -> list[str]:
    return list(all_holdout_subsets()) + list(EXTRA_EVAL_SUBSETS)


def _load_overlay(family: str) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    data = load_overlays()
    if family not in data["families"]:
        raise KeyError(f"No overlay for family {family!r} in {OVERLAYS_PATH}")
    entry = data["families"][family]
    return entry["overlay"], entry


def run_degraded(
    subset: str,
    *,
    force: bool = False,
    write_lean: bool = False,
) -> dict[str, Any]:
    cfg = case_config_for(subset)
    family = family_of_subset(subset)
    input_txt = REPO_ROOT / cfg["input_txt"]
    if not input_txt.exists():
        raise FileNotFoundError(f"Missing subset file {input_txt}")

    study = study_root(subset)
    runs_root = study / "runs"
    params_root = study / "params"
    logs_root = study / "logs"
    for d in (runs_root, params_root, logs_root):
        d.mkdir(parents=True, exist_ok=True)

    run_id = f"{subset}-bad"
    run_dir = runs_root / run_id
    log_path = logs_root / f"{run_id}.log"
    manifest_path = study / "manifest.json"

    if manifest_path.exists() and not force:
        man = json.loads(manifest_path.read_text(encoding="utf-8"))
        for rec in man.get("runs", []):
            if rec.get("run_id") == run_id and rec.get("status") == "ok" and rec.get("mIoU") is not None:
                print(f"Skip existing ok run {run_id} mIoU={rec['mIoU']}")
                if write_lean and not rec.get("lean_features"):
                    lean = process_run(run_dir, write_shadow=False)
                    rec["lean_features"] = {k: lean.get(k) for k in LEAN4}
                    (run_dir / "lean_features.json").write_text(
                        json.dumps(lean, indent=2) + "\n", encoding="utf-8"
                    )
                return rec

    params_src = REPO_ROOT / cfg["params_dir"]
    base = load_anchor_params(params_src)
    family_params = load_family_params(params_src)
    overlay: dict[str, dict[str, Any]] = {}
    if "random_seed" not in base.get("unfolding", {}):
        overlay.setdefault("unfolding", {})["random_seed"] = 0

    bad, overlay_meta = _load_overlay(family)
    for stage, kv in bad.items():
        if stage == "unfolding":
            continue
        overlay.setdefault(stage, {}).update(kv)

    params_dir = materialize_run_params(
        params_root / run_id, base, overlay, family_params=family_params
    )

    if run_dir.exists():
        shutil.rmtree(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)

    status = "ok"
    log_text = ""
    elapsed = 0.0
    try:
        log_text, elapsed = run_stages(
            run_id=run_id,
            params_dir=params_dir,
            input_txt=input_txt,
            out_root=runs_root,
            log_path=log_path,
            start_stage=1,
            end_stage=6,
        )
    except RuntimeError as exc:
        print(f"FAILED {run_id}: {exc}")
        status = "failed"
        if log_path.exists():
            log_text = log_path.read_text(encoding="utf-8")

    perf = parse_performance(run_dir / "evaluation" / "performance.md")
    miou = perf.get("mIoU")
    metrics = extract_intrinsics(
        run_dir,
        params_dir=params_dir,
        log_text=log_text,
        expected_rings=int(cfg["expected_rings"]),
    )
    metrics.update({f"perf_{k}": v for k, v in perf.items()})
    write_intrinsics(run_dir, metrics)

    lean: dict[str, Any] = {}
    if write_lean and status == "ok":
        lean = process_run(run_dir, write_shadow=False)
        (run_dir / "lean_features.json").write_text(
            json.dumps(lean, indent=2) + "\n", encoding="utf-8"
        )

    if status == "ok" and miou is None:
        status = "failed"

    rec: dict[str, Any] = {
        "run_id": run_id,
        "subset": subset,
        "family": family,
        "family_label": FAMILY_LABEL[family],
        "config_kind": "bad",
        "sibling": cfg.get("sibling"),
        "params_dir": cfg["params_dir"],
        "overlay_trial_id": overlay_meta["trial_id"],
        "overlay_source_mIoU": overlay_meta["mIoU"],
        "status": status,
        "mIoU": miou,
        "elapsed_s": elapsed,
        "tier1_complete": has_complete_tier1(metrics),
        "metrics": metrics,
        "lean_features": {
            k: lean.get(k) for k in LEAN4
        }
        if lean
        else None,
        "output_dir": str(run_dir),
        "log_path": str(log_path),
        "params_path": str(params_dir),
        "finished_at": datetime.now().isoformat(),
    }

    if manifest_path.exists():
        man = json.loads(manifest_path.read_text(encoding="utf-8"))
    else:
        man = {"subset": subset, "family": family, "runs": []}
    man["runs"] = [r for r in man.get("runs", []) if r.get("run_id") != run_id]
    man["runs"].append(rec)
    man["updated_at"] = datetime.now().isoformat()
    man["overlay_trial_id"] = overlay_meta["trial_id"]
    manifest_path.write_text(json.dumps(man, indent=2) + "\n", encoding="utf-8")

    print(
        f"{run_id} status={status} mIoU={miou} elapsed={elapsed:.1f}s "
        f"tier1_ok={rec['tier1_complete']} overlay={overlay_meta['trial_id']}"
    )
    return rec


def run_gate(dev_subset: str, *, force: bool = False) -> dict[str, Any]:
    if dev_subset not in DEV_GATE_SUBSETS:
        raise ValueError(f"gate subset must be one of {DEV_GATE_SUBSETS}, got {dev_subset!r}")

    family = family_of_subset(dev_subset)
    family_label = FAMILY_LABEL[family]
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

    rec = run_degraded(dev_subset, force=force, write_lean=True)
    miou = rec.get("mIoU")
    miou_f = float(miou) if miou is not None else float("nan")
    lean = rec.get("lean_features") or {}
    metrics = rec.get("metrics") or {}
    # correspondence_f1@15 / ring_count_error from lean replay;
    # sam_fill_rate / depth_nan_ratio from stage intrinsics (same sources as
    # the holdout table join).
    feature_vals = {
        "correspondence_f1@15": lean.get("correspondence_f1@15"),
        "ring_count_error": lean.get("ring_count_error"),
        "sam_fill_rate": metrics.get("sam_fill_rate"),
        "depth_nan_ratio": metrics.get("depth_nan_ratio"),
    }
    lean_finite = {
        k: bool(v is not None and math.isfinite(float(v))) for k, v in feature_vals.items()
    }
    passed = (
        rec["status"] == "ok"
        and math.isfinite(miou_f)
        and miou_f < 0.15
        and all(lean_finite.values())
    )
    evidence = EVIDENCE_DIR / f"gate_{family_label}.json"
    gate = {
        "case": dev_subset,
        "family": family,
        "family_label": family_label,
        "gate_kind": "degraded_devonly",
        "command": (
            f"./venv/bin/python -m bo.sc_general.run_degraded_devonly "
            f"--gate {dev_subset}"
        ),
        "lineage": (
            f"overlay from {OVERLAYS_PATH.name} "
            f"(trial {rec.get('overlay_trial_id')}) → "
            f"data/{dev_subset}-degraded-devonly/runs/{dev_subset}-bad; "
            f"base params {rec.get('params_dir')}; stages 1–6"
        ),
        "pass_fail_criteria": {
            "pipeline_ok": rec["status"] == "ok",
            "miou_finite_and_lt_0.15": bool(math.isfinite(miou_f) and miou_f < 0.15),
            "lean4_finite": lean_finite,
        },
        "measured_mIoU": miou,
        "lean_features": feature_vals,
        "tier1_complete": rec["tier1_complete"],
        "passed": passed,
        "evidence_path": str(evidence),
        "output_dir": rec["output_dir"],
        "log_path": rec["log_path"],
        "study_root": str(study_root(dev_subset)),
    }
    evidence.write_text(json.dumps(gate, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(gate, indent=2))
    if not passed:
        raise RuntimeError(f"Dev-only degradation gate FAILED for {dev_subset}; see {evidence}")
    return gate


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--gate", type=str, default=None, help="dev subset for single-instance gate")
    p.add_argument("--subset", type=str, default=None)
    p.add_argument("--all-eval", action="store_true", help="run all 27 evaluation degraded cases")
    p.add_argument("--force", action="store_true")
    args = p.parse_args()

    if args.gate:
        run_gate(args.gate, force=args.force)
        return

    if args.all_eval:
        for subset in all_eval_subsets():
            run_degraded(subset, force=args.force)
        return

    if args.subset:
        run_degraded(args.subset, force=args.force)
        return

    p.error("Specify --gate, --subset, or --all-eval")


if __name__ == "__main__":
    main()
