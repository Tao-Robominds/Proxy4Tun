from pathlib import Path
from dataclasses import replace

import numpy as np
import pandas as pd

from sam4tun.config import REFERENCE_CONFIGS, get_reference_config
from sam4tun.state import StageState
from sam4tun.stages.stage1_centreline import generate_slices, unroll_points
from sam4tun.stages import run_stage1, run_stage2
from sam4tun.stages.stage2_denoise import denoise_point_cloud
from sam4tun.stages.stage3_upsample import project_to_depth_map
from sam4tun.stages.stage4_detection import build_ring_centres, prompt_centres
from sam4tun.stages.stage5_segmentation import (
    merge_instances,
    reproject_labels,
    segment_instances,
)


def test_reference_profiles_use_physical_features():
    compact = get_reference_config("compact_six_segment_railway")
    sparse = get_reference_config("shallow_key_six_segment_sparse_joint")
    large = get_reference_config("large_seven_segment_top_tube")
    assert len(REFERENCE_CONFIGS) == 3
    assert compact.geometry.segment_count == sparse.geometry.segment_count == 6
    assert large.geometry.segment_count == 7
    assert compact.stage1.obstruction == "railway_bottom"
    assert large.stage1.obstruction == "service_tube_top"
    assert large.geometry.block_labels[-2:] == ("A4", "B2")


def test_state_manifest_round_trip(tmp_path: Path):
    state = StageState(1, "centreline", "completed", "profile", {"ring_count": 3})
    state.add_artifact("cloud", "cloud.csv", "text/csv")
    manifest = state.write(tmp_path / "manifest.json")
    loaded = StageState.read(manifest)
    assert loaded.parameters["ring_count"] == 3
    assert loaded.require("cloud", manifest) == tmp_path / "cloud.csv"


def test_stage1_slice_and_unroll_primitives():
    axis_x = np.linspace(0, 2.4, 20)
    points = np.column_stack((axis_x, np.ones(20), np.zeros(20)))
    origins, slices, ring_count = generate_slices(
        points, np.array([0, 0, 0]), np.array([2.4, 0, 0]), 1.2, 0.1
    )
    assert ring_count == 2
    assert len(origins) == len(slices) == 2
    curve = np.column_stack((axis_x, np.zeros(20), np.zeros(20)))
    tangents = np.tile([1.0, 0.0, 0.0], (20, 1))
    cylindrical = unroll_points(points, curve, tangents, 5.5)
    assert cylindrical.shape == (20, 3)
    assert np.allclose(cylindrical[:, 0], 1.0)


def test_manifests_connect_stage1_to_stage2(tmp_path: Path):
    pipeline = get_reference_config("compact_six_segment_railway")
    stage1_config = replace(
        pipeline.stage1,
        obstruction="none",
        ellipse_ransac_iterations=10,
        curve_sample_factor=10,
    )
    rng = np.random.default_rng(3)
    rows = []
    for x in np.linspace(0, 3.6, 4):
        for angle in np.linspace(0, 2 * np.pi, 80, endpoint=False):
            rows.append(
                [
                    x + rng.normal(0, 0.001),
                    2.75 * np.cos(angle),
                    2.75 * np.sin(angle),
                    100,
                    1,
                    int(round(x / 1.2)),
                ]
            )
    input_path = tmp_path / "cloud.txt"
    np.savetxt(input_path, np.asarray(rows))
    stage1_manifest = run_stage1(
        input_path,
        tmp_path / "stage1",
        pipeline.geometry,
        stage1_config,
        pipeline.profile,
    )
    stage2_manifest = run_stage2(
        stage1_manifest,
        tmp_path / "stage2",
        pipeline.stage2,
        pipeline.profile,
    )
    state2 = StageState.read(stage2_manifest)
    assert Path(state2.upstream_manifest) == Path(stage1_manifest).resolve()
    assert state2.require("denoised_point_cloud", stage2_manifest).exists()


def test_stage2_correct_angular_gate_and_labels():
    config = get_reference_config("shallow_key_six_segment_sparse_joint").stage2
    rows = 100
    df = pd.DataFrame(
        {
            "h": np.linspace(0, 4, rows),
            "theta": np.linspace(0, 18, rows),
            "r": np.full(rows, 2.9),
        }
    )
    result, cutoffs = denoise_point_cloud(df, 4, config)
    assert not cutoffs.empty
    assert (result.loc[result["theta"] < 1.55, "pred"] == 0).all()
    assert (result.loc[result["theta"] > 17.15, "pred"] == 0).all()


def test_stage3_projection_preserves_point_mapping():
    config = get_reference_config("compact_six_segment_railway").stage3
    surface = pd.DataFrame(
        {
            "h": [0.0, 0.01],
            "theta": [0.0, 0.01],
            "r": [2.7, 2.71],
            "pred": [7, config.surface_interpolated_marker],
            "point_index": [42, -1],
        }
    )
    joints = surface.iloc[0:0].copy()
    depth, mapping, transform = project_to_depth_map(surface, joints, config)
    assert depth.shape == (3, 3)
    assert mapping["point_index"].tolist() == [42]
    assert transform["resolution"] == config.resolution_m_per_px


def test_stage4_falls_back_without_hough_lines():
    pipeline = get_reference_config("compact_six_segment_railway")
    centres = build_ring_centres([], 500, 2, 240)
    prompts = prompt_centres(
        centres,
        {"positive": [], "negative": [], "horizontal": [], "vertical": []},
        400,
        pipeline.geometry,
        0.005,
        pipeline.stage4,
    )
    assert len(prompts) == 2
    assert set(prompts["Type"]) == {"image_center"}


class FakePredictor:
    def set_image(self, image):
        self.shape = image.shape[:2]

    def predict(self, point_coords, point_labels, mask_input, multimask_output):
        mask = np.ones((1, *self.shape), dtype=bool)
        score = np.array([0.9])
        logits = np.ones((1, 256, 256), dtype=np.float32)
        return mask, score, logits


def test_stage5_segments_merges_and_reprojects():
    pipeline = get_reference_config("compact_six_segment_railway")
    image = np.zeros((800, 400, 3), dtype=np.uint8)
    prompts = pd.DataFrame({"Type": ["midpoint"], "X": [200.0], "Y": [400.0]})
    results = segment_instances(
        image,
        prompts,
        pipeline.geometry,
        pipeline.stage5,
        0.005,
        FakePredictor(),
    )
    assert len(results) == 1
    assert len(results[0]) == 6
    logits, labels, rings = merge_instances(
        results, image.shape[:2], pipeline.geometry.block_to_label
    )
    assert logits.shape == labels.shape == rings.shape == image.shape[:2]
    ys, xs = np.where(labels > 0)
    mapping = pd.DataFrame(
        {"pixel_x": [xs[0]], "pixel_y": [ys[0]], "point_index": [10]}
    )
    cloud = pd.DataFrame({"point_index": [10], "pred": [7]})
    projected = reproject_labels(cloud, mapping, labels, rings, 7, False)
    assert projected.loc[0, "pred"] > 0
    assert projected.loc[0, "pred_ring"] == 0
