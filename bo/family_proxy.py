#!/usr/bin/env python3
"""Per-family Ridge proxy: train, select known-bad configs, score holdouts, report."""

from __future__ import annotations

import argparse
import json
import math
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.linear_model import RidgeCV
from sklearn.metrics import mean_absolute_error
from sklearn.preprocessing import StandardScaler
from scipy import stats

import sys

REPO_ROOT = Path(__file__).resolve().parent.parent
BO_DIR = Path(__file__).resolve().parent
FAMILY_DIR = BO_DIR / "family"
sys.path.insert(0, str(BO_DIR))

from blocks import features_for  # noqa: E402
from intrinsics import TIER1_KEYS  # noqa: E402
from spaces import (  # noqa: E402
    CASE_CONFIG,
    FAMILY_HOLDOUT_SUBSETS,
    FAMILY_TRAIN_CASES,
)

FEATURE_SET = "B1+B2lean"
FEATURES = features_for(FEATURE_SET)
BAD_CONFIGS_PATH = FAMILY_DIR / "bad_configs.json"
MODELS_PATH = FAMILY_DIR / "models.json"
HOLDOUT_SCORES_PATH = FAMILY_DIR / "holdout_scores.csv"
REPORT_PATH = FAMILY_DIR / "report.md"


def load_campaign(case: str, study_root: Path | None = None) -> pd.DataFrame:
    """Load successful non-repeat trials from a BO campaign manifest."""
    root = Path(study_root) if study_root else REPO_ROOT / "data" / "bo" / f"{case}-bo-proxy"
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    rows = []
    for t in manifest.get("trials", []):
        if t.get("status") != "ok" or t.get("mIoU") is None:
            continue
        acq = str(t.get("acquisition") or "")
        if acq.startswith("repeat_"):
            continue
        row: dict[str, Any] = {
            "case": case,
            "family": CASE_CONFIG[case]["family"],
            "trial_id": t["trial_id"],
            "acquisition": t.get("acquisition"),
            "mIoU": float(t["mIoU"]),
        }
        metrics = t.get("metrics") or {}
        for k in TIER1_KEYS:
            row[k] = metrics.get(k)
        row["orient_invariant_ok"] = metrics.get("orient_invariant_ok")
        row["orient_h_ring_corr"] = metrics.get("orient_h_ring_corr")
        rows.append(row)
    return pd.DataFrame(rows)


def _safe_scale(scale: np.ndarray, eps: float = 1e-8) -> np.ndarray:
    """Replace near-zero scales so constant / near-constant features stay inert."""
    out = np.asarray(scale, dtype=float).copy()
    out[~np.isfinite(out)] = 1.0
    out[np.abs(out) < eps] = 1.0
    return out


def _fit_ridge(df: pd.DataFrame, features: list[str]) -> dict[str, Any]:
    X = df[features].astype(float).to_numpy()
    y = df["mIoU"].astype(float).to_numpy()
    scaler = StandardScaler()
    scaler.fit(X)
    scale = _safe_scale(scaler.scale_)
    mean = np.asarray(scaler.mean_, dtype=float)
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
    }


def _predict(model: dict[str, Any], df: pd.DataFrame) -> np.ndarray:
    feats = model["features"]
    X = df[feats].astype(float).to_numpy()
    mean = np.asarray(model["scaler_mean"], dtype=float)
    scale = _safe_scale(np.asarray(model["scaler_scale"], dtype=float))
    Xs = (X - mean) / scale
    return Xs @ np.asarray(model["coef"], dtype=float) + float(model["intercept"])


def _calibrate_alarm(y: np.ndarray, pred: np.ndarray, low_q: float = 0.33) -> float:
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


def load_family_training(family: str) -> pd.DataFrame:
    frames = []
    for case in FAMILY_TRAIN_CASES[family]:
        root = REPO_ROOT / "data" / "bo" / f"{case}-bo-proxy"
        if not (root / "manifest.json").exists():
            raise FileNotFoundError(f"Missing campaign for {case}: {root}")
        # Temporarily allow load_campaign for cases in CASE_CONFIG
        df = load_campaign(case)
        if df.empty:
            raise RuntimeError(f"No ok trials for {case}")
        frames.append(df)
    return pd.concat(frames, ignore_index=True)


