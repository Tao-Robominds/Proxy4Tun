#!/usr/bin/env python3
"""Stage 2: build SC-general feature tables for the frozen bo-bayes 120 + 54 runs.

Reads:
  bo/bayes/training_table.csv   (120 calibration rows)
  bo/bayes/holdout_scores.csv   (54 holdout rows: 27 anchor + 27 bad)

Writes under data/sc-general/stage2/ only:
  training_table.csv, holdout_table.csv, replay_audit.csv, gate.md, progress.log

Never writes into anchors/, data/anchors/, data/bo/, bo/bayes/, or bo/full_stage/.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from bo.sc_general.features import all_features  # noqa: E402
from bo.sc_general.label_map import build_label_map  # noqa: E402
from bo.sc_general.replay import compare_prompts, replay_run  # noqa: E402

OUT = _REPO / "data" / "sc-general" / "stage2"
REPLAY_ROOT = _REPO / "data" / "sc-general" / "replay"
TRAIN_SRC = _REPO / "bo" / "bayes" / "training_table.csv"
HOLDOUT_SRC = _REPO / "bo" / "bayes" / "holdout_scores.csv"

BAYES_FEATURE_COLS = [
    "depth_nan_ratio",
    "denoise_retained_ratio",
    "unfold_residual",
    "orient_agreement",
    "sam_fill_rate",
    "sam_ontology_divergence",
    "det_row_residual_px",
    "det_row_gated",
    "det_row_y_std",
    "phase_incoherence_deg",
]

SC_GENERAL_KEYS = [
    "correspondence_f1@8",
    "correspondence_f1@15",
    "correspondence_f1@25",
    "line_explained@8",
    "line_explained@15",
    "line_explained@25",
    "boundary_explained_line@8",
    "boundary_explained_line@15",
    "boundary_explained_line@25",
    "boundary_explained_edge@8",
    "boundary_explained_edge@15",
    "boundary_explained_edge@25",
    "chamfer_sym_px",
    "chamfer_line_to_bnd_px",
    "chamfer_bnd_to_line_px",
]

# Lean-10 candidate pool (K-row trio removed).
LEAN10 = [
    "depth_nan_ratio",
    "denoise_retained_ratio",
    "unfold_residual",
    "orient_agreement",
    "ring_count_error",
    "correspondence_f1@15",
    "boundary_explained_edge@25",
    "chamfer_sym_px",
    "sam_fill_rate",
    "phase_incoherence_deg",
]

LEGACY_LEAN = [
    "depth_nan_ratio",
    "denoise_retained_ratio",
    "sam_fill_rate",
    "det_row_residual_px",
    "det_row_gated",
]


def _log(msg: str, *, fh=None) -> None:
    line = f"[{datetime.now().isoformat(timespec='seconds')}] {msg}"
    print(line, flush=True)
    if fh is not None:
        fh.write(line + "\n")
        fh.flush()


def process_run(run_dir: Path, *, write_shadow: bool = True) -> dict[str, Any]:
    t0 = time.time()
    run_dir = Path(run_dir)
    ls = replay_run(run_dir, write_shadow=write_shadow, shadow_root=REPLAY_ROOT)
    stored = pd.read_csv(run_dir / "initial_points.csv")
    cmp = compare_prompts(ls.prompts, stored)
    lm = build_label_map(run_dir)
    feats = all_features(ls, lm, ring_count=ls.ring_count)
    ring_count = int(ls.ring_count)
    out: dict[str, Any] = {
        "path": str(run_dir),
        "run_id": run_dir.name,
        "ring_count": ring_count,
        "ring_count_source": str(ls.ring_count_source).split(":")[0],
        "ring_count_error": float(abs(ring_count - 10)),
        "replay_prompt_match": bool(cmp["match"]),
        "replay_max_dx": float(cmp["max_dx"]),
        "replay_max_dy": float(cmp["max_dy"]),
        "replay_type_match": float(cmp["type_match"]),
        "labelmap_source": lm.source,
        "labelmap_coverage_known": float(lm.coverage_known),
        "labelmap_coverage_filled": float(lm.coverage_filled),
        "elapsed_s": round(time.time() - t0, 2),
    }
    for k in SC_GENERAL_KEYS:
        out[k] = float(feats.get(k, float("nan")))
    return out


def _join_row(base: pd.Series, computed: dict[str, Any], *, kind: str) -> dict[str, Any]:
    row = dict(computed)
    row["split"] = kind
    if kind == "train":
        row["case"] = base["case"]
        row["family"] = base["family"]
        row["trial_id"] = base["trial_id"]
        row["mIoU"] = float(base["mIoU"])
        row["stage1_varied"] = bool(base["stage1_varied"])
        row["acquisition"] = base["acquisition"]
        row["source"] = base["source"]
    else:
        row["subset"] = base["subset"]
        row["family"] = base["family"]
        row["config_kind"] = base["config_kind"]
        row["trial_id"] = base["run_id"]
        row["mIoU"] = float(base["mIoU"])
        row["status"] = base["status"]
        row["legacy_proxy"] = float(base["proxy"]) if pd.notna(base["proxy"]) else float("nan")
    for c in BAYES_FEATURE_COLS:
        if c in base.index:
            row[c] = float(base[c]) if pd.notna(base[c]) else float("nan")
    return row


def build(split: str, *, limit: int | None = None, write_shadow: bool = True) -> pd.DataFrame:
    OUT.mkdir(parents=True, exist_ok=True)
    REPLAY_ROOT.mkdir(parents=True, exist_ok=True)
    src = TRAIN_SRC if split == "train" else HOLDOUT_SRC
    df = pd.read_csv(src)
    if limit is not None:
        df = df.head(limit)
    rows: list[dict[str, Any]] = []
    with (OUT / "progress.log").open("a", encoding="utf-8") as fh:
        _log(f"=== build {split}: n={len(df)} from {src} ===", fh=fh)
        for i, (_, base) in enumerate(df.iterrows(), start=1):
            run_dir = _REPO / str(base["path"])
            tid = base["trial_id"] if split == "train" else base["run_id"]
            try:
                if not run_dir.is_dir():
                    raise FileNotFoundError(f"missing run dir {run_dir}")
                computed = process_run(run_dir, write_shadow=write_shadow)
                row = _join_row(base, computed, kind=split)
                rows.append(row)
                _log(
                    f"{split} {i}/{len(df)} {tid} "
                    f"f1@15={row['correspondence_f1@15']:.3f} "
                    f"edge@25={row['boundary_explained_edge@25']:.3f} "
                    f"rc={row['ring_count']} match={row['replay_prompt_match']} "
                    f"src={row['labelmap_source']} {row['elapsed_s']}s",
                    fh=fh,
                )
            except Exception as exc:  # noqa: BLE001
                _log(f"{split} {i}/{len(df)} {tid} FAIL {type(exc).__name__}: {exc}", fh=fh)
                _log(traceback.format_exc(), fh=fh)
                raise
    return pd.DataFrame(rows)


def write_gate(train: pd.DataFrame, holdout: pd.DataFrame) -> bool:
    all_df = pd.concat([train, holdout], ignore_index=True)
    n = len(all_df)
    n_match = int(all_df["replay_prompt_match"].sum())
    mismatch = all_df.loc[
        ~all_df["replay_prompt_match"],
        ["trial_id", "path", "replay_max_dx", "replay_max_dy"],
    ]
    nonfinite: list[tuple[str, pd.DataFrame]] = []
    for k in LEAN10:
        bad = all_df.loc[~np.isfinite(all_df[k].astype(float)), ["trial_id", "path"]]
        if len(bad):
            nonfinite.append((k, bad))
    src_counts = all_df["labelmap_source"].value_counts().to_dict()
    rc_src = all_df["ring_count_source"].value_counts().to_dict()
    # Full run requires exact 120/54; --limit smoke runs are allowed to be smaller.
    full_counts = len(train) == 120 and len(holdout) == 54
    partial_ok = 0 < len(train) <= 120 and 0 < len(holdout) <= 54
    ok_counts = full_counts or (partial_ok and not full_counts)
    ok = (n_match == n) and (not nonfinite) and ok_counts

    lines = [
        "# Stage-2 feature-table gate\n",
        f"Generated {datetime.now().isoformat()}\n",
        "Command: `./venv/bin/python bo/sc_general/build_tables.py`\n",
        f"\n## Counts\n- training rows: {len(train)} (expect 120)\n"
        f"- holdout rows: {len(holdout)} (expect 54)\n"
        f"- lean-10: `{LEAN10}`\n",
        f"\n## Replay prompt match\n- {n_match}/{n} exact (criterion: all)\n",
    ]
    if len(mismatch):
        lines.append("- mismatches:\n")
        for _, r in mismatch.iterrows():
            lines.append(
                f"  - {r['trial_id']}: dx={r['replay_max_dx']} dy={r['replay_max_dy']} `{r['path']}`\n"
            )
    lines.append(f"- **{'PASS' if n_match == n else 'FAIL'}**\n")

    lines.append("\n## Lean-10 finite\n")
    if not nonfinite:
        lines.append("- all lean-10 features finite on all rows\n- **PASS**\n")
    else:
        for k, bad in nonfinite:
            lines.append(f"- {k}: {len(bad)} non-finite\n")
            for _, r in bad.head(5).iterrows():
                lines.append(f"  - {r['trial_id']} `{r['path']}`\n")
        lines.append("- **FAIL**\n")

    lines.append(
        f"\n## Label-map sources\n```\n{json.dumps(src_counts, indent=2)}\n```\n"
        f"\n## Ring-count sources\n```\n{json.dumps(rc_src, indent=2)}\n```\n"
    )
    if "family" in train.columns:
        complex_src = (
            train.loc[train["family"] == "complex", "labelmap_source"].value_counts().to_dict()
        )
        lines.append(
            f"\n## Complex-family label sources (train)\n```\n{json.dumps(complex_src, indent=2)}\n```\n"
        )
    lines.append(f"\n## Overall: **{'PASS' if ok else 'FAIL'}**\n")
    (OUT / "gate.md").write_text("".join(lines), encoding="utf-8")
    return ok


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--limit", type=int, default=None, help="first N rows per split (smoke)")
    ap.add_argument("--split", choices=["train", "holdout", "both"], default="both")
    ap.add_argument("--no-shadow", action="store_true")
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    write_shadow = not args.no_shadow

    train = holdout = None
    if args.split in ("train", "both"):
        train = build("train", limit=args.limit, write_shadow=write_shadow)
        train.to_csv(OUT / "training_table.csv", index=False)
        print(f"wrote {OUT / 'training_table.csv'} ({len(train)} rows)")
    if args.split in ("holdout", "both"):
        holdout = build("holdout", limit=args.limit, write_shadow=write_shadow)
        holdout.to_csv(OUT / "holdout_table.csv", index=False)
        print(f"wrote {OUT / 'holdout_table.csv'} ({len(holdout)} rows)")

    if train is None:
        train = pd.read_csv(OUT / "training_table.csv")
    if holdout is None:
        holdout = pd.read_csv(OUT / "holdout_table.csv")

    audit_cols = [
        "split",
        "trial_id",
        "family",
        "path",
        "ring_count",
        "ring_count_source",
        "ring_count_error",
        "replay_prompt_match",
        "replay_max_dx",
        "replay_max_dy",
        "replay_type_match",
        "labelmap_source",
        "labelmap_coverage_known",
        "labelmap_coverage_filled",
        "elapsed_s",
    ]
    audit = pd.concat([train, holdout], ignore_index=True)[audit_cols]
    audit.to_csv(OUT / "replay_audit.csv", index=False)
    print(f"wrote {OUT / 'replay_audit.csv'}")

    ok = write_gate(train, holdout)
    print(f"gate {'PASS' if ok else 'FAIL'} -> {OUT / 'gate.md'}")
    if not ok and args.limit is None:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
