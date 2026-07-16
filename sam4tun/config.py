"""Feature-based configuration for the five SAM4Tun stages.

Reference presets reproduce the values used by the three notebooks, but stage
code never branches on a tunnel identifier. Behaviour is selected by physical
geometry, point-density, obstruction and scan-coverage characteristics.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Literal


@dataclass(frozen=True)
class GeometryConfig:
    diameter_m: float
    ring_pitch_m: float
    segment_count: int
    segment_width_mm: float
    key_height_mm: float
    regular_height_mm: float
    taper_angle_deg: float

    @property
    def block_labels(self) -> tuple[str, ...]:
        a_blocks = tuple(f"A{i + 1}" for i in range(self.segment_count - 3))
        return ("K", "B1", *a_blocks, "B2")

    @property
    def block_to_label(self) -> dict[str, int]:
        return {name: i + 1 for i, name in enumerate(self.block_labels)}


@dataclass(frozen=True)
class Stage1Config:
    slice_half_thickness_m: float = 0.005
    ring_count_multiplier: int = 1
    reverse_direction: bool = False
    obstruction: Literal["railway_bottom", "service_tube_top", "none"] = (
        "railway_bottom"
    )
    railway_keep_height_m: float = 4.5
    service_tube_exclusion_radius_m: float = 3.5
    ellipse_ransac_threshold_m: float = 0.05
    ellipse_ransac_inlier_fraction: float = 0.75
    ellipse_ransac_iterations: int = 200
    ellipse_refine: bool = True
    curve_degree: int = 3
    curve_sample_factor: int = 1210
    curve_backend: Literal["scipy", "faiss"] = "scipy"


@dataclass(frozen=True)
class Stage2Config:
    radial_range_m: tuple[float, float]
    angular_range_m: tuple[float, float] | None = None
    lining_marker: int = 7
    h_bins_per_ring: int = 1
    theta_step_m: float = 0.5
    radius_step_m: float = 0.001
    gradient_threshold: float = 0.2
    density_smoothing_bins: int = 10
    cutoff_offset_m: float = -0.003


@dataclass(frozen=True)
class Stage3Config:
    target_distance_schedule_m: tuple[float, ...]
    curvature_neighbors: int = 20
    curvature_threshold: float = 0.0005
    surface_interpolated_marker: int = 8
    midpoint_distance_range: tuple[float, float] = (0.9, 2.0)
    radius_filter_factor: float = 0.15
    depth_threshold_low_m: float = 0.003
    depth_threshold_high_m: float = 0.008
    joint_neighbors: int = 21
    interpolation_radius_m: float = 0.06
    interpolation_count: int = 2
    duplicate_threshold_m: float = 0.02
    high_density_ring_range: tuple[int, int] = (0, 5)
    joint_curvature_min: float | None = None
    interpolate_joints: bool = True
    projection_uses_surface_upsampling: bool = True
    resolution_m_per_px: float = 0.005
    projection_window: int = 9
    mapping_excluded_markers: tuple[int, ...] = (8,)


@dataclass(frozen=True)
class HoughConfig:
    oblique_threshold: int
    oblique_min_length_px: int
    oblique_max_gap_px: int
    horizontal_threshold: int
    horizontal_min_length_px: int
    horizontal_max_gap_px: int
    vertical_threshold: int
    positive_angle_deg: tuple[float, float]
    negative_angle_deg: tuple[float, float]


@dataclass(frozen=True)
class CoverageConfig:
    """How the reliable vertical-joint detection band is positioned."""

    anchor: Literal["left", "center", "absolute"]
    start_ring: float
    end_ring: float
    pitch_override_m: float | None = None


@dataclass(frozen=True)
class Stage4Config:
    hough: HoughConfig
    coverage: CoverageConfig
    intensity_max: float | None = None
    binary_threshold: int = 127
    dilation_kernel: int = 3
    dilation_iterations: int = 1
    vertical_angle_tolerance_deg: float = 0.5
    vertical_merge_distance_px: float = 3.0
    intersection_merge_distance_px: float = 6.0
    pattern_tolerance_px: float = 50.0
    fallback: Literal["geometry_pattern", "previous_prompt", "image_center"] = (
        "geometry_pattern"
    )


@dataclass(frozen=True)
class PromptConfig:
    """Geometry-derived SAM prompt generation.

    `template_half_width_mm` is extracted from notebook polygon vertices.
    Positive and negative prompts are generated as regular grids inside and
    just outside the same polygons, avoiding tunnel-specific hard-coded point
    arrays while preserving their intended geometry.
    """

    template_half_width_mm: float
    positive_grid: tuple[int, int] = (5, 5)
    negative_margin_mm: float = 100.0
    sealing_mode: Literal["drop", "flip", "disabled"] = "drop"
    sealing_y_range_mm: tuple[float, float] | None = (4200.0, 13100.0)


@dataclass(frozen=True)
class Stage5Config:
    prompt: PromptConfig
    sam_model_type: Literal["vit_h", "vit_l", "vit_b"] = "vit_h"
    sam_checkpoint: str = "segment-anything-main/sam_vit_h_4b8939.pth"
    device: str = "cuda"
    taper_crop_offset_mm: float = 700.0
    crop_margin_x_mm: float = 150.0
    crop_margin_y_mm: float = 150.0
    extra_boundary_iteration: bool = False
    ring_index_mode: Literal["preserve_zero", "reverse"] = "preserve_zero"
    clear_unassigned_lining: bool = False


@dataclass(frozen=True)
class PipelineConfig:
    profile: str
    geometry: GeometryConfig
    stage1: Stage1Config
    stage2: Stage2Config
    stage3: Stage3Config
    stage4: Stage4Config
    stage5: Stage5Config

    def to_dict(self) -> dict:
        return asdict(self)


def _compact_six_rail() -> PipelineConfig:
    return PipelineConfig(
        profile="compact_six_segment_railway",
        geometry=GeometryConfig(5.5, 1.2, 6, 1200, 1079.92, 3239.77, 7.52),
        stage1=Stage1Config(curve_degree=3),
        stage2=Stage2Config((2.7, 2.8)),
        stage3=Stage3Config((0.08, 0.04, 0.02)),
        stage4=Stage4Config(
            HoughConfig(50, 100, 40, 50, 100, 10, 500, (6, 9), (-9, -6)),
            CoverageConfig("left", 0, 5),
            fallback="geometry_pattern",
        ),
        stage5=Stage5Config(PromptConfig(625), ring_index_mode="preserve_zero"),
    )


def _shallow_key_six_sparse() -> PipelineConfig:
    return PipelineConfig(
        profile="shallow_key_six_segment_sparse_joint",
        geometry=GeometryConfig(5.9, 1.2, 6, 1200, 823.8, 3346.8, 6.12),
        stage1=Stage1Config(
            reverse_direction=True,
            ellipse_ransac_inlier_fraction=0.8,
            curve_degree=2,
        ),
        stage2=Stage2Config(
            (2.85, 3.0),
            angular_range_m=(1.55, 17.15),
            theta_step_m=0.5,
        ),
        stage3=Stage3Config(
            (0.08, 0.04, 0.02),
            depth_threshold_low_m=0.01,
            depth_threshold_high_m=0.01,
            high_density_ring_range=(11, 11),
            joint_curvature_min=0.01,
            interpolate_joints=False,
            # Notebook overwrote the upsampled surface. Keep this configurable;
            # the corrected production default uses the actual upsampled data.
            projection_uses_surface_upsampling=True,
        ),
        stage4=Stage4Config(
            HoughConfig(30, 40, 30, 30, 50, 10, 1500, (4, 10), (-10, -4)),
            CoverageConfig("absolute", 14, 15.2),
            intensity_max=500,
            fallback="previous_prompt",
        ),
        stage5=Stage5Config(
            PromptConfig(600, sealing_mode="flip", sealing_y_range_mm=(4500, 14000)),
            extra_boundary_iteration=True,
            ring_index_mode="reverse",
        ),
    )


def _large_seven_top_tube() -> PipelineConfig:
    return PipelineConfig(
        profile="large_seven_segment_top_tube",
        geometry=GeometryConfig(7.5, 1.8, 7, 1800, 1226.97, 3726.88, 9.8),
        stage1=Stage1Config(
            ring_count_multiplier=2,
            obstruction="service_tube_top",
            ellipse_refine=False,
            curve_degree=2,
            curve_sample_factor=1810,
        ),
        stage2=Stage2Config(
            (3.65, 3.9),
            lining_marker=9,
            theta_step_m=0.1,
            cutoff_offset_m=-0.005,
        ),
        stage3=Stage3Config(
            (0.09, 0.045, 0.0225),
            surface_interpolated_marker=10,
            depth_threshold_low_m=0.0065,
            depth_threshold_high_m=0.013,
            high_density_ring_range=(5, 14),
            mapping_excluded_markers=(10,),
        ),
        stage4=Stage4Config(
            HoughConfig(50, 100, 50, 50, 105, 10, 800, (5, 10), (-10, -5)),
            CoverageConfig("center", 2, 5, pitch_override_m=1.85),
            fallback="image_center",
        ),
        stage5=Stage5Config(
            PromptConfig(900, sealing_mode="disabled", sealing_y_range_mm=None),
            taper_crop_offset_mm=1000,
            extra_boundary_iteration=True,
            ring_index_mode="reverse",
            clear_unassigned_lining=True,
        ),
    )


REFERENCE_CONFIGS = {
    "compact_six_segment_railway": _compact_six_rail(),
    "shallow_key_six_segment_sparse_joint": _shallow_key_six_sparse(),
    "large_seven_segment_top_tube": _large_seven_top_tube(),
}

# Notebook provenance only; pipeline code does not branch on these names.
NOTEBOOK_REFERENCE = {
    "t1&t2.ipynb": "compact_six_segment_railway",
    "t3.ipynb": "shallow_key_six_segment_sparse_joint",
    "t4&5.ipynb": "large_seven_segment_top_tube",
}


def get_reference_config(profile: str) -> PipelineConfig:
    try:
        return REFERENCE_CONFIGS[profile]
    except KeyError as exc:
        options = ", ".join(sorted(REFERENCE_CONFIGS))
        raise KeyError(f"Unknown profile {profile!r}; choose one of: {options}") from exc