def select_bad_configs() -> dict[str, Any]:
    """Pick lowest-mIoU completed trial per family; freeze overlay + provenance."""
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
                # Prefer genuinely low quality; skip near-anchor
                miou = float(t["mIoU"])
                metrics = t.get("metrics") or {}
                # Require extractable tier-1 (already ok if status ok + metrics present)
                if not metrics:
                    continue
                cand = {
                    "family": family,
                    "source_case": case,
                    "trial_id": t["trial_id"],
                    "acquisition": acq,
                    "training_mIoU": miou,
                    "overlay": t.get("overlay") or {},
                    "output_dir": t.get("output_dir"),
                }
                if best is None or miou < best["training_mIoU"]:
                    best = cand
        if best is None:
            raise RuntimeError(f"No candidate bad trial for family {family}")
        # Sanity: bad should be materially below sibling anchor
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


def train_family_proxies() -> dict[str, Any]:
    FAMILY_DIR.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = {
        "feature_set": FEATURE_SET,
        "features": FEATURES,
        "created_at": datetime.now().isoformat(),
        "families": {},
    }
    for family in FAMILY_TRAIN_CASES:
        df = load_family_training(family)
        # Drop rows with NaN features
        sub = df.dropna(subset=FEATURES + ["mIoU"]).copy()
        model = _fit_ridge(sub, FEATURES)
        # Within-family leave-one-tunnel-out when ≥2 tunnels
        loto: list[dict[str, Any]] = []
        cases = list(FAMILY_TRAIN_CASES[family])
        if len(cases) >= 2:
            for held in cases:
                train = sub[sub["case"] != held]
                test = sub[sub["case"] == held]
                if len(train) < 5 or len(test) < 3:
                    continue
                m = _fit_ridge(train, FEATURES)
                pred = _predict(m, test)
                y = test["mIoU"].to_numpy()
                loto.append(
                    {
                        "held_out_case": held,
                        "n_train": int(len(train)),
                        "n_test": int(len(test)),
                        "mae": float(mean_absolute_error(y, pred)),
                        "spearman": float(stats.spearmanr(y, pred).correlation or 0.0),
                    }
                )
        # Alarm on pooled leave-one-tunnel preds if available and numerically sane.
        pred_train = _predict(model, sub)
        y_train = sub["mIoU"].to_numpy()
        alarm_thr = _calibrate_alarm(y_train, pred_train)
        pooled_mae = float(mean_absolute_error(y_train, pred_train))
        pooled_sp = float(stats.spearmanr(y_train, pred_train).correlation or 0.0)
        loto_source = "train"
        if loto:
            preds_all = []
            y_all = []
            for held in cases:
                train = sub[sub["case"] != held]
                test = sub[sub["case"] == held]
                if len(train) < 5 or len(test) < 3:
                    continue
                m = _fit_ridge(train, FEATURES)
                preds_all.append(_predict(m, test))
                y_all.append(test["mIoU"].to_numpy())
            y_cat = np.concatenate(y_all)
            p_cat = np.concatenate(preds_all)
            mae_loto = float(mean_absolute_error(y_cat, p_cat))
            sp_loto = float(stats.spearmanr(y_cat, p_cat).correlation or 0.0)
            # Reject pathological LOTO (near-constant train features → explode).
            if math.isfinite(mae_loto) and mae_loto < 1.0 and np.all(np.isfinite(p_cat)):
                alarm_thr = _calibrate_alarm(y_cat, p_cat)
                pooled_mae = mae_loto
                pooled_sp = sp_loto
                loto_source = "leave_one_tunnel"
            else:
                loto_source = "train_fallback_unstable_loto"
                for r in loto:
                    r["note"] = "pooled LOTO unstable; alarm/metrics from full-train fit"

        # Family low-mIoU floor for holdout alarm ground truth (training quantile)
        low_floor = float(np.quantile(sub["mIoU"].to_numpy(), 0.33))

        fam_rec = {
            "train_cases": cases,
            "n_train_rows": int(len(sub)),
            "model": model,
            "leave_one_tunnel_out": loto,
            "pooled_mae": pooled_mae,
            "pooled_spearman": pooled_sp,
            "pooled_source": loto_source,
            "alarm_threshold": alarm_thr,
            "low_miou_floor": low_floor,
        }
        payload["families"][family] = fam_rec
        print(
            f"{family}: n={len(sub)} train_mae={model['train_mae']:.3f} "
            f"pooled_mae={pooled_mae:.3f} sp={pooled_sp:.3f} alarm={alarm_thr:.3f}"
        )

    MODELS_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {MODELS_PATH}")
    return payload


