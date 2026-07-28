#!/usr/bin/env python3
"""Assemble refined_scores.csv and the panel summary for the campaign report.

Uses one selection per GT-low subset (4-3 -> cursor2_s1 per user decision) and
anchor rows from bo-full-stage/holdout_scores.csv for the unrefined subsets.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent
HOLDOUT = REPO_ROOT / "bo-full-stage" / "holdout_scores.csv"
SEL = HERE / "selections"
OUT_CSV = HERE / "refined_scores.csv"

# One arm per refined subset (user decision: 4-3 uses the stage-1-unlocked retry).
REFINED = {
    "4-4": "cursor2",
    "4-3": "cursor2_s1",
    "1-5": "cursor2",
    "1-4": "cursor2",
    "3-5": "cursor2",
    "3-4": "cursor3",
    "3-2": "cursor3",
    "4-1": "cursor3",
    "2-2": "cursor3",
}


def clip(p: float) -> float:
    return min(max(p, 0.0), 1.0)


def main() -> None:
    anchors = {
        r["subset"]: r
        for r in csv.DictReader(HOLDOUT.open())
        if r["config_kind"] == "anchor"
    }

    rows = []
    for subset in sorted(anchors, key=lambda s: (s.split("-")[0], s)):
        a = anchors[subset]
        anchor_proxy = clip(float(a["proxy"]))
        anchor_miou = float(a["mIoU"])
        row = {
            "subset": subset,
            "family": a["family"],
            "refined": subset in REFINED,
            "arm": REFINED.get(subset, ""),
            "anchor_proxy_scaled": round(anchor_proxy, 4),
            "anchor_mIoU": anchor_miou,
            "selected_round": "",
            "selected_proxy_scaled": round(anchor_proxy, 4),
            "selected_mIoU": anchor_miou,
            "delta_proxy_scaled": 0.0,
            "delta_mIoU": 0.0,
            "crossed_accept": False,
        }
        if subset in REFINED:
            sel = json.loads((SEL / f"{subset}_{REFINED[subset]}.json").read_text())
            s = sel["selected"]
            row.update(
                selected_round=s["round"],
                selected_proxy_scaled=s["proxy_scaled"],
                selected_mIoU=s["mIoU"],
                delta_proxy_scaled=round(s["proxy_scaled"] - row["anchor_proxy_scaled"], 4),
                delta_mIoU=round(s["mIoU"] - anchor_miou, 4),
                crossed_accept=row["anchor_proxy_scaled"] < 0.7 <= s["proxy_scaled"],
            )
        rows.append(row)

    with OUT_CSV.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    def mean(xs):
        return sum(xs) / len(xs)

    refined = [r for r in rows if r["refined"]]
    band = [r for r in rows if r["anchor_proxy_scaled"] < 0.7]
    summary = {
        "n_panel": len(rows),
        "n_refined (GT-low)": len(refined),
        "refined_mean_proxy_before": round(mean([r["anchor_proxy_scaled"] for r in refined]), 4),
        "refined_mean_proxy_after": round(mean([r["selected_proxy_scaled"] for r in refined]), 4),
        "refined_mean_mIoU_before": round(mean([r["anchor_mIoU"] for r in refined]), 4),
        "refined_mean_mIoU_after": round(mean([r["selected_mIoU"] for r in refined]), 4),
        "band21_mean_proxy_before": round(mean([r["anchor_proxy_scaled"] for r in band]), 4),
        "band21_mean_proxy_after": round(mean([r["selected_proxy_scaled"] for r in band]), 4),
        "band21_mean_mIoU_before": round(mean([r["anchor_mIoU"] for r in band]), 4),
        "band21_mean_mIoU_after": round(mean([r["selected_mIoU"] for r in band]), 4),
        "panel_mean_mIoU_before": round(mean([r["anchor_mIoU"] for r in rows]), 4),
        "panel_mean_mIoU_after": round(mean([r["selected_mIoU"] for r in rows]), 4),
        "improved": sum(1 for r in refined if r["delta_mIoU"] > 0),
        "neutral_or_worse": sum(1 for r in refined if r["delta_mIoU"] <= 0),
        "crossed_accept": [r["subset"] for r in rows if r["crossed_accept"]],
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
