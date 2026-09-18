#!/usr/bin/env python3
"""Sensitivity: mean-impute complex K-row features (standardised zero when N/A)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.metrics import mean_absolute_error

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))
from bo.paths import BAYES_PKG
from bo.bayes.train_proxy import LEAN_FEATURES, fit_ridge, leave_one_family_out_cv, predict

OUT = BAYES_PKG
TRAIN = OUT / "training_table.csv"
HOLDOUT = OUT / "holdout_scores.csv"
MODELS = OUT / "models.json"
REPORT = OUT / "sensitivity_complex_krow.json"

KROW = ["det_row_residual_px", "det_row_gated"]


def mean_impute_complex(df: pd.DataFrame, means: dict[str, float]) -> pd.DataFrame:
    out = df.copy()
    mask = out["family"] == "complex"
    for f in KROW:
        out.loc[mask, f] = float(means[f])
    return out


def main() -> None:
    train = pd.read_csv(TRAIN)
    hs = pd.read_csv(HOLDOUT)
    hs = hs[hs["status"] == "ok"].copy()
    # Training means from non-complex rows only (applicable regime).
    means = {f: float(train.loc[train["family"] != "complex", f].mean()) for f in KROW}
    train_imp = mean_impute_complex(train, means)
    lean = fit_ridge(train_imp, LEAN_FEATURES)
    lolo = leave_one_family_out_cv(train_imp, LEAN_FEATURES)
    # Also LOFO on original (frozen) for comparison
    lolo_orig = leave_one_family_out_cv(train, LEAN_FEATURES)
    # Holdout: impute complex K-row with same training means, score with refit model
    hs_imp = mean_impute_complex(hs, means)
    pred = predict(lean, hs_imp)
    # Drop-KROW lean (3 features) on original data
    lean3 = [f for f in LEAN_FEATURES if f not in KROW]
    m3 = fit_ridge(train, lean3)
    lolo3 = leave_one_family_out_cv(train, lean3)
    pred3 = predict(m3, hs)
    out = {
        "imputation_means_from_noncomplex": means,
        "frozen_lolo": lolo_orig,
        "mean_imputed_refit": {
            "train_mae": lean["train_mae"],
            "train_spearman": lean["train_spearman"],
            "lolo": lolo,
            "holdout_mae": float(mean_absolute_error(hs["mIoU"], pred)),
            "holdout_spearman": float(stats.spearmanr(hs["mIoU"], pred).correlation or 0.0),
            "coef": dict(zip(LEAN_FEATURES, lean["coef"])),
            "intercept": lean["intercept"],
        },
        "drop_krow_3feat": {
            "features": lean3,
            "train_mae": m3["train_mae"],
            "train_spearman": m3["train_spearman"],
            "lolo": lolo3,
            "holdout_mae": float(mean_absolute_error(hs["mIoU"], pred3)),
            "holdout_spearman": float(stats.spearmanr(hs["mIoU"], pred3).correlation or 0.0),
        },
        "note": (
            "Frozen deployment model unchanged. Mean-imputation sets standardised "
            "K-row features to 0 for complex runs; drop-krow removes both features."
        ),
    }
    # Frozen holdout for reference
    models = json.loads(MODELS.read_text())
    from bo.bayes.train_proxy import predict as pred_fn

    pred_f = pred_fn(models["model"], hs)
    out["frozen_holdout"] = {
        "mae": float(mean_absolute_error(hs["mIoU"], pred_f)),
        "spearman": float(stats.spearmanr(hs["mIoU"], pred_f).correlation or 0.0),
    }
    REPORT.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
