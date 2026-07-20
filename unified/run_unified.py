#!/usr/bin/env python3
"""Run the unified multi-family pipeline for a first-subset case.

Usage:
  ./venv/bin/python unified/run_unified.py --case 1-1
  ./venv/bin/python unified/run_unified.py --case 3-1-1 --overwrite
  ./venv/bin/python unified/run_unified.py --case 4-1 --through-stage 3

Outputs go under data/unified/<case>/ (never data/anchors/).
Params come from unified/params/<case>/ which includes parameters_family.json.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
UNIFIED_DIR = Path(__file__).resolve().parent
SAM4TUN = REPO_ROOT / "sam4tun"

# Case -> (input subset stem under data/subsets/, output dir name under data/unified/)
CASE_MAP = {
    "1-1": {"input": "1-1", "out": "1-1", "anchor_miou": 0.787},
    "2-1": {"input": "2-1", "out": "2-1", "anchor_miou": 0.874},
    "3-1-1": {"input": "3-1", "out": "3-1-1", "anchor_miou": 0.850},
    "4-1": {"input": "4-1", "out": "4-1", "anchor_miou": 0.635},
    "5-1": {"input": "5-1", "out": "5-1", "anchor_miou": 0.808},
}

STAGES = [
    "1_unfolding.py",
    "2_denoising.py",
    "3_enhancing.py",
    "4_detection.py",
    "5_sam.py",
    "6_evaluation.py",
]


def parse_miou(case_out: Path) -> float | None:
    perf = case_out / "evaluation" / "performance.md"
    if not perf.is_file():
        return None
    for line in perf.read_text(encoding="utf-8").splitlines():
        if "Mean IoU" in line or "mIoU" in line:
            # e.g. "- Mean IoU (mIoU): 0.787"
            for tok in line.replace("=", " ").replace(":", " ").split():
                try:
                    v = float(tok)
                    if 0.0 <= v <= 1.0:
                        return v
                except ValueError:
                    continue
    return None


def run_case(
    case: str,
    *,
    overwrite: bool = False,
    through_stage: int = 6,
    out_root: Path | None = None,
) -> dict:
    if case not in CASE_MAP:
        raise SystemExit(f"Unknown case {case!r}; choose from {sorted(CASE_MAP)}")
    cfg = CASE_MAP[case]
    input_txt = REPO_ROOT / "data" / "subsets" / f"{cfg['input']}.txt"
    if not input_txt.is_file():
        raise SystemExit(f"Missing input: {input_txt}")

    params_dir = UNIFIED_DIR / "params" / case
    if not (params_dir / "parameters_family.json").is_file():
        raise SystemExit(f"Missing params for {case}: {params_dir}")

    out_root = (out_root or (REPO_ROOT / "data" / "unified")).resolve()
    out_root.mkdir(parents=True, exist_ok=True)
    case_out = out_root / cfg["out"]
    if case_out.exists() and any(case_out.iterdir()) and not overwrite:
        raise SystemExit(
            f"Output exists and is non-empty: {case_out}\n"
            f"Pass --overwrite to replace (never writes into data/anchors/)."
        )
    case_out.mkdir(parents=True, exist_ok=True)

    fam = json.loads((params_dir / "parameters_family.json").read_text(encoding="utf-8"))
    mode = fam.get("family_mode")
    print(f"=== unified run case={case} mode={mode} out={case_out} ===", flush=True)

    env = os.environ.copy()
    env["PROXY4TUN_OUT_ROOT"] = str(out_root)
    env["PROXY4TUN_INPUT_TXT"] = str(input_txt)
    env["PROXY4TUN_PARAMS_DIR"] = str(params_dir)
    env["PYTHONPATH"] = os.pathsep.join(
        [
            str(UNIFIED_DIR),
            str(SAM4TUN),
            str(SAM4TUN / "segment-anything"),
            env.get("PYTHONPATH", ""),
        ]
    ).rstrip(os.pathsep)
    env["MPLBACKEND"] = env.get("MPLBACKEND", "Agg")

    t0 = time.time()
    for stage in STAGES[:through_stage]:
        script = UNIFIED_DIR / stage
        print(f"\n=== {stage} ===", flush=True)
        subprocess.run(
            [sys.executable, "-u", str(script), cfg["out"]],
            cwd=str(REPO_ROOT),
            env=env,
            check=True,
        )
    elapsed = time.time() - t0
    miou = parse_miou(case_out) if through_stage >= 6 else None
    rec = {
        "case": case,
        "family_mode": mode,
        "input_txt": str(input_txt),
        "params_dir": str(params_dir),
        "output_dir": str(case_out),
        "anchor_miou": cfg["anchor_miou"],
        "unified_miou": miou,
        "delta": (None if miou is None else round(miou - cfg["anchor_miou"], 4)),
        "elapsed_s": round(elapsed, 1),
        "through_stage": through_stage,
    }
    print(f"\n=== done case={case} mIoU={miou} (anchor {cfg['anchor_miou']}) ===", flush=True)
    return rec


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--case", required=True, choices=sorted(CASE_MAP))
    ap.add_argument("--overwrite", action="store_true")
    ap.add_argument("--through-stage", type=int, default=6, choices=range(1, 7))
    ap.add_argument("--out-root", type=Path, default=None)
    args = ap.parse_args()
    rec = run_case(
        args.case,
        overwrite=args.overwrite,
        through_stage=args.through_stage,
        out_root=args.out_root,
    )
    print(json.dumps(rec, indent=2))


if __name__ == "__main__":
    main()
