#!/usr/bin/env python3
"""Extract and validate a proposal JSON from an agent response text file."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from validate_overlay import validate_overlay


def extract_json(text: str) -> dict:
    text = text.strip()
    # Prefer fenced block
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, flags=re.S)
    if m:
        return json.loads(m.group(1))
    # Or first balanced {...}
    start = text.find("{")
    if start < 0:
        raise ValueError("no JSON object found")
    depth = 0
    for i, ch in enumerate(text[start:], start=start):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return json.loads(text[start : i + 1])
    raise ValueError("unbalanced JSON object")


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--subset", required=True)
    p.add_argument("--response", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    text = args.response.read_text(encoding="utf-8", errors="replace")
    prop = extract_json(text)
    for key in ("observation", "failure_mode", "rationale", "overlay"):
        if key not in prop:
            print(f"missing key: {key}", file=sys.stderr)
            return 1
    ok, errors, norm = validate_overlay(args.subset, prop["overlay"])
    if not ok:
        print(json.dumps({"ok": False, "errors": errors}, indent=2), file=sys.stderr)
        return 1
    prop["overlay"] = norm
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(prop, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "out": str(args.out), "overlay": norm}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
