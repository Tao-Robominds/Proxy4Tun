#!/usr/bin/env python3
"""Held-out subset runner for per-family proxy evaluation.

Runs sibling-anchor (and optionally known-bad) configs on unseen sub-tunnels.
Outputs under data/<subset>-family-proxy/ (never data/anchors|baseline|bo).
"""

from __future__ import annotations

import argparse
import json
import math
import os
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
BO_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BO_DIR))

from intrinsics import (  # noqa: E402
    extract_intrinsics,
    has_complete_tier1,
    write_intrinsics,
)
from param_io import load_anchor_params, materialize_run_params  # noqa: E402
from run_bo import (  # noqa: E402
    PROFILE_SCRIPT_DIR,
    STAGE_SCRIPTS,
    VENV_PY,
    parse_performance,
)
from spaces import (  # noqa: E402
    FAMILY_HOLDOUT_SUBSETS,
    family_of_subset,
    holdout_case_config,
)

FAMILY_DIR = BO_DIR / "family"
BAD_CONFIGS_PATH = FAMILY_DIR / "bad_configs.json"


def _env(input_txt: Path, params_dir: Path, out_root: Path, script_dir: Path) -> dict[str, str]:
    env = os.environ.copy()
    env["MPLBACKEND"] = "Agg"
    env["PROXY4TUN_OUT_ROOT"] = str(out_root.resolve())
    env["PROXY4TUN_INPUT_TXT"] = str(input_txt.resolve())
    env["PROXY4TUN_PARAMS_DIR"] = str(params_dir.resolve())
    env["PYTHONPATH"] = os.pathsep.join(
        [
            str(script_dir),
            str(REPO_ROOT / "sam4tun"),
            str(REPO_ROOT / "sam4tun" / "segment-anything"),
            env.get("PYTHONPATH", ""),
        ]
    ).rstrip(os.pathsep)
    return env


def _run_stages(
    *,
    run_id: str,
    params_dir: Path,
    input_txt: Path,
    out_root: Path,
    script_dir: Path,
    log_path: Path,
    start_stage: int = 1,
    end_stage: int = 6,
) -> tuple[str, float]:
    import subprocess

    t0 = time.time()
    lines: list[str] = []
    env = _env(input_txt, params_dir, out_root, script_dir)
    for stage in range(start_stage, end_stage + 1):
        script = script_dir / STAGE_SCRIPTS[stage]
        lines.append(f"\n=== stage {stage}: {script.name} ===\n")
        proc = subprocess.run(
            [str(VENV_PY), "-u", str(script), run_id],
            cwd=str(REPO_ROOT),
            env=env,
            capture_output=True,
            text=True,
        )
        lines.append(proc.stdout or "")
        if proc.stderr:
            lines.append(proc.stderr)
        if proc.returncode != 0:
            lines.append(f"\nFAILED stage {stage} exit={proc.returncode}\n")
            log_path.write_text("".join(lines), encoding="utf-8")
            raise RuntimeError(f"Stage {stage} failed for {run_id}; see {log_path}")
    elapsed = time.time() - t0
    text = "".join(lines)
    log_path.write_text(text, encoding="utf-8")
    return text, elapsed


def _load_bad_overlay(family: str) -> dict[str, dict[str, Any]]:
    if not BAD_CONFIGS_PATH.exists():
        raise FileNotFoundError(
            f"Missing {BAD_CONFIGS_PATH}; run family_proxy.py --select-bad first"
        )
    data = json.loads(BAD_CONFIGS_PATH.read_text(encoding="utf-8"))
    if family not in data:
        raise KeyError(f"No known-bad config for family {family!r} in {BAD_CONFIGS_PATH}")
    return data[family]["overlay"]


def study_root_for(subset: str) -> Path:
    return (REPO_ROOT / "data" / f"{subset}-family-proxy").resolve()


