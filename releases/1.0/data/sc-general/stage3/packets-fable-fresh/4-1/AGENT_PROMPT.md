# Fable 5.1 reflection — subset 4-1 (propose round 3)

You are a reflective parameter agent for the SAM4Tun tunnel-lining pipeline.
Propose ONE bounded multi-stage overlay to improve the GT-free SC-general proxy.

## Isolation (hard rules)

Read ONLY:
- this prompt and the attached diagnostic images
- `context.json` in this packet directory
- ontology files listed under context.ontology (generic priors only)

Do NOT read or search for:
- `evaluation/`, `offline_gt.json`, `performance.md`, any mIoU / GT labels
- GT-bearing CSVs, holdout score tables with mIoU columns used as targets
- `data/sc-general/stage3/selections/`, `selections-fable/`, `selections-fable-fresh/`,
  `selections-gpt56/`, `selections-gemini38/`, `selections-random/`
- any other cases' proposals, or `data/refinement/` trees for any arm
- `data/bo/`, `data/anchors/`, `data/baseline`

## State

- subset: `4-1`
- family: `t4&5`
- lining_mode: `complex`
- stage1_unlocked: `False` (residual gate 10 cm)
- arm: `fable_fresh` / proposer: `Fable-5.1 (fresh per-case agent)`
- model: `claude-fable-5-1-thinking-high`

### Anchor (GT-blind)
```json
{
  "proxy_raw": 0.551819,
  "proxy_scaled": 0.551819,
  "band": "refine",
  "features": {
    "correspondence_f1@15": 0.225171,
    "sam_fill_rate": 0.748831,
    "ring_count_error": 0.0,
    "depth_nan_ratio": 0.223307
  },
  "recentre_residual_max_cm": 2.4,
  "orient_axis_corr": 0.9398124965718192,
  "ring_count": 10,
  "ring_count_error": 0.0,
  "labelmap_source": "only_label.csv",
  "run_dir": "/home/boringtao/Projects/Proxy4Tun/data/bo/unified/4-1-family-proxy/runs/4-1-anchor"
}
```

### Intrinsics (GT-blind)
```json
{
  "orient_axis_corr": 0.9398124965718192,
  "orient_invariant_ok": 1.0,
  "recentre_residual_max_cm": 2.4,
  "denoise_retained_ratio": 0.7583892868338517,
  "depth_nan_ratio": 0.22330735765617338,
  "depth_outlier_ratio": 0.0010889418251959948,
  "det_real_detection_ratio": 0.4,
  "det_fallback_ratio": 0.6,
  "det_n_points": 10.0,
  "sam_fill_rate": 0.7488305972058229,
  "sam_ring_completeness": 1.0,
  "sam_segment_size_cv": 1.0601700064349866,
  "sam_ontology_divergence": 0.10154601537508416
}
```

