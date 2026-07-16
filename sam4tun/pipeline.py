"""Pipeline orchestration and CLI."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from .config import REFERENCE_CONFIGS, PipelineConfig, get_reference_config
from .stages import run_stage1, run_stage2, run_stage3, run_stage4, run_stage5


def run_pipeline(
    input_path: str | Path,
    output_root: str | Path,
    config: PipelineConfig,
    *,
    through_stage: int = 5,
    predictor: Any | None = None,
) -> Path:
    """Run sequentially, passing only manifest-backed intermediate state."""

    if not 1 <= through_stage <= 5:
        raise ValueError("through_stage must be between 1 and 5")
    output_root = Path(output_root)
    manifest = run_stage1(
        input_path,
        output_root / "stage1_centreline",
        config.geometry,
        config.stage1,
        config.profile,
    )
    if through_stage == 1:
        return manifest
    manifest = run_stage2(
        manifest, output_root / "stage2_denoise", config.stage2, config.profile
    )
    if through_stage == 2:
        return manifest
    manifest = run_stage3(
        manifest,
        output_root / "stage3_upsample",
        config.geometry,
        config.stage3,
        config.profile,
    )
    if through_stage == 3:
        return manifest
    manifest = run_stage4(
        manifest,
        output_root / "stage4_detection",
        config.geometry,
        config.stage4,
        config.profile,
    )
    if through_stage == 4:
        return manifest
    return run_stage5(
        manifest,
        output_root / "stage5_segmentation",
        config.geometry,
        config.stage5,
        config.profile,
        predictor=predictor,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the five-stage SAM4Tun pipeline")
    parser.add_argument("input", help="Nx6 point-cloud TXT or CSV")
    parser.add_argument("output", help="Output directory")
    parser.add_argument(
        "--profile",
        choices=sorted(REFERENCE_CONFIGS),
        default="compact_six_segment_railway",
        help="Feature-based reference profile (not a tunnel-id switch)",
    )
    parser.add_argument("--through-stage", type=int, choices=range(1, 6), default=5)
    args = parser.parse_args()
    manifest = run_pipeline(
        args.input,
        args.output,
        get_reference_config(args.profile),
        through_stage=args.through_stage,
    )
    print(manifest)


if __name__ == "__main__":
    main()
