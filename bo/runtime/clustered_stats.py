#!/usr/bin/env python3
"""Subset-level bootstrap CI and cluster-aware Wilcoxon for the holdout panel."""

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
from bo.runtime.bayes_proxy import LEAN_FEATURES, predict

OUT = Path(__file__).resolve().parent
HOLDOUT = OUT / "holdout_scores.csv"
MODELS = OUT / "models.json"
REPORT = OUT / "clustered_stats.json"


def spearman(y, p) -> float:
    r = stats.spearmanr(y, p).correlation
    return float(r if r is not None and np.isfinite(r) else 0.0)


def subset_bootstrap_spearman(hs: pd.DataFrame, n_boot: int = 2000, seed: int = 0) -> dict:
    """Resample 27 subsets (keeping good/bad pairs), stratified by family."""
    rng = np.random.default_rng(seed)
    families = sorted(hs["family"].unique())
    by_fam = {
        fam: sorted(g["subset"].unique())
        for fam, g in hs.groupby("family")
    }
    vals = []
    for _ in range(n_boot):
        chosen = []
        for fam in families:
            subs = by_fam[fam]
            chosen.extend(rng.choice(subs, size=len(subs), replace=True).tolist())
        boot = hs[hs["subset"].isin(chosen)].copy()
        # Preserve multiplicity of resampled subsets.
        parts = [hs[hs["subset"] == s] for s in chosen]
        boot = pd.concat(parts, ignore_index=True)
        vals.append(spearman(boot["mIoU"].to_numpy(), boot["proxy"].to_numpy()))
    lo, hi = np.percentile(vals, [2.5, 97.5])
    return {
        "spearman": spearman(hs["mIoU"].to_numpy(), hs["proxy"].to_numpy()),
        "ci95": [float(lo), float(hi)],
        "n_boot": n_boot,
        "unit": "subset (good/bad pair preserved; stratified by family)",
    }


def cluster_wilcoxon(hs: pd.DataFrame, models: dict) -> dict:
    """Wilcoxon on subset-aggregated MAE (n=27): unified vs per-family scorer."""
    uni_abs = []
    fam_abs = []
    for subset, g in hs.groupby("subset"):
        fam = str(g["family"].iloc[0])
        fam_model = models["per_family_models"][fam]
        y = g["mIoU"].to_numpy(dtype=float)
        uni = g["proxy"].to_numpy(dtype=float)
        fam_pred = predict(fam_model, g)
        uni_abs.append(float(np.mean(np.abs(uni - y))))
        fam_abs.append(float(np.mean(np.abs(fam_pred - y))))
    uni_abs = np.asarray(uni_abs)
    fam_abs = np.asarray(fam_abs)
    w = stats.wilcoxon(fam_abs, uni_abs, alternative="two-sided")
    return {
        "n_subsets": int(len(uni_abs)),
        "unified_subset_mae": float(np.mean(uni_abs)),
        "perfamily_subset_mae": float(np.mean(fam_abs)),
        "wilcoxon_W": float(w.statistic),
        "wilcoxon_p": float(w.pvalue),
        "unit": "subset-aggregated mean abs error (n=27)",
    }


def main() -> None:
    hs = pd.read_csv(HOLDOUT)
    hs = hs[hs["status"] == "ok"].copy()
    models = json.loads(MODELS.read_text(encoding="utf-8"))
    boot = subset_bootstrap_spearman(hs)
    wil = cluster_wilcoxon(hs, models)
    mae = float(mean_absolute_error(hs["mIoU"], hs["proxy"]))
    out = {
        "holdout_mae": mae,
        "bootstrap": boot,
        "wilcoxon": wil,
        "lean_features": LEAN_FEATURES,
    }
    REPORT.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
