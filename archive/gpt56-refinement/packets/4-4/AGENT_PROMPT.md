# GPT-5.6 Sol reflection — subset 4-4 (round proposal)

You are a reflective parameter agent for the SAM4Tun tunnel-lining pipeline.
Propose ONE bounded parameter overlay to improve the GT-free scaled proxy.

## Isolation (hard rules)

Read ONLY:
- this packet (`packet.json`)
- `images/` under this packet directory
- knowledge files under `/home/boringtao/Projects/Proxy4Tun/gpt56-refinement/knowledge` (sanitized experiences, ontology, priors)
- allowlist.md / denylist.md in this packet

Do NOT read or search for: data/bo/reflect/, bo/proxy_scale/selections/, campaign logs,
prior Fable/Cursor results, evaluation/, or any mIoU / ground-truth labels.

## State

- subset: `4-4`
- family: `t4&5`
- stage1_unlocked: `True` (residual=35.0 cm)
- anchor_proxy_scaled: `0.6225` (band=refine)

### GT-blind intrinsics
```json
{
  "orient_h_ring_corr": 0.982325904264996,
  "orient_invariant_ok": 1.0,
  "recentre_residual_max_cm": 35.0,
  "denoise_retained_ratio": 0.7307847028878226,
  "depth_nan_ratio": 0.2589034743193495,
  "depth_outlier_ratio": 0.0009653158680709993,
  "det_midpoint_ratio": 0.2,
  "det_real_detection_ratio": 0.4,
  "det_fallback_ratio": 0.6,
  "det_x_spacing_cv": 0.565685424949238,
  "det_y_std": 420.19585501343244,
  "det_ring_count_error": 0.0,
  "det_n_points": 10.0,
  "sam_fill_rate": 0.7221990764584009,
  "sam_ring_completeness": 1.0,
  "sam_segment_size_cv": 1.0641571760916866,
  "sam_ontology_divergence": 0.11076856798207825
}
```

### Lean proxy features
```json
{
  "depth_nan_ratio": 0.2589034743193495,
  "denoise_retained_ratio": 0.7307847028878226,
  "unfold_residual": 3.58351893845611,
  "orient_agreement": 0.9415770058931677,
  "sam_fill_rate": 0.7221990764584009,
  "sam_ontology_divergence": 0.11076856798207825,
  "det_row_residual_px": 0.0,
  "det_row_gated": 0.0,
  "det_row_y_std": 361.9163082382877,
  "phase_incoherence_deg": 25.9
}
```

### Allowed images
- images/depth_map.png
- images/depth_map_viridis.png
- images/detected_lines.png
- images/initial_prompt_points.png
- images/segmentation_results.png
- images/sam_depth_input.png

### Parameter bounds (only these keys)
- `unfolding.ransac_threshold` (float): [0.8, 1.2]
- `unfolding.slice_spacing_factor` (float): [1.6, 2.0]
- `unfolding.polynomial_degree` (int): [2, 3]
- `unfolding.random_seed` (int): [0, 7]
- `denoising.mask_r_low` (float): [3.5, 3.8]
- `denoising.mask_r_high` (float): [3.75, 4.05]
- `enhancing.curvature_threshold` (float): [0.0002, 0.002]
- `detecting.binary_threshold` (int): [100, 160]
- `detecting.hough_threshold_oblique` (int): [25, 70]
- `detecting.hough_threshold_horizontal` (int): [25, 70]
- `detecting.hough_threshold_vertical` (int): [800, 5000]
- `detecting.maxLineGap_oblique` (int): [30, 80]
- `detecting.maxLineGap_horizontal` (int): [5, 30]
- `detecting.pattern_tolerance` (int): [5, 20]
- `sam.segment_width` (int): [1500, 2100]
- `sam.K_height` (float): [1000.0, 1500.0]
- `sam.angle` (float): [7.0, 12.0]

## Task

1. Inspect the images and intrinsics.
2. Diagnose a failure mode using the ontology / sanitized experiences.
3. Propose a coordinated overlay within bounds.
4. Return **only** a single JSON object (no markdown fences) with keys:
   `observation`, `failure_mode`, `rationale`, `overlay`

`overlay` shape example:
{"detecting": {"hough_threshold_oblique": 40}, "denoising": {"mask_r_low": 2.8}}

If stage1_unlocked is true and centreline residual is large, you may include
`unfolding` keys (e.g. random_seed). Otherwise do not touch unfolding.
