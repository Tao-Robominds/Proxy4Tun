# GPT-5.6 reflection — subset 5-3 (propose round 3)

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

- subset: `5-3`
- family: `t4&5`
- lining_mode: `complex`
- stage1_unlocked: `False` (residual gate 10 cm)
- arm: `gpt56` / proposer: `GPT-5.6 (fresh per-case agent)`
- model: `gpt-5.6-sol-medium`

### Anchor (GT-blind)
```json
{
  "proxy_raw": 0.680653,
  "proxy_scaled": 0.680653,
  "band": "refine",
  "features": {
    "correspondence_f1@15": 0.458619,
    "sam_fill_rate": 0.736776,
    "ring_count_error": 0.0,
    "depth_nan_ratio": 0.201357
  },
  "recentre_residual_max_cm": 3.5,
  "orient_axis_corr": -0.8773629680874642,
  "ring_count": 10,
  "ring_count_error": 0.0,
  "labelmap_source": "only_label.csv",
  "run_dir": "/home/boringtao/Projects/Proxy4Tun/data/bo/unified/5-3-family-proxy/runs/5-3-anchor"
}
```

### Intrinsics (GT-blind)
```json
{
  "orient_axis_corr": -0.8773629680874642,
  "orient_invariant_ok": 1.0,
  "recentre_residual_max_cm": 3.5,
  "denoise_retained_ratio": 0.7488301283104651,
  "depth_nan_ratio": 0.2013572349021065,
  "depth_outlier_ratio": 0.0013759294357778102,
  "det_real_detection_ratio": 0.7,
  "det_fallback_ratio": 0.3,
  "det_n_points": 10.0,
  "sam_fill_rate": 0.7367757097474392,
  "sam_ring_completeness": 1.0,
  "sam_segment_size_cv": 1.013794842616219,
  "sam_ontology_divergence": 0.09703285217926161
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
        "mask_r_low": 3.55,
        "mask_r_high": 3.95
      },
      "enhancing": {
        "curvature_threshold": 0.0007
      },
      "detecting": {
        "binary_threshold": 118,
        "hough_threshold_oblique": 35,
        "hough_threshold_horizontal": 32,
        "hough_threshold_vertical": 2600,
        "maxLineGap_oblique": 65,
        "maxLineGap_horizontal": 20,
        "pattern_tolerance": 12
      },
      "sam": {
        "segment_width": 1750,
        "K_height": 1250.0,
        "angle": 9.5
      }
    },
    "proxy_scaled": 0.6587012546193832,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.4091547313694746,
      "sam_fill_rate": 0.7489090045864532,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.1927505185087641
    },
    "recentre_residual_max_cm": 3.5,
    "full_pipeline": false,
    "rationale": "This is a balanced recovery proposal: a moderate curvature threshold and lower Hough thresholds should recover structural fragments, larger line gaps should bridge broken joints, and mid-range SAM geometry should improve boundary reach without radically changing the complete 10-ring partition.",
    "proposer": "GPT-5.6 (fresh per-case agent)"
  },
  {
    "round": 2,
    "status": "ok",
    "overlay": {
      "denoising": {
        "mask_r_low": 3.7,
        "mask_r_high": 3.9
      },
      "enhancing": {
        "curvature_threshold": 0.0014
      },
      "detecting": {
        "binary_threshold": 145,
        "hough_threshold_oblique": 58,
        "hough_threshold_horizontal": 55,
        "hough_threshold_vertical": 4000,
        "maxLineGap_oblique": 38,
        "maxLineGap_horizontal": 9,
        "pattern_tolerance": 8
      },
      "sam": {
        "segment_width": 1980,
        "K_height": 1425.0,
        "angle": 10.8
      }
    },
    "proxy_scaled": 0.49282139665213565,
    "band": "reject",
    "features": {
      "correspondence_f1@15": 0.11294708870629024,
      "sam_fill_rate": 0.736644249287459,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.19619031270428774
    },
    "recentre_residual_max_cm": 3.5,
    "full_pipeline": false,
    "rationale": "This proposal deliberately trades recall for stability. Higher binary and Hough thresholds reject weaker fragments, shorter allowed gaps reduce accidental bridging, and larger SAM spatial scales encourage more coherent regions. It is distinct from the balanced proposal and tests whether false or unstable boundaries dominate the low correspondence.",
    "proposer": "GPT-5.6 (fresh per-case agent)"
  },
  {
    "round": 3,
    "status": "ok",
    "overlay": {
      "denoising": {
        "mask_r_low": 3.5,
        "mask_r_high": 4.05
      },
      "enhancing": {
        "curvature_threshold": 0.0003
      },
      "detecting": {
        "binary_threshold": 104,
        "hough_threshold_oblique": 27,
        "hough_threshold_horizontal": 27,
        "hough_threshold_vertical": 1200,
        "maxLineGap_oblique": 78,
        "maxLineGap_horizontal": 29,
        "pattern_tolerance": 18
      },
      "sam": {
        "segment_width": 1540,
        "K_height": 1075.0,
        "angle": 7.8
      }
    },
    "proxy_scaled": 0.5906776846005035,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.288799521598805,
      "sam_fill_rate": 0.7439271587703593,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.1971557854290807
    },
    "recentre_residual_max_cm": 3.5,
    "full_pipeline": false,
    "rationale": "This is the permissive alternative: low enhancement and detection thresholds maximize candidate recovery, long gap limits reconnect interrupted horizontal and oblique joints, and smaller SAM scales emphasize local boundary adherence. The wide pattern tolerance accommodates visibly irregular joint spacing while preserving the fixed stage-1 geometry.",
    "proposer": "GPT-5.6 (fresh per-case agent)"
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
`/home/boringtao/Projects/Proxy4Tun/data/sc-general/stage3/packets-gpt56/5-3/round3_proposal.json`

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
