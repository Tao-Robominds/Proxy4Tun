#!/usr/bin/env python3
"""Re-score Release-3 copied reference/degraded runs with the five-feature proxy."""

from __future__ import annotations

import csv
import json
import math
import sys
from pathlib import Path

import numpy as np
from scipy import stats
from sklearn.metrics import mean_absolute_error

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from bo.paths import REFERENCES_DIR, RELEASE3_DATA  # noqa: E402
from bo.release3.rotation_features import compute_rotation_features  # noqa: E402
from bo.release3.score import score_measurements  # noqa: E402
from bo.release3.synth_rotate import offline_gt_miou, write_shifted_run  # noqa: E402
from bo.runtime.metadata import family_of  # noqa: E402

INPUTS = RELEASE3_DATA / "inputs"
OUT = RELEASE3_DATA / "degradation"
R2_RHO = 0.791
R2_MAE = 0.106
R2_PAIR = 27


def _params_for(run_dir: Path, subset: str) -> Path:
    local = run_dir / "params"
    if (local / "parameters_sam.json").exists():
        return local
    return REFERENCES_DIR / family_of(subset)


def _rotation(run_dir: Path, subset: str) -> float:
    if not (run_dir / "final.csv").exists():
        return 0.0
    params = _params_for(run_dir, subset)
    rot = compute_rotation_features(run_dir, params_dir=params, subset=subset)
    val = float(rot["rotation_advantage"])
    return 0.0 if not math.isfinite(val) else val


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    pairs_src = INPUTS / "degradation" / "records" / "pairs.csv"
    old = list(csv.DictReader(pairs_src.open()))
    rows = []
    for row in old:
        subset = row["subset"]
        arm = row["arm"]
        if arm == "reference":
            run_dir = INPUTS / "references" / subset
        else:
            run_dir = INPUTS / "degradation" / subset
        measurements = {
            "correspondence_f1@15": float(row["correspondence_f1@15"]),
            "sam_fill_rate": float(row["sam_fill_rate"]),
            "ring_count_error": float(row["ring_count_error"]),
            "depth_nan_ratio": float(row["depth_nan_ratio"]),
            "rotation_advantage": _rotation(run_dir, subset),
        }
        scored = score_measurements(measurements)
        rows.append(
            {
                "subset": subset,
                "family": row["family"],
                "arm": arm,
                **{k: measurements[k] for k in measurements},
                "score": scored["score"],
                "band": scored["band"],
                "gt_miou": float(row["gt_miou"]),
                "score_r2": float(row["score"]),
            }
        )
        print(f"{subset}/{arm}: r2={row['score']} -> r3={scored['score']:.4f} rot={measurements['rotation_advantage']:.4f}", flush=True)

    # Synthetic rotation check on a few references.
    synth_checks = []
    for subset in ("1-1", "3-3", "5-5"):
        src = INPUTS / "references" / subset
        dst = OUT / "synth_check" / f"{subset}_k1"
        write_shifted_run(src, dst, shift=1, params_dir=REFERENCES_DIR / family_of(subset), light=True)
        base = next(r for r in rows if r["subset"] == subset and r["arm"] == "reference")
        m = {
            "correspondence_f1@15": base["correspondence_f1@15"],
            "sam_fill_rate": base["sam_fill_rate"],
            "ring_count_error": base["ring_count_error"],
            "depth_nan_ratio": base["depth_nan_ratio"],
            "rotation_advantage": _rotation(dst, subset),
        }
        sc = score_measurements(m)
        synth_checks.append(
            {
                "subset": subset,
                "base_score": base["score"],
                "rotated_score": sc["score"],
                "rotated_gt": offline_gt_miou(dst, subset),
                "rotation_advantage": m["rotation_advantage"],
                "ok": sc["score"] < base["score"] - 1e-4,
            }
        )

    y = np.asarray([r["gt_miou"] for r in rows], dtype=float)
    pred = np.asarray([r["score"] for r in rows], dtype=float)
    rho = float(stats.spearmanr(y, pred).correlation)
    mae = float(mean_absolute_error(y, pred))
    pair_ok = 0
    for subset in sorted({r["subset"] for r in rows}):
        ref = next(r for r in rows if r["subset"] == subset and r["arm"] == "reference")
        deg = next(r for r in rows if r["subset"] == subset and r["arm"] == "degraded")
        if ref["score"] > deg["score"]:
            pair_ok += 1

    admitted = sorted(
        r["subset"]
        for r in rows
        if r["arm"] == "reference" and 0.5 <= r["score"] <= 0.7
    )
    r2_admitted = [
        "1-1", "1-3", "1-5", "3-10", "3-3", "3-4", "3-6", "3-7", "3-8", "3-9",
        "4-1", "4-2", "4-3", "4-4", "5-5",
    ]
    overlap = sorted(set(admitted) & set(r2_admitted))

    pass_rho = rho >= R2_RHO - 0.05  # allow small tolerance
    pass_mae = mae <= R2_MAE + 0.05
    pass_pair = pair_ok >= R2_PAIR - 1
    pass_synth = all(c["ok"] for c in synth_checks)
    passed = pass_rho and pass_mae and pass_pair and pass_synth

    out_csv = OUT / "records" / "pairs.csv"
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    summary = {
        "rho": rho,
        "mae": mae,
        "pair_ranking": f"{pair_ok}/27",
        "r2_rho": R2_RHO,
        "r2_mae": R2_MAE,
        "pass_rho": pass_rho,
        "pass_mae": pass_mae,
        "pass_pair": pass_pair,
        "pass_synth": pass_synth,
        "passed": passed,
        "admitted": admitted,
        "r2_admitted": r2_admitted,
        "overlap": overlap,
        "synth_checks": synth_checks,
    }
    (OUT / "records" / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    lines = [
        "# Release 3 degradation re-score",
        "",
        f"- Spearman rho: {rho:.3f} (Release 2 {R2_RHO:.3f}) pass={pass_rho}",
        f"- MAE: {mae:.3f} (Release 2 {R2_MAE:.3f}) pass={pass_mae}",
        f"- Strict pair ranking: {pair_ok}/27 pass={pass_pair}",
        f"- Synthetic rotated refs scored lower: {pass_synth}",
        f"- **Overall gate: {'PASS' if passed else 'FAIL'}**",
        "",
        f"Admitted ({len(admitted)}): {', '.join(admitted)}",
        f"Overlap with Release 2 15: {len(overlap)} — {', '.join(overlap)}",
        "",
    ]
    (OUT / "records" / "summary.md").write_text("\n".join(lines) + "\n")
    (OUT / "admitted.json").write_text(json.dumps({"admitted": admitted, "overlap": overlap}, indent=2) + "\n")
    print("\n".join(lines))
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
