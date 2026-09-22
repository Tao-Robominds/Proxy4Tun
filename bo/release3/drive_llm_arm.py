#!/usr/bin/env python3
"""Drive one LLM arm for release-2 refinement via Cursor Task subagents.

This module is invoked by the parent agent orchestration; it prepares packets
and applies proposals. The parent agent launches the subagent and writes
response.json before calling --apply.

Helpers used by the parent:
  ./venv/bin/python bo/release2/drive_llm_arm.py --prepare SUBSET --arm ARM --round R
  ./venv/bin/python bo/release2/drive_llm_arm.py --apply-file SUBSET --arm ARM --round R --proposal FILE
  ./venv/bin/python bo/release2/drive_llm_arm.py --finish SUBSET --arm ARM
  ./venv/bin/python bo/release2/drive_llm_arm.py --pending --arm ARM
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from bo.release3.refine import (  # noqa: E402
    ADMITTED,
    ARMS,
    MODEL_SLUG,
    apply_proposal,
    case_root,
    emit,
    finish,
    round_dir,
)


def pending(arm: str) -> list[tuple[str, int]]:
    out = []
    for subset in ADMITTED:
        for r in (1, 2, 3):
            if not (round_dir(arm, subset, r) / "record.json").exists():
                out.append((subset, r))
                break  # next round only after current
        else:
            continue
    return out


def prepare(subset: str, arm: str) -> dict:
    packet = emit(subset, arm)
    root = case_root(arm, subset) / "packet"
    return {
        "subset": subset,
        "arm": arm,
        "round": packet["round"],
        "model": MODEL_SLUG[arm],
        "prompt_path": str(root / "AGENT_PROMPT.md"),
        "packet_path": str(root / "packet.json"),
        "feedback_path": str(root / "feedback.json") if (root / "feedback.json").exists() else None,
        "images": packet.get("images") or {},
        "response_path": str(round_dir(arm, subset, packet["round"]) / "response.json"),
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--prepare", metavar="SUBSET")
    p.add_argument("--apply-file", metavar="SUBSET")
    p.add_argument("--finish", metavar="SUBSET")
    p.add_argument("--arm", choices=[a for a in ARMS if a != "random"], required=True)
    p.add_argument("--round", type=int)
    p.add_argument("--proposal", type=Path)
    p.add_argument("--pending", action="store_true")
    args = p.parse_args()
    if args.pending:
        print(json.dumps(pending(args.arm)))
        return 0
    if args.prepare:
        print(json.dumps(prepare(args.prepare, args.arm), indent=2))
        return 0
    if args.apply_file:
        if not args.round or not args.proposal:
            raise SystemExit("--round and --proposal required")
        # Ensure round dir exists for response copy destination
        round_dir(args.arm, args.apply_file, args.round).mkdir(parents=True, exist_ok=True)
        apply_proposal(
            args.apply_file,
            args.arm,
            args.round,
            args.proposal,
            provenance={"model": MODEL_SLUG[args.arm]},
        )
        return 0
    if args.finish:
        finish(args.finish, args.arm)
        return 0
    raise SystemExit("no action")


if __name__ == "__main__":
    raise SystemExit(main())
