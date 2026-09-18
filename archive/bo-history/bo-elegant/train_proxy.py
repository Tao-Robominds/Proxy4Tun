#!/usr/bin/env python3
"""Train a unified lean Ridge proxy on the 3-anchor BO corpus.

Mini-ablation: Evidence / Coherence / Evidence+Coherence / leave-one-out.
Permutation control required before freeze.

Uses the local filled table ``family/training_table.csv`` when present
(40 trials × 3 anchors = 120 rows); otherwise slices the bo-unified archive.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.linear_model import RidgeCV
from sklearn.metrics import mean_absolute_error
from sklearn.preprocessing import StandardScaler

from features import DROPPED, TRAIN_ANCHORS

# v1 lean taxonomy (matches family/training_table.csv columns).
# features.py CANDIDATE is the v2 set and is intentionally not used here.
EVIDENCE: tuple[str, ...] = (
    "depth_nan_ratio",
    "denoise_retained_ratio",
    "det_real_detection_ratio",
)
COHERENCE: tuple[str, ...] = (
    "sam_fill_rate",
    "sam_ring_completeness",
    "sam_ontology_divergence",
)
CANDIDATE: tuple[str, ...] = EVIDENCE + COHERENCE

REPO_ROOT = Path(__file__).resolve().parent.parent
BO_DIR = Path(__file__).resolve().parent
TRAINING_CSV = REPO_ROOT / "bo-unified" / "family" / "training_table.csv"
OUT_DIR = BO_DIR / "family"
MODELS_PATH = OUT_DIR / "models.json"
ABLATION_PATH = OUT_DIR / "ablation.json"
TRAIN_TABLE_PATH = OUT_DIR / "training_table.csv"

COEF_PRUNE_FRAC = 0.10
PERM_REPEATS = 20
PERM_SEED = 0


def _safe_scale(scale: np.ndarray, eps: float = 1e-8) -> np.ndarray:
    out = np.asarray(scale, dtype=float).copy()
    out[~np.isfinite(out)] = 1.0
    out[np.abs(out) < eps] = 1.0
    return out


def load_train() -> pd.DataFrame:
    """Prefer filled local table (120 rows); else archived bo-unified slice."""
    need = list(CANDIDATE) + ["mIoU", "case", "family"]
    if TRAIN_TABLE_PATH.exists():
        local = pd.read_csv(TRAIN_TABLE_PATH)
        if set(TRAIN_ANCHORS).issubset(set(local["case"].unique())):
            sub = local[local["case"].isin(TRAIN_ANCHORS)].copy()
            if all(c in sub.columns for c in need):
                sub = sub.dropna(subset=list(CANDIDATE) + ["mIoU"]).reset_index(drop=True)
                if len(sub) >= 108:
                    print(f"load_train: {TRAIN_TABLE_PATH} n={len(sub)}")
                    return sub[need]
    df = pd.read_csv(TRAINING_CSV)
    sub = df[df["case"].isin(TRAIN_ANCHORS)].copy()
    sub = sub.dropna(subset=list(CANDIDATE) + ["mIoU"]).reset_index(drop=True)
    print(f"load_train: fallback {TRAINING_CSV} n={len(sub)}")
    return sub[need]


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


def leave_one_family_out_cv(df: pd.DataFrame, features: list[str]) -> dict[str, float]:
    """Leave-one-anchor-family-out CV on the 108 training rows."""
    maes, sps = [], []
    for fam in sorted(df["family"].unique()):
        train = df[df["family"] != fam]
        test = df[df["family"] == fam]
        if train.empty or test.empty:
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


def prune_tiny(model: dict[str, Any], frac: float = COEF_PRUNE_FRAC) -> list[str]:
    coefs = np.asarray(model["coef"], dtype=float)
    feats = list(model["features"])
    max_abs = float(np.max(np.abs(coefs))) if len(coefs) else 0.0
    if max_abs <= 0:
        return feats
    keep = [f for f, c in zip(feats, coefs) if abs(c) >= frac * max_abs]
    return keep if keep else feats


def permutation_control(
    df: pd.DataFrame, features: list[str], n: int = PERM_REPEATS, seed: int = PERM_SEED
) -> dict[str, Any]:
    rng = np.random.default_rng(seed)
    real = fit_ridge(df, features)
    real_mae = real["train_mae"]
    real_sp = real["train_spearman"]
    perm_maes, perm_sps = [], []
    for _ in range(n):
        shuffled = df.copy()
        # Within-family shuffle
        for fam in shuffled["family"].unique():
            idx = shuffled.index[shuffled["family"] == fam]
            vals = shuffled.loc[idx, "mIoU"].to_numpy().copy()
            rng.shuffle(vals)
            shuffled.loc[idx, "mIoU"] = vals
        m = fit_ridge(shuffled, features)
        perm_maes.append(m["train_mae"])
        perm_sps.append(m["train_spearman"])
    return {
        "real_mae": real_mae,
        "real_spearman": real_sp,
        "perm_mae_mean": float(np.mean(perm_maes)),
        "perm_mae_std": float(np.std(perm_maes)),
        "perm_spearman_mean": float(np.mean(perm_sps)),
        "perm_spearman_std": float(np.std(perm_sps)),
        "pass": real_mae < float(np.mean(perm_maes)) - float(np.std(perm_maes)),
        "n_repeats": n,
    }


def run_ablation(df: pd.DataFrame) -> dict[str, Any]:
    variants: dict[str, list[str]] = {
        "Evidence": list(EVIDENCE),
        "Coherence": list(COHERENCE),
        "Evidence+Coherence": list(CANDIDATE),
    }
    for drop in CANDIDATE:
        name = f"loo_{drop}"
        variants[name] = [f for f in CANDIDATE if f != drop]

    rows = []
    for name, feats in variants.items():
        model = fit_ridge(df, feats)
        cv = leave_one_family_out_cv(df, feats)
        coef_abs = {f: abs(c) for f, c in zip(model["features"], model["coef"])}
        rows.append(
            {
                "set": name,
                "n_features": len(feats),
                "features": feats,
                "train_mae": model["train_mae"],
                "train_spearman": model["train_spearman"],
                "train_pearson": model["train_pearson"],
                **cv,
                "coef_abs": coef_abs,
                "alpha": model["alpha"],
            }
        )
        print(
            f"{name:40s} n={len(feats)} mae={model['train_mae']:.3f} "
            f"sp={model['train_spearman']:.3f} "
            f"lolo_mae={cv['lolo_mae']:.3f} lolo_sp={cv['lolo_spearman']:.3f}"
        )
    return {"variants": rows, "dropped_upfront": DROPPED}


def _covers_both_blocks(feats: list[str]) -> bool:
    return any(f in EVIDENCE for f in feats) and any(f in COHERENCE for f in feats)


def select_lean(ablation: dict[str, Any], df: pd.DataFrame) -> tuple[list[str], dict[str, Any]]:
    """Pick leanest balanced set not meaningfully worse than full Evidence+Coherence.

    Criteria (training / LOLO): keep if train_spearman >= full - 0.03 and
    lolo_mae <= full + 0.02. Prefer sets that retain ≥1 Evidence and ≥1 Coherence
    feature (design intent); among those, fewer features then higher spearman.
    Then apply |coef| prune, but never drop the last feature of a block.
    """
    variants = {r["set"]: r for r in ablation["variants"]}
    full = variants["Evidence+Coherence"]
    full_sp = full["train_spearman"]
    full_lolo = full["lolo_mae"]

    candidates = []
    for r in ablation["variants"]:
        if r["train_spearman"] + 1e-9 < full_sp - 0.03:
            continue
        if r["lolo_mae"] - 1e-9 > full_lolo + 0.02:
            continue
        candidates.append(r)

    if not candidates:
        candidates = [full]

    both = [r for r in candidates if _covers_both_blocks(r["features"])]
    pool = both if both else candidates
    pool.sort(key=lambda r: (r["n_features"], -r["train_spearman"], r["train_mae"]))
    chosen = pool[0]
    feats = list(chosen["features"])
    model = fit_ridge(df, feats)
    pruned = prune_tiny(model)
    # Never drop the last Evidence / Coherence feature during tidy-up.
    for block in (EVIDENCE, COHERENCE):
        if any(f in feats for f in block) and not any(f in pruned for f in block):
            # restore the largest-|coef| member of that block
            coef_map = {f: abs(c) for f, c in zip(model["features"], model["coef"])}
            best = max((f for f in feats if f in block), key=lambda f: coef_map.get(f, 0.0))
            if best not in pruned:
                pruned.append(best)
                print(f"Coef prune: restored block survivor `{best}`")
    if set(pruned) != set(feats):
        print(f"Coef prune: {feats} -> {pruned}")
        model2 = fit_ridge(df, pruned)
        cv2 = leave_one_family_out_cv(df, pruned)
        if (
            model2["train_spearman"] >= full_sp - 0.03
            and cv2["lolo_mae"] <= full_lolo + 0.02
            and (not both or _covers_both_blocks(pruned))
        ):
            feats = pruned
            chosen = {
                **chosen,
                "set": chosen["set"] + "+pruned",
                "features": feats,
                "n_features": len(feats),
                "train_mae": model2["train_mae"],
                "train_spearman": model2["train_spearman"],
                "lolo_mae": cv2["lolo_mae"],
                "lolo_spearman": cv2["lolo_spearman"],
            }
        else:
            print("Prune rejected (metrics/blocks); keeping pre-prune set")
            feats = list(chosen["features"])

    return feats, chosen


def train_and_freeze() -> dict[str, Any]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df = load_train()
    # Do not overwrite the filled training_table.csv (keeps trial_id/source).
    print(f"Training rows: {len(df)} cases={sorted(df['case'].unique())}")

    ablation = run_ablation(df)
    feats, chosen = select_lean(ablation, df)
    print(f"Selected lean set ({chosen['set']}): {feats}")

    model = fit_ridge(df, feats)
    pred = predict(model, df)
    y = df["mIoU"].to_numpy()
    alarm = calibrate_alarm(y, pred)
    low_floor = float(np.quantile(y, 0.33))

    perm = permutation_control(df, feats)
    print(
        f"Permutation: real_mae={perm['real_mae']:.3f} vs "
        f"perm={perm['perm_mae_mean']:.3f}±{perm['perm_mae_std']:.3f} "
        f"pass={perm['pass']}"
    )
    if not perm["pass"]:
        raise RuntimeError(
            "Permutation control FAILED — lean set rejected. "
            f"real MAE {perm['real_mae']:.3f} not clearly below "
            f"shuffled {perm['perm_mae_mean']:.3f}±{perm['perm_mae_std']:.3f}"
        )

    # Full 6-feature model for side-by-side report
    full_model = fit_ridge(df, list(CANDIDATE))

    payload = {
        "created_at": datetime.now().isoformat(),
        "train_anchors": list(TRAIN_ANCHORS),
        "n_train_rows": int(len(df)),
        "candidate_features": {
            "Evidence": list(EVIDENCE),
            "Coherence": list(COHERENCE),
        },
        "dropped_upfront": DROPPED,
        "selected_set": chosen["set"],
        "features": feats,
        "model": model,
        "full_candidate_model": full_model,
        "alarm_threshold": alarm,
        "low_miou_floor": low_floor,
        "permutation": perm,
        "selection": {
            "train_mae": chosen["train_mae"],
            "train_spearman": chosen["train_spearman"],
            "lolo_mae": chosen["lolo_mae"],
            "lolo_spearman": chosen["lolo_spearman"],
        },
        "provenance": (
            "bo-elegant/family/training_table.csv — 40 ok trials × anchors "
            "2-1/3-1/5-1 (archived bo-unified rows + bo-elegant-fill tops-ups)"
        ),
    }
    MODELS_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    ABLATION_PATH.write_text(json.dumps(ablation, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {MODELS_PATH}")
    print(f"Wrote {ABLATION_PATH}")
    print(
        f"Frozen proxy: n_feat={len(feats)} train_mae={model['train_mae']:.3f} "
        f"sp={model['train_spearman']:.3f} alarm={alarm:.3f} floor={low_floor:.3f}"
    )
    for f, c in sorted(zip(feats, model["coef"]), key=lambda t: -abs(t[1])):
        print(f"  {f:28s} {c:+.4f}")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--train", action="store_true", help="Run ablation + freeze proxy")
    args = parser.parse_args()
    if args.train or True:
        train_and_freeze()


if __name__ == "__main__":
    main()
