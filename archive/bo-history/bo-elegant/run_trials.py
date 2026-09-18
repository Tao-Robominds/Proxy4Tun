#!/usr/bin/env python3
"""Artifact-keeping stage-2–6 trial campaign for bo-elegant proxy v2.

Outputs under data/bo-elegant/<case>-trials/ (never data/anchors, data/bo,
data/baseline). Freezes stage-1 from data/anchors/<case> or data/unified/<case>.
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
sys.path.insert(0, str(REPO_ROOT / "bo-unified"))

from param_io import load_anchor_params, load_family_params, materialize_run_params  # noqa: E402
from pipeline import copy_checkpoint, parse_performance, run_stages  # noqa: E402
from spaces import CASE_CONFIG, decode_vector, space_for_case  # noqa: E402
from intrinsics import write_intrinsics  # noqa: E402

from features import ANCHOR_PARAMS, extract_lean, features_complete, CANDIDATE  # noqa: E402

DATA_ROOT = REPO_ROOT / "data" / "bo-elegant"


def _stage1_source(case: str) -> Path:
    """Prefer frozen data/anchors/<case>; fall back to data/unified/<case>."""
    anchors = REPO_ROOT / "data" / "anchors" / case
    if (anchors / "state.pkl").exists() and (anchors / "unwrapped.csv").exists():
        return anchors
    u_out = CASE_CONFIG[case].get("unified_out") or case
    unified = REPO_ROOT / "data" / "unified" / u_out
    if (unified / "state.pkl").exists():
        return unified
    raise FileNotFoundError(f"No stage-1 source for {case} under data/anchors or data/unified")


def _study(case: str) -> Path:
    return DATA_ROOT / f"{case}-trials"


def ensure_checkpoint(case: str) -> Path:
    study = _study(case)
    ckpt = study / "checkpoints" / "after_1"
    if (ckpt / "state.pkl").exists() and (ckpt / "unwrapped.csv").exists():
        return ckpt
    src = _stage1_source(case)
    n = copy_checkpoint(src, ckpt)
    meta = {"source": str(src.relative_to(REPO_ROOT)), "n_files": n, "case": case}
    ckpt.mkdir(parents=True, exist_ok=True)
    (ckpt / "checkpoint_meta.json").write_text(json.dumps(meta, indent=2) + "\n")
    print(f"Stage-1 checkpoint for {case} from {src} ({n} files)")
    return ckpt


def _sobol_overlays(case: str, n: int, seed: int = 0) -> list[dict[str, dict[str, Any]]]:
    """Quasi-random overlays in the family BO space (stage 2–6 knobs only)."""
    dims = space_for_case(case)
    params_src = REPO_ROOT / CASE_CONFIG[case]["params_dir"]
    base = load_anchor_params(params_src)
    rng = np.random.default_rng(seed)
    # Sobol if available, else uniform
    try:
        from scipy.stats import qmc

        sampler = qmc.Sobol(d=len(dims), scramble=True, seed=seed)
        # power of 2 for sobol balance
        m = int(np.ceil(np.log2(max(n, 2))))
        unit = sampler.random_base2(m)[:n]
    except Exception:  # noqa: BLE001
        unit = rng.random((n, len(dims)))

    overlays = []
    for row in unit:
        x = []
        for d, u in zip(dims, row):
            if d.kind == "bool":
                x.append(1.0 if u >= 0.5 else 0.0)
            else:
                x.append(float(d.low + u * (d.high - d.low)))
        overlays.append(decode_vector(dims, x, base))
    return overlays


def run_trial(
    case: str,
    trial_id: str,
    overlay: dict[str, dict[str, Any]] | None,
    *,
    acquisition: str,
    force: bool = False,
) -> dict[str, Any]:
    cfg = CASE_CONFIG[case]
    study = _study(case)
    runs_root = study / "runs"
    params_root = study / "params"
    logs_root = study / "logs"
    for d in (runs_root, params_root, logs_root):
        d.mkdir(parents=True, exist_ok=True)
    manifest_path = study / "manifest.json"

    if manifest_path.exists() and not force:
        man = json.loads(manifest_path.read_text(encoding="utf-8"))
        for rec in man.get("trials", []):
            if rec.get("trial_id") == trial_id and rec.get("status") == "ok" and rec.get("mIoU") is not None:
                print(f"Skip existing ok {trial_id} mIoU={rec['mIoU']}")
                return rec

    ckpt = ensure_checkpoint(case)
    params_src = REPO_ROOT / cfg["params_dir"]
    base = load_anchor_params(params_src)
    family_params = load_family_params(params_src)
    params_dir = materialize_run_params(
        params_root / trial_id, base, overlay, family_params=family_params
    )

    run_dir = runs_root / trial_id
    if run_dir.exists():
        shutil.rmtree(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    copy_checkpoint(ckpt, run_dir)

    log_path = logs_root / f"{trial_id}.log"
    status = "ok"
    log_text = ""
    elapsed = 0.0
    try:
        log_text, elapsed = run_stages(
            run_id=trial_id,
            params_dir=params_dir,
            input_txt=REPO_ROOT / cfg["input_txt"],
            out_root=runs_root,
            log_path=log_path,
            start_stage=2,
            end_stage=6,
        )
    except RuntimeError as exc:
        print(f"FAILED {trial_id}: {exc}")
        status = "failed"
        if log_path.exists():
            log_text = log_path.read_text(encoding="utf-8")

    perf = parse_performance(run_dir / "evaluation" / "performance.md")
    miou = perf.get("mIoU")
    metrics = extract_lean(run_dir, params_dir=params_dir, expected_rings=int(cfg["expected_rings"]))
    metrics.update({f"perf_{k}": v for k, v in perf.items()})
    write_intrinsics(run_dir, metrics)

    if status == "ok" and miou is None:
        status = "failed"

    rec: dict[str, Any] = {
        "trial_id": trial_id,
        "case": case,
        "family": cfg["family"],
        "acquisition": acquisition,
        "status": status,
        "mIoU": miou,
        "elapsed_s": elapsed,
        "overlay": overlay or {},
        "metrics": {k: metrics.get(k) for k in (*CANDIDATE, "det_real_detection_ratio", "orient_invariant_ok")},
        "lean_complete": features_complete(metrics, CANDIDATE),
        "path": str(run_dir.relative_to(REPO_ROOT)),
        "created_at": datetime.now().isoformat(),
    }

    man = {"case": case, "trials": []}
    if manifest_path.exists():
        man = json.loads(manifest_path.read_text(encoding="utf-8"))
    man["trials"] = [t for t in man.get("trials", []) if t.get("trial_id") != trial_id]
    man["trials"].append(rec)
    man["updated_at"] = datetime.now().isoformat()
    manifest_path.write_text(json.dumps(man, indent=2) + "\n", encoding="utf-8")
    print(
        f"{trial_id} [{acquisition}] status={status} mIoU={miou} "
        f"lean_ok={rec['lean_complete']} residual={metrics.get('det_row_residual_px')} "
        f"phase={metrics.get('phase_incoherence_deg')}"
    )
    return rec


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", required=True, choices=sorted(CASE_CONFIG))
    parser.add_argument("--gate", action="store_true", help="Single-instance gate: anchor overlay only")
    parser.add_argument("--n", type=int, default=35, help="Number of Sobol overlay trials")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--start-index", type=int, default=0)
    args = parser.parse_args()

    ensure_checkpoint(args.case)

    if args.gate:
        run_trial(args.case, f"{args.case}-gate", None, acquisition="gate_anchor", force=args.force)
        return

    # Always include the zero-overlay (deployed anchor params) as t000.
    run_trial(
        args.case,
        f"{args.case}-t{args.start_index:03d}",
        None,
        acquisition="anchor_overlay",
        force=args.force,
    )
    overlays = _sobol_overlays(args.case, args.n, seed=args.seed)
    for i, ov in enumerate(overlays, start=args.start_index + 1):
        run_trial(
            args.case,
            f"{args.case}-t{i:03d}",
            ov,
            acquisition="sobol",
            force=args.force,
        )


if __name__ == "__main__":
    main()
