"""Shared overlay validation against family BO search spaces.

Used by GPT-5.6, Gemini-3.8, and the random-overlay control arm.
Rejects unknown/dead knobs; clamps types; expands y_bounds_lower.
"""

from __future__ import annotations

from typing import Any

from bo.unified.spaces import FAMILY_SPACES, Dim, family_of_subset


def dims_by_key(dims: list[Dim]) -> dict[tuple[str, str], Dim]:
    return {(d.stage, d.key): d for d in dims}


def validate_overlay(
    subset: str, overlay: dict[str, Any], *, stage1_unlocked: bool
) -> tuple[bool, list[str], dict[str, Any]]:
    """Reject unknown/dead knobs; clamp types; expand y_bounds."""
    errors: list[str] = []
    if not isinstance(overlay, dict):
        return False, ["overlay must be a JSON object"], {}

    dims = FAMILY_SPACES[family_of_subset(subset)]()
    by_key = dims_by_key(dims)
    allowed_stages = {d.stage for d in dims}
    normalized: dict[str, dict[str, Any]] = {}

    for stage, params in overlay.items():
        if stage not in allowed_stages:
            errors.append(f"unknown stage {stage!r}")
            continue
        if not isinstance(params, dict):
            errors.append(f"stage {stage} must be an object")
            continue
        # Flatten nested {"processing": {"y_bounds": [...]}} -> "processing.y_bounds"
        flat_params: dict[str, Any] = {}
        for key, val in params.items():
            if key == "processing" and isinstance(val, dict) and "y_bounds" in val:
                flat_params["processing.y_bounds"] = val["y_bounds"]
                for k2, v2 in val.items():
                    if k2 != "y_bounds":
                        flat_params[f"processing.{k2}"] = v2
            else:
                flat_params[key] = val
        for key, val in flat_params.items():
            dim = by_key.get((stage, key))
            if dim is None and key == "processing.y_bounds":
                dim = by_key.get((stage, "processing.y_bounds"))
            if dim is None:
                errors.append(f"param {stage}.{key} not in family space (dead/unknown knob)")
                continue
            if stage == "unfolding" and not stage1_unlocked:
                errors.append(
                    f"unfolding overlays forbidden for {subset} (stage1 not unlocked)"
                )
                continue
            try:
                if dim.special == "y_bounds_lower" or key == "processing.y_bounds":
                    if isinstance(val, (list, tuple)) and len(val) == 2:
                        lo, hi = int(val[0]), int(val[1])
                        if not (dim.low <= lo <= dim.high):
                            errors.append(
                                f"y_bounds lower {lo} outside [{dim.low}, {dim.high}]"
                            )
                        cast: Any = [lo, hi]
                        key = "processing.y_bounds"
                    else:
                        lo = int(val)
                        if not (dim.low <= lo <= dim.high):
                            errors.append(
                                f"{stage}.{key}={lo} outside [{dim.low}, {dim.high}]"
                            )
                        key = "processing.y_bounds"
                        cast = [lo, 13300]
                elif dim.kind == "bool":
                    cast = bool(val)
                elif dim.kind == "int":
                    cast = int(val)
                    if not (dim.low <= cast <= dim.high):
                        errors.append(
                            f"{stage}.{key}={cast} outside [{dim.low}, {dim.high}]"
                        )
                else:
                    cast = float(val)
                    if not (dim.low <= cast <= dim.high):
                        errors.append(
                            f"{stage}.{key}={cast} outside [{dim.low}, {dim.high}]"
                        )
            except (TypeError, ValueError) as exc:
                errors.append(f"{stage}.{key} cast failed: {exc}")
                continue
            normalized.setdefault(stage, {})[key] = cast

    # Drop empty stage dicts from the raw overlay before validation result.
    normalized = {s: p for s, p in normalized.items() if p}

    if not normalized and not errors:
        errors.append("empty overlay")
    return (len(errors) == 0), errors, normalized
