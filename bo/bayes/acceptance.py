#!/usr/bin/env python3
"""Acceptance report: hard PoC-panel + alarm constraints vs published structure."""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.metrics import mean_absolute_error

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))
from bo.paths import BAYES_PKG

OUT_DIR = BAYES_PKG
MODELS = OUT_DIR / "models.json"
ABLATION = OUT_DIR / "ablation.json"
HOLDOUT = OUT_DIR / "holdout_scores.csv"
REPORT = OUT_DIR / "acceptance_report.md"

POC_PANEL = {"4-4", "1-5", "3-2", "1-4", "3-5", "4-3", "4-1", "3-4", "2-2"}
TAU_ALARM = 0.5
TAU_ACCEPT = 0.7

# Published reference numbers (Sobol-only campaign).
PUB = {
    "train_mae": 0.129,
    "train_spearman": 0.853,
    "lolo_mae": 0.156,
    "lolo_spearman": 0.717,
    "holdout_mae": 0.071,
    "holdout_spearman": 0.848,
    "coef": {
        "depth_nan_ratio": -0.174,
        "denoise_retained_ratio": -0.392,
        "sam_fill_rate": 0.471,
        "det_row_residual_px": -0.112,
        "det_row_gated": 0.127,
    },
    "intercept": 0.478,
}


def main() -> None:
    models = json.loads(MODELS.read_text(encoding="utf-8"))
    abl = json.loads(ABLATION.read_text(encoding="utf-8"))
    hs = pd.read_csv(HOLDOUT)
    lean = models["model"]
    lolo = models["lolo_cv"]
    perm = models["permutation"]

    anchors = hs[hs["config_kind"] == "anchor"]
    bads = hs[hs["config_kind"] == "bad"]
    tp = int((bads["proxy"] < TAU_ALARM).sum())
    fp = int((anchors["proxy"] < TAU_ALARM).sum())
    panel = anchors[
        (anchors["proxy"] >= TAU_ALARM)
        & (anchors["proxy"] < TAU_ACCEPT)
        & (anchors["mIoU"] < TAU_ACCEPT)
    ]
    panel_set = set(panel["subset"].tolist())

    hold_sp = float(stats.spearmanr(hs["mIoU"], hs["proxy"]).correlation or 0.0)
    hold_mae = float(mean_absolute_error(hs["mIoU"], hs["proxy"]))

    variants = {v["set"]: v for v in abl["variants"]}
    lean_lolo = variants.get("Lean", {}).get("lolo_spearman", float("nan"))
    ev_lolo = variants.get("Evidence", {}).get("lolo_spearman", float("nan"))
    co_lolo = variants.get("Coherence", {}).get("lolo_spearman", float("nan"))
    full_lolo = variants.get("Evidence+Coherence", {}).get("lolo_spearman", float("nan"))

    hard_panel = panel_set == POC_PANEL
    hard_alarm = tp == len(bads) == 27 and fp == 0
    structural = {
        "lean_best_or_near_lolo": lean_lolo >= full_lolo - 0.05,
        "coherence_gt_evidence": co_lolo > ev_lolo,
        "perm_pass": bool(perm.get("pass")),
    }

    lines = [
        "# Acceptance report — bo-bayes Bayesian exploration",
        "",
        f"- created_at: {datetime.now().isoformat()}",
        f"- n_train: {models['n_train']}",
        f"- lean features: {models['lean_features']}",
        "",
        "## Hard constraints",
        "",
        f"- PoC panel identical: **{'PASS' if hard_panel else 'FAIL'}**",
        f"  - expected: `{sorted(POC_PANEL)}`",
        f"  - observed: `{sorted(panel_set)}`",
        f"  - missing: `{sorted(POC_PANEL - panel_set)}`",
        f"  - extra: `{sorted(panel_set - POC_PANEL)}`",
        f"- Alarm 27/27 TP, 0 FP at τ={TAU_ALARM}: **{'PASS' if hard_alarm else 'FAIL'}** "
        f"(TP={tp}/{len(bads)}, FP={fp}/{len(anchors)})",
        "",
        "## Structural checks",
        "",
    ]
    for k, v in structural.items():
        lines.append(f"- {k}: **{'PASS' if v else 'FAIL'}**")

    lines += [
        "",
        "## Drift vs published Sobol-only numbers",
        "",
        "| Metric | Published | Bayes | Δ |",
        "|---|---:|---:|---:|",
        f"| Train MAE | {PUB['train_mae']:.3f} | {lean['train_mae']:.3f} | {lean['train_mae']-PUB['train_mae']:+.3f} |",
        f"| Train Spearman | {PUB['train_spearman']:.3f} | {lean['train_spearman']:.3f} | {lean['train_spearman']-PUB['train_spearman']:+.3f} |",
        f"| LOLO MAE | {PUB['lolo_mae']:.3f} | {lolo['lolo_mae']:.3f} | {lolo['lolo_mae']-PUB['lolo_mae']:+.3f} |",
        f"| LOLO Spearman | {PUB['lolo_spearman']:.3f} | {lolo['lolo_spearman']:.3f} | {lolo['lolo_spearman']-PUB['lolo_spearman']:+.3f} |",
        f"| Holdout MAE | {PUB['holdout_mae']:.3f} | {hold_mae:.3f} | {hold_mae-PUB['holdout_mae']:+.3f} |",
        f"| Holdout Spearman | {PUB['holdout_spearman']:.3f} | {hold_sp:.3f} | {hold_sp-PUB['holdout_spearman']:+.3f} |",
        f"| Intercept | {PUB['intercept']:.3f} | {lean['intercept']:.3f} | {lean['intercept']-PUB['intercept']:+.3f} |",
        "",
        "### Coefficients (z-scored)",
        "",
        "| Feature | Published | Bayes | Δ |",
        "|---|---:|---:|---:|",
    ]
    for f, c in zip(lean["features"], lean["coef"]):
        pub = PUB["coef"].get(f, float("nan"))
        lines.append(f"| {f} | {pub:.3f} | {c:.3f} | {c-pub:+.3f} |")

    lines += [
        "",
        "## Ablation LOLO Spearman",
        "",
        f"- Evidence: {ev_lolo:.3f}",
        f"- Coherence: {co_lolo:.3f}",
        f"- Evidence+Coherence: {full_lolo:.3f}",
        f"- Lean: {lean_lolo:.3f}",
        "",
        f"## Overall: **{'ACCEPT' if hard_panel and hard_alarm else 'REJECT — raise N0 / regenerate GP tail'}**",
        "",
    ]
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    if not (hard_panel and hard_alarm):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
