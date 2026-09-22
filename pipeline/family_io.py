"""Shared parameter I/O and family-mode dispatch for the unified pipeline.

The unified pipeline runs one set of stage scripts for all three anchor
families. The active behaviour is selected by ``family_mode`` read from
``parameters_family.json`` in the resolved params dir:

    family_mode == "staggered"  -> t1&2 behaviour
    family_mode == "continuous" -> t3 behaviour
    family_mode == "complex"    -> t4&5 behaviour

The mode only sets *defaults* for keys that are missing from a stage's
``parameters_<stage>.json``. Any key that is explicitly present in the JSON
always wins, so the frozen anchor parameter snapshots reproduce their anchor
mIoU unchanged.
"""

from __future__ import annotations

import json
import os

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(_THIS_DIR)

VALID_MODES = ("staggered", "continuous", "complex")

# Per-stage, per-mode defaults. Only applied when the key is absent from the
# stage JSON (explicit keys always override). Keep these aligned with the
# behaviour of the corresponding source family so anchor params are unchanged.
MODE_DEFAULTS: dict[str, dict[str, dict[str, object]]] = {
    "unfolding": {
        "staggered": {},
        "continuous": {},
        "complex": {
            "top_tube_radius": 3.5,
            "top_tube_top_n": 10,
        },
    },
    "denoising": {
        "staggered": {},
        "continuous": {},
        "complex": {},
    },
    "enhancing": {
        "staggered": {},
        "continuous": {},
        "complex": {},
    },
    "detecting": {
        "staggered": {
            "prompt_logic": "t12_pattern",
            "uniform_k_snap": False,
        },
        "continuous": {
            "prompt_logic": "t3_inherit",
            "uniform_k_snap": True,
        },
        "complex": {
            "prompt_logic": "t12_pattern",
            "uniform_k_snap": False,
        },
    },
    "sam": {
        # segment_loop_extra matters for staggered: the t1&2 source loops over
        # exactly segment_per_ring blocks (no extra), whereas t3/t4&5 add one.
        "staggered": {
            "geometry_profile": "t12",
            "mirror_k_geometry": False,
            "segment_per_ring": 6,
            "segment_loop_extra": 0,
        },
        "continuous": {
            "geometry_profile": "t3",
            "mirror_k_geometry": True,
            "segment_per_ring": 6,
            "segment_loop_extra": 1,
        },
        "complex": {
            "geometry_profile": "t45",
            "segment_per_ring": 7,
            "segment_loop_extra": 1,
        },
    },
}


def _resolve_params_root(params_dir: str | None = None) -> str:
    """Resolve the directory that holds the ``parameters_*.json`` files."""
    if params_dir:
        return os.path.abspath(params_dir)
    env = (os.environ.get("PROXY4TUN_PARAMS_DIR") or "").strip()
    if env:
        return os.path.abspath(env)
    return os.path.join(_THIS_DIR, "params")


def load_family_mode(params_dir: str | None = None) -> str:
    """Read and validate ``family_mode`` from ``parameters_family.json``.

    Returns one of ``VALID_MODES``. Exits with a clear message when the file
    is missing or the mode is invalid.
    """
    root = _resolve_params_root(params_dir)
    path = os.path.join(root, "parameters_family.json")
    if not os.path.isfile(path):
        raise SystemExit(
            f"Missing parameters_family.json under resolved params dir: {root}. "
            "Provide it with a 'family_mode' of "
            f"{', '.join(VALID_MODES)}."
        )
    with open(path, "r") as f:
        data = json.load(f)
    mode = data.get("family_mode")
    if mode not in VALID_MODES:
        raise SystemExit(
            f"Invalid family_mode={mode!r} in {path}; "
            f"expected one of {', '.join(VALID_MODES)}"
        )
    return mode


def apply_mode_defaults(stage: str, params: dict, mode: str) -> dict:
    """Return a copy of ``params`` with mode-appropriate defaults filled in.

    Never overwrites keys already present in ``params``.
    """
    if mode not in VALID_MODES:
        raise SystemExit(
            f"Invalid family_mode={mode!r}; expected one of {', '.join(VALID_MODES)}"
        )
    merged = dict(params)
    defaults = MODE_DEFAULTS.get(stage, {}).get(mode, {})
    for key, value in defaults.items():
        if key not in merged:
            merged[key] = value
    return merged


def load_raw_params(stage: str, params_dir: str | None = None) -> tuple[dict, str]:
    """Load ``parameters_<stage>.json`` without applying mode defaults."""
    root = _resolve_params_root(params_dir)
    path = os.path.join(root, f"parameters_{stage}.json")
    if not os.path.isfile(path):
        raise SystemExit(
            f"Missing parameters_{stage}.json under resolved params dir: {root}"
        )
    with open(path, "r") as f:
        data = json.load(f)
    return data, path


def load_stage_params(stage: str, params_dir: str | None = None) -> tuple[dict, str, str]:
    """Load a stage's params merged with mode defaults.

    Returns ``(params_with_defaults, param_file_path, family_mode)``.
    """
    mode = load_family_mode(params_dir)
    data, path = load_raw_params(stage, params_dir)
    merged = apply_mode_defaults(stage, data, mode)
    try:
        rel = os.path.relpath(path, _REPO_ROOT)
    except ValueError:
        rel = path
    print(f"Loaded {stage} parameters from {rel} (family_mode={mode})")
    return merged, path, mode