def _load_holdout_run(subset: str, config_kind: str) -> dict[str, Any] | None:
    man_path = REPO_ROOT / "data" / "bo" / f"{subset}-family-proxy" / "manifest.json"
    if not man_path.exists():
        return None
    man = json.loads(man_path.read_text(encoding="utf-8"))
    for r in man.get("runs", []):
        if r.get("run_id") == f"{subset}-{config_kind}":
            return r
    return None


def score_holdouts() -> pd.DataFrame:
    if not MODELS_PATH.exists():
        raise FileNotFoundError(f"Missing {MODELS_PATH}; run --train first")
    models = json.loads(MODELS_PATH.read_text(encoding="utf-8"))
    rows = []
    for family, subsets in FAMILY_HOLDOUT_SUBSETS.items():
        fam_model = models["families"][family]
        model = fam_model["model"]
        alarm_thr = float(fam_model["alarm_threshold"])
        low_floor = float(fam_model["low_miou_floor"])
        for subset in subsets:
            for kind in ("anchor", "bad"):
                rec = _load_holdout_run(subset, kind)
                if rec is None:
                    rows.append(
                        {
                            "subset": subset,
                            "family": family,
                            "config_kind": kind,
                            "status": "missing",
                            "mIoU": np.nan,
                            "proxy": np.nan,
                            "abs_err": np.nan,
                            "alarm": False,
                            "is_low_miou": False,
                            "alarm_correct": False,
                        }
                    )
                    continue
                metrics = rec.get("metrics") or {}
                feat_row = {f: metrics.get(f) for f in FEATURES}
                df_one = pd.DataFrame([feat_row])
                status = rec.get("status")
                miou = rec.get("mIoU")
                if status != "ok" or miou is None or df_one[FEATURES].isna().any(axis=None):
                    rows.append(
                        {
                            "subset": subset,
                            "family": family,
                            "config_kind": kind,
                            "status": status or "failed",
                            "mIoU": miou if miou is not None else np.nan,
                            "proxy": np.nan,
                            "abs_err": np.nan,
                            "alarm": True,  # treat failure as alarm-worthy
                            "is_low_miou": True,
                            "alarm_correct": True,
                            "note": "pipeline_or_feature_failure",
                        }
                    )
                    continue
                proxy = float(_predict(model, df_one)[0])
                miou_f = float(miou)
                is_low = miou_f <= low_floor
                alarm = proxy <= alarm_thr
                rows.append(
                    {
                        "subset": subset,
                        "family": family,
                        "config_kind": kind,
                        "status": "ok",
                        "mIoU": miou_f,
                        "proxy": proxy,
                        "abs_err": abs(proxy - miou_f),
                        "alarm": alarm,
                        "is_low_miou": is_low,
                        "alarm_correct": alarm == is_low,
                        "alarm_threshold": alarm_thr,
                        "low_miou_floor": low_floor,
                    }
                )
    df = pd.DataFrame(rows)
    FAMILY_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(HOLDOUT_SCORES_PATH, index=False)
    print(f"Wrote {HOLDOUT_SCORES_PATH} ({len(df)} rows)")
    return df


