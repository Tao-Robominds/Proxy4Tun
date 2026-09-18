#!/usr/bin/env python3
"""Per-family + pooled cross-family Ridge proxy for bo-unified."""

from __future__ import annotations

import argparse
import json
import math
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

REPO_ROOT = Path(__file__).resolve().parent.parent
BO_DIR = Path(__file__).resolve().parent
FAMILY_DIR = BO_DIR / "family"
sys.path.insert(0, str(BO_DIR))

from blocks import features_for  # noqa: E402
from pipeline import DATA_ROOT  # noqa: E402
from spaces import FAMILY_HOLDOUT_SUBSETS, FAMILY_TRAIN_CASES  # noqa: E402

FEATURE_SET = "B1+B2lean"
FEATURES = features_for(FEATURE_SET)
FAMILY_ONEHOT = ("fam_t12", "fam_t3", "fam_t45")
BAD_CONFIGS_PATH = FAMILY_DIR / "bad_configs.json"
MODELS_PATH = FAMILY_DIR / "models.json"
HOLDOUT_SCORES_PATH = FAMILY_DIR / "holdout_scores.csv"
TRAINING_CSV = FAMILY_DIR / "training_table.csv"
REPORT_PATH = BO_DIR / "report.md"

FAM_TO_OH = {"t1&2": "fam_t12", "t3": "fam_t3", "t4&5": "fam_t45"}


def _safe_scale(scale: np.ndarray, eps: float = 1e-8) -> np.ndarray:
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


def load_training_table() -> pd.DataFrame:
    if not TRAINING_CSV.exists():
        raise FileNotFoundError(f"Missing {TRAINING_CSV}; run bo-unified/ingest.py --table")
    return pd.read_csv(TRAINING_CSV)


