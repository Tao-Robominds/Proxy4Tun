#!/usr/bin/env python3
"""Reference and degraded runs for one evaluation subset.

Reference parameters come from configs/references/<family>. The degraded arm
uses the frozen stage 2-5 overlay and a copy of the reference stage-1
checkpoint, so both arms share the unfolding frame.

Usage:
  ./venv/bin/python -u bo/release2/run_pair.py --subset 1-2 --arm reference
  ./venv/bin/python -u bo/release2/run_pair.py --subset 1-2 --arm degraded
  ./venv/bin/python -u bo/release2/run_pair.py --gate
  ./venv/bin/python -u bo/release2/run_pair.py --bulk
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from bo.paths import REFERENCES_DIR, RELEASE2_DATA, REPO_ROOT  # noqa: E402
from bo.release2.measure import measure_run  # noqa: E402
from bo.release2.score import score_measurements  # noqa: E402
from bo.runtime.metadata import family_of  # noqa: E402
from bo.runtime.param_io import (  # noqa: E402
    get_nested,
    load_anchor_params,
    load_family_params,
    materialize_run_params,
)
from bo.runtime.pipeline import copy_checkpoint, parse_performance, run_stages  # noqa: E402

DEG = RELEASE2_DATA / "degradation"
REFS = RELEASE2_DATA / "references"
SELECTION = DEG / "records" / "overlay_selection.json"
FAILURES = DEG / "records" / "failures.csv"
# Plan 1 measured stage 1-6 times. A gate run must finish within 1.5x.
GATE_BUDGET_S = {"staggered": 283.1 * 1.5, "continuous": 223.2 * 1.5, "complex": 268.7 * 1.5}
GATE_SUBSET = "1-2"
SLIM_NAMES = (
    "state.pkl",
    "unwrapped.csv",
    "denoised.csv",
    "enhanced.csv",
    "final.csv",
    "pixel_to_point.pkl",
    "results.pkl",
)

# 27 evaluation subsets: every labelled subset except the three development scans.
EVAL_SUBSETS = (
    "1-1", "1-2", "1-3", "1-4", "1-5",
    "2-2", "2-3", "2-4", "2-5",
    "3-2", "3-3", "3-4", "3-5", "3-6", "3-7", "3-8", "3-9", "3-10",
    "4-1", "4-2", "4-3", "4-4", "4-5",
    "5-2", "5-3", "5-4", "5-5",
)


def _log(msg: str) -> None:
    print(f"[{datetime.now().isoformat(timespec='seconds')}] {msg}", flush=True)


def load_selection() -> dict[str, dict[str, Any]]:
    if not SELECTION.exists():
        raise SystemExit(f"missing frozen overlay selection: {SELECTION}")
    payload = json.loads(SELECTION.read_text(encoding="utf-8"))
    return {item["family"]: item for item in payload["families"]}


def run_dir_for(subset: str, arm: str) -> Path:
    root = REFS if arm == "reference" else DEG
    return root / subset


def _sha256(path: Path) -> str | None:
    if not path.exists():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _finite_score(scored: dict[str, Any] | None) -> bool:
    if not scored:
        return False
    try:
        return math.isfinite(float(scored["score"]))
    except (KeyError, TypeError, ValueError):
        return False


def _append_failure(subset: str, arm: str, attempt: int, reason: str) -> None:
    FAILURES.parent.mkdir(parents=True, exist_ok=True)
    new = not FAILURES.exists()
    with FAILURES.open("a", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["subset", "arm", "attempt", "failure_reason"])
        if new:
            writer.writeheader()
        writer.writerow(
            {"subset": subset, "arm": arm, "attempt": attempt, "failure_reason": reason}
        )


def _write_record(run_dir: Path, record: dict[str, Any]) -> None:
    (run_dir / "record.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")


def _existing(subset: str, arm: str) -> dict[str, Any] | None:
    path = run_dir_for(subset, arm) / "record.json"
    if not path.exists():
        return None
    rec = json.loads(path.read_text(encoding="utf-8"))
    if rec.get("valid") and rec.get("arm") == arm:
        return rec
    return None


def _slim(run_dir: Path) -> None:
    for name in SLIM_NAMES:
        path = run_dir / name
        if path.exists():
            path.unlink()


def run_arm(subset: str, arm: str, *, force: bool = False) -> dict[str, Any]:
    if arm not in ("reference", "degraded"):
        raise SystemExit(f"unknown arm {arm}")
    if subset not in EVAL_SUBSETS:
        raise SystemExit(f"{subset} is not an evaluation subset")
    if not force:
        existing = _existing(subset, arm)
        if existing is not None:
            _log(f"skip existing valid {subset}/{arm}")
            return existing

    family = family_of(subset)
    params_src = REFERENCES_DIR / family
    base = load_anchor_params(params_src)
    overlay: dict = {}
    if arm == "degraded":
        overlay = load_selection()[family]["overlay"]
    run_dir = run_dir_for(subset, arm)
    if run_dir.exists():
        shutil.rmtree(run_dir)
    run_dir.mkdir(parents=True)
    if arm == "reference":
        params_dir = params_src
    else:
        params_dir = materialize_run_params(
            run_dir / "params",
            base,
            overlay,
            family_params=load_family_params(params_src),
        )
    input_txt = REPO_ROOT / "data" / "subsets" / f"{subset}.txt"
    log_path = run_dir / "pipeline.log"
    os.environ["PROXY4TUN_SUBSET"] = subset
    failure = None
    log_text = ""
    t0 = time.time()
    try:
        if arm == "degraded":
            ref_dir = run_dir_for(subset, "reference")
            copied = copy_checkpoint(ref_dir, run_dir)
            if copied < 2 or not (run_dir / "unwrapped.csv").exists() or not (run_dir / "state.pkl").exists():
                raise RuntimeError(f"reference stage-1 checkpoint missing in {ref_dir}")
            log_text, _elapsed = run_stages(
                run_id=subset,
                params_dir=params_dir,
                input_txt=input_txt,
                out_root=DEG,
                log_path=log_path,
                start_stage=2,
            )
        else:
            log_text, _elapsed = run_stages(
                run_id=subset,
                params_dir=params_dir,
                input_txt=input_txt,
                out_root=REFS,
                log_path=log_path,
            )
    except Exception as exc:  # noqa: BLE001
        failure = str(exc)
        if log_path.exists():
            log_text = log_path.read_text(encoding="utf-8", errors="ignore")
    elapsed = time.time() - t0

    measured = None
    scored = None
    if failure is None:
        try:
            measured = measure_run(run_dir, subset, params_dir, log_text=log_text)
            scored = score_measurements(measured["measurements"])
        except Exception as exc:  # noqa: BLE001
            failure = f"measurement failed: {exc}"
    perf = parse_performance(run_dir / "evaluation" / "performance.md")
    gt_miou = perf.get("mIoU")
    stage1_hash = _sha256(run_dir / "unwrapped.csv")
    valid = (
        failure is None
        and measured is not None
        and measured["finite"]
        and _finite_score(scored)
        and gt_miou is not None
        and math.isfinite(float(gt_miou))
        and stage1_hash is not None
    )
    record = {
        "subset": subset,
        "family": family,
        "arm": arm,
        "overlay": overlay,
        "measurements": None if measured is None else measured["measurements"],
        "score": None if scored is None else scored["score"],
        "score_raw": None if scored is None else scored["score_raw"],
        "band": None if scored is None else scored["band"],
        "gt_miou": gt_miou,
        "valid": valid,
        "failure_reason": failure,
        "elapsed_s": round(elapsed, 1),
        "stage1_unwrapped_sha256": stage1_hash,
        "log": str(log_path),
    }
    _write_record(run_dir, record)
    if arm == "degraded":
        _slim(run_dir)
    _log(
        f"{subset}/{arm} valid={valid} score={record['score']} mIoU={gt_miou} "
        f"elapsed={elapsed:.0f}s failure={failure}"
    )
    return record


def _values_match(left, right) -> bool:
    if isinstance(left, bool) or isinstance(right, bool):
        return bool(left) == bool(right)
    if isinstance(left, list) and isinstance(right, list):
        return len(left) == len(right) and all(_values_match(a, b) for a, b in zip(left, right))
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return math.isclose(float(left), float(right), rel_tol=0.0, abs_tol=1e-6)
    return left == right


def _overlay_applied(subset: str, overlay: dict) -> bool:
    params_dir = run_dir_for(subset, "degraded") / "params"
    ref_unfold = REFERENCES_DIR / family_of(subset) / "parameters_unfolding.json"
    deg_unfold = params_dir / "parameters_unfolding.json"
    if _sha256(ref_unfold) != _sha256(deg_unfold):
        return False
    for stage, keys in overlay.items():
        path = params_dir / f"parameters_{stage}.json"
        if not path.exists():
            return False
        params = json.loads(path.read_text(encoding="utf-8"))
        for key, value in keys.items():
            try:
                got = get_nested(params, key)
            except (KeyError, TypeError):
                return False
            if not _values_match(got, value):
                return False
    return True


def run_gate() -> dict[str, Any]:
    subset = GATE_SUBSET
    family = family_of(subset)
    budget = GATE_BUDGET_S[family]
    ref = run_arm(subset, "reference")
    deg = run_arm(subset, "degraded") if ref.get("valid") else {"valid": False, "failure_reason": "reference invalid"}
    selection = load_selection()[family]
    same_frame = (
        ref.get("stage1_unwrapped_sha256")
        and ref.get("stage1_unwrapped_sha256") == deg.get("stage1_unwrapped_sha256")
    )
    checks = {
        "reference_valid": bool(ref.get("valid")),
        "degraded_valid": bool(deg.get("valid")),
        "overlay_matches_selection": _overlay_applied(subset, selection["overlay"]) if deg.get("valid") else False,
        "stage1_hash_equal": bool(same_frame),
        "reference_score": ref.get("score"),
        "degraded_score": deg.get("score"),
        "scores_finite": _finite_score(ref) and _finite_score(deg),
        "reference_elapsed_s": ref.get("elapsed_s"),
        "degraded_elapsed_s": deg.get("elapsed_s"),
        "reference_within_budget": float(ref.get("elapsed_s") or 1e9) <= budget,
        "degraded_within_budget": float(deg.get("elapsed_s") or 1e9) <= budget,
        "budget_s": budget,
        "reference_miou": ref.get("gt_miou"),
        "degraded_miou": deg.get("gt_miou"),
    }
    passed = all(
        checks[k]
        for k in (
            "reference_valid",
            "degraded_valid",
            "overlay_matches_selection",
            "stage1_hash_equal",
            "scores_finite",
            "reference_within_budget",
            "degraded_within_budget",
        )
    )
    evidence = {
        "subset": subset,
        "command": f"./venv/bin/python -u bo/release2/run_pair.py --gate",
        "passed": passed,
        "checks": checks,
        "reference_record": str(run_dir_for(subset, "reference") / "record.json"),
        "degraded_record": str(run_dir_for(subset, "degraded") / "record.json"),
    }
    (DEG / "gate.json").write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    (DEG / "GATE.md").write_text(
        "\n".join(
            [
                "# Release 2 degradation gate",
                "",
                f"## {subset} — {'pass' if passed else 'fail'}",
                "",
                f"- Command: `{evidence['command']}`",
                f"- Reference: valid={checks['reference_valid']}, score={checks['reference_score']}, "
                f"mIoU={checks['reference_miou']}, elapsed={checks['reference_elapsed_s']} s "
                f"(budget {budget:.0f} s)",
                f"- Degraded: valid={checks['degraded_valid']}, score={checks['degraded_score']}, "
                f"mIoU={checks['degraded_miou']}, elapsed={checks['degraded_elapsed_s']} s",
                f"- Overlay matches frozen selection: {checks['overlay_matches_selection']}",
                f"- Stage-1 unwrapped.csv hash equal: {checks['stage1_hash_equal']}",
                f"- Reference record: `{evidence['reference_record']}`",
                f"- Degraded record: `{evidence['degraded_record']}`",
                "",
            ]
        ),
        encoding="utf-8",
    )
    _log(f"degradation gate passed={passed}")
    if not passed:
        raise SystemExit(f"Degradation gate FAILED; see {DEG / 'GATE.md'}")
    return evidence


def _run_with_retry(subset: str, arm: str) -> dict[str, Any]:
    rec = run_arm(subset, arm)
    if rec.get("valid"):
        return rec
    _append_failure(subset, arm, 1, str(rec.get("failure_reason")))
    _log(f"retry {subset}/{arm}")
    rec = run_arm(subset, arm, force=True)
    if not rec.get("valid"):
        _append_failure(subset, arm, 2, str(rec.get("failure_reason")))
    return rec


def run_bulk() -> int:
    gate_path = DEG / "gate.json"
    if not gate_path.exists():
        raise SystemExit("refusing bulk: degradation gate has not been run")
    gate = json.loads(gate_path.read_text(encoding="utf-8"))
    if not gate.get("passed"):
        raise SystemExit("refusing bulk: degradation gate failed")
    short = []
    for subset in EVAL_SUBSETS:
        ref = _run_with_retry(subset, "reference")
        if not ref.get("valid"):
            short.append(f"{subset}/reference")
            continue
        deg = _run_with_retry(subset, "degraded")
        if not deg.get("valid"):
            short.append(f"{subset}/degraded")
    if short:
        _log(f"shortfall ({len(short)}): {', '.join(short)}")
    else:
        _log("bulk pairs complete: 27 reference + 27 degraded")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--subset")
    parser.add_argument("--arm", choices=("reference", "degraded"))
    parser.add_argument("--gate", action="store_true")
    parser.add_argument("--bulk", action="store_true")
    args = parser.parse_args()
    if args.gate:
        run_gate()
        return 0
    if args.bulk:
        return run_bulk()
    if not args.subset or not args.arm:
        raise SystemExit("pass --subset and --arm, or --gate, or --bulk")
    run_arm(args.subset, args.arm)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
