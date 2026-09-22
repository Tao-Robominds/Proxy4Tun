#!/usr/bin/env python3
"""Apply queued LLM proposals then finish cases (GPU serial).

Usage:
  ./venv/bin/python -u bo/release2/apply_queue.py --arm fable --round 1
  ./venv/bin/python -u bo/release2/apply_queue.py --arm fable --finish-done
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from bo.release2.refine import ADMITTED, MODEL_SLUG, apply_proposal, finish, round_dir  # noqa: E402


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--arm", required=True)
    p.add_argument("--round", type=int)
    p.add_argument("--finish-done", action="store_true")
    args = p.parse_args()
    if args.finish_done:
        for subset in ADMITTED:
            n = sum(1 for r in (1, 2, 3) if (round_dir(args.arm, subset, r) / "record.json").exists())
            if n == 3:
                finish(subset, args.arm)
        return 0
    if not args.round:
        raise SystemExit("--round required")
    for subset in ADMITTED:
        rec = round_dir(args.arm, subset, args.round) / "record.json"
        if rec.exists():
            print(f"skip {subset} r{args.round}")
            continue
        prop = (
            _REPO
            / "data"
            / "release2"
            / "refinement"
            / args.arm
            / subset
            / "proposals"
            / f"round{args.round}_proposal.json"
        )
        if not prop.exists():
            print(f"missing proposal {prop}")
            continue
        apply_proposal(subset, args.arm, args.round, prop, provenance={"model": MODEL_SLUG.get(args.arm, args.arm)})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
