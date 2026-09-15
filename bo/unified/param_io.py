"""Parameter overlay I/O for bo-unified (includes parameters_family.json)."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any


STAGES = ("unfolding", "denoising", "enhancing", "detecting", "sam")
FAMILY_FILENAME = "parameters_family.json"


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


def get_nested(d: dict[str, Any], key: str) -> Any:
    if "." not in key:
        return d[key]
    cur: Any = d
    for part in key.split("."):
        cur = cur[part]
    return cur


def apply_overlay(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    out = copy.deepcopy(base)
    for key, value in overlay.items():
        set_nested(out, key, value)
    return out


def load_family_params(params_dir: Path) -> dict[str, Any]:
    path = Path(params_dir) / FAMILY_FILENAME
    if not path.exists():
        raise FileNotFoundError(f"Missing {path}")
    return load_json(path)


def load_anchor_params(params_dir: Path) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for stage in STAGES:
        path = Path(params_dir) / f"parameters_{stage}.json"
        out[stage] = load_json(path)
    return out


def materialize_run_params(
    out_dir: Path,
    base_by_stage: dict[str, dict[str, Any]],
    overlay_by_stage: dict[str, dict[str, Any]] | None = None,
    *,
    family_params: dict[str, Any] | None = None,
    family_src_dir: Path | None = None,
) -> Path:
    """Write full parameter set for a run; always emit parameters_family.json."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    overlay_by_stage = overlay_by_stage or {}
    for stage, base in base_by_stage.items():
        if stage == "family":
            continue
        merged = apply_overlay(base, overlay_by_stage.get(stage, {}))
        save_json(out_dir / f"parameters_{stage}.json", merged)

    fam = family_params
    if fam is None and family_src_dir is not None:
        fam = load_family_params(family_src_dir)
    if fam is None:
        raise ValueError("family_params or family_src_dir required for unified runs")
    save_json(out_dir / FAMILY_FILENAME, fam)
    return out_dir
