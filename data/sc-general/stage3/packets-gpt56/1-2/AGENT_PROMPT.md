# GPT-5.6 reflection — subset 1-2 (propose round 3)

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

- subset: `1-2`
- family: `t1&2`
- lining_mode: `staggered`
- stage1_unlocked: `False` (residual gate 10 cm)
- arm: `gpt56` / proposer: `GPT-5.6 (fresh per-case agent)`
- model: `gpt-5.6-sol-medium`

### Anchor (GT-blind)
```json
{
  "proxy_raw": 0.647823,
  "proxy_scaled": 0.647823,
  "band": "refine",
  "features": {
    "correspondence_f1@15": 0.367509,
    "sam_fill_rate": 0.722929,
    "ring_count_error": 0.0,
    "depth_nan_ratio": 0.101505
  },
  "recentre_residual_max_cm": 3.5,
  "orient_axis_corr": 0.9999355849000731,
  "ring_count": 10,
  "ring_count_error": 0.0,
  "labelmap_source": "results.pkl",
  "run_dir": "/home/boringtao/Projects/Proxy4Tun/data/bo/unified/1-2-family-proxy/runs/1-2-anchor"
}
```

### Intrinsics (GT-blind)
```json
{
  "orient_axis_corr": 0.9999355849000731,
  "orient_invariant_ok": 1.0,
  "recentre_residual_max_cm": 3.5,
  "denoise_retained_ratio": 0.7585160833227094,
  "depth_nan_ratio": 0.10150520930740327,
  "depth_outlier_ratio": 0.005202745247880946,
  "det_real_detection_ratio": 0.8,
  "det_fallback_ratio": 0.2,
  "det_n_points": 10.0,
  "sam_fill_rate": 0.7229286883173068,
  "sam_ring_completeness": 0.8888888888888888,
  "sam_segment_size_cv": 1.3381961231118245,
  "sam_ontology_divergence": 0.2397912045632986
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
        "curvature_threshold": 0.001,
        "inter_radius": 0.05
      },
      "detecting": {
        "binary_threshold": 115,
        "hough_threshold_oblique": 45,
        "hough_threshold_horizontal": 45,
        "maxLineGap_oblique": 65
      },
      "sam": {
        "processing.y_bounds": [
          3800,
          13300
        ]
      }
    },
    "proxy_scaled": 0.628551177627753,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.33364111248696454,
      "sam_fill_rate": 0.7231162626416735,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.10544906469897454
    },
    "recentre_residual_max_cm": 3.5,
    "full_pipeline": false,
    "rationale": "Lower curvature and binary thresholds should retain faint joint evidence, while lower horizontal/oblique Hough thresholds and a larger oblique gap allowance should connect the repeated staggered joints visible across rings. Keeping the vertical Hough setting untouched protects the exact ring count. A lower processing bound of 3800 extends promptable coverage while retaining the required upper bound of 13300. Unfolding is omitted because stage1_unlocked is false.",
    "proposer": "GPT-5.6 (fresh per-case agent)"
  },
  {
    "round": 2,
    "status": "ok",
    "overlay": {
      "enhancing": {
        "curvature_threshold": 0.006,
        "inter_radius": 0.03
      },
      "detecting": {
        "binary_threshold": 150,
        "hough_threshold_oblique": 80,
        "hough_threshold_horizontal": 75,
        "maxLineGap_oblique": 30
      },
      "sam": {
        "processing.y_bounds": [
          4200,
          13300
        ]
      }
    },
    "proxy_scaled": 0.6474017612408824,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.366194389427476,
      "sam_fill_rate": 0.7237422070444347,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.10113519322713976
    },
    "recentre_residual_max_cm": 3.5,
    "full_pipeline": false,
    "rationale": "This proposal deliberately reverses round 1 rather than making another permissive adjustment. A higher curvature threshold, smaller interaction radius, stronger binary threshold, higher horizontal and oblique Hough thresholds, and shorter oblique gap allowance prioritize repeatable joints over line count. Raising the SAM lower bound to 4200 removes more of the irregular lower fringe while preserving the required upper bound of 13300. Vertical detection remains untouched because ring count error is zero, and unfolding is omitted because stage1_unlocked is false.",
    "proposer": "GPT-5.6 (fresh per-case agent)"
  },
  {
    "round": 3,
    "status": "ok",
    "overlay": {
      "enhancing": {
        "curvature_threshold": 0.007,
        "inter_radius": 0.025
      },
      "detecting": {
        "binary_threshold": 155,
        "hough_threshold_oblique": 70,
        "hough_threshold_horizontal": 80,
        "maxLineGap_oblique": 20
      },
      "sam": {
        "processing.y_bounds": [
          4300,
          13300
        ]
      }
    },
    "proxy_scaled": 0.6404392361806862,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.35312154414271596,
      "sam_fill_rate": 0.7241873695078342,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.10084824806856378
    },
    "recentre_residual_max_cm": 3.5,
    "full_pipeline": false,
    "rationale": "The proposal retains a high curvature threshold, small interaction radius, and strong binary threshold to preserve round 2's depth and fill gains. It lowers only the oblique Hough threshold relative to round 2 while setting the oblique gap allowance to its minimum, allowing compact well-supported staggered joints without reconnecting distant fragments. A stricter horizontal threshold limits unrelated transverse clutter. Raising the SAM lower bound modestly to 4300 further avoids the irregular lower fringe. Vertical detection remains untouched because ring count error is zero; unfolding is omitted because stage1_unlocked is false.",
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
`/home/boringtao/Projects/Proxy4Tun/data/sc-general/stage3/packets-gpt56/1-2/round3_proposal.json`

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
