#!/usr/bin/env python3
"""Score the published 54 holdout runs with the bo-bayes lean proxy."""

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
from bo.paths import BAYES_PKG, ELEGANT_PKG, FULL_STAGE_PKG, REPO_ROOT
from bo.elegant.features import ANCHOR_PARAMS, CANDIDATE, extract_lean  # noqa: E402
from bo.unified.spaces import sibling_anchor_case  # noqa: E402
from bo.bayes.train_proxy import ALARM_THRESHOLD, predict  # noqa: E402

OUT_DIR = BAYES_PKG
MODELS = OUT_DIR / "models.json"
HOLDOUT_CSV = OUT_DIR / "holdout_scores.csv"
# Reuse published holdout run inventory (paths + GT mIoU); do not re-run holdouts.
V2_HOLDOUT = ELEGANT_PKG / "family" / "holdout_scores_v2.csv"
FULL_HOLDOUT = FULL_STAGE_PKG / "holdout_scores.csv"

POC_PANEL = {"4-4", "1-5", "3-2", "1-4", "3-5", "4-3", "4-1", "3-4", "2-2"}
TAU_ALARM = 0.5
TAU_ACCEPT = 0.7


def _params_for(subset: str) -> Path:
    if subset in ANCHOR_PARAMS:
        return ANCHOR_PARAMS[subset]
    return ANCHOR_PARAMS[sibling_anchor_case(subset)]


def main() -> None:
    models = json.loads(MODELS.read_text(encoding="utf-8"))
    model = models["model"]
    # Prefer full-stage inventory (has proxy_v2 etc.); fall back to v2.
    src = FULL_HOLDOUT if FULL_HOLDOUT.exists() else V2_HOLDOUT
    base = pd.read_csv(src)

    rows = []
    for _, r in base.iterrows():
        path = REPO_ROOT / str(r["path"])
        subset = str(r["subset"])
        if not path.exists():
            raise SystemExit(f"Missing holdout path {path}")
        params = _params_for(subset)
        metrics = extract_lean(path, params_dir=params)
        # Prefer published feature values when present (stable residual backfill).
        feat = {}
        for k in CANDIDATE:
            if k in r and pd.notna(r[k]):
                feat[k] = float(r[k])
            else:
                v = float(metrics.get(k, 0.0))
                feat[k] = v if np.isfinite(v) else 0.0
        df = pd.DataFrame([{**feat}])
        proxy = float(predict(model, df)[0])
        rows.append(
            {
                "subset": subset,
                "family": str(r["family"]),
                "config_kind": str(r["config_kind"]),
                "run_id": str(r["run_id"]),
                "path": str(r["path"]),
                "status": str(r["status"]),
                "mIoU": float(r["mIoU"]),
                "proxy": proxy,
                "abs_err": abs(proxy - float(r["mIoU"])),
                "alarm": proxy < TAU_ALARM,
                **feat,
            }
        )

    hs = pd.DataFrame(rows)
    hs = hs[hs["status"] == "ok"].copy()
    hs.to_csv(HOLDOUT_CSV, index=False)

    y = hs["mIoU"].to_numpy()
    pred = hs["proxy"].to_numpy()
    sp = float(stats.spearmanr(y, pred).correlation or 0.0)
    mae = float(mean_absolute_error(y, pred))
    fam_mae = {
        fam: float(mean_absolute_error(g["mIoU"], g["proxy"]))
        for fam, g in hs.groupby("family")
    }
    anchors = hs[hs["config_kind"] == "anchor"]
    bads = hs[hs["config_kind"] == "bad"]
    tp = int((bads["proxy"] < TAU_ALARM).sum())
    fp = int((anchors["proxy"] < TAU_ALARM).sum())

    # Dual-gate PoC panel
    panel = anchors[(anchors["proxy"] >= TAU_ALARM) & (anchors["proxy"] < TAU_ACCEPT) & (anchors["mIoU"] < TAU_ACCEPT)]
    panel_set = set(panel["subset"].tolist())

    print(f"Wrote {HOLDOUT_CSV} n={len(hs)}")
    print(f"Spearman={sp:.3f} MAE={mae:.3f} fam_mae={fam_mae}")
    print(f"Alarm TP={tp}/{len(bads)} FP={fp}/{len(anchors)}")
    print(f"PoC panel ({len(panel_set)}): {sorted(panel_set)}")
    print(f"Panel match published: {panel_set == POC_PANEL}")


if __name__ == "__main__":
    main()
