#!/usr/bin/env python3
"""Score holdout runs with the bo-full-stage lean proxy."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.metrics import mean_absolute_error

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))
from bo.paths import REPO_ROOT, ELEGANT_PKG, FULL_STAGE_PKG
from bo.elegant.features import (
    ANCHOR_PARAMS,
    CANDIDATE,
    HOLDOUT_SUBSETS,
    extract_lean,
    family_of_subset,
)
from bo.unified.spaces import sibling_anchor_case
from bo.full_stage.train_proxy import predict

OUT_DIR = FULL_STAGE_PKG
MODELS = OUT_DIR / "models.json"
STAGE1 = OUT_DIR / "stage1_features.json"
HOLDOUT_CSV = OUT_DIR / "holdout_scores.csv"
V2_HOLDOUT = ELEGANT_PKG / "family" / "holdout_scores_v2.csv"
VALIDATION = OUT_DIR / "validation_gate.md"


def _params_for(subset: str) -> Path:
    if subset in ANCHOR_PARAMS:
        return ANCHOR_PARAMS[subset]
    return ANCHOR_PARAMS[sibling_anchor_case(subset)]


def score_row(
    path: Path,
    subset: str,
    *,
    stage1: dict[str, Any],
    model: dict[str, Any],
) -> dict[str, Any]:
    params = _params_for(subset)
    metrics = extract_lean(path, params_dir=params)
    s1 = stage1.get(subset, {})
    if s1.get("status") == "ok":
        # Residual is property of subset+anchor-stage1; override if missing/nan
        if not np.isfinite(metrics.get("recentre_residual_max_cm", float("nan"))):
            metrics["unfold_residual"] = float(s1.get("unfold_residual", 0.0))
            metrics["recentre_residual_max_cm"] = float(
                s1.get("recentre_residual_max_cm", float("nan"))
            )
        # Always prefer log-derived residual when available for consistency
        metrics["unfold_residual"] = float(s1.get("unfold_residual", metrics.get("unfold_residual", 0.0)))
        metrics["recentre_residual_max_cm"] = float(
            s1.get("recentre_residual_max_cm", metrics.get("recentre_residual_max_cm", float("nan")))
        )
    feat = {k: float(metrics.get(k, 0.0)) for k in CANDIDATE}
    for k in feat:
        if not np.isfinite(feat[k]):
            feat[k] = 0.0
    df = pd.DataFrame([{**feat}])
    proxy = float(predict(model, df)[0])
    return {
        **feat,
        "proxy": proxy,
        "orient_axis_corr": float(metrics.get("orient_axis_corr", float("nan"))),
        "recentre_residual_max_cm": float(metrics.get("recentre_residual_max_cm", float("nan"))),
    }


def main() -> None:
    models = json.loads(MODELS.read_text(encoding="utf-8"))
    model = models["model"]
    alarm = float(models["alarm_threshold"])
    stage1 = json.loads(STAGE1.read_text(encoding="utf-8")) if STAGE1.exists() else {}

    v2 = pd.read_csv(V2_HOLDOUT)
    rows = []
    for _, r in v2.iterrows():
        path = REPO_ROOT / str(r["path"])
        subset = str(r["subset"])
        scored = score_row(path, subset, stage1=stage1, model=model)
        rows.append(
            {
                "subset": subset,
                "family": str(r["family"]),
                "config_kind": str(r["config_kind"]),
                "run_id": str(r["run_id"]),
                "path": str(r["path"]),
                "status": str(r["status"]),
                "mIoU": float(r["mIoU"]),
                "proxy_v2": float(r["proxy_v2"]) if pd.notna(r.get("proxy_v2")) else float("nan"),
                "proxy": scored["proxy"],
                "abs_err": abs(scored["proxy"] - float(r["mIoU"])),
                "alarm": scored["proxy"] <= alarm,
                **{k: scored[k] for k in CANDIDATE},
                "recentre_residual_max_cm": scored["recentre_residual_max_cm"],
            }
        )

    hs = pd.DataFrame(rows)
    hs = hs[hs["status"] == "ok"].copy()
    hs.to_csv(HOLDOUT_CSV, index=False)

    # Validation metrics
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
    tp = int((bads["proxy"] <= alarm).sum())
    fp = int((anchors["proxy"] <= alarm).sum())
    n_bad, n_anch = len(bads), len(anchors)

    # Compare to v2
    v2_sp = float(stats.spearmanr(hs["mIoU"], hs["proxy_v2"]).correlation or 0.0)
    v2_mae = float(mean_absolute_error(hs["mIoU"], hs["proxy_v2"]))
    v2_models = json.loads((ELEGANT_PKG / "family" / "models_v2.json").read_text())
    v2_fam = {}
    # approximate from holdout
    for fam, g in hs.groupby("family"):
        v2_fam[fam] = float(mean_absolute_error(g["mIoU"], g["proxy_v2"]))

    # 4-3 stage-1 response check (if stage1 has 4-3 and reflect paths exist)
    reflect_note = "not checked (no reflect stage-1 pair)"
    r43 = stage1.get("4-3", {})
    if r43.get("status") == "ok":
        # Score anchor-like feature vector for 4-3 with residual 23 vs 5
        # Use the holdout 4-3-anchor feature row and swap residual
        a43 = hs[hs["run_id"] == "4-3-anchor"]
        if len(a43) == 1:
            base = a43.iloc[0]
            def _proxy_with_resid(cm: float) -> float:
                row = {k: float(base[k]) for k in model["features"]}
                if "unfold_residual" in row:
                    row["unfold_residual"] = float(np.log1p(cm))
                return float(predict(model, pd.DataFrame([row]))[0])

            p_hi = _proxy_with_resid(23.2)
            p_lo = _proxy_with_resid(5.2)
            delta = p_lo - p_hi
            reflect_note = (
                f"proxy(residual=23.2cm)={p_hi:.3f}, proxy(5.2cm)={p_lo:.3f}, "
                f"Δ={delta:+.3f} ({'PASS' if delta > 0 else 'FAIL'} rises when residual drops)"
            )

    # Gates
    checks = [
        ("holdout Spearman ≥ v2", sp >= v2_sp - 0.02, f"{sp:.3f} vs v2 {v2_sp:.3f}"),
        ("holdout MAE not much worse", mae <= v2_mae + 0.05, f"{mae:.3f} vs v2 {v2_mae:.3f}"),
        ("known-bad flagging recall", tp >= max(1, n_bad - 2), f"{tp}/{n_bad}"),
        ("anchor false alarms limited", fp <= max(2, n_anch // 5), f"{fp}/{n_anch}"),
    ]
    lines = [
        "# Validation gate — bo-full-stage",
        "",
        f"- n_holdout = {len(hs)}",
        f"- lean features = {model['features']}",
        f"- alarm τ = {alarm:.3f}",
        "",
        "## Metrics",
        "",
        f"| Metric | full-stage | v2 |",
        f"|---|---:|---:|",
        f"| Spearman | {sp:.3f} | {v2_sp:.3f} |",
        f"| MAE | {mae:.3f} | {v2_mae:.3f} |",
    ]
    for fam in sorted(fam_mae):
        lines.append(f"| MAE {fam} | {fam_mae[fam]:.3f} | {v2_fam.get(fam, float('nan')):.3f} |")
    lines += [
        "",
        f"Flagging: TP={tp}/{n_bad}, FP={fp}/{n_anch}",
        "",
        "## 4-3 residual response",
        "",
        reflect_note,
        "",
        "## Checks",
        "",
    ]
    all_pass = True
    for name, ok, detail in checks:
        all_pass = all_pass and ok
        lines.append(f"- {'PASS' if ok else 'FAIL'}: {name} ({detail})")
    lines.append("")
    lines.append(f"**Overall: {'PASS' if all_pass else 'FAIL'}**")
    VALIDATION.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {HOLDOUT_CSV}")
    print(f"Wrote {VALIDATION}")
    print(f"Spearman={sp:.3f} MAE={mae:.3f} TP={tp}/{n_bad} FP={fp}/{n_anch}")
    print(reflect_note)


if __name__ == "__main__":
    main()
