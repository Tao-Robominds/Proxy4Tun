# Fable 5.1 reflection — subset 3-7 (propose round 3)

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

- subset: `3-7`
- family: `t3`
- lining_mode: `continuous`
- stage1_unlocked: `False` (residual gate 10 cm)
- arm: `fable_fresh` / proposer: `Fable-5.1 (fresh per-case agent)`
- model: `claude-fable-5-1-thinking-high`

### Anchor (GT-blind)
```json
{
  "proxy_raw": 0.539694,
  "proxy_scaled": 0.539694,
  "band": "refine",
  "features": {
    "correspondence_f1@15": 0.171748,
    "sam_fill_rate": 0.766799,
    "ring_count_error": 0.0,
    "depth_nan_ratio": 0.164506
  },
  "recentre_residual_max_cm": 3.6,
  "orient_axis_corr": -0.9991211319489915,
  "ring_count": 10,
  "ring_count_error": 0.0,
  "labelmap_source": "results.pkl",
  "run_dir": "/home/boringtao/Projects/Proxy4Tun/data/bo/unified/3-7-family-proxy/runs/3-7-anchor"
}
```

### Intrinsics (GT-blind)
```json
{
  "orient_axis_corr": -0.9991211319489915,
  "orient_invariant_ok": 1.0,
  "recentre_residual_max_cm": 3.6,
  "denoise_retained_ratio": 0.7976920114616173,
  "depth_nan_ratio": 0.16450624232718375,
  "depth_outlier_ratio": 0.000299478779485916,
  "det_real_detection_ratio": 0.0,
  "det_fallback_ratio": 1.0,
  "det_n_points": 10.0,
  "sam_fill_rate": 0.7667991671398826,
  "sam_ring_completeness": 1.0,
  "sam_segment_size_cv": 0.6717568636337622,
  "sam_ontology_divergence": 0.24785280773585067
}
```

