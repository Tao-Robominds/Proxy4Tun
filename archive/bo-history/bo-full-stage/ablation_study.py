#!/usr/bin/env python3
"""Ablation study over the bo-full-stage extended feature set."""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "bo-elegant"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from features import CANDIDATE, COHERENCE, EVIDENCE  # noqa: E402
from train_proxy import fit_ridge, leave_one_family_out_cv  # noqa: E402

OUT = Path(__file__).resolve().parent / "ablation.json"
TRAIN_TABLE = Path(__file__).resolve().parent / "training_table.csv"
STAGE1_FEATURES = ("unfold_residual", "orient_agreement")


def main() -> None:
    df = pd.read_csv(TRAIN_TABLE)
    for k in CANDIDATE:
        df[k] = df[k].astype(float).fillna(0.0)

    variants: dict[str, list[str]] = {
        "Evidence": list(EVIDENCE),
        "Coherence": list(COHERENCE),
        "Evidence+Coherence": list(CANDIDATE),
        "no_stage1 (v2 features)": [f for f in CANDIDATE if f not in STAGE1_FEATURES],
        "stage1_only": list(STAGE1_FEATURES),
    }
    for drop in CANDIDATE:
        variants[f"loo_{drop}"] = [f for f in CANDIDATE if f != drop]

    rows = []
    for name, feats in variants.items():
        model = fit_ridge(df, feats)
        cv = leave_one_family_out_cv(df, feats)
        rows.append(
            {
                "set": name,
                "n_features": len(feats),
                "features": feats,
                "train_mae": model["train_mae"],
                "train_spearman": model["train_spearman"],
                **cv,
            }
        )
        print(
            f"{name:32s} mae={model['train_mae']:.4f} "
            f"sp={model['train_spearman']:.3f} lolo_mae={cv['lolo_mae']:.4f}"
        )

    OUT.write_text(
        json.dumps({"variants": rows, "created_at": datetime.now().isoformat()}, indent=2)
        + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
