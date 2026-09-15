#!/usr/bin/env python3
"""Verify the scaled-proxy mid band against the frozen holdout table.

Reads bo/full_stage/holdout_scores.csv, applies the [0,1] clip, and writes
bands.json with the per-anchor band assignment. Asserts that the refine band
[0.5, 0.7) contains all 9 anchors whose GT mIoU < 0.7.
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))
from bo.paths import FULL_STAGE_PKG, PROXY_SCALE_PKG
from bo.proxy_scale.score_scaled import band, scale

HOLDOUT = FULL_STAGE_PKG / "holdout_scores.csv"
OUT = PROXY_SCALE_PKG / "bands.json"


def main() -> None:
    rows = list(csv.DictReader(HOLDOUT.open()))
    anchors = [r for r in rows if r["config_kind"] == "anchor"]
    table = []
    for r in anchors:
        ps = scale(float(r["proxy"]))
        table.append(
            {
                "subset": r["subset"],
                "family": r["family"],
                "proxy_raw": round(float(r["proxy"]), 4),
                "proxy_scaled": round(ps, 4),
                "band": band(ps),
                "gt_mIoU": round(float(r["mIoU"]), 4),
                "gt_low": float(r["mIoU"]) < 0.7,
                "recentre_residual_max_cm": float(r["recentre_residual_max_cm"])
                if r.get("recentre_residual_max_cm") not in (None, "")
                else None,
            }
        )
    table.sort(key=lambda t: t["proxy_scaled"])

    refine = [t for t in table if t["band"] == "refine"]
    gt_low = {t["subset"] for t in table if t["gt_low"]}
    refine_set = {t["subset"] for t in refine}
    missing = sorted(gt_low - refine_set)

    summary = {
        "n_anchors": len(table),
        "n_refine_band": len(refine),
        "refine_band": sorted(refine_set),
        "n_gt_low": len(gt_low),
        "gt_low_missing_from_band": missing,
        "check_all_gt_low_in_band": not missing,
        "refine_band_mean_proxy_scaled": round(
            sum(t["proxy_scaled"] for t in refine) / len(refine), 4
        ),
        "refine_band_mean_gt_mIoU": round(sum(t["gt_mIoU"] for t in refine) / len(refine), 4),
    }
    OUT.write_text(json.dumps({"summary": summary, "anchors": table}, indent=2) + "\n")
    print(json.dumps(summary, indent=2))
    assert not missing, f"GT-low anchors missing from refine band: {missing}"


if __name__ == "__main__":
    main()
