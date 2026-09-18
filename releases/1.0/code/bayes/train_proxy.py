#!/usr/bin/env python3
"""Fit frozen lean five-feature Ridge proxy on bo-bayes/training_table.csv.

Lean feature set is frozen to the published set (no re-pruning) to minimise
paper structural rewrite. Alarm threshold for evaluation is fixed at 0.5.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.linear_model import RidgeCV
from sklearn.metrics import mean_absolute_error
from sklearn.preprocessing import StandardScaler

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))
from bo.paths import BAYES_PKG
from bo.elegant.features import CANDIDATE, COHERENCE, EVIDENCE  # noqa: E402

OUT_DIR = BAYES_PKG
TRAIN_TABLE = OUT_DIR / "training_table.csv"
MODELS = OUT_DIR / "models.json"
ABLATION = OUT_DIR / "ablation.json"

# Frozen published lean set (paper Eq. lean-proxy).
LEAN_FEATURES = [
    "depth_nan_ratio",
    "denoise_retained_ratio",
    "sam_fill_rate",
    "det_row_residual_px",
    "det_row_gated",
]
ALARM_THRESHOLD = 0.5
PERM_REPEATS = 20
PERM_SEED = 0


def _safe_scale(scale: np.ndarray, eps: float = 1e-8) -> np.ndarray:
    out = np.asarray(scale, dtype=float).copy()
    out[~np.isfinite(out)] = 1.0
    out[np.abs(out) < eps] = 1.0
    return out


def fit_ridge(df: pd.DataFrame, features: list[str]) -> dict[str, Any]:
    X = df[features].astype(float).to_numpy()
    y = df["mIoU"].astype(float).to_numpy()
    scaler = StandardScaler()
    scaler.fit(X)
    mean = np.asarray(scaler.mean_, dtype=float)
    scale = _safe_scale(scaler.scale_)
    Xs = (X - mean) / scale
    model = RidgeCV(alphas=np.logspace(-3, 3, 25))
    model.fit(Xs, y)
    pred = model.predict(Xs)
    return {
        "scaler_mean": mean.tolist(),
        "scaler_scale": scale.tolist(),
        "coef": model.coef_.tolist(),
        "intercept": float(model.intercept_),
        "alpha": float(model.alpha_),
        "features": list(features),
        "n_train": int(len(df)),
        "train_mae": float(mean_absolute_error(y, pred)),
        "train_spearman": float(stats.spearmanr(y, pred).correlation or 0.0),
        "train_pearson": float(stats.pearsonr(y, pred).statistic),
    }


def predict(model: dict[str, Any], df: pd.DataFrame) -> np.ndarray:
    feats = model["features"]
    X = df[feats].astype(float).to_numpy()
    mean = np.asarray(model["scaler_mean"], dtype=float)
    scale = _safe_scale(np.asarray(model["scaler_scale"], dtype=float))
    Xs = (X - mean) / scale
    return Xs @ np.asarray(model["coef"], dtype=float) + float(model["intercept"])


def leave_one_family_out_cv(df: pd.DataFrame, features: list[str]) -> dict[str, float]:
    maes, sps = [], []
    for fam in sorted(df["family"].unique()):
        train = df[df["family"] != fam]
        test = df[df["family"] == fam]
        if len(train) < 5 or len(test) < 2:
            continue
        model = fit_ridge(train, features)
        pred = predict(model, test)
        y = test["mIoU"].to_numpy()
        maes.append(float(mean_absolute_error(y, pred)))
        sp = stats.spearmanr(y, pred).correlation
        sps.append(float(sp if sp is not None and np.isfinite(sp) else 0.0))
    return {
        "lolo_mae": float(np.mean(maes)) if maes else float("nan"),
        "lolo_spearman": float(np.mean(sps)) if sps else float("nan"),
    }


def permutation_control(df: pd.DataFrame, features: list[str]) -> dict[str, Any]:
    rng = np.random.default_rng(PERM_SEED)
    real = fit_ridge(df, features)
    perm_maes, perm_sps = [], []
    for _ in range(PERM_REPEATS):
        shuffled = df.copy()
        for fam in shuffled["family"].unique():
            idx = shuffled.index[shuffled["family"] == fam]
            vals = shuffled.loc[idx, "mIoU"].to_numpy().copy()
            rng.shuffle(vals)
            shuffled.loc[idx, "mIoU"] = vals
        m = fit_ridge(shuffled, features)
        perm_maes.append(m["train_mae"])
        perm_sps.append(m["train_spearman"])
    return {
        "real_mae": real["train_mae"],
        "real_spearman": real["train_spearman"],
        "perm_mae_mean": float(np.mean(perm_maes)),
        "perm_mae_std": float(np.std(perm_maes)),
        "perm_spearman_mean": float(np.mean(perm_sps)),
        "perm_spearman_std": float(np.std(perm_sps)),
        "pass": real["train_mae"] < float(np.mean(perm_maes)) - float(np.std(perm_maes)),
        "n_repeats": PERM_REPEATS,
    }


def run_ablation(df: pd.DataFrame) -> dict[str, Any]:
    variants: dict[str, list[str]] = {
        "Evidence": list(EVIDENCE),
        "Coherence": list(COHERENCE),
        "Evidence+Coherence": list(CANDIDATE),
        "Lean": list(LEAN_FEATURES),
    }
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
    return {"variants": rows, "created_at": datetime.now().isoformat()}


def main() -> None:
    if not TRAIN_TABLE.exists():
        raise SystemExit(f"Missing {TRAIN_TABLE}")
    df = pd.read_csv(TRAIN_TABLE)
    for k in CANDIDATE:
        df[k] = df[k].astype(float).fillna(0.0)

    lean = fit_ridge(df, LEAN_FEATURES)
    full = fit_ridge(df, list(CANDIDATE))
    perm = permutation_control(df, LEAN_FEATURES)
    cv = leave_one_family_out_cv(df, LEAN_FEATURES)
    abl = run_ablation(df)

    fam_mae = {}
    for fam in sorted(df["family"].unique()):
        sub = df[df["family"] == fam]
        fam_mae[fam] = float(mean_absolute_error(sub["mIoU"], predict(lean, sub)))

    # Per-family models (same lean features)
    per_family = {}
    for fam in sorted(df["family"].unique()):
        sub = df[df["family"] == fam]
        per_family[fam] = fit_ridge(sub, LEAN_FEATURES)

    payload = {
        "created_at": datetime.now().isoformat(),
        "n_train": int(len(df)),
        "n_per_case": df.groupby("case").size().to_dict(),
        "candidate_features": list(CANDIDATE),
        "lean_features": list(LEAN_FEATURES),
        "model": lean,
        "full_model": full,
        "per_family_models": per_family,
        "alarm_threshold": ALARM_THRESHOLD,
        "permutation": perm,
        "lolo_cv": cv,
        "family_mae": fam_mae,
        "formula_terms": [
            {"feature": f, "coef_z": float(c)}
            for f, c in zip(lean["features"], lean["coef"])
        ],
        "intercept": lean["intercept"],
    }
    MODELS.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    ABLATION.write_text(json.dumps(abl, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {MODELS}")
    print(f"lean features: {LEAN_FEATURES}")
    print(f"train MAE={lean['train_mae']:.4f} spearman={lean['train_spearman']:.3f}")
    print(f"LOLO MAE={cv['lolo_mae']:.4f} spearman={cv['lolo_spearman']:.3f}")
    print(f"family MAE: {fam_mae}")
    print(f"perm pass={perm['pass']} alarm={ALARM_THRESHOLD}")


if __name__ == "__main__":
    main()
