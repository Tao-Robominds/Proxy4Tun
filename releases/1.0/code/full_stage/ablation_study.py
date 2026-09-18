#!/usr/bin/env python3
"""Ablation study over the bo-full-stage extended feature set."""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))
from bo.paths import FULL_STAGE_PKG
from bo.elegant.features import CANDIDATE, COHERENCE, EVIDENCE
from bo.full_stage.train_proxy import fit_ridge, leave_one_family_out_cv

OUT = FULL_STAGE_PKG / "ablation.json"
TRAIN_TABLE = FULL_STAGE_PKG / "training_table.csv"
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
