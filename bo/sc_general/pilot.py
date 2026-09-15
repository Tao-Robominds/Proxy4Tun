#!/usr/bin/env python3
"""Stage-1 pilot driver: one-instance gate, then 15 stratified calibration trials.

Outputs (all under data/sc-general/):
  gate.md                       one-instance validation log (5-1 anchor)
  pilot/pilot_features.csv      15 runs x candidate features (+ legacy columns)
  pilot/overlays/<trial>.png    correspondence overlays
  pilot/report.md               per-family Spearman, sign consistency, redundancy

Usage:
  ./venv/bin/python bo/sc_general/pilot.py --gate
  ./venv/bin/python bo/sc_general/pilot.py --run
  ./venv/bin/python bo/sc_general/pilot.py --report
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))
from bo.sc_general.features import DELTAS, all_features  # noqa: E402
from bo.sc_general.label_map import build_label_map, compare_routes, sam_scores  # noqa: E402
from bo.sc_general.overlay import render_overlay  # noqa: E402
from bo.sc_general.replay import compare_prompts, replay_run  # noqa: E402

OUT = _REPO / "data" / "sc-general"
PILOT = OUT / "pilot"
TRAIN_TABLE = _REPO / "bo" / "full_stage" / "training_table.csv"

PILOT_TRIALS: dict[str, list[str]] = {
    "staggered": ["2-1-f019", "2-1-f009", "2-1-f002", "2-1-t012", "2-1-anchor"],
    "continuous": ["3-1-t025", "3-1-t010", "3-1-f005", "3-1-t029", "3-1-t015"],
    "complex": ["5-1-t002", "5-1-f008", "5-1-f018", "5-1-t004", "5-1-f000"],
}
LEGACY_COLS = [
    "depth_nan_ratio", "denoise_retained_ratio", "unfold_residual", "orient_agreement",
    "sam_fill_rate", "sam_ontology_divergence", "det_row_residual_px", "det_row_gated",
    "det_row_y_std", "phase_incoherence_deg",
]
LEAN_LEGACY = ["depth_nan_ratio", "denoise_retained_ratio", "sam_fill_rate", "det_row_residual_px", "det_row_gated"]

# Expected direction of association with mIoU (+1 higher is better, -1 lower is better)
EXPECTED_SIGN: dict[str, int] = {
    "line_explained": +1, "line_explained_obl": +1, "line_explained_hor": +1,
    "boundary_explained_line": +1, "boundary_explained_edge": +1, "correspondence_f1": +1,
    "chamfer_line_to_bnd_px": -1, "chamfer_bnd_to_line_px": -1, "chamfer_sym_px": -1,
    "chamfer_median_line_to_bnd_px": -1, "bnd_edge_dist_mean_px": -1,
    "prompt_k_hit": +1, "prompt_k_hit_real": +1, "prompt_real_frac": +1, "prompt_block_hit": +1,
    "transition_valid_frac": +1, "ring_label_completeness": +1, "ring_label_presence": +1,
    "mask_fragmentation": -1, "mask_rectangularity": +1, "block_height_dispersion": -1,
    "boundary_straightness_px": -1, "sam_score_mean": +1, "sam_score_min": +1, "sam_score_p10": +1,
    "n_oblique_lines": +1, "n_horizontal_lines": 0, "line_px": 0, "boundary_px": 0,
}


def _base(name: str) -> str:
    return name.split("@")[0]


def process_run(run_dir: Path, trial_id: str, *, overlay_delta: int = 15) -> dict:
    t0 = time.time()
    ls = replay_run(run_dir, write_shadow=True)
    stored = pd.read_csv(run_dir / "initial_points.csv")
    cmp = compare_prompts(ls.prompts, stored)
    lm = build_label_map(run_dir)
    feats = all_features(ls, lm, ring_count=ls.ring_count, sam_scores=sam_scores(run_dir))
    render_overlay(run_dir, ls, lm, PILOT / "overlays" / f"{trial_id}.png", delta=overlay_delta,
                   title=f"{trial_id}  ({run_dir})")
    feats.update({
        "trial_id": trial_id, "path": str(run_dir), "ring_count": ls.ring_count,
        "ring_count_source": ls.ring_count_source.split(":")[0],
        "replay_prompt_match": cmp["match"], "replay_max_dx": cmp["max_dx"], "replay_max_dy": cmp["max_dy"],
        "elapsed_s": round(time.time() - t0, 1),
    })
    return feats


# --------------------------------------------------------------------------- #
def run_gate() -> bool:
    OUT.mkdir(parents=True, exist_ok=True)
    case = _REPO / "data" / "anchors" / "5-1"
    lines = [f"# SC-general one-instance gate\n", f"Generated {datetime.now().isoformat()}\n",
             f"Case: `{case}` (complex family; label map via only_label.csv fallback)\n",
             "Command: `./venv/bin/python bo/sc_general/pilot.py --gate`\n"]
    ok_all = True

    ls = replay_run(case, write_shadow=True)
    stored = pd.read_csv(case / "initial_points.csv")
    cmp = compare_prompts(ls.prompts, stored)
    ok = bool(cmp["match"])
    ok_all &= ok
    lines.append(f"\n## 1. Hough replay reproduces stored prompt points\n"
                 f"- rows replayed/stored: {cmp['n_replayed']}/{cmp['n_stored']}\n"
                 f"- max |dx|, |dy|: {cmp['max_dx']:.2e}, {cmp['max_dy']:.2e} px (criterion <= 1 px)\n"
                 f"- type agreement: {cmp['type_match']:.2f} (criterion 1.00)\n"
                 f"- ring_count {ls.ring_count} from {ls.ring_count_source.split(':')[0]}\n"
                 f"- **{'PASS' if ok else 'FAIL'}**\n")

    lm = build_label_map(case)
    tt = pd.read_csv(TRAIN_TABLE).set_index("trial_id")
    fill_rate = float(tt.loc["5-1-anchor", "sam_fill_rate"])
    labelled = float((lm.label > 0).mean())
    ok = lm.coverage_filled >= 0.8 and labelled > 0.5 * fill_rate
    ok_all &= ok
    lines.append(f"\n## 2. Fallback label map coverage (complex has no results.pkl)\n"
                 f"- source: {lm.source}; direct-evidence coverage {lm.coverage_known:.3f}; after {lm.fill_dist_px:.0f} px fill {lm.coverage_filled:.3f}\n"
                 f"- labelled (>0) fraction {labelled:.3f} vs stored sam_fill_rate {fill_rate:.3f}\n"
                 f"- criterion: filled coverage >= 0.80 and labelled fraction > 0.5 x fill rate\n"
                 f"- **{'PASS' if ok else 'FAIL'}**\n")

    cr = compare_routes(_REPO / "data" / "anchors" / "3-1")
    ok = cr["label_agreement_nonbg"] >= 0.98 and cr["ring_agreement"] >= 0.9
    ok_all &= ok
    lines.append(f"\n## 3. results.pkl composition vs reprojected labels (3-1, both routes exist)\n"
                 f"- evidence pixels: {cr['n_known']}\n"
                 f"- label agreement (non-background): {cr['label_agreement_nonbg']:.4f} (criterion >= 0.98)\n"
                 f"- ring agreement: {cr['ring_agreement']:.4f} (criterion >= 0.90)\n"
                 f"- **{'PASS' if ok else 'FAIL'}**\n")

    feats = all_features(ls, lm, ring_count=ls.ring_count)
    numeric = {k: v for k, v in feats.items() if isinstance(v, (int, float))}
    nonfinite = [k for k, v in numeric.items() if not np.isfinite(v) and not k.startswith("sam_score")]
    ok = not nonfinite
    ok_all &= ok
    lines.append(f"\n## 4. All candidate features finite\n"
                 f"- {len(numeric)} numeric features; non-finite (excluding sam_score*, N/A for complex): {nonfinite or 'none'}\n"
                 f"- **{'PASS' if ok else 'FAIL'}**\n")
    lines.append("\n## Feature values on the gate case\n\n| feature | value |\n|---|---|\n")
    for k, v in numeric.items():
        lines.append(f"| {k} | {v:.4f} |\n")
    lines.append(f"\n## Overall: **{'PASS' if ok_all else 'FAIL'}**\n")
    (OUT / "gate.md").write_text("".join(lines), encoding="utf-8")
    print("".join(lines[:1]), f"overall {'PASS' if ok_all else 'FAIL'} -> {OUT / 'gate.md'}")
    return ok_all


# --------------------------------------------------------------------------- #
def run_pilot() -> pd.DataFrame:
    PILOT.mkdir(parents=True, exist_ok=True)
    tt = pd.read_csv(TRAIN_TABLE).set_index("trial_id")
    rows = []
    for fam, trials in PILOT_TRIALS.items():
        for tid in trials:
            run_dir = _REPO / tt.loc[tid, "path"]
            print(f"[{fam}] {tid} mIoU={tt.loc[tid, 'mIoU']:.3f} ...", flush=True)
            feats = process_run(run_dir, tid)
            feats["family"] = fam
            feats["mIoU"] = float(tt.loc[tid, "mIoU"])
            for c in LEGACY_COLS:
                feats[f"legacy_{c}"] = float(tt.loc[tid, c])
            rows.append(feats)
            print(f"    {feats['elapsed_s']}s  f1@15={feats['correspondence_f1@15']:.3f} "
                  f"line_expl@15={feats['line_explained@15']:.3f} chamfer={feats['chamfer_sym_px']:.1f} "
                  f"replay_ok={feats['replay_prompt_match']} src={feats['labelmap_source']}", flush=True)
    df = pd.DataFrame(rows)
    df.to_csv(PILOT / "pilot_features.csv", index=False)
    print(f"wrote {PILOT / 'pilot_features.csv'}")
    return df


# --------------------------------------------------------------------------- #
def _spearman(x: pd.Series, y: pd.Series) -> float:
    m = np.isfinite(x) & np.isfinite(y)
    if m.sum() < 3 or x[m].nunique() < 2:
        return float("nan")
    r = stats.spearmanr(x[m], y[m]).correlation
    return float(r) if r is not None and np.isfinite(r) else float("nan")


def write_report(df: pd.DataFrame) -> None:
    fams = list(PILOT_TRIALS)
    skip = {"trial_id", "path", "family", "mIoU", "labelmap_source", "ring_count_source", "replay_prompt_match"}
    cand = [c for c in df.columns if c not in skip and not c.startswith("legacy_")
            and not c.startswith("replay_") and c not in ("elapsed_s",)]
    rows = []
    for c in cand:
        if not np.issubdtype(df[c].dtype, np.number):
            continue
        r_pool = _spearman(df[c], df["mIoU"])
        r_fam = {f: _spearman(df.loc[df.family == f, c], df.loc[df.family == f, "mIoU"]) for f in fams}
        signs = [np.sign(v) for v in r_fam.values() if np.isfinite(v) and v != 0]
        consistent = len(signs) == 3 and len(set(signs)) == 1
        exp = EXPECTED_SIGN.get(_base(c), 0)
        exp_ok = (exp == 0) or (np.isfinite(r_pool) and np.sign(r_pool) == exp)
        n_strong = sum(abs(v) >= 0.5 for v in r_fam.values() if np.isfinite(v))
        red_fill = _spearman(df[c], df["legacy_sam_fill_rate"])
        red_nan = _spearman(df[c], df["legacy_depth_nan_ratio"])
        sd = float(df[c].std()) if df[c].notna().sum() > 1 else float("nan")
        gap = float(df.loc[df.trial_id == "5-1-f000", c].iloc[0] - df.loc[df.trial_id == "5-1-f008", c].iloc[0])
        gap_sd = gap / sd if sd and np.isfinite(sd) and sd > 0 else float("nan")
        passes = consistent and exp_ok and n_strong >= 2 and (not np.isfinite(red_fill) or abs(red_fill) < 0.8) \
            and (not np.isfinite(red_nan) or abs(red_nan) < 0.8)
        rows.append({
            "feature": c, "rho_pooled": r_pool, **{f"rho_{f}": r_fam[f] for f in fams},
            "sign_consistent": consistent, "expected_sign_ok": exp_ok, "n_fam_strong": n_strong,
            "rho_vs_fill": red_fill, "rho_vs_nan": red_nan, "f000_minus_f008_sd": gap_sd, "nan_count": int(df[c].isna().sum()),
            "pass": passes,
        })
    res = pd.DataFrame(rows).sort_values(["pass", "rho_pooled"], ascending=[False, False], key=lambda s: s if s.dtype == bool else s.abs())
    res.to_csv(PILOT / "feature_screen.csv", index=False)

    # legacy comparators on the same 15
    leg_rows = []
    for c in LEGACY_COLS:
        col = f"legacy_{c}"
        leg_rows.append({"feature": c, "rho_pooled": _spearman(df[col], df["mIoU"]),
                         **{f"rho_{f}": _spearman(df.loc[df.family == f, col], df.loc[df.family == f, "mIoU"]) for f in fams},
                         "f000_minus_f008_sd": (df.loc[df.trial_id == "5-1-f000", col].iloc[0] - df.loc[df.trial_id == "5-1-f008", col].iloc[0]) / (df[col].std() or np.nan)})
    leg = pd.DataFrame(leg_rows)

    # delta stability of the correspondence family
    delta_rows = []
    for base in ["line_explained", "line_explained_obl", "line_explained_hor", "boundary_explained_line", "boundary_explained_edge", "correspondence_f1"]:
        delta_rows.append({"feature": base, **{f"rho@{d}": _spearman(df[f"{base}@{d}"], df["mIoU"]) for d in DELTAS}})
    dstab = pd.DataFrame(delta_rows)

    def fmt(x):
        return "" if (isinstance(x, float) and not np.isfinite(x)) else (f"{x:+.2f}" if isinstance(x, float) else str(x))

    def table(d: pd.DataFrame, cols: list[str]) -> str:
        head = "| " + " | ".join(cols) + " |\n|" + "---|" * len(cols) + "\n"
        body = "".join("| " + " | ".join(fmt(r[c]) for c in cols) + " |\n" for _, r in d.iterrows())
        return head + body

    n_pass = int(res["pass"].sum())
    md = [f"# SC-general pilot report\n\nGenerated {datetime.now().isoformat()}. "
          f"15 frozen calibration trials (5 per family, stratified on GT mIoU); replay prompt match "
          f"{int(df['replay_prompt_match'].sum())}/15; label-map sources: {df['labelmap_source'].value_counts().to_dict()}.\n",
          "\n## Panel\n\n", table(df.sort_values(["family", "mIoU"])[["family", "trial_id", "mIoU", "ring_count", "labelmap_source", "n_oblique_lines", "n_horizontal_lines", "boundary_px"]].assign(mIoU=lambda d: d.mIoU.astype(float)),
                                   ["family", "trial_id", "mIoU", "ring_count", "labelmap_source", "n_oblique_lines", "n_horizontal_lines", "boundary_px"]),
          f"\n## Candidate screen ({n_pass} pass)\n\nPass = same sign in all 3 families, sign matches expectation, |rho| >= 0.5 in >= 2 families, |rho| vs sam_fill_rate and depth_nan_ratio < 0.8. "
          "`f000_minus_f008_sd` is the must-separate complex pair gap in pooled-SD units (positive = good run scores higher).\n\n",
          table(res, ["feature", "rho_pooled", "rho_staggered", "rho_continuous", "rho_complex", "sign_consistent", "expected_sign_ok", "n_fam_strong", "rho_vs_fill", "rho_vs_nan", "f000_minus_f008_sd", "nan_count", "pass"]),
          "\n## Legacy features on the same 15 runs\n\n", table(leg, ["feature", "rho_pooled", "rho_staggered", "rho_continuous", "rho_complex", "f000_minus_f008_sd"]),
          "\n## Delta stability (pooled Spearman)\n\n", table(dstab, ["feature"] + [f"rho@{d}" for d in DELTAS]),
          "\n## Overlays\n\n" + "".join(f"- `pilot/overlays/{t}.png`\n" for t in df.sort_values(["family", "mIoU"]).trial_id),
          ]
    (PILOT / "report.md").write_text("".join(md), encoding="utf-8")
    print(f"wrote {PILOT / 'report.md'}  ({n_pass} candidates pass)")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--gate", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--report", action="store_true")
    args = ap.parse_args()
    if args.gate:
        if not run_gate():
            raise SystemExit("gate FAILED; not proceeding")
    if args.run:
        df = run_pilot()
        write_report(df)
    elif args.report:
        write_report(pd.read_csv(PILOT / "pilot_features.csv"))


if __name__ == "__main__":
    main()
