#!/usr/bin/env python3
"""Phase B Fable-5 proposals + sequential execution for remaining in-band cases.

Proposals are authored from GT-blind context packets (features/intrinsics only).
Does not call run_campaign.propose (deterministic arm).
"""

from __future__ import annotations

import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from bo.sc_general.refine_pilot import build_context, out_root_for, run_round  # noqa: E402
from bo.sc_general.select_round import select  # noqa: E402

STAGE3 = _REPO / "data" / "sc-general" / "stage3"
CAMPAIGN = STAGE3 / "campaign_fable.md"
LOGS = STAGE3 / "logs"

PHASE_B = [
    "1-1", "1-2", "1-3", "2-4",
    "3-10", "3-3", "3-6", "3-7", "3-8", "3-9",
    "4-2", "4-5", "5-2", "5-3", "5-4", "5-5",
]


def _append(text: str) -> None:
    CAMPAIGN.parent.mkdir(parents=True, exist_ok=True)
    with CAMPAIGN.open("a", encoding="utf-8") as fh:
        fh.write(text if text.endswith("\n") else text + "\n")


def propose_t12(subset: str, round_id: int, ctx: dict[str, Any]) -> dict[str, Any]:
    a = ctx["anchor"]
    f1 = float(a["features"]["correspondence_f1@15"])
    fill = float(a["features"]["sam_fill_rate"])
    if round_id == 1:
        return {
            "observation": (
                f"F1={f1:.3f} fill={fill:.3f}; detection mostly real. "
                "Low/mid F1 with healthy fill → SAM crop / template irregularity."
            ),
            "failure_mode": "f_template_mismatch / K-row crop",
            "rationale": "1-5 R3-style: denser z_step + mid Hough + y_bounds 4100.",
            "overlay": {
                "denoising": {
                    "mask_r_low": 2.35,
                    "mask_r_high": 2.82,
                    "z_step": 0.002,
                    "grad_threshold": 0.20,
                },
                "enhancing": {"curvature_threshold": 0.004, "inter_radius": 0.05},
                "detecting": {
                    "binary_threshold": 125,
                    "hough_threshold_oblique": 70,
                    "hough_threshold_horizontal": 70,
                    "hough_threshold_vertical": 650,
                    "maxLineGap_oblique": 30,
                },
                "sam": {"processing.y_bounds": [4100, 13300]},
            },
            "full": False,
        }
    if round_id == 2:
        return {
            "observation": f"After R1 history; push stronger y_bounds/Hough. F1 was {f1:.3f}.",
            "failure_mode": "residual K-crop / size irregularity",
            "rationale": "1-5 R2-style: y_bounds 4300 + stronger Hough.",
            "overlay": {
                "denoising": {
                    "mask_r_low": 2.30,
                    "mask_r_high": 2.80,
                    "z_step": 0.004,
                    "grad_threshold": 0.16,
                },
                "enhancing": {"curvature_threshold": 0.005, "inter_radius": 0.06},
                "detecting": {
                    "binary_threshold": 115,
                    "hough_threshold_oblique": 80,
                    "hough_threshold_horizontal": 80,
                    "hough_threshold_vertical": 750,
                    "maxLineGap_oblique": 40,
                },
                "sam": {"processing.y_bounds": [4300, 13300]},
            },
            "full": False,
        }
    return {
        "observation": f"Alternate milder mid recipe; F1={f1:.3f}.",
        "failure_mode": "depth/lining density vs crop tradeoff",
        "rationale": "1-5 R1-style mid recipe for diversity.",
        "overlay": {
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
        },
        "full": False,
    }