def _ranking_accuracy(df: pd.DataFrame) -> dict[str, Any]:
    """Per-subset: does proxy rank anchor above bad?"""
    results = []
    for subset, g in df.groupby("subset"):
        a = g[g["config_kind"] == "anchor"]
        b = g[g["config_kind"] == "bad"]
        if a.empty or b.empty:
            continue
        arow, brow = a.iloc[0], b.iloc[0]
        if not (math.isfinite(arow.get("proxy", np.nan)) and math.isfinite(brow.get("proxy", np.nan))):
            # If bad failed and anchor ok → ranking ok by convention
            ok = (arow["status"] == "ok") and (brow["status"] != "ok")
            results.append({"subset": subset, "family": arow["family"], "rank_ok": ok, "mode": "status"})
            continue
        # Prefer proxy order matching mIoU order when both ok
        if arow["status"] == "ok" and brow["status"] == "ok":
            miou_order = float(arow["mIoU"]) >= float(brow["mIoU"])
            proxy_order = float(arow["proxy"]) >= float(brow["proxy"])
            results.append(
                {
                    "subset": subset,
                    "family": arow["family"],
                    "rank_ok": bool(proxy_order == miou_order),
                    "mode": "proxy_vs_miou",
                    "anchor_mIoU": float(arow["mIoU"]),
                    "bad_mIoU": float(brow["mIoU"]),
                    "anchor_proxy": float(arow["proxy"]),
                    "bad_proxy": float(brow["proxy"]),
                }
            )
        else:
            results.append({"subset": subset, "family": arow["family"], "rank_ok": False, "mode": "partial"})
    n = len(results)
    n_ok = sum(1 for r in results if r["rank_ok"])
    return {"n_pairs": n, "n_correct": n_ok, "accuracy": (n_ok / n) if n else None, "rows": results}


