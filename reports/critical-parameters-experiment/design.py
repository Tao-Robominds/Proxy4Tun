"""Fractional factorial designs for interaction screening."""

from __future__ import annotations

# 7-factor Resolution IV design (2^(7-3)), standard generator set.
# Factors: A mask_r_low, B mask_r_high, C z_step, D upsample1, E inter_radius,
#          F curvature, G sam_y_lower (3800 vs 4200)
# Encoded as -1 (LOW) / +1 (HIGH)

FRACTIONAL_7F_RES4: list[dict[str, int]] = [
    {"A": -1, "B": -1, "C": -1, "D": -1, "E": -1, "F": -1, "G": -1},
    {"A": +1, "B": -1, "C": -1, "D": -1, "E": +1, "F": +1, "G": +1},
    {"A": -1, "B": +1, "C": -1, "D": -1, "E": +1, "F": +1, "G": -1},
    {"A": +1, "B": +1, "C": -1, "D": -1, "E": -1, "F": -1, "G": +1},
    {"A": -1, "B": -1, "C": +1, "D": -1, "E": +1, "F": -1, "G": +1},
    {"A": +1, "B": -1, "C": +1, "D": -1, "E": -1, "F": -1, "G": -1},
    {"A": -1, "B": +1, "C": +1, "D": -1, "E": -1, "F": -1, "G": +1},
    {"A": +1, "B": +1, "C": +1, "D": -1, "E": +1, "F": +1, "G": -1},
    {"A": -1, "B": -1, "C": -1, "D": +1, "E": -1, "F": +1, "G": +1},
    {"A": +1, "B": -1, "C": -1, "D": +1, "E": +1, "F": -1, "G": -1},
    {"A": -1, "B": +1, "C": -1, "D": +1, "E": +1, "F": -1, "G": +1},
    {"A": +1, "B": +1, "C": -1, "D": +1, "E": -1, "F": +1, "G": -1},
    {"A": -1, "B": -1, "C": +1, "D": +1, "E": +1, "F": +1, "G": -1},
    {"A": +1, "B": -1, "C": +1, "D": +1, "E": -1, "F": +1, "G": +1},
    {"A": -1, "B": +1, "C": +1, "D": +1, "E": -1, "F": +1, "G": -1},
    {"A": +1, "B": +1, "C": +1, "D": +1, "E": +1, "F": -1, "G": +1},
]

FACTOR_MAP = {
    "A": ("denoising", "mask_r_low"),
    "B": ("denoising", "mask_r_high"),
    "C": ("denoising", "z_step"),
    "D": ("enhancing", "upsampling_stage1_target_distance"),
    "E": ("enhancing", "inter_radius"),
    "F": ("enhancing", "curvature_threshold"),
    "G": ("sam", "processing.y_bounds"),
}

FACTOR_HIGH = {
    "A": 2.33,
    "B": 2.78,
    "C": 0.005,
    "D": 0.06,
    "E": 0.03,
    "F": 0.005,
    "G": [3800, 13300],
}

FACTOR_LOW = {
    "A": 2.7,
    "B": 2.8,
    "C": 0.001,
    "D": 0.08,
    "E": 0.06,
    "F": 0.0005,
    "G": [4200, 13100],
}


def design_row_to_overlay(row: dict[str, int]) -> dict[str, dict[str, object]]:
    overlay: dict[str, dict[str, object]] = {}
    for factor, level in row.items():
        stage, key = FACTOR_MAP[factor]
        value = FACTOR_HIGH[factor] if level == +1 else FACTOR_LOW[factor]
        overlay.setdefault(stage, {})[key] = value
    return overlay
