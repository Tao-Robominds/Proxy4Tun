#!/usr/bin/env python3
"""Build the Release-3 training table with rotation_advantage and synthetic copies.

Calibration trial dirs under inputs/calibration were slimmed (no final.csv), so
rotation_advantage is 0 for those 120 originals. Synthetic rotations are built
from the 30 full reference runs under inputs/references/, which keep final.csv.
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from bo.paths import REFERENCES_DIR, RELEASE3_DATA  # noqa: E402
from bo.release3.rotation_features import compute_rotation_features  # noqa: E402
from bo.release3.synth_rotate import offline_gt_miou, write_shifted_run  # noqa: E402
from bo.runtime.metadata import DEV_SUBSETS, family_of  # noqa: E402
from bo.sc_general.label_map import block_to_label_from_config, load_sam_config  # noqa: E402

INPUT_CAL = RELEASE3_DATA / "inputs" / "calibration"
INPUT_REF = RELEASE3_DATA / "inputs" / "references"
OUT = RELEASE3_DATA / "calibration" / "records"
SYNTH_ROOT = RELEASE3_DATA / "calibration" / "synth"
FEATURE = "rotation_advantage"
FOUR = (
    "correspondence_f1@15",
    "sam_fill_rate",
    "ring_count_error",
    "depth_nan_ratio",
)


def _safe_rm(path: Path) -> None:
    if not path.exists():
        return
    for p in path.rglob("*"):
        try:
            p.chmod(p.stat().st_mode | 0o200)
        except OSError:
            pass
    try:
        path.chmod(path.stat().st_mode | 0o200)
    except OSError:
        pass
    import shutil

    shutil.rmtree(path)


def main() -> int:
    src_table = INPUT_CAL / "records" / "training_table.csv"
    rows = list(csv.DictReader(src_table.open()))
    if len(rows) != 120:
        raise SystemExit(f"expected 120 rows, found {len(rows)}")

    OUT.mkdir(parents=True, exist_ok=True)
    SYNTH_ROOT.mkdir(parents=True, exist_ok=True)

    out_rows = []
    for row in rows:
        new = dict(row)
        new[FEATURE] = "0"
        new["key_block_mismatch"] = "nan"
        new["key_observability"] = "nan"
        new["synthetic"] = "false"
        new["shift"] = "0"
        new["source"] = "calibration"
        out_rows.append(new)

    ref_dirs = sorted(p for p in INPUT_REF.iterdir() if p.is_dir() and (p / "final.csv").exists())
    print(f"augmenting from {len(ref_dirs)} references", flush=True)
    for ref in ref_dirs:
        subset = ref.name
        fam = family_of(subset)
        params = REFERENCES_DIR / fam
        rec = json.loads((ref / "record.json").read_text())
        base_m = rec["measurements"]
        cfg = load_sam_config(ref, params_dir=params)
        _b2l, order = block_to_label_from_config(cfg)
        n = len(order)
        base_rot = compute_rotation_features(ref, params_dir=params, subset=subset)
        # Keep an unrotated reference row too (with measured rotation feature).
        base_row = {
            "family": fam,
            "dev": subset if subset in DEV_SUBSETS else f"ref:{subset}",
            "trial_id": "reference",
            "acquisition": "reference",
            "unfold_residual": base_m.get("unfold_residual"),
            "orient_agreement": base_m.get("orient_agreement"),
            "denoise_retained_ratio": base_m.get("denoise_retained_ratio"),
            "depth_nan_ratio": base_m["depth_nan_ratio"],
            "ring_count_error": base_m["ring_count_error"],
            "boundary_explained_edge@25": base_m.get("boundary_explained_edge@25"),
            "correspondence_f1@15": base_m["correspondence_f1@15"],
            "chamfer_sym_px": base_m.get("chamfer_sym_px"),
            "sam_fill_rate": base_m["sam_fill_rate"],
            "phase_incoherence_deg": base_m.get("phase_incoherence_deg"),
            "gt_miou": rec["gt_miou"],
            FEATURE: f"{base_rot[FEATURE]:.10g}",
            "key_block_mismatch": f"{base_rot['key_block_mismatch']:.10g}",
            "key_observability": f"{base_rot['key_observability']:.10g}",
            "synthetic": "false",
            "shift": "0",
            "source": "reference",
        }
        out_rows.append(base_row)

        for shift in range(1, n):
            dst = SYNTH_ROOT / f"{subset}_k{shift}"
            _safe_rm(dst)
            write_shifted_run(ref, dst, shift=shift, params_dir=params, light=True)
            rot = compute_rotation_features(dst, params_dir=dst, subset=subset)
            gt = offline_gt_miou(dst, subset)
            syn = dict(base_row)
            syn["trial_id"] = f"reference_rot{shift}"
            syn["gt_miou"] = f"{gt:.10g}"
            syn[FEATURE] = f"{rot[FEATURE]:.10g}"
            syn["key_block_mismatch"] = f"{rot['key_block_mismatch']:.10g}"
            syn["key_observability"] = f"{rot['key_observability']:.10g}"
            syn["synthetic"] = "true"
            syn["shift"] = str(shift)
            # Four proxy features unchanged under pure label rotation.
            for k in FOUR:
                syn[k] = base_m[k]
            out_rows.append(syn)
        print(f"  {subset}: +{n - 1} synthetic", flush=True)

    # Normalise fieldnames across mixed rows.
    fieldnames: list[str] = []
    seen = set()
    for r in out_rows:
        for k in r:
            if k not in seen:
                seen.add(k)
                fieldnames.append(k)
    out_path = OUT / "training_table.csv"
    with out_path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        w.writerows(out_rows)

    n_syn = sum(1 for r in out_rows if str(r.get("synthetic")).lower() == "true")
    summary = {
        "n_total": len(out_rows),
        "n_calibration_original": 120,
        "n_reference_original": len(ref_dirs),
        "n_synthetic": n_syn,
        "feature": FEATURE,
        "path": str(out_path),
        "note": (
            "calibration runs lack final.csv; rotation_advantage=0 there. "
            "Synthetic rotations come from the 30 reference runs."
        ),
    }
    (OUT / "training_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
