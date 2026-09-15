#!/usr/bin/env python3
"""Round selection for the widened refinement campaign (arm cursor3).

Rule (user-approved):
  1. Score anchor and every round with the scaled frozen proxy (score_scaled).
  2. Monotone accept: only rounds whose scaled proxy beats the anchor's are
     candidates; if none, keep the anchor.
  3. Residual tiebreak: among candidates within TIE_MARGIN of the best scaled
     proxy, prefer the lowest recentre_residual_max_cm (missing residual loses
     the tiebreak). GT mIoU is recorded for offline evaluation only and never
     used for selection.

Usage:
  ./venv/bin/python bo/proxy_scale/select_round.py --subset 3-4 --arm cursor3
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))
from bo.paths import PROXY_SCALE_PKG, REFLECT_ROOT
from bo.proxy_scale.score_scaled import _anchor_run_dir, score_scaled

SELECT_DIR = PROXY_SCALE_PKG / "selections"

TIE_MARGIN = 0.01


def _residual(entry: dict[str, Any]) -> float:
    r = entry.get("recentre_residual_max_cm")
    return float(r) if r is not None and math.isfinite(float(r)) else float("inf")


def _own_residual(run_dir: str, entry: dict[str, Any]) -> None:
    """Prefer the run's own stage-1 residual (full 1-6 reruns re-measure it);
    score_run backfills the anchor's value when the run lacks one, which would
    blunt the residual tiebreak for stage-1 overlays."""
    intr_path = Path(run_dir) / "intrinsics.json"
    if intr_path.exists():
        intr = json.loads(intr_path.read_text(encoding="utf-8"))
        r = intr.get("recentre_residual_max_cm")
        if r is not None and math.isfinite(float(r)):
            entry["recentre_residual_max_cm"] = float(r)


def select(subset: str, arm: str) -> dict[str, Any]:
    anchor = score_scaled(_anchor_run_dir(subset), subset)
    anchor["round"] = "anchor"

    rounds = []
    arm_dir = REFLECT_ROOT / subset / arm
    for rd in sorted(arm_dir.glob("round*")):
        if not rd.is_dir():
            continue
        entry = score_scaled(rd, subset)
        entry["round"] = rd.name
        _own_residual(str(rd), entry)
        rounds.append(entry)

    candidates = [r for r in rounds if r["proxy_scaled"] > anchor["proxy_scaled"]]
    if candidates:
        best = max(c["proxy_scaled"] for c in candidates)
        tied = [c for c in candidates if c["proxy_scaled"] >= best - TIE_MARGIN]
        # Residual first; among equal residuals prefer the higher proxy score.
        selected = min(tied, key=lambda c: (_residual(c), -c["proxy_scaled"]))
        reason = (
            f"best proxy {best:.4f}; {len(tied)} within {TIE_MARGIN} margin; "
            f"residual tiebreak -> {selected['round']}"
        )
    else:
        selected = anchor
        reason = "monotone accept: no round beat anchor scaled proxy"

    result = {
        "subset": subset,
        "arm": arm,
        "anchor": _slim(anchor),
        "rounds": [_slim(r) for r in rounds],
        "selected": _slim(selected),
        "selection_reason": reason,
        "delta_proxy_scaled": round(selected["proxy_scaled"] - anchor["proxy_scaled"], 4),
        "delta_mIoU_offline": (
            round(selected["mIoU"] - anchor["mIoU"], 4)
            if selected.get("mIoU") is not None and anchor.get("mIoU") is not None
            else None
        ),
    }
    SELECT_DIR.mkdir(exist_ok=True)
    out_path = SELECT_DIR / f"{subset}_{arm}.json"
    out_path.write_text(json.dumps(result, indent=2) + "\n")
    return result


def _slim(entry: dict[str, Any]) -> dict[str, Any]:
    return {
        "round": entry["round"],
        "run_dir": entry["run_dir"],
        "proxy_raw": round(entry["proxy_raw"], 4),
        "proxy_scaled": round(entry["proxy_scaled"], 4),
        "band": entry["band"],
        "mIoU": entry.get("mIoU"),
        "recentre_residual_max_cm": entry.get("recentre_residual_max_cm"),
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--subset", required=True)
    p.add_argument("--arm", default="cursor3")
    args = p.parse_args()
    print(json.dumps(select(args.subset, args.arm), indent=2))


if __name__ == "__main__":
    main()