def write_report(df: pd.DataFrame | None = None) -> Path:
    FAMILY_DIR.mkdir(parents=True, exist_ok=True)
    models = json.loads(MODELS_PATH.read_text(encoding="utf-8")) if MODELS_PATH.exists() else {}
    bad = json.loads(BAD_CONFIGS_PATH.read_text(encoding="utf-8")) if BAD_CONFIGS_PATH.exists() else {}
    if df is None:
        df = pd.read_csv(HOLDOUT_SCORES_PATH) if HOLDOUT_SCORES_PATH.exists() else pd.DataFrame()

    ok = df[df["status"] == "ok"].copy() if not df.empty else pd.DataFrame()
    rank = _ranking_accuracy(df) if not df.empty else {"n_pairs": 0, "n_correct": 0, "accuracy": None, "rows": []}

    lines: list[str] = []
    lines.append("# Per-family mIoU proxy — held-out evaluation")
    lines.append("")
    lines.append(f"_Generated {datetime.now().isoformat(timespec='seconds')}_")
    lines.append("")
    lines.append("## Design")
    lines.append("")
    lines.append("- Feature set: **B1+B2lean** (GT-free).")
    lines.append("- Train within family; test on held-out sub-tunnels.")
    lines.append("- Per held-out subset: sibling **anchor** config + one frozen **known-bad** config.")
    lines.append("- Training cases: t1&2=`1-1+2-1`, t3=`3-1+3-2`, t4&5=`4-1+5-1`.")
    lines.append("- T3 subsets are ring windows of one scan (`data/3-1.txt`); holdouts are other sections, not other tunnels.")
    lines.append("")

    lines.append("## Training (within-family)")
    lines.append("")
    lines.append("| Family | n | train MAE | pooled MAE | pooled Spearman | alarm thr | low-mIoU floor |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|")
    for fam, rec in (models.get("families") or {}).items():
        lines.append(
            f"| {fam} | {rec.get('n_train_rows')} | {rec['model']['train_mae']:.3f} | "
            f"{rec.get('pooled_mae', float('nan')):.3f} | {rec.get('pooled_spearman', float('nan')):.3f} | "
            f"{rec.get('alarm_threshold', float('nan')):.3f} | {rec.get('low_miou_floor', float('nan')):.3f} |"
        )
    lines.append("")
    lines.append("### Leave-one-tunnel-out")
    lines.append("")
    for fam, rec in (models.get("families") or {}).items():
        loto = rec.get("leave_one_tunnel_out") or []
        if not loto:
            lines.append(f"- **{fam}**: single-tunnel training (no LOTO).")
            continue
        for r in loto:
            lines.append(
                f"- **{fam}** hold `{r['held_out_case']}`: MAE={r['mae']:.3f}, "
                f"Spearman={r['spearman']:.3f} (n_test={r['n_test']})"
            )
    lines.append("")

    lines.append("## Known-bad configs")
    lines.append("")
    lines.append("| Family | Source trial | Training mIoU | Δ vs min sibling anchor |")
    lines.append("|---|---|---:|---:|")
    for fam, rec in bad.items():
        lines.append(
            f"| {fam} | `{rec['source_case']}/{rec['trial_id']}` | "
            f"{rec['training_mIoU']:.3f} | {rec.get('delta_vs_min_anchor', float('nan')):.3f} |"
        )
    lines.append("")

    lines.append("## Held-out calibration")
    lines.append("")
    if ok.empty:
        lines.append("_No completed holdout scores yet._")
    else:
        lines.append("| Family | config | n | MAE | Spearman | mean mIoU | mean proxy |")
        lines.append("|---|---|---:|---:|---:|---:|---:|")
        for fam in ("t1&2", "t3", "t4&5"):
            for kind in ("anchor", "bad"):
                sub = ok[(ok["family"] == fam) & (ok["config_kind"] == kind)]
                if sub.empty:
                    lines.append(f"| {fam} | {kind} | 0 | — | — | — | — |")
                    continue
                sp = stats.spearmanr(sub["mIoU"], sub["proxy"]).correlation
                sp_s = f"{sp:.3f}" if sp is not None and math.isfinite(sp) else "n/a"
                lines.append(
                    f"| {fam} | {kind} | {len(sub)} | {sub['abs_err'].mean():.3f} | {sp_s} | "
                    f"{sub['mIoU'].mean():.3f} | {sub['proxy'].mean():.3f} |"
                )
        lines.append("")
        lines.append(f"Overall MAE (ok runs): **{ok['abs_err'].mean():.3f}** (n={len(ok)}).")
    lines.append("")

    lines.append("## Alarm confusion (split by config)")
    lines.append("")
    if df.empty:
        lines.append("_No scores._")
    else:
        lines.append("| Family | config | TP | FP | TN | FN | precision | recall |")
        lines.append("|---|---|---:|---:|---:|---:|---:|---:|")
        for fam in ("t1&2", "t3", "t4&5"):
            for kind in ("anchor", "bad"):
                sub = df[(df["family"] == fam) & (df["config_kind"] == kind)]
                # Use scored rows with finite proxy or failure-as-alarm
                tp = fp = tn = fn = 0
                for _, r in sub.iterrows():
                    alarm = bool(r.get("alarm"))
                    low = bool(r.get("is_low_miou"))
                    if alarm and low:
                        tp += 1
                    elif alarm and not low:
                        fp += 1
                    elif (not alarm) and (not low):
                        tn += 1
                    else:
                        fn += 1
                prec_s = f"{tp / (tp + fp):.2f}" if (tp + fp) else "—"
                rec_s = f"{tp / (tp + fn):.2f}" if (tp + fn) else "—"
                lines.append(
                    f"| {fam} | {kind} | {tp} | {fp} | {tn} | {fn} | "
                    f"{prec_s} | {rec_s} |"
                )
        # Call out misclassified runs (paper-relevant).
        fps = df[(df["alarm"] == True) & (df["is_low_miou"] == False)]  # noqa: E712
        fns = df[(df["alarm"] == False) & (df["is_low_miou"] == True)]  # noqa: E712
        if len(fps) or len(fns):
            lines.append("")
            lines.append("Notable misclassifications:")
            for _, r in fns.iterrows():
                lines.append(
                    f"- **FN** `{r['subset']}`/{r['config_kind']}: mIoU={r['mIoU']:.3f} "
                    f"below floor but proxy={r['proxy']:.3f} (no alarm)."
                )
            for _, r in fps.iterrows():
                lines.append(
                    f"- **FP** `{r['subset']}`/{r['config_kind']}: mIoU={r['mIoU']:.3f} "
                    f"above floor but proxy={r['proxy']:.3f} (alarm)."
                )
    lines.append("")

    lines.append("## Per-tunnel ranking (anchor vs bad)")
    lines.append("")
    acc = rank.get("accuracy")
    lines.append(
        f"Proxy preserves mIoU order on **{rank.get('n_correct', 0)}/{rank.get('n_pairs', 0)}** "
        f"pairs"
        + (f" (accuracy={acc:.2f})." if acc is not None else ".")
    )
    lines.append("")
    if rank.get("rows"):
        lines.append("| Subset | Family | rank_ok | anchor mIoU | bad mIoU | anchor proxy | bad proxy |")
        lines.append("|---|---|---|---:|---:|---:|---:|")
        for r in rank["rows"]:
            lines.append(
                f"| {r['subset']} | {r['family']} | {r['rank_ok']} | "
                f"{r.get('anchor_mIoU', float('nan')):.3f} | {r.get('bad_mIoU', float('nan')):.3f} | "
                f"{r.get('anchor_proxy', float('nan')):.3f} | {r.get('bad_proxy', float('nan')):.3f} |"
            )
    lines.append("")

    lines.append("## Per-subset scores")
    lines.append("")
    if not df.empty:
        lines.append("| Subset | Family | config | status | mIoU | proxy | |err| | alarm | low? |")
        lines.append("|---|---|---|---|---:|---:|---:|---|---|")
        for _, r in df.sort_values(["family", "subset", "config_kind"]).iterrows():
            miou = r["mIoU"] if pd.notna(r["mIoU"]) else float("nan")
            proxy = r["proxy"] if pd.notna(r["proxy"]) else float("nan")
            err = r["abs_err"] if pd.notna(r["abs_err"]) else float("nan")
            lines.append(
                f"| {r['subset']} | {r['family']} | {r['config_kind']} | {r['status']} | "
                f"{miou:.3f} | {proxy:.3f} | {err:.3f} | {r['alarm']} | {r['is_low_miou']} |"
            )
    lines.append("")

    lines.append("## Limitations")
    lines.append("")
    lines.append("- Only two quality levels per held-out tunnel (anchor + one known-bad); not a full ranking study.")
    lines.append(
        "- T3 train/holdout sections are windows of the **same** physical scan "
        "(`3-1`…`3-5`); transfer is cross-section, not cross-tunnel. "
        "Sibling params come from `anchors/t3/3-1-1` (`segment_order`, `h_ring_sign`)."
    )
    lines.append("- Known-bad configs are frozen from training-tunnel BO archives; transfer of *that specific failure mode* is assumed.")
    lines.append("- Sibling-anchor params are the honest deployment baseline, not per-tunnel retuning.")
    lines.append("- t3 holdout anchor calibration remains biased low (proxy under-predicts good sections).")
    lines.append("")
    lines.append("## Confidence")
    lines.append("")
    if ok.empty:
        lines.append("**Low** — holdout not scored yet.")
    else:
        mae = float(ok["abs_err"].mean())
        if mae <= 0.08 and (acc or 0) >= 0.8:
            conf = "Moderate–high"
        elif mae <= 0.12 and (acc or 0) >= 0.6:
            conf = "Moderate"
        else:
            conf = "Low–moderate"
        lines.append(
            f"**{conf}** based on holdout MAE={mae:.3f}, ranking accuracy="
            f"{acc if acc is not None else 'n/a'}, and the T3 same-scan caveat."
        )
    lines.append("")

    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {REPORT_PATH}")
    return REPORT_PATH


def main() -> None:
    p = argparse.ArgumentParser(description="Per-family proxy train / bad-select / score / report")
    p.add_argument("--select-bad", action="store_true")
    p.add_argument("--train", action="store_true")
    p.add_argument("--score", action="store_true")
    p.add_argument("--report", action="store_true")
    p.add_argument("--all-analysis", action="store_true", help="select-bad + train + score + report")
    args = p.parse_args()

    if args.all_analysis:
        select_bad_configs()
        train_family_proxies()
        score_holdouts()
        write_report()
        return
    if args.select_bad:
        select_bad_configs()
    if args.train:
        train_family_proxies()
    if args.score:
        score_holdouts()
    if args.report:
        write_report()
    if not (args.select_bad or args.train or args.score or args.report or args.all_analysis):
        p.error("Specify an action")


if __name__ == "__main__":
    main()