def _add_family_onehot(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in FAMILY_ONEHOT:
        out[col] = 0.0
    for fam, col in FAM_TO_OH.items():
        out.loc[out["family"] == fam, col] = 1.0
    return out


def train_proxies() -> dict[str, Any]:
    FAMILY_DIR.mkdir(parents=True, exist_ok=True)
    df = load_training_table()
    payload: dict[str, Any] = {
        "feature_set": FEATURE_SET,
        "features": FEATURES,
        "created_at": datetime.now().isoformat(),
        "families": {},
        "unified": {},
        "provenance": "training_table.csv from data/bo historical campaigns",
    }

    for family in FAMILY_TRAIN_CASES:
        sub = df[df["family"] == family].dropna(subset=FEATURES + ["mIoU"]).copy()
        if sub.empty:
            raise RuntimeError(f"No training rows for {family}")
        model = _fit_ridge(sub, FEATURES)
        pred_train = _predict(model, sub)
        y_train = sub["mIoU"].to_numpy()
        alarm_thr = _calibrate_alarm(y_train, pred_train)
        low_floor = float(np.quantile(y_train, 0.33))
        payload["families"][family] = {
            "train_cases": list(FAMILY_TRAIN_CASES[family]),
            "n_train_rows": int(len(sub)),
            "model": model,
            "pooled_mae": float(mean_absolute_error(y_train, pred_train)),
            "pooled_spearman": float(stats.spearmanr(y_train, pred_train).correlation or 0.0),
            "alarm_threshold": alarm_thr,
            "low_miou_floor": low_floor,
        }
        print(
            f"{family}: n={len(sub)} train_mae={model['train_mae']:.3f} "
            f"alarm={alarm_thr:.3f} floor={low_floor:.3f}"
        )

    # Pooled cross-family model with family one-hot
    all_df = _add_family_onehot(df.dropna(subset=FEATURES + ["mIoU"]).copy())
    u_feats = FEATURES + list(FAMILY_ONEHOT)
    u_model = _fit_ridge(all_df, u_feats)
    u_pred = _predict(u_model, all_df)
    u_y = all_df["mIoU"].to_numpy()
    payload["unified"] = {
        "n_train_rows": int(len(all_df)),
        "features": u_feats,
        "model": u_model,
        "train_mae": float(mean_absolute_error(u_y, u_pred)),
        "train_spearman": float(stats.spearmanr(u_y, u_pred).correlation or 0.0),
        "alarm_threshold": _calibrate_alarm(u_y, u_pred),
        "low_miou_floor": float(np.quantile(u_y, 0.33)),
        "note": "B1+B2lean + family one-hot (fam_t12 / fam_t3 / fam_t45)",
    }
    print(
        f"unified: n={len(all_df)} train_mae={payload['unified']['train_mae']:.3f} "
        f"sp={payload['unified']['train_spearman']:.3f}"
    )

    MODELS_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {MODELS_PATH}")
    return payload


def _load_holdout_run(subset: str, config_kind: str) -> dict[str, Any] | None:
    man_path = DATA_ROOT / f"{subset}-family-proxy" / "manifest.json"
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
    u_model = models["unified"]["model"]
    u_alarm = float(models["unified"]["alarm_threshold"])
    u_floor = float(models["unified"]["low_miou_floor"])
    rows = []
    for family, subsets in FAMILY_HOLDOUT_SUBSETS.items():
        fam_model = models["families"][family]["model"]
        alarm_thr = float(models["families"][family]["alarm_threshold"])
        low_floor = float(models["families"][family]["low_miou_floor"])
        for subset in subsets:
            for kind in ("anchor", "bad"):
                rec = _load_holdout_run(subset, kind)
                base = {
                    "subset": subset,
                    "family": family,
                    "config_kind": kind,
                }
                if rec is None:
                    rows.append(
                        {
                            **base,
                            "status": "missing",
                            "mIoU": np.nan,
                            "proxy_family": np.nan,
                            "proxy_unified": np.nan,
                            "abs_err_family": np.nan,
                            "abs_err_unified": np.nan,
                            "alarm_family": False,
                            "alarm_unified": False,
                            "is_low_miou": False,
                        }
                    )
                    continue
                metrics = rec.get("metrics") or {}
                feat_row = {f: metrics.get(f) for f in FEATURES}
                for col in FAMILY_ONEHOT:
                    feat_row[col] = 1.0 if FAM_TO_OH[family] == col else 0.0
                df_one = pd.DataFrame([feat_row])
                status = rec.get("status")
                miou = rec.get("mIoU")
                if status != "ok" or miou is None or df_one[FEATURES].isna().any(axis=None):
                    rows.append(
                        {
                            **base,
                            "status": status or "failed",
                            "mIoU": miou if miou is not None else np.nan,
                            "proxy_family": np.nan,
                            "proxy_unified": np.nan,
                            "abs_err_family": np.nan,
                            "abs_err_unified": np.nan,
                            "alarm_family": True,
                            "alarm_unified": True,
                            "is_low_miou": True,
                            "note": "pipeline_or_feature_failure",
                        }
                    )
                    continue
                pf = float(_predict(fam_model, df_one)[0])
                pu = float(_predict(u_model, df_one)[0])
                miou_f = float(miou)
                is_low = miou_f <= low_floor
                rows.append(
                    {
                        **base,
                        "status": "ok",
                        "mIoU": miou_f,
                        "proxy_family": pf,
                        "proxy_unified": pu,
                        "abs_err_family": abs(pf - miou_f),
                        "abs_err_unified": abs(pu - miou_f),
                        "alarm_family": pf <= alarm_thr,
                        "alarm_unified": pu <= u_alarm,
                        "is_low_miou": is_low,
                        "alarm_threshold_family": alarm_thr,
                        "alarm_threshold_unified": u_alarm,
                        "low_miou_floor": low_floor,
                        "unified_low_floor": u_floor,
                    }
                )
    out = pd.DataFrame(rows)
    FAMILY_DIR.mkdir(parents=True, exist_ok=True)
    out.to_csv(HOLDOUT_SCORES_PATH, index=False)
    print(f"Wrote {HOLDOUT_SCORES_PATH} ({len(out)} rows)")
    return out


def _ranking_accuracy(df: pd.DataFrame, proxy_col: str) -> dict[str, Any]:
    results = []
    for subset, g in df.groupby("subset"):
        a = g[g["config_kind"] == "anchor"]
        b = g[g["config_kind"] == "bad"]
        if a.empty or b.empty:
            continue
        arow, brow = a.iloc[0], b.iloc[0]
        if not (
            math.isfinite(arow.get(proxy_col, np.nan))
            and math.isfinite(brow.get(proxy_col, np.nan))
        ):
            ok = (arow["status"] == "ok") and (brow["status"] != "ok")
            results.append({"subset": subset, "family": arow["family"], "rank_ok": ok})
            continue
        if arow["status"] == "ok" and brow["status"] == "ok":
            miou_order = float(arow["mIoU"]) >= float(brow["mIoU"])
            proxy_order = float(arow[proxy_col]) >= float(brow[proxy_col])
            results.append(
                {
                    "subset": subset,
                    "family": arow["family"],
                    "rank_ok": bool(proxy_order == miou_order),
                    "anchor_mIoU": float(arow["mIoU"]),
                    "bad_mIoU": float(brow["mIoU"]),
                    "anchor_proxy": float(arow[proxy_col]),
                    "bad_proxy": float(brow[proxy_col]),
                }
            )
        else:
            results.append({"subset": subset, "family": arow["family"], "rank_ok": False})
    n = len(results)
    n_ok = sum(1 for r in results if r["rank_ok"])
    return {"n_pairs": n, "n_correct": n_ok, "accuracy": (n_ok / n) if n else None, "rows": results}


def write_report(df: pd.DataFrame | None = None) -> Path:
    FAMILY_DIR.mkdir(parents=True, exist_ok=True)
    models = json.loads(MODELS_PATH.read_text(encoding="utf-8")) if MODELS_PATH.exists() else {}
    bad = json.loads(BAD_CONFIGS_PATH.read_text(encoding="utf-8")) if BAD_CONFIGS_PATH.exists() else {}
    ingest = {}
    ingest_path = FAMILY_DIR / "ingest_manifest.json"
    if ingest_path.exists():
        ingest = json.loads(ingest_path.read_text(encoding="utf-8"))
    if df is None:
        df = pd.read_csv(HOLDOUT_SCORES_PATH) if HOLDOUT_SCORES_PATH.exists() else pd.DataFrame()

    ok = df[df["status"] == "ok"].copy() if not df.empty else pd.DataFrame()
    rank_f = _ranking_accuracy(df, "proxy_family") if not df.empty else {"n_pairs": 0, "n_correct": 0, "accuracy": None, "rows": []}
    rank_u = _ranking_accuracy(df, "proxy_unified") if not df.empty else {"n_pairs": 0, "n_correct": 0, "accuracy": None, "rows": []}

    lines: list[str] = []
    lines.append("# BO-unified: unified proxy strategy")
    lines.append("")
    lines.append(f"_Generated {datetime.now().isoformat(timespec='seconds')}_")
    lines.append("")
    lines.append("## Design")
    lines.append("")
    lines.append("- Pipeline: **anchors/unified** (staggered / continuous / complex via `parameters_family.json`).")
    lines.append("- Feature set: **B1+B2lean** (GT-free).")
    lines.append("- Training: reused historical `data/bo/<case>-bo-proxy` trials (no fresh BO campaigns).")
    lines.append("- Proxies: **per-family** RidgeCV **and** one **pooled cross-family** RidgeCV (+ family one-hot).")
    lines.append("- Holdouts: 24 subsets with existing `.txt` files (includes new T3 gaps `3-6`…`3-10`).")
    lines.append("- Orientation / seed knobs frozen in unified params; BO overlays touch stages 2–6 only.")
    lines.append("")
    if ingest:
        lines.append("## Training data provenance")
        lines.append("")
        lines.append(f"- Rows: **{ingest.get('n_rows')}** from `{ingest.get('source')}`.")
        lines.append(f"- Justification: {ingest.get('justification')}")
        lines.append(f"- Counts: `{ingest.get('counts_per_case')}`")
        lines.append("")

    lines.append("## Training metrics")
    lines.append("")
    lines.append("| Model | n | train MAE | Spearman | alarm thr | low floor |")
    lines.append("|---|---:|---:|---:|---:|---:|")
    for fam, rec in (models.get("families") or {}).items():
        lines.append(
            f"| family `{fam}` | {rec.get('n_train_rows')} | {rec['model']['train_mae']:.3f} | "
            f"{rec.get('pooled_spearman', float('nan')):.3f} | "
            f"{rec.get('alarm_threshold', float('nan')):.3f} | "
            f"{rec.get('low_miou_floor', float('nan')):.3f} |"
        )
    u = models.get("unified") or {}
    if u:
        lines.append(
            f"| **unified (pooled)** | {u.get('n_train_rows')} | {u.get('train_mae', float('nan')):.3f} | "
            f"{u.get('train_spearman', float('nan')):.3f} | "
            f"{u.get('alarm_threshold', float('nan')):.3f} | "
            f"{u.get('low_miou_floor', float('nan')):.3f} |"
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

    lines.append("## Held-out calibration (family vs unified proxy)")
    lines.append("")
    if ok.empty:
        lines.append("_No completed holdout scores yet._")
    else:
        lines.append("| Family | config | n | MAE_family | MAE_unified | mean mIoU |")
        lines.append("|---|---|---:|---:|---:|---:|")
        for fam in ("t1&2", "t3", "t4&5"):
            for kind in ("anchor", "bad"):
                sub = ok[(ok["family"] == fam) & (ok["config_kind"] == kind)]
                if sub.empty:
                    lines.append(f"| {fam} | {kind} | 0 | — | — | — |")
                    continue
                lines.append(
                    f"| {fam} | {kind} | {len(sub)} | {sub['abs_err_family'].mean():.3f} | "
                    f"{sub['abs_err_unified'].mean():.3f} | {sub['mIoU'].mean():.3f} |"
                )
        lines.append("")
        lines.append(
            f"Overall MAE — family: **{ok['abs_err_family'].mean():.3f}**, "
            f"unified: **{ok['abs_err_unified'].mean():.3f}** (n={len(ok)})."
        )
        lines.append(
            f"Old `bo/family` baseline to beat: pooled MAE **0.099**, ranking **26/26** "
            f"(different holdout set; this run uses 24 available subsets)."
        )
    lines.append("")

    lines.append("## Ranking accuracy (anchor vs bad)")
    lines.append("")
    af, au = rank_f.get("accuracy"), rank_u.get("accuracy")
    lines.append(
        f"- Per-family proxy: **{rank_f.get('n_correct', 0)}/{rank_f.get('n_pairs', 0)}**"
        + (f" (acc={af:.2f})" if af is not None else "")
    )
    lines.append(
        f"- Unified proxy: **{rank_u.get('n_correct', 0)}/{rank_u.get('n_pairs', 0)}**"
        + (f" (acc={au:.2f})" if au is not None else "")
    )
    lines.append("")

    # Gate evidence
    lines.append("## Validation gates")
    lines.append("")
    gate_files = sorted(FAMILY_DIR.glob("gate_*.json"))
    if not gate_files:
        lines.append("_No gate evidence yet._")
    else:
        lines.append("| Case | Kind | mIoU | Passed | Evidence |")
        lines.append("|---|---|---:|---|---|")
        for gp in gate_files:
            g = json.loads(gp.read_text(encoding="utf-8"))
            lines.append(
                f"| {g.get('case')} | {g.get('gate_kind', g.get('config_kind', ''))} | "
                f"{g.get('measured_mIoU', float('nan'))} | {g.get('passed')} | `{gp.name}` |"
            )
    lines.append("")

    lines.append("## Per-subset scores")
    lines.append("")
    if not df.empty:
        lines.append(
            "| Subset | Family | config | status | mIoU | proxy_f | proxy_u | |err_f| | |err_u| |"
        )
        lines.append("|---|---|---|---|---:|---:|---:|---:|---:|")
        for _, r in df.sort_values(["family", "subset", "config_kind"]).iterrows():
            def _f(v: Any) -> str:
                return f"{float(v):.3f}" if pd.notna(v) else "nan"

            lines.append(
                f"| {r['subset']} | {r['family']} | {r['config_kind']} | {r['status']} | "
                f"{_f(r['mIoU'])} | {_f(r['proxy_family'])} | {_f(r['proxy_unified'])} | "
                f"{_f(r['abs_err_family'])} | {_f(r['abs_err_unified'])} |"
            )
    lines.append("")

    lines.append("## Artifacts")
    lines.append("")
    lines.append("- Code: `bo-unified/` (historical `bo/` untouched)")
    lines.append("- Outputs: `data/bo-unified/`")
    lines.append("- Models: `bo-unified/family/models.json`")
    lines.append("- Bad configs: `bo-unified/family/bad_configs.json`")
    lines.append("- Scores: `bo-unified/family/holdout_scores.csv`")
    lines.append("")

    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {REPORT_PATH}")
    return REPORT_PATH


def main() -> None:
    p = argparse.ArgumentParser(description="bo-unified proxy train / score / report")
    p.add_argument("--train", action="store_true")
    p.add_argument("--score", action="store_true")
    p.add_argument("--report", action="store_true")
    p.add_argument("--all-analysis", action="store_true")
    args = p.parse_args()
    if args.all_analysis:
        train_proxies()
        score_holdouts()
        write_report()
        return
    if args.train:
        train_proxies()
    if args.score:
        score_holdouts()
    if args.report:
        write_report()
    if not (args.train or args.score or args.report or args.all_analysis):
        p.error("Specify an action")


if __name__ == "__main__":
    main()
