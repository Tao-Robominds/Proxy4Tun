#!/usr/bin/env python3
"""Drive the SC-general Stage-3 refinement campaign (22 cases × 3 rounds).

Overlays are GT-blind, family-bounded recipes chosen from the context packet
features (F1, fill, residual unlock, fallback). Each proposal is logged to
data/sc-general/stage3/campaign.md before execution.

Usage:
  ./venv/bin/python bo/sc_general/run_campaign.py                 # all remaining
  ./venv/bin/python bo/sc_general/run_campaign.py --subset 3-4    # one case
  ./venv/bin/python bo/sc_general/run_campaign.py --subset 3-4 --from-round 2
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from bo.sc_general.refine_pilot import (  # noqa: E402
    build_context,
    out_root_for,
    run_round,
)
from bo.sc_general.select_round import select  # noqa: E402
from bo.sc_general.score_scaled import score_run, anchor_run_dir  # noqa: E402
from bo.runtime.spaces import FAMILY_MODE, family_of_subset  # noqa: E402

STAGE3 = _REPO / "data" / "sc-general" / "stage3"
CAMPAIGN = STAGE3 / "campaign.md"
PANEL = [
    "1-3", "1-5", "1-1", "1-4", "1-2", "2-4", "2-2",
    "3-4", "3-3", "3-7", "3-8", "3-10", "3-9", "3-6",
    "4-3", "4-2", "4-1", "4-5", "5-5", "5-3", "5-2", "5-4",
]


def _append_campaign(text: str) -> None:
    STAGE3.mkdir(parents=True, exist_ok=True)
    if not CAMPAIGN.exists():
        CAMPAIGN.write_text(
            "# SC-general Stage-3 refinement campaign\n\n"
            "GT-blind reflective loop. Proxy = pruned_lean. Panel = proxy ∈ [0.5, 0.7].\n\n",
            encoding="utf-8",
        )
    with CAMPAIGN.open("a", encoding="utf-8") as fh:
        fh.write(text)
        if not text.endswith("\n"):
            fh.write("\n")


def propose(subset: str, round_id: int, ctx: dict[str, Any]) -> dict[str, Any]:
    """GT-blind overlay proposal from context features."""
    fam = ctx["family"]
    anchor = ctx["anchor"]
    feats = anchor["features"]
    f1 = float(feats["correspondence_f1@15"])
    fill = float(feats["sam_fill_rate"])
    nan = float(feats["depth_nan_ratio"])
    unlocked = bool(ctx["stage1_unlocked"])
    intr = ctx.get("intrinsics_gt_blind") or {}
    fallback = float(intr.get("det_fallback_ratio") or 0.0)
    hist = ctx.get("history") or []

    # Prefer the latest round's features when proposing R2/R3.
    if hist:
        last = hist[-1]
        if last.get("features"):
            f1 = float(last["features"].get("correspondence_f1@15", f1))
            fill = float(last["features"].get("sam_fill_rate", fill))
            nan = float(last["features"].get("depth_nan_ratio", nan))

    if fam == "t1&2":
        return _propose_t12(subset, round_id, f1, fill, nan, unlocked)
    if fam == "t3":
        return _propose_t3(subset, round_id, f1, fill, nan, unlocked, fallback, hist)
    return _propose_t45(subset, round_id, f1, fill, nan, unlocked, fallback, hist)


def _propose_t12(subset, round_id, f1, fill, nan, unlocked) -> dict[str, Any]:
    # Staggered: K-row / template sensitivity; raise Hough, retune mask + y_bounds.
    if round_id == 1:
        observation = (
            f"F1@15={f1:.3f} fill={fill:.3f} nan={nan:.3f}. "
            "Detection mostly real; SC bottleneck is line↔boundary agreement / SAM crop."
        )
        failure = "f_template_mismatch / weak correspondence"
        overlay = {
            "denoising": {
                "mask_r_low": 2.40,
                "mask_r_high": 2.85,
                "z_step": 0.003,
                "grad_threshold": 0.18,
            },
            "enhancing": {"curvature_threshold": 0.006, "inter_radius": 0.055},
            "detecting": {
                "binary_threshold": 120,
                "hough_threshold_oblique": 75,
                "hough_threshold_horizontal": 75,
                "hough_threshold_vertical": 700,
                "maxLineGap_oblique": 35,
            },
            "sam": {"processing.y_bounds": [4200, 13300]},
        }
        rationale = "1-5-style multi-stage: tighten Hough + raise y_bounds lower + mask/curv retune."
    elif round_id == 2:
        observation = f"After R1: F1={f1:.3f} fill={fill:.3f}. Probe milder Hough / wider gap."
        failure = "over-suppressed joints or residual K-crop mismatch"
        overlay = {
            "denoising": {
                "mask_r_low": 2.30,
                "mask_r_high": 2.80,
                "z_step": 0.004,
                "grad_threshold": 0.16,
            },
            "enhancing": {"curvature_threshold": 0.004, "inter_radius": 0.045},
            "detecting": {
                "binary_threshold": 110,
                "hough_threshold_oblique": 60,
                "hough_threshold_horizontal": 60,
                "hough_threshold_vertical": 550,
                "maxLineGap_oblique": 50,
            },
            "sam": {"processing.y_bounds": [4000, 13300]},
        }
        rationale = "Relax Hough slightly; widen gap; nudge y_bounds toward K band."
    else:
        observation = f"R3 alternate: F1={f1:.3f} fill={fill:.3f}."
        failure = "incomplete correspondence; try denser retention + stronger vertical"
        overlay = {
            "denoising": {
                "mask_r_low": 2.35,
                "mask_r_high": 2.88,
                "z_step": 0.002,
                "grad_threshold": 0.20,
            },
            "enhancing": {"curvature_threshold": 0.005, "inter_radius": 0.06},
            "detecting": {
                "binary_threshold": 130,
                "hough_threshold_oblique": 80,
                "hough_threshold_horizontal": 70,
                "hough_threshold_vertical": 750,
                "maxLineGap_oblique": 40,
            },
            "sam": {"processing.y_bounds": [4300, 13300]},
        }
        rationale = "Third recipe: stronger vertical Hough + lower z_step for denser lining."
    if unlocked:
        overlay["unfolding"] = {"random_seed": int(round_id % 8)}
        rationale += " Stage-1 unlocked: include unfolding.random_seed."
    return {
        "observation": observation,
        "failure_mode": failure,
        "rationale": rationale,
        "overlay": overlay,
    }


def _propose_t3(subset, round_id, f1, fill, nan, unlocked, fallback, hist) -> dict[str, Any]:
    # Continuous: fallback often 1.0 — need real Hough lines to lift F1.
    if round_id == 1:
        observation = (
            f"F1@15={f1:.3f} fill={fill:.3f} nan={nan:.3f} fallback={fallback:.2f}. "
            "Uniform-K continuous; correspondence weak when Hough falls back."
        )
        failure = "f_detection_fallback / low line↔boundary F1"
        overlay = {
            "denoising": {
                "mask_r_low": 2.85,
                "mask_r_high": 3.05,
                "mask_theta_low": 1.5,
                "mask_theta_high": 17.0,
            },
            "enhancing": {"curvature_threshold": 0.0008},
            "detecting": {
                "binary_threshold": 120,
                "hough_threshold_oblique": 35,
                "hough_threshold_horizontal": 35,
                "hough_threshold_vertical": 1600,
                "maxLineGap_oblique": 40,
                "pattern_tolerance": 12,
                "uniform_k_snap": True,
            },
            "sam": {"segment_width": 1200, "K_height": 900, "angle": 6.0},
        }
        rationale = (
            "Moderate Hough (not ultra-low) to recover real joints without flooding "
            "spurious lines that tank F1; keep uniform_k_snap."
        )
    elif round_id == 2:
        if unlocked:
            observation = f"Residual unlocked; F1={f1:.3f}. Probe stage-1 seed."
            failure = "f_centreline_residual"
            overlay = {"unfolding": {"random_seed": 0}}
            rationale = "Stage-1 seed probe (seed 0) with frozen later stages from overlay materialization of base+seed."
        else:
            observation = f"F1={f1:.3f} fill={fill:.3f}. Try wider mask + lower binary."
            failure = "f_depth_incomplete or weak edges"
            overlay = {
                "denoising": {
                    "mask_r_low": 2.75,
                    "mask_r_high": 3.12,
                    "mask_theta_low": 1.2,
                    "mask_theta_high": 18.0,
                },
                "enhancing": {"curvature_threshold": 0.0012},
                "detecting": {
                    "binary_threshold": 105,
                    "hough_threshold_oblique": 28,
                    "hough_threshold_horizontal": 28,
                    "hough_threshold_vertical": 2000,
                    "maxLineGap_oblique": 55,
                    "pattern_tolerance": 15,
                    "uniform_k_snap": True,
                },
                "sam": {"segment_width": 1150, "K_height": 850, "angle": 7.0},
            }
            rationale = "Widen retention + slightly lower Hough to catch more joint evidence."
    else:
        if unlocked:
            observation = f"Combine seed 5 with detection recipe; F1={f1:.3f}."
            failure = "f_centreline_residual + weak correspondence"
            overlay = {
                "unfolding": {"random_seed": 5},
                "denoising": {
                    "mask_r_low": 2.85,
                    "mask_r_high": 3.05,
                    "mask_theta_low": 1.5,
                    "mask_theta_high": 17.0,
                },
                "enhancing": {"curvature_threshold": 0.0008},
                "detecting": {
                    "binary_threshold": 120,
                    "hough_threshold_oblique": 35,
                    "hough_threshold_horizontal": 35,
                    "hough_threshold_vertical": 1600,
                    "maxLineGap_oblique": 40,
                    "pattern_tolerance": 12,
                    "uniform_k_snap": True,
                },
                "sam": {"segment_width": 1200, "K_height": 900, "angle": 6.0},
            }
            rationale = "Combined stage-1 seed 5 + R1 detection recipe."
        else:
            observation = f"R3 alternate SAM/Hough; F1={f1:.3f} fill={fill:.3f}."
            failure = "f_sam_crop_mismatch"
            overlay = {
                "denoising": {
                    "mask_r_low": 2.90,
                    "mask_r_high": 3.10,
                    "mask_theta_low": 1.8,
                    "mask_theta_high": 16.5,
                },
                "enhancing": {"curvature_threshold": 0.0005},
                "detecting": {
                    "binary_threshold": 140,
                    "hough_threshold_oblique": 45,
                    "hough_threshold_horizontal": 40,
                    "hough_threshold_vertical": 1800,
                    "maxLineGap_oblique": 30,
                    "pattern_tolerance": 10,
                    "uniform_k_snap": True,
                },
                "sam": {"segment_width": 1300, "K_height": 950, "angle": 5.0},
            }
            rationale = "Cleaner edges (higher binary) + larger SAM window."
    return {
        "observation": observation,
        "failure_mode": failure,
        "rationale": rationale,
        "overlay": overlay,
    }


def _propose_t45(subset, round_id, f1, fill, nan, unlocked, fallback, hist) -> dict[str, Any]:
    if round_id == 1:
        observation = (
            f"F1@15={f1:.3f} fill={fill:.3f} nan={nan:.3f} fallback={fallback:.2f}. "
            "Complex irregular K; widen mask and raise vertical Hough hard."
        )
        failure = "f_detection_sparse / complex layout mismatch"
        overlay = {
            "denoising": {"mask_r_low": 3.55, "mask_r_high": 3.95},
            "enhancing": {"curvature_threshold": 0.001},
            "detecting": {
                "binary_threshold": 120,
                "hough_threshold_oblique": 40,
                "hough_threshold_horizontal": 30,
                "hough_threshold_vertical": 3500,
                "maxLineGap_oblique": 70,
                "maxLineGap_horizontal": 20,
                "pattern_tolerance": 12,
            },
            "sam": {"segment_width": 1700, "K_height": 1150, "angle": 9.0},
        }
        rationale = "4-4 cursor2 coordinated recipe: widen mask, hard vertical, live SAM sizes."
    elif round_id == 2:
        if unlocked:
            observation = f"Residual unlocked ({unlocked}); F1={f1:.3f}. Stage-1 seed probe."
            failure = "f_centreline_residual"
            overlay = {"unfolding": {"random_seed": 1}}
            rationale = "Stage-1 unlock seed 1 (sibling of healthy complex anchors)."
        else:
            observation = f"F1={f1:.3f} fill={fill:.3f}. Alternate: looser oblique, taller K."
            failure = "f_k_height_mismatch"
            overlay = {
                "denoising": {"mask_r_low": 3.60, "mask_r_high": 4.00},
                "enhancing": {"curvature_threshold": 0.0006},
                "detecting": {
                    "binary_threshold": 110,
                    "hough_threshold_oblique": 32,
                    "hough_threshold_horizontal": 28,
                    "hough_threshold_vertical": 2800,
                    "maxLineGap_oblique": 75,
                    "maxLineGap_horizontal": 15,
                    "pattern_tolerance": 15,
                },
                "sam": {"segment_width": 1900, "K_height": 1300, "angle": 10.0},
            }
            rationale = "Widen SAM K_height/width; slightly looser oblique Hough."
    else:
        if unlocked:
            observation = f"Combine seed 3 with R1 recipe; F1={f1:.3f}."
            failure = "f_centreline_residual + sparse detection"
            overlay = {
                "unfolding": {"random_seed": 3},
                "denoising": {"mask_r_low": 3.55, "mask_r_high": 3.95},
                "enhancing": {"curvature_threshold": 0.001},
                "detecting": {
                    "binary_threshold": 120,
                    "hough_threshold_oblique": 40,
                    "hough_threshold_horizontal": 30,
                    "hough_threshold_vertical": 3500,
                    "maxLineGap_oblique": 70,
                    "maxLineGap_horizontal": 20,
                    "pattern_tolerance": 12,
                },
                "sam": {"segment_width": 1700, "K_height": 1150, "angle": 9.0},
            }
            rationale = "Seed 3 + R1 detection/SAM recipe."
        else:
            observation = f"R3: tighter Hough + smaller SAM; F1={f1:.3f}."
            failure = "f_spurious_lines"
            overlay = {
                "denoising": {"mask_r_low": 3.65, "mask_r_high": 3.90},
                "enhancing": {"curvature_threshold": 0.0015},
                "detecting": {
                    "binary_threshold": 135,
                    "hough_threshold_oblique": 55,
                    "hough_threshold_horizontal": 45,
                    "hough_threshold_vertical": 4000,
                    "maxLineGap_oblique": 50,
                    "maxLineGap_horizontal": 10,
                    "pattern_tolerance": 8,
                },
                "sam": {"segment_width": 1600, "K_height": 1100, "angle": 8.0},
            }
            rationale = "Suppress spurious joints; keep SAM near family centre."
    return {
        "observation": observation,
        "failure_mode": failure,
        "rationale": rationale,
        "overlay": overlay,
    }


def run_case(subset: str, from_round: int = 1) -> dict[str, Any]:
    mode = FAMILY_MODE[family_of_subset(subset)]
    _append_campaign(f"\n---\n\n## {subset} ({mode})\n\n")
    for r in range(from_round, 4):
        # Skip if round already succeeded; wipe failed rounds so they can retry.
        rec_path = out_root_for(subset) / f"round{r}" / "reflection_record.json"
        if rec_path.exists():
            rec = json.loads(rec_path.read_text(encoding="utf-8"))
            if rec.get("status") == "ok" and rec.get("proxy_scaled") is not None:
                _append_campaign(
                    f"### Round {r} — already present (proxy={rec.get('proxy_scaled'):.4f}, "
                    f"band={rec.get('band')}); skip.\n"
                )
                continue
            # Incomplete / failed prior attempt — remove and retry.
            import shutil

            shutil.rmtree(out_root_for(subset) / f"round{r}", ignore_errors=True)
            _append_campaign(f"### Round {r} — prior status={rec.get('status')}; retrying.\n")

        ctx = build_context(subset, write_overlay=(r == from_round))
        proposal = propose(subset, r, ctx)
        overlay = proposal["overlay"]
        full = bool(overlay.get("unfolding"))

        _append_campaign(
            f"### Round {r} CoT ({datetime.now().isoformat()})\n"
            f"- Observation: {proposal['observation']}\n"
            f"- Failure mode: `{proposal['failure_mode']}`\n"
            f"- Rationale: {proposal['rationale']}\n"
            f"- Overlay: `{json.dumps(overlay, separators=(',', ':'))}`\n"
            f"- full_pipeline: {full}\n"
        )
        print(f"=== {subset} round{r} ===", flush=True)
        t0 = time.time()
        rec = run_round(subset, r, overlay, full=full)
        dt = time.time() - t0
        _append_campaign(
            f"- Result: status={rec['status']} proxy_scaled={rec.get('proxy_scaled'):.4f} "
            f"band={rec.get('band')} F1={rec['features']['correspondence_f1@15']:.3f} "
            f"fill={rec['features']['sam_fill_rate']:.3f} elapsed={dt:.1f}s\n"
        )
        if rec["status"] != "ok":
            _append_campaign(f"- **FAILED** round{r}; continuing.\n")

    print(f"=== select {subset} ===", flush=True)
    result = select(subset)
    _append_campaign(
        f"\n**Selected:** `{result['selected']['round']}` "
        f"(Δproxy={result['delta_proxy_scaled']:+.4f}, "
        f"ΔmIoU_offline={result.get('delta_mIoU_offline')}). "
        f"Reason: {result['selection_reason']}\n"
    )
    return result


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--subset", default=None)
    p.add_argument("--from-round", type=int, default=1)
    p.add_argument(
        "--panel",
        default=",".join(PANEL),
        help="Comma-separated subsets (default: full 22-case panel)",
    )
    args = p.parse_args()

    subsets = [args.subset] if args.subset else [s.strip() for s in args.panel.split(",") if s.strip()]
    for s in subsets:
        if s not in PANEL:
            print(f"WARNING: {s} not in label-free panel", file=sys.stderr)
        run_case(s, from_round=args.from_round if args.subset else 1)


if __name__ == "__main__":
    main()
