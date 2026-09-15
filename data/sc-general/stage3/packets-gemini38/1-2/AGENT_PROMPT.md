# Gemini 3.8 reflection — subset 1-2 (propose round 3)

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

- subset: `1-2`
- family: `t1&2`
- lining_mode: `staggered`
- stage1_unlocked: `False` (residual gate 10 cm)
- arm: `gemini38` / proposer: `Gemini-3.8 (fresh per-case agent)`
- model: `inherit`

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
      "detecting": {
        "binary_threshold": 115,
        "hough_threshold_oblique": 45,
        "hough_threshold_horizontal": 50,
        "hough_threshold_vertical": 500,
        "maxLineGap_oblique": 70
      },
      "sam": {
        "processing.y_bounds": [
          3900,
          13300
        ]
      }
    },
    "proxy_scaled": 0.5852408076121618,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.25420479403208524,
      "sam_fill_rate": 0.7204390179674258,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.10150520930740327
    },
    "recentre_residual_max_cm": 3.5,
    "full_pipeline": false,
    "rationale": "Relax oblique Hough and widen maxLineGap to reconnect staggered joint fragments, lightly drop binary_threshold for more joint pixels, and set y_bounds lower mid-band so K/AB crops stay on lining. Goal: raise real detections and F1@15 without changing stage-1 geometry.",
    "proposer": "Gemini-3.8 (fresh per-case agent)"
  },
  {
    "round": 2,
    "status": "ok",
    "overlay": {
      "denoising": {
        "mask_r_low": 2.35,
        "mask_r_high": 2.85,
        "z_step": 0.002,
        "grad_threshold": 0.15
      },
      "enhancing": {
        "curvature_threshold": 0.0004,
        "inter_radius": 0.07
      },
      "detecting": {
        "binary_threshold": 120,
        "hough_threshold_oblique": 55,
        "hough_threshold_horizontal": 55,
        "hough_threshold_vertical": 550,
        "maxLineGap_oblique": 50
      },
      "sam": {
        "processing.y_bounds": [
          4000,
          13300
        ]
      }
    },
    "proxy_scaled": 0.6796548316864679,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.42558385409814203,
      "sam_fill_rate": 0.7287001256068735,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.10856340587659198
    },
    "recentre_residual_max_cm": 3.5,
    "full_pipeline": false,
    "rationale": "Strengthen the joint cloud first so staggered seams become Hough-visible under mid thresholds; slight mask widening and finer z_step reduce fringe holes that break continuity. Distinct from R1's detection-only relax.",
    "proposer": "Gemini-3.8 (fresh per-case agent)"
  },
  {
    "round": 3,
    "status": "ok",
    "overlay": {
      "denoising": {
        "mask_r_low": 2.4,
        "mask_r_high": 2.8,
        "z_step": 0.0015,
        "grad_threshold": 0.18
      },
      "enhancing": {
        "curvature_threshold": 0.0006,
        "inter_radius": 0.05
      },
      "detecting": {
        "binary_threshold": 135,
        "hough_threshold_oblique": 70,
        "hough_threshold_horizontal": 65,
        "hough_threshold_vertical": 650,
        "maxLineGap_oblique": 30
      },
      "sam": {
        "processing.y_bounds": [
          4300,
          13300
        ]
      }
    },
    "proxy_scaled": 0.6995369815636407,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.4597569000596479,
      "sam_fill_rate": 0.7266200883219047,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.10000446692095138
    },
    "recentre_residual_max_cm": 3.5,
    "full_pipeline": false,
    "rationale": "Shift the SAM axial window upward into the lining band and suppress spurious fringe joints so edge rings receive real prompts and supported (green/cyan) boundaries rise. Opposite detection polarity from R1; stronger y_bounds move than R2.",
    "proposer": "Gemini-3.8 (fresh per-case agent)"
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
`/home/boringtao/Projects/Proxy4Tun/data/sc-general/stage3/packets-gemini38/1-2/round3_proposal.json`

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
