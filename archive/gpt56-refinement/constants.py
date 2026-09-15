"""Shared constants for the GPT-5.6 isolated refinement campaign."""
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CAMPAIGN_DIR = Path(__file__).resolve().parent
KNOWLEDGE_DIR = CAMPAIGN_DIR / "knowledge"
PACKETS_DIR = CAMPAIGN_DIR / "packets"
SELECTIONS_DIR = CAMPAIGN_DIR / "selections"
LOGS_DIR = CAMPAIGN_DIR / "logs"

ARM = "gpt56"
MODEL_ID = "gpt-5.6-sol-medium"
MODEL_LABEL = "GPT-5.6 Sol"

# Nine GT-low refine-band subsets (same panel as the Fable campaign).
SUBSETS = [
    "3-4", "3-2", "3-5",
    "4-4", "4-3", "4-1",
    "1-4", "1-5", "2-2",
]

# Neutral stage-1 unlock: residual > 10 cm (from holdout table / stage1_gate).
STAGE1_UNLOCK = {"3-2", "3-4", "3-5", "4-3", "4-4"}

TIE_MARGIN = 0.01
RESIDUAL_UNLOCK_CM = 10.0

# Artifact images exposed to the agent (GT-free). Never include evaluation/.
AGENT_IMAGES = [
    "depth_map.png",
    "depth_map_viridis.png",
    "detected_lines.png",
    "initial_prompt_points.png",
    "segmentation_results.png",
    "sam_depth_input.png",
]

# Intrinsic keys stripped from model-facing packets (GT leakage).
GT_KEYS = {
    "mIoU", "perf_mIoU", "perf_OA", "perf_F1", "perf_mAP",
    "OA", "F1", "mAP",
}


def out_root(subset: str) -> Path:
    """data/<subset>-gpt56-refinement/ — campaign artifacts for one tunnel."""
    return REPO_ROOT / "data" / f"{subset}-gpt56-refinement"


def round_dir(subset: str, round_id: int) -> Path:
    return out_root(subset) / f"round{round_id}"
