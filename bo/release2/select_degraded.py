#!/usr/bin/env python3
"""Freeze one stage 2-5 degradation overlay per family.

For each family, take the valid development trial with the lowest GT mIoU
and keep only the stage 2-5 parameter keys that differ from the family
reference. Unfolding keys are dropped so both members of a pair share the
stage-1 frame.

The written file is not replaced on a later run. Selection is frozen before
any evaluation-subset run.

Usage:
  ./venv/bin/python bo/release2/select_degraded.py
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from bo.paths import REFERENCES_DIR, RELEASE2_DATA  # noqa: E402
from bo.runtime.metadata import family_of  # noqa: E402
from bo.runtime.param_io import get_nested, load_anchor_params  # noqa: E402

TABLE = RELEASE2_DATA / "calibration" / "records" / "training_table.csv"
OUT = RELEASE2_DATA / "degradation" / "records" / "overlay_selection.json"
LATER_STAGES = ("denoising", "enhancing", "detecting", "sam")
FAMILIES = ("staggered", "continuous", "complex")


def _differs(left, right) -> bool:
    if isinstance(left, bool) or isinstance(right, bool):
        return bool(left) != bool(right)
    if isinstance(left, list) and isinstance(right, list):
        return len(left) != len(right) or any(_differs(a, b) for a, b in zip(left, right))
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return not math.isclose(float(left), float(right), rel_tol=0.0, abs_tol=1e-8)
    return left != right


def stage2to5_diff(overlay: dict, base: dict) -> dict:
    kept: dict[str, dict] = {}
    for stage in LATER_STAGES:
        stage_overlay = overlay.get(stage) or {}
        stage_base = base.get(stage) or {}
        changed = {}
        for key, value in stage_overlay.items():
            try:
                current = get_nested(stage_base, key)
            except (KeyError, TypeError):
                current = None
            if _differs(value, current):
                changed[key] = value
        if changed:
            kept[stage] = changed
    return kept


def _load_table():
    import pandas as pd

    if not TABLE.exists():
        raise SystemExit(f"missing {TABLE}")
    df = pd.read_csv(TABLE)
    if df["family"].nunique() != 3 or len(df) != 120:
        raise SystemExit(f"expected 120 rows across 3 families, found {len(df)}")
    return df


def select(df) -> list[dict]:
    chosen = []
    for family in FAMILIES:
        part = df[df["family"] == family].sort_values(["gt_miou", "trial_id"])
        if part.empty:
            raise SystemExit(f"no training rows for {family}")
        row = part.iloc[0]
        dev = str(row["dev"])
        trial_id = str(row["trial_id"])
        if family_of(dev) != family:
            raise SystemExit(f"{dev} is not family {family}")
        record_path = RELEASE2_DATA / "calibration" / dev / "runs" / trial_id / "record.json"
        record = json.loads(record_path.read_text(encoding="utf-8"))
        base = load_anchor_params(REFERENCES_DIR / family)
        overlay = stage2to5_diff(record.get("overlay") or {}, base)
        chosen.append(
            {
                "family": family,
                "dev": dev,
                "source_trial": trial_id,
                "source_gt_miou": float(row["gt_miou"]),
                "source_record": str(record_path),
                "overlay": overlay,
            }
        )
    return chosen


def _markdown(chosen: list[dict]) -> str:
    lines = [
        "# Degradation overlays",
        "",
        "Lowest-GT-mIoU valid development trial per family. Unfolding keys dropped.",
        "",
        "| family | source | GT mIoU | stage 2-5 keys |",
        "| --- | --- | ---: | --- |",
    ]
    for item in chosen:
        keys = [f"{stage}.{key}" for stage, vals in item["overlay"].items() for key in vals]
        lines.append(
            f"| {item['family']} | {item['dev']}/{item['source_trial']} | "
            f"{item['source_gt_miou']:.4f} | {', '.join(keys) or '(none)'} |"
        )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    if OUT.exists():
        print(f"already frozen: {OUT}")
        return 0
    chosen = select(_load_table())
    OUT.parent.mkdir(parents=True, exist_ok=True)
    payload = {"frozen": True, "families": chosen}
    OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    (OUT.parent / "overlay_selection.md").write_text(_markdown(chosen), encoding="utf-8")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