### Prior rounds (this arm only)
```json
[
  {
    "round": 1,
    "status": "ok",
    "overlay": {
      "enhancing": {
        "curvature_threshold": 0.0004
      },
      "detecting": {
        "binary_threshold": 112,
        "hough_threshold_oblique": 22,
        "hough_threshold_horizontal": 26,
        "maxLineGap_oblique": 50,
        "pattern_tolerance": 12,
        "uniform_k_snap": true
      }
    },
    "proxy_scaled": 0.5438708383714845,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.1805422375809007,
      "sam_fill_rate": 0.7675954754025599,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.16857814484577904
    },
    "recentre_residual_max_cm": 3.6,
    "full_pipeline": false,
    "rationale": "Relax the oblique HoughLinesP so the fragmented bolt-pocket evidence chains into longitudinal joint lines across all 10 rings: threshold 30->22 and maxLineGap 30->50 (both inside bounds, still above the floor to avoid pure noise). Lower binary_threshold 127->112 so dilated faint outlier pixels survive binarisation, and lower enhancing.curvature_threshold 0.0005->0.0004 so slightly more edge points are labelled as joint candidates. Vertical accumulator kept at prior (10 verticals == 10 rings is already correct; do not disturb). Horizontal threshold trimmed to 26 only as a fallback aid. uniform_k_snap left true and pattern_tolerance at 12 px so extra intersections cannot move the propagated K row. Expected effect: more K-band boundaries supported within 15 px -> correspondence_f1@15 rises; fill rate and ring count should be unchanged. Denoising kept at tunnel priors (experiences \u00a74).",
    "proposer": "Fable-5.1 (fresh per-case agent)"
  },
  {
    "round": 2,
    "status": "ok",
    "overlay": {
      "enhancing": {
        "curvature_threshold": 0.0008
      },
      "detecting": {
        "binary_threshold": 112,
        "hough_threshold_oblique": 22,
        "hough_threshold_horizontal": 45,
        "maxLineGap_oblique": 50,
        "pattern_tolerance": 12,
        "uniform_k_snap": true
      },
      "sam": {
        "angle": 5.3
      }
    },
    "proxy_scaled": 0.5216501493815697,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.13502451808030927,
      "sam_fill_rate": 0.767425770362973,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.15557975693367712
    },
    "recentre_residual_max_cm": 3.6,
    "full_pipeline": false,
    "rationale": "Pivot away from the saturated Hough path. (1) enhancing.curvature_threshold 0.0004->0.0008 (bounds [0.0002,0.002]): more lining points qualify as flat surface and get the 3-step densification, shrinking voids -> depth_nan_ratio down and sam_fill_rate up; bolt pockets remain depth outliers so the outlier map used for detection is unaffected. (2) detecting.hough_threshold_horizontal 26->45 (bounds [20,60]): suppress the spurious ~0 deg fragment near (2300,800) that counts against correspondence precision; obliques + uniform_k_snap already fix the K row, so horizontals are not needed. (3) sam.angle 6.12->5.3 (bounds [4,9]): match the K template taper to the measured +5.0/+5.5/-5.5 deg joint slopes so the K label boundaries track the detected lines within 15 px along the whole ring width. Keep the round-1 oblique settings (threshold 22, maxLineGap 50, binary 112, pattern_tolerance 12, uniform_k_snap true) so the detected line set is unchanged except for the removed horizontal, isolating the effect of the stage-3/stage-5 change. K_height and segment_width left at priors (measured 168 px / 240 px agree). Expected: depth_nan_ratio ~0.15, sam_fill_rate >0.78, ring_count_error 0 unchanged, f1@15 flat-to-up; a proxy rise driven by NaN alone with fill flat would be treated as cosmetic and reverted in round 3.",
    "proposer": "Fable-5.1 (fresh per-case agent)"
  },
  {
    "round": 3,
    "status": "ok",
    "overlay": {
      "enhancing": {
        "curvature_threshold": 0.0004
      },
      "detecting": {
        "binary_threshold": 100,
        "hough_threshold_oblique": 20,
        "hough_threshold_horizontal": 26,
        "maxLineGap_oblique": 60,
        "pattern_tolerance": 12,
        "uniform_k_snap": true
      }
    },
    "proxy_scaled": 0.5431988875418318,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.1793124100591481,
      "sam_fill_rate": 0.7675954754025599,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.16857814484577904
    },
    "recentre_residual_max_cm": 3.6,
    "full_pipeline": false,
    "rationale": "Return to the round-1 configuration as the base (it is the best measured point: proxy 0.5439, f1@15 0.181) and spend the final round on the untested remaining headroom of r_relax_hough, which round 1 showed to be safe (going 30->22 / 30->50 added zero spurious lines). (1) detecting.maxLineGap_oblique 50 -> 60 (bound max): the K-edge bolt pockets are ~45-50 px apart, so 60 clears the spacing and lets HoughLinesP chain adjacent pockets along the true +/-5.3 deg joint into segments that pass minLineLength 40 and the [5,10] deg angle filter; 50 was at the spacing boundary. (2) detecting.hough_threshold_oblique 22 -> 20 (bound floor): accept the shorter chains from sparser left-ring glyphs. (3) detecting.binary_threshold 112 -> 100 (bound floor): keep fainter dilated outlier pixels so the pocket glyphs are wider and easier to chain. (4) enhancing.curvature_threshold back to 0.0004 (round-1 value): removes the round-2 K-edge blurring that cost f1; the small NaN increase is accepted as non-cosmetic. (5) sam.angle omitted -> T3 prior 6.12 deg restored; K_height/segment_width untouched (measured 168 px / 240 px agree with priors). (6) hough_threshold_horizontal kept at 26 (round-1 value) so the horizontal path is identical to round 1 and any line-set change is attributable to the oblique relaxation alone; the (2300,800) fragment is insensitive to this knob anyway. (7) hough_threshold_vertical, pattern_tolerance 12, uniform_k_snap true unchanged so 10 verticals == 10 rings and the K row stays snapped at y~1550. Expected: ring_count_error 0 and sam_fill_rate ~0.77 unchanged; depth_nan_ratio back to ~0.169; f1@15 >= 0.181 if any additional K-edge segments appear in rings 1-7 (each new supported ring adds ~2 boundaries within 15 px), otherwise a reproduction of round 1. Downside is bounded: spurious obliques would have to fall in [5,10] deg on a nearly horizontal glyph field, which round 1 showed does not happen at 22/50.",
    "proposer": "Fable-5.1 (fresh per-case agent)"
  }
]
```

### Parameter bounds (ONLY these keys; reject anything else)
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

## Required output

Write a single JSON object to:
`/home/boringtao/Projects/Proxy4Tun/data/sc-general/stage3/packets-fable-fresh/3-7/round3_proposal.json`

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
