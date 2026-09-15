#!/usr/bin/env python3
"""Select best GPT-5.6 round by scaled proxy (GT-blind).

Same rule as bo/proxy_scale/select_round.py:
  monotone accept vs anchor; residual tiebreak within 0.01 proxy.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from bo.full_stage.score_run import _anchor_run_dir  # noqa: E402
from bo.proxy_scale.score_scaled import score_scaled  # noqa: E402


from constants import SELECTIONS_DIR, TIE_MARGIN, out_root  # noqa: E402


def _residual(entry: dict[str, Any]) -> float:
    r = entry.get("recentre_residual_max_cm")
    return float(r) if r is not None and math.isfinite(float(r)) else float("inf")


def _own_residual(run_dir: Path, entry: dict[str, Any]) -> None:
    intr = run_dir / "intrinsics.json"
    if intr.exists():
        data = json.loads(intr.read_text(encoding="utf-8"))
        r = data.get("recentre_residual_max_cm")
        if r is not None and math.isfinite(float(r)):
            entry["recentre_residual_max_cm"] = float(r)


def _offline_miou(run_dir: Path) -> float | None:
    offline = run_dir / "evaluation_offline.json"
    if offline.exists():
        return json.loads(offline.read_text()).get("mIoU")
    perf = run_dir / "evaluation" / "performance.md"
    if perf.exists():
        import re
        m = re.search(r"Mean IoU \(mIoU\):\s*([0-9.]+)", perf.read_text())
        return float(m.group(1)) if m else None
    return None


def select(subset: str) -> dict[str, Any]:
    anchor = score_scaled(_anchor_run_dir(subset), subset)
    anchor["round"] = "anchor"
    anchor_miou = anchor.get("mIoU")

    rounds = []
    root = out_root(subset)
    for rd in sorted(root.glob("round*")):
        if not rd.is_dir():
            continue
        entry = score_scaled(rd, subset)
        entry["round"] = rd.name
        _own_residual(rd, entry)
        entry["mIoU_offline"] = _offline_miou(rd)
        rounds.append(entry)

    candidates = [r for r in rounds if r["proxy_scaled"] > anchor["proxy_scaled"]]
    if candidates:
        best = max(c["proxy_scaled"] for c in candidates)
        tied = [c for c in candidates if c["proxy_scaled"] >= best - TIE_MARGIN]
        selected = min(tied, key=lambda c: (_residual(c), -c["proxy_scaled"]))
        reason = (
            f"best proxy {best:.4f}; {len(tied)} within {TIE_MARGIN}; "
            f"residual tiebreak -> {selected['round']}"
        )
    else:
        selected = {**anchor, "mIoU_offline": anchor_miou}
        reason = "monotone accept: no round beat anchor scaled proxy"

    def slim(e: dict[str, Any]) -> dict[str, Any]:
        return {
            "round": e["round"],
            "run_dir": e.get("run_dir"),
            "proxy_raw": round(float(e["proxy_raw"]), 4),
            "proxy_scaled": round(float(e["proxy_scaled"]), 4),
            "band": e["band"],
            "recentre_residual_max_cm": e.get("recentre_residual_max_cm"),
            "mIoU_offline": e.get("mIoU_offline", e.get("mIoU")),
        }

    result = {
        "subset": subset,
        "arm": "gpt56",
        "anchor": slim(anchor),
        "rounds": [slim(r) for r in rounds],
        "selected": slim(selected),
        "selection_reason": reason,
        "delta_proxy_scaled": round(
            float(selected["proxy_scaled"]) - float(anchor["proxy_scaled"]), 4
        ),
        "delta_mIoU_offline": (
            round(
                float(selected.get("mIoU_offline") or selected.get("mIoU"))
                - float(anchor_miou),
                4,
            )
            if selected.get("mIoU_offline", selected.get("mIoU")) is not None
            and anchor_miou is not None
            else None
        ),
    }
    SELECTIONS_DIR.mkdir(exist_ok=True)
    out = SELECTIONS_DIR / f"{subset}_gpt56.json"
    out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    return result


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--subset", required=True)
    args = p.parse_args()
    select(args.subset)


if __name__ == "__main__":
    main()
