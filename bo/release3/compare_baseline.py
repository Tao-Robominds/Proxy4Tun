#!/usr/bin/env python3
"""Compare Release-3 panel results with the frozen Release-2 baseline numbers."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from bo.paths import RELEASE2_DATA, RELEASE3_DATA  # noqa: E402
from bo.release3.refine import ADMITTED, PANEL_ARMS  # noqa: E402

OUT = RELEASE3_DATA / "analysis"


def _load_sel(root: Path, arm: str, subset: str) -> dict | None:
    path = root / "refinement" / "records" / "selections" / arm / f"{subset}.json"
    # release2 path uses same layout; release3 uses RELEASE3_DATA/refinement/records
    if not path.exists():
        alt = root / "records" / "selections" / arm / f"{subset}.json"
        path = alt if alt.exists() else path
    if not path.exists():
        return None
    return json.loads(path.read_text())


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    r3_sel = RELEASE3_DATA / "refinement" / "records" / "selections"
    r2_sel = RELEASE2_DATA / "refinement" / "records" / "selections"
    rows = []
    for arm in PANEL_ARMS:
        for subset in ADMITTED:
            s3 = _load_sel(RELEASE3_DATA / "refinement", arm, subset)
            if s3 is None:
                continue
            s2 = None
            r2_arm = "gpt56_medium" if arm == "gpt56_medium" else arm
            p2 = r2_sel / r2_arm / f"{subset}.json"
            if p2.exists():
                s2 = json.loads(p2.read_text())
            rows.append(
                {
                    "arm": arm,
                    "subset": subset,
                    "r3_start": float(s3["start"]["gt_miou"]),
                    "r3_selected": float(s3["selected"]["gt_miou"]),
                    "r3_delta": float(s3["delta_gt_miou"] or 0.0),
                    "r2_selected": None if s2 is None else float(s2["selected"]["gt_miou"]),
                    "r2_delta": None if s2 is None else float(s2["delta_gt_miou"] or 0.0),
                }
            )
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "baseline_vs_release2.csv", index=False)
    lines = ["# Release 3 vs Release 2 baseline", ""]
    for arm, g in df.groupby("arm"):
        lines.append(f"## {arm}")
        lines.append(f"- N={len(g)}; start mean {g['r3_start'].mean():.3f}")
        lines.append(f"- R3 selected mean {g['r3_selected'].mean():.3f} (Δ {g['r3_delta'].mean():+.3f})")
        both = g.dropna(subset=["r2_selected"])
        if len(both):
            lines.append(
                f"- Overlap with R2 ({len(both)}): R3 {both['r3_selected'].mean():.3f} vs R2 {both['r2_selected'].mean():.3f}"
            )
        lines.append("")
    (OUT / "baseline_vs_release2.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
