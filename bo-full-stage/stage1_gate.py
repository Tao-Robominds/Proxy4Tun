#!/usr/bin/env python3
"""Stage-1 geometry gate (auxiliary, outside the frozen Ridge proxy).

Follows the phase-alarm pattern: compute a boolean from stage-1 artifacts and
OR it with the proxy alarm without touching Ridge weights.

Signals
-------
- Orientation validity: |orient_axis_corr| < ORIENT_MIN → orient_fail
  (label-free Tier-0; validated at 0.6 in orientation_gate.md).
- Residual diagnostic: recentre_residual_max_cm > RESIDUAL_CM → residual_high
  Used as a *reflection unlock* trigger. Empirically cannot join the quality
  OR-alarm without false-alarming high-mIoU anchors (see stage1_gate.md).

Usage
-----
  ./venv/bin/python bo-full-stage/stage1_gate.py
  ./venv/bin/python bo-full-stage/stage1_gate.py --json-out bo-full-stage/stage1_gate.json
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(OUT_DIR))
sys.path.insert(0, str(REPO_ROOT / "bo-elegant"))

from train_proxy import predict  # noqa: E402

MODELS = OUT_DIR / "models.json"
STAGE1 = OUT_DIR / "stage1_features.json"
HOLDOUT_CSV = OUT_DIR / "holdout_scores.csv"
TRAIN_CSV = OUT_DIR / "training_table.csv"
REPORT_MD = OUT_DIR / "stage1_gate.md"
DEFAULT_JSON = OUT_DIR / "stage1_gate.json"

# Orientation: validated label-free Tier-0 cutoff (orientation_gate.md).
ORIENT_MIN = 0.6
# Residual: unlock / diagnostic candidate (cm). Calibrated in main().
RESIDUAL_CM_CANDIDATES = (10.0, 15.0, 20.0, 25.0)
DEFAULT_RESIDUAL_CM = 10.0


def _finite(x: Any) -> float:
    try:
        v = float(x)
    except (TypeError, ValueError):
        return float("nan")
    return v if math.isfinite(v) else float("nan")


def stage1_signals(
    *,
    residual_cm: float,
    orient_axis_corr: float,
    residual_thr: float = DEFAULT_RESIDUAL_CM,
    orient_min: float = ORIENT_MIN,
) -> dict[str, Any]:
    resid = _finite(residual_cm)
    corr = _finite(orient_axis_corr)
    orient_fail = bool(math.isfinite(corr) and abs(corr) < orient_min)
    residual_high = bool(math.isfinite(resid) and resid > residual_thr)
    # Quality OR companion: orientation only (residual is unlock/diagnostic).
    stage1_quality_alarm = orient_fail
    return {
        "recentre_residual_max_cm": resid,
        "orient_axis_corr": corr,
        "orient_fail": orient_fail,
        "residual_high": residual_high,
        "stage1_quality_alarm": stage1_quality_alarm,
        "unlock_stage1": residual_high or orient_fail,
        "residual_thr_cm": residual_thr,
        "orient_min": orient_min,
    }


def evaluate_alarms(
    df: pd.DataFrame,
    *,
    residual_thr: float,
    proxy_alarm_col: str = "proxy_alarm",
    is_low_col: str = "is_low",
) -> dict[str, Any]:
    """Precision/recall for proxy-only vs proxy OR stage1_quality vs residual-OR."""
    rows = []
    for _, r in df.iterrows():
        sig = stage1_signals(
            residual_cm=float(r["recentre_residual_max_cm"]),
            orient_axis_corr=float(r["orient_axis_corr"]),
            residual_thr=residual_thr,
        )
        proxy_a = bool(r[proxy_alarm_col])
        rows.append(
            {
                **sig,
                "proxy_alarm": proxy_a,
                "alarm_proxy_or_orient": proxy_a or sig["stage1_quality_alarm"],
                "alarm_proxy_or_resid": proxy_a or sig["residual_high"],
                "alarm_proxy_or_either": proxy_a
                or sig["stage1_quality_alarm"]
                or sig["residual_high"],
                "is_low": bool(r[is_low_col]),
                "run_id": r.get("run_id", ""),
                "subset": r.get("subset", ""),
                "config_kind": r.get("config_kind", ""),
                "mIoU": float(r["mIoU"]),
                "proxy": float(r["proxy"]),
            }
        )
    scored = pd.DataFrame(rows)

    def _prf(alarm_col: str) -> dict[str, Any]:
        tp = int(((scored[alarm_col]) & (scored["is_low"])).sum())
        fp = int(((scored[alarm_col]) & (~scored["is_low"])).sum())
        fn = int(((~scored[alarm_col]) & (scored["is_low"])).sum())
        prec = tp / (tp + fp) if (tp + fp) else float("nan")
        rec = tp / (tp + fn) if (tp + fn) else float("nan")
        return {"tp": tp, "fp": fp, "fn": fn, "precision": prec, "recall": rec}

    return {
        "residual_thr_cm": residual_thr,
        "proxy_only": _prf("proxy_alarm"),
        "proxy_or_orient": _prf("alarm_proxy_or_orient"),
        "proxy_or_resid": _prf("alarm_proxy_or_resid"),
        "proxy_or_either": _prf("alarm_proxy_or_either"),
        "scored": scored,
    }


def load_holdout(models: dict[str, Any]) -> pd.DataFrame:
    hs = pd.read_csv(HOLDOUT_CSV)
    alarm_thr = float(models["alarm_threshold"])
    # Prefer CSV residual/orient; fall back to stage1_features.json
    s1 = json.loads(STAGE1.read_text(encoding="utf-8")) if STAGE1.exists() else {}
    rows = []
    for _, r in hs.iterrows():
        subset = str(r["subset"])
        resid = _finite(r.get("recentre_residual_max_cm"))
        # holdout_scores may lack orient_axis_corr; recover from stage1 cache
        corr = _finite(r.get("orient_axis_corr")) if "orient_axis_corr" in r else float("nan")
        if subset in s1 and s1[subset].get("status") == "ok":
            if not math.isfinite(resid):
                resid = _finite(s1[subset].get("recentre_residual_max_cm"))
            if not math.isfinite(corr):
                corr = _finite(s1[subset].get("orient_axis_corr"))
        proxy = float(r["proxy"])
        rows.append(
            {
                "subset": subset,
                "family": str(r["family"]),
                "config_kind": str(r["config_kind"]),
                "run_id": str(r["run_id"]),
                "mIoU": float(r["mIoU"]),
                "proxy": proxy,
                "proxy_alarm": proxy <= alarm_thr,
                # Known-bad flagging uses config_kind == bad (paired evaluation).
                "is_low": str(r["config_kind"]) == "bad",
                "recentre_residual_max_cm": resid,
                "orient_axis_corr": corr,
            }
        )
    return pd.DataFrame(rows)


def load_train_for_resid_stats() -> pd.DataFrame:
    tt = pd.read_csv(TRAIN_CSV)
    return tt


def write_report(
    *,
    holdout_eval: dict[str, Any],
    residual_thr: float,
    train_resid: pd.Series,
    pass_fail: dict[str, Any],
) -> str:
    scored: pd.DataFrame = holdout_eval["scored"]
    anchors = scored[scored["config_kind"] == "anchor"].copy()
    high = anchors[anchors["residual_high"]].sort_values(
        "recentre_residual_max_cm", ascending=False
    )

    lines: list[str] = []
    lines.append("# Stage-1 geometry gate")
    lines.append("")
    lines.append("Auxiliary gate outside the frozen lean Ridge proxy.")
    lines.append("")
    lines.append("## Thresholds")
    lines.append("")
    lines.append(f"- Orientation fail: `|orient_axis_corr| < {ORIENT_MIN}`")
    lines.append(
        f"- Residual high (unlock / diagnostic): `recentre_residual_max_cm > {residual_thr}` cm"
    )
    lines.append(
        "- Quality OR companion: **orientation only** "
        "(`proxy_alarm OR orient_fail`). Residual is **not** OR-ed into the "
        "quality alarm — any threshold that catches 4-3 also false-alarms "
        "high-mIoU anchors (3-8, 3-10)."
    )
    lines.append("")
    lines.append("## Training residual stats")
    lines.append("")
    tr = train_resid.dropna()
    lines.append(f"- n={len(tr)}, min={tr.min():.1f}, median={tr.median():.1f}, max={tr.max():.1f}")
    lines.append(
        f"- fraction > {residual_thr} cm: "
        f"{(tr > residual_thr).mean():.2%} ({int((tr > residual_thr).sum())}/{len(tr)})"
    )
    lines.append("")
    lines.append("## Holdout alarm metrics (is_low = known-bad config)")
    lines.append("")
    lines.append("| Variant | TP | FP | FN | Precision | Recall |")
    lines.append("|---|---:|---:|---:|---:|---:|")
    for key, label in (
        ("proxy_only", "proxy only"),
        ("proxy_or_orient", "proxy OR orient"),
        ("proxy_or_resid", "proxy OR residual"),
        ("proxy_or_either", "proxy OR either"),
    ):
        m = holdout_eval[key]
        lines.append(
            f"| {label} | {m['tp']} | {m['fp']} | {m['fn']} | "
            f"{m['precision']:.2f} | {m['recall']:.2f} |"
        )
    lines.append("")
    lines.append("## Holdout anchors with residual_high")
    lines.append("")
    lines.append("| Subset | residual_cm | mIoU | proxy | unlock |")
    lines.append("|---|---:|---:|---:|---|")
    for _, r in high.iterrows():
        lines.append(
            f"| {r['subset']} | {r['recentre_residual_max_cm']:.1f} | "
            f"{r['mIoU']:.3f} | {r['proxy']:.3f} | "
            f"{'yes' if r['unlock_stage1'] else 'no'} |"
        )
    lines.append("")
    lines.append("## Pass / fail vs plan criteria")
    lines.append("")
    for k, v in pass_fail.items():
        lines.append(f"- **{k}**: {v}")
    lines.append("")
    lines.append("## Phase B unlock rule")
    lines.append("")
    lines.append(
        f"Unlock stage-1 (`reflect_pilot.py --full` with `unfolding` overlays) "
        f"when the subset's *anchor* fires `unlock_stage1` "
        f"(residual > {residual_thr} cm or orientation fail)."
    )
    lines.append("")
    lines.append(
        "Target subsets for the widened campaign: "
        "3-4 (unlock), 3-2 (unlock), 4-1 (locked), 2-2 (locked)."
    )
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    p = argparse.ArgumentParser(description="Stage-1 geometry gate")
    p.add_argument("--residual-cm", type=float, default=DEFAULT_RESIDUAL_CM)
    p.add_argument("--json-out", type=Path, default=DEFAULT_JSON)
    p.add_argument("--md-out", type=Path, default=REPORT_MD)
    args = p.parse_args()

    models = json.loads(MODELS.read_text(encoding="utf-8"))
    holdout = load_holdout(models)
    train = load_train_for_resid_stats()
    train_resid = train["recentre_residual_max_cm"].astype(float)

    # Sweep residual thresholds for the report appendix
    sweeps = {}
    for thr in RESIDUAL_CM_CANDIDATES:
        sweeps[thr] = {
            k: v
            for k, v in evaluate_alarms(holdout, residual_thr=thr).items()
            if k != "scored"
        }

    holdout_eval = evaluate_alarms(holdout, residual_thr=args.residual_cm)
    scored = holdout_eval["scored"]
    anchors = scored[scored["config_kind"] == "anchor"]

    # Plan criteria
    row_43 = anchors[anchors["subset"] == "4-3"]
    flags_43 = bool(row_43["residual_high"].iloc[0]) if len(row_43) else False
    # "healthy-side anchor" for residual-as-quality = mIoU >= 0.7
    healthy = anchors[anchors["mIoU"] >= 0.7]
    resid_fp_healthy = int(healthy["residual_high"].sum())
    orient_fp_anchors = int(anchors["orient_fail"].sum())
    # Known-bad pairing: proxy OR orient must keep FP=0 on anchors
    or_orient_fp = holdout_eval["proxy_or_orient"]["fp"]

    pass_fail = {
        "flags_4-3_via_residual_high": "PASS" if flags_43 else "FAIL",
        "orient_false_alarms_on_27_anchors": (
            f"PASS ({orient_fp_anchors})" if orient_fp_anchors == 0 else f"FAIL ({orient_fp_anchors})"
        ),
        "proxy_OR_orient_preserves_anchor_FP0": (
            "PASS" if or_orient_fp == 0 else f"FAIL (fp={or_orient_fp})"
        ),
        "residual_as_quality_OR_zero_FP_on_mIoU>=0.7_anchors": (
            f"FAIL ({resid_fp_healthy} FPs: "
            + ", ".join(
                f"{s}({m:.2f})"
                for s, m in zip(
                    healthy.loc[healthy["residual_high"], "subset"],
                    healthy.loc[healthy["residual_high"], "mIoU"],
                )
            )
            + ") — residual kept as unlock/diagnostic only"
            if resid_fp_healthy
            else "PASS"
        ),
        "overall_quality_gate": (
            "PASS (orientation OR; residual unlock-only)"
            if or_orient_fp == 0 and orient_fp_anchors == 0
            else "FAIL"
        ),
    }

    report = write_report(
        holdout_eval=holdout_eval,
        residual_thr=args.residual_cm,
        train_resid=train_resid,
        pass_fail=pass_fail,
    )
    # Append sweep table
    report += "## Residual threshold sweep (proxy OR residual)\n\n"
    report += "| thr_cm | TP | FP | FN | Prec | Rec |\n|---|---:|---:|---:|---:|---:|\n"
    for thr, ev in sweeps.items():
        m = ev["proxy_or_resid"]
        report += (
            f"| {thr:.0f} | {m['tp']} | {m['fp']} | {m['fn']} | "
            f"{m['precision']:.2f} | {m['recall']:.2f} |\n"
        )
    report += "\n"

    args.md_out.write_text(report, encoding="utf-8")

    # Per-subset unlock table for Phase B
    unlock_targets = {}
    for subset in ("3-4", "3-2", "4-1", "2-2", "4-3", "4-4", "1-4", "1-5", "3-5"):
        row = anchors[anchors["subset"] == subset]
        if row.empty:
            continue
        r = row.iloc[0]
        unlock_targets[subset] = {
            "residual_cm": float(r["recentre_residual_max_cm"]),
            "orient_axis_corr": float(r["orient_axis_corr"]),
            "mIoU": float(r["mIoU"]),
            "proxy": float(r["proxy"]),
            "unlock_stage1": bool(r["unlock_stage1"]),
            "residual_high": bool(r["residual_high"]),
            "orient_fail": bool(r["orient_fail"]),
        }

    payload = {
        "orient_min": ORIENT_MIN,
        "residual_thr_cm": args.residual_cm,
        "alarm_threshold_proxy": float(models["alarm_threshold"]),
        "holdout_metrics": {
            k: holdout_eval[k]
            for k in ("proxy_only", "proxy_or_orient", "proxy_or_resid", "proxy_or_either")
        },
        "residual_sweep": sweeps,
        "pass_fail": pass_fail,
        "unlock_targets": unlock_targets,
        "anchor_residual_high": [
            {
                "subset": str(r["subset"]),
                "residual_cm": float(r["recentre_residual_max_cm"]),
                "mIoU": float(r["mIoU"]),
                "proxy": float(r["proxy"]),
            }
            for _, r in anchors[anchors["residual_high"]]
            .sort_values("recentre_residual_max_cm", ascending=False)
            .iterrows()
        ],
    }
    args.json_out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(report)
    print(f"Wrote {args.md_out}")
    print(f"Wrote {args.json_out}")


if __name__ == "__main__":
    main()
