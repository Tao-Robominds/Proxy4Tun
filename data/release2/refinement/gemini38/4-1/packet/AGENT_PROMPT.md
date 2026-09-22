# Reflection — subset 4-1, round 3 (Gemini 3.8)

You are a reflective parameter agent for the SAM4Tun tunnel-lining pipeline.
Propose exactly ONE bounded multi-stage overlay to improve the frozen four-feature proxy.

## Isolation (hard rules)

- Read only this prompt, attached images, packet.json, feedback.json (if present), and the ontology YAML.
- Do NOT read evaluation/, performance.md, gt_*, mIoU, other arms, or selection files.
- Return exactly one overlay. Multiple proposals are invalid.

## Case

- Family: complex
- Expected rings: 10
- Stage-1 unlocked: True (residual 13.50 cm; gate 10.0 cm)
- Incumbent score: 0.6504 (refine), source=start
- Incumbent four measurements: {"correspondence_f1@15": 0.36527770315648833, "sam_fill_rate": 0.7516065103119458, "ring_count_error": 0.0, "depth_nan_ratio": 0.22606519178835907}

## Parameter bounds

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

## Worked examples (development only; joint outcomes)

### Example 1: complex-depthnanratio-improve-s005
- Condition: family=complex, development subset 5-1, expected_rings=10, reference proxy=0.700
- Observed problem: Dominant concern depth_nan_ratio; measurements: correspondence_f1@15=0.4462, sam_fill_rate=0.7524, ring_count_error=0, depth_nan_ratio=0.2084
- Parameter changes: `{"unfolding": {"ransac_threshold": 0.9964667443186045, "slice_spacing_factor": 1.9663509022444488, "polynomial_degree": 3, "random_seed": 6}, "denoising": {"mask_r_low": 3.5142921728082, "mask_r_high": 4.012441172730178}, "enhancing": {"curvature_threshold": 0.0019850904366001485}, "detecting": {"binary_threshold": 150, "hough_threshold_oblique": 44, "hough_threshold_horizontal": 70, "hough_threshold_vertical": 4133, "maxLineGap_oblique": 64, "maxLineGap_horizontal": 12, "pattern_tolerance": 13}, "sam": {"segment_width": 1969, "K_height": 1094.3226064555347, "angle": 7.12304752599448}}`
- Measured response (joint): proxy 0.700→0.481; correspondence_f1@15 0.4462→0.194; sam_fill_rate 0.7524→0.7524; ring_count_error 0→1; depth_nan_ratio 0.2084→0.184. Joint outcome of the full overlay; no per-parameter causal attribution.
- Applicability limits: Applies to complex within configs/bounds/complex.json; stage-1 unlocked on this reference; development scan only — not an evaluation subset.

### Example 2: complex-depthnanratio-degrade-s016
- Condition: family=complex, development subset 5-1, expected_rings=10, reference proxy=0.700
- Observed problem: Dominant concern depth_nan_ratio; measurements: correspondence_f1@15=0.4462, sam_fill_rate=0.7524, ring_count_error=0, depth_nan_ratio=0.2084
- Parameter changes: `{"unfolding": {"ransac_threshold": 1.077580063045025, "slice_spacing_factor": 1.715012985095382, "polynomial_degree": 3, "random_seed": 3}, "denoising": {"mask_r_low": 3.795598308369517, "mask_r_high": 3.966197416651994}, "enhancing": {"curvature_threshold": 0.0011984110618010165}, "detecting": {"binary_threshold": 109, "hough_threshold_oblique": 45, "hough_threshold_horizontal": 68, "hough_threshold_vertical": 3654, "maxLineGap_oblique": 53, "maxLineGap_horizontal": 9, "pattern_tolerance": 12}, "sam": {"segment_width": 1610, "K_height": 1147.9954258538783, "angle": 8.085971118882298}}`
- Measured response (joint): proxy 0.700→0.000; correspondence_f1@15 0.4462→0; sam_fill_rate 0.7524→0.007367; ring_count_error 0→1; depth_nan_ratio 0.2084→0.9831. Joint outcome of the full overlay; no per-parameter causal attribution.
- Applicability limits: Applies to complex within configs/bounds/complex.json; stage-1 unlocked on this reference; development scan only — not an evaluation subset.

### Example 3: complex-correspondencef1at15-improve-s021
- Condition: family=complex, development subset 5-1, expected_rings=10, reference proxy=0.700
- Observed problem: Dominant concern correspondence_f1@15; measurements: correspondence_f1@15=0.4462, sam_fill_rate=0.7524, ring_count_error=0, depth_nan_ratio=0.2084
- Parameter changes: `{"unfolding": {"ransac_threshold": 0.9714595459401607, "slice_spacing_factor": 1.8489205356687308, "polynomial_degree": 3, "random_seed": 0}, "denoising": {"mask_r_low": 3.6008071053773163, "mask_r_high": 3.794932061433792}, "enhancing": {"curvature_threshold": 0.00036597516089677815}, "detecting": {"binary_threshold": 127, "hough_threshold_oblique": 27, "hough_threshold_horizontal": 60, "hough_threshold_vertical": 4306, "maxLineGap_oblique": 74, "maxLineGap_horizontal": 28, "pattern_tolerance": 11}, "sam": {"segment_width": 1874, "K_height": 1120.300923474133, "angle": 11.78815640322864}}`
- Measured response (joint): proxy 0.700→0.708; correspondence_f1@15 0.4462→0.4596; sam_fill_rate 0.7524→0.7457; ring_count_error 0→0; depth_nan_ratio 0.2084→0.1968. Joint outcome of the full overlay; no per-parameter causal attribution.
- Applicability limits: Applies to complex within configs/bounds/complex.json; stage-1 unlocked on this reference; development scan only — not an evaluation subset.

## Execution feedback from previous round (required reading)

- Previous round: 2
- Overlay applied: `{"sam": {"angle": 11.79}}`
- Verdict: rejected
- Score: 0.6504471704561834 → 0.6504471704561834
- Measurement deltas: {"correspondence_f1@15": 0.0, "sam_fill_rate": 0.0, "ring_count_error": 0.0, "depth_nan_ratio": 0.0}
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
