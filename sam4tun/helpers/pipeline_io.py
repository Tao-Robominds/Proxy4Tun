"""Artifact paths for the modular SAM4Tun pipeline."""

from __future__ import annotations

import os
from pathlib import Path

SAM4TUN_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO_ROOT = os.path.dirname(SAM4TUN_ROOT)

# Protected experiment roots — never overwrite via ensure_dir / prepare_output_dir.
PROTECTED_OUT_NAMES = frozenset({"baseline", "bo"})


class OutputPathError(RuntimeError):
    """Raised when an output path is unsafe or already occupied."""


def _repo_data_root() -> str:
    return os.path.join(REPO_ROOT, "data")


def _out_root() -> str:
    """Optional override so agents can write under repo data/<tunnel_id>/."""
    override = (os.environ.get("PROXY4TUN_OUT_ROOT") or "").strip()
    if override:
        return os.path.abspath(override)
    # Legacy modular scripts historically defaulted to sam4tun/data/.
    # New CLI sets PROXY4TUN_OUT_ROOT to repo data/ explicitly.
    return os.path.join(SAM4TUN_ROOT, "data")


def pipeline_dir(tunnel_id: str) -> str:
    return os.path.join(_out_root(), tunnel_id)


def _is_protected_path(path: str | Path) -> bool:
    resolved = Path(path).resolve()
    parts = resolved.parts
    for name in PROTECTED_OUT_NAMES:
        if name in parts:
            # Protect .../data/baseline and .../data/bo (and nested).
            try:
                data_idx = parts.index("data")
            except ValueError:
                continue
            if data_idx + 1 < len(parts) and parts[data_idx + 1] == name:
                return True
    return False


def prepare_output_dir(
    tunnel_id: str,
    *,
    overwrite: bool = False,
    resume: bool = False,
) -> str:
    """Create or validate the output directory for a run.

    Rejects an existing non-empty directory unless ``overwrite`` or ``resume``.
    Always rejects protected roots ``data/baseline`` and ``data/bo``.
    """
    out = pipeline_dir(tunnel_id)
    if _is_protected_path(out):
        raise OutputPathError(
            f"Refusing to write under protected experiment path: {out}"
        )
    if os.path.isdir(out) and os.listdir(out):
        if not (overwrite or resume):
            raise OutputPathError(
                f"Output directory already exists and is not empty: {out}. "
                "Pass overwrite=True or resume=True (CLI: --overwrite / --resume)."
            )
    os.makedirs(out, exist_ok=True)
    return out


def artifact_paths(tunnel_id: str) -> dict[str, str]:
    d = pipeline_dir(tunnel_id)
    mono = os.path.join(SAM4TUN_ROOT, "data", "monolith")
    input_override = (os.environ.get("PROXY4TUN_INPUT_TXT") or "").strip()
    input_txt = input_override or os.path.join(SAM4TUN_ROOT, "data", f"{tunnel_id}.txt")
    return {
        "input_txt": input_txt,
        "state": os.path.join(d, "state.pkl"),
        "unwrapped_csv": os.path.join(d, "unwrapped.csv"),
        "denoised_csv": os.path.join(d, "denoised.csv"),
        "enhanced_csv": os.path.join(d, "enhanced.csv"),
        "pixel_to_point": os.path.join(d, "pixel_to_point.pkl"),
        "depth_map": os.path.join(d, "depth_map.png"),
        "depth_map_outlier": os.path.join(d, "depth_map_outlier.npy"),
        "detected_lines": os.path.join(d, "detected_lines.png"),
        "initial_points": os.path.join(d, "initial_points.csv"),
        "results_pkl": os.path.join(d, "results.pkl"),
        "final_csv": os.path.join(d, "final.csv"),
        "only_label": os.path.join(d, "only_label.csv"),
        "evaluation_dir": os.path.join(d, "evaluation"),
        "monolith_dir": mono,
        "sam_checkpoint": os.path.join(
            SAM4TUN_ROOT, "segment-anything", "sam_vit_h_4b8939.pth"
        ),
        "segment_anything": os.path.join(SAM4TUN_ROOT, "segment-anything"),
    }


def ensure_dir(
    tunnel_id: str,
    *,
    overwrite: bool = False,
    resume: bool = False,
    allow_existing: bool | None = None,
) -> dict[str, str]:
    """Ensure output dirs exist and return artifact paths.

    By default, existing non-empty output dirs are allowed for backward
    compatibility with stage-by-stage scripts (each stage reuses the same
    tunnel directory). Set ``allow_existing=False`` (or use
    ``prepare_output_dir`` from the CLI) to enforce overwrite/resume gates.

    Protected paths ``data/baseline`` and ``data/bo`` are always rejected.
    """
    out = pipeline_dir(tunnel_id)
    if _is_protected_path(out):
        raise OutputPathError(
            f"Refusing to write under protected experiment path: {out}"
        )
    if allow_existing is False:
        prepare_output_dir(tunnel_id, overwrite=overwrite, resume=resume)
    else:
        os.makedirs(out, exist_ok=True)
    paths = artifact_paths(tunnel_id)
    os.makedirs(paths["evaluation_dir"], exist_ok=True)
    return paths


def monolith_data_dir() -> str:
    path = os.path.join(SAM4TUN_ROOT, "data", "monolith")
    os.makedirs(path, exist_ok=True)
    return path
