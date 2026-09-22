#!/usr/bin/env python3
"""Release-2 calibration: 32 scrambled-Sobol + 8 GP-uncertainty trials per family.

Manuscript settings (Appendix tab:bo-config): scrambled Sobol; integers rounded
and Booleans thresholded inside decode_vector; inverted radial gates reset to
the midpoint ∓ 0.02 m; GP is ConstantKernel * Matern(nu=2.5) + WhiteKernel,
normalize_y, 3 restarts, refit after each valid trial; acquisition maximises
predictive std over 2048 candidates.

Usage:
  ./venv/bin/python -u bo/release2/calibrate.py --dev 2-1 --gate
  ./venv/bin/python -u bo/release2/calibrate.py --dev 2-1
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import ConstantKernel, Matern, WhiteKernel

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from bo.paths import REFERENCES_DIR, RELEASE2_DATA, REPO_ROOT  # noqa: E402
from bo.release2.measure import MEASUREMENT_KEYS, measure_run  # noqa: E402
from bo.runtime.metadata import family_of  # noqa: E402
from bo.runtime.param_io import (  # noqa: E402
    get_nested,
    load_anchor_params,
    load_family_params,
    materialize_run_params,
)
from bo.runtime.pipeline import parse_performance, run_stages  # noqa: E402
from bo.runtime.spaces import (  # noqa: E402
    Dim,
    decode_vector,
    denormalize,
    normalize,
)

DEV_CASES = ("2-1", "3-1", "5-1")
DEFAULT_SEED = {"2-1": 2, "3-1": 3, "5-1": 5}
# Plan 1 gate wall times (seconds). A gate trial must finish within 1.5x.
GATE_BUDGET_S = {"2-1": 283.1, "3-1": 223.2, "5-1": 268.7}
N_CAND = 2048
# Dropped after the record is written. A full run is ~1.6 GB; 120 of them
# do not fit on the disk. The scientific record is record.json.
SLIM_NAMES = (
    "state.pkl",
    "unwrapped.csv",
    "denoised.csv",
    "enhanced.csv",
    "final.csv",
    "pixel_to_point.pkl",
    "results.pkl",
)

CALIB = RELEASE2_DATA / "calibration"
RECORDS = CALIB / "records"
BOUNDS = REPO_ROOT / "configs" / "bounds"


def _log(msg: str) -> None:
    print(f"[{datetime.now().isoformat(timespec='seconds')}] {msg}", flush=True)


def load_dims(family: str) -> list[Dim]:
    path = BOUNDS / f"{family}.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    dims = []
    for raw in data["dims"]:
        dims.append(
            Dim(
                name=raw["name"],
                stage=raw["stage"],
                key=raw["key"],
                kind=raw["kind"],
                low=float(raw["low"]),
                high=float(raw["high"]),
                special=raw.get("special"),
            )
        )
    return dims


def study_dir(dev: str) -> Path:
    return CALIB / dev


def manifest_path(dev: str) -> Path:
    return study_dir(dev) / "manifest.json"


def load_manifest(dev: str) -> dict[str, Any]:
    path = manifest_path(dev)
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {"dev": dev, "family": family_of(dev), "trials": []}


def save_manifest(dev: str, man: dict[str, Any]) -> None:
    path = manifest_path(dev)
    path.parent.mkdir(parents=True, exist_ok=True)
    man["updated_at"] = datetime.now().isoformat(timespec="seconds")
    path.write_text(json.dumps(man, indent=2) + "\n", encoding="utf-8")


def valid_trials(man: dict[str, Any], prefix: str | None = None) -> list[dict[str, Any]]:
    out = []
    for trial in man.get("trials", []):
        if not trial.get("valid"):
            continue
        if prefix and not str(trial.get("acquisition", "")).startswith(prefix):
            continue
        out.append(trial)
    return out


def _sobol_unit(n: int, d: int, seed: int) -> np.ndarray:
    from scipy.stats import qmc

    sampler = qmc.Sobol(d=d, scramble=True, seed=seed)
    m = int(np.ceil(np.log2(max(n, 2))))
    return sampler.random_base2(m)[:n]


def _unit_to_x(dims: list[Dim], unit_row: np.ndarray) -> list[float]:
    x: list[float] = []
    for dim, unit in zip(dims, unit_row):
        if dim.kind == "bool":
            x.append(1.0 if float(unit) >= 0.5 else 0.0)
        else:
            x.append(float(dim.low + float(unit) * (dim.high - dim.low)))
    return x


def _overlay_value(overlay: dict[str, Any], dim: Dim) -> Any:
    stage = overlay.get(dim.stage) or {}
    if dim.special == "y_bounds_lower":
        bounds = stage.get("processing.y_bounds")
        return None if not bounds else bounds[0]
    return stage.get(dim.key)


def overlay_in_bounds(dims: list[Dim], overlay: dict[str, Any]) -> bool:
    """True when every overlay value sits in its bound.

    Radial-gate repair may move mask_r_* by 0.02 m past the bound; that
    repair is part of the sampler, so it is allowed.
    """
    for dim in dims:
        value = _overlay_value(overlay, dim)
        if value is None:
            return False
        if dim.kind == "bool":
            continue
        lo, hi = float(dim.low), float(dim.high)
        if dim.key in ("mask_r_low", "mask_r_high"):
            lo -= 0.021
            hi += 0.021
        if not (lo - 1e-6 <= float(value) <= hi + 1e-6):
            return False
    return True


def _slim(run_dir: Path) -> None:
    for name in SLIM_NAMES:
        path = run_dir / name
        if path.exists():
            path.unlink()


def _rewrite_failures() -> None:
    RECORDS.mkdir(parents=True, exist_ok=True)
    rows = []
    for dev in DEV_CASES:
        man = load_manifest(dev)
        for trial in man.get("trials", []):
            if trial.get("valid"):
                continue
            rows.append(
                {
                    "dev": dev,
                    "trial_id": trial.get("trial_id"),
                    "acquisition": trial.get("acquisition"),
                    "failure_reason": trial.get("failure_reason") or "",
                    "elapsed_s": trial.get("elapsed_s"),
                }
            )
    path = RECORDS / "failures.csv"
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=["dev", "trial_id", "acquisition", "failure_reason", "elapsed_s"],
        )
        writer.writeheader()
        writer.writerows(rows)


def write_training_table() -> Path:
    """Rewrite the table from manifests. Idempotent across resumes."""
    RECORDS.mkdir(parents=True, exist_ok=True)
    path = RECORDS / "training_table.csv"
    fields = ["family", "dev", "trial_id", "acquisition", *MEASUREMENT_KEYS, "gt_miou"]
    rows = []
    for dev in DEV_CASES:
        man = load_manifest(dev)
        for trial in man.get("trials", []):
            if not trial.get("valid"):
                continue
            # Gate extras are real Sobol/GP trials and belong in the table.
            # Skip nothing valid. The bulk campaign stops at 32+8, so the
            # table does not grow past that unless the gate ran extras first;
            # those extras are part of the 32.
            row = {
                "family": trial["family"],
                "dev": dev,
                "trial_id": trial["trial_id"],
                "acquisition": "sobol" if str(trial["acquisition"]).startswith("sobol") else "gp",
                "gt_miou": trial["gt_miou"],
            }
            row.update(trial["measurements"])
            rows.append(row)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    return path


def write_summary(dev: str) -> None:
    man = load_manifest(dev)
    trials = man.get("trials", [])
    valid = [t for t in trials if t.get("valid")]
    failed = [t for t in trials if not t.get("valid")]
    mious = [float(t["gt_miou"]) for t in valid if t.get("gt_miou") is not None]
    summary = {
        "dev": dev,
        "family": family_of(dev),
        "attempts": len(trials),
        "valid": len(valid),
        "sobol_valid": len(valid_trials(man, "sobol")),
        "gp_valid": len(valid_trials(man, "gp")),
        "failures": len(failed),
        "miou_min": min(mious) if mious else None,
        "miou_max": max(mious) if mious else None,
        "n_below_0_3": sum(1 for v in mious if v < 0.3),
        "wall_time_s": round(sum(float(t.get("elapsed_s") or 0) for t in trials), 1),
    }
    (study_dir(dev) / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    note = ""
    if valid and summary["n_below_0_3"] == 0:
        note = "\n\nNo valid trial has GT mIoU below 0.3. Recorded for Plan 3; not resampled.\n"
    text = (
        f"# {dev} calibration summary\n\n"
        f"- valid: {summary['valid']} (sobol {summary['sobol_valid']}, gp {summary['gp_valid']})\n"
        f"- attempts: {summary['attempts']}, failures: {summary['failures']}\n"
        f"- GT mIoU range: {summary['miou_min']} .. {summary['miou_max']}\n"
        f"- trials below 0.3: {summary['n_below_0_3']}\n"
        f"- wall time: {summary['wall_time_s']} s\n"
        f"{note}"
    )
    (study_dir(dev) / "summary.md").write_text(text, encoding="utf-8")
    _log(f"summary {dev}: {json.dumps(summary)}")


def run_trial(
    dev: str,
    trial_id: str,
    x: list[float],
    *,
    acquisition: str,
    seed: int,
) -> dict[str, Any]:
    man = load_manifest(dev)
    for rec in man.get("trials", []):
        if rec.get("trial_id") == trial_id and rec.get("valid"):
            _log(f"skip existing valid {dev}/{trial_id}")
            return rec

    family = family_of(dev)
    dims = load_dims(family)
    params_src = REFERENCES_DIR / family
    base = load_anchor_params(params_src)
    overlay = decode_vector(dims, x, base)
    runs_root = study_dir(dev) / "runs"
    run_dir = runs_root / trial_id
    if run_dir.exists():
        shutil.rmtree(run_dir)
    run_dir.mkdir(parents=True)
    params_dir = materialize_run_params(
        run_dir / "params",
        base,
        overlay,
        family_params=load_family_params(params_src),
    )
    log_path = run_dir / "pipeline.log"
    os.environ["PROXY4TUN_SUBSET"] = dev
    t0 = time.time()
    failure = None
    log_text = ""
    try:
        log_text, _elapsed = run_stages(
            run_id=trial_id,
            params_dir=params_dir,
            input_txt=REPO_ROOT / "data" / "subsets" / f"{dev}.txt",
            out_root=runs_root,
            log_path=log_path,
        )
    except Exception as exc:  # noqa: BLE001
        failure = str(exc)
        if log_path.exists():
            log_text = log_path.read_text(encoding="utf-8", errors="ignore")
    elapsed = time.time() - t0

    measured = None
    if failure is None:
        try:
            measured = measure_run(run_dir, dev, params_dir, log_text=log_text)
        except Exception as exc:  # noqa: BLE001
            failure = f"measurement failed: {exc}"
    perf = parse_performance(run_dir / "evaluation" / "performance.md")
    gt_miou = perf.get("mIoU")
    finite = bool(measured and measured["finite"])
    in_bounds = overlay_in_bounds(dims, overlay)
    valid = failure is None and finite and gt_miou is not None and math.isfinite(float(gt_miou))
    if valid and not in_bounds:
        valid = False
        failure = "overlay outside bounds"
    record = {
        "dev": dev,
        "family": family,
        "trial_id": trial_id,
        "acquisition": acquisition,
        "seed": seed,
        "x_unit": normalize(dims, x),
        "x": [float(v) for v in x],
        "overlay": overlay,
        "overlay_in_bounds": in_bounds,
        "measurements": None if measured is None else measured["measurements"],
        "gt_miou": gt_miou,
        "valid": valid,
        "failure_reason": failure,
        "elapsed_s": round(elapsed, 1),
        "log": str(log_path),
    }
    (run_dir / "record.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    _slim(run_dir)
    man = load_manifest(dev)
    man["seed"] = seed
    man["trials"] = [t for t in man.get("trials", []) if t.get("trial_id") != trial_id]
    man["trials"].append(record)
    save_manifest(dev, man)
    _rewrite_failures()
    _log(
        f"{dev}/{trial_id} [{acquisition}] valid={valid} mIoU={gt_miou} "
        f"elapsed={elapsed:.0f}s failure={failure}"
    )
    return record


def _fit_gp(dims: list[Dim], points: list[tuple[list[float], float]], seed: int) -> GaussianProcessRegressor:
    if len(points) < 3:
        raise RuntimeError(f"GP needs >= 3 points, have {len(points)}")
    X = np.asarray([normalize(dims, x) for x, _y in points], dtype=float)
    y = np.asarray([y for _x, y in points], dtype=float)
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


def _propose(gp: GaussianProcessRegressor, dims: list[Dim], rng: np.random.Generator, existing: list[list[float]]) -> tuple[list[float], float]:
    cand = rng.random((N_CAND, len(dims)))
    _mean, sigma = gp.predict(cand, return_std=True)
    order = np.argsort(-np.maximum(sigma, 1e-9))
    existing_z = [normalize(dims, x) for x in existing]
    chosen = int(order[0])
    for idx in order:
        z = cand[int(idx)]
        if existing_z and min(float(np.linalg.norm(z - ez)) for ez in existing_z) < 0.05:
            continue
        chosen = int(idx)
        break
    x = denormalize(dims, list(cand[chosen]))
    return x, float(sigma[chosen])


def _reference_point(dev: str, dims: list[Dim]) -> tuple[list[float], float] | None:
    path = RELEASE2_DATA / "references" / dev / "record.json"
    if not path.exists():
        return None
    rec = json.loads(path.read_text(encoding="utf-8"))
    if rec.get("gt_miou") is None:
        return None
    base = load_anchor_params(REFERENCES_DIR / family_of(dev))
    x: list[float] = []
    for dim in dims:
        stage = base.get(dim.stage) or {}
        try:
            if dim.special == "y_bounds_lower":
                val = get_nested(stage, "processing.y_bounds")[0]
            else:
                val = get_nested(stage, dim.key)
        except (KeyError, TypeError):
            val = 0.5 * (dim.low + dim.high)
        if dim.kind == "bool":
            x.append(1.0 if bool(val) else 0.0)
        else:
            x.append(float(val))
    return x, float(rec["gt_miou"])


def _gp_points(dims: list[Dim], trials: list[dict[str, Any]]) -> list[tuple[list[float], float]]:
    return [(t["x"], float(t["gt_miou"])) for t in trials if t.get("valid") and t.get("x") and t.get("gt_miou") is not None]


def run_gate(dev: str, *, seed: int) -> dict[str, Any]:
    """One Sobol trial and one GP trial. Extras exist only to fit the GP."""
    dims = load_dims(family_of(dev))
    unit = _sobol_unit(4, len(dims), seed=seed)
    sobol = run_trial(dev, "s000", _unit_to_x(dims, unit[0]), acquisition="sobol", seed=seed)
    budget = 1.5 * GATE_BUDGET_S[dev]
    if not sobol.get("valid") or float(sobol.get("elapsed_s") or 1e9) > budget:
        evidence = _gate_evidence(dev, seed, sobol, None, budget, None)
        _save_gate(evidence)
        raise SystemExit(f"Calibration gate FAILED for {dev} on the Sobol trial; see {CALIB / 'GATE.md'}")
    man = load_manifest(dev)
    ok = valid_trials(man)
    extra = 0
    # Up to two further Sobol points, plus the reference, so the GP can fit.
    i = 1
    while len(ok) < 3 and extra < 2 and i < 4:
        run_trial(dev, f"s{i:03d}", _unit_to_x(dims, unit[i]), acquisition="sobol", seed=seed)
        extra += 1
        i += 1
        man = load_manifest(dev)
        ok = valid_trials(man)
    points = _gp_points(dims, ok)
    if len(points) < 3:
        ref = _reference_point(dev, dims)
        if ref is not None:
            points.append(ref)
    gp = _fit_gp(dims, points, seed=seed)
    rng = np.random.default_rng(seed + 17)
    x_g, sigma = _propose(gp, dims, rng, [t["x"] for t in ok])
    gp_trial = run_trial(
        dev,
        "g000",
        x_g,
        acquisition=f"gp_uncertainty_sigma={sigma:.4f}",
        seed=seed,
    )
    budget = 1.5 * GATE_BUDGET_S[dev]
    evidence = _gate_evidence(dev, seed, sobol, gp_trial, budget, sigma)
    _save_gate(evidence)
    _log(f"gate {dev} passed={evidence['passed']}")
    if not evidence["passed"]:
        raise SystemExit(f"Calibration gate FAILED for {dev}; see {CALIB / 'GATE.md'}")
    return evidence


def _gate_evidence(dev, seed, sobol, gp_trial, budget, sigma) -> dict[str, Any]:
    gp_trial = gp_trial or {}
    checks = {
        "sobol_valid": bool(sobol.get("valid")),
        "sobol_measurements_finite": bool(sobol.get("valid")),
        "sobol_miou": sobol.get("gt_miou"),
        "sobol_in_bounds": bool(sobol.get("overlay_in_bounds")),
        "sobol_elapsed_s": sobol.get("elapsed_s"),
        "sobol_within_budget": float(sobol.get("elapsed_s") or 1e9) <= budget,
        "gp_valid": bool(gp_trial.get("valid")),
        "gp_measurements_finite": bool(gp_trial.get("valid")),
        "gp_miou": gp_trial.get("gt_miou"),
        "gp_in_bounds": bool(gp_trial.get("overlay_in_bounds")),
        "gp_elapsed_s": gp_trial.get("elapsed_s"),
        "gp_within_budget": float(gp_trial.get("elapsed_s") or 1e9) <= budget,
        "gp_sigma": sigma,
        "budget_s": budget,
    }
    passed = all(
        checks[k]
        for k in (
            "sobol_valid",
            "sobol_in_bounds",
            "sobol_within_budget",
            "gp_valid",
            "gp_in_bounds",
            "gp_within_budget",
        )
    )
    return {
        "dev": dev,
        "command": f"./venv/bin/python -u bo/release2/calibrate.py --dev {dev} --gate --seed {seed}",
        "passed": passed,
        "checks": checks,
        "sobol_path": str(study_dir(dev) / "runs" / "s000" / "record.json"),
        "gp_path": str(study_dir(dev) / "runs" / "g000" / "record.json"),
    }


def _save_gate(evidence: dict[str, Any]) -> None:
    study_dir(evidence["dev"]).mkdir(parents=True, exist_ok=True)
    (study_dir(evidence["dev"]) / "gate.json").write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    _write_gate_md(evidence)


def _write_gate_md(evidence: dict[str, Any]) -> None:
    path = CALIB / "GATE.md"
    checks = evidence["checks"]
    sigma = checks.get("gp_sigma")
    sigma_txt = "n/a" if sigma is None else f"{sigma:.4f}"
    block = (
        f"## {evidence['dev']} — {'pass' if evidence['passed'] else 'fail'}\n\n"
        f"- Command: `{evidence['command']}`\n"
        f"- Sobol: valid={checks['sobol_valid']}, mIoU={checks['sobol_miou']}, "
        f"in_bounds={checks['sobol_in_bounds']}, elapsed={checks['sobol_elapsed_s']} s "
        f"(budget {checks['budget_s']:.0f} s)\n"
        f"- GP: valid={checks['gp_valid']}, mIoU={checks['gp_miou']}, "
        f"in_bounds={checks['gp_in_bounds']}, sigma={sigma_txt}, "
        f"elapsed={checks['gp_elapsed_s']} s\n"
        f"- Sobol record: `{evidence['sobol_path']}`\n"
        f"- GP record: `{evidence['gp_path']}`\n\n"
    )
    previous = path.read_text(encoding="utf-8") if path.exists() else "# Release 2 calibration gate\n\n"
    # Replace an existing section for this dev.
    heading = f"## {evidence['dev']}"
    if heading in previous:
        head, _, tail = previous.partition(heading)
        rest = tail.split("\n## ", 1)
        previous = head.rstrip() + "\n\n"
        if len(rest) == 2:
            previous += "## " + rest[1]
    path.write_text(previous.rstrip() + "\n\n" + block, encoding="utf-8")


def run_campaign(dev: str, *, n_sobol: int, n_gp: int, seed: int) -> None:
    dims = load_dims(family_of(dev))
    pool_n = max(int(math.ceil(n_sobol * 2)), n_sobol + 16)
    unit = _sobol_unit(pool_n, len(dims), seed=seed)
    man = load_manifest(dev)
    sobol_ok = valid_trials(man, "sobol")
    existing = [
        int(t["trial_id"][1:])
        for t in man.get("trials", [])
        if str(t.get("trial_id", "")).startswith("s") and str(t["trial_id"][1:]).isdigit()
    ]
    i = (max(existing) + 1) if existing else 0
    attempts = 0
    while len(sobol_ok) < n_sobol and attempts < pool_n + 32:
        if i >= len(unit):
            more = _sobol_unit(pool_n, len(dims), seed=seed + 1000 + attempts)
            unit = np.vstack([unit, more])
        run_trial(dev, f"s{i:03d}", _unit_to_x(dims, unit[i]), acquisition="sobol", seed=seed)
        man = load_manifest(dev)
        sobol_ok = valid_trials(man, "sobol")
        i += 1
        attempts += 1
    if len(sobol_ok) < n_sobol:
        raise SystemExit(f"{dev}: only {len(sobol_ok)}/{n_sobol} valid Sobol trials")

    gp_ok = valid_trials(man, "gp")
    existing_g = [
        int(t["trial_id"][1:])
        for t in man.get("trials", [])
        if str(t.get("trial_id", "")).startswith("g") and str(t["trial_id"][1:]).isdigit()
    ]
    g = (max(existing_g) + 1) if existing_g else 0
    rng = np.random.default_rng(seed + 17)
    attempts = 0
    while len(gp_ok) < n_gp and attempts < n_gp * 3:
        man = load_manifest(dev)
        points = _gp_points(dims, valid_trials(man))
        gp = _fit_gp(dims, points, seed=seed)
        x_next, sigma = _propose(gp, dims, rng, [p[0] for p in points])
        run_trial(
            dev,
            f"g{g:03d}",
            x_next,
            acquisition=f"gp_uncertainty_sigma={sigma:.4f}",
            seed=seed,
        )
        man = load_manifest(dev)
        gp_ok = valid_trials(man, "gp")
        g += 1
        attempts += 1
    if len(gp_ok) < n_gp:
        raise SystemExit(f"{dev}: only {len(gp_ok)}/{n_gp} valid GP trials")
    write_training_table()
    write_summary(dev)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dev", required=True, choices=DEV_CASES)
    parser.add_argument("--gate", action="store_true")
    parser.add_argument("--n-sobol", type=int, default=32)
    parser.add_argument("--n-gp", type=int, default=8)
    parser.add_argument("--seed", type=int, default=None)
    args = parser.parse_args()
    seed = DEFAULT_SEED[args.dev] if args.seed is None else args.seed
    if args.gate:
        run_gate(args.dev, seed=seed)
    else:
        run_campaign(args.dev, n_sobol=args.n_sobol, n_gp=args.n_gp, seed=seed)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
