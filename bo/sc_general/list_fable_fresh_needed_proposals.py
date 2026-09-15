#!/usr/bin/env python3
"""List fable_fresh cases that need a proposal written (not applied)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO))
from bo.sc_general.stage3_report import PANEL  # noqa: E402

ROOT = _REPO / "data" / "refinement" / "fable_fresh"
PK = _REPO / "data" / "sc-general" / "stage3" / "packets-fable-fresh"
SEL = _REPO / "data" / "sc-general" / "stage3" / "selections-fable-fresh"


def round_ok(subset: str, r: int) -> bool:
    rec = ROOT / subset / f"round{r}" / "reflection_record.json"
    if not rec.exists():
        return False
    try:
        data = json.loads(rec.read_text(encoding="utf-8"))
    except Exception:
        return False
    return data.get("status") == "ok" and data.get("proxy_scaled") is not None


def main() -> None:
    needed = []
    for s in PANEL:
        if (SEL / f"{s}.json").exists() and all(round_ok(s, r) for r in (1, 2, 3)):
            continue
        for r in (1, 2, 3):
            if round_ok(s, r):
                continue
            if r > 1 and not all(round_ok(s, p) for p in range(1, r)):
                break
            prop = PK / s / f"round{r}_proposal.json"
            if not prop.exists():
                needed.append((s, r))
            break
    for s, r in needed:
        print(f"{s}\t{r}")
    if not needed:
        print("NONE", file=sys.stderr)


if __name__ == "__main__":
    main()
