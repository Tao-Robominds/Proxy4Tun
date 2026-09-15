# GPT-5.6 Sol reflection — subset 1-5 (round proposal)

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

- subset: `1-5`
- family: `t1&2`
- stage1_unlocked: `False` (residual=2.5 cm)
- anchor_proxy_scaled: `0.6745` (band=refine)

### GT-blind intrinsics
```json
{
  "orient_h_ring_corr": 0.985655524300288,
  "orient_invariant_ok": 1.0,
  "recentre_residual_max_cm": null,
  "denoise_retained_ratio": 0.7638200158043973,
  "depth_nan_ratio": 0.11774456253619453,
  "depth_outlier_ratio": 0.006866276013199325,
  "det_midpoint_ratio": 0.8,
  "det_real_detection_ratio": 0.8,
  "det_fallback_ratio": 0.2,
  "det_x_spacing_cv": 3.4512751936690116e-16,
  "det_y_std": 332.19236555239945,
  "det_ring_count_error": 0.0,
  "det_n_points": 10.0,
  "sam_fill_rate": 0.7294291823548552,
  "sam_ring_completeness": 0.8888888888888888,
  "sam_segment_size_cv": 1.303208521951268,
  "sam_ontology_divergence": 0.19335931650162724
}
```

### Lean proxy features
```json
{
  "depth_nan_ratio": 0.11774456253619453,
  "denoise_retained_ratio": 0.7638200158043973,
  "unfold_residual": 1.252762968495368,
  "orient_agreement": 0.9991614281123364,
  "sam_fill_rate": 0.7294291823548552,
  "sam_ontology_divergence": 0.19335931650162724,
  "det_row_residual_px": 0.0,
  "det_row_gated": 0.0,
  "det_row_y_std": 154.64367111801712,
  "phase_incoherence_deg": 20.6
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
- `denoising.mask_r_low` (float): [2.2, 2.5]
- `denoising.mask_r_high` (float): [2.7, 2.9]
- `denoising.z_step` (float): [0.001, 0.008]
- `denoising.grad_threshold` (float): [0.1, 0.25]
- `enhancing.curvature_threshold` (float): [0.0003, 0.008]
- `enhancing.inter_radius` (float): [0.02, 0.08]
- `detecting.binary_threshold` (int): [100, 160]
- `detecting.hough_threshold_oblique` (int): [40, 90]
- `detecting.hough_threshold_horizontal` (int): [40, 90]
- `detecting.hough_threshold_vertical` (int): [400, 800]
- `detecting.maxLineGap_oblique` (int): [20, 80]
- `sam.processing.y_bounds` (int): [3600, 4400]

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
