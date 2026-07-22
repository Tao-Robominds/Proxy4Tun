#!/usr/bin/env python3
"""Run missing holdout configs under data/bo-elegant/ (never data/anchors / data/bo).

Reuses bo-unified pipeline + bad_configs. Params follow tunnel-local sibling
(1-x→1-1, 3-x→3-1-1, 4-x→4-1) so new bad runs pair cleanly with reused goods.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
BO_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO_ROOT / "bo-unified"))

from intrinsics import extract_intrinsics, write_intrinsics  # noqa: E402
from param_io import load_anchor_params, load_family_params, materialize_run_params  # noqa: E402
from pipeline import parse_performance, run_stages  # noqa: E402

from features import family_of_subset  # noqa: E402

DATA_ROOT = REPO_ROOT / "data" / "bo-elegant"
BAD_CONFIGS_PATH = REPO_ROOT / "bo-unified" / "family" / "bad_configs.json"
REGISTRY_PATH = BO_DIR / "registry.json"

# Family name mapping for bad_configs keys
FAM_KEY = {"staggered": "t1&2", "continuous": "t3", "complex": "t4&5"}


def _load_bad_overlay(family_key: str) -> dict[str, dict[str, Any]]:
    data = json.loads(BAD_CONFIGS_PATH.read_text(encoding="utf-8"))
    return data[family_key]["overlay"]


def run_one(subset: str, config_kind: str, *, force: bool = False) -> dict[str, Any]:
    if config_kind not in ("anchor", "bad"):
        raise ValueError(config_kind)

    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    entry = next(
        e
        for e in registry["runs"]
        if e["subset"] == subset and e["config_kind"] == config_kind
    )
    family = entry["family"]
    fam_key = FAM_KEY[family]
    params_src = REPO_ROOT / entry["params_dir"]
    input_txt = REPO_ROOT / "data" / "subsets" / f"{subset}.txt"
    if not input_txt.exists():
        raise FileNotFoundError(input_txt)

    study = DATA_ROOT / f"{subset}-holdout"
    runs_root = study / "runs"
    params_root = study / "params"
    logs_root = study / "logs"
    for d in (runs_root, params_root, logs_root):
        d.mkdir(parents=True, exist_ok=True)

    run_id = f"{subset}-{config_kind}"
    run_dir = runs_root / run_id
    log_path = logs_root / f"{run_id}.log"
    manifest_path = study / "manifest.json"

    if manifest_path.exists() and not force:
        man = json.loads(manifest_path.read_text(encoding="utf-8"))
        for rec in man.get("runs", []):
            if rec.get("run_id") == run_id and rec.get("status") == "ok" and rec.get("mIoU") is not None:
                print(f"Skip existing ok run {run_id} mIoU={rec['mIoU']}")
                return rec

    base = load_anchor_params(params_src)
    family_params = load_family_params(params_src)
    overlay: dict[str, dict[str, Any]] = {}
    if "random_seed" not in base.get("unfolding", {}):
        overlay.setdefault("unfolding", {})["random_seed"] = 0
    if config_kind == "bad":
        bad = _load_bad_overlay(fam_key)
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
        expected_rings=10,
    )
    metrics.update({f"perf_{k}": v for k, v in perf.items()})
    write_intrinsics(run_dir, metrics)

    if status == "ok" and miou is None:
        status = "failed"

    rec: dict[str, Any] = {
        "run_id": run_id,
        "subset": subset,
        "family": family,
        "config_kind": config_kind,
        "params_dir": entry["params_dir"],
        "status": status,
        "mIoU": miou,
        "elapsed_s": elapsed,
        "metrics": {k: metrics.get(k) for k in (
            "orient_h_ring_corr",
            "orient_invariant_ok",
            "depth_nan_ratio",
            "denoise_retained_ratio",
            "det_real_detection_ratio",
            "sam_fill_rate",
            "sam_ring_completeness",
            "sam_ontology_divergence",
        )},
        "created_at": datetime.now().isoformat(),
        "path": str(run_dir.relative_to(REPO_ROOT)),
    }

    man = {"subset": subset, "family": family, "runs": []}
    if manifest_path.exists():
        man = json.loads(manifest_path.read_text(encoding="utf-8"))
    man["runs"] = [r for r in man.get("runs", []) if r.get("run_id") != run_id]
    man["runs"].append(rec)
    manifest_path.write_text(json.dumps(man, indent=2) + "\n", encoding="utf-8")
    print(f"{run_id}: status={status} mIoU={miou}")
    return rec


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--all-missing", action="store_true", help="Run every to_run entry")
    parser.add_argument("--subset", type=str, default=None)
    parser.add_argument("--kind", choices=("anchor", "bad"), default=None)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    if not REGISTRY_PATH.exists():
        raise SystemExit("Missing registry.json; run build_registry.py first")

    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    if args.all_missing:
        targets = [e for e in registry["runs"] if e["status"] == "to_run"]
    elif args.subset and args.kind:
        targets = [
            e
            for e in registry["runs"]
            if e["subset"] == args.subset and e["config_kind"] == args.kind
        ]
    else:
        raise SystemExit("Use --all-missing or --subset X --kind {anchor,bad}")

    for e in targets:
        print(f"=== {e['run_id']} ({e['status']}) ===")
        run_one(e["subset"], e["config_kind"], force=args.force)


if __name__ == "__main__":
    main()
