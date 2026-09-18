# GPT-5.6 reflection — subset 1-1 (propose round 3)

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

- subset: `1-1`
- family: `t1&2`
- lining_mode: `staggered`
- stage1_unlocked: `False` (residual gate 10 cm)
- arm: `gpt56` / proposer: `GPT-5.6 (fresh per-case agent)`
- model: `gpt-5.6-sol-medium`

### Anchor (GT-blind)
```json
{
  "proxy_raw": 0.606657,
  "proxy_scaled": 0.606657,
  "band": "refine",
  "features": {
    "correspondence_f1@15": 0.29438,
    "sam_fill_rate": 0.722949,
    "ring_count_error": 0.0,
    "depth_nan_ratio": 0.107366
  },
  "recentre_residual_max_cm": 2.8,
  "orient_axis_corr": -0.999934241125118,
  "ring_count": 10,
  "ring_count_error": 0.0,
  "labelmap_source": "results.pkl",
  "run_dir": "/home/boringtao/Projects/Proxy4Tun/data/anchors/1-1"
}
```

### Intrinsics (GT-blind)
```json
{
  "orient_axis_corr": -0.999934241125118,
  "orient_invariant_ok": 1.0,
  "recentre_residual_max_cm": 2.8,
  "denoise_retained_ratio": 0.7531270323506135,
  "depth_nan_ratio": 0.10736613189903915,
  "depth_outlier_ratio": 0.0032266563656320134,
  "det_real_detection_ratio": 0.7,
  "det_fallback_ratio": 0.3,
  "det_n_points": 10.0,
  "sam_fill_rate": 0.7229494457484911,
  "sam_ring_completeness": 0.8888888888888888,
  "sam_segment_size_cv": 1.2876045298188923,
  "sam_ontology_divergence": 0.21232044530496946
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
        "grad_threshold": 0.18
      },
      "enhancing": {
        "curvature_threshold": 0.0015,
        "inter_radius": 0.05
      },
      "detecting": {
        "binary_threshold": 115,
        "hough_threshold_oblique": 45,
        "hough_threshold_horizontal": 45,
        "hough_threshold_vertical": 650,
        "maxLineGap_oblique": 70
      },
      "sam": {
        "processing.y_bounds": [
          4000,
          13300
        ]
      }
    },
    "proxy_scaled": 0.5703690479040527,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.22927916961579253,
      "sam_fill_rate": 0.7235966862118074,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.11167673249457637
    },
    "recentre_residual_max_cm": 2.8,
    "full_pipeline": false,
    "rationale": "Lower horizontal and oblique Hough thresholds together with a larger oblique line gap should connect the visible staggered seams. A moderately permissive binary threshold and enhancement settings expose faint joint responses without changing the already-correct unfolding or aggressively relaxing the vertical detector. The flat SAM y-bound keeps processing bounded while allowing broader support for prompt-driven segmentation.",
    "proposer": "GPT-5.6 (fresh per-case agent)"
  },
  {
    "round": 2,
    "status": "ok",
    "overlay": {
      "denoising": {
        "grad_threshold": 0.12
      },
      "enhancing": {
        "curvature_threshold": 0.006,
        "inter_radius": 0.025
      },
      "detecting": {
        "binary_threshold": 150,
        "hough_threshold_oblique": 85,
        "hough_threshold_horizontal": 80,
        "hough_threshold_vertical": 700,
        "maxLineGap_oblique": 25
      },
      "sam": {
        "processing.y_bounds": [
          3800,
          13300
        ]
      }
    },
    "proxy_scaled": 0.6039612659737986,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.29060780937802155,
      "sam_fill_rate": 0.7194860869231495,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.10589871882445359
    },
    "recentre_residual_max_cm": 2.8,
    "full_pipeline": false,
    "rationale": "This overlay tests the opposite detection regime from round 1. Higher binary and Hough thresholds reject weak texture responses, while a short oblique gap prevents disconnected marks from becoming joint lines. A higher curvature threshold and smaller interaction radius restrict enhancement to sharper local seams. The denoising gradient threshold is reduced to suppress residual fine texture, and the lower SAM bound is moved modestly from 4000 to 3800 without changing the fixed upper bound.",
    "proposer": "GPT-5.6 (fresh per-case agent)"
  },
  {
    "round": 3,
    "status": "ok",
    "overlay": {
      "denoising": {
        "grad_threshold": 0.115
      },
      "enhancing": {
        "curvature_threshold": 0.0055,
        "inter_radius": 0.03
      },
      "detecting": {
        "binary_threshold": 148,
        "hough_threshold_oblique": 88,
        "hough_threshold_horizontal": 75,
        "hough_threshold_vertical": 720,
        "maxLineGap_oblique": 28
      },
      "sam": {
        "processing.y_bounds": [
          3600,
          13300
        ]
      }
    },
    "proxy_scaled": 0.6008541375590224,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.28504705276800124,
      "sam_fill_rate": 0.7193424285831346,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.10604293814713965
    },
    "recentre_residual_max_cm": 2.8,
    "full_pipeline": false,
    "rationale": "The proposal stays close to the successful round-2 regime but separates horizontal from oblique behavior. A slightly lower horizontal Hough threshold can recover strong cross-joints, while a higher oblique threshold and short line gap continue rejecting disconnected texture. Minor enhancement and binary adjustments soften the conservative cutoff without returning to round-1 permissiveness. Keeping the low denoising gradient threshold protects the improved NaN ratio, and moving the flat SAM lower bound to 3600 aims to recover the small fill deficit.",
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
`/home/boringtao/Projects/Proxy4Tun/data/sc-general/stage3/packets-gpt56/1-1/round3_proposal.json`

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
