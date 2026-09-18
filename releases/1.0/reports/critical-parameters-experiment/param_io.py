"""Parameter overlay I/O for ablation runs."""

from __future__ import annotations

import copy
import json
import os
from pathlib import Path
from typing import Any


def resolve_params_dir(pipeline_dir: str) -> str:
    override = (os.environ.get("PROXY4TUN_PARAMS_DIR") or "").strip()
    if override:
        return override
    return os.path.join(pipeline_dir, "parameters")


def load_json(path: Path | str) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path | str, data: dict[str, Any]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def set_nested(d: dict[str, Any], key: str, value: Any) -> None:
    if "." not in key:
        d[key] = value
        return
    parts = key.split(".")
    cur = d
    for part in parts[:-1]:
        cur = cur.setdefault(part, {})
    cur[parts[-1]] = value


def apply_overlay(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    out = copy.deepcopy(base)
    for key, value in overlay.items():
        set_nested(out, key, value)
    return out


def write_stage_params(
    out_dir: Path,
    stage: str,
    high_params: dict[str, Any],
    overlay: dict[str, Any] | None = None,
) -> Path:
    merged = apply_overlay(high_params, overlay or {})
    path = out_dir / f"parameters_{stage}.json"
    save_json(path, merged)
    return path


def materialize_run_params(
    out_dir: Path,
    high_by_stage: dict[str, dict[str, Any]],
    overlay_by_stage: dict[str, dict[str, Any]] | None = None,
) -> Path:
    """Write full parameter set for a run; stages without overlay keep HIGH."""
    out_dir.mkdir(parents=True, exist_ok=True)
    overlay_by_stage = overlay_by_stage or {}
    for stage, high in high_by_stage.items():
        write_stage_params(out_dir, stage, high, overlay_by_stage.get(stage))
    return out_dir
