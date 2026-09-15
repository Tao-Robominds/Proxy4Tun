#!/usr/bin/env python3
"""Campaign driver: run the 3-round cursor3 reflection trio for one subset.

Round recipes are family-level distillations of the cursor2/cursor3 winners
(Fable reflection): the t1&2 trio derives from the 1-5 round-2 winner
(validated on 2-2), the t3 trio from the 3-5/3-4 widen winner plus the 3-2
stage-1 seed fix, and the t4&5 trio from the 4-4 winner as adapted on 4-1.
Stage-1 (unfolding) overlays are only issued when the subset is in
STAGE1_UNLOCK (anchor residual > 10 cm per bo-full-stage/stage1_gate.md).

Usage:
  ./venv/bin/python bo/proxy_scale/run_subset.py --subset 5-2
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))
from bo.paths import PROXY_SCALE_PKG, REPO_ROOT, UNIFIED_PKG, VENV_PY

PILOT = UNIFIED_PKG / "reflect_pilot.py"
PY = VENV_PY
ARM = "cursor3"

STAGE1_UNLOCK = {"3-4", "3-2", "3-8"}  # anchor residual > 10 cm (holdout table)

T12_R1 = {
    "denoising": {"mask_r_low": 2.495, "mask_r_high": 2.782, "z_step": 0.0026},
    "enhancing": {"curvature_threshold": 0.0078, "inter_radius": 0.067},
    "detecting": {
        "binary_threshold": 154,
        "hough_threshold_oblique": 84,
        "hough_threshold_horizontal": 83,
        "hough_threshold_vertical": 680,
        "maxLineGap_oblique": 35,
    },
    "sam": {"processing.y_bounds": [4196, 13300]},
}
T12_R2 = {
    "denoising": {"mask_r_low": 2.495, "mask_r_high": 2.782, "z_step": 0.0026},
    "enhancing": {"curvature_threshold": 0.0078, "inter_radius": 0.067},
    "detecting": {
        "binary_threshold": 140,
        "hough_threshold_oblique": 75,
        "hough_threshold_horizontal": 75,
        "hough_threshold_vertical": 700,
        "maxLineGap_oblique": 40,
    },
    "sam": {"processing.y_bounds": [4196, 13300]},
}
T12_R3 = {
    "enhancing": {"curvature_threshold": 0.005, "inter_radius": 0.06},
    "sam": {
        "segment_width": 1150,
        "K_height": 1050.0,
        "angle": 7.3,
        "processing.y_bounds": [4300, 13000],
    },
}

T3_WIDEN = {
    "denoising": {
        "mask_r_low": 2.7,
        "mask_r_high": 3.12,
        "mask_theta_low": 1.0,
        "mask_theta_high": 18.5,
    },
    "enhancing": {"curvature_threshold": 0.0015},
    "detecting": {
        "binary_threshold": 110,
        "hough_threshold_oblique": 22,
        "hough_threshold_horizontal": 22,
        "hough_threshold_vertical": 2200,
        "maxLineGap_oblique": 50,
        "pattern_tolerance": 18,
        "uniform_k_snap": True,
    },
    "sam": {"segment_width": 1100, "K_height": 880, "angle": 7.0},
}

T45_R1 = {
    "denoising": {"mask_r_low": 3.55, "mask_r_high": 3.95},
    "enhancing": {"curvature_threshold": 0.001},
    "detecting": {
        "hough_threshold_oblique": 40,
        "hough_threshold_horizontal": 30,
        "maxLineGap_oblique": 70,
        "maxLineGap_horizontal": 20,
        "pattern_tolerance": 12,
    },
}
T45_R2 = {
    "denoising": {"mask_r_low": 3.6, "mask_r_high": 3.95},
    "enhancing": {"curvature_threshold": 0.0008},
    "detecting": {
        "binary_threshold": 110,
        "hough_threshold_oblique": 35,
        "hough_threshold_horizontal": 25,
        "maxLineGap_oblique": 60,
        "pattern_tolerance": 14,
    },
}
T45_R3 = {
    "denoising": {"mask_r_low": 3.6, "mask_r_high": 3.95, "z_step": 0.002, "grad_threshold": 0.18},
    "enhancing": {"curvature_threshold": 0.0008, "inter_radius": 0.07},
    "detecting": {
        "binary_threshold": 110,
        "hough_threshold_oblique": 35,
        "hough_threshold_horizontal": 25,
        "maxLineGap_oblique": 60,
        "pattern_tolerance": 14,
    },
    "sam": {"segment_width": 1700, "K_height": 1200.0},
}


def trios(subset: str) -> list[dict]:
    fam = subset.split("-")[0]
    if fam in ("1", "2"):
        return [T12_R1, T12_R2, T12_R3]
    if fam == "3":
        if subset in STAGE1_UNLOCK:
            seed = {"unfolding": {"random_seed": 0}}
            combined = {**T3_WIDEN, "unfolding": {"random_seed": 0}}
            return [T3_WIDEN, seed, combined]
        lite = json.loads(json.dumps(T3_WIDEN))
        lite["detecting"]["binary_threshold"] = 120
        lite["detecting"]["hough_threshold_oblique"] = 26
        no_sam = {k: v for k, v in T3_WIDEN.items() if k != "sam"}
        return [T3_WIDEN, lite, no_sam]
    if fam in ("4", "5"):
        r1 = dict(T45_R1)
        if fam == "4":
            r1 = json.loads(json.dumps(T45_R1))
            r1["detecting"]["hough_threshold_vertical"] = 1200
        return [r1, T45_R2, T45_R3]
    raise ValueError(f"unknown family for {subset}")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--subset", required=True)
    args = p.parse_args()

    for i, overlay in enumerate(trios(args.subset), start=1):
        cmd = [
            str(PY), str(PILOT),
            "--subset", args.subset,
            "--round", str(i),
            "--arm", ARM,
            "--overlay-json", json.dumps(overlay),
        ]
        if overlay.get("unfolding"):
            cmd.append("--full")
        print(f"=== {args.subset} round {i} ===", flush=True)
        subprocess.run(cmd, check=False, cwd=REPO_ROOT)

    subprocess.run(
        [str(PY), str(PROXY_SCALE_PKG / "select_round.py"),
         "--subset", args.subset, "--arm", ARM],
        check=True, cwd=REPO_ROOT,
    )


if __name__ == "__main__":
    main()
