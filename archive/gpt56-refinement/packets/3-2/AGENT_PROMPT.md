# GPT-5.6 Sol reflection — subset 3-2 (round proposal)

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

- subset: `3-2`
- family: `t3`
- stage1_unlocked: `True` (residual=16.8 cm)
- anchor_proxy_scaled: `0.5999` (band=refine)

### GT-blind intrinsics
```json
{
  "orient_h_ring_corr": -0.9956222226110221,
  "orient_invariant_ok": 1.0,
  "recentre_residual_max_cm": 16.8,
  "denoise_retained_ratio": 0.823253345584304,
  "depth_nan_ratio": 0.15886482349763578,
  "depth_outlier_ratio": 0.0006226809803916667,
  "det_midpoint_ratio": 0.0,
  "det_real_detection_ratio": 0.0,
  "det_fallback_ratio": 1.0,
  "det_x_spacing_cv": 0.0,
  "det_y_std": 0.0,
  "det_ring_count_error": 0.0,
  "det_n_points": 10.0,
  "sam_fill_rate": 0.6768357643853194,
  "sam_ring_completeness": 0.8888888888888888,
  "sam_segment_size_cv": 0.7106115297981687,
  "sam_ontology_divergence": 0.23302359873375506
}
```

### Lean proxy features
```json
{
  "depth_nan_ratio": 0.15886482349763578,
  "denoise_retained_ratio": 0.823253345584304,
  "unfold_residual": 2.8791984572980396,
  "orient_agreement": 0.999817082148587,
  "sam_fill_rate": 0.6768357643853194,
  "sam_ontology_divergence": 0.23302359873375506,
  "det_row_residual_px": 3.5299247761787234,
  "det_row_gated": 1.0,
  "det_row_y_std": 1.7662757987279532,
  "phase_incoherence_deg": 3.2
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
- `unfolding.slice_spacing_factor` (float): [1.05, 1.35]
- `unfolding.polynomial_degree` (int): [2, 3]
- `unfolding.random_seed` (int): [0, 7]
- `denoising.mask_r_low` (float): [2.7, 3.0]
- `denoising.mask_r_high` (float): [2.9, 3.15]
- `denoising.mask_theta_low` (float): [1.0, 2.5]
- `denoising.mask_theta_high` (float): [15.0, 19.0]
- `enhancing.curvature_threshold` (float): [0.0002, 0.002]
- `detecting.binary_threshold` (int): [100, 160]
- `detecting.hough_threshold_oblique` (int): [20, 60]
- `detecting.hough_threshold_horizontal` (int): [20, 60]
- `detecting.hough_threshold_vertical` (int): [800, 2500]
- `detecting.maxLineGap_oblique` (int): [10, 60]
- `detecting.pattern_tolerance` (int): [5, 20]
- `detecting.uniform_k_snap` (bool): [0.0, 1.0]
- `sam.segment_width` (int): [1000, 1400]
- `sam.K_height` (float): [700.0, 1000.0]
- `sam.angle` (float): [4.0, 9.0]

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
