#!/usr/bin/env python3
"""Freeze the Plan-4 worked-example bank from development records only.

Sources (never evaluation subsets):
  - data/release2/calibration/{2-1,3-1,5-1}/runs/*/record.json
  - data/release2/references/{2-1,3-1,5-1}/record.json (family baselines)
  - data/release2/degradation/records/overlay_selection.json (worst degradations)

For each family and each of the four proxy features, keep the largest improver
and largest degrader relative to the family reference. Joint multi-parameter
changes are described as one outcome without per-parameter causal claims.

Usage:
  ./venv/bin/python bo/release2/build_example_bank.py
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
from datetime import datetime
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from bo.paths import REFERENCES_DIR, RELEASE2_DATA, REPO_ROOT  # noqa: E402
from bo.runtime.metadata import expected_rings, family_of  # noqa: E402
from bo.release2.score import score_measurements  # noqa: E402

OUT = REPO_ROOT / "configs" / "example_bank.json"
DEV = ("2-1", "3-1", "5-1")
FOUR = (
    "correspondence_f1@15",
    "sam_fill_rate",
    "ring_count_error",
    "depth_nan_ratio",
)
HIGHER_BETTER = {"correspondence_f1@15", "sam_fill_rate"}
FAMILY_OF_DEV = {"2-1": "staggered", "3-1": "continuous", "5-1": "complex"}


def _delta(feat: str, before: float, after: float) -> float:
    if feat in HIGHER_BETTER:
        return after - before
    return before - after  # positive = improvement for lower-better


def _response_text(before: dict, after: dict, before_score: float, after_score: float) -> str:
    parts = [
        f"proxy {before_score:.3f}→{after_score:.3f}",
    ]
    for k in FOUR:
        parts.append(f"{k} {before.get(k):.4g}→{after.get(k):.4g}")
    return "; ".join(parts) + ". Joint outcome of the full overlay; no per-parameter causal attribution."


def _problem_text(before: dict, feat: str) -> str:
    cues = []
    for k in FOUR:
        cues.append(f"{k}={before.get(k):.4g}")
    return f"Dominant concern {feat}; measurements: " + ", ".join(cues)


def main() -> int:
    if OUT.exists():
        print(f"already frozen: {OUT}")
        return 0

    examples: list[dict] = []
    for dev in DEV:
        family = FAMILY_OF_DEV[dev]
        ref = json.loads(
            (RELEASE2_DATA / "references" / dev / "record.json").read_text(encoding="utf-8")
        )
        ref_m = ref["measurements"]
        ref_score = float(ref["score"]) if ref.get("score") is not None else float(
            score_measurements(ref_m)["score"]
        )
        trials = []
        runs = RELEASE2_DATA / "calibration" / dev / "runs"
        for rec_path in sorted(runs.glob("*/record.json")):
            rec = json.loads(rec_path.read_text(encoding="utf-8"))
            if not rec.get("valid"):
                continue
            m = rec["measurements"]
            scored = score_measurements(m)
            trials.append(
                {
                    "id": f"{dev}/{rec['trial_id']}",
                    "trial_id": rec["trial_id"],
                    "overlay": rec.get("overlay") or {},
                    "measurements": m,
                    "score": float(scored["score"]),
                    "gt_miou": rec.get("gt_miou"),  # never written into bank text
                }
            )

        # Also include the Plan-3 degradation overlay selection as a degrader.
        sel = json.loads(
            (RELEASE2_DATA / "degradation" / "records" / "overlay_selection.json").read_text(
                encoding="utf-8"
            )
        )
        for item in sel["families"]:
            if item["family"] != family:
                continue
            # Re-score is not available without a run; use source trial from calibration.
            src = next((t for t in trials if t["trial_id"] == item["source_trial"]), None)
            if src is None:
                break

        by_feat: dict[str, dict] = {}
        for feat in FOUR:
            best = None
            worst = None
            best_d = -1e9
            worst_d = 1e9
            for t in trials:
                d = _delta(feat, float(ref_m[feat]), float(t["measurements"][feat]))
                if d > best_d:
                    best_d, best = d, t
                if d < worst_d:
                    worst_d, worst = d, t
            by_feat[feat] = {"improve": best, "degrade": worst, "improve_d": best_d, "degrade_d": worst_d}

        for feat in FOUR:
            for direction in ("improve", "degrade"):
                t = by_feat[feat][direction]
                if t is None:
                    continue
                eid = f"{family}-{feat.replace('@', 'at').replace('_', '')}-{direction}-{t['trial_id']}"
                # Deduplicate by trial within family.
                if any(e["source_trial"] == t["trial_id"] and e["family"] == family for e in examples):
                    # Still allow if different direction tags needed; skip exact id dupes.
                    if any(e["id"] == eid for e in examples):
                        continue
                unlocked = float(ref_m.get("unfold_residual") or 0) > 0 and math.expm1(
                    float(ref_m.get("unfold_residual") or 0)
                ) > 10
                examples.append(
                    {
                        "id": eid,
                        "family": family,
                        "dev": dev,
                        "source_trial": t["trial_id"],
                        "dominant_feature": feat,
                        "direction": direction,
                        "condition": (
                            f"family={family}, development subset {dev}, "
                            f"expected_rings={expected_rings(dev)}, "
                            f"reference proxy={ref_score:.3f}"
                        ),
                        "problem": _problem_text(ref_m, feat),
                        "overlay": t["overlay"],
                        "before": {
                            "measurements": {k: ref_m[k] for k in FOUR},
                            "score": ref_score,
                        },
                        "after": {
                            "measurements": {k: t["measurements"][k] for k in FOUR},
                            "score": t["score"],
                        },
                        "response": _response_text(
                            {k: ref_m[k] for k in FOUR},
                            {k: t["measurements"][k] for k in FOUR},
                            ref_score,
                            t["score"],
                        ),
                        "limits": (
                            f"Applies to {family} within configs/bounds/{family}.json; "
                            f"stage-1 {'unlocked' if unlocked else 'locked'} on this reference; "
                            "development scan only — not an evaluation subset."
                        ),
                    }
                )

    # Cap ~8 per family: prefer unique trials covering all features.
    trimmed: list[dict] = []
    for family in ("staggered", "continuous", "complex"):
        fam = [e for e in examples if e["family"] == family]
        # Prefer one improve+degrade per feature, then stop at 8.
        seen_trials = set()
        chosen = []
        for feat in FOUR:
            for direction in ("improve", "degrade"):
                for e in fam:
                    if e["dominant_feature"] == feat and e["direction"] == direction:
                        if e["source_trial"] not in seen_trials:
                            chosen.append(e)
                            seen_trials.add(e["source_trial"])
                        break
            if len(chosen) >= 8:
                break
        trimmed.extend(chosen[:8])

    payload = {
        "frozen": True,
        "n_examples": len(trimmed),
        "features": list(FOUR),
        "sources": [
            "data/release2/calibration/{2-1,3-1,5-1}",
            "data/release2/references/{2-1,3-1,5-1}",
        ],
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "examples": trimmed,
    }
    text = json.dumps(payload, indent=2) + "\n"
    payload["sha256"] = hashlib.sha256(text.encode()).hexdigest()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {OUT} n={len(trimmed)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
