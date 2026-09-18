#!/usr/bin/env python3
"""Scaled proxy scorer for the widened refinement campaign.

Wraps the frozen pooled lean proxy (bo-full-stage/score_run.py) and clips the
raw score to [0, 1]. Scaling choice validated 2026-07-28: raw holdout proxies
span [-0.092, 0.977], so clipping changes no anchor score, while min-max
rescaling would un-flag GT-low anchors 1-4, 1-5, 2-2 and is rejected.

Bands on the scaled score:
  reject  : < 0.5
  refine  : [0.5, 0.7)   <- campaign target band
  accept  : >= 0.7

Usage:
  ./venv/bin/python bo-proxy-scale/score_scaled.py data/reflect/3-4/cursor3/round1 --subset 3-4
  ./venv/bin/python bo-proxy-scale/score_scaled.py --subset 3-4 --anchor
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "bo-full-stage"))

from score_run import _anchor_run_dir, score_run  # noqa: E402

REJECT_THR = 0.5
ACCEPT_THR = 0.7


def scale(proxy_raw: float) -> float:
    return min(max(float(proxy_raw), 0.0), 1.0)


def band(proxy_scaled: float) -> str:
    if proxy_scaled < REJECT_THR:
        return "reject"
    if proxy_scaled < ACCEPT_THR:
        return "refine"
    return "accept"


def score_scaled(run_dir: Path, subset: str, **kwargs: Any) -> dict[str, Any]:
    out = score_run(run_dir, subset, **kwargs)
    out["proxy_raw"] = out["proxy"]
    out["proxy_scaled"] = scale(out["proxy"])
    out["band"] = band(out["proxy_scaled"])
    return out


def main() -> None:
    p = argparse.ArgumentParser(description="Score a run with the scaled frozen proxy")
    p.add_argument("run_dir", nargs="?", type=Path, default=None)
    p.add_argument("--subset", required=True)
    p.add_argument("--anchor", action="store_true", help="Score the holdout/family anchor run")
    args = p.parse_args()

    if args.anchor:
        run_dir = _anchor_run_dir(args.subset)
    elif args.run_dir is not None:
        run_dir = args.run_dir
    else:
        p.error("Provide run_dir or --anchor")

    print(json.dumps(score_scaled(run_dir, args.subset), indent=2))


if __name__ == "__main__":
    main()
