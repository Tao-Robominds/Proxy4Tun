#!/usr/bin/env python3
"""Rebuild the 54-run holdout table using development-only degraded overlays.

- Reuses the 27 anchor rows from data/sc-general/stage2/holdout_table.csv
- Recomputes the 27 bad rows from data/<subset>-degraded-devonly/
- Scores with the frozen bo/sc_general/models.json (no refit)
- Writes under data/sc-general/stage2_devonly/ only
"""

from __future__ import annotations

import json
import math
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from bo.bayes.clustered_stats import subset_bootstrap_spearman  # noqa: E402
from bo.full_stage.train_proxy import predict  # noqa: E402
from bo.sc_general.build_tables import (  # noqa: E402
    BAYES_FEATURE_COLS,
    _join_row,
    process_run,
)
from bo.sc_general.run_degraded_devonly import (  # noqa: E402
    FAMILY_LABEL,
    all_eval_subsets,
    study_root,
)
from bo.sc_general.score_holdouts import (  # noqa: E402
    alarm_at_tau,
    apply_gate,
    band_check,
    pair_rank,
    per_family_vs_pooled,
    spearman,
    tau_sweep,
    write_gate_md,
)
from bo.unified.spaces import family_of_subset  # noqa: E402

STAGE2 = _REPO / "data" / "sc-general" / "stage2"
OUT = _REPO / "data" / "sc-general" / "stage2_devonly"
MODELS = _REPO / "bo" / "sc_general" / "models.json"
ANCHOR_TABLE = STAGE2 / "holdout_table.csv"
TRAIN_SUMMARY = STAGE2 / "train_summary.json"


def _base_row_from_run(subset: str, run_dir: Path, rec: dict[str, Any]) -> pd.Series:
    metrics = rec.get("metrics") or {}
    if not metrics and (run_dir / "intrinsics.json").exists():
        metrics = json.loads((run_dir / "intrinsics.json").read_text(encoding="utf-8"))
    fam_code = family_of_subset(subset)
    data: dict[str, Any] = {
        "subset": subset,
        "family": FAMILY_LABEL[fam_code],
        "config_kind": "bad",
        "run_id": f"{subset}-bad",
        "path": str(run_dir),
        "status": rec.get("status", "ok"),
        "mIoU": float(rec["mIoU"]),
        "proxy": float("nan"),
    }
    for c in BAYES_FEATURE_COLS:
        v = metrics.get(c)
        if v is None and c == "orient_agreement":
            v = metrics.get("orient_h_ring_corr")
        if v is None and c == "unfold_residual":
            # recentre residual is in cm in unified intrinsics; leave nan if absent
            v = metrics.get("recentre_residual_max_cm")
        data[c] = float(v) if v is not None and math.isfinite(float(v)) else float("nan")
    return pd.Series(data)


def build_holdout_table(*, write_shadow: bool = False) -> pd.DataFrame:
    if not ANCHOR_TABLE.exists():
        raise SystemExit(f"missing {ANCHOR_TABLE}")
    anchors = pd.read_csv(ANCHOR_TABLE)
    anchors = anchors[anchors["config_kind"] == "anchor"].copy()
    if len(anchors) != 27:
        raise SystemExit(f"expected 27 anchor rows, got {len(anchors)}")

    bad_rows: list[dict[str, Any]] = []
    log_path = OUT / "rebuild_progress.log"
    OUT.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as fh:
        fh.write(f"\n=== rebuild {datetime.now().isoformat()} ===\n")
        for i, subset in enumerate(all_eval_subsets(), start=1):
            study = study_root(subset)
            run_dir = study / "runs" / f"{subset}-bad"
            man_path = study / "manifest.json"
            if not run_dir.is_dir() or not man_path.exists():
                raise FileNotFoundError(f"missing degraded run for {subset}: {run_dir}")
            man = json.loads(man_path.read_text(encoding="utf-8"))
            rec = next(r for r in man["runs"] if r["run_id"] == f"{subset}-bad")
            if rec.get("status") != "ok" or rec.get("mIoU") is None:
                raise RuntimeError(f"unusable degraded run {subset}: {rec.get('status')}")
            base = _base_row_from_run(subset, run_dir, rec)
            computed = process_run(run_dir, write_shadow=write_shadow)
            row = _join_row(base, computed, kind="holdout")
            bad_rows.append(row)
            msg = (
                f"bad {i}/27 {subset} mIoU={row['mIoU']:.3f} "
                f"f1@15={row['correspondence_f1@15']:.3f} "
                f"fill={row['sam_fill_rate']:.3f} nan={row['depth_nan_ratio']:.3f}"
            )
            print(msg)
            fh.write(msg + "\n")
            fh.flush()

    bads = pd.DataFrame(bad_rows)
    # Align column order with the existing anchor table where possible.
    cols = list(anchors.columns)
    for c in bads.columns:
        if c not in cols:
            cols.append(c)
    anchors = anchors.reindex(columns=cols)
    bads = bads.reindex(columns=cols)
    out = pd.concat([anchors, bads], ignore_index=True)
    # Stable order: by subset then anchor before bad
    out["_kind_ord"] = out["config_kind"].map({"anchor": 0, "bad": 1}).fillna(2)
    out = out.sort_values(["subset", "_kind_ord"]).drop(columns=["_kind_ord"]).reset_index(drop=True)
    return out


