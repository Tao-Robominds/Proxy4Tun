# Reflection — subset 3-3, round 3 (Fable 5.1)

You are a reflective parameter agent for the SAM4Tun tunnel-lining pipeline.
Propose exactly ONE bounded multi-stage overlay to improve the frozen four-feature proxy.

## Isolation (hard rules)

- Read only this prompt, attached images, packet.json, feedback.json (if present), and the ontology YAML.
- Do NOT read evaluation/, performance.md, gt_*, mIoU, other arms, or selection files.
- Return exactly one overlay. Multiple proposals are invalid.

## Case

- Family: continuous
- Expected rings: 10
- Stage-1 unlocked: False (residual 2.70 cm; gate 10.0 cm)
- Incumbent score: 0.5578 (refine), source=round1
- Incumbent four measurements: {"correspondence_f1@15": 0.15268920015725135, "sam_fill_rate": 0.779964327151194, "ring_count_error": 0.0, "depth_nan_ratio": 0.11387375767737186}

## Parameter bounds

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

## Worked examples (development only; joint outcomes)

### Example 1: continuous-correspondencef1at15-improve-s019
- Condition: family=continuous, development subset 3-1, expected_rings=10, reference proxy=0.624
- Observed problem: Dominant concern correspondence_f1@15; measurements: correspondence_f1@15=0.3437, sam_fill_rate=0.6735, ring_count_error=0, depth_nan_ratio=0.1623
- Parameter changes: `{"unfolding": {"ransac_threshold": 1.107143509015441, "slice_spacing_factor": 1.1542314120568336, "polynomial_degree": 3, "random_seed": 0}, "denoising": {"mask_r_low": 2.818221717886627, "mask_r_high": 3.13379466147162, "mask_theta_low": 1.0313344611786306, "mask_theta_high": 16.31902088597417}, "enhancing": {"curvature_threshold": 0.0008843313163146376}, "detecting": {"binary_threshold": 118, "hough_threshold_oblique": 49, "hough_threshold_horizontal": 46, "hough_threshold_vertical": 2291, "maxLineGap_oblique": 53, "pattern_tolerance": 16, "uniform_k_snap": false}, "sam": {"segment_width": 1395, "K_height": 710.0875707343221, "angle": 8.39040036406368}}`
- Measured response (joint): proxy 0.624→0.509; correspondence_f1@15 0.3437→0.3025; sam_fill_rate 0.6735→0.4327; ring_count_error 0→0; depth_nan_ratio 0.1623→0.2241. Joint outcome of the full overlay; no per-parameter causal attribution.
- Applicability limits: Applies to continuous within configs/bounds/continuous.json; stage-1 locked on this reference; development scan only — not an evaluation subset.

### Example 2: continuous-correspondencef1at15-degrade-g005
- Condition: family=continuous, development subset 3-1, expected_rings=10, reference proxy=0.624
- Observed problem: Dominant concern correspondence_f1@15; measurements: correspondence_f1@15=0.3437, sam_fill_rate=0.6735, ring_count_error=0, depth_nan_ratio=0.1623
- Parameter changes: `{"unfolding": {"ransac_threshold": 1.0296846675091944, "slice_spacing_factor": 1.2594787760629067, "polynomial_degree": 3, "random_seed": 1}, "denoising": {"mask_r_low": 2.8911596294040742, "mask_r_high": 2.976694722284688, "mask_theta_low": 1.0823763855965738, "mask_theta_high": 15.544656845105369}, "enhancing": {"curvature_threshold": 0.0007102282768632207}, "detecting": {"binary_threshold": 150, "hough_threshold_oblique": 22, "hough_threshold_horizontal": 26, "hough_threshold_vertical": 822, "maxLineGap_oblique": 53, "pattern_tolerance": 19, "uniform_k_snap": true}, "sam": {"segment_width": 1043, "K_height": 998.7170069558166, "angle": 6.896375485980592}}`
- Measured response (joint): proxy 0.624→0.357; correspondence_f1@15 0.3437→0; sam_fill_rate 0.6735→0.4935; ring_count_error 0→0; depth_nan_ratio 0.1623→0.2136. Joint outcome of the full overlay; no per-parameter causal attribution.
- Applicability limits: Applies to continuous within configs/bounds/continuous.json; stage-1 locked on this reference; development scan only — not an evaluation subset.

### Example 3: continuous-samfillrate-improve-s000
- Condition: family=continuous, development subset 3-1, expected_rings=10, reference proxy=0.624
- Observed problem: Dominant concern sam_fill_rate; measurements: correspondence_f1@15=0.3437, sam_fill_rate=0.6735, ring_count_error=0, depth_nan_ratio=0.1623
- Parameter changes: `{"unfolding": {"ransac_threshold": 1.079762351885438, "slice_spacing_factor": 1.2104076792486014, "polynomial_degree": 2, "random_seed": 3}, "denoising": {"mask_r_low": 2.831238817702979, "mask_r_high": 3.022039988869801, "mask_theta_low": 1.4647601777687669, "mask_theta_high": 18.906503092497587}, "enhancing": {"curvature_threshold": 0.0008407603044062853}, "detecting": {"binary_threshold": 100, "hough_threshold_oblique": 58, "hough_threshold_horizontal": 41, "hough_threshold_vertical": 2066, "maxLineGap_oblique": 36, "pattern_tolerance": 14, "uniform_k_snap": true}, "sam": {"segment_width": 1042, "K_height": 839.9676816537976, "angle": 5.60974286030978}}`
- Measured response (joint): proxy 0.624→0.587; correspondence_f1@15 0.3437→0.3005; sam_fill_rate 0.6735→0.6571; ring_count_error 0→0; depth_nan_ratio 0.1623→0.1972. Joint outcome of the full overlay; no per-parameter causal attribution.
- Applicability limits: Applies to continuous within configs/bounds/continuous.json; stage-1 locked on this reference; development scan only — not an evaluation subset.

## Execution feedback from previous round (required reading)

- Previous round: 2
- Overlay applied: `{"detecting": {"binary_threshold": 100, "hough_threshold_oblique": 25, "maxLineGap_oblique": 60, "pattern_tolerance": 16}}`
- Verdict: rejected
- Score: 0.5578123030644832 → 0.5476130000498961
- Measurement deltas: {"correspondence_f1@15": -0.017184, "sam_fill_rate": -0.000977, "ring_count_error": 0.0, "depth_nan_ratio": 0.0}
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
