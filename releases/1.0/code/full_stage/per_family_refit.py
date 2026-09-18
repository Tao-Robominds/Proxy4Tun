#!/usr/bin/env python3
"""Per-family vs pooled Ridge refit on the 120-row full-stage training table.

Same lean features as the frozen unified model; fits one RidgeCV per family
(40 rows each) and scores the 54 holdouts. Does not retrain or overwrite
models.json — results go to family_refit.json only.

Single-instance gate (required before full run):
  ./venv/bin/python bo-full-stage/per_family_refit.py --gate
  # prove staggered alone; then:
  ./venv/bin/python bo-full-stage/per_family_refit.py
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

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))
from bo.paths import REPO_ROOT, FULL_STAGE_PKG
from bo.full_stage.train_proxy import calibrate_alarm, fit_ridge, predict

OUT_DIR = FULL_STAGE_PKG
TRAIN_CSV = OUT_DIR / "training_table.csv"
HOLDOUT_CSV = OUT_DIR / "holdout_scores.csv"
MODELS = OUT_DIR / "models.json"
OUT_JSON = OUT_DIR / "family_refit.json"
GATE_MD = OUT_DIR / "family_refit_gate.md"

GATE_FAMILY = "staggered"


def _holdout_metrics(
    hold: pd.DataFrame,
    preds: np.ndarray,
    *,
    alarm_thr: float | dict[str, float],
    low_floor: float | dict[str, float],
) -> dict[str, Any]:
    df = hold.copy()
    df["proxy"] = preds
    df = df[np.isfinite(df["proxy"])].copy()
    y = df["mIoU"].to_numpy(dtype=float)
    p = df["proxy"].to_numpy(dtype=float)
    mae = float(mean_absolute_error(y, p))
    sp = float(stats.spearmanr(y, p).correlation or 0.0)

    # Alarm: proxy <= thr flags low quality; GT-low = mIoU <= floor
    alarms = []
    labels = []
    for _, row in df.iterrows():
        fam = str(row["family"])
        thr = float(alarm_thr[fam] if isinstance(alarm_thr, dict) else alarm_thr)
        floor = float(low_floor[fam] if isinstance(low_floor, dict) else low_floor)
        alarms.append(bool(row["proxy"] <= thr))
        labels.append(bool(row["mIoU"] <= floor))
    alarms_a = np.asarray(alarms)
    labels_a = np.asarray(labels)
    tp = int(np.sum(alarms_a & labels_a))
    fp = int(np.sum(alarms_a & ~labels_a))
    fn = int(np.sum(~alarms_a & labels_a))
    prec = tp / (tp + fp) if (tp + fp) else 0.0
    rec = tp / (tp + fn) if (tp + fn) else 0.0

    # Anchor vs bad ranking (config_kind)
    rank_ok = rank_total = 0
    if "config_kind" in df.columns and "subset" in df.columns:
        for subset, g in df.groupby("subset"):
            a = g[g["config_kind"] == "anchor"]
            b = g[g["config_kind"] == "bad"]
            if len(a) == 1 and len(b) == 1:
                rank_total += 1
                if float(a["proxy"].iloc[0]) > float(b["proxy"].iloc[0]):
                    rank_ok += 1

    fam_mae = {
        fam: float(mean_absolute_error(g["mIoU"], g["proxy"]))
        for fam, g in df.groupby("family")
    }
    return {
        "n": int(len(df)),
        "mae": mae,
        "spearman": sp,
        "family_mae": fam_mae,
        "rank_ok": rank_ok,
        "rank_total": rank_total,
        "rank_acc": float(rank_ok / rank_total) if rank_total else float("nan"),
        "alarm_precision": float(prec),
        "alarm_recall": float(rec),
        "alarm_tp": tp,
        "alarm_fp": fp,
        "alarm_fn": fn,
    }


def fit_pooled(train: pd.DataFrame, features: list[str]) -> dict[str, Any]:
    model = fit_ridge(train, features)
    pred = predict(model, train)
    alarm = calibrate_alarm(train["mIoU"].to_numpy(), pred)
    floor = float(np.quantile(train["mIoU"].to_numpy(), 0.33))
    return {"model": model, "alarm": alarm, "low_floor": floor}


def fit_per_family(
    train: pd.DataFrame, features: list[str], families: list[str] | None = None
) -> dict[str, Any]:
    families = families or sorted(train["family"].unique())
    models: dict[str, Any] = {}
    alarms: dict[str, float] = {}
    floors: dict[str, float] = {}
    n_train: dict[str, int] = {}
    for fam in families:
        sub = train[train["family"] == fam].dropna(subset=features + ["mIoU"])
        if len(sub) < 5:
            raise RuntimeError(f"Family {fam} has only {len(sub)} rows; need ≥5")
        m = fit_ridge(sub, features)
        models[fam] = m
        pred = predict(m, sub)
        alarms[fam] = calibrate_alarm(sub["mIoU"].to_numpy(), pred)
        floors[fam] = float(np.quantile(sub["mIoU"].to_numpy(), 0.33))
        n_train[fam] = int(len(sub))
    return {
        "models": models,
        "alarms": alarms,
        "low_floors": floors,
        "n_train_per_family": n_train,
    }


def score_pooled(hold: pd.DataFrame, bundle: dict[str, Any], features: list[str]) -> dict[str, Any]:
    ok = hold.dropna(subset=features + ["mIoU"]).copy()
    preds = predict(bundle["model"], ok)
    return _holdout_metrics(
        ok, preds, alarm_thr=bundle["alarm"], low_floor=bundle["low_floor"]
    )


def score_per_family(
    hold: pd.DataFrame, bundle: dict[str, Any], features: list[str]
) -> dict[str, Any]:
    ok = hold.dropna(subset=features + ["mIoU"]).copy()
    preds = np.full(len(ok), np.nan)
    for i, (_, row) in enumerate(ok.iterrows()):
        fam = str(row["family"])
        if fam not in bundle["models"]:
            continue
        preds[i] = float(predict(bundle["models"][fam], pd.DataFrame([row]))[0])
    return _holdout_metrics(
        ok,
        preds,
        alarm_thr=bundle["alarms"],
        low_floor=bundle["low_floors"],
    )


def run_gate() -> dict[str, Any]:
    """Single-instance validation: staggered family only."""
    models_payload = json.loads(MODELS.read_text(encoding="utf-8"))
    features = list(models_payload["lean_features"])
    train = pd.read_csv(TRAIN_CSV)
    hold = pd.read_csv(HOLDOUT_CSV)
    for k in features:
        if k not in train.columns or k not in hold.columns:
            raise SystemExit(f"Missing feature {k}")

    tr = train[train["family"] == GATE_FAMILY].copy()
    ho = hold[hold["family"] == GATE_FAMILY].copy()
    if len(tr) < 5 or len(ho) < 2:
        raise SystemExit(f"Gate family {GATE_FAMILY}: train={len(tr)} hold={len(ho)}")

    bundle = fit_per_family(tr, features, families=[GATE_FAMILY])
    metrics = score_per_family(ho, bundle, features)

    proof = {
        "case": GATE_FAMILY,
        "command": "./venv/bin/python bo-full-stage/per_family_refit.py --gate",
        "n_train": int(len(tr)),
        "n_holdout": int(len(ho)),
        "features": features,
        "metrics": metrics,
        "pass_criteria": {
            "finite_mae": bool(np.isfinite(metrics["mae"])),
            "rank_perfect_or_near": metrics["rank_ok"] >= max(0, metrics["rank_total"] - 1),
            "n_train_40": len(tr) == 40,
        },
        "output": str(GATE_MD.relative_to(REPO_ROOT)),
    }
    all_pass = all(proof["pass_criteria"].values())
    proof["status"] = "PASS" if all_pass else "FAIL"

    lines = [
        "# Single-instance gate — per-family refit",
        "",
        f"- Family: `{GATE_FAMILY}` (representative of 40-row family fit)",
        f"- Command: `{proof['command']}`",
        f"- n_train={proof['n_train']}, n_holdout={proof['n_holdout']}",
        f"- lean features: {features}",
        "",
        "## Metrics",
        "",
        f"| Metric | Value |",
        f"|---|---:|",
        f"| MAE | {metrics['mae']:.3f} |",
        f"| Spearman | {metrics['spearman']:.3f} |",
        f"| Rank (anchor>bad) | {metrics['rank_ok']}/{metrics['rank_total']} |",
        f"| Alarm P/R | {metrics['alarm_precision']:.2f}/{metrics['alarm_recall']:.2f} "
        f"(TP={metrics['alarm_tp']} FP={metrics['alarm_fp']} FN={metrics['alarm_fn']}) |",
        "",
        "## Pass criteria",
        "",
    ]
    for k, v in proof["pass_criteria"].items():
        lines.append(f"- {'PASS' if v else 'FAIL'}: {k}")
    lines += ["", f"**Overall: {proof['status']}**", ""]
    GATE_MD.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    if not all_pass:
        raise SystemExit("Gate FAILED — do not scale to all families")
    return proof


def run_full() -> dict[str, Any]:
    if not GATE_MD.exists() or "Overall: PASS" not in GATE_MD.read_text(encoding="utf-8"):
        raise SystemExit(
            f"Missing/failed gate proof at {GATE_MD}; run with --gate first"
        )

    models_payload = json.loads(MODELS.read_text(encoding="utf-8"))
    features = list(models_payload["lean_features"])
    train = pd.read_csv(TRAIN_CSV).dropna(subset=features + ["mIoU"])
    hold = pd.read_csv(HOLDOUT_CSV).dropna(subset=features + ["mIoU"])

    pooled = fit_pooled(train, features)
    per_fam = fit_per_family(train, features)

    pooled_hold = score_pooled(hold, pooled, features)
    per_fam_hold = score_per_family(hold, per_fam, features)

    payload = {
        "created_at": datetime.now().isoformat(),
        "features": features,
        "n_train": int(len(train)),
        "n_train_per_family": per_fam["n_train_per_family"],
        "n_holdout": int(len(hold)),
        "gate": str(GATE_MD.relative_to(REPO_ROOT)),
        "pooled": {
            "train_mae": pooled["model"]["train_mae"],
            "train_spearman": pooled["model"]["train_spearman"],
            "alarm_threshold": pooled["alarm"],
            "holdout": pooled_hold,
            "coef": {
                f: float(c)
                for f, c in zip(pooled["model"]["features"], pooled["model"]["coef"])
            },
        },
        "per_family": {
            "alarms": per_fam["alarms"],
            "holdout": per_fam_hold,
            "coef_by_family": {
                fam: {
                    f: float(c)
                    for f, c in zip(m["features"], m["coef"])
                }
                for fam, m in per_fam["models"].items()
            },
            "train_mae_by_family": {
                fam: float(m["train_mae"]) for fam, m in per_fam["models"].items()
            },
        },
        "verdict": {
            "mae_delta_per_family_minus_pooled": float(
                per_fam_hold["mae"] - pooled_hold["mae"]
            ),
            "spearman_delta": float(
                per_fam_hold["spearman"] - pooled_hold["spearman"]
            ),
            "prefer_pooled_for_alarm_recall": bool(
                pooled_hold["alarm_recall"] >= per_fam_hold["alarm_recall"]
            ),
        },
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(
        f"Pooled   MAE={pooled_hold['mae']:.3f} Sp={pooled_hold['spearman']:.3f} "
        f"Alarm P/R={pooled_hold['alarm_precision']:.2f}/{pooled_hold['alarm_recall']:.2f}"
    )
    print(
        f"Per-fam  MAE={per_fam_hold['mae']:.3f} Sp={per_fam_hold['spearman']:.3f} "
        f"Alarm P/R={per_fam_hold['alarm_precision']:.2f}/{per_fam_hold['alarm_recall']:.2f}"
    )
    print(f"Wrote {OUT_JSON}")
    return payload


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--gate",
        action="store_true",
        help="Single-instance staggered gate (must pass before full run)",
    )
    args = p.parse_args()
    if args.gate:
        run_gate()
    else:
        run_full()


if __name__ == "__main__":
    main()
