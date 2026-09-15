# GPT-5.6 reflection — subset 3-4 (propose round 3)

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

- subset: `3-4`
- family: `t3`
- lining_mode: `continuous`
- stage1_unlocked: `True` (residual gate 10 cm)
- arm: `gpt56` / proposer: `GPT-5.6 (fresh per-case agent)`
- model: `gpt-5.6-sol-medium`

### Anchor (GT-blind)
```json
{
  "proxy_raw": 0.519691,
  "proxy_scaled": 0.519691,
  "band": "refine",
  "features": {
    "correspondence_f1@15": 0.243977,
    "sam_fill_rate": 0.570766,
    "ring_count_error": 0.0,
    "depth_nan_ratio": 0.194979
  },
  "recentre_residual_max_cm": 20.8,
  "orient_axis_corr": -0.9984156385609421,
  "ring_count": 10,
  "ring_count_error": 0.0,
  "labelmap_source": "results.pkl",
  "run_dir": "/home/boringtao/Projects/Proxy4Tun/data/bo/unified/3-4-family-proxy/runs/3-4-anchor"
}
```

### Intrinsics (GT-blind)
```json
{
  "orient_axis_corr": -0.9984156385609421,
  "orient_invariant_ok": 1.0,
  "recentre_residual_max_cm": 20.8,
  "denoise_retained_ratio": 0.6936518019734892,
  "depth_nan_ratio": 0.19497856422227988,
  "depth_outlier_ratio": 0.0007883432849587916,
  "det_real_detection_ratio": 0.0,
  "det_fallback_ratio": 1.0,
  "det_n_points": 10.0,
  "sam_fill_rate": 0.5707661034176089,
  "sam_ring_completeness": 0.8888888888888888,
  "sam_segment_size_cv": 0.6606793479372685,
  "sam_ontology_divergence": 0.1918493785939529
}
```

### Prior rounds (this arm only)
```json
[
  {
    "round": 1,
    "status": "ok",
    "overlay": {
      "unfolding": {
        "ransac_threshold": 0.9,
        "slice_spacing_factor": 1.08,
        "polynomial_degree": 3,
        "random_seed": 0
      },
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
        "binary_threshold": 120,
        "hough_threshold_oblique": 25,
        "hough_threshold_horizontal": 30,
        "hough_threshold_vertical": 1500,
        "maxLineGap_oblique": 40,
        "pattern_tolerance": 10,
        "uniform_k_snap": true
      },
      "sam": {
        "segment_width": 1200,
        "K_height": 823.8,
        "angle": 6.12
      }
    },
    "proxy_scaled": 0.2958800169572248,
    "band": "reject",
    "features": {
      "correspondence_f1@15": 0.0,
      "sam_fill_rate": 0.5881717697878287,
      "ring_count_error": 1.0,
      "depth_nan_ratio": 0.20964221860175616
    },
    "recentre_residual_max_cm": 12.8,
    "full_pipeline": true,
    "rationale": "Use a denser slice factor, cubic centre curve, tighter RANSAC acceptance, and a pinned seed to make the unlocked full rerun reproducible while addressing the residual. Preserve the T3 radius and theta intervals rather than widening them around an off-centre fit. Use the generic curvature prior, moderately permissive binarization/Hough settings, T3 vertical prior, a small pattern tolerance, and uniform snapping to retain ten regularly spaced prompts. Match SAM to the T3 width, K height, and taper so downstream masks are not compensating for upstream geometry.",
    "proposer": "GPT-5.6 (fresh per-case agent)"
  },
  {
    "round": 2,
    "status": "ok",
    "overlay": {
      "unfolding": {
        "ransac_threshold": 1.0,
        "slice_spacing_factor": 1.18,
        "polynomial_degree": 3,
        "random_seed": 0
      },
      "denoising": {
        "mask_r_low": 2.82,
        "mask_r_high": 3.04,
        "mask_theta_low": 1.4,
        "mask_theta_high": 17.4
      },
      "enhancing": {
        "curvature_threshold": 0.0008
      },
      "detecting": {
        "binary_threshold": 140,
        "hough_threshold_oblique": 45,
        "hough_threshold_horizontal": 50,
        "hough_threshold_vertical": 1800,
        "maxLineGap_oblique": 22,
        "pattern_tolerance": 6,
        "uniform_k_snap": true
      },
      "sam": {
        "segment_width": 1200,
        "K_height": 823.8,
        "angle": 6.12
      }
    },
    "proxy_scaled": 0.3617688238411307,
    "band": "reject",
    "features": {
      "correspondence_f1@15": 0.060627519597086746,
      "sam_fill_rate": 0.4464108753652649,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.31086424957204195
    },
    "recentre_residual_max_cm": 35.6,
    "full_pipeline": true,
    "rationale": "Keep the cubic, seeded unfolding behavior that reduced residual, but move slice_spacing_factor upward from 1.08 to 1.18 to target the original ten-ring topology and relax RANSAC threshold modestly to 1.0. Slightly broaden the T3 gates to limit residual-induced clipping. Reverse round 1's permissive detector by using stronger binary and Hough thresholds, a 22 px oblique gap, and 6 px pattern tolerance; this suppresses short upper fragments while preserving the long central red/green lines visible in the diagnostic. Keep uniform snapping and the T3 SAM geometry because fill improved and the dominant failures are ring topology and prompt-row selection.",
    "proposer": "GPT-5.6 (fresh per-case agent)"
  },
  {
    "round": 3,
    "status": "ok",
    "overlay": {
      "denoising": {
        "mask_r_low": 2.81,
        "mask_r_high": 3.04,
        "mask_theta_low": 1.45,
        "mask_theta_high": 17.35
      },
      "enhancing": {
        "curvature_threshold": 0.0004
      },
      "detecting": {
        "binary_threshold": 128,
        "hough_threshold_oblique": 32,
        "hough_threshold_horizontal": 35,
        "hough_threshold_vertical": 1500,
        "maxLineGap_oblique": 35,
        "pattern_tolerance": 14,
        "uniform_k_snap": true
      },
      "sam": {
        "segment_width": 1180,
        "K_height": 810.0,
        "angle": 6.4
      }
    },
    "proxy_scaled": 0.535336152117809,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.264087016056494,
      "sam_fill_rate": 0.5872697243044086,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.1940973525192749
    },
    "recentre_residual_max_cm": 20.8,
    "full_pipeline": false,
    "rationale": "Run stages 2-6 only from the anchor's exact ten-ring unroll. Widen the T3 radial interval by 4 cm on each side and theta modestly to recover points clipped by the anchor's 20.8 cm residual without opening the bounds aggressively. Lower curvature threshold from round 2 and return detection to balanced values between rounds 1 and 2, with enough gap bridging for the curved central seam and moderate pattern tolerance. Keep snapping enabled and adjust SAM width, K height, and taper only slightly around the observed T3 geometry, prioritizing recovery of fill and correspondence over another risky full rerun.",
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
`/home/boringtao/Projects/Proxy4Tun/data/sc-general/stage3/packets-gpt56/3-4/round3_proposal.json`

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
