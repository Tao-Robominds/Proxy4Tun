# Reflection — subset 3-9, round 3 (Gemini 3.8)

You are a reflective parameter agent for the SAM4Tun tunnel-lining pipeline.
Propose exactly ONE bounded multi-stage overlay to improve the frozen four-feature proxy.

## Isolation (hard rules)

- Read only this prompt, attached images, packet.json, feedback.json (if present), and the ontology YAML.
- Do NOT read evaluation/, performance.md, gt_*, mIoU, other arms, or selection files.
- Return exactly one overlay. Multiple proposals are invalid.

## Case

- Family: continuous
- Expected rings: 10
- Stage-1 unlocked: False (residual 2.80 cm; gate 10.0 cm)
- Incumbent score: 0.6592 (refine), source=start
- Incumbent four measurements: {"correspondence_f1@15": 0.36367764129925506, "sam_fill_rate": 0.7289890931960742, "ring_count_error": 0.0, "depth_nan_ratio": 0.13082197231971604}

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

### Example 1: continuous-ringcounterror-improve-g003
- Condition: family=continuous, development subset 3-1, expected_rings=10, reference proxy=0.624
- Observed problem: Dominant concern ring_count_error; measurements: correspondence_f1@15=0.3437, sam_fill_rate=0.6735, ring_count_error=0, depth_nan_ratio=0.1623
- Parameter changes: `{"unfolding": {"ransac_threshold": 1.17566673447332, "slice_spacing_factor": 1.2237711390855832, "polynomial_degree": 3, "random_seed": 6}, "denoising": {"mask_r_low": 2.816899026090796, "mask_r_high": 3.099836427710328, "mask_theta_low": 2.461479864497342, "mask_theta_high": 17.444843677019314}, "enhancing": {"curvature_threshold": 0.001707429781503714}, "detecting": {"binary_threshold": 145, "hough_threshold_oblique": 58, "hough_threshold_horizontal": 27, "hough_threshold_vertical": 997, "maxLineGap_oblique": 35, "pattern_tolerance": 5, "uniform_k_snap": true}, "sam": {"segment_width": 1361, "K_height": 772.7284454397203, "angle": 5.47029829595881}}`
- Measured response (joint): proxy 0.624→0.480; correspondence_f1@15 0.3437→0.2769; sam_fill_rate 0.6735→0.3973; ring_count_error 0→0; depth_nan_ratio 0.1623→0.2378. Joint outcome of the full overlay; no per-parameter causal attribution.
- Applicability limits: Applies to continuous within configs/bounds/continuous.json; stage-1 locked on this reference; development scan only — not an evaluation subset.

### Example 2: continuous-ringcounterror-degrade-g000
- Condition: family=continuous, development subset 3-1, expected_rings=10, reference proxy=0.624
- Observed problem: Dominant concern ring_count_error; measurements: correspondence_f1@15=0.3437, sam_fill_rate=0.6735, ring_count_error=0, depth_nan_ratio=0.1623
- Parameter changes: `{"unfolding": {"ransac_threshold": 1.0894961134153907, "slice_spacing_factor": 1.2922607061537947, "polynomial_degree": 2, "random_seed": 5}, "denoising": {"mask_r_low": 2.747200962481015, "mask_r_high": 2.964603735667865, "mask_theta_low": 2.265163713510307, "mask_theta_high": 18.463370613295105}, "enhancing": {"curvature_threshold": 0.0005056758948359012}, "detecting": {"binary_threshold": 138, "hough_threshold_oblique": 52, "hough_threshold_horizontal": 30, "hough_threshold_vertical": 2081, "maxLineGap_oblique": 43, "pattern_tolerance": 8, "uniform_k_snap": false}, "sam": {"segment_width": 1160, "K_height": 739.0200893080571, "angle": 7.906067618143172}}`
- Measured response (joint): proxy 0.624→0.209; correspondence_f1@15 0.3437→0.09859; sam_fill_rate 0.6735→0.29; ring_count_error 0→1; depth_nan_ratio 0.1623→0.5403. Joint outcome of the full overlay; no per-parameter causal attribution.
- Applicability limits: Applies to continuous within configs/bounds/continuous.json; stage-1 locked on this reference; development scan only — not an evaluation subset.

### Example 3: continuous-correspondencef1at15-improve-s019
- Condition: family=continuous, development subset 3-1, expected_rings=10, reference proxy=0.624
- Observed problem: Dominant concern correspondence_f1@15; measurements: correspondence_f1@15=0.3437, sam_fill_rate=0.6735, ring_count_error=0, depth_nan_ratio=0.1623
- Parameter changes: `{"unfolding": {"ransac_threshold": 1.107143509015441, "slice_spacing_factor": 1.1542314120568336, "polynomial_degree": 3, "random_seed": 0}, "denoising": {"mask_r_low": 2.818221717886627, "mask_r_high": 3.13379466147162, "mask_theta_low": 1.0313344611786306, "mask_theta_high": 16.31902088597417}, "enhancing": {"curvature_threshold": 0.0008843313163146376}, "detecting": {"binary_threshold": 118, "hough_threshold_oblique": 49, "hough_threshold_horizontal": 46, "hough_threshold_vertical": 2291, "maxLineGap_oblique": 53, "pattern_tolerance": 16, "uniform_k_snap": false}, "sam": {"segment_width": 1395, "K_height": 710.0875707343221, "angle": 8.39040036406368}}`
- Measured response (joint): proxy 0.624→0.509; correspondence_f1@15 0.3437→0.3025; sam_fill_rate 0.6735→0.4327; ring_count_error 0→0; depth_nan_ratio 0.1623→0.2241. Joint outcome of the full overlay; no per-parameter causal attribution.
- Applicability limits: Applies to continuous within configs/bounds/continuous.json; stage-1 locked on this reference; development scan only — not an evaluation subset.

## Execution feedback from previous round (required reading)

- Previous round: 2
- Overlay applied: `{"enhancing": {"curvature_threshold": 0.0008}, "detecting": {"binary_threshold": 136, "hough_threshold_oblique": 36, "hough_threshold_horizontal": 50}}`
- Verdict: rejected
- Score: 0.6591558534408575 → 0.653929080377693
- Measurement deltas: {"correspondence_f1@15": -0.009903, "sam_fill_rate": -0.001088, "ring_count_error": 0.0, "depth_nan_ratio": -0.00459}
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
