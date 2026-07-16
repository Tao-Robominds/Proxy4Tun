"""Stage 5: template-prompt SAM segmentation and 3-D reprojection."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from ..config import GeometryConfig, Stage5Config
from ..io import ensure_output_dir, save_array, save_dataframe, save_pickle
from ..state import StageState


def load_predictor(config: Stage5Config) -> Any:
    """Load Segment Anything lazily so stages 1-4 do not require it."""

    import torch

    try:
        from segment_anything import SamPredictor, sam_model_registry
    except ImportError as exc:
        raise RuntimeError(
            "Stage 5 requires Meta's segment-anything package. Install it and "
            "set stage5.sam_checkpoint to a valid checkpoint."
        ) from exc
    device = config.device
    if device.startswith("cuda") and not torch.cuda.is_available():
        device = "cpu"
    model = sam_model_registry[config.sam_model_type](checkpoint=config.sam_checkpoint)
    model.to(device=device)
    return SamPredictor(model)


def depth_to_rgb(depth: np.ndarray) -> np.ndarray:
    import matplotlib

    valid = depth[~np.isnan(depth)]
    if not len(valid):
        return np.zeros((*depth.shape, 3), dtype=np.uint8)
    low, high = np.percentile(valid, [1, 99])
    normalized = np.nan_to_num((depth - low) / max(high - low, 1e-8))
    return (matplotlib.colormaps["viridis"](np.clip(normalized, 0, 1))[..., :3] * 255).astype(
        np.uint8
    )


def block_polygon_mm(
    block: str, geometry: GeometryConfig, half_width: float
) -> np.ndarray:
    height = (
        geometry.key_height_mm if block == "K" else geometry.regular_height_mm
    )
    slope = np.tan(np.deg2rad(geometry.taper_angle_deg)) * half_width
    # B1/B2 slope directions are mirrored; A blocks are near-rectangular.
    sign = 1 if block in ("K", "B1") else -1 if block == "B2" else 0
    return np.array(
        [
            [-half_width, -height / 2 - sign * slope],
            [-half_width, height / 2 - sign * slope],
            [half_width, height / 2 + sign * slope],
            [half_width, -height / 2 + sign * slope],
        ],
        dtype=float,
    )


def polygon_mask(
    height: int,
    width: int,
    centre: tuple[float, float],
    vertices_px: np.ndarray,
) -> np.ndarray:
    from matplotlib.path import Path as PolygonPath

    vertices = vertices_px + np.asarray(centre)
    yy, xx = np.mgrid[:height, :width]
    inside = PolygonPath(vertices).contains_points(
        np.column_stack((xx.ravel(), yy.ravel()))
    )
    return inside.reshape(height, width)


def template_and_prompts(
    crop_shape: tuple[int, int],
    centre: tuple[float, float],
    block: str,
    map_y_px: float,
    geometry: GeometryConfig,
    config: Stage5Config,
    resolution: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    height, width = crop_shape
    scale = 1000 * resolution
    polygon_mm = block_polygon_mm(
        block, geometry, config.prompt.template_half_width_mm
    )
    polygon_px = polygon_mm / scale
    mask = polygon_mask(height, width, centre, polygon_px)

    gx, gy = config.prompt.positive_grid
    xs = np.linspace(
        centre[0] - config.prompt.template_half_width_mm / scale * 0.7,
        centre[0] + config.prompt.template_half_width_mm / scale * 0.7,
        gx,
    )
    block_height = (
        geometry.key_height_mm if block == "K" else geometry.regular_height_mm
    )
    ys = np.linspace(
        centre[1] - block_height / scale * 0.35,
        centre[1] + block_height / scale * 0.35,
        gy,
    )
    positive = np.array([(x, y) for y in ys for x in xs if 0 <= x < width and 0 <= y < height])
    margin = config.prompt.negative_margin_mm / scale
    min_x, min_y = np.min(polygon_px, axis=0) + centre
    max_x, max_y = np.max(polygon_px, axis=0) + centre
    negative = np.array(
        [
            (min_x - margin, min_y),
            (min_x - margin, max_y),
            (max_x + margin, min_y),
            (max_x + margin, max_y),
            (centre[0], min_y - margin),
            (centre[0], max_y + margin),
        ]
    )
    negative = negative[
        (negative[:, 0] >= 0)
        & (negative[:, 0] < width)
        & (negative[:, 1] >= 0)
        & (negative[:, 1] < height)
    ]
    points = np.vstack((positive, negative))
    labels = np.r_[np.ones(len(positive), dtype=int), np.zeros(len(negative), dtype=int)]
    sealing = config.prompt.sealing_y_range_mm
    if sealing and not sealing[0] <= map_y_px * scale <= sealing[1]:
        if config.prompt.sealing_mode == "drop":
            keep = labels == 1
            points, labels = points[keep], labels[keep]
        elif config.prompt.sealing_mode == "flip":
            labels[labels == 0] = 1
    return mask, points.astype(float), labels


def mask_to_sam_logits(mask: np.ndarray, eps: float = 1e-3) -> np.ndarray:
    """Notebook-compatible `(1, 256, 256)` template logits."""

    import cv2

    probability = np.where(mask, 1 - eps, eps).astype(np.float32)
    logits = np.log(probability / (1 - probability))
    resized = cv2.resize(logits, (256, 256), interpolation=cv2.INTER_LINEAR)
    return resized[None]


def _crop(
    image: np.ndarray, cx: float, cy: float, half_width: int, half_height: int
) -> tuple[np.ndarray, tuple[int, int], tuple[float, float]]:
    image_height, image_width = image.shape[:2]
    x1, x2 = max(0, int(cx - half_width)), min(image_width, int(cx + half_width))
    y1, y2 = max(0, int(cy - half_height)), min(image_height, int(cy + half_height))
    return image[y1:y2, x1:x2], (x1, y1), (cx - x1, cy - y1)


def segment_instances(
    image: np.ndarray,
    prompts: pd.DataFrame,
    geometry: GeometryConfig,
    config: Stage5Config,
    resolution: float,
    predictor: Any,
) -> list[list[dict]]:
    results: list[list[dict]] = []
    scale = 1000 * resolution
    half_width = int(
        (geometry.segment_width_mm / 2 + config.crop_margin_x_mm) / scale
    )
    for _, prompt in prompts.iterrows():
        ring_results = []
        y = float(prompt["Y"])
        for block_index, block in enumerate(geometry.block_labels):
            if block_index:
                previous = (
                    geometry.key_height_mm
                    if block_index == 1
                    else geometry.regular_height_mm
                )
                current = geometry.regular_height_mm
                y -= (previous + current) / (2 * scale)
            # Circumferential unrolling is periodic. This replaces the notebook's
            # reverse/stop branches while preserving edge blocks.
            map_y = y % image.shape[0]
            block_height = (
                geometry.key_height_mm if block == "K" else geometry.regular_height_mm
            )
            taper = (
                np.tan(np.deg2rad(geometry.taper_angle_deg))
                * config.taper_crop_offset_mm
            )
            half_height = int(
                (block_height / 2 + taper + config.crop_margin_y_mm) / scale
            )
            crop, left_top, centre = _crop(
                image, float(prompt["X"]), map_y, half_width, half_height
            )
            if not crop.size:
                continue
            template, points, labels = template_and_prompts(
                crop.shape[:2],
                centre,
                block,
                map_y,
                geometry,
                config,
                resolution,
            )
            predictor.set_image(crop)
            masks, scores, low_res = predictor.predict(
                point_coords=points,
                point_labels=labels,
                mask_input=mask_to_sam_logits(template),
                multimask_output=False,
            )
            ring_results.append(
                {
                    "left_top": left_top,
                    "block": block,
                    "mask": masks[0],
                    "score": float(np.asarray(scores).ravel()[0]),
                    "logit": np.asarray(low_res)[0],
                    "points": points,
                    "labels": labels,
                }
            )
        results.append(ring_results)
    return results


def merge_instances(
    results: list[list[dict]],
    image_shape: tuple[int, int],
    block_to_label: dict[str, int],
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    import cv2

    height, width = image_shape
    logits_map = np.full((height, width), -np.inf, dtype=np.float32)
    label_map = np.zeros((height, width), dtype=np.int16)
    ring_map = np.full((height, width), -1, dtype=np.int32)
    for ring_index, ring in enumerate(results):
        for item in ring:
            mask = np.asarray(item["mask"], dtype=bool)
            logits = cv2.resize(
                np.asarray(item["logit"], dtype=np.float32),
                (mask.shape[1], mask.shape[0]),
                interpolation=cv2.INTER_LINEAR,
            )
            x1, y1 = map(int, item["left_top"])
            x2, y2 = min(width, x1 + mask.shape[1]), min(height, y1 + mask.shape[0])
            source_x1, source_y1 = max(0, -x1), max(0, -y1)
            x1, y1 = max(0, x1), max(0, y1)
            valid_h, valid_w = y2 - y1, x2 - x1
            if valid_h <= 0 or valid_w <= 0:
                continue
            mask = mask[source_y1 : source_y1 + valid_h, source_x1 : source_x1 + valid_w]
            logits = logits[
                source_y1 : source_y1 + valid_h, source_x1 : source_x1 + valid_w
            ]
            current = logits_map[y1:y2, x1:x2]
            update = mask & (logits > current)
            current[update] = logits[update]
            label_map[y1:y2, x1:x2][update] = block_to_label[item["block"]]
            ring_map[y1:y2, x1:x2][update] = ring_index
    return logits_map, label_map, ring_map


def reproject_labels(
    point_cloud: pd.DataFrame,
    mapping: pd.DataFrame,
    labels: np.ndarray,
    rings: np.ndarray,
    lining_marker: int,
    clear_unassigned: bool,
) -> pd.DataFrame:
    result = point_cloud.copy()
    if "point_index" not in result:
        result["point_index"] = np.arange(len(result))
    result["pred_ring"] = -1
    valid_mapping = mapping[
        mapping["point_index"].isin(result["point_index"])
    ].copy()
    row_lookup = pd.Series(result.index, index=result["point_index"]).to_dict()
    for row in valid_mapping.itertuples(index=False):
        target = row_lookup[int(row.point_index)]
        if int(result.at[target, "pred"]) != lining_marker:
            continue
        result.at[target, "pred"] = int(labels[int(row.pixel_y), int(row.pixel_x)])
        result.at[target, "pred_ring"] = int(rings[int(row.pixel_y), int(row.pixel_x)])
    if clear_unassigned:
        result.loc[
            (result["pred"] == lining_marker) & (result["pred_ring"] == -1), "pred"
        ] = 0
    return result


def run_stage5(
    upstream_manifest: str | Path,
    output_dir: str | Path,
    geometry: GeometryConfig,
    config: Stage5Config,
    profile: str,
    predictor: Any | None = None,
) -> Path:
    upstream_manifest = Path(upstream_manifest)
    detection = StageState.read(upstream_manifest)
    stage3_manifest = Path(detection.upstream_manifest or "")
    stage3 = StageState.read(stage3_manifest)
    stage2_manifest = Path(stage3.upstream_manifest or "")
    stage2 = StageState.read(stage2_manifest)
    output_dir = ensure_output_dir(output_dir)
    depth = np.load(stage3.require("depth_map", stage3_manifest))
    image = depth_to_rgb(depth)
    prompts = pd.read_csv(detection.require("prompt_centres", upstream_manifest))
    mapping = pd.read_csv(stage3.require("pixel_to_point", stage3_manifest))
    cloud = pd.read_csv(stage3.require("filtered_point_cloud", stage3_manifest))
    resolution = float(stage3.parameters["projection_transform"]["resolution"])
    predictor = predictor or load_predictor(config)
    results = segment_instances(
        image, prompts, geometry, config, resolution, predictor
    )
    logits, labels, rings = merge_instances(
        results, depth.shape, geometry.block_to_label
    )
    if config.ring_index_mode == "reverse":
        valid = rings >= 0
        rings[valid] = int(stage3.parameters["ring_count"]) - 1 - rings[valid]
    lining_marker = int(stage2.parameters["stage"]["lining_marker"])
    final = reproject_labels(
        cloud,
        mapping,
        labels,
        rings,
        lining_marker,
        config.clear_unassigned_lining,
    )
    evaluation = pd.DataFrame(
        {
            "gt_labels": final.get("segment", pd.Series(-1, index=final.index)),
            "gt_rings": final.get("ring", pd.Series(-1, index=final.index)),
            "pred_labels": final["pred"],
            "pred_rings": final["pred_ring"],
        }
    )

    results_path = save_pickle(results, output_dir / "results.pkl")
    logits_path = save_array(logits, output_dir / "logits_map.npy")
    labels_path = save_array(labels, output_dir / "label_map.npy")
    rings_path = save_array(rings, output_dir / "ring_map.npy")
    final_path = save_dataframe(final, output_dir / "segmented_point_cloud.csv")
    eval_path = save_dataframe(evaluation, output_dir / "labels_for_evaluation.csv")
    state = StageState(
        5,
        "segmentation",
        "completed",
        profile,
        {"stage": asdict(config), "geometry": asdict(geometry)},
        metrics={
            "instance_count": sum(len(ring) for ring in results),
            "mean_sam_score": float(
                np.mean([item["score"] for ring in results for item in ring])
            )
            if any(results)
            else 0.0,
            "labelled_pixel_ratio": float((labels > 0).mean()),
            "assigned_point_ratio": float((final["pred_ring"] >= 0).mean()),
        },
        upstream_manifest=str(upstream_manifest),
    )
    state.add_artifact("sam_results", results_path.name, "application/x-python-pickle")
    state.add_artifact("logits_map", logits_path.name, "application/x-npy")
    state.add_artifact("label_map", labels_path.name, "application/x-npy")
    state.add_artifact("ring_map", rings_path.name, "application/x-npy")
    state.add_artifact("segmented_point_cloud", final_path.name, "text/csv")
    state.add_artifact("evaluation_labels", eval_path.name, "text/csv")
    return state.write(output_dir / "manifest.json")
