"""Shared unified-pipeline stage runner for bo-unified."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BO_DIR = Path(__file__).resolve().parent
VENV_PY = REPO_ROOT / "venv" / "bin" / "python"
SCRIPT_DIR = REPO_ROOT / "anchors" / "unified"
DATA_ROOT = REPO_ROOT / "data" / "bo-unified"

STAGE_SCRIPTS = {
    1: "1_unfolding.py",
    2: "2_denoising.py",
    3: "3_enhancing.py",
    4: "4_detection.py",
    5: "5_sam.py",
    6: "6_evaluation.py",
}
CHECKPOINT_FILES = [
    "state.pkl",
    "unwrapped.csv",
    "projected_point_cloud_bbox.png",
    "slice_point_cloud_2d.png",
    "ellipse_centres_3d.png",
    "tunnel_centre_curve_3d.png",
]
MIoU_RE = re.compile(r"Mean IoU \(mIoU\):\s*([\d.]+)")


def parse_performance(perf_path: Path) -> dict[str, float]:
    if not perf_path.exists():
        return {}
    text = perf_path.read_text(encoding="utf-8")
    out: dict[str, float] = {}
    patterns = {
        "OA": r"Overall Accuracy \(OA\):\s*([\d.]+)",
        "F1": r"F1 Score:\s*([\d.]+)",
        "mIoU": r"Mean IoU \(mIoU\):\s*([\d.]+)",
        "mAP": r"mAP:\s*([\d.]+)",
    }
    for k, pat in patterns.items():
        m = re.search(pat, text)
        if m:
            out[k] = float(m.group(1))
    return out


def make_env(input_txt: Path, params_dir: Path, out_root: Path) -> dict[str, str]:
    env = os.environ.copy()
    env["MPLBACKEND"] = "Agg"
    env["PROXY4TUN_OUT_ROOT"] = str(out_root.resolve())
    env["PROXY4TUN_INPUT_TXT"] = str(input_txt.resolve())
    env["PROXY4TUN_PARAMS_DIR"] = str(params_dir.resolve())
    env["PYTHONPATH"] = os.pathsep.join(
        [
            str(SCRIPT_DIR),
            str(REPO_ROOT / "sam4tun"),
            str(REPO_ROOT / "sam4tun" / "segment-anything"),
            env.get("PYTHONPATH", ""),
        ]
    ).rstrip(os.pathsep)
    return env


def run_stages(
    *,
    run_id: str,
    params_dir: Path,
    input_txt: Path,
    out_root: Path,
    log_path: Path,
    start_stage: int = 1,
    end_stage: int = 6,
) -> tuple[str, float]:
    t0 = time.time()
    lines: list[str] = []
    env = make_env(input_txt, params_dir, out_root)
    for stage in range(start_stage, end_stage + 1):
        script = SCRIPT_DIR / STAGE_SCRIPTS[stage]
        lines.append(f"\n=== stage {stage}: {script.name} ===\n")
        proc = subprocess.run(
            [str(VENV_PY), "-u", str(script), run_id],
            cwd=str(REPO_ROOT),
            env=env,
            capture_output=True,
            text=True,
        )
        lines.append(proc.stdout or "")
        if proc.stderr:
            lines.append(proc.stderr)
        if proc.returncode != 0:
            lines.append(f"\nFAILED stage {stage} exit={proc.returncode}\n")
            log_path.write_text("".join(lines), encoding="utf-8")
            raise RuntimeError(f"Stage {stage} failed for {run_id}; see {log_path}")
    elapsed = time.time() - t0
    text = "".join(lines)
    log_path.write_text(text, encoding="utf-8")
    return text, elapsed


def copy_checkpoint(src_dir: Path, dst_dir: Path) -> int:
    dst_dir.mkdir(parents=True, exist_ok=True)
    n = 0
    for fname in CHECKPOINT_FILES:
        src = src_dir / fname
        if src.exists():
            shutil.copy2(src, dst_dir / fname)
            n += 1
    return n


def trial_run_id(case: str, index: int | str) -> str:
    if isinstance(index, int):
        return f"{case}-t{index:03d}"
    return f"{case}-{index}"
