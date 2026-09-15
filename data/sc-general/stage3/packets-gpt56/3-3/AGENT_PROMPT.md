# GPT-5.6 reflection — subset 3-3 (propose round 3)

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
- `data/sc-general/stage3/selections/`, `selections-fable/`, Fable/deterministic
  refinement trees, or other cases' GPT proposals
- `data/bo/`, `data/anchors/`, `data/baseline`

## State

- subset: `3-3`
- family: `t3`
- lining_mode: `continuous`
- stage1_unlocked: `False` (residual gate 10 cm)
- arm: `gpt56` / proposer: `GPT-5.6 (fresh per-case agent)`
- model: `gpt-5.6-sol-medium`

### Anchor (GT-blind)
```json
{
  "proxy_raw": 0.52158,
  "proxy_scaled": 0.52158,
  "band": "refine",
  "features": {
    "correspondence_f1@15": 0.112841,
    "sam_fill_rate": 0.779975,
    "ring_count_error": 0.0,
    "depth_nan_ratio": 0.113874
  },
  "recentre_residual_max_cm": 2.7,
  "orient_axis_corr": 0.99996584722565,
  "ring_count": 10,
  "ring_count_error": 0.0,
  "labelmap_source": "results.pkl",
  "run_dir": "/home/boringtao/Projects/Proxy4Tun/data/bo/unified/3-3-family-proxy/runs/3-3-anchor"
}
```

### Intrinsics (GT-blind)
```json
{
  "orient_axis_corr": 0.99996584722565,
  "orient_invariant_ok": 1.0,
  "recentre_residual_max_cm": 2.7,
  "denoise_retained_ratio": 0.81787798500355,
  "depth_nan_ratio": 0.11387375767737186,
  "depth_outlier_ratio": 0.0007244705635925862,
  "det_real_detection_ratio": 0.0,
  "det_fallback_ratio": 1.0,
  "det_n_points": 10.0,
  "sam_fill_rate": 0.7799747173013317,
  "sam_ring_completeness": 1.0,
  "sam_segment_size_cv": 0.5941911494447767,
  "sam_ontology_divergence": 0.2503766921544423
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
        "pattern_tolerance": 20,
        "uniform_k_snap": true
      },
      "sam": {
        "segment_width": 1000,
        "K_height": 800.0,
        "angle": 4.0
      }
    },
    "proxy_scaled": 0.5254809422517643,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.11369481708859827,
      "sam_fill_rate": 0.79264377370253,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.11387375767737186
    },
    "recentre_residual_max_cm": 2.7,
    "full_pipeline": false,
    "rationale": "Raise pattern_tolerance to recover imperfect repeated joint evidence while retaining uniform_k_snap because the ten-column lattice and ring count are already correct. Use the minimum segment_width and angle to limit horizontal leakage and tilt, with a mid-low K_height to reduce oversized vertical propagation without aggressively sacrificing the currently strong fill rate.",
    "proposer": "GPT-5.6 (fresh per-case agent)"
  },
  {
    "round": 2,
    "status": "ok",
    "overlay": {
      "detecting": {
        "binary_threshold": 110,
        "hough_threshold_oblique": 25,
        "hough_threshold_horizontal": 25,
        "hough_threshold_vertical": 1000,
        "maxLineGap_oblique": 50,
        "pattern_tolerance": 12,
        "uniform_k_snap": true
      },
      "sam": {
        "segment_width": 1000,
        "K_height": 900.0,
        "angle": 4.0
      }
    },
    "proxy_scaled": 0.5040837777036201,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.07596629540525246,
      "sam_fill_rate": 0.7897553119642579,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.11387375767737186
    },
    "recentre_residual_max_cm": 2.7,
    "full_pipeline": false,
    "rationale": "Lower binary and Hough thresholds to admit the visible fragmented horizontal and oblique joint evidence, and increase maxLineGap_oblique so short aligned fragments can form usable lines. Use a mid-range pattern_tolerance of 12 to avoid the previous maximum-permissiveness setting while uniform_k_snap protects the already-correct ten-ring lattice. K_height 900 is safely above the requested 850 floor; segment_width 1000 and angle 4 retain the conservative geometry that improved fill in round 1.",
    "proposer": "GPT-5.6 (fresh per-case agent)"
  },
  {
    "round": 3,
    "status": "ok",
    "overlay": {
      "denoising": {
        "mask_r_low": 2.8,
        "mask_r_high": 3.05,
        "mask_theta_low": 1.5,
        "mask_theta_high": 17.0
      },
      "enhancing": {
        "curvature_threshold": 0.0008
      },
      "detecting": {
        "binary_threshold": 130,
        "hough_threshold_oblique": 35,
        "hough_threshold_horizontal": 35,
        "hough_threshold_vertical": 1500,
        "maxLineGap_oblique": 30,
        "pattern_tolerance": 16,
        "uniform_k_snap": true
      },
      "sam": {
        "segment_width": 1000,
        "K_height": 850.0,
        "angle": 4.0
      }
    },
    "proxy_scaled": 0.5197608485891081,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.09828716771255032,
      "sam_fill_rate": 0.7956049664917658,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.10473235790957432
    },
    "recentre_residual_max_cm": 2.7,
    "full_pipeline": false,
    "rationale": "Apply mild radial and angular denoising within the bounded interior, then use a low-interior curvature threshold to retain coherent joint structure without aggressively amplifying speckle. Move binary and Hough thresholds back to moderate values, shorten the oblique gap bridge, and use pattern_tolerance 16 as a compromise between round 1's permissive 20 and round 2's 12. Keep uniform_k_snap true and use conservative SAM settings with K_height 850, the nearest safe height to round 1's successful geometry.",
    "proposer": "GPT-5.6 (fresh per-case agent)"
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
`/home/boringtao/Projects/Proxy4Tun/data/sc-general/stage3/packets-gpt56/3-3/round3_proposal.json`

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
