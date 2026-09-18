# Gemini 3.8 reflection — subset 3-6 (propose round 3)

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

- subset: `3-6`
- family: `t3`
- lining_mode: `continuous`
- stage1_unlocked: `False` (residual gate 10 cm)
- arm: `gemini38` / proposer: `Gemini-3.8 (fresh per-case agent)`
- model: `inherit`

### Anchor (GT-blind)
```json
{
  "proxy_raw": 0.681391,
  "proxy_scaled": 0.681391,
  "band": "refine",
  "features": {
    "correspondence_f1@15": 0.467009,
    "sam_fill_rate": 0.649052,
    "ring_count_error": 0.0,
    "depth_nan_ratio": 0.105203
  },
  "recentre_residual_max_cm": 3.2,
  "orient_axis_corr": -0.9998273166785221,
  "ring_count": 10,
  "ring_count_error": 0.0,
  "labelmap_source": "results.pkl",
  "run_dir": "/home/boringtao/Projects/Proxy4Tun/data/bo/unified/3-6-family-proxy/runs/3-6-anchor"
}
```

### Intrinsics (GT-blind)
```json
{
  "orient_axis_corr": -0.9998273166785221,
  "orient_invariant_ok": 1.0,
  "recentre_residual_max_cm": 3.2,
  "denoise_retained_ratio": 0.6947482510592177,
  "depth_nan_ratio": 0.1052027439356335,
  "depth_outlier_ratio": 0.0011429524394758353,
  "det_real_detection_ratio": 0.0,
  "det_fallback_ratio": 1.0,
  "det_n_points": 10.0,
  "sam_fill_rate": 0.6490524518014911,
  "sam_ring_completeness": 1.0,
  "sam_segment_size_cv": 0.4615271364828772,
  "sam_ontology_divergence": 0.20053605374706296
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
        "mask_r_low": 2.85,
        "mask_r_high": 3.0,
        "mask_theta_low": 1.55,
        "mask_theta_high": 17.15
      },
      "enhancing": {
        "curvature_threshold": 0.0005
      },
      "detecting": {
        "binary_threshold": 127,
        "hough_threshold_oblique": 28,
        "hough_threshold_horizontal": 30,
        "hough_threshold_vertical": 1500,
        "maxLineGap_oblique": 35,
        "pattern_tolerance": 12,
        "uniform_k_snap": true
      },
      "sam": {
        "segment_width": 1200,
        "K_height": 825.0,
        "angle": 6.1
      }
    },
    "proxy_scaled": 0.6842012527442756,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.4721520651700822,
      "sam_fill_rate": 0.6490524518014911,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.1052027439356335
    },
    "recentre_residual_max_cm": 3.2,
    "full_pipeline": false,
    "rationale": "stage1_unlocked=false and residual 3.2 cm \u226a 10 cm gate \u2192 omit unfolding, full=false. Round 1 prioritizes detection: slightly relax oblique Hough and maxLineGap toward T3 prior (30/30), keep vertical high for synthetic consistency, enable uniform_k_snap, and set SAM segment_width/K_height/angle near T3 priors (1200 / ~824 / 6.12) inside bounds. Avoid low empty-crop K_height.",
    "proposer": "Gemini-3.8 (fresh per-case agent)"
  },
  {
    "round": 2,
    "status": "ok",
    "overlay": {
      "denoising": {
        "mask_r_low": 2.84,
        "mask_r_high": 3.02,
        "mask_theta_low": 1.5,
        "mask_theta_high": 17.3
      },
      "enhancing": {
        "curvature_threshold": 0.00045
      },
      "detecting": {
        "binary_threshold": 120,
        "hough_threshold_oblique": 35,
        "hough_threshold_horizontal": 35,
        "hough_threshold_vertical": 1600,
        "maxLineGap_oblique": 25,
        "pattern_tolerance": 10,
        "uniform_k_snap": true
      },
      "sam": {
        "segment_width": 1250,
        "K_height": 880.0,
        "angle": 6.8
      }
    },
    "proxy_scaled": 0.6623952653451913,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.4351012099066825,
      "sam_fill_rate": 0.6453542220908464,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.10790127576972197
    },
    "recentre_residual_max_cm": 3.2,
    "full_pipeline": false,
    "rationale": "Distinct from round 1: keep detection moderately strict (higher oblique threshold, tighter gap) and push SAM geometry toward the measured slant and slightly taller K crop (K_height\u2248880, angle\u22486.8, segment_width\u22481250) while staying clear of empty-crop lows near 700. No unfolding; full=false.",
    "proposer": "Gemini-3.8 (fresh per-case agent)"
  },
  {
    "round": 3,
    "status": "ok",
    "overlay": {
      "denoising": {
        "mask_r_low": 2.8,
        "mask_r_high": 3.05,
        "mask_theta_low": 1.4,
        "mask_theta_high": 17.5
      },
      "enhancing": {
        "curvature_threshold": 0.0003
      },
      "detecting": {
        "binary_threshold": 110,
        "hough_threshold_oblique": 22,
        "hough_threshold_horizontal": 25,
        "hough_threshold_vertical": 1400,
        "maxLineGap_oblique": 45,
        "pattern_tolerance": 15,
        "uniform_k_snap": true
      },
      "sam": {
        "segment_width": 1150,
        "K_height": 800.0,
        "angle": 5.5
      }
    },
    "proxy_scaled": 0.7142542609670351,
    "band": "accept",
    "features": {
      "correspondence_f1@15": 0.5188145058656862,
      "sam_fill_rate": 0.6684172496469275,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.10854278966213657
    },
    "recentre_residual_max_cm": 3.2,
    "full_pipeline": false,
    "rationale": "Third distinct axis: retention/enhancement first (wider r/theta, lower curvature), aggressive oblique recovery (low Hough oblique, larger maxLineGap, lower binary threshold), then SAM with slightly narrower width, mid K_height\u2248800 (avoid empty-crop extremes), and angle\u22485.5. stage1 locked \u2192 no unfolding, full=false.",
    "proposer": "Gemini-3.8 (fresh per-case agent)"
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
`/home/boringtao/Projects/Proxy4Tun/data/sc-general/stage3/packets-gemini38/3-6/round3_proposal.json`

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