def propose_t3(subset: str, round_id: int, ctx: dict[str, Any]) -> dict[str, Any]:
    a = ctx["anchor"]
    f1 = float(a["features"]["correspondence_f1@15"])
    fill = float(a["features"]["sam_fill_rate"])
    unlocked = bool(ctx["stage1_unlocked"])
    residual = a.get("recentre_residual_max_cm")
    fb = float((ctx.get("intrinsics_gt_blind") or {}).get("det_fallback_ratio") or 0.0)

    if unlocked and round_id == 1:
        seed = 1 if float(residual or 0) > 15 else 5
        return {
            "observation": (
                f"Residual {residual} cm unlocked; fallback={fb:.2f} F1={f1:.3f}. "
                "Centreline first."
            ),
            "failure_mode": "f_centreline_residual (+ detection fallback)",
            "rationale": f"Probe seed {seed} alone (full 1–6).",
            "overlay": {"unfolding": {"random_seed": seed}},
            "full": True,
        }
    if unlocked and round_id == 2:
        return {
            "observation": f"Combine seed 1 with detection recovery; F1={f1:.3f}.",
            "failure_mode": "f_centreline_residual + f_detection_fallback",
            "rationale": "Seed 1 + moderate Hough recovery + slight mask widen.",
            "overlay": {
                "unfolding": {"random_seed": 1},
                "denoising": {
                    "mask_r_low": 2.80,
                    "mask_r_high": 3.08,
                    "mask_theta_low": 1.3,
                    "mask_theta_high": 17.5,
                },
                "enhancing": {"curvature_threshold": 0.0008},
                "detecting": {
                    "binary_threshold": 115,
                    "hough_threshold_oblique": 25,
                    "hough_threshold_horizontal": 25,
                    "hough_threshold_vertical": 1800,
                    "maxLineGap_oblique": 45,
                    "pattern_tolerance": 14,
                    "uniform_k_snap": True,
                },
                "sam": {"segment_width": 1250, "K_height": 900, "angle": 6.5},
            },
            "full": True,
        }
    if unlocked and round_id == 3:
        return {
            "observation": f"Alternate seed 5; F1={f1:.3f}.",
            "failure_mode": "f_centreline_residual",
            "rationale": "Seed 5 alone for centreline diversity.",
            "overlay": {"unfolding": {"random_seed": 5}},
            "full": True,
        }

    # Locked t3: 100% fallback typical — recover Hough under frozen stage-1.
    if round_id == 1:
        return {
            "observation": (
                f"F1={f1:.3f} fill={fill:.3f} fallback={fb:.2f}. "
                "Uniform-K continuous; correspondence weak when Hough falls back."
            ),
            "failure_mode": "f_detection_fallback / low line↔boundary F1",
            "rationale": "Moderate Hough recovery + slight mask widen; keep uniform_k_snap.",
            "overlay": {
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
            },
            "full": False,
        }
    if round_id == 2:
        return {
            "observation": f"Widen retention + lower binary; F1={f1:.3f}.",
            "failure_mode": "f_depth_incomplete or weak edges",
            "rationale": "Wider mask + lower binary + looser Hough to catch more joints.",
            "overlay": {
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
            },
            "full": False,
        }
    return {
        "observation": f"Alternate cleaner edges / larger SAM; F1={f1:.3f}.",
        "failure_mode": "f_sam_crop_mismatch",
        "rationale": "Higher binary + larger SAM window.",
        "overlay": {
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
        },
        "full": False,
    }


def propose_t45(subset: str, round_id: int, ctx: dict[str, Any]) -> dict[str, Any]:
    a = ctx["anchor"]
    f1 = float(a["features"]["correspondence_f1@15"])
    fb = float((ctx.get("intrinsics_gt_blind") or {}).get("det_fallback_ratio") or 0.0)
    unlocked = bool(ctx["stage1_unlocked"])
    residual = a.get("recentre_residual_max_cm")

    if unlocked and round_id == 1:
        return {
            "observation": f"Residual {residual} cm unlocked; F1={f1:.3f}.",
            "failure_mode": "f_centreline_residual",
            "rationale": "Probe seed 1 alone.",
            "overlay": {"unfolding": {"random_seed": 1}},
            "full": True,
        }

    if round_id == 1:
        return {
            "observation": (
                f"F1={f1:.3f} fallback={fb:.2f}. Complex irregular K; "
                "widen mask and raise vertical Hough hard."
            ),
            "failure_mode": "f_detection_sparse / complex layout mismatch",
            "rationale": "4-4 cursor2 coordinated: widen mask, hard vertical, live SAM sizes.",
            "overlay": {
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
                "sam": {"K_height": 1150, "segment_width": 1700, "angle": 9.5},
            },
            "full": False,
        }
    if round_id == 2:
        return {
            "observation": f"Milder vertical + wider SAM; F1={f1:.3f}.",
            "failure_mode": "over-aggressive vertical or SAM crop",
            "rationale": "Milder vertical 2500 + larger SAM window.",
            "overlay": {
                "denoising": {"mask_r_low": 3.60, "mask_r_high": 4.00},
                "enhancing": {"curvature_threshold": 0.0008},
                "detecting": {
                    "binary_threshold": 110,
                    "hough_threshold_oblique": 35,
                    "hough_threshold_horizontal": 35,
                    "hough_threshold_vertical": 2500,
                    "maxLineGap_oblique": 60,
                    "maxLineGap_horizontal": 15,
                    "pattern_tolerance": 14,
                },
                "sam": {"K_height": 1300, "segment_width": 1900, "angle": 10.0},
            },
            "full": False,
        }
    return {
        "observation": f"Aggressive vertical + max widen; F1={f1:.3f}.",
        "failure_mode": "sparse detection ceiling",
        "rationale": "Aggressive vertical 4000 + edge-widen mask + larger K_height.",
        "overlay": {
            "denoising": {"mask_r_low": 3.50, "mask_r_high": 4.05},
            "enhancing": {"curvature_threshold": 0.0015},
            "detecting": {
                "binary_threshold": 130,
                "hough_threshold_oblique": 45,
                "hough_threshold_horizontal": 40,
                "hough_threshold_vertical": 4000,
                "maxLineGap_oblique": 75,
                "maxLineGap_horizontal": 25,
                "pattern_tolerance": 10,
            },
            "sam": {"K_height": 1400, "segment_width": 2000, "angle": 8.5},
        },
        "full": False,
    }


