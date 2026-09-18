# GPT-5.6 reflection — subset 3-10 (propose round 3)

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

- subset: `3-10`
- family: `t3`
- lining_mode: `continuous`
- stage1_unlocked: `True` (residual gate 10 cm)
- arm: `gpt56` / proposer: `GPT-5.6 (fresh per-case agent)`
- model: `gpt-5.6-sol-medium`

### Anchor (GT-blind)
```json
{
  "proxy_raw": 0.588697,
  "proxy_scaled": 0.588697,
  "band": "refine",
  "features": {
    "correspondence_f1@15": 0.287265,
    "sam_fill_rate": 0.697553,
    "ring_count_error": 0.0,
    "depth_nan_ratio": 0.142028
  },
  "recentre_residual_max_cm": 10.2,
  "orient_axis_corr": -0.9990592937874491,
  "ring_count": 10,
  "ring_count_error": 0.0,
  "labelmap_source": "results.pkl",
  "run_dir": "/home/boringtao/Projects/Proxy4Tun/data/bo/unified/3-10-family-proxy/runs/3-10-anchor"
}
```

### Intrinsics (GT-blind)
```json
{
  "orient_axis_corr": -0.9990592937874491,
  "orient_invariant_ok": 1.0,
  "recentre_residual_max_cm": 10.2,
  "denoise_retained_ratio": 0.7404734761200185,
  "depth_nan_ratio": 0.14202755710717666,
  "depth_outlier_ratio": 0.0008614399729785715,
  "det_real_detection_ratio": 0.0,
  "det_fallback_ratio": 1.0,
  "det_n_points": 10.0,
  "sam_fill_rate": 0.697552574768962,
  "sam_ring_completeness": 1.0,
  "sam_segment_size_cv": 0.5772969297747274,
  "sam_ontology_divergence": 0.2235725711106475
}
```

### Prior rounds (this arm only)
```json
[
  {
    "round": 1,
    "status": "ok",
    "overlay": {
      "denoising": {
        "mask_r_low": 2.75,
        "mask_r_high": 3.1,
        "mask_theta_low": 1.25,
        "mask_theta_high": 18.0
      },
      "enhancing": {
        "curvature_threshold": 0.0006
      },
      "detecting": {
        "binary_threshold": 110,
        "hough_threshold_oblique": 25,
        "hough_threshold_horizontal": 25,
        "hough_threshold_vertical": 1200,
        "maxLineGap_oblique": 50,
        "pattern_tolerance": 16,
        "uniform_k_snap": true
      },
      "sam": {
        "segment_width": 1200,
        "K_height": 900.0,
        "angle": 6.5
      }
    },
    "proxy_scaled": 0.518777423364332,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.15467784636817522,
      "sam_fill_rate": 0.7123001916219953,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.1491418310622614
    },
    "recentre_residual_max_cm": 10.2,
    "full_pipeline": false,
    "rationale": "This bounded stages-2-to-6 overlay keeps denoising broad enough to retain joint traces, lowers the image and Hough acceptance barriers, bridges fragmented oblique segments, and tolerates the visible transverse-line slope. Uniform K snapping retains the already-correct 10-ring regularity. K_height is raised to 900 (meeting the requested >=850 constraint), with moderate segment width and angle changes to improve horizontal prompt placement. Unfolding is intentionally omitted because the 10.2 cm residual only barely unlocks stage 1 and a full rerun is not preferred.",
    "proposer": "GPT-5.6 (fresh per-case agent)"
  },
  {
    "round": 2,
    "status": "ok",
    "overlay": {
      "denoising": {
        "mask_r_low": 2.9,
        "mask_r_high": 3.0,
        "mask_theta_low": 2.0,
        "mask_theta_high": 17.0
      },
      "enhancing": {
        "curvature_threshold": 0.0012
      },
      "detecting": {
        "binary_threshold": 130,
        "hough_threshold_oblique": 38,
        "hough_threshold_horizontal": 38,
        "hough_threshold_vertical": 1800,
        "maxLineGap_oblique": 28,
        "pattern_tolerance": 10,
        "uniform_k_snap": true
      },
      "sam": {
        "segment_width": 1100,
        "K_height": 900.0,
        "angle": 5.5
      }
    },
    "proxy_scaled": 0.5220298233128438,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.16689024829632274,
      "sam_fill_rate": 0.67744843589557,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.12006578314379102
    },
    "recentre_residual_max_cm": 10.2,
    "full_pipeline": false,
    "rationale": "This proposal is deliberately different from round 1: horizontal and oblique Hough thresholds move to 38, maxLineGap_oblique drops to 28, and binary threshold rises to 130. Denoising is narrowed and curvature filtering strengthened to reduce noisy fragments, while moderate pattern tolerance and uniform snapping preserve the correct 10-ring structure. K_height remains 900 as requested; segment width and angle are reduced moderately to avoid compounding the detector regression. No unfolding keys are included and full remains false.",
    "proposer": "GPT-5.6 (fresh per-case agent)"
  },
  {
    "round": 3,
    "status": "ok",
    "overlay": {
      "denoising": {
        "mask_r_low": 2.82,
        "mask_r_high": 3.08,
        "mask_theta_low": 1.6,
        "mask_theta_high": 17.8
      },
      "enhancing": {
        "curvature_threshold": 0.0008
      },
      "detecting": {
        "binary_threshold": 120,
        "hough_threshold_oblique": 30,
        "hough_threshold_horizontal": 30,
        "hough_threshold_vertical": 1500,
        "maxLineGap_oblique": 40,
        "pattern_tolerance": 14,
        "uniform_k_snap": true
      },
      "sam": {
        "segment_width": 1250,
        "K_height": 925.0,
        "angle": 6.0
      }
    },
    "proxy_scaled": 0.5333275740929334,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.18554623703723963,
      "sam_fill_rate": 0.6963761612535474,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.13948808538335505
    },
    "recentre_residual_max_cm": 10.2,
    "full_pipeline": false,
    "rationale": "Round 3 targets the untested middle regime with Hough thresholds of 30, maxLineGap_oblique 40, and pattern tolerance 14. The mask is mildly wider than round 2 without returning to round 1's broad angular range, and curvature and binary thresholds are set between prior values. K_height rises to 925 as requested, paired with an intermediate segment width and angle. Uniform snapping is retained because ring count has remained exact. Unfolding is omitted and full is false.",
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
`/home/boringtao/Projects/Proxy4Tun/data/sc-general/stage3/packets-gpt56/3-10/round3_proposal.json`

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
