#!/usr/bin/env python3
"""Held-out subset runner for bo-unified proxy evaluation.

Outputs under data/bo-unified/<subset>-family-proxy/ (never data/bo, data/anchors).
Uses sibling unified params; does not override random_seed (baked into params).
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

REPO_ROOT = Path(__file__).resolve().parent.parent
BO_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BO_DIR))

from intrinsics import extract_intrinsics, has_complete_tier1, write_intrinsics  # noqa: E402
from param_io import load_anchor_params, load_family_params, materialize_run_params  # noqa: E402
from pipeline import DATA_ROOT, parse_performance, run_stages  # noqa: E402
from spaces import (  # noqa: E402
    FAMILY_HOLDOUT_SUBSETS,
    all_holdout_subsets,
    family_of_subset,
    holdout_case_config,
)

FAMILY_DIR = BO_DIR / "family"
BAD_CONFIGS_PATH = FAMILY_DIR / "bad_configs.json"


def _load_bad_overlay(family: str) -> dict[str, dict[str, Any]]:
    if not BAD_CONFIGS_PATH.exists():
        raise FileNotFoundError(
            f"Missing {BAD_CONFIGS_PATH}; run bo-unified/ingest.py --select-bad first"
        )
    data = json.loads(BAD_CONFIGS_PATH.read_text(encoding="utf-8"))
    if family not in data:
        raise KeyError(f"No known-bad config for family {family!r} in {BAD_CONFIGS_PATH}")
    return data[family]["overlay"]


def study_root_for(subset: str) -> Path:
    return (DATA_ROOT / f"{subset}-family-proxy").resolve()


def run_holdout_config(
    subset: str,
    config_kind: str,
    *,
    force: bool = False,
) -> dict[str, Any]:
    if config_kind not in ("anchor", "bad"):
        raise ValueError(f"config_kind must be 'anchor' or 'bad', got {config_kind!r}")

    cfg = holdout_case_config(subset)
    family = cfg["family"]
    input_txt = REPO_ROOT / cfg["input_txt"]
    if not input_txt.exists():
        raise FileNotFoundError(f"Missing subset file {input_txt}")

    study = study_root_for(subset)
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

    params_src = REPO_ROOT / cfg["params_dir"]
    base = load_anchor_params(params_src)
    family_params = load_family_params(params_src)
    overlay: dict[str, dict[str, Any]] = {}
    # Pin seed when sibling params omit it (1-1 / 2-1) so holdouts are repeatable.
    if "random_seed" not in base.get("unfolding", {}):
        overlay.setdefault("unfolding", {})["random_seed"] = 0
    if config_kind == "bad":
        bad = _load_bad_overlay(family)
        for stage, kv in bad.items():
            if stage == "unfolding":
                # Keep deterministic unfolding keys from sibling base; only allow
                # stage-2–6 knobs from the known-bad overlay.
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

    if status == "ok" and miou is None:
        status = "failed"

    rec: dict[str, Any] = {
        "run_id": run_id,
        "subset": subset,
        "family": family,
        "config_kind": config_kind,
        "sibling": cfg["sibling"],
        "params_dir": cfg["params_dir"],
        "status": status,
        "mIoU": miou,
        "elapsed_s": elapsed,
        "tier1_complete": has_complete_tier1(metrics),
        "orient_h_ring_corr": metrics.get("orient_h_ring_corr"),
        "orient_invariant_ok": metrics.get("orient_invariant_ok"),
        "metrics": metrics,
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
    manifest_path.write_text(json.dumps(man, indent=2) + "\n", encoding="utf-8")

    print(
        f"{run_id} status={status} mIoU={miou} elapsed={elapsed:.1f}s "
        f"tier1_ok={rec['tier1_complete']}"
    )
    return rec


def run_holdout_gate(subset: str, *, force: bool = False, floor: float = 0.30) -> dict[str, Any]:
    """Gate B: single-instance holdout with sibling unified params."""
    cfg = holdout_case_config(subset)
    FAMILY_DIR.mkdir(parents=True, exist_ok=True)
    rec = run_holdout_config(subset, "anchor", force=force)
    miou = rec.get("mIoU")
    miou_f = float(miou) if miou is not None else float("nan")
    passed = (
        rec["status"] == "ok"
        and math.isfinite(miou_f)
        and miou_f >= floor
        and bool(rec["tier1_complete"])
    )
    evidence = FAMILY_DIR / f"gate_{subset}.json"
    gate = {
        "case": subset,
        "gate_kind": "holdout",
        "config_kind": "anchor",
        "command": (
            f"./venv/bin/python bo-unified/run_holdout.py --gate-subset {subset} "
            f"# full pipeline, params from {cfg['params_dir']}"
        ),
        "lineage": (
            f"sibling unified params {cfg['params_dir']} → "
            f"data/bo-unified/{subset}-family-proxy/runs/{subset}-anchor; "
            f"stages 1–6 via anchors/unified"
        ),
        "pass_fail_criteria": {
            "pipeline_ok": rec["status"] == "ok",
            f"miou_finite_and_ge_{floor}": bool(math.isfinite(miou_f) and miou_f >= floor),
            "intrinsics_tier1_no_nan": bool(rec["tier1_complete"]),
        },
        "measured_mIoU": miou,
        "orient_h_ring_corr": rec.get("orient_h_ring_corr"),
        "orient_invariant_ok": rec.get("orient_invariant_ok"),
        "tier1_complete": rec["tier1_complete"],
        "passed": passed,
        "evidence_path": str(evidence),
        "output_dir": rec["output_dir"],
        "log_path": rec["log_path"],
        "study_root": str(study_root_for(subset)),
    }
    evidence.write_text(json.dumps(gate, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(gate, indent=2))
    if not passed:
        raise RuntimeError(f"Holdout validation gate FAILED for {subset}; see {evidence}")
    return gate


def run_all_holdout(
    *,
    configs: tuple[str, ...] = ("anchor", "bad"),
    force: bool = False,
    only_family: str | None = None,
    only_subsets: list[str] | None = None,
) -> list[dict[str, Any]]:
    results = []
    subsets = only_subsets if only_subsets is not None else all_holdout_subsets()
    for subset in subsets:
        fam = family_of_subset(subset)
        if only_family and fam != only_family:
            continue
        for kind in configs:
            results.append(run_holdout_config(subset, kind, force=force))
    return results


def main() -> None:
    p = argparse.ArgumentParser(description="bo-unified held-out subset runner")
    p.add_argument("--gate-subset", type=str, default=None)
    p.add_argument("--subset", type=str, default=None)
    p.add_argument("--config", choices=("anchor", "bad", "both"), default="both")
    p.add_argument("--all", action="store_true")
    p.add_argument("--family", choices=("t1&2", "t3", "t4&5"), default=None)
    p.add_argument("--force", action="store_true")
    args = p.parse_args()

    if args.gate_subset:
        run_holdout_gate(args.gate_subset, force=args.force)
        return

    kinds: tuple[str, ...]
    if args.config == "both":
        kinds = ("anchor", "bad")
    else:
        kinds = (args.config,)

    if args.all:
        run_all_holdout(configs=kinds, force=args.force, only_family=args.family)
        return

    if args.subset:
        for kind in kinds:
            run_holdout_config(args.subset, kind, force=args.force)
        return

    p.error("Specify --gate-subset, --subset, or --all")


if __name__ == "__main__":
    main()
