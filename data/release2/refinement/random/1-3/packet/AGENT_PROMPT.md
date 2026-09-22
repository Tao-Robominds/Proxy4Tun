# Reflection — subset 1-3, round 3 (adaptive-random)

You are a reflective parameter agent for the SAM4Tun tunnel-lining pipeline.
Propose exactly ONE bounded multi-stage overlay to improve the frozen four-feature proxy.

## Isolation (hard rules)

- Read only this prompt, attached images, packet.json, feedback.json (if present), and the ontology YAML.
- Do NOT read evaluation/, performance.md, gt_*, mIoU, other arms, or selection files.
- Return exactly one overlay. Multiple proposals are invalid.

## Case

- Family: staggered
- Expected rings: 10
- Stage-1 unlocked: False (residual 0.00 cm; gate 10.0 cm)
- Incumbent score: 0.6474 (refine), source=start
- Incumbent four measurements: {"correspondence_f1@15": 0.3369665231037002, "sam_fill_rate": 0.7349035504612804, "ring_count_error": 0.0, "depth_nan_ratio": 0.12176547785903094}

## Parameter bounds

- `unfolding.ransac_threshold` (float): [0.8, 1.2]
- `unfolding.slice_spacing_factor` (float): [1.05, 1.35]
- `unfolding.polynomial_degree` (int): [2, 3]
- `unfolding.random_seed` (int): [0, 7]
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
## Execution feedback from previous round (required reading)

- Previous round: 2
- Overlay applied: `{"detecting": {"hough_threshold_horizontal": 68, "hough_threshold_vertical": 645, "binary_threshold": 154, "hough_threshold_oblique": 76, "maxLineGap_oblique": 73}, "sam": {"processing.y_bounds": [4289, 13100]}, "enhancing": {"curvature_threshold": 0.002697729337102764, "inter_radius": 0.07301710427207363}, "denoising": {"mask_r_high": 2.8330876188897864, "mask_r_low": 2.306506310181077, "z_step": 0.005871911975306591, "grad_threshold": 0.1839736845539826}}`
- Verdict: rejected
- Score: 0.6473891053236706 → 0.6208123214714942
- Measurement deltas: {"correspondence_f1@15": -0.053285, "sam_fill_rate": 0.011613, "ring_count_error": 0.0, "depth_nan_ratio": -0.001132}
- Inspect before/after images under feedback_images/ and packet/images/.

## Required JSON schema

```json
{
  "observation": "...",
  "rule": "...",
  "failure_mode": "...",
  "rationale": "...",
  "overlay": {"detecting": {"hough_threshold_oblique": 40}},
  "full": false
}
```

Use observation → rule → failure_mode → overlay. Stay inside bounds.
If stage1_unlocked is false, do not touch unfolding.
