#!/usr/bin/env python3
"""Resumable Release-3 panel driver (random + LLM arms).

Usage examples:
  ./venv/bin/python -u bo/release3/run_panel.py --random-remaining
  ./venv/bin/python -u bo/release3/run_panel.py --apply-arm fable --round 1
  ./venv/bin/python -u bo/release3/run_panel.py --finish-arm fable
  ./venv/bin/python -u bo/release3/run_panel.py --status
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import traceback
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from bo.release3.refine import (  # noqa: E402
    ADMITTED,
    MODEL_SLUG,
    PANEL_ARMS,
    apply_proposal,
    emit,
    finish,
    round_dir,
    run_random_case,
)

REFINE = _REPO / "data" / "release3" / "refinement"


def _done(arm: str, subset: str, rounds=(1, 2, 3)) -> bool:
    return all((round_dir(arm, subset, r) / "record.json").exists() for r in rounds)


def status() -> None:
    for arm in PANEL_ARMS:
        n = sum(1 for s in ADMITTED if _done(arm, s))
        props = {
            r: sum(
                1
                for s in ADMITTED
                if (REFINE / arm / s / "proposals" / f"round{r}_proposal.json").exists()
            )
            for r in (1, 2, 3)
        }
        print(f"{arm}: finished {n}/{len(ADMITTED)}; proposals r1={props[1]} r2={props[2]} r3={props[3]}")


def random_remaining() -> None:
    for subset in ADMITTED:
        if _done("random", subset):
            print("skip", subset, flush=True)
            continue
        # Drop incomplete round dirs (no record) left by prior crashes.
        for r in (1, 2, 3):
            rd = round_dir("random", subset, r)
            if rd.exists() and not (rd / "record.json").exists():
                import shutil

                for p in rd.rglob("*"):
                    try:
                        p.chmod(p.stat().st_mode | 0o200)
                    except OSError:
                        pass
                shutil.rmtree(rd, ignore_errors=True)
                print("cleared incomplete", subset, f"r{r}", flush=True)
        print("=== random", subset, flush=True)
        try:
            run_random_case(subset)
        except Exception as exc:  # noqa: BLE001
            print("FAIL", subset, exc, flush=True)
            traceback.print_exc()
    print("RANDOM_ALL_DONE", flush=True)


def apply_arm(arm: str, round_id: int, loop: bool = False) -> None:
    while True:
        applied = 0
        for subset in ADMITTED:
            rec = round_dir(arm, subset, round_id) / "record.json"
            if rec.exists():
                continue
            prop = REFINE / arm / subset / "proposals" / f"round{round_id}_proposal.json"
            if not prop.exists():
                continue
            print(f"apply {subset}/{arm}/r{round_id}", flush=True)
            apply_proposal(
                subset,
                arm,
                round_id,
                prop,
                provenance={"model": MODEL_SLUG.get(arm, arm)},
            )
            applied += 1
        done = sum(1 for s in ADMITTED if (round_dir(arm, s, round_id) / "record.json").exists())
        print(f"records {done}/{len(ADMITTED)} applied_this_pass={applied}", flush=True)
        if done >= len(ADMITTED) or not loop:
            break
        time.sleep(15)
    print(f"APPLY_DONE {arm} r{round_id}", flush=True)


def finish_arm(arm: str) -> None:
    for subset in ADMITTED:
        if _done(arm, subset):
            finish(subset, arm)
    print(f"FINISH_DONE {arm}", flush=True)


def emit_missing(arm: str) -> None:
    for subset in ADMITTED:
        try:
            info = emit(subset, arm)
            print("emit", arm, subset, info.get("round"), flush=True)
        except SystemExit as exc:
            print("skip", arm, subset, exc, flush=True)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--status", action="store_true")
    p.add_argument("--random-remaining", action="store_true")
    p.add_argument("--apply-arm")
    p.add_argument("--round", type=int, default=1)
    p.add_argument("--loop", action="store_true")
    p.add_argument("--finish-arm")
    p.add_argument("--emit-arm")
    args = p.parse_args()
    if args.status:
        status()
        return 0
    if args.random_remaining:
        random_remaining()
        return 0
    if args.apply_arm:
        apply_arm(args.apply_arm, args.round, loop=args.loop)
        return 0
    if args.finish_arm:
        finish_arm(args.finish_arm)
        return 0
    if args.emit_arm:
        emit_missing(args.emit_arm)
        return 0
    status()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
