"""Parameterized five-stage SAM4Tun pipeline."""

from .config import PipelineConfig, get_reference_config
from .state import Artifact, StageState


def run_pipeline(*args, **kwargs):
    """Import the orchestrator lazily to keep ``python -m`` warning-free."""

    from .pipeline import run_pipeline as _run_pipeline

    return _run_pipeline(*args, **kwargs)

__all__ = [
    "Artifact",
    "PipelineConfig",
    "StageState",
    "get_reference_config",
    "run_pipeline",
]
