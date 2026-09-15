# GPT-5.6 Sol reflection — subset 4-1 (round proposal)

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

- subset: `4-1`
- family: `t4&5`
- stage1_unlocked: `False` (residual=2.4 cm)
- anchor_proxy_scaled: `0.6516` (band=refine)

### GT-blind intrinsics
```json
{}
```

### Lean proxy features
```json
{
  "depth_nan_ratio": 0.22330735765617338,
  "denoise_retained_ratio": 0.7583892868338517,
  "unfold_residual": 1.2237754316221157,
  "orient_agreement": 0.9398124965718192,
  "sam_fill_rate": 0.7488305972058229,
  "sam_ontology_divergence": 0.10154601537508416,
  "det_row_residual_px": 0.0,
  "det_row_gated": 0.0,
  "det_row_y_std": 500.5483095210783,
  "phase_incoherence_deg": 29.2
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
