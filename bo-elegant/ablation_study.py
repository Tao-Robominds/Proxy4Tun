#!/usr/bin/env python3
"""Consolidated holdout ablation for bo-elegant (zero new pipeline runs).

Variants:
  A. Regime-swap — v1 features vs v2 lean (controlled + frozen)
  B. Unified vs per-family vs pooled+one-hot
  C. Block ablation — Evidence / Coherence / both
  D. Leanness — lean-5 / v2-candidate-8 / Tier1+gate-17
  + leave-one-out on lean-5, permutation controls, alarm sensitivity
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.metrics import mean_absolute_error

REPO_ROOT = Path(__file__).resolve().parent.parent
BO_DIR = Path(__file__).resolve().parent
OUT_DIR = BO_DIR / "family"
sys.path.insert(0, str(REPO_ROOT / "bo-unified"))

from intrinsics import TIER1_KEYS, extract_intrinsics  # noqa: E402

from features import (  # noqa: E402
    ANCHOR_PARAMS,
    CANDIDATE,
    COHERENCE,
    EVIDENCE,
    TRAIN_ANCHORS,
    compute_phase_feature,
    compute_row_features,
    extract_lean,
)
from train_proxy_v2 import (  # noqa: E402
    calibrate_alarm,
    fit_ridge,
    permutation_control,
    predict,
)

TRAIN_CSV = OUT_DIR / "training_table_v2.csv"
HOLDOUT_CSV = OUT_DIR / "holdout_scores_v2.csv"
REGISTRY = BO_DIR / "registry.json"
MODELS_V1 = OUT_DIR / "models.json"
MODELS_V2 = OUT_DIR / "models_v2.json"
DATA_ROOT = REPO_ROOT / "data" / "bo-elegant"

ABLATION_CSV = OUT_DIR / "ablation_study.csv"
ABLATION_JSON = OUT_DIR / "ablation_study.json"
REPORT = BO_DIR / "report.md"
HARNESS_GATE = BO_DIR / "ablation_harness_gate.md"

# 14 classic Tier-1 + 3 gate-regime features = 17
FULL_17: tuple[str, ...] = tuple(TIER1_KEYS) + (
    "det_row_residual_px",
    "det_row_gated",
    "det_row_y_std",
)

V1_FEATURES: tuple[str, ...] = (
    "depth_nan_ratio",
    "denoise_retained_ratio",
    "det_real_detection_ratio",
    "sam_fill_rate",
    "sam_ontology_divergence",
)

FAM_OH = ("fam_staggered", "fam_continuous", "fam_complex")
FAM_TO_OH = {
    "staggered": "fam_staggered",
    "continuous": "fam_continuous",
    "complex": "fam_complex",
    "t1&2": "fam_staggered",
    "t3": "fam_continuous",
    "t4&5": "fam_complex",
}

# Frozen holdout targets for harness fidelity check
HARNESS_TARGETS = {"mae": 0.094, "spearman": 0.808, "rank_ok": 27, "rank_total": 27}
HARNESS_TOL = {"mae": 0.005, "spearman": 0.015}


def _normalize_family(fam: str) -> str:
    return {
        "t1&2": "staggered",
        "t3": "continuous",
        "t4&5": "complex",
    }.get(fam, fam)


def _add_onehot(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in FAM_OH:
        out[col] = 0.0
    for fam, col in FAM_TO_OH.items():
        out.loc[out["family"].map(_normalize_family) == _normalize_family(fam), col] = 1.0
    # Prefer canonical family names
    out["family"] = out["family"].map(_normalize_family)
    return out


def _extract_full_metrics(run_dir: Path, params_dir: Path | None) -> dict[str, float]:
    metrics = extract_intrinsics(run_dir, params_dir=params_dir, expected_rings=10)
    metrics.update(compute_row_features(run_dir, params_dir=params_dir))
    metrics.update(compute_phase_feature(run_dir))
    out: dict[str, float] = {}
    for k in set(FULL_17) | set(CANDIDATE) | set(V1_FEATURES) | {"phase_incoherence_deg"}:
        try:
            fv = float(metrics.get(k, float("nan")))
            out[k] = fv if np.isfinite(fv) else float("nan")
        except (TypeError, ValueError):
            out[k] = float("nan")
    return out


def build_train_matrix() -> pd.DataFrame:
    """Rebuild training rows with Tier-1 + gate features from artifacts."""
    base = pd.read_csv(TRAIN_CSV)
    rows = []
    # Anchors
    for case in TRAIN_ANCHORS:
        run_dir = REPO_ROOT / "data" / "anchors" / case
        params = ANCHOR_PARAMS[case]
        feats = _extract_full_metrics(run_dir, params)
        # mIoU from base table if present
        sub = base[base["trial_id"] == f"{case}-anchor"]
        miou = float(sub.iloc[0]["mIoU"]) if len(sub) else float("nan")
        rows.append(
            {
                "trial_id": f"{case}-anchor",
                "case": case,
                "family": _normalize_family(str(sub.iloc[0]["family"]) if len(sub) else case),
                "mIoU": miou,
                **feats,
            }
        )
    # Trials
    for case in TRAIN_ANCHORS:
        man_path = DATA_ROOT / f"{case}-trials" / "manifest.json"
        if not man_path.exists():
            continue
        man = json.loads(man_path.read_text(encoding="utf-8"))
        for t in man.get("trials", []):
            if t.get("status") != "ok" or t.get("mIoU") is None:
                continue
            run_dir = REPO_ROOT / t["path"]
            params = ANCHOR_PARAMS[case]
            feats = _extract_full_metrics(run_dir, params)
            rows.append(
                {
                    "trial_id": t["trial_id"],
                    "case": case,
                    "family": _normalize_family(str(t.get("family", case))),
                    "mIoU": float(t["mIoU"]),
                    **feats,
                }
            )
    df = pd.DataFrame(rows).drop_duplicates(subset=["trial_id"], keep="last")
    # Fix family from case id
    from features import FAMILY_OF

    df["family"] = df["case"].map(lambda c: FAMILY_OF[c.split("-")[0]])
    return df.reset_index(drop=True)


def build_holdout_matrix() -> pd.DataFrame:
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    # Prefer cached lean columns from holdout_scores_v2; recompute Tier-1 as needed
    cached = pd.read_csv(HOLDOUT_CSV)
    cache_by_id = {r["run_id"]: r for _, r in cached.iterrows()}
    rows = []
    for entry in registry["runs"]:
        run_dir = REPO_ROOT / entry["path"]
        params = REPO_ROOT / entry["params_dir"]
        if not run_dir.exists():
            continue
        feats = _extract_full_metrics(run_dir, params if params.exists() else None)
        cached_row = cache_by_id.get(entry["run_id"], {})
        miou = cached_row.get("mIoU")
        if miou is None or (isinstance(miou, float) and not np.isfinite(miou)):
            continue
        rows.append(
            {
                "run_id": entry["run_id"],
                "subset": entry["subset"],
                "family": _normalize_family(entry["family"]),
                "config_kind": entry["config_kind"],
                "path": entry["path"],
                "mIoU": float(miou),
                **feats,
            }
        )
    return pd.DataFrame(rows)


def score_holdout(
    model: dict[str, Any] | dict[str, dict[str, Any]],
    hold: pd.DataFrame,
    *,
    mode: str = "pooled",
    alarm_thr: float | None = None,
    low_floor: float | None = None,
) -> dict[str, Any]:
    """Score holdout. mode: pooled | per_family | pooled_oh.

    For per_family, model is {family: model_dict}.
    """
    df = hold.copy()
    features = (
        model["features"]
        if mode != "per_family"
        else next(iter(model.values()))["features"]  # type: ignore[arg-type]
    )
    # Drop incomplete
    ok_mask = df[features].apply(lambda c: pd.to_numeric(c, errors="coerce")).notna().all(axis=1)
    df = df.loc[ok_mask].copy()
    if df.empty:
        return {"n": 0, "mae": float("nan"), "spearman": float("nan"), "rank_ok": 0, "rank_total": 0}

    if mode == "per_family":
        preds = np.full(len(df), np.nan)
        for fam, sub_idx in df.groupby("family").groups.items():
            if fam not in model:
                continue
            preds[df.index.get_indexer(sub_idx)] = predict(model[fam], df.loc[sub_idx])  # type: ignore[index]
        df["proxy"] = preds
    else:
        df["proxy"] = predict(model, df)  # type: ignore[arg-type]

    df = df[np.isfinite(df["proxy"])].copy()
    y = df["mIoU"].to_numpy()
    p = df["proxy"].to_numpy()
    mae = float(mean_absolute_error(y, p))
    sp = float(stats.spearmanr(y, p).correlation or 0.0)
    pe = float(stats.pearsonr(y, p).statistic) if len(df) > 2 else float("nan")

    # Per-family / config MAE
    fam_stats = {}
    for fam, g in df.groupby("family"):
        a = g[g["config_kind"] == "anchor"]
        b = g[g["config_kind"] == "bad"]
        fam_stats[fam] = {
            "mae": float(mean_absolute_error(g["mIoU"], g["proxy"])),
            "mae_anchor": float(mean_absolute_error(a["mIoU"], a["proxy"])) if len(a) else float("nan"),
            "mae_bad": float(mean_absolute_error(b["mIoU"], b["proxy"])) if len(b) else float("nan"),
            "spearman": float(stats.spearmanr(g["mIoU"], g["proxy"]).correlation or 0.0),
            "n": int(len(g)),
        }

    # Ranking
    ok = tot = 0
    misses = []
    for subset, g in df.groupby("subset"):
        a = g[g["config_kind"] == "anchor"]
        b = g[g["config_kind"] == "bad"]
        if a.empty or b.empty:
            continue
        tot += 1
        if float(a.iloc[0]["proxy"]) > float(b.iloc[0]["proxy"]):
            ok += 1
        else:
            misses.append(subset)

    # Alarm
    if alarm_thr is None:
        # calibrate on predictions vs train-like floor from holdout quantile of mIoU
        alarm_thr = float(np.quantile(p, 0.33))
    if low_floor is None:
        low_floor = float(np.quantile(y, 0.33))
    alarm = p <= alarm_thr
    is_low = y <= low_floor
    tp = int(np.sum(alarm & is_low))
    fp = int(np.sum(alarm & ~is_low))
    fn = int(np.sum(~alarm & is_low))
    prec = tp / (tp + fp) if (tp + fp) else 0.0
    rec = tp / (tp + fn) if (tp + fn) else 0.0

    return {
        "n": int(len(df)),
        "mae": mae,
        "spearman": sp,
        "pearson": pe,
        "mae_anchor": float(
            mean_absolute_error(
                df[df.config_kind == "anchor"]["mIoU"],
                df[df.config_kind == "anchor"]["proxy"],
            )
        )
        if (df.config_kind == "anchor").any()
        else float("nan"),
        "mae_bad": float(
            mean_absolute_error(
                df[df.config_kind == "bad"]["mIoU"],
                df[df.config_kind == "bad"]["proxy"],
            )
        )
        if (df.config_kind == "bad").any()
        else float("nan"),
        "mae_anchor_continuous": fam_stats.get("continuous", {}).get("mae_anchor", float("nan")),
        "mae_anchor_staggered": fam_stats.get("staggered", {}).get("mae_anchor", float("nan")),
        "mae_anchor_complex": fam_stats.get("complex", {}).get("mae_anchor", float("nan")),
        "family": fam_stats,
        "rank_ok": ok,
        "rank_total": tot,
        "rank_acc": ok / tot if tot else 0.0,
        "rank_misses": misses,
        "alarm_threshold": float(alarm_thr),
        "low_miou_floor": float(low_floor),
        "alarm_precision": prec,
        "alarm_recall": rec,
        "alarm_tp": tp,
        "alarm_fp": fp,
        "alarm_fn": fn,
    }


def fit_and_score(
    train: pd.DataFrame,
    hold: pd.DataFrame,
    features: list[str],
    *,
    mode: str = "pooled",
    label: str = "",
    group: str = "",
) -> dict[str, Any]:
    need = list(features) + ["mIoU"]
    if mode == "pooled_oh":
        tr = _add_onehot(train)
        ho = _add_onehot(hold)
        feats = list(features) + list(FAM_OH)
        tr = tr.dropna(subset=feats + ["mIoU"])
        model = fit_ridge(tr, feats)
        pred_tr = predict(model, tr)
        alarm = calibrate_alarm(tr["mIoU"].to_numpy(), pred_tr)
        floor = float(np.quantile(tr["mIoU"].to_numpy(), 0.33))
        hold_s = score_holdout(model, ho, mode="pooled", alarm_thr=alarm, low_floor=floor)
        return {
            "label": label,
            "group": group,
            "mode": mode,
            "n_features": len(feats),
            "features": feats,
            "n_train": int(len(tr)),
            "train_mae": model["train_mae"],
            "train_spearman": model["train_spearman"],
            "alarm_threshold": alarm,
            **{f"holdout_{k}": v for k, v in hold_s.items() if not isinstance(v, (dict, list))},
            "holdout_family": hold_s["family"],
            "holdout_rank_misses": hold_s["rank_misses"],
        }

    if mode == "per_family":
        models: dict[str, Any] = {}
        alarms: dict[str, float] = {}
        floors: dict[str, float] = {}
        n_train = 0
        train_maes = []
        for fam in sorted(train["family"].unique()):
            sub = train[train["family"] == fam].dropna(subset=features + ["mIoU"])
            if len(sub) < 5:
                continue
            m = fit_ridge(sub, features)
            models[fam] = m
            pred = predict(m, sub)
            alarms[fam] = calibrate_alarm(sub["mIoU"].to_numpy(), pred)
            floors[fam] = float(np.quantile(sub["mIoU"].to_numpy(), 0.33))
            n_train += len(sub)
            train_maes.append(m["train_mae"])
        # Score with per-family alarm: use family-specific threshold
        df = hold.copy()
        ok_mask = df[features].notna().all(axis=1)
        df = df.loc[ok_mask].copy()
        preds = []
        for _, row in df.iterrows():
            fam = row["family"]
            if fam not in models:
                preds.append(np.nan)
                continue
            preds.append(float(predict(models[fam], pd.DataFrame([row]))[0]))
        df["proxy"] = preds
        df = df[np.isfinite(df["proxy"])].copy()
        y = df["mIoU"].to_numpy()
        p = df["proxy"].to_numpy()
        mae = float(mean_absolute_error(y, p))
        sp = float(stats.spearmanr(y, p).correlation or 0.0)
        ok = tot = 0
        for subset, g in df.groupby("subset"):
            a = g[g["config_kind"] == "anchor"]
            b = g[g["config_kind"] == "bad"]
            if a.empty or b.empty:
                continue
            tot += 1
            ok += int(float(a.iloc[0]["proxy"]) > float(b.iloc[0]["proxy"]))
        alarm_arr = df.apply(
            lambda r: float(r["proxy"]) <= alarms.get(r["family"], 0.5), axis=1
        ).to_numpy()
        is_low_arr = df.apply(
            lambda r: float(r["mIoU"]) <= floors.get(r["family"], 0.33), axis=1
        ).to_numpy()
        tp = int(np.sum(alarm_arr & is_low_arr))
        fp = int(np.sum(alarm_arr & ~is_low_arr))
        fn = int(np.sum(~alarm_arr & is_low_arr))
        a = df[df.config_kind == "anchor"]
        cont_a = a[a.family == "continuous"]
        return {
            "label": label,
            "group": group,
            "mode": mode,
            "n_features": len(features),
            "features": features,
            "n_train": n_train,
            "train_mae": float(np.mean(train_maes)) if train_maes else float("nan"),
            "train_spearman": float("nan"),
            "holdout_n": int(len(df)),
            "holdout_mae": mae,
            "holdout_spearman": sp,
            "holdout_mae_anchor": float(mean_absolute_error(a["mIoU"], a["proxy"])) if len(a) else float("nan"),
            "holdout_mae_anchor_continuous": float(
                mean_absolute_error(cont_a["mIoU"], cont_a["proxy"])
            )
            if len(cont_a)
            else float("nan"),
            "holdout_mae_anchor_staggered": float(
                mean_absolute_error(a[a.family == "staggered"]["mIoU"], a[a.family == "staggered"]["proxy"])
            )
            if (a.family == "staggered").any()
            else float("nan"),
            "holdout_mae_anchor_complex": float(
                mean_absolute_error(a[a.family == "complex"]["mIoU"], a[a.family == "complex"]["proxy"])
            )
            if (a.family == "complex").any()
            else float("nan"),
            "holdout_rank_ok": ok,
            "holdout_rank_total": tot,
            "holdout_rank_acc": ok / tot if tot else 0.0,
            "holdout_alarm_precision": tp / (tp + fp) if (tp + fp) else 0.0,
            "holdout_alarm_recall": tp / (tp + fn) if (tp + fn) else 0.0,
            "holdout_alarm_tp": tp,
            "holdout_alarm_fp": fp,
            "holdout_alarm_fn": fn,
            "n_train_per_family": {
                fam: int((train["family"] == fam).sum()) for fam in sorted(train["family"].unique())
            },
        }

    # pooled
    tr = train.dropna(subset=features + ["mIoU"]).copy()
    model = fit_ridge(tr, features)
    pred_tr = predict(model, tr)
    alarm = calibrate_alarm(tr["mIoU"].to_numpy(), pred_tr)
    floor = float(np.quantile(tr["mIoU"].to_numpy(), 0.33))
    hold_s = score_holdout(model, hold, mode="pooled", alarm_thr=alarm, low_floor=floor)
    return {
        "label": label,
        "group": group,
        "mode": mode,
        "n_features": len(features),
        "features": features,
        "n_train": int(len(tr)),
        "train_mae": model["train_mae"],
        "train_spearman": model["train_spearman"],
        "alarm_threshold": alarm,
        "model": model,
        **{f"holdout_{k}": v for k, v in hold_s.items() if not isinstance(v, (dict, list))},
        "holdout_family": hold_s["family"],
        "holdout_rank_misses": hold_s["rank_misses"],
    }


def score_frozen(hold: pd.DataFrame, path: Path, label: str, group: str) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    model = payload["model"]
    alarm = float(payload["alarm_threshold"])
    floor = float(payload["low_miou_floor"])
    hold_s = score_holdout(model, hold, mode="pooled", alarm_thr=alarm, low_floor=floor)
    return {
        "label": label,
        "group": group,
        "mode": "frozen",
        "n_features": len(model["features"]),
        "features": model["features"],
        "n_train": payload.get("n_train_rows", model.get("n_train")),
        "train_mae": model.get("train_mae"),
        "train_spearman": model.get("train_spearman"),
        "alarm_threshold": alarm,
        **{f"holdout_{k}": v for k, v in hold_s.items() if not isinstance(v, (dict, list))},
        "holdout_family": hold_s["family"],
        "holdout_rank_misses": hold_s["rank_misses"],
    }


def harness_check(hold: pd.DataFrame) -> dict[str, Any]:
    """Reproduce frozen v2 holdout numbers."""
    result = score_frozen(hold, MODELS_V2, "frozen_v2_lean", "harness")
    mae = result["holdout_mae"]
    sp = result["holdout_spearman"]
    rank_ok = result["holdout_rank_ok"]
    rank_tot = result["holdout_rank_total"]
    criteria = {
        "mae_close": abs(mae - HARNESS_TARGETS["mae"]) <= HARNESS_TOL["mae"],
        "spearman_close": abs(sp - HARNESS_TARGETS["spearman"]) <= HARNESS_TOL["spearman"],
        "rank_27_27": rank_ok == HARNESS_TARGETS["rank_ok"] and rank_tot == HARNESS_TARGETS["rank_total"],
    }
    passed = all(criteria.values())
    lines = [
        "# Ablation harness gate — frozen v2 reproduction",
        "",
        f"_Generated {datetime.now().isoformat(timespec='seconds')}_",
        "",
        f"- Holdout MAE: {mae:.3f} (target {HARNESS_TARGETS['mae']:.3f} ± {HARNESS_TOL['mae']})",
        f"- Spearman: {sp:.3f} (target {HARNESS_TARGETS['spearman']:.3f} ± {HARNESS_TOL['spearman']})",
        f"- Ranking: {rank_ok}/{rank_tot} (target 27/27)",
        "",
        "## Criteria",
        "",
    ]
    for k, v in criteria.items():
        lines.append(f"- `{k}`: **{'PASS' if v else 'FAIL'}**")
    lines += ["", f"## Overall: **{'PASS' if passed else 'FAIL'}**", ""]
    HARNESS_GATE.write_text("\n".join(lines), encoding="utf-8")
    print(f"Harness gate: {'PASS' if passed else 'FAIL'} MAE={mae:.3f} Sp={sp:.3f} rank={rank_ok}/{rank_tot}")
    print(f"Wrote {HARNESS_GATE}")
    if not passed:
        raise SystemExit(f"Harness fidelity check failed: {criteria}")
    return result


def alarm_sensitivity(
    train: pd.DataFrame, hold: pd.DataFrame, features: list[str]
) -> list[dict[str, Any]]:
    tr = train.dropna(subset=features + ["mIoU"])
    model = fit_ridge(tr, features)
    pred_tr = predict(model, tr)
    base_thr = calibrate_alarm(tr["mIoU"].to_numpy(), pred_tr)
    floor = float(np.quantile(tr["mIoU"].to_numpy(), 0.33))
    # Quantile steps around base
    qs = np.quantile(pred_tr, np.linspace(0.05, 0.95, 19))
    # Find index closest to base_thr
    idx = int(np.argmin(np.abs(qs - base_thr)))
    steps = []
    for j, label in [(-1, "thr_minus_1q"), (0, "thr_base"), (1, "thr_plus_1q")]:
        k = max(0, min(len(qs) - 1, idx + j))
        thr = float(qs[k])
        s = score_holdout(model, hold, mode="pooled", alarm_thr=thr, low_floor=floor)
        steps.append(
            {
                "label": label,
                "threshold": thr,
                "precision": s["alarm_precision"],
                "recall": s["alarm_recall"],
                "tp": s["alarm_tp"],
                "fp": s["alarm_fp"],
                "fn": s["alarm_fn"],
            }
        )
    return steps


def run_all() -> dict[str, Any]:
    print("Building train/holdout feature matrices (Tier-1 + gate)...")
    train = build_train_matrix()
    hold = build_holdout_matrix()
    print(f"Train n={len(train)} Holdout n={len(hold)}")
    print(train.groupby("family").size().to_dict())

    # --- Harness check ---
    harness_check(hold)

    lean5 = list(json.loads(MODELS_V2.read_text())["features"])
    results: list[dict[str, Any]] = []

    # A. Regime-swap
    print("\n=== A. Regime-swap ===")
    results.append(
        fit_and_score(train, hold, list(V1_FEATURES), mode="pooled", label="A_v1_features_refit", group="regime")
    )
    results.append(
        fit_and_score(train, hold, lean5, mode="pooled", label="A_v2_lean_refit", group="regime")
    )
    results.append(score_frozen(hold, MODELS_V1, "A_frozen_v1", "regime"))
    results.append(score_frozen(hold, MODELS_V2, "A_frozen_v2", "regime"))

    # B. Unified vs per-family
    print("\n=== B. Unified vs per-family ===")
    results.append(
        fit_and_score(train, hold, lean5, mode="pooled", label="B_pooled", group="architecture")
    )
    results.append(
        fit_and_score(train, hold, lean5, mode="per_family", label="B_per_family", group="architecture")
    )
    results.append(
        fit_and_score(train, hold, lean5, mode="pooled_oh", label="B_pooled_onehot", group="architecture")
    )

    # C. Blocks
    print("\n=== C. Block ablation ===")
    results.append(
        fit_and_score(train, hold, list(EVIDENCE), mode="pooled", label="C_Evidence", group="blocks")
    )
    results.append(
        fit_and_score(train, hold, list(COHERENCE), mode="pooled", label="C_Coherence", group="blocks")
    )
    results.append(
        fit_and_score(train, hold, list(CANDIDATE), mode="pooled", label="C_Evidence+Coherence", group="blocks")
    )

    # D. Leanness
    print("\n=== D. Leanness ===")
    results.append(
        fit_and_score(train, hold, lean5, mode="pooled", label="D_lean5", group="leanness")
    )
    results.append(
        fit_and_score(train, hold, list(CANDIDATE), mode="pooled", label="D_candidate8", group="leanness")
    )
    results.append(
        fit_and_score(train, hold, list(FULL_17), mode="pooled", label="D_tier1_gate17", group="leanness")
    )
    for drop in lean5:
        feats = [f for f in lean5 if f != drop]
        results.append(
            fit_and_score(
                train, hold, feats, mode="pooled", label=f"D_loo_{drop}", group="leanness_loo"
            )
        )

    # Controls: permutation on key variants
    print("\n=== Controls: permutation ===")
    perm_labels = {
        "A_v2_lean_refit": lean5,
        "B_pooled": lean5,
        "C_Evidence+Coherence": list(CANDIDATE),
        "D_lean5": lean5,
        "D_tier1_gate17": list(FULL_17),
        "A_v1_features_refit": list(V1_FEATURES),
    }
    permutations = {}
    for lab, feats in perm_labels.items():
        tr = train.dropna(subset=feats + ["mIoU"])
        permutations[lab] = permutation_control(tr, feats)
        print(
            f"  perm {lab}: real={permutations[lab]['real_mae']:.3f} "
            f"vs {permutations[lab]['perm_mae_mean']:.3f}±{permutations[lab]['perm_mae_std']:.3f} "
            f"pass={permutations[lab]['pass']}"
        )

    print("\n=== Controls: alarm sensitivity (lean5) ===")
    alarm_sens = alarm_sensitivity(train, hold, lean5)
    for s in alarm_sens:
        print(
            f"  {s['label']}: thr={s['threshold']:.3f} P={s['precision']:.2f} "
            f"R={s['recall']:.2f} TP/FP/FN={s['tp']}/{s['fp']}/{s['fn']}"
        )

    # Attach perm pass to matching results
    for r in results:
        if r["label"] in permutations:
            r["perm_real_mae"] = permutations[r["label"]]["real_mae"]
            r["perm_mae_mean"] = permutations[r["label"]]["perm_mae_mean"]
            r["perm_mae_std"] = permutations[r["label"]]["perm_mae_std"]
            r["perm_pass"] = permutations[r["label"]]["pass"]

    payload = {
        "created_at": datetime.now().isoformat(),
        "n_train": int(len(train)),
        "n_holdout": int(len(hold)),
        "lean5": lean5,
        "full17": list(FULL_17),
        "results": results,
        "permutations": permutations,
        "alarm_sensitivity_lean5": alarm_sens,
        "historical_bo_unified": {
            "note": "Quoted from bo-unified/ablation.md (different train/holdout era)",
            "per_family_B1B2lean_mae": 0.110,
            "per_family_rank": "24/24",
            "pooled_B1B2lean_mae": 0.122,
        },
    }

    # Strip heavy model blobs from JSON
    for r in payload["results"]:
        r.pop("model", None)

    ABLATION_JSON.write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")

    # Flat CSV
    flat_rows = []
    for r in results:
        flat_rows.append(
            {
                "label": r["label"],
                "group": r["group"],
                "mode": r["mode"],
                "n_features": r["n_features"],
                "n_train": r.get("n_train"),
                "train_mae": r.get("train_mae"),
                "train_spearman": r.get("train_spearman"),
                "holdout_n": r.get("holdout_n"),
                "holdout_mae": r.get("holdout_mae"),
                "holdout_spearman": r.get("holdout_spearman"),
                "holdout_mae_anchor": r.get("holdout_mae_anchor"),
                "holdout_mae_anchor_continuous": r.get("holdout_mae_anchor_continuous"),
                "holdout_mae_anchor_staggered": r.get("holdout_mae_anchor_staggered"),
                "holdout_mae_anchor_complex": r.get("holdout_mae_anchor_complex"),
                "holdout_rank_ok": r.get("holdout_rank_ok"),
                "holdout_rank_total": r.get("holdout_rank_total"),
                "holdout_rank_acc": r.get("holdout_rank_acc"),
                "holdout_alarm_precision": r.get("holdout_alarm_precision"),
                "holdout_alarm_recall": r.get("holdout_alarm_recall"),
                "holdout_alarm_tp": r.get("holdout_alarm_tp"),
                "holdout_alarm_fp": r.get("holdout_alarm_fp"),
                "holdout_alarm_fn": r.get("holdout_alarm_fn"),
                "perm_pass": r.get("perm_pass"),
                "features": ",".join(r.get("features") or []),
            }
        )
    pd.DataFrame(flat_rows).to_csv(ABLATION_CSV, index=False)
    print(f"Wrote {ABLATION_CSV}")
    print(f"Wrote {ABLATION_JSON}")

    write_report_section(payload)
    return payload


def _fmt(x: Any, nd: int = 3) -> str:
    try:
        if x is None or (isinstance(x, float) and not np.isfinite(x)):
            return "—"
        return f"{float(x):.{nd}f}"
    except (TypeError, ValueError):
        return "—"


def write_report_section(payload: dict[str, Any]) -> None:
    by = {r["label"]: r for r in payload["results"]}

    def row(label: str, note: str = "") -> str:
        r = by[label]
        rank = f"{r.get('holdout_rank_ok')}/{r.get('holdout_rank_total')}"
        alarm = f"{_fmt(r.get('holdout_alarm_precision'), 2)}/{_fmt(r.get('holdout_alarm_recall'), 2)}"
        return (
            f"| `{label}` | {r['n_features']} | {_fmt(r.get('holdout_mae'))} | "
            f"{_fmt(r.get('holdout_spearman'))} | {_fmt(r.get('holdout_mae_anchor'))} | "
            f"{_fmt(r.get('holdout_mae_anchor_continuous'))} | {rank} | {alarm} | {note} |"
        )

    lines = [
        "",
        "---",
        "",
        "# Consolidated ablation study",
        "",
        f"_Generated {datetime.now().isoformat(timespec='seconds')}_",
        "",
        "Zero new pipeline runs. All variants refit on the v2 training table",
        f"(n={payload['n_train']}) and scored on the same {payload['n_holdout']} holdout runs.",
        "Harness gate: frozen v2 numbers reproduced (`ablation_harness_gate.md`).",
        "",
        "Columns: MAE / Spearman / MAE_anchor / MAE_anchor(continuous) / Rank / Alarm P/R.",
        "",
        "## A. Regime-swap (headline)",
        "",
        "v1 features include strategy-confounded `det_real_detection_ratio`;",
        "v2 replaces it with gate-conditional `det_row_residual_px` + `det_row_gated`.",
        "",
        "| Variant | n_feat | MAE | Sp | MAE_a | MAE_a_cont | Rank | Alarm P/R | Note |",
        "|---|---:|---:|---:|---:|---:|---|---|---|",
        row("A_v1_features_refit", "controlled: v1 feats on v2 table"),
        row("A_v2_lean_refit", "controlled: v2 lean on v2 table"),
        row("A_frozen_v1", "deployed v1"),
        row("A_frozen_v2", "deployed v2"),
        "",
        f"Continuous MAE_anchor: v1-features {_fmt(by['A_v1_features_refit'].get('holdout_mae_anchor_continuous'))} → "
        f"v2-lean {_fmt(by['A_v2_lean_refit'].get('holdout_mae_anchor_continuous'))} "
        f"(frozen v1 {_fmt(by['A_frozen_v1'].get('holdout_mae_anchor_continuous'))} → "
        f"frozen v2 {_fmt(by['A_frozen_v2'].get('holdout_mae_anchor_continuous'))}).",
        "",
        "## B. Unified vs per-family",
        "",
        "All on v2 lean-5 features. Per-family n_train = "
        f"`{by['B_per_family'].get('n_train_per_family')}` — the 3-anchor design starves",
        "family-specific models (staggered/complex ≈14 rows).",
        "",
        "| Variant | n_feat | MAE | Sp | MAE_a | MAE_a_cont | Rank | Alarm P/R | Note |",
        "|---|---:|---:|---:|---:|---:|---|---|---|",
        row("B_pooled", "one Ridge"),
        row("B_per_family", "3 RidgeCVs"),
        row("B_pooled_onehot", "+ family one-hot"),
        "",
        "Historical reference (`bo-unified/ablation.md`, different era): per-family",
        f"B1+B2lean MAE={payload['historical_bo_unified']['per_family_B1B2lean_mae']}, "
        f"rank {payload['historical_bo_unified']['per_family_rank']}; "
        f"pooled MAE={payload['historical_bo_unified']['pooled_B1B2lean_mae']}.",
        "",
        "## C. Block ablation",
        "",
        "Evidence = depth/artifact quality; Coherence = detection+SAM form (regime-neutral).",
        "Narrative: Coherence predicts; Evidence audits (cosmetic-fix anti-pattern).",
        "",
        "| Variant | n_feat | MAE | Sp | MAE_a | MAE_a_cont | Rank | Alarm P/R | Note |",
        "|---|---:|---:|---:|---:|---:|---|---|---|",
        row("C_Evidence", "depth_nan + retention"),
        row("C_Coherence", "fill/onto/gate/phase/y_std"),
        row("C_Evidence+Coherence", "full candidate"),
        "",
        "## D. Leanness",
        "",
        "| Variant | n_feat | MAE | Sp | MAE_a | MAE_a_cont | Rank | Alarm P/R | Note |",
        "|---|---:|---:|---:|---:|---:|---|---|---|",
        row("D_lean5", "frozen v2 set"),
        row("D_candidate8", "full v2 candidate"),
        row("D_tier1_gate17", "14 Tier-1 + 3 gate feats"),
        "",
        "### Leave-one-out (lean-5)",
        "",
        "| Variant | MAE | Sp | MAE_a_cont | Rank |",
        "|---|---:|---:|---:|---|",
    ]
    for lab, r in sorted(by.items()):
        if not lab.startswith("D_loo_"):
            continue
        lines.append(
            f"| `{lab}` | {_fmt(r.get('holdout_mae'))} | {_fmt(r.get('holdout_spearman'))} | "
            f"{_fmt(r.get('holdout_mae_anchor_continuous'))} | "
            f"{r.get('holdout_rank_ok')}/{r.get('holdout_rank_total')} |"
        )

    lines += [
        "",
        "## Controls",
        "",
        "### Permutation (within-family mIoU shuffle, 20 reps)",
        "",
        "| Variant | real MAE | perm MAE | pass |",
        "|---|---:|---:|---|",
    ]
    for lab, p in payload["permutations"].items():
        lines.append(
            f"| `{lab}` | {_fmt(p['real_mae'])} | "
            f"{_fmt(p['perm_mae_mean'])}±{_fmt(p['perm_mae_std'])} | {p['pass']} |"
        )

    lines += [
        "",
        "### Alarm-threshold sensitivity (lean-5)",
        "",
        "| Step | threshold | P | R | TP/FP/FN |",
        "|---|---:|---:|---:|---|",
    ]
    for s in payload["alarm_sensitivity_lean5"]:
        lines.append(
            f"| {s['label']} | {_fmt(s['threshold'])} | {_fmt(s['precision'], 2)} | "
            f"{_fmt(s['recall'], 2)} | {s['tp']}/{s['fp']}/{s['fn']} |"
        )

    lines += [
        "",
        "## Artifacts",
        "",
        "- `bo-elegant/family/ablation_study.csv`",
        "- `bo-elegant/family/ablation_study.json`",
        "- `bo-elegant/ablation_harness_gate.md`",
        "",
    ]

    text = REPORT.read_text(encoding="utf-8") if REPORT.exists() else ""
    marker = "\n---\n\n# Consolidated ablation study"
    if marker in text:
        text = text.split(marker)[0].rstrip() + "\n"
    REPORT.write_text(text + "\n".join(lines), encoding="utf-8")
    print(f"Wrote ablation section to {REPORT}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--harness-only", action="store_true")
    args = parser.parse_args()
    if args.harness_only:
        hold = build_holdout_matrix()
        harness_check(hold)
        return
    run_all()


if __name__ == "__main__":
    main()
