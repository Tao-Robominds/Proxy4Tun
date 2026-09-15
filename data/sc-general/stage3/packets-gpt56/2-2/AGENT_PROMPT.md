# GPT-5.6 reflection — subset 2-2 (propose round 3)

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

- subset: `2-2`
- family: `t1&2`
- lining_mode: `staggered`
- stage1_unlocked: `False` (residual gate 10 cm)
- arm: `gpt56` / proposer: `GPT-5.6 (fresh per-case agent)`
- model: `gpt-5.6-sol-medium`

### Anchor (GT-blind)
```json
{
  "proxy_raw": 0.699142,
  "proxy_scaled": 0.699142,
  "band": "refine",
  "features": {
    "correspondence_f1@15": 0.455,
    "sam_fill_rate": 0.743164,
    "ring_count_error": 0.0,
    "depth_nan_ratio": 0.111005
  },
  "recentre_residual_max_cm": 1.5,
  "orient_axis_corr": -0.9998899225490308,
  "ring_count": 10,
  "ring_count_error": 0.0,
  "labelmap_source": "results.pkl",
  "run_dir": "/home/boringtao/Projects/Proxy4Tun/data/bo/unified/2-2-family-proxy/runs/2-2-anchor"
}
```

### Intrinsics (GT-blind)
```json
{
  "orient_axis_corr": -0.9998899225490308,
  "orient_invariant_ok": 1.0,
  "recentre_residual_max_cm": 1.5,
  "denoise_retained_ratio": 0.7711390480524585,
  "depth_nan_ratio": 0.11100505152955387,
  "depth_outlier_ratio": 0.003969557138198945,
  "det_real_detection_ratio": 0.9,
  "det_fallback_ratio": 0.1,
  "det_n_points": 10.0,
  "sam_fill_rate": 0.7431639534162133,
  "sam_ring_completeness": 0.8888888888888888,
  "sam_segment_size_cv": 1.1492356762263811,
  "sam_ontology_divergence": 0.16496563728120134
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
        "curvature_threshold": 0.004,
        "inter_radius": 0.05
      },
      "detecting": {
        "hough_threshold_oblique": 62,
        "maxLineGap_oblique": 48
      },
      "sam": {
        "processing.y_bounds": [
          4000,
          13300
        ]
      }
    },
    "proxy_scaled": 0.68676588920136,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.43152422423518316,
      "sam_fill_rate": 0.7416921788056182,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.10690951130186013
    },
    "recentre_residual_max_cm": 1.5,
    "full_pipeline": false,
    "rationale": "Use near-midpoint bounded values to strengthen local joint continuity without unlocking unfolding or broadly changing the established geometry. A mid-range curvature threshold and interaction radius target faint joint structure, while moderate Hough support and line-gap tolerance consolidate repeated oblique boundaries. A centered lower y bound avoids an extreme crop while retaining the required fixed upper bound.",
    "proposer": "GPT-5.6 (fresh per-case agent)"
  },
  {
    "round": 2,
    "status": "ok",
    "overlay": {
      "detecting": {
        "binary_threshold": 125,
        "hough_threshold_horizontal": 55
      },
      "sam": {
        "processing.y_bounds": [
          3800,
          13300
        ]
      }
    },
    "proxy_scaled": 0.7123548569660481,
    "band": "accept",
    "features": {
      "correspondence_f1@15": 0.47963565346554715,
      "sam_fill_rate": 0.7422496535175723,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.11100505152955387
    },
    "recentre_residual_max_cm": 1.5,
    "full_pipeline": false,
    "rationale": "Leave denoising, enhancement, oblique detection, and unfolding unchanged. Use a moderately permissive binary threshold with a below-midpoint horizontal Hough threshold to recover faint repeated horizontal joints, and move the SAM lower bound toward the lower half of its allowed range to retain more usable wall area than round 1. This is a different, conservative test aimed directly at correspondence while protecting exact ring count and orientation.",
    "proposer": "GPT-5.6 (fresh per-case agent)"
  },
  {
    "round": 3,
    "status": "ok",
    "overlay": {
      "detecting": {
        "binary_threshold": 122,
        "hough_threshold_horizontal": 52
      },
      "sam": {
        "processing.y_bounds": [
          3700,
          13300
        ]
      }
    },
    "proxy_scaled": 0.7118948319031799,
    "band": "accept",
    "features": {
      "correspondence_f1@15": 0.47879369977184677,
      "sam_fill_rate": 0.7422496535175723,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.11100505152955387
    },
    "recentre_residual_max_cm": 1.5,
    "full_pipeline": false,
    "rationale": "Keep denoising, enhancement, oblique detection, vertical detection, and unfolding untouched. Move the successful binary and horizontal Hough thresholds only slightly toward greater sensitivity, and lower the flat SAM crop by just 100 units to test whether a little more wall support improves correspondence or fill. This provides a distinct local refinement around the accepted round while limiting regression risk.",
    "proposer": "GPT-5.6 (fresh per-case agent)"
  }
]
```

### Parameter bounds (ONLY these keys; reject anything else)
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

## Required output

Write a single JSON object to:
`/home/boringtao/Projects/Proxy4Tun/data/sc-general/stage3/packets-gpt56/2-2/round3_proposal.json`

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