def propose(subset: str, round_id: int, ctx: dict[str, Any]) -> dict[str, Any]:
    fam = ctx["family"]
    if fam == "t1&2":
        return propose_t12(subset, round_id, ctx)
    if fam == "t3":
        return propose_t3(subset, round_id, ctx)
    return propose_t45(subset, round_id, ctx)


def case_done(subset: str) -> bool:
    root = out_root_for(subset, arm="fable")
    sel = STAGE3 / "selections-fable" / f"{subset}.json"
    if not sel.exists():
        return False
    for r in (1, 2, 3):
        rec = root / f"round{r}" / "reflection_record.json"
        if not rec.exists():
            return False
        data = json.loads(rec.read_text(encoding="utf-8"))
        if data.get("status") != "ok":
            return False
    return True


def run_case(subset: str) -> None:
    if case_done(subset):
        print(f"SKIP {subset} (already complete)")
        return

    ctx = build_context(subset, arm="fable", write_overlay=True)
    a = ctx["anchor"]
    _append(
        f"\n## {subset} ({ctx['family']}) — Phase B\n\n"
        f"### Anchor (GT-blind)\n"
        f"- proxy {a['proxy_scaled']:.3f} / {a['band']}; "
        f"F1={a['features']['correspondence_f1@15']:.3f} "
        f"fill={a['features']['sam_fill_rate']:.3f} "
        f"nan={a['features']['depth_nan_ratio']:.3f} "
        f"residual={a.get('recentre_residual_max_cm')} "
        f"unlocked={ctx['stage1_unlocked']}\n"
    )

    root = out_root_for(subset, arm="fable")
    for round_id in (1, 2, 3):
        rec_path = root / f"round{round_id}" / "reflection_record.json"
        if rec_path.exists():
            data = json.loads(rec_path.read_text(encoding="utf-8"))
            if data.get("status") == "ok" and data.get("proxy_scaled") is not None:
                print(f"SKIP {subset} R{round_id} (exists)")
                # refresh context history for next propose
                ctx = build_context(subset, arm="fable", write_overlay=False)
                continue

        prop = propose(subset, round_id, ctx)
        _append(
            f"\n### Round {round_id} CoT\n"
            f"- Observation: {prop['observation']}\n"
            f"- Failure mode: {prop['failure_mode']}\n"
            f"- Rationale: {prop['rationale']}\n"
            f"- Overlay: `{json.dumps(prop['overlay'], separators=(',', ':'))}`\n"
            f"- full={prop['full']}\n"
        )
        t0 = time.time()
        rec = run_round(
            subset,
            round_id,
            prop["overlay"],
            arm="fable",
            full=bool(prop["full"]),
            rationale=prop["rationale"],
        )
        elapsed = time.time() - t0
        _append(
            f"### Round {round_id} result\n"
            f"- status={rec['status']} proxy={rec.get('proxy_scaled')} "
            f"band={rec.get('band')} residual={rec.get('recentre_residual_max_cm')} "
            f"elapsed={elapsed:.1f}s\n"
        )
        ctx = build_context(subset, arm="fable", write_overlay=False)

    sel = select(subset, arm="fable")
    _append(
        f"\n### Selection\n"
        f"- selected **{sel['selected']['round']}** "
        f"Δproxy={sel['delta_proxy_scaled']:+.3f} "
        f"ΔmIoU={sel.get('delta_mIoU_offline')}\n"
        f"- reason: {sel['selection_reason']}\n"
    )
    print(
        f"DONE {subset}: {sel['selected']['round']} "
        f"dproxy={sel['delta_proxy_scaled']:+.3f} "
        f"dmiou={sel.get('delta_mIoU_offline')}"
    )


def main() -> None:
    LOGS.mkdir(parents=True, exist_ok=True)
    subsets = sys.argv[1:] or PHASE_B
    _append(
        f"\n---\n\n# Phase B start {datetime.now().isoformat()}\n"
        f"Cases: {', '.join(subsets)}\n"
    )
    for subset in subsets:
        print(f"\n======== {subset} ========")
        run_case(subset)


if __name__ == "__main__":
    main()
