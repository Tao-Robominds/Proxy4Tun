# Fable 5.1 reflection — subset 5-4 (propose round 3)

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

- subset: `5-4`
- family: `t4&5`
- lining_mode: `complex`
- stage1_unlocked: `False` (residual gate 10 cm)
- arm: `fable_fresh` / proposer: `Fable-5.1 (fresh per-case agent)`
- model: `claude-fable-5-1-thinking-high`

### Anchor (GT-blind)
```json
{
  "proxy_raw": 0.692326,
  "proxy_scaled": 0.692326,
  "band": "refine",
  "features": {
    "correspondence_f1@15": 0.467401,
    "sam_fill_rate": 0.759939,
    "ring_count_error": 0.0,
    "depth_nan_ratio": 0.19849
  },
  "recentre_residual_max_cm": 2.1,
  "orient_axis_corr": -0.7738736413768053,
  "ring_count": 10,
  "ring_count_error": 0.0,
  "labelmap_source": "only_label.csv",
  "run_dir": "/home/boringtao/Projects/Proxy4Tun/data/bo/unified/5-4-family-proxy/runs/5-4-anchor"
}
```

### Intrinsics (GT-blind)
```json
{
  "orient_axis_corr": -0.7738736413768053,
  "orient_invariant_ok": 1.0,
  "recentre_residual_max_cm": 2.1,
  "denoise_retained_ratio": 0.771714565621628,
  "depth_nan_ratio": 0.19848996720212705,
  "depth_outlier_ratio": 0.00134290457193032,
  "det_real_detection_ratio": 0.7,
  "det_fallback_ratio": 0.3,
  "det_n_points": 10.0,
  "sam_fill_rate": 0.7599389968796842,
  "sam_ring_completeness": 1.0,
  "sam_segment_size_cv": 1.1070596715680279,
  "sam_ontology_divergence": 0.14195278326436073
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
        "maxLineGap_oblique": 65,
        "pattern_tolerance": 15
      }
    },
    "proxy_scaled": 0.6924116195581295,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.46755743575458175,
      "sam_fill_rate": 0.7599389968796842,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.19848996720212705
    },
    "recentre_residual_max_cm": 2.1,
    "full_pipeline": false,
    "rationale": "Anchor proxy 0.692 sits just under the accept band (>=0.7); the lean feature that is far from healthy is correspondence_f1@15 (0.467), which is driven by prompt-centre placement, not by coverage. Keep the healthy stages frozen (no unfolding since stage1 is locked; denoising and enhancing left at anchor values so NaN/retention are unchanged and attribution stays clean) and make one coordinated detection move: lower binary_threshold 127->110 so the faint dotted joint pixels survive binarisation, lower hough_threshold_oblique to 35 and raise maxLineGap_oblique to 65 so the dotted tapered joints link into oblique segments instead of falling through to horizontal fallback, and set pattern_tolerance to 15 px so genuine K/AB-pattern intersections are accepted over midpoint/assume fallbacks. Verticals are left alone because 10 lines already equal the ring count. Expected signature: det_real_detection_ratio up from 0.7 toward 1.0, fewer 'assume'/'midpoint' prompts, correspondence_f1@15 up, sam_segment_size_cv down, with depth_nan_ratio and ring_count_error unchanged. If oblique yield rises but boundaries still miss, round 2 should turn to SAM geometry (K_height / angle).",
    "proposer": "Fable-5.1 (fresh per-case agent)"
  },
  {
    "round": 2,
    "status": "ok",
    "overlay": {
      "detecting": {
        "binary_threshold": 100,
        "hough_threshold_oblique": 25,
        "maxLineGap_oblique": 80,
        "pattern_tolerance": 20
      }
    },
    "proxy_scaled": 0.6725740030729044,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.4312499477020581,
      "sam_fill_rate": 0.7599389968796842,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.19848996720212705
    },
    "recentre_residual_max_cm": 2.1,
    "full_pipeline": false,
    "rationale": "Round 1 proved the direction (more oblique lines, no side effects on evidence features) but at 35/65/110/15 the effect was confined to rings that were already detected, so the prompt set and the proxy did not move. Round 2 completes the same move at the admissible extremes, keeping all other stages frozen for clean attribution: binary_threshold 110 -> 100 (bound min) so the faintest dotted joint pixels in the sparse outer rings survive binarisation and get bridged by the 3x3 dilation; hough_threshold_oblique 35 -> 25 (bound min) and maxLineGap_oblique 65 -> 80 (bound max) so 30-80 px dotted runs accumulate into [5,10]-degree segments instead of dropping to horizontal fallback; pattern_tolerance 15 -> 20 px (bound max, 100 mm, ~8% of K_height_pixel 245) so the three midpoint rings, which already have both slopes, can pass the K/AB distance check and become real prompts. Spurious-line risk is bounded because the angle filter, the vertical-intersection step, minLineLength (not in bounds, unchanged) and the pattern gate still screen candidates, and the bolt-pocket chevrons are ~30 px long. Verticals, horizontal Hough, denoising and enhancing are untouched, so depth_nan_ratio, sam_fill_rate and ring_count_error must stay identical and any proxy change is attributable to correspondence_f1@15 via prompt placement. Expected signature: det_real_detection_ratio 0.7 -> >=0.8 (midpoint -> positive/negative_slope first, then outer-ring assume -> real), oblique count up in x<1100 / x>2500, more green boundaries in the fallback columns, sam_segment_size_cv down. Decision rule for round 3: if prompt types still do not change at these bound edges, detection is non-identifiable within this parameter box for 5-4 (the true fix is stage-3 joint enhancement, out of bounds) and round 3 should either try a single SAM geometry move (K_height/angle) or stop and keep the anchor rather than inflate evidence features.",
    "proposer": "Fable-5.1 (fresh per-case agent)"
  },
  {
    "round": 3,
    "status": "ok",
    "overlay": {
      "detecting": {
        "hough_threshold_horizontal": 30,
        "maxLineGap_horizontal": 25
      }
    },
    "proxy_scaled": 0.7086898612470216,
    "band": "accept",
    "features": {
      "correspondence_f1@15": 0.4973504336218273,
      "sam_fill_rate": 0.7599389968796842,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.19848996720212705
    },
    "recentre_residual_max_cm": 2.1,
    "full_pipeline": false,
    "rationale": "The anchor proxy 0.692 sits 0.008 under the accept band and the only lean feature far from healthy is correspondence_f1@15 (0.467), which is set by prompt-centre y placement. Two rounds established that the oblique-Hough axis is flat-to-negative in this box, so round 3 spends the final budget on the one detection axis with fresh evidence and a clear mechanism: horizontal joints are the most numerous, longest, and most regularly spaced (AB_height_pixel 745) joint lines on this map, they are visibly present in the outer rings on the depth map, and they feed the same intersection + distance-pattern step that decides whether a ring gets a real K centre or a guess. Move hough_threshold_horizontal 50 -> 30 (accumulator votes; dotted outer-ring joints have roughly 30-60 lit pixels per 105 px window after 3x3 dilation) and maxLineGap_horizontal 10 -> 25 (bridges the 10-25 px gaps between dots without joining separate joints, which are >=245 px apart). Both are interior points of the bounds ([25,70], [5,30]) chosen deliberately after round 2 showed bound-edge stampedes generate spurious candidates. minLineLength 105 stays (out of bounds) so the periodic bolt-pocket chevrons (~30 px) and isolated speckle cannot become lines; the [5,10]-degree angle filter, ring-vertical intersection, merge_close_points(6) and check_distance_pattern still gate every candidate. Oblique keys, binary_threshold and pattern_tolerance are omitted (back to anchor) and denoising/enhancing/sam are untouched, so depth_nan_ratio, sam_fill_rate and ring_count_error must remain identical and any proxy change is attributable to correspondence_f1@15 via horizontal-line-driven prompt placement. Expected signature: more blue horizontal segments in x<900 and x>2900, edge-ring 'assume' prompts converted to pattern-derived prompts, midpoint prompts snapping onto the AB lattice, det_real_detection_ratio 0.7 -> >=0.8, sam_segment_size_cv down from 1.11, correspondence_f1@15 up toward >=0.5 (proxy >=0.70 crosses the accept band). Failure signature: if horizontal yield rises but prompt types are unchanged, detection for 5-4 is non-identifiable across all in-bounds Hough knobs and the selector should keep the anchor / round 1; the true remediation is stage-3 joint enhancement (r_lower_depth_threshold), which is outside this campaign's bounds.",
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
`/home/boringtao/Projects/Proxy4Tun/data/sc-general/stage3/packets-fable-fresh/5-4/round3_proposal.json`

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
