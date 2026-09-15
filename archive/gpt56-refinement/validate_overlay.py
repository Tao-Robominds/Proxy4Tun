#!/usr/bin/env python3
"""Validate a GPT-proposed overlay against family BO spaces."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from bo.unified.spaces import Dim, family_of_subset, sibling_anchor_case, space_for_case  # noqa: E402


from constants import STAGE1_UNLOCK  # noqa: E402


def _dims_by_key(dims: list[Dim]) -> dict[tuple[str, str], Dim]:
    return {(d.stage, d.key): d for d in dims}


def validate_overlay(subset: str, overlay: dict[str, Any]) -> tuple[bool, list[str], dict[str, Any]]:
    """Return (ok, errors, normalized_overlay).

    Normalization: cast ints/floats/bools; map nested processing.y_bounds when
    only y_bounds_lower is provided via the special dim.
    """
    errors: list[str] = []
    if not isinstance(overlay, dict):
        return False, ["overlay must be a JSON object"], {}

    sibling = sibling_anchor_case(subset)
    dims = space_for_case(sibling)
    by_key = _dims_by_key(dims)
    allowed_stages = {d.stage for d in dims}
    normalized: dict[str, dict[str, Any]] = {}

    for stage, params in overlay.items():
        if stage not in allowed_stages:
            errors.append(f"unknown stage {stage!r}")
            continue
        if not isinstance(params, dict):
            errors.append(f"stage {stage} must be an object")
            continue
        for key, val in params.items():
            dim = by_key.get((stage, key))
            # Allow processing.y_bounds as a 2-list when y_bounds_lower dim exists.
            if dim is None and key == "processing.y_bounds":
                dim = by_key.get((stage, "processing.y_bounds"))
            if dim is None:
                errors.append(f"param {stage}.{key} not in family space")
                continue
            if stage == "unfolding" and subset not in STAGE1_UNLOCK:
                errors.append(
                    f"unfolding overlays forbidden for {subset} "
                    f"(residual unlock only)"
                )
                continue
            try:
                # y_bounds must expand to [low, high] before the generic int path.
                if dim.special == "y_bounds_lower" or key == "processing.y_bounds":
                    # Accept either lower int or [low, high] list.
                    if isinstance(val, (list, tuple)) and len(val) == 2:
                        lo, hi = int(val[0]), int(val[1])
                        if not (dim.low <= lo <= dim.high):
                            errors.append(
                                f"y_bounds lower {lo} outside [{dim.low}, {dim.high}]"
                            )
                        cast = [lo, hi]
                        key = "processing.y_bounds"
                    else:
                        cast = int(val)
                        if not (dim.low <= cast <= dim.high):
                            errors.append(
                                f"{stage}.{key}={cast} outside [{dim.low}, {dim.high}]"
                            )
                        # Expand to full bounds using a default upper near anchor.
                        key = "processing.y_bounds"
                        cast = [cast, 13300]
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

    if not normalized and not errors:
        errors.append("empty overlay")
    return (len(errors) == 0), errors, normalized


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--subset", required=True)
    p.add_argument("--overlay-json", required=True)
    args = p.parse_args()
    overlay = json.loads(args.overlay_json)
    ok, errors, norm = validate_overlay(args.subset, overlay)
    print(json.dumps({"ok": ok, "errors": errors, "normalized": norm}, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
