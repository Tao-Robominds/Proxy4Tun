#!/usr/bin/env python3
"""Assemble GPT-5.6 campaign results vs anchors and prior Fable campaign."""
from __future__ import annotations

import csv
import json
from pathlib import Path

from constants import CAMPAIGN_DIR, SELECTIONS_DIR, SUBSETS

PRIOR = {
    # From user table / bo-proxy-scale report (offline mIoU after selection)
    "3-4": {"arm": "cursor3", "anchor_mIoU": 0.622, "selected_mIoU": 0.631, "d": 0.009},
    "3-2": {"arm": "cursor3", "anchor_mIoU": 0.631, "selected_mIoU": 0.719, "d": 0.088},
    "3-5": {"arm": "cursor2", "anchor_mIoU": 0.588, "selected_mIoU": 0.628, "d": 0.040},
    "4-4": {"arm": "cursor2", "anchor_mIoU": 0.347, "selected_mIoU": 0.700, "d": 0.353},
    "4-3": {"arm": "cursor2_s1", "anchor_mIoU": 0.516, "selected_mIoU": 0.554, "d": 0.038},
    "4-1": {"arm": "cursor3", "anchor_mIoU": 0.635, "selected_mIoU": 0.655, "d": 0.020},
    "1-4": {"arm": "cursor2", "anchor_mIoU": 0.556, "selected_mIoU": 0.596, "d": 0.040},
    "1-5": {"arm": "cursor2", "anchor_mIoU": 0.549, "selected_mIoU": 0.782, "d": 0.233},
    "2-2": {"arm": "cursor3", "anchor_mIoU": 0.673, "selected_mIoU": 0.668, "d": -0.005},
}


def main() -> None:
    rows = []
    for s in SUBSETS:
        path = SELECTIONS_DIR / f"{s}_gpt56.json"
        if not path.exists():
            rows.append({"subset": s, "status": "missing"})
            continue
        sel = json.loads(path.read_text())
        prior = PRIOR[s]
        rows.append(
            {
                "subset": s,
                "status": "ok",
                "anchor_proxy_scaled": sel["anchor"]["proxy_scaled"],
                "anchor_mIoU": sel["anchor"]["mIoU_offline"],
                "selected_round": sel["selected"]["round"],
                "selected_proxy_scaled": sel["selected"]["proxy_scaled"],
                "selected_mIoU": sel["selected"]["mIoU_offline"],
                "delta_proxy_scaled": sel["delta_proxy_scaled"],
                "delta_mIoU": sel["delta_mIoU_offline"],
                "fable_selected_mIoU": prior["selected_mIoU"],
                "fable_delta_mIoU": prior["d"],
                "selection_reason": sel["selection_reason"],
            }
        )

    csv_path = CAMPAIGN_DIR / "results.csv"
    fields = [
        "subset", "status", "anchor_proxy_scaled", "anchor_mIoU",
        "selected_round", "selected_proxy_scaled", "selected_mIoU",
        "delta_proxy_scaled", "delta_mIoU",
        "fable_selected_mIoU", "fable_delta_mIoU", "selection_reason",
    ]
    with csv_path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

    ok = [r for r in rows if r.get("status") == "ok" and r.get("selected_mIoU") is not None]
    def mean(key):
        xs = [float(r[key]) for r in ok if r.get(key) is not None]
        return sum(xs) / len(xs) if xs else float("nan")

    md = []
    md.append("# GPT-5.6 Isolated Refinement Campaign — Report")
    md.append("")
    md.append("Model: **GPT-5.6 Sol**. Arm: `gpt56`.")
    md.append("Isolation: sanitized domain knowledge; Fable recipes/logs denied;")
    md.append("GT mIoU withheld until after proxy selection.")
    md.append("Stage-1 policy: residual > 10 cm unlocks unfolding overlays.")
    md.append("")
    md.append("## Headline")
    md.append("")
    md.append("| Scope | n | Mean mIoU |")
    md.append("|---|---:|---:|")
    md.append(f"| Anchor | {len(ok)} | {mean('anchor_mIoU'):.3f} |")
    md.append(f"| GPT-5.6 selected | {len(ok)} | **{mean('selected_mIoU'):.3f}** |")
    md.append(f"| Prior Fable selected | {len(ok)} | {mean('fable_selected_mIoU'):.3f} |")
    md.append(f"| Mean ΔmIoU (GPT-5.6) | {len(ok)} | {mean('delta_mIoU'):+.3f} |")
    md.append(f"| Mean ΔmIoU (Fable) | {len(ok)} | {mean('fable_delta_mIoU'):+.3f} |")
    md.append("")
    md.append("## Per-subset")
    md.append("")
    md.append("| Subset | Anchor proxy | Anchor mIoU | Selected | GPT mIoU | Δ | Fable mIoU | Fable Δ |")
    md.append("|---|---:|---:|---|---:|---:|---:|---:|")
    for r in rows:
        if r.get("status") != "ok":
            md.append(f"| {r['subset']} | — | — | — | — | — | — | missing |")
            continue
        md.append(
            f"| {r['subset']} | {r['anchor_proxy_scaled']:.3f} | {r['anchor_mIoU']:.3f} | "
            f"{r['selected_round']} | {r['selected_mIoU']:.3f} | "
            f"{r['delta_mIoU']:+.3f} | {r['fable_selected_mIoU']:.3f} | "
            f"{r['fable_delta_mIoU']:+.3f} |"
        )
    md.append("")
    md.append("## Notes")
    md.append("")
    md.append("- Selection used scaled frozen pooled proxy only (monotone accept + residual tiebreak).")
    md.append("- Prior Fable column is the published 9-candidate table for comparison, not an input.")
    md.append("- Artifacts: `data/<subset>-gpt56-refinement/`; selections: `gpt56-refinement/selections/`.")
    md.append("")
    (CAMPAIGN_DIR / "report.md").write_text("\n".join(md))
    print(f"Wrote {csv_path}")
    print(f"Wrote {CAMPAIGN_DIR / 'report.md'}")
    print(f"GPT mean selected mIoU={mean('selected_mIoU'):.3f} (n={len(ok)})")


if __name__ == "__main__":
    main()
