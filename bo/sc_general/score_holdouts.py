#!/usr/bin/env python3
"""Stage 2: score 54 holdouts with the frozen SC-general package.

Writes:
  data/sc-general/stage2/holdout_scores.csv
  data/sc-general/stage2/holdout_metrics.json
  data/sc-general/stage2/band_check.json
  data/sc-general/stage2/validation_gate.md
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
from sklearn.metrics import mean_absolute_error

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from bo.runtime.clustered_stats import subset_bootstrap_spearman  # noqa: E402
from bo.runtime.ridge import fit_ridge, predict  # noqa: E402

STAGE2 = _REPO / "data" / "sc-general" / "stage2"
HOLDOUT_TABLE = STAGE2 / "holdout_table.csv"
MODELS = _REPO / "bo" / "sc_general" / "models.json"
OUT_SCORES = STAGE2 / "holdout_scores.csv"
OUT_METRICS = STAGE2 / "holdout_metrics.json"
OUT_BAND = STAGE2 / "band_check.json"
OUT_GATE = STAGE2 / "validation_gate.md"

PAPER_PANEL = ["1-4", "1-5", "2-2", "3-2", "3-4", "3-5", "4-1", "4-3", "4-4"]
PUBLISHED = {
    "train_mae": 0.098,
    "train_spearman": 0.877,
    "lolo_mae": 0.143,
    "lolo_spearman": 0.678,
    "holdout_mae": 0.086,
    "holdout_spearman": 0.827,
}


def spearman(y: np.ndarray, p: np.ndarray) -> float:
    if len(y) < 3:
        return float("nan")
    r, _ = stats.spearmanr(y, p)
    return float(r)


def pair_rank(hs: pd.DataFrame) -> dict[str, Any]:
    wins = 0
    n = 0
    for subset, g in hs.groupby("subset"):
        a = g[g["config_kind"] == "anchor"]
        b = g[g["config_kind"] == "bad"]
        if len(a) != 1 or len(b) != 1:
            continue
        n += 1
        if float(a["proxy"].iloc[0]) > float(b["proxy"].iloc[0]):
            wins += 1
    return {"wins": wins, "n": n, "pass": wins == n and n == 27}


def alarm_at_tau(hs: pd.DataFrame, tau: float) -> dict[str, Any]:
    anchors = hs[hs["config_kind"] == "anchor"]
    bads = hs[hs["config_kind"] == "bad"]
    tp = int((bads["proxy"] < tau).sum())
    fp = int((anchors["proxy"] < tau).sum())
    return {
        "tau": float(tau),
        "tp": tp,
        "fp": fp,
        "n_bad": int(len(bads)),
        "n_anchor": int(len(anchors)),
        "pass": tp == len(bads) and fp == 0,
    }


def tau_sweep(hs: pd.DataFrame, lo: float = 0.4, hi: float = 0.6, step: float = 0.01) -> list[dict]:
    rows = []
    t = lo
    while t <= hi + 1e-12:
        rows.append(alarm_at_tau(hs, round(t, 4)))
        t += step
    return rows


def per_family_vs_pooled(hs: pd.DataFrame, models: dict) -> dict[str, Any]:
    """Wilcoxon on subset-aggregated abs error: pooled vs per-family refit scorers."""
    feats = models["lean_features"]
    fam_models = models["per_family_models"]
    uni_abs = []
    fam_abs = []
    for subset, g in hs.groupby("subset"):
        fam = str(g["family"].iloc[0])
        y = g["mIoU"].to_numpy(dtype=float)
        uni = g["proxy"].to_numpy(dtype=float)
        fam_pred = predict(fam_models[fam], g)
        uni_abs.append(float(np.mean(np.abs(uni - y))))
        fam_abs.append(float(np.mean(np.abs(fam_pred - y))))
    uni_abs_a = np.asarray(uni_abs)
    fam_abs_a = np.asarray(fam_abs)
    w = stats.wilcoxon(fam_abs_a, uni_abs_a, alternative="two-sided")
    return {
        "n_subsets": int(len(uni_abs_a)),
        "unified_subset_mae": float(np.mean(uni_abs_a)),
        "perfamily_subset_mae": float(np.mean(fam_abs_a)),
        "wilcoxon_W": float(w.statistic),
        "wilcoxon_p": float(w.pvalue),
        "features": feats,
        "unit": "subset-aggregated mean abs error (n=27)",
    }


def band_check(hs: pd.DataFrame) -> dict[str, Any]:
    anchors = hs[hs["config_kind"] == "anchor"].copy()
    in_band = anchors[
        (anchors["proxy"] >= 0.5) & (anchors["proxy"] <= 0.7) & (anchors["mIoU"] < 0.7)
    ]
    cases = sorted(in_band["subset"].astype(str).tolist())
    paper = set(PAPER_PANEL)
    return {
        "criteria": "anchor proxy in [0.5, 0.7] and GT mIoU < 0.7",
        "n_in_band": len(cases),
        "in_band_cases": cases,
        "paper_panel": PAPER_PANEL,
        "intersection_with_paper": sorted(paper & set(cases)),
        "paper_only": sorted(paper - set(cases)),
        "new_only": sorted(set(cases) - paper),
        "in_band_rows": in_band[
            ["subset", "family", "mIoU", "proxy"]
        ].to_dict(orient="records"),
    }


def apply_gate(train: dict, metrics: dict, models: dict) -> dict[str, Any]:
    feats = models["lean_features"]
    has_sc = any(
        f.split("@")[0]
        in {"correspondence_f1", "boundary_explained_edge", "chamfer_sym_px"}
        for f in feats
    )
    has_krow = any(
        f.startswith("det_row") or "k_row" in f or "uniform_k" in f for f in feats
    )
    lofo_ok = float(train["lolo_spearman"]) >= PUBLISHED["lolo_spearman"]
    hold_ok = (
        float(metrics["spearman"]) >= PUBLISHED["holdout_spearman"]
        or float(metrics["mae"]) <= PUBLISHED["holdout_mae"]
    )
    pair_ok = bool(metrics["pair_rank"]["pass"])
    alarm_ok = any(r["pass"] for r in metrics["tau_sweep"])
    preferred = metrics["alarm_0.5"]["pass"]
    checks = {
        "lolo_spearman_ge_0.678": lofo_ok,
        "holdout_spearman_or_mae": hold_ok,
        "pair_rank_27_27": pair_ok,
        "alarm_some_tau_in_0.4_0.6": alarm_ok,
        "lean_has_sc_general": has_sc,
        "lean_no_krow": not has_krow,
    }
    return {
        "pass": all(checks.values()),
        "checks": checks,
        "alarm_at_0.5_preferred": preferred,
        "lean_features": feats,
        "deployment_arm": models.get("deployment_arm"),
        "published": PUBLISHED,
        "observed": {
            "lolo_spearman": train["lolo_spearman"],
            "holdout_spearman": metrics["spearman"],
            "holdout_mae": metrics["mae"],
            "pair_rank": metrics["pair_rank"],
            "alarm_0.5": metrics["alarm_0.5"],
            "tau_pass": [r["tau"] for r in metrics["tau_sweep"] if r["pass"]],
        },
    }


def write_gate_md(gate: dict, metrics: dict, path: Path) -> None:
    lines = [
        f"# Stage-2 validation gate — {'PASS' if gate['pass'] else 'FAIL'}",
        "",
        f"- deployment_arm: `{gate['deployment_arm']}`",
        f"- lean_features: `{gate['lean_features']}`",
        "",
        "| check | result |",
        "|---|---|",
    ]
    for k, v in gate["checks"].items():
        lines.append(f"| {k} | {'PASS' if v else 'FAIL'} |")
    lines += [
        "",
        "## Observed vs published (bayes)",
        "",
        f"- LOFO Spearman: {gate['observed']['lolo_spearman']:.3f} (pub {PUBLISHED['lolo_spearman']})",
        f"- Holdout Spearman: {gate['observed']['holdout_spearman']:.3f} "
        f"(pub {PUBLISHED['holdout_spearman']}; CI95 {metrics['bootstrap']['ci95']})",
        f"- Holdout MAE: {gate['observed']['holdout_mae']:.4f} (pub {PUBLISHED['holdout_mae']})",
        f"- PairRank: {gate['observed']['pair_rank']['wins']}/{gate['observed']['pair_rank']['n']}",
        f"- Alarm @0.5: TP={gate['observed']['alarm_0.5']['tp']} "
        f"FP={gate['observed']['alarm_0.5']['fp']} "
        f"(preferred={'yes' if gate['alarm_at_0.5_preferred'] else 'no'})",
        f"- Passing tau in [0.4,0.6]: {gate['observed']['tau_pass']}",
        "",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    if not HOLDOUT_TABLE.exists():
        raise SystemExit(f"missing {HOLDOUT_TABLE}")
    if not MODELS.exists():
        raise SystemExit(f"missing {MODELS}; run train_proxy.py first")

    models = json.loads(MODELS.read_text(encoding="utf-8"))
    hs = pd.read_csv(HOLDOUT_TABLE)
    feats = models["lean_features"]
    for f in feats:
        if f not in hs.columns:
            raise SystemExit(f"holdout missing feature {f}")
        hs[f] = hs[f].astype(float)

    hs["proxy"] = predict(models["model"], hs)
    hs["abs_err"] = (hs["proxy"] - hs["mIoU"]).abs()

    mae = float(mean_absolute_error(hs["mIoU"], hs["proxy"]))
    sp = spearman(hs["mIoU"].to_numpy(), hs["proxy"].to_numpy())
    fam_mae = {
        str(fam): float(mean_absolute_error(g["mIoU"], g["proxy"]))
        for fam, g in hs.groupby("family")
    }
    boot = subset_bootstrap_spearman(hs, n_boot=2000, seed=0)
    pr = pair_rank(hs)
    alarm05 = alarm_at_tau(hs, 0.5)
    sweep = tau_sweep(hs)
    wil = per_family_vs_pooled(hs, models)
    band = band_check(hs)

    metrics = {
        "created_at": datetime.now().isoformat(),
        "n": int(len(hs)),
        "mae": mae,
        "spearman": sp,
        "family_mae": fam_mae,
        "bootstrap": boot,
        "pair_rank": pr,
        "alarm_0.5": alarm05,
        "tau_sweep": sweep,
        "wilcoxon_pooled_vs_family": wil,
        "deployment_arm": models["deployment_arm"],
        "lean_features": feats,
    }

    train_summary = json.loads((STAGE2 / "train_summary.json").read_text(encoding="utf-8"))
    gate = apply_gate(train_summary, metrics, models)

    STAGE2.mkdir(parents=True, exist_ok=True)
    hs.to_csv(OUT_SCORES, index=False)
    OUT_METRICS.write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    OUT_BAND.write_text(json.dumps(band, indent=2) + "\n", encoding="utf-8")
    write_gate_md(gate, metrics, OUT_GATE)
    (STAGE2 / "gate_result.json").write_text(
        json.dumps(gate, indent=2) + "\n", encoding="utf-8"
    )

    print(
        f"holdout mae={mae:.4f} sp={sp:.3f} "
        f"pair={pr['wins']}/{pr['n']} alarm@0.5 TP={alarm05['tp']} FP={alarm05['fp']}"
    )
    print(f"gate={'PASS' if gate['pass'] else 'FAIL'}")
    print(f"band n={band['n_in_band']} intersection={band['intersection_with_paper']}")
    print(f"wrote {OUT_SCORES}")
    print(f"wrote {OUT_GATE}")


if __name__ == "__main__":
    main()