def score_holdout(hs: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any], dict[str, Any]]:
    models = json.loads(MODELS.read_text(encoding="utf-8"))
    feats = models["lean_features"]
    for f in feats:
        if f not in hs.columns:
            raise SystemExit(f"holdout missing feature {f}")
        hs[f] = hs[f].astype(float)
    hs = hs.copy()
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
        "degraded_overlays": "devonly",
        "overlay_source": "bo/sc_general/degraded_overlays_devonly.json",
    }
    return hs, metrics, band


def write_report(metrics: dict[str, Any], hs: pd.DataFrame, path: Path) -> None:
    bads = hs[hs["config_kind"] == "bad"]
    lines = [
        "# Dev-only degradation holdout report",
        "",
        f"- n={metrics['n']}",
        f"- Spearman={metrics['spearman']:.3f} (CI95 {metrics['bootstrap']['ci95']})",
        f"- MAE={metrics['mae']:.4f}",
        f"- Pair rank={metrics['pair_rank']['wins']}/{metrics['pair_rank']['n']}",
        f"- Alarm @0.5: TP={metrics['alarm_0.5']['tp']} FP={metrics['alarm_0.5']['fp']}",
        f"- Degraded mIoU range: {bads['mIoU'].min():.3f}–{bads['mIoU'].max():.3f}",
        "",
        "## Family MAE",
        "",
    ]
    for fam, v in metrics["family_mae"].items():
        lines.append(f"- {fam}: {v:.4f}")
    lines += ["", "## Per-subset degraded mIoU", ""]
    for _, r in bads.sort_values("subset").iterrows():
        lines.append(
            f"- {r['subset']}: mIoU={r['mIoU']:.3f} proxy={r['proxy']:.3f} "
            f"abs_err={r['abs_err']:.3f}"
        )
    # Note pre-existing 1-1 / 4-1 base asymmetry
    lines += [
        "",
        "## Notes",
        "",
        "- Anchor rows reused from `data/sc-general/stage2/holdout_table.csv`.",
        "- Degraded overlays from development calibration trials only "
        "(2-1-s013, 3-1-s008, 5-1-s011).",
        "- Base params for 1-1 and 4-1 degraded runs use "
        "`anchors/unified/params/{1-1,4-1}` (same as the previous bad runs); "
        "their anchor rows still point at `data/anchors/{1-1,4-1}` "
        "(pre-existing asymmetry).",
        "",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    hs_table = build_holdout_table(write_shadow=False)
    hs_table.to_csv(OUT / "holdout_table.csv", index=False)

    hs, metrics, band = score_holdout(hs_table)
    hs.to_csv(OUT / "holdout_scores.csv", index=False)
    (OUT / "holdout_metrics.json").write_text(
        json.dumps(metrics, indent=2) + "\n", encoding="utf-8"
    )
    (OUT / "band_check.json").write_text(json.dumps(band, indent=2) + "\n", encoding="utf-8")
    write_report(metrics, hs, OUT / "report.md")

    train_summary = json.loads(TRAIN_SUMMARY.read_text(encoding="utf-8"))
    models = json.loads(MODELS.read_text(encoding="utf-8"))
    gate = apply_gate(train_summary, metrics, models)
    write_gate_md(gate, metrics, OUT / "validation_gate.md")
    (OUT / "gate_result.json").write_text(json.dumps(gate, indent=2) + "\n", encoding="utf-8")

    print(
        f"holdout mae={metrics['mae']:.4f} sp={metrics['spearman']:.3f} "
        f"pair={metrics['pair_rank']['wins']}/{metrics['pair_rank']['n']} "
        f"alarm@0.5 TP={metrics['alarm_0.5']['tp']} FP={metrics['alarm_0.5']['fp']}"
    )


if __name__ == "__main__":
    main()
