#!/usr/bin/env python3
"""Train unified lean proxy on bo-full-stage training_table.csv."""

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
from bo.runtime.features import CANDIDATE, COHERENCE, EVIDENCE

OUT_DIR = Path(__file__).resolve().parent
TRAIN_TABLE = OUT_DIR / "training_table.csv"
MODELS = OUT_DIR / "models.json"
ABLATION = OUT_DIR / "ablation.json"

COEF_PRUNE_FRAC = 0.10
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


def prune_tiny(model: dict[str, Any], frac: float = COEF_PRUNE_FRAC) -> list[str]:
    coefs = np.asarray(model["coef"], dtype=float)
    feats = list(model["features"])
    max_abs = float(np.max(np.abs(coefs))) if len(coefs) else 0.0
    if max_abs <= 0:
        return feats
    keep = [f for f, c in zip(feats, coefs) if abs(c) >= frac * max_abs]
    # Ensure ≥1 Evidence and ≥1 Coherence survive
    ev = [f for f in keep if f in EVIDENCE]
    co = [f for f in keep if f in COHERENCE]
    if not ev:
        # restore largest Evidence coef
        ev_cands = [(abs(c), f) for f, c in zip(feats, coefs) if f in EVIDENCE]
        if ev_cands:
            keep.append(max(ev_cands)[1])
    if not co:
        co_cands = [(abs(c), f) for f, c in zip(feats, coefs) if f in COHERENCE]
        if co_cands:
            keep.append(max(co_cands)[1])
    return keep if keep else feats


def select_lean(df: pd.DataFrame) -> tuple[list[str], dict[str, Any]]:
    full = fit_ridge(df, list(CANDIDATE))
    kept = prune_tiny(full)
    # Refit on pruned
    lean = fit_ridge(df, kept)
    return kept, {"full": full, "lean": lean, "pruned_features": kept}


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


def calibrate_alarm(y: np.ndarray, pred: np.ndarray, low_q: float = 0.33) -> float:
    thr_true = float(np.quantile(y, low_q))
    labels = y <= thr_true
    best_t, best_f1 = float(np.median(pred)), -1.0
    for t in np.quantile(pred, np.linspace(0.05, 0.95, 19)):
        alarm = pred <= t
        tp = float(np.sum(alarm & labels))
        fp = float(np.sum(alarm & ~labels))
        fn = float(np.sum(~alarm & labels))
        prec = tp / (tp + fp) if (tp + fp) else 0.0
        rec = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = 2 * prec * rec / (prec + rec) if (prec + rec) else 0.0
        if f1 > best_f1:
            best_f1, best_t = f1, float(t)
    return best_t


def run_ablation(df: pd.DataFrame) -> dict[str, Any]:
    variants: dict[str, list[str]] = {
        "Evidence": list(EVIDENCE),
        "Coherence": list(COHERENCE),
        "Evidence+Coherence": list(CANDIDATE),
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
    return {"variants": rows, "created_at": datetime.now().isoformat()}


def main() -> None:
    if not TRAIN_TABLE.exists():
        raise SystemExit(f"Missing {TRAIN_TABLE}; run merge_training_table.py first")
    df = pd.read_csv(TRAIN_TABLE)
    for k in CANDIDATE:
        if k not in df.columns:
            raise SystemExit(f"Missing feature column {k}")
        df[k] = df[k].astype(float).fillna(0.0)

    kept, pack = select_lean(df)
    lean = pack["lean"]
    pred = predict(lean, df)
    alarm = calibrate_alarm(df["mIoU"].to_numpy(), pred)
    perm = permutation_control(df, kept)
    cv = leave_one_family_out_cv(df, kept)
    abl = run_ablation(df)

    # Per-family MAE
    fam_mae = {}
    for fam in sorted(df["family"].unique()):
        sub = df[df["family"] == fam]
        fam_mae[fam] = float(mean_absolute_error(sub["mIoU"], predict(lean, sub)))

    formula_terms = []
    for f, c in zip(lean["features"], lean["coef"]):
        formula_terms.append({"feature": f, "coef_z": float(c)})

    payload = {
        "created_at": datetime.now().isoformat(),
        "n_train": int(len(df)),
        "n_per_case": df.groupby("case").size().to_dict(),
        "stage1_varied_counts": df.groupby("case")["stage1_varied"].sum().astype(int).to_dict()
        if "stage1_varied" in df.columns
        else {},
        "candidate_features": list(CANDIDATE),
        "lean_features": kept,
        "model": lean,
        "full_model": pack["full"],
        "alarm_threshold": alarm,
        "permutation": perm,
        "lolo_cv": cv,
        "family_mae": fam_mae,
        "formula_terms": formula_terms,
        "intercept": lean["intercept"],
    }
    MODELS.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    ABLATION.write_text(json.dumps(abl, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {MODELS}")
    print(f"lean features: {kept}")
    print(f"train MAE={lean['train_mae']:.4f} spearman={lean['train_spearman']:.3f}")
    print(f"family MAE: {fam_mae}")
    print(f"perm pass={perm['pass']} alarm={alarm:.3f}")


if __name__ == "__main__":
    main()
