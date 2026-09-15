#!/usr/bin/env python3
"""Round selection for the SC-general refinement campaign.

Rule (same as bo/proxy_scale/select_round.py):
  1. Score anchor and every round with the scaled SC-general proxy.
  2. Monotone accept: only rounds whose scaled proxy beats the anchor.
  3. Among candidates within TIE_MARGIN of the best, prefer lowest residual.
  GT mIoU is revealed offline only and never used for selection.

Usage:
  ./venv/bin/python bo/sc_general/select_round.py --subset 3-4
  ./venv/bin/python bo/sc_general/select_round.py --subset 3-4 --arm fable
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

from bo.sc_general.refine_pilot import VALID_ARMS, out_root_for  # noqa: E402
from bo.sc_general.score_scaled import anchor_run_dir, score_run  # noqa: E402

STAGE3 = _REPO / "data" / "sc-general" / "stage3"
TIE_MARGIN = 0.01


def select_dir_for(arm: str) -> Path:
    if arm == "fable":
        return STAGE3 / "selections-fable"
    if arm == "fable_fresh":
        return STAGE3 / "selections-fable-fresh"
    if arm == "gpt56":
        return STAGE3 / "selections-gpt56"
    if arm == "gemini38":
        return STAGE3 / "selections-gemini38"
    if arm == "random":
        return STAGE3 / "selections-random"
    return STAGE3 / "selections"


def _residual(entry: dict[str, Any]) -> float:
    r = entry.get("recentre_residual_max_cm")
    return float(r) if r is not None and math.isfinite(float(r)) else float("inf")


def _own_residual(run_dir: str, entry: dict[str, Any]) -> None:
    """Prefer the run's own stage-1 residual (full 1-6 reruns re-measure it)."""
    intr_path = Path(run_dir) / "intrinsics.json"
    if intr_path.exists():
        intr = json.loads(intr_path.read_text(encoding="utf-8"))
        r = intr.get("recentre_residual_max_cm")
        if r is not None and math.isfinite(float(r)):
            entry["recentre_residual_max_cm"] = float(r)


def _slim(entry: dict[str, Any]) -> dict[str, Any]:
    return {
        "round": entry["round"],
        "run_dir": entry["run_dir"],
        "proxy_raw": round(float(entry["proxy_raw"]), 4),
        "proxy_scaled": round(float(entry["proxy_scaled"]), 4),
        "band": entry["band"],
        "mIoU": entry.get("mIoU"),
        "recentre_residual_max_cm": entry.get("recentre_residual_max_cm"),
        "features": entry.get("features"),
    }


def _entry_from_record(rd: Path, subset: str) -> dict[str, Any] | None:
    """Build a selection entry from slimmed round artefacts (no depth replay)."""
    rec_path = rd / "reflection_record.json"
    if not rec_path.exists():
        return None
    rec = json.loads(rec_path.read_text(encoding="utf-8"))
    if rec.get("status") != "ok" or rec.get("proxy_scaled") is None:
        return None
    if not (rd / "only_label.csv").exists():
        return None
    miou = None
    og = rd / "offline_gt.json"
    if og.exists():
        try:
            miou = json.loads(og.read_text(encoding="utf-8")).get("perf_mIoU")
        except Exception:
            miou = None
    residual = rec.get("recentre_residual_max_cm")
    _own_residual(str(rd), {"recentre_residual_max_cm": residual})
    intr = rd / "intrinsics.json"
    if intr.exists():
        try:
            r = json.loads(intr.read_text(encoding="utf-8")).get(
                "recentre_residual_max_cm"
            )
            if r is not None and math.isfinite(float(r)):
                residual = float(r)
        except Exception:
            pass
    return {
        "subset": subset,
        "run_dir": str(rd),
        "round": rd.name,
        "proxy_raw": float(rec.get("proxy_raw", rec["proxy_scaled"])),
        "proxy_scaled": float(rec["proxy_scaled"]),
        "band": rec.get("band"),
        "mIoU": float(miou) if miou is not None else None,
        "recentre_residual_max_cm": (
            float(residual) if residual is not None and math.isfinite(float(residual)) else None
        ),
        "features": rec.get("features"),
    }


def select(subset: str, *, arm: str = "scgen") -> dict[str, Any]:
    if arm not in VALID_ARMS:
        raise ValueError(f"unknown arm {arm!r}; expected one of {VALID_ARMS}")
    anchor = score_run(anchor_run_dir(subset), subset, reveal_gt=True)
    anchor["round"] = "anchor"

    rounds: list[dict[str, Any]] = []
    arm_dir = out_root_for(subset, arm=arm)
    for rd in sorted(arm_dir.glob("round*")):
        if not rd.is_dir():
            continue
        rec_path = rd / "reflection_record.json"
        if rec_path.exists():
            rec = json.loads(rec_path.read_text(encoding="utf-8"))
            if rec.get("status") != "ok" or rec.get("proxy_scaled") is None:
                continue
        if not (rd / "only_label.csv").exists():
            continue
        # Prefer live re-score; fall back to reflection_record after slim.
        try:
            entry = score_run(rd, subset, reveal_gt=True)
            entry["round"] = rd.name
            _own_residual(str(rd), entry)
        except (FileNotFoundError, OSError, ValueError):
            entry = _entry_from_record(rd, subset)
            if entry is None:
                continue
        rounds.append(entry)

    candidates = [r for r in rounds if r["proxy_scaled"] > anchor["proxy_scaled"]]
    if candidates:
        best = max(c["proxy_scaled"] for c in candidates)
        tied = [c for c in candidates if c["proxy_scaled"] >= best - TIE_MARGIN]
        selected = min(tied, key=lambda c: (_residual(c), -c["proxy_scaled"]))
        reason = (
            f"best proxy {best:.4f}; {len(tied)} within {TIE_MARGIN} margin; "
            f"residual tiebreak -> {selected['round']}"
        )
    else:
        selected = anchor
        reason = "monotone accept: no round beat anchor scaled proxy"

    a_miou = anchor.get("mIoU")
    s_miou = selected.get("mIoU")
    result = {
        "subset": subset,
        "arm": arm,
        "anchor": _slim(anchor),
        "rounds": [_slim(r) for r in rounds],
        "selected": _slim(selected),
        "selection_reason": reason,
        "delta_proxy_scaled": round(
            float(selected["proxy_scaled"]) - float(anchor["proxy_scaled"]), 4
        ),
        "delta_mIoU_offline": (
            round(float(s_miou) - float(a_miou), 4)
            if a_miou is not None and s_miou is not None
            else None
        ),
    }
    out_dir = select_dir_for(arm)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{subset}.json"
    out_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--subset", required=True)
    p.add_argument("--arm", default="scgen", choices=VALID_ARMS)
    args = p.parse_args()
    print(json.dumps(select(args.subset, arm=args.arm), indent=2))


if __name__ == "__main__":
    main()
