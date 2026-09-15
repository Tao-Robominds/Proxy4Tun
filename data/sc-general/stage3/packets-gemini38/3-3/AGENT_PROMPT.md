# Gemini 3.8 reflection — subset 3-3 (propose round 3)

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

- subset: `3-3`
- family: `t3`
- lining_mode: `continuous`
- stage1_unlocked: `False` (residual gate 10 cm)
- arm: `gemini38` / proposer: `Gemini-3.8 (fresh per-case agent)`
- model: `inherit`

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
        "hough_threshold_oblique": 30,
        "hough_threshold_horizontal": 30,
        "hough_threshold_vertical": 1500,
        "maxLineGap_oblique": 30,
        "pattern_tolerance": 12,
        "uniform_k_snap": true
      },
      "sam": {
        "segment_width": 1200,
        "K_height": 824.0,
        "angle": 6.12
      }
    },
    "proxy_scaled": 0.5215796595654445,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.11284116113121614,
      "sam_fill_rate": 0.7799747173013317,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.11387375767737186
    },
    "recentre_residual_max_cm": 2.7,
    "full_pipeline": false,
    "rationale": "Round-1 locks onto T3 notebook priors for SAM (segment_width=1200, K_height\u2248824 near block_height.K, angle\u22486.12) while keeping K_height well above the empty-crop floor. Denoise r/theta gates move toward T3 priors; Hough/binary stay near T3 notebook; uniform_k_snap=true for continuous lining. stage1_unlocked=false \u2192 no unfolding; full=false.",
    "proposer": "Gemini-3.8 (fresh per-case agent)"
  },
  {
    "round": 2,
    "status": "ok",
    "overlay": {
      "denoising": {
        "mask_r_low": 2.78,
        "mask_r_high": 3.05,
        "mask_theta_low": 1.3,
        "mask_theta_high": 17.8
      },
      "enhancing": {
        "curvature_threshold": 0.00035
      },
      "detecting": {
        "binary_threshold": 110,
        "hough_threshold_oblique": 22,
        "hough_threshold_horizontal": 25,
        "hough_threshold_vertical": 1200,
        "maxLineGap_oblique": 45,
        "pattern_tolerance": 16,
        "uniform_k_snap": true
      },
      "sam": {
        "segment_width": 1100,
        "K_height": 900.0,
        "angle": 5.0
      }
    },
    "proxy_scaled": 0.4859975325456736,
    "band": "reject",
    "features": {
      "correspondence_f1@15": 0.045373365966792756,
      "sam_fill_rate": 0.7892427312241329,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.11981525872782714
    },
    "recentre_residual_max_cm": 2.7,
    "full_pipeline": false,
    "rationale": "Distinct from round-1 prior-lock: detection-first recovery. Lower binary/Hough thresholds and larger maxLineGap_oblique to raise joint-line yield; looser pattern_tolerance (16) for continuous K-row snap; slightly narrower segment_width (1100) with taller K_height (900) and lower taper angle (5.0) to enlarge the K crop around the central band. Mild denoise widen + lower curvature to preserve joint contrast. No unfolding; full=false.",
    "proposer": "Gemini-3.8 (fresh per-case agent)"
  },
  {
    "round": 3,
    "status": "ok",
    "overlay": {
      "denoising": {
        "mask_r_low": 2.75,
        "mask_r_high": 3.1,
        "mask_theta_low": 1.2,
        "mask_theta_high": 18.0
      },
      "enhancing": {
        "curvature_threshold": 0.0008
      },
      "detecting": {
        "binary_threshold": 140,
        "hough_threshold_oblique": 40,
        "hough_threshold_horizontal": 40,
        "hough_threshold_vertical": 1800,
        "maxLineGap_oblique": 20,
        "pattern_tolerance": 8,
        "uniform_k_snap": true
      },
      "sam": {
        "segment_width": 1350,
        "K_height": 960.0,
        "angle": 7.5
      }
    },
    "proxy_scaled": 0.450828947051017,
    "band": "reject",
    "features": {
      "correspondence_f1@15": 0.0,
      "sam_fill_rate": 0.7430308067951582,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.10943899401377323
    },
    "recentre_residual_max_cm": 2.7,
    "full_pipeline": false,
    "rationale": "Distinct corner from rounds 1\u20132: coverage-oriented SAM \u2014 segment_width=1350, high K_height=960 (avoids empty crop), angle=7.5 toward upper taper. Detection is tightened (higher binary/Hough, smaller gap, tighter pattern_tolerance=8) to suppress spurious lines after the larger template. Denoise slightly looser on r/theta for more lining retention; curvature raised to 0.0008 to reduce soft surface clutter. stage1_unlocked=false \u2192 omit unfolding; full=false.",
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
`/home/boringtao/Projects/Proxy4Tun/data/sc-general/stage3/packets-gemini38/3-3/round3_proposal.json`

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
