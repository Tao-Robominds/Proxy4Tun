#!/usr/bin/env python3
"""Ingest historical data/bo BO campaigns into bo-unified training artifacts.

Does not re-run pipelines. Writes:
  bo-unified/family/training_table.csv
  bo-unified/family/bad_configs.json
  bo-unified/family/ingest_manifest.json
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

import sys

REPO_ROOT = Path(__file__).resolve().parent.parent
BO_DIR = Path(__file__).resolve().parent
FAMILY_DIR = BO_DIR / "family"
sys.path.insert(0, str(BO_DIR))

from intrinsics import TIER1_KEYS  # noqa: E402
from spaces import CASE_CONFIG, FAMILY_TRAIN_CASES  # noqa: E402

TRAINING_CSV = FAMILY_DIR / "training_table.csv"
BAD_CONFIGS_PATH = FAMILY_DIR / "bad_configs.json"
INGEST_MANIFEST = FAMILY_DIR / "ingest_manifest.json"


def load_campaign_rows(case: str) -> list[dict[str, Any]]:
    root = REPO_ROOT / "data" / "bo" / f"{case}-bo-proxy"
    man_path = root / "manifest.json"
    if not man_path.exists():
        raise FileNotFoundError(f"Missing campaign for {case}: {man_path}")
    man = json.loads(man_path.read_text(encoding="utf-8"))
    rows = []
    for t in man.get("trials", []):
        if t.get("status") != "ok" or t.get("mIoU") is None:
            continue
        acq = str(t.get("acquisition") or "")
        if acq.startswith("repeat_"):
            continue
        row: dict[str, Any] = {
            "case": case,
            "family": CASE_CONFIG[case]["family"],
            "trial_id": t["trial_id"],
            "acquisition": acq,
            "mIoU": float(t["mIoU"]),
            "source_root": str(root),
            "output_dir": t.get("output_dir"),
        }
        metrics = t.get("metrics") or {}
        for k in TIER1_KEYS:
            row[k] = metrics.get(k)
        row["orient_invariant_ok"] = metrics.get("orient_invariant_ok")
        row["orient_h_ring_corr"] = metrics.get("orient_h_ring_corr")
        row["overlay_json"] = json.dumps(t.get("overlay") or {})
        rows.append(row)
    return rows


def ingest_training_table() -> pd.DataFrame:
    FAMILY_DIR.mkdir(parents=True, exist_ok=True)
    frames = []
    counts: dict[str, int] = {}
    for family, cases in FAMILY_TRAIN_CASES.items():
        for case in cases:
            rows = load_campaign_rows(case)
            counts[case] = len(rows)
            frames.append(pd.DataFrame(rows))
            print(f"Ingested {case}: {len(rows)} ok trials from data/bo/{case}-bo-proxy")
    df = pd.concat(frames, ignore_index=True)
    df.to_csv(TRAINING_CSV, index=False)
    meta = {
        "created_at": datetime.now().isoformat(),
        "source": "data/bo/<case>-bo-proxy/manifest.json",
        "justification": (
            "Unified pipeline passed parity gates vs the anchors these trials ran on "
            "(|ΔmIoU| ≤ 0.02 per anchors/unified/verification.md), so (features → mIoU) "
            "pairs remain valid proxy training data."
        ),
        "n_rows": int(len(df)),
        "counts_per_case": counts,
        "training_csv": str(TRAINING_CSV),
    }
    INGEST_MANIFEST.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {TRAINING_CSV} ({len(df)} rows)")
    print(f"Wrote {INGEST_MANIFEST}")
    return df


def select_bad_configs() -> dict[str, Any]:
    """Pick lowest-mIoU completed trial per family from historical BO archives."""
    FAMILY_DIR.mkdir(parents=True, exist_ok=True)
    out: dict[str, Any] = {}
    for family, cases in FAMILY_TRAIN_CASES.items():
        best: dict[str, Any] | None = None
        for case in cases:
            man_path = REPO_ROOT / "data" / "bo" / f"{case}-bo-proxy" / "manifest.json"
            man = json.loads(man_path.read_text(encoding="utf-8"))
            for t in man.get("trials", []):
                if t.get("status") != "ok" or t.get("mIoU") is None:
                    continue
                acq = str(t.get("acquisition") or "")
                if acq.startswith("repeat_"):
                    continue
                metrics = t.get("metrics") or {}
                if not metrics:
                    continue
                miou = float(t["mIoU"])
                cand = {
                    "family": family,
                    "source_case": case,
                    "trial_id": t["trial_id"],
                    "acquisition": acq,
                    "training_mIoU": miou,
                    "overlay": t.get("overlay") or {},
                    "output_dir": t.get("output_dir"),
                    "source": "data/bo historical campaign",
                }
                if best is None or miou < best["training_mIoU"]:
                    best = cand
        if best is None:
            raise RuntimeError(f"No candidate bad trial for family {family}")
        anchors = [CASE_CONFIG[c]["anchor_miou"] for c in cases]
        best["sibling_anchor_mious"] = anchors
        best["delta_vs_min_anchor"] = float(min(anchors) - best["training_mIoU"])
        out[family] = best
        print(
            f"{family}: bad={best['trial_id']} mIoU={best['training_mIoU']:.3f} "
            f"(Δ vs min-anchor={best['delta_vs_min_anchor']:.3f})"
        )
    BAD_CONFIGS_PATH.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {BAD_CONFIGS_PATH}")
    return out


def main() -> None:
    p = argparse.ArgumentParser(description="Ingest data/bo campaigns for bo-unified")
    p.add_argument("--table", action="store_true", help="Write training_table.csv")
    p.add_argument("--select-bad", action="store_true", help="Freeze known-bad overlays")
    p.add_argument("--all", action="store_true")
    args = p.parse_args()
    if args.all or (not args.table and not args.select_bad):
        ingest_training_table()
        select_bad_configs()
        return
    if args.table:
        ingest_training_table()
    if args.select_bad:
        select_bad_configs()


if __name__ == "__main__":
    main()
