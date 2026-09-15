# Gemini 3.8 reflection — subset 5-3 (propose round 3)

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
- `data/sc-general/stage3/selections/`, `selections-fable/`, `selections-gpt56/`,
  Fable/GPT/deterministic refinement trees, or other cases' Gemini proposals
- `data/bo/`, `data/anchors/`, `data/baseline`

## State

- subset: `5-3`
- family: `t4&5`
- lining_mode: `complex`
- stage1_unlocked: `False` (residual gate 10 cm)
- arm: `gemini38` / proposer: `Gemini-3.8 (fresh per-case agent)`
- model: `inherit`

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
      "detecting": {
        "hough_threshold_oblique": 40,
        "maxLineGap_oblique": 55,
        "pattern_tolerance": 12
      },
      "sam": {
        "segment_width": 1800,
        "K_height": 1230.0,
        "angle": 9.8
      }
    },
    "proxy_scaled": 0.6842658469861389,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.4652309099884805,
      "sam_fill_rate": 0.7367757097474392,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.2013572349021065
    },
    "recentre_residual_max_cm": 3.5,
    "full_pipeline": false,
    "rationale": "Round 1 pins SAM to notebook priors with a mid-band K_height (not floor/ceiling) to avoid empty-crop into the large white horizontal voids. Mild pattern_tolerance and oblique Hough easing help distance-pattern match without touching locked unfolding.",
    "proposer": "Gemini-3.8 (fresh per-case agent)"
  },
  {
    "round": 2,
    "status": "ok",
    "overlay": {
      "enhancing": {
        "curvature_threshold": 0.0004
      },
      "detecting": {
        "binary_threshold": 115,
        "hough_threshold_oblique": 30,
        "hough_threshold_horizontal": 35,
        "maxLineGap_oblique": 65,
        "maxLineGap_horizontal": 12,
        "pattern_tolerance": 8
      },
      "sam": {
        "segment_width": 1650,
        "K_height": 1180.0,
        "angle": 11.0
      }
    },
    "proxy_scaled": 0.6806079426741911,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.4594594960733605,
      "sam_fill_rate": 0.7358216101782755,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.20254292688203396
    },
    "recentre_residual_max_cm": 3.5,
    "full_pipeline": false,
    "rationale": "Distinct from prior-pin: deliberately narrower width (1650) and steeper angle (11.0) to tighten trapezoid K templates. K_height 1180 stays above the empty-crop floor. Pair with more sensitive oblique detection and slightly lower binary_threshold to recover faint slanted joints without unlocking stage 1.",
    "proposer": "Gemini-3.8 (fresh per-case agent)"
  },
  {
    "round": 3,
    "status": "ok",
    "overlay": {
      "denoising": {
        "mask_r_low": 3.6,
        "mask_r_high": 3.95
      },
      "detecting": {
        "binary_threshold": 125,
        "hough_threshold_oblique": 45,
        "hough_threshold_horizontal": 30,
        "maxLineGap_oblique": 50,
        "maxLineGap_horizontal": 20,
        "pattern_tolerance": 15
      },
      "sam": {
        "segment_width": 1950,
        "K_height": 1280.0,
        "angle": 8.0
      }
    },
    "proxy_scaled": 0.6547720502707504,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.40375017701035637,
      "sam_fill_rate": 0.7472303556359374,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.19526393389424773
    },
    "recentre_residual_max_cm": 3.5,
    "full_pipeline": false,
    "rationale": "Third distinct axis: detection-first horizontal recovery (lower horizontal threshold, larger maxLineGap_horizontal) plus wider segment_width 1950 and milder angle 8.0 so A/B blocks cover more seam context. K_height 1280 sits above prior without hitting the 1500 empty-crop ceiling. Tiny denoise outer-band nudge only as support for joint contrast.",
    "proposer": "Gemini-3.8 (fresh per-case agent)"
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
`/home/boringtao/Projects/Proxy4Tun/data/sc-general/stage3/packets-gemini38/5-3/round3_proposal.json`

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