### Prior rounds (this arm only)
```json
[
  {
    "round": 1,
    "status": "ok",
    "overlay": {
      "detecting": {
        "binary_threshold": 110,
        "hough_threshold_oblique": 35,
        "maxLineGap_oblique": 70,
        "hough_threshold_horizontal": 40,
        "pattern_tolerance": 15
      }
    },
    "proxy_scaled": 0.5452959284080028,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.2127022364539851,
      "sam_fill_rate": 0.7498783735648481,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.22328257687193515
    },
    "recentre_residual_max_cm": 2.4,
    "full_pipeline": false,
    "rationale": "Coordinated detection-only overlay. binary_threshold 127->110 lets fainter joint pixels through binarisation before dilation. hough_threshold_oblique 50->35 and maxLineGap_oblique 50->70 accept the broken oblique joint traces as single lines. hough_threshold_horizontal 50->40 keeps the horizontal fallback reliable where oblique still fails. pattern_tolerance raised to 15 px so real intersections that are a few pixels off the K/AB pattern are kept instead of replaced by 'assume' points. hough_threshold_vertical is left untouched because the vertical count already equals ring_count (10/10). Denoising, enhancing and SAM keys are left at anchor values to attribute any proxy delta to detection; SAM geometry will be revisited in later rounds only if per-block coherence (fill rate, size CV) is the remaining weak feature.",
    "proposer": "Fable-5.1 (fresh per-case agent)"
  },
  {
    "round": 2,
    "status": "ok",
    "overlay": {
      "detecting": {
        "binary_threshold": 100,
        "hough_threshold_oblique": 35,
        "maxLineGap_oblique": 70,
        "hough_threshold_horizontal": 30,
        "maxLineGap_horizontal": 25,
        "pattern_tolerance": 20
      }
    },
    "proxy_scaled": 0.5502988864501946,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.22185882235125973,
      "sam_fill_rate": 0.7498783735648481,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.22328257687193515
    },
    "recentre_residual_max_cm": 2.4,
    "full_pipeline": false,
    "rationale": "Coordinated detection overlay that targets the correspondence ceiling directly. binary_threshold 110 -> 100 (lower bound) admits the faintest dotted seam pixels into the binarised outlier map before the 3x3 dilation, which is what the horizontal Hough needs to see a continuous trace. hough_threshold_horizontal 40 -> 30 and maxLineGap_horizontal 10 -> 25 let HoughLinesP bridge the 10-40 px gaps in dotted seam traces at the fixed minLineLength (105 px) so that many more of the ~70 real seams become detected joint lines; the 30 px gap bound is well below the ~100 px chevron spacing, so bolt rows are not joined into false horizontals. Oblique parameters are held at the round-1 values (35 / 70) because further relaxation produced a spurious cross-ring line without raising correspondence. pattern_tolerance 15 -> 20 (bound) so real intersections that are within 20 px of the K/AB spacing (K 245 px, AB 745 px at 5 mm/px) are kept as prompt centres instead of being replaced by alternating 'assume' points. hough_threshold_vertical untouched: 10 verticals == 10 rings. Denoising, enhancing and SAM keys are left at anchor values; SAM geometry (segment_width 1800 mm matches the observed ~362 px ring pitch) is reserved for round 3 only if per-block coherence remains the weak feature after line yield is fixed. Expected GT-free signal: more cyan (explained) joint lines and more green (supported) boundaries in the SC overlay, correspondence_f1@15 up, sam_fill_rate and ring_count_error unchanged.",
    "proposer": "Fable-5.1 (fresh per-case agent)"
  },
  {
    "round": 3,
    "status": "ok",
    "overlay": {
      "detecting": {
        "binary_threshold": 100,
        "hough_threshold_oblique": 25,
        "maxLineGap_oblique": 80,
        "hough_threshold_horizontal": 30,
        "maxLineGap_horizontal": 25,
        "pattern_tolerance": 20
      }
    },
    "proxy_scaled": 0.5563469957354461,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.23292828000400617,
      "sam_fill_rate": 0.7498783735648481,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.22328257687193515
    },
    "recentre_residual_max_cm": 2.4,
    "full_pipeline": false,
    "rationale": "Detection overlay that converts 'assume' rings into real prompts. hough_threshold_oblique 35 -> 25 (bound) and maxLineGap_oblique 70 -> 80 (bound): the tapered K-block edges are ~360 px long at 5-10 deg but appear as dotted traces in the binarised outlier map; at the fixed minLineLength the lower accumulator threshold lets faint left-half traces register and the larger gap bridges the breaks so each K edge becomes ONE segment that reaches the ring-centre vertical, which is the geometric requirement for line_segment_vertical_intersection to fire. A K edge found on either side yields a positive_slope / negative_slope centre; both sides yield a midpoint, which is exactly the prompt type that produced supported boundaries in rings 2340/2700/3060. binary_threshold 100, hough_threshold_horizontal 30, maxLineGap_horizontal 25 and pattern_tolerance 20 are carried over from round 2 (the horizontal seam traces are what the SC overlay needs to explain label boundaries, and the 20 px tolerance is what accepts real intersections into the K/AB pattern). hough_threshold_vertical untouched: 10 verticals == 10 rings. SAM segment_width / K_height / angle stay at prior because the detected seam spacing (745 px AB, ~250 px K, 360 px ring pitch) confirms them; changing them would fit noise. Denoising mask_r and enhancing curvature_threshold stay at anchor so the proxy delta is attributable to prompt-centre quality. Expected GT-free signal: det_real_detection_ratio rises above 0.5 (fewer green 'assume' diamonds in initial_prompt_points, more stars / triangles in the left half), more green supported boundaries in the left-half rings of the SC overlay, correspondence_f1@15 up from 0.222, sam_segment_size_cv down, sam_fill_rate / ring_count_error / depth_nan_ratio unchanged. If det_real_detection_ratio does not rise, the left-half joints are below what stage-4 binarisation can recover and the remaining lever is the out-of-bounds enhancing depth_threshold (r_lower_depth_threshold), not further Hough or SAM tuning.",
    "proposer": "Fable-5.1 (fresh per-case agent)"
  }
]
```

### Parameter bounds (ONLY these keys; reject anything else)
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

## Required output

Write a single JSON object to:
`/home/boringtao/Projects/Proxy4Tun/data/sc-general/stage3/packets-fable-fresh/4-1/round3_proposal.json`

Schema:
```json
{
  "observation": "...",
  "rule": "...",
  "failure_mode": "...",
  "rationale": "...",
  "overlay": { "denoising": {}, "enhancing": {}, "detecting": {}, "sam": {} },
  "full": false
}
```

Use observation → rule → failure_mode → overlay. Stay inside bounds. If
stage1_unlocked is false, omit unfolding. Do not invent dead knobs.
