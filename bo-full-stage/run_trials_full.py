#!/usr/bin/env python3
"""Full-pipeline (stages 1–6) trial campaign for bo-full-stage.

Outputs under data/bo-full-stage/<case>-trials/ (never data/anchors, data/bo,
data/baseline). Stage-1 is tunable; residual + orientation are recorded.
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
BO_ELEGANT = REPO_ROOT / "bo-elegant"
sys.path.insert(0, str(REPO_ROOT / "bo-unified"))
sys.path.insert(0, str(BO_ELEGANT))

from param_io import load_anchor_params, load_family_params, materialize_run_params  # noqa: E402
from pipeline import parse_performance, run_stages  # noqa: E402
from spaces import CASE_CONFIG, decode_vector, space_for_case  # noqa: E402
from intrinsics import write_intrinsics  # noqa: E402

from features import CANDIDATE, extract_lean, features_complete  # noqa: E402

DATA_ROOT = REPO_ROOT / "data" / "bo-full-stage"


def _study(case: str) -> Path:
    return DATA_ROOT / f"{case}-trials"


def _sobol_overlays(case: str, n: int, seed: int = 0) -> list[dict[str, dict[str, Any]]]:
    dims = space_for_case(case)
    params_src = REPO_ROOT / CASE_CONFIG[case]["params_dir"]
    base = load_anchor_params(params_src)
    rng = np.random.default_rng(seed)
    try:
        from scipy.stats import qmc

        sampler = qmc.Sobol(d=len(dims), scramble=True, seed=seed)
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
    end_stage: int = 6,
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

    params_src = REPO_ROOT / cfg["params_dir"]
    base = load_anchor_params(params_src)
    family_params = load_family_params(params_src)
    # Ensure residual recentre is on so unfold_residual is always measurable.
    ov = dict(overlay or {})
    unf = dict(ov.get("unfolding") or {})
    unf["residual_recentre"] = True
    ov["unfolding"] = unf
    params_dir = materialize_run_params(
        params_root / trial_id, base, ov, family_params=family_params
    )

    run_dir = runs_root / trial_id
    if run_dir.exists():
        shutil.rmtree(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)

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
            start_stage=1,
            end_stage=end_stage,
        )
    except RuntimeError as exc:
        print(f"FAILED {trial_id}: {exc}")
        status = "failed"
        if log_path.exists():
            log_text = log_path.read_text(encoding="utf-8")

    perf = parse_performance(run_dir / "evaluation" / "performance.md") if end_stage >= 6 else {}
    miou = perf.get("mIoU")
    metrics = extract_lean(
        run_dir,
        params_dir=params_dir,
        expected_rings=int(cfg["expected_rings"]),
        log_text=log_text,
    )
    metrics.update({f"perf_{k}": v for k, v in perf.items()})
    write_intrinsics(run_dir, metrics)

    if status == "ok" and end_stage >= 6 and miou is None:
        status = "failed"

    rec: dict[str, Any] = {
        "trial_id": trial_id,
        "case": case,
        "family": cfg["family"],
        "acquisition": acquisition,
        "status": status,
        "mIoU": miou,
        "elapsed_s": elapsed,
        "stage1_varied": bool(overlay and "unfolding" in (overlay or {})),
        "overlay": overlay or {},
        "metrics": {
            k: metrics.get(k)
            for k in (
                *CANDIDATE,
                "det_real_detection_ratio",
                "orient_invariant_ok",
                "orient_axis_corr",
                "recentre_residual_max_cm",
            )
        },
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
        f"lean_ok={rec['lean_complete']} "
        f"residual_cm={metrics.get('recentre_residual_max_cm')} "
        f"orient={metrics.get('orient_agreement')} "
        f"elapsed={elapsed:.1f}s"
    )
    return rec


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", required=True, choices=sorted(CASE_CONFIG))
    parser.add_argument(
        "--gate",
        action="store_true",
        help="Single-instance gate: anchor params with random_seed=1 overlay",
    )
    parser.add_argument("--n", type=int, default=0, help="Number of Sobol overlay trials")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--start-index", type=int, default=0)
    parser.add_argument(
        "--trial-id",
        type=str,
        default=None,
        help="Explicit trial id (used with --gate or single overlay)",
    )
    args = parser.parse_args()

    if args.gate:
        tid = args.trial_id or f"{args.case}-gate-seed1"
        overlay = {"unfolding": {"random_seed": 1}}
        run_trial(
            args.case,
            tid,
            overlay,
            acquisition="gate_stage1_seed1",
            force=args.force,
        )
        return

    if args.n <= 0:
        parser.error("Provide --n > 0 or --gate")

    # Oversample Sobol so stage-1 crashes don't leave us short of N ok trials.
    target = args.n
    pool = max(target * 2, target + 8)
    overlays = _sobol_overlays(args.case, pool, seed=args.seed)
    ok = 0
    i = args.start_index
    for ov in overlays:
        if ok >= target:
            break
        tid = f"{args.case}-f{i:03d}"
        rec = run_trial(
            args.case,
            tid,
            ov,
            acquisition="sobol_full",
            force=args.force,
        )
        i += 1
        if rec.get("status") == "ok" and rec.get("mIoU") is not None:
            ok += 1
    print(f"{args.case}: collected {ok}/{target} ok full-pipeline trials")
    if ok < target:
        raise SystemExit(f"Only {ok}/{target} ok trials for {args.case}")



if __name__ == "__main__":
    main()
