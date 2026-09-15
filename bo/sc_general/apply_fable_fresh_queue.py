#!/usr/bin/env python3
"""Serial apply queue for fable_fresh. Only this process may apply.

Requires FABLE_FRESH_ALLOW_APPLY=1 (set by this script for child applies).

Usage:
  ./venv/bin/python bo/sc_general/apply_fable_fresh_queue.py
  ./venv/bin/python bo/sc_general/apply_fable_fresh_queue.py --once
  ./venv/bin/python bo/sc_general/apply_fable_fresh_queue.py --status
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from bo.sc_general.stage3_report import PANEL  # noqa: E402

STAGE3 = _REPO / "data" / "sc-general" / "stage3"
ROOT = _REPO / "data" / "refinement" / "fable_fresh"
PK = STAGE3 / "packets-fable-fresh"
SEL = STAGE3 / "selections-fable-fresh"
LOG = STAGE3 / "apply_fable_fresh_queue.log"
VENV_PY = str(_REPO / "venv" / "bin" / "python")
CAMPAIGN = str(_REPO / "bo" / "sc_general" / "run_fable_fresh_campaign.py")


def _log(msg: str) -> None:
    line = f"[{time.strftime('%Y-%m-%dT%H:%M:%S')}] {msg}"
    print(line, flush=True)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as fh:
        fh.write(line + "\n")


def round_ok(subset: str, r: int) -> bool:
    rec = ROOT / subset / f"round{r}" / "reflection_record.json"
    if not rec.exists():
        return False
    try:
        data = json.loads(rec.read_text(encoding="utf-8"))
    except Exception:
        return False
    return data.get("status") == "ok" and data.get("proxy_scaled") is not None


def selection_path(subset: str) -> Path:
    return SEL / f"{subset}.json"


def case_done(subset: str) -> bool:
    return all(round_ok(subset, r) for r in (1, 2, 3)) and selection_path(subset).exists()


def clean_incomplete(subset: str) -> None:
    for r in (1, 2, 3):
        d = ROOT / subset / f"round{r}"
        if d.exists() and not round_ok(subset, r):
            _log(f"clean incomplete {subset} R{r}")
            shutil.rmtree(d, ignore_errors=True)


def next_apply(subset: str) -> tuple[int, Path] | None:
    if case_done(subset):
        return None
    for r in (1, 2, 3):
        if round_ok(subset, r):
            continue
        # prior rounds must be ok
        if r > 1 and not all(round_ok(subset, p) for p in range(1, r)):
            return None
        prop = PK / subset / f"round{r}_proposal.json"
        if prop.exists():
            return r, prop
        return None
    # all rounds ok, need finish
    return None


def needs_finish(subset: str) -> bool:
    return all(round_ok(subset, r) for r in (1, 2, 3)) and not selection_path(
        subset
    ).exists()


def run_apply(subset: str, r: int, prop: Path) -> int:
    env = os.environ.copy()
    env["FABLE_FRESH_ALLOW_APPLY"] = "1"
    env["PYTHONUNBUFFERED"] = "1"
    cmd = [
        VENV_PY,
        CAMPAIGN,
        "--apply",
        subset,
        "--round",
        str(r),
        "--proposal-json",
        str(prop),
    ]
    _log(f"APPLY {subset} R{r}")
    proc = subprocess.run(cmd, cwd=str(_REPO), env=env)
    _log(f"APPLY {subset} R{r} rc={proc.returncode}")
    return proc.returncode


def run_finish(subset: str) -> int:
    _log(f"FINISH {subset}")
    proc = subprocess.run(
        [VENV_PY, CAMPAIGN, "--finish", subset],
        cwd=str(_REPO),
    )
    _log(f"FINISH {subset} rc={proc.returncode}")
    return proc.returncode


def status() -> None:
    done = sum(1 for s in PANEL if case_done(s))
    print(f"done={done}/22 free_gb={shutil.disk_usage(_REPO).free/1e9:.1f}")
    for s in PANEL:
        rounds = "".join("Y" if round_ok(s, r) else "." for r in (1, 2, 3))
        props = "".join(
            "p" if (PK / s / f"round{r}_proposal.json").exists() else "."
            for r in (1, 2, 3)
        )
        sel = "S" if selection_path(s).exists() else "-"
        na = next_apply(s)
        hint = f"next=R{na[0]}" if na else ("finish" if needs_finish(s) else ("done" if case_done(s) else "wait_prop"))
        print(f"  {s:5} rounds={rounds} props={props} sel={sel} {hint}")


def step_once(fail_counts: dict[str, int] | None = None) -> bool:
    """Return True if work was done."""
    if fail_counts is None:
        fail_counts = {}
    for s in PANEL:
        clean_incomplete(s)
    for s in PANEL:
        if needs_finish(s):
            run_finish(s)
            return True
    for s in PANEL:
        na = next_apply(s)
        if na is None:
            continue
        r, prop = na
        key = f"{s}:R{r}"
        if fail_counts.get(key, 0) >= 2:
            _log(f"SKIP {key} after {fail_counts[key]} failures")
            continue
        clean_incomplete(s)
        rc = run_apply(s, r, prop)
        if rc != 0:
            fail_counts[key] = fail_counts.get(key, 0) + 1
            _log(f"FAIL {s} R{r} count={fail_counts[key]}; will retry later")
            clean_incomplete(s)
            time.sleep(5)
            return True
        fail_counts.pop(key, None)
        if needs_finish(s):
            run_finish(s)
        return True
    return False


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--once", action="store_true")
    p.add_argument("--status", action="store_true")
    p.add_argument("--idle-sleep", type=float, default=20.0)
    args = p.parse_args()

    if args.status:
        status()
        return

    if args.once:
        did = step_once()
        status()
        sys.exit(0 if did else 2)

    _log("queue start")
    idle = 0
    fail_counts: dict[str, int] = {}
    while True:
        if all(case_done(s) for s in PANEL):
            _log("ALL DONE")
            status()
            break
        did = step_once(fail_counts)
        if did:
            idle = 0
            continue
        idle += 1
        if idle % 6 == 1:
            _log("idle — waiting for proposals")
            status()
        time.sleep(args.idle_sleep)


if __name__ == "__main__":
    main()
