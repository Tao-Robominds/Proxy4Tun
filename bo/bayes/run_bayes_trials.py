#!/usr/bin/env python3
"""Bayesian-exploration trial campaign (Sobol init + GP uncertainty acquisition).

Outputs under data/bo/bayes/<case>-trials/ (never data/anchors, data/baseline,
or other frozen data/bo/* trees).

Matches the manuscript method text:
  Phase 1 — scrambled-Sobol initialisation (N0)
  Phase 2 — full pipeline execution + feature logging
  Phase 3 — GP (Matérn ν=2.5 + white noise) with uncertainty-max acquisition
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

import numpy as np
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import ConstantKernel, Matern, WhiteKernel

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))
from bo.paths import BAYES_DATA, REPO_ROOT
from bo.unified.param_io import load_anchor_params, load_family_params, materialize_run_params  # noqa: E402
from bo.unified.pipeline import parse_performance, run_stages  # noqa: E402
from bo.unified.spaces import (  # noqa: E402
    CASE_CONFIG,
    decode_vector,
    denormalize,
    encode_params,
    normalize,
    space_for_case,
)
from bo.unified.intrinsics import write_intrinsics  # noqa: E402
from bo.elegant.features import CANDIDATE, extract_lean, features_complete  # noqa: E402

DATA_ROOT = BAYES_DATA
TRAIN_CASES = ("2-1", "3-1", "5-1")

def _study(case: str) -> Path:
    return DATA_ROOT / f"{case}-trials"


def _load_manifest(case: str) -> dict[str, Any]:
    path = _study(case) / "manifest.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {
        "case": case,
        "profile": "bayesian_exploration",
        "trials": [],
        "created_at": datetime.now().isoformat(),
    }


def _save_manifest(case: str, man: dict[str, Any]) -> None:
    study = _study(case)
    study.mkdir(parents=True, exist_ok=True)
    man["updated_at"] = datetime.now().isoformat()
    (study / "manifest.json").write_text(
        json.dumps(man, indent=2) + "\n", encoding="utf-8"
    )


def _ok_trials(man: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        t
        for t in man.get("trials", [])
        if t.get("status") == "ok"
        and t.get("mIoU") is not None
        and t.get("lean_complete")
        and t.get("x")
    ]


def _sobol_unit(n: int, d: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    try:
        from scipy.stats import qmc

        sampler = qmc.Sobol(d=d, scramble=True, seed=seed)
        m = int(np.ceil(np.log2(max(n, 2))))
        return sampler.random_base2(m)[:n]
    except Exception:  # noqa: BLE001
        return rng.random((n, d))


def _unit_to_x(dims: list, unit_row: np.ndarray) -> list[float]:
    x: list[float] = []
    for d, u in zip(dims, unit_row):
        if d.kind == "bool":
            x.append(1.0 if float(u) >= 0.5 else 0.0)
        else:
            x.append(float(d.low + float(u) * (d.high - d.low)))
    return x


def _overlay_from_x(case: str, x: list[float]) -> dict[str, dict[str, Any]]:
    dims = space_for_case(case)
    params_src = REPO_ROOT / CASE_CONFIG[case]["params_dir"]
    base = load_anchor_params(params_src)
    return decode_vector(dims, x, base)


def run_trial(
    case: str,
    trial_id: str,
    x: list[float],
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

    man = _load_manifest(case)
    if not force:
        for rec in man.get("trials", []):
            if (
                rec.get("trial_id") == trial_id
                and rec.get("status") == "ok"
                and rec.get("mIoU") is not None
            ):
                print(f"Skip existing ok {trial_id} mIoU={rec['mIoU']}")
                return rec

    overlay = _overlay_from_x(case, x)
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

    lean_ok = bool(features_complete(metrics, CANDIDATE))
    rec: dict[str, Any] = {
        "trial_id": trial_id,
        "case": case,
        "family": cfg["family"],
        "acquisition": acquisition,
        "status": status if lean_ok or status != "ok" else "incomplete_features",
        "mIoU": miou,
        "elapsed_s": elapsed,
        "stage1_varied": True,
        "x": [float(v) for v in x],
        "overlay": ov,
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
        "lean_complete": lean_ok,
        "path": str(run_dir.relative_to(REPO_ROOT)),
        "created_at": datetime.now().isoformat(),
    }
    if rec["status"] == "incomplete_features":
        status = "incomplete_features"

    man["trials"] = [t for t in man.get("trials", []) if t.get("trial_id") != trial_id]
    man["trials"].append(rec)
    _save_manifest(case, man)
    print(
        f"{trial_id} [{acquisition}] status={rec['status']} mIoU={miou} "
        f"lean_ok={lean_ok} "
        f"residual_cm={metrics.get('recentre_residual_max_cm')} "
        f"orient={metrics.get('orient_agreement')} "
        f"elapsed={elapsed:.1f}s"
    )
    return rec


def _fit_gp(dims: list, ok: list[dict[str, Any]], seed: int) -> GaussianProcessRegressor | None:
    if len(ok) < 3:
        return None
    X = np.asarray([normalize(dims, t["x"]) for t in ok], dtype=float)
    y = np.asarray([float(t["mIoU"]) for t in ok], dtype=float)
    kernel = ConstantKernel(1.0, (1e-3, 1e3)) * Matern(
        length_scale=np.ones(X.shape[1]),
        length_scale_bounds=(1e-2, 1e2),
        nu=2.5,
    ) + WhiteKernel(noise_level=1e-3, noise_level_bounds=(1e-6, 1e-1))
    gp = GaussianProcessRegressor(
        kernel=kernel,
        normalize_y=True,
        n_restarts_optimizer=3,
        random_state=seed,
    )
    gp.fit(X, y)
    return gp


def _propose_uncertainty(
    gp: GaussianProcessRegressor,
    dims: list,
    rng: np.random.Generator,
    *,
    n_cand: int = 2048,
    existing_x: list[list[float]] | None = None,
    min_l2: float = 0.05,
) -> list[float]:
    cand = rng.random((n_cand, len(dims)))
    _, sigma = gp.predict(cand, return_std=True)
    sigma = np.maximum(sigma, 1e-9)
    order = np.argsort(-sigma)
    existing_z = (
        [normalize(dims, x) for x in (existing_x or [])] if existing_x else []
    )
    for idx in order:
        z = list(cand[int(idx)])
        if existing_z:
            dists = [float(np.linalg.norm(np.asarray(z) - np.asarray(ez))) for ez in existing_z]
            if min(dists) < min_l2:
                continue
        return denormalize(dims, z)
    return denormalize(dims, list(cand[int(order[0])]))


def run_campaign(
    case: str,
    *,
    n0: int = 24,
    n_gp: int = 16,
    seed: int = 0,
    force: bool = False,
    sobol_pool_factor: float = 2.0,
) -> dict[str, Any]:
    """Collect n0 Sobol + n_gp GP-uncertainty valid trials (target = n0 + n_gp)."""
    target = n0 + n_gp
    dims = space_for_case(case)
    rng = np.random.default_rng(seed + 17)
    man = _load_manifest(case)

    # --- Phase 1/2: Sobol initialisation with top-up ---
    sobol_ok = [
        t for t in _ok_trials(man) if str(t.get("acquisition", "")).startswith("sobol")
    ]
    # Oversample the unit-cube draw so crashes / skips can still reach N0.
    pool_n = max(int(math.ceil(n0 * sobol_pool_factor)), n0 + 16, len(sobol_ok) + 16)
    unit = _sobol_unit(pool_n, len(dims), seed=seed)
    # Resume at the next free -s### index so top-ups do not spin on existing ids.
    existing_s_idx = []
    for t in man.get("trials", []):
        tid = str(t.get("trial_id", ""))
        if tid.startswith(f"{case}-s") and tid[len(case) + 2 :].isdigit():
            existing_s_idx.append(int(tid[len(case) + 2 :]))
    i = (max(existing_s_idx) + 1) if existing_s_idx else 0
    attempts = 0
    while len(sobol_ok) < n0 and attempts < pool_n:
        if i >= len(unit):
            # Extend unit cube draw if we need more candidates.
            more = _sobol_unit(pool_n, len(dims), seed=seed + 1000 + attempts)
            unit = np.vstack([unit, more])
        tid = f"{case}-s{i:03d}"
        x = _unit_to_x(dims, unit[i % len(unit)])
        rec = run_trial(case, tid, x, acquisition="sobol_init", force=force)
        man = _load_manifest(case)
        sobol_ok = [
            t for t in _ok_trials(man) if str(t.get("acquisition", "")).startswith("sobol")
        ]
        i += 1
        attempts += 1

    if len(sobol_ok) < n0:
        raise SystemExit(
            f"{case}: only {len(sobol_ok)}/{n0} Sobol ok trials after {attempts} attempts"
        )

    # --- Phase 3: GP uncertainty acquisitions ---
    gp_ok = [
        t for t in _ok_trials(man) if str(t.get("acquisition", "")).startswith("gp_")
    ]
    existing_g_idx = []
    for t in man.get("trials", []):
        tid = str(t.get("trial_id", ""))
        if tid.startswith(f"{case}-g") and tid[len(case) + 2 :].isdigit():
            existing_g_idx.append(int(tid[len(case) + 2 :]))
    g = (max(existing_g_idx) + 1) if existing_g_idx else 0
    max_gp_attempts = n_gp * 3
    attempts = 0
    while len(gp_ok) < n_gp and attempts < max_gp_attempts:
        man = _load_manifest(case)
        # Fit GP on Sobol + already-accepted GP trials only (not archived).
        ok_all = _ok_trials(man)
        gp = _fit_gp(dims, ok_all, seed=seed)
        if gp is None:
            raise SystemExit(f"{case}: GP fit failed with {len(ok_all)} ok trials")
        x_next = _propose_uncertainty(
            gp, dims, rng, existing_x=[t["x"] for t in ok_all]
        )
        tid = f"{case}-g{g:03d}"
        z = normalize(dims, x_next)
        _, sig = gp.predict(np.asarray([z], dtype=float), return_std=True)
        rec = run_trial(
            case,
            tid,
            x_next,
            acquisition=f"gp_uncertainty_sigma={float(sig[0]):.4f}",
            force=force,
        )
        man = _load_manifest(case)
        gp_ok = [
            t for t in _ok_trials(man) if str(t.get("acquisition", "")).startswith("gp_")
        ]
        g += 1
        attempts += 1

    man = _load_manifest(case)
    ok_all = _ok_trials(man)
    summary = {
        "case": case,
        "n0_target": n0,
        "n_gp_target": n_gp,
        "sobol_ok": len(
            [t for t in ok_all if str(t.get("acquisition", "")).startswith("sobol")]
        ),
        "gp_ok": len(
            [t for t in ok_all if str(t.get("acquisition", "")).startswith("gp_")]
        ),
        "total_ok": len(ok_all),
        "target": target,
        "passed": len(ok_all) >= target
        and len([t for t in ok_all if str(t.get("acquisition", "")).startswith("sobol")])
        >= n0
        and len([t for t in ok_all if str(t.get("acquisition", "")).startswith("gp_")])
        >= n_gp,
    }
    man["campaign_summary"] = summary
    _save_manifest(case, man)
    print(json.dumps(summary, indent=2))
    if not summary["passed"]:
        raise SystemExit(f"{case}: campaign incomplete: {summary}")
    # Trim to exactly target by preferring sobol then gp order (keep first n0+n_gp)
    return summary


def run_gate(case: str = "3-1", *, seed: int = 0, force: bool = False) -> dict[str, Any]:
    """Single-instance validation: 1 Sobol + 1 GP trial on the chosen case."""
    dims = space_for_case(case)
    unit = _sobol_unit(4, len(dims), seed=seed)
    x0 = _unit_to_x(dims, unit[0])
    r0 = run_trial(case, f"{case}-gate-s000", x0, acquisition="sobol_init", force=force)

    # Need ≥3 ok for GP; run two more quick Sobol seeds if needed
    man = _load_manifest(case)
    ok = _ok_trials(man)
    i = 1
    while len(ok) < 3 and i < 4:
        xi = _unit_to_x(dims, unit[i])
        run_trial(case, f"{case}-gate-s{i:03d}", xi, acquisition="sobol_init", force=force)
        man = _load_manifest(case)
        ok = _ok_trials(man)
        i += 1

    gp = _fit_gp(dims, ok, seed=seed)
    if gp is None:
        raise SystemExit("Gate FAILED: GP could not be fit")
    rng = np.random.default_rng(seed + 17)
    x_g = _propose_uncertainty(gp, dims, rng, existing_x=[t["x"] for t in ok])
    z = normalize(dims, x_g)
    _, sig = gp.predict(np.asarray([z], dtype=float), return_std=True)
    r1 = run_trial(
        case,
        f"{case}-gate-g000",
        x_g,
        acquisition=f"gp_uncertainty_sigma={float(sig[0]):.4f}",
        force=force,
    )

    checks = {
        "sobol_status_ok": r0.get("status") == "ok",
        "sobol_miou_finite": r0.get("mIoU") is not None and math.isfinite(float(r0["mIoU"])),
        "sobol_lean_complete": bool(r0.get("lean_complete")),
        "gp_status_ok": r1.get("status") == "ok",
        "gp_miou_finite": r1.get("mIoU") is not None and math.isfinite(float(r1["mIoU"])),
        "gp_lean_complete": bool(r1.get("lean_complete")),
        "gp_fit_ok": True,
        "gp_sigma": float(sig[0]),
    }
    passed = all(
        checks[k]
        for k in (
            "sobol_status_ok",
            "sobol_miou_finite",
            "sobol_lean_complete",
            "gp_status_ok",
            "gp_miou_finite",
            "gp_lean_complete",
            "gp_fit_ok",
        )
    )
    evidence = {
        "case": case,
        "command": (
            f"./venv/bin/python bo/bayes/run_bayes_trials.py --case {case} --gate "
            f"--seed {seed}"
        ),
        "lineage": f"data/bo/bayes/{case}-trials/runs/{{gate-s000,gate-g000}}",
        "pass_fail_criteria": checks,
        "passed": passed,
        "sobol_trial": {
            "trial_id": r0.get("trial_id"),
            "mIoU": r0.get("mIoU"),
            "status": r0.get("status"),
            "path": r0.get("path"),
        },
        "gp_trial": {
            "trial_id": r1.get("trial_id"),
            "mIoU": r1.get("mIoU"),
            "status": r1.get("status"),
            "path": r1.get("path"),
            "acquisition": r1.get("acquisition"),
        },
        "evidence_path": str((_study(case) / "validation_gate.json").relative_to(REPO_ROOT)),
    }
    out_json = _study(case) / "validation_gate.json"
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(evidence, indent=2))
    if not passed:
        raise SystemExit(f"Validation gate FAILED for {case}; see {out_json}")
    return evidence


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--case", choices=sorted(CASE_CONFIG), required=True)
    p.add_argument("--gate", action="store_true", help="Single-instance Sobol+GP gate")
    p.add_argument("--n0", type=int, default=24, help="Sobol init valid-trial count")
    p.add_argument("--n-gp", type=int, default=16, help="GP uncertainty valid-trial count")
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--force", action="store_true")
    args = p.parse_args()

    if args.case not in TRAIN_CASES and not args.gate:
        print(f"Warning: {args.case} is not a train anchor; proceeding anyway")

    if args.gate:
        run_gate(args.case, seed=args.seed, force=args.force)
        return

    run_campaign(
        args.case,
        n0=args.n0,
        n_gp=args.n_gp,
        seed=args.seed,
        force=args.force,
    )


if __name__ == "__main__":
    main()
