"""Per-family BO search spaces (mechanism coverage, stages 2–6 only)."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

sys.path.insert(0, str(Path(__file__).resolve().parent))
from param_io import get_nested, load_anchor_params  # noqa: E402

ParamType = Literal["float", "int", "bool"]


@dataclass(frozen=True)
class Dim:
    name: str  # unique id, e.g. "mask_r_low"
    stage: str  # denoising | enhancing | detecting | sam
    key: str  # possibly nested, e.g. "processing.y_bounds_lower"
    kind: ParamType
    low: float
    high: float
    # For y_bounds_lower: we write [value, upper_fixed]
    special: str | None = None


CASE_CONFIG: dict[str, dict[str, Any]] = {
    "1-1": {
        "family": "t1&2",
        "profile": "t1&2",
        "params_dir": "anchors/t1&2/1-1",
        "input_txt": "data/subsets/1-1.txt",
        "anchor_miou": 0.787,
        "expected_rings": 10,
    },
    "2-1": {
        "family": "t1&2",
        "profile": "t1&2",
        "params_dir": "anchors/t1&2/2-1",
        "input_txt": "data/subsets/2-1.txt",
        "anchor_miou": 0.874,
        "expected_rings": 10,
    },
    "3-1": {
        "family": "t3",
        "profile": "t3",
        "params_dir": "anchors/t3/3-1-1",  # protected anchor params (unchanged)
        "frozen_anchor": "3-1-1",  # protected data/anchors/3-1-1 stage-1
        "input_txt": "data/subsets/3-1.txt",
        "anchor_miou": 0.850,
        "expected_rings": 10,
    },
    "3-2": {
        "family": "t3",
        "profile": "t3",
        "params_dir": "anchors/t3/3-1-1",  # sibling params; no dedicated 3-2 anchor
        "input_txt": "data/subsets/3-2.txt",
        "anchor_miou": 0.631,  # from seeded stage-1 gate run (data/bo/3-2-bo-proxy)
        "expected_rings": 10,
    },
    "4-1": {
        "family": "t4&5",
        "profile": "t4&5",
        "params_dir": "anchors/t4&5/4-1",
        "input_txt": "data/subsets/4-1.txt",
        "anchor_miou": 0.635,
        "expected_rings": 10,
    },
    "5-1": {
        "family": "t4&5",
        "profile": "t4&5",
        "params_dir": "anchors/t4&5/5-1",
        "input_txt": "data/subsets/5-1.txt",
        "anchor_miou": 0.808,
        "expected_rings": 10,
    },
}

# Per-family training cases (BO campaigns) and held-out evaluation subsets.
FAMILY_TRAIN_CASES: dict[str, tuple[str, ...]] = {
    "t1&2": ("1-1", "2-1"),
    "t3": ("3-1", "3-2"),
    "t4&5": ("4-1", "5-1"),
}

FAMILY_HOLDOUT_SUBSETS: dict[str, tuple[str, ...]] = {
    "t1&2": ("1-2", "1-3", "1-4", "1-5", "2-2", "2-3", "2-4", "2-5"),
    "t3": ("3-3", "3-4", "3-5"),
    "t4&5": (
        "4-2",
        "4-3",
        "4-4",
        "4-5",
        "4-6",
        "4-7",
        "4-8",
        "4-9",
        "4-10",
        "5-2",
        "5-3",
        "5-4",
        "5-5",
        "5-6",
        "5-7",
    ),
}


def family_of_subset(subset: str) -> str:
    if subset.startswith("1-") or subset.startswith("2-"):
        return "t1&2"
    if subset.startswith("3-"):
        return "t3"
    if subset.startswith("4-") or subset.startswith("5-"):
        return "t4&5"
    raise ValueError(f"Cannot map subset {subset!r} to a family")


def sibling_anchor_case(subset: str) -> str:
    """Nearest promoted sibling used as param source for held-out runs."""
    if subset.startswith("1-"):
        return "1-1"
    if subset.startswith("2-"):
        return "2-1"
    if subset.startswith("3-"):
        return "3-1"
    if subset.startswith("4-"):
        return "4-1"
    if subset.startswith("5-"):
        return "5-1"
    raise ValueError(f"No sibling anchor for subset {subset!r}")


def holdout_case_config(subset: str) -> dict[str, Any]:
    """Runtime config for a held-out subset (params from sibling anchor)."""
    sibling = sibling_anchor_case(subset)
    base = CASE_CONFIG[sibling]
    return {
        "subset": subset,
        "family": family_of_subset(subset),
        "profile": base["profile"],
        "params_dir": base["params_dir"],
        "sibling": sibling,
        "input_txt": f"data/subsets/{subset}.txt",
        "expected_rings": int(base["expected_rings"]),
        "anchor_miou": None,  # unknown a priori for held-out tunnels
    }


def _t12_space() -> list[Dim]:
    # Ranges span 1-1 and 2-1 anchors with modest padding (R4 ranges where useful)
    return [
        Dim("mask_r_low", "denoising", "mask_r_low", "float", 2.20, 2.50),
        Dim("mask_r_high", "denoising", "mask_r_high", "float", 2.70, 2.90),
        Dim("z_step", "denoising", "z_step", "float", 0.001, 0.008),
        Dim("grad_threshold", "denoising", "grad_threshold", "float", 0.10, 0.25),
        Dim("curvature_threshold", "enhancing", "curvature_threshold", "float", 0.0003, 0.008),
        Dim("inter_radius", "enhancing", "inter_radius", "float", 0.02, 0.08),
        Dim("binary_threshold", "detecting", "binary_threshold", "int", 100, 160),
        Dim("hough_threshold_oblique", "detecting", "hough_threshold_oblique", "int", 40, 90),
        Dim("hough_threshold_horizontal", "detecting", "hough_threshold_horizontal", "int", 40, 90),
        Dim("hough_threshold_vertical", "detecting", "hough_threshold_vertical", "int", 400, 800),
        Dim("maxLineGap_oblique", "detecting", "maxLineGap_oblique", "int", 20, 80),
        Dim(
            "y_bounds_lower",
            "sam",
            "processing.y_bounds",
            "int",
            3600,
            4400,
            special="y_bounds_lower",
        ),
    ]


def _t3_space() -> list[Dim]:
    return [
        Dim("mask_r_low", "denoising", "mask_r_low", "float", 2.70, 3.00),
        Dim("mask_r_high", "denoising", "mask_r_high", "float", 2.90, 3.15),
        Dim("mask_theta_low", "denoising", "mask_theta_low", "float", 1.0, 2.5),
        Dim("mask_theta_high", "denoising", "mask_theta_high", "float", 15.0, 19.0),
        Dim("curvature_threshold", "enhancing", "curvature_threshold", "float", 0.0002, 0.002),
        Dim("binary_threshold", "detecting", "binary_threshold", "int", 100, 160),
        Dim("hough_threshold_oblique", "detecting", "hough_threshold_oblique", "int", 20, 60),
        Dim("hough_threshold_horizontal", "detecting", "hough_threshold_horizontal", "int", 20, 60),
        Dim("hough_threshold_vertical", "detecting", "hough_threshold_vertical", "int", 800, 2500),
        Dim("maxLineGap_oblique", "detecting", "maxLineGap_oblique", "int", 10, 60),
        Dim("pattern_tolerance", "detecting", "pattern_tolerance", "int", 5, 20),
        Dim("uniform_k_snap", "detecting", "uniform_k_snap", "bool", 0.0, 1.0),
        Dim("segment_width", "sam", "segment_width", "int", 1000, 1400),
        Dim("K_height", "sam", "K_height", "float", 700.0, 1000.0),
        Dim("angle", "sam", "angle", "float", 4.0, 9.0),
    ]


def _t45_space() -> list[Dim]:
    # Ranges span 4-1 and 5-1 (vertical Hough 800–5000)
    return [
        Dim("mask_r_low", "denoising", "mask_r_low", "float", 3.50, 3.80),
        Dim("mask_r_high", "denoising", "mask_r_high", "float", 3.75, 4.05),
        Dim("curvature_threshold", "enhancing", "curvature_threshold", "float", 0.0002, 0.002),
        Dim("binary_threshold", "detecting", "binary_threshold", "int", 100, 160),
        Dim("hough_threshold_oblique", "detecting", "hough_threshold_oblique", "int", 25, 70),
        Dim("hough_threshold_horizontal", "detecting", "hough_threshold_horizontal", "int", 25, 70),
        Dim("hough_threshold_vertical", "detecting", "hough_threshold_vertical", "int", 800, 5000),
        Dim("maxLineGap_oblique", "detecting", "maxLineGap_oblique", "int", 30, 80),
        Dim("maxLineGap_horizontal", "detecting", "maxLineGap_horizontal", "int", 5, 30),
        Dim("pattern_tolerance", "detecting", "pattern_tolerance", "int", 5, 20),
        Dim("segment_width", "sam", "segment_width", "int", 1500, 2100),
        Dim("K_height", "sam", "K_height", "float", 1000.0, 1500.0),
        Dim("angle", "sam", "angle", "float", 7.0, 12.0),
    ]


FAMILY_SPACES = {
    "t1&2": _t12_space,
    "t3": _t3_space,
    "t4&5": _t45_space,
}


def space_for_case(case: str) -> list[Dim]:
    cfg = CASE_CONFIG[case]
    return FAMILY_SPACES[cfg["family"]]()


def encode_params(
    dims: list[Dim], overlay_by_stage: dict[str, dict[str, Any]], base_by_stage: dict[str, dict[str, Any]]
) -> list[float]:
    """Map a concrete param overlay (+ base for missing) to a unit-cube vector? No — raw values in dim units."""
    x: list[float] = []
    for d in dims:
        stage_params = overlay_by_stage.get(d.stage) or {}
        if d.special == "y_bounds_lower":
            if d.key in stage_params:
                val = stage_params[d.key]
                if isinstance(val, list):
                    x.append(float(val[0]))
                else:
                    x.append(float(val))
            else:
                yb = get_nested(base_by_stage[d.stage], "processing.y_bounds")
                x.append(float(yb[0]))
            continue
        if d.key in stage_params:
            val = stage_params[d.key]
        else:
            val = get_nested(base_by_stage[d.stage], d.key)
        if d.kind == "bool":
            x.append(1.0 if bool(val) else 0.0)
        else:
            x.append(float(val))
    return x


def decode_vector(dims: list[Dim], x: list[float] | Any, base_by_stage: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Map a numeric vector to overlay_by_stage."""
    overlay: dict[str, dict[str, Any]] = {}
    for d, raw in zip(dims, x):
        if d.kind == "bool":
            value: Any = bool(int(round(float(raw))))
        elif d.kind == "int":
            value = int(round(float(raw)))
            value = int(max(d.low, min(d.high, value)))
        else:
            value = float(raw)
            value = float(max(d.low, min(d.high, value)))

        if d.special == "y_bounds_lower":
            yb = list(get_nested(base_by_stage["sam"], "processing.y_bounds"))
            yb[0] = int(round(float(value)))
            overlay.setdefault("sam", {})["processing.y_bounds"] = yb
            continue
        overlay.setdefault(d.stage, {})[d.key] = value

    # Enforce mask_r_low < mask_r_high (independent sampling can invert them).
    den = overlay.get("denoising", {})
    if "mask_r_low" in den and "mask_r_high" in den:
        lo, hi = float(den["mask_r_low"]), float(den["mask_r_high"])
        if lo >= hi:
            mid = 0.5 * (lo + hi)
            den["mask_r_low"] = mid - 0.02
            den["mask_r_high"] = mid + 0.02
    return overlay


