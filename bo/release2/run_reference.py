#!/usr/bin/env python3
"""Run one family-reference pipeline (stages 1-6) and write record.json.

Output: data/release2/references/<subset>/. Refuses to overwrite an existing
run unless --overwrite. Does not score a proxy.

Usage:
  ./venv/bin/python bo/release2/run_reference.py --subset 2-1
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
import time
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from bo.paths import REFERENCES_DIR, RELEASE2_DATA, REPO_ROOT  # noqa: E402
from bo.release2.measure import measure_run  # noqa: E402
from bo.runtime.metadata import expected_rings, family_of  # noqa: E402
from bo.runtime.pipeline import parse_performance, run_stages  # noqa: E402

INVARIANT_RE = re.compile(
    r"Canonical invariant \(label-free\): corr\(h, axis\)=([+-]?\d+(?:\.\d+)?) "
    r"\(expected sign ([+-]?\d+)\)"
)
RING_READ_RE = re.compile(r"corr\(h,\s*ring\)|axis_projection,\s*ring|h_ring_sign")


def params_sha256(params_dir: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(params_dir.glob("parameters_*.json")):
        digest.update(path.name.encode())
        digest.update(b"\0")
        digest.update(path.read_bytes())
    return digest.hexdigest()


def _checks(run_dir: Path, log_text: str) -> dict:
    only = run_dir / "only_label.csv"
    columns: list[str] = []
    if only.exists():
        header = only.read_text(encoding="utf-8", errors="ignore").splitlines()[:1]
        if header:
            columns = [c.strip() for c in header[0].split(",")]
    match = INVARIANT_RE.search(log_text)
    corr = float(match.group(1)) if match else None
    sign = int(match.group(2)) if match else None
    sign_ok = (
        corr is not None
        and sign is not None
        and abs(corr) >= 0.5
        and (1 if corr >= 0 else -1) == sign
    )
    return {
        "metadata_orientation": "Metadata orientation:" in log_text,
        "label_free_invariant": match is not None,
        "invariant_corr": corr,
        "invariant_expected_sign": sign,
        "invariant_ok": sign_ok,
        "only_label_columns": columns,
        "only_label_no_gt": bool(columns) and "gt_labels" not in columns and "gt_rings" not in columns,
        "ring_column_reads": len(RING_READ_RE.findall(log_text)),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--subset", required=True)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    subset = args.subset
    family = family_of(subset)
    params_dir = REFERENCES_DIR / family
    input_txt = REPO_ROOT / "data" / "subsets" / f"{subset}.txt"
    if not params_dir.is_dir():
        raise SystemExit(f"missing family reference: {params_dir}")
    if not input_txt.is_file():
        raise SystemExit(f"missing input cloud: {input_txt}")

    out_root = RELEASE2_DATA / "references"
    run_dir = out_root / subset
    if run_dir.exists() and any(run_dir.iterdir()) and not args.overwrite:
        raise SystemExit(
            f"refusing to overwrite non-empty {run_dir} (pass --overwrite)"
        )
    if args.overwrite and run_dir.exists():
        shutil.rmtree(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    log_path = run_dir / "pipeline.log"

    t0 = time.time()
    failure = None
    try:
        run_stages(
            run_id=subset,
            params_dir=params_dir,
            input_txt=input_txt,
            out_root=out_root,
            log_path=log_path,
        )
    except Exception as exc:  # noqa: BLE001
        failure = str(exc)
    elapsed = time.time() - t0
    log_text = log_path.read_text(encoding="utf-8", errors="ignore") if log_path.exists() else ""

    measured = None
    measure_error = None
    if failure is None:
        try:
            measured = measure_run(run_dir, subset, params_dir, log_text=log_text)
        except Exception as exc:  # noqa: BLE001
            measure_error = str(exc)
            failure = f"measurement failed: {exc}"

    perf = parse_performance(run_dir / "evaluation" / "performance.md")
    checks = _checks(run_dir, log_text)
    finite = bool(measured and measured["finite"])
    valid = (
        failure is None
        and finite
        and checks["metadata_orientation"]
        and checks["invariant_ok"]
        and checks["only_label_no_gt"]
        and checks["ring_column_reads"] == 0
    )
    record = {
        "subset": subset,
        "family": family,
        "params_dir": str(params_dir),
        "params_sha256": params_sha256(params_dir),
        "overlay": {},
        "input_txt": str(input_txt),
        "measurements": None if measured is None else measured["measurements"],
        "expected_rings": expected_rings(subset),
        "ring_count": None if measured is None else measured["ring_count"],
        "ring_count_source": None if measured is None else measured["ring_count_source"],
        "valid": valid,
        "gt_miou": perf.get("mIoU"),
        "elapsed_s": round(elapsed, 1),
        "log": str(log_path),
        "checks": checks,
        "failure": failure,
        "measure_error": measure_error,
    }
    (run_dir / "record.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"subset": subset, "valid": valid, "gt_miou": record["gt_miou"], "elapsed_s": record["elapsed_s"], "failure": failure}, indent=2))
    return 0 if valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