def run_holdout_config(
    subset: str,
    config_kind: str,
    *,
    random_seed: int = 10,
    force: bool = False,
) -> dict[str, Any]:
    """Run one held-out subset with sibling anchor or known-bad overlay."""
    if config_kind not in ("anchor", "bad"):
        raise ValueError(f"config_kind must be 'anchor' or 'bad', got {config_kind!r}")

    cfg = holdout_case_config(subset)
    family = cfg["family"]
    profile = cfg["profile"]
    script_dir = PROFILE_SCRIPT_DIR[profile]
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

    # Resume if already ok
    if manifest_path.exists() and not force:
        man = json.loads(manifest_path.read_text(encoding="utf-8"))
        for rec in man.get("runs", []):
            if rec.get("run_id") == run_id and rec.get("status") == "ok" and rec.get("mIoU") is not None:
                print(f"Skip existing ok run {run_id} mIoU={rec['mIoU']}")
                return rec

    base = load_anchor_params(REPO_ROOT / cfg["params_dir"])
    overlay: dict[str, dict[str, Any]] = {"unfolding": {"random_seed": int(random_seed)}}
    if config_kind == "bad":
        bad = _load_bad_overlay(family)
        for stage, kv in bad.items():
            overlay.setdefault(stage, {}).update(kv)
        overlay.setdefault("unfolding", {})["random_seed"] = int(random_seed)

    params_dir = materialize_run_params(params_root / run_id, base, overlay)
    # Ensure seed written even if overlay merge order differed
    u_path = params_dir / "parameters_unfolding.json"
    u = json.loads(u_path.read_text(encoding="utf-8"))
    u["random_seed"] = int(random_seed)
    u_path.write_text(json.dumps(u, indent=2) + "\n", encoding="utf-8")

    if run_dir.exists():
        shutil.rmtree(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)

    status = "ok"
    log_text = ""
    elapsed = 0.0
    try:
        log_text, elapsed = _run_stages(
            run_id=run_id,
            params_dir=params_dir,
            input_txt=input_txt,
            out_root=runs_root,
            script_dir=script_dir,
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
        "random_seed": int(random_seed),
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

    man: dict[str, Any]
    if manifest_path.exists():
        man = json.loads(manifest_path.read_text(encoding="utf-8"))
    else:
        man = {"subset": subset, "family": family, "runs": []}
    man["runs"] = [r for r in man.get("runs", []) if r.get("run_id") != run_id]
    man["runs"].append(rec)
    man["updated_at"] = datetime.now().isoformat()
    # Drop heavy metrics from nested duplicate? keep full for analysis.
    manifest_path.write_text(json.dumps(man, indent=2) + "\n", encoding="utf-8")

    print(
        f"{run_id} status={status} mIoU={miou} elapsed={elapsed:.1f}s "
        f"tier1_ok={rec['tier1_complete']}"
    )
    return rec


def run_gate_1_2(*, force: bool = False) -> dict[str, Any]:
    """Single-instance validation before scaling held-out evaluation.

    Case: 1-2 with sibling 1-1 anchor params, random_seed=10, full pipeline.
    Pass if pipeline ok, mIoU finite and >= 0.30, Tier-1 complete.
    (No promoted anchor mIoU for 1-2 — floor proves eval + intrinsics work.)
    """
    subset = "1-2"
    FAMILY_DIR.mkdir(parents=True, exist_ok=True)
    rec = run_holdout_config(subset, "anchor", random_seed=10, force=force)
    miou = rec.get("mIoU")
    miou_f = float(miou) if miou is not None else float("nan")
    passed = (
        rec["status"] == "ok"
        and math.isfinite(miou_f)
        and miou_f >= 0.30
        and bool(rec["tier1_complete"])
    )
    gate = {
        "case": subset,
        "config_kind": "anchor",
        "command": (
            "./venv/bin/python bo/run_holdout.py --gate "
            "# 1-2 full pipeline, params from anchors/t1&2/1-1, random_seed=10"
        ),
        "lineage": (
            "sibling anchor params anchors/t1&2/1-1 → data/1-2-family-proxy/runs/1-2-anchor; "
            "stages 1–6 via anchors/t1&2 scripts"
        ),
        "pass_fail_criteria": {
            "pipeline_ok": rec["status"] == "ok",
            "miou_finite_and_ge_0.30": bool(math.isfinite(miou_f) and miou_f >= 0.30),
            "intrinsics_tier1_no_nan": bool(rec["tier1_complete"]),
        },
        "measured_mIoU": miou,
        "orient_h_ring_corr": rec.get("orient_h_ring_corr"),
        "orient_invariant_ok": rec.get("orient_invariant_ok"),
        "tier1_complete": rec["tier1_complete"],
        "passed": passed,
        "evidence_path": str(FAMILY_DIR / "gate_1-2.json"),
        "output_dir": rec["output_dir"],
        "log_path": rec["log_path"],
        "study_root": str(study_root_for(subset)),
    }
    out = FAMILY_DIR / "gate_1-2.json"
    out.write_text(json.dumps(gate, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(gate, indent=2))
    if not passed:
        raise RuntimeError(f"Holdout validation gate FAILED for 1-2; see {out}")
    return gate


def all_holdout_subsets() -> list[str]:
    out: list[str] = []
    for fam in ("t1&2", "t3", "t4&5"):
        out.extend(FAMILY_HOLDOUT_SUBSETS[fam])
    return out


def run_all_holdout(
    *,
    configs: tuple[str, ...] = ("anchor", "bad"),
    force: bool = False,
    only_family: str | None = None,
) -> list[dict[str, Any]]:
    results = []
    for subset in all_holdout_subsets():
        fam = family_of_subset(subset)
        if only_family and fam != only_family:
            continue
        for kind in configs:
            results.append(run_holdout_config(subset, kind, force=force))
    return results


def main() -> None:
    p = argparse.ArgumentParser(description="Per-family held-out subset runner")
    p.add_argument("--gate", action="store_true", help="Single-instance gate on 1-2")
    p.add_argument("--subset", type=str, default=None, help="e.g. 1-3")
    p.add_argument(
        "--config",
        choices=("anchor", "bad", "both"),
        default="both",
        help="Which config(s) to run for --subset / --all",
    )
    p.add_argument("--all", action="store_true", help="Run all held-out subsets")
    p.add_argument("--family", choices=("t1&2", "t3", "t4&5"), default=None)
    p.add_argument("--force", action="store_true")
    p.add_argument("--seed", type=int, default=10)
    args = p.parse_args()

    if args.gate:
        run_gate_1_2(force=args.force)
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
            run_holdout_config(args.subset, kind, random_seed=args.seed, force=args.force)
        return

    p.error("Specify --gate, --subset, or --all")


if __name__ == "__main__":
    main()
