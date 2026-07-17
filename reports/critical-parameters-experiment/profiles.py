"""HIGH/LOW parameter profiles and ablation groups for tunnel 1-1."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from param_io import load_json

_REPO = Path(__file__).resolve().parents[3]
HIGH_DIR = _REPO / "agents" / "t1&2" / "parameters"
LOW_DIR = _REPO / "agents" / "sample" / "parameters"

STAGES = ("unfolding", "denoising", "enhancing", "detecting", "sam")


def load_profile(profile_dir: Path) -> dict[str, dict[str, Any]]:
    return {stage: load_json(profile_dir / f"parameters_{stage}.json") for stage in STAGES}


HIGH = load_profile(HIGH_DIR)
LOW = load_profile(LOW_DIR)

# Core 20 parameter deltas (denoising 8 + enhancing 7 + detecting 5)
DENOISING_KEYS = [
    "mask_r_low",
    "mask_r_high",
    "y_step",
    "z_step",
    "grad_threshold",
    "smoothing_window_size",
    "smoothing_offset",
    "default_cutoff_z",
]

ENHANCING_KEYS = [
    "upsampling_stage1_target_distance",
    "upsampling_stage2_target_distance",
    "upsampling_stage3_target_distance",
    "curvature_threshold",
    "depth_threshold_low",
    "depth_threshold_high",
    "inter_radius",
]

DETECTING_KEYS = [
    "binary_threshold",
    "hough_threshold_oblique",
    "hough_threshold_horizontal",
    "hough_threshold_vertical",
    "maxLineGap_oblique",
]

SAM_CONTROL_KEYS = ["processing.y_bounds"]

ALL_STUDY_KEYS = DENOISING_KEYS + ENHANCING_KEYS + DETECTING_KEYS + SAM_CONTROL_KEYS


def low_overlay_for_stage(stage: str) -> dict[str, Any]:
    """Return LOW values for keys that differ in this stage."""
    high = HIGH[stage]
    low = LOW[stage]
    overlay: dict[str, Any] = {}
    if stage == "sam":
        if high["processing"]["y_bounds"] != low["processing"]["y_bounds"]:
            overlay["processing.y_bounds"] = low["processing"]["y_bounds"]
        return overlay
    for key in high:
        if high[key] != low.get(key):
            overlay[key] = low[key]
    return overlay


def stage_revert_overlay(stage: str) -> dict[str, dict[str, Any]]:
    """Revert entire stage to LOW; others stay HIGH."""
    return {stage: low_overlay_for_stage(stage)}


# Mechanism groups (subset of keys reverted to LOW within a stage)
GROUPS: dict[str, dict[str, dict[str, Any]]] = {
    "denoise_radial_mask": {
        "denoising": {k: LOW["denoising"][k] for k in ("mask_r_low", "mask_r_high")},
    },
    "denoise_grid_cutoff": {
        "denoising": {
            k: LOW["denoising"][k]
            for k in ("y_step", "z_step", "grad_threshold", "default_cutoff_z")
        },
    },
    "denoise_smoothing": {
        "denoising": {
            k: LOW["denoising"][k]
            for k in ("smoothing_window_size", "smoothing_offset")
        },
    },
    "enhance_upsampling": {
        "enhancing": {
            k: LOW["enhancing"][k]
            for k in (
                "upsampling_stage1_target_distance",
                "upsampling_stage2_target_distance",
                "upsampling_stage3_target_distance",
            )
        },
    },
    "enhance_curvature": {
        "enhancing": {"curvature_threshold": LOW["enhancing"]["curvature_threshold"]},
    },
    "enhance_depth_thresholds": {
        "enhancing": {
            k: LOW["enhancing"][k]
            for k in ("depth_threshold_low", "depth_threshold_high")
        },
    },
    "enhance_inter_radius": {
        "enhancing": {"inter_radius": LOW["enhancing"]["inter_radius"]},
    },
    "detect_binary": {
        "detecting": {"binary_threshold": LOW["detecting"]["binary_threshold"]},
    },
    "detect_hough_oblique_horiz": {
        "detecting": {
            k: LOW["detecting"][k]
            for k in ("hough_threshold_oblique", "hough_threshold_horizontal")
        },
    },
    "detect_hough_vertical": {
        "detecting": {"hough_threshold_vertical": LOW["detecting"]["hough_threshold_vertical"]},
    },
    "detect_line_gap": {
        "detecting": {"maxLineGap_oblique": LOW["detecting"]["maxLineGap_oblique"]},
    },
    "sam_y_bounds": {
        "sam": {"processing.y_bounds": LOW["sam"]["processing"]["y_bounds"]},
    },
}

STAGE_TO_START = {
    "unfolding": 1,
    "denoising": 2,
    "enhancing": 3,
    "detecting": 4,
    "sam": 5,
}

CHECKPOINT_AFTER_STAGE = {
    1: "after_1.pkl",
    2: "after_2.pkl",
    3: "after_3.pkl",
    4: "after_4.pkl",
}


def individual_overlays() -> dict[str, dict[str, dict[str, Any]]]:
    """One-factor reversions keyed by factor id."""
    factors: dict[str, dict[str, dict[str, Any]]] = {}
    for key in DENOISING_KEYS:
        factors[f"denoise_{key}"] = {"denoising": {key: LOW["denoising"][key]}}
    for key in ENHANCING_KEYS:
        factors[f"enhance_{key}"] = {"enhancing": {key: LOW["enhancing"][key]}}
    for key in DETECTING_KEYS:
        factors[f"detect_{key}"] = {"detecting": {key: LOW["detecting"][key]}}
    factors["sam_y_bounds"] = {"sam": {"processing.y_bounds": LOW["sam"]["processing"]["y_bounds"]}}
    return factors


def start_stage_for_overlay(overlay_by_stage: dict[str, dict[str, Any]]) -> int:
    """Earliest pipeline stage affected by overlay."""
    if not overlay_by_stage:
        return 2
    starts = [STAGE_TO_START[s] for s in overlay_by_stage if s in STAGE_TO_START]
    return min(starts) if starts else 2
