# Reflection — subset 4-2, round 3 (Fable 5.1)

You are a reflective parameter agent for the SAM4Tun tunnel-lining pipeline.
Propose exactly ONE bounded multi-stage overlay to improve the frozen four-feature proxy.

## Isolation (hard rules)

- Read only this prompt, attached images, packet.json, feedback.json (if present), and the ontology YAML.
- Do NOT read evaluation/, performance.md, gt_*, mIoU, other arms, or selection files.
- Return exactly one overlay. Multiple proposals are invalid.

## Case

- Family: complex
- Expected rings: 10
- Stage-1 unlocked: False (residual 1.90 cm; gate 10.0 cm)
- Incumbent score: 0.7187 (accept), source=round1
- Incumbent four measurements: {"correspondence_f1@15": 0.49168118133685346, "sam_fill_rate": 0.7293530342193588, "ring_count_error": 0.0, "depth_nan_ratio": 0.209318279915068}

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

### Example 1: complex-samfillrate-improve-s028
- Condition: family=complex, development subset 5-1, expected_rings=10, reference proxy=0.700
- Observed problem: Dominant concern sam_fill_rate; measurements: correspondence_f1@15=0.4462, sam_fill_rate=0.7524, ring_count_error=0, depth_nan_ratio=0.2084
- Parameter changes: `{"unfolding": {"ransac_threshold": 1.1896771639585495, "slice_spacing_factor": 1.7718921441584825, "polynomial_degree": 3, "random_seed": 4}, "denoising": {"mask_r_low": 3.5849630857817827, "mask_r_high": 4.0397284020669755}, "enhancing": {"curvature_threshold": 0.0013000535065308214}, "detecting": {"binary_threshold": 113, "hough_threshold_oblique": 42, "hough_threshold_horizontal": 26, "hough_threshold_vertical": 4532, "maxLineGap_oblique": 35, "maxLineGap_horizontal": 23, "pattern_tolerance": 8}, "sam": {"segment_width": 1952, "K_height": 1164.699537679553, "angle": 10.322905539534986}}`
- Measured response (joint): proxy 0.700→0.654; correspondence_f1@15 0.4462→0.3652; sam_fill_rate 0.7524→0.7586; ring_count_error 0→0; depth_nan_ratio 0.2084→0.2192. Joint outcome of the full overlay; no per-parameter causal attribution.
- Applicability limits: Applies to complex within configs/bounds/complex.json; stage-1 unlocked on this reference; development scan only — not an evaluation subset.

### Example 2: complex-samfillrate-degrade-g007
- Condition: family=complex, development subset 5-1, expected_rings=10, reference proxy=0.700
- Observed problem: Dominant concern sam_fill_rate; measurements: correspondence_f1@15=0.4462, sam_fill_rate=0.7524, ring_count_error=0, depth_nan_ratio=0.2084
- Parameter changes: `{"unfolding": {"ransac_threshold": 0.9576979331345302, "slice_spacing_factor": 1.6102269297642489, "polynomial_degree": 3, "random_seed": 1}, "denoising": {"mask_r_low": 3.7986340197350836, "mask_r_high": 4.045975097550956}, "enhancing": {"curvature_threshold": 0.0007228470662847283}, "detecting": {"binary_threshold": 155, "hough_threshold_oblique": 51, "hough_threshold_horizontal": 53, "hough_threshold_vertical": 4872, "maxLineGap_oblique": 32, "maxLineGap_horizontal": 22, "pattern_tolerance": 13}, "sam": {"segment_width": 1625, "K_height": 1489.9337782046296, "angle": 10.154370042682586}}`
- Measured response (joint): proxy 0.700→0.000; correspondence_f1@15 0.4462→0; sam_fill_rate 0.7524→0.006653; ring_count_error 0→1; depth_nan_ratio 0.2084→0.9825. Joint outcome of the full overlay; no per-parameter causal attribution.
- Applicability limits: Applies to complex within configs/bounds/complex.json; stage-1 unlocked on this reference; development scan only — not an evaluation subset.

### Example 3: complex-correspondencef1at15-improve-s021
- Condition: family=complex, development subset 5-1, expected_rings=10, reference proxy=0.700
- Observed problem: Dominant concern correspondence_f1@15; measurements: correspondence_f1@15=0.4462, sam_fill_rate=0.7524, ring_count_error=0, depth_nan_ratio=0.2084
- Parameter changes: `{"unfolding": {"ransac_threshold": 0.9714595459401607, "slice_spacing_factor": 1.8489205356687308, "polynomial_degree": 3, "random_seed": 0}, "denoising": {"mask_r_low": 3.6008071053773163, "mask_r_high": 3.794932061433792}, "enhancing": {"curvature_threshold": 0.00036597516089677815}, "detecting": {"binary_threshold": 127, "hough_threshold_oblique": 27, "hough_threshold_horizontal": 60, "hough_threshold_vertical": 4306, "maxLineGap_oblique": 74, "maxLineGap_horizontal": 28, "pattern_tolerance": 11}, "sam": {"segment_width": 1874, "K_height": 1120.300923474133, "angle": 11.78815640322864}}`
- Measured response (joint): proxy 0.700→0.708; correspondence_f1@15 0.4462→0.4596; sam_fill_rate 0.7524→0.7457; ring_count_error 0→0; depth_nan_ratio 0.2084→0.1968. Joint outcome of the full overlay; no per-parameter causal attribution.
- Applicability limits: Applies to complex within configs/bounds/complex.json; stage-1 unlocked on this reference; development scan only — not an evaluation subset.

## Execution feedback from previous round (required reading)

- Previous round: 2
- Overlay applied: `{"denoising": {"mask_r_low": 3.6, "mask_r_high": 3.85}, "enhancing": {"curvature_threshold": 0.0004}, "detecting": {"binary_threshold": 110, "hough_threshold_oblique": 25, "hough_threshold_horizontal": 65, "hough_threshold_vertical": 4300, "maxLineGap_oblique": 80, "maxLineGap_horizontal": 28, "pattern_tolerance": 14}, "sam": {"segment_width": 1900, "K_height": 1140.0, "angle": 11.8}}`
- Verdict: rejected
- Score: 0.7187375177901674 → 0.7110957924515351
- Measurement deltas: {"correspondence_f1@15": -0.013504, "sam_fill_rate": 0.000361, "ring_count_error": 0.0, "depth_nan_ratio": 0.0}
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