def normalize(dims: list[Dim], x: list[float]) -> list[float]:
    out = []
    for d, v in zip(dims, x):
        span = d.high - d.low
        out.append(0.0 if span <= 0 else (float(v) - d.low) / span)
    return out


def denormalize(dims: list[Dim], z: list[float]) -> list[float]:
    out = []
    for d, u in zip(dims, z):
        u = min(1.0, max(0.0, float(u)))
        out.append(d.low + u * (d.high - d.low))
    return out


def anchor_vector(case: str, repo_root: Path) -> list[float]:
    cfg = CASE_CONFIG[case]
    dims = space_for_case(case)
    base = load_anchor_params(repo_root / cfg["params_dir"])
    return encode_params(dims, {}, base)


def space_summary(case: str) -> dict[str, Any]:
    dims = space_for_case(case)
    return {
        "case": case,
        "family": CASE_CONFIG[case]["family"],
        "n_dims": len(dims),
        "dims": [
            {
                "name": d.name,
                "stage": d.stage,
                "key": d.key,
                "kind": d.kind,
                "low": d.low,
                "high": d.high,
                "special": d.special,
            }
            for d in dims
        ],
    }


if __name__ == "__main__":
    import json

    for case in CASE_CONFIG:
        print(json.dumps(space_summary(case), indent=2))
