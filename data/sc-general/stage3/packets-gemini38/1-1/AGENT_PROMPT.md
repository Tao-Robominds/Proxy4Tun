# Gemini 3.8 reflection — subset 1-1 (propose round 3)

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

- subset: `1-1`
- family: `t1&2`
- lining_mode: `staggered`
- stage1_unlocked: `False` (residual gate 10 cm)
- arm: `gemini38` / proposer: `Gemini-3.8 (fresh per-case agent)`
- model: `inherit`

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
      "detecting": {
        "binary_threshold": 112,
        "hough_threshold_oblique": 45,
        "hough_threshold_horizontal": 45,
        "hough_threshold_vertical": 500,
        "maxLineGap_oblique": 70
      }
    },
    "proxy_scaled": 0.604516878900438,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.28997353421679883,
      "sam_fill_rate": 0.7239358651084491,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.10736613189903915
    },
    "recentre_residual_max_cm": 2.8,
    "full_pipeline": false,
    "rationale": "Round 1 spends budget on detection-side correspondence. Keep vertical threshold near the T1 prior (500) so the 10-ring lattice stays stable, but relax oblique/horizontal thresholds and raise maxLineGap_oblique so short staggered joint segments connect across columns. Slightly lower binary_threshold to retain fainter joint pixels visible in the depth map without inventing dead knobs (depth_threshold_* is out of bounds).",
    "proposer": "Gemini-3.8 (fresh per-case agent)"
  },
  {
    "round": 2,
    "status": "ok",
    "overlay": {
      "enhancing": {
        "curvature_threshold": 0.0005,
        "inter_radius": 0.07
      },
      "sam": {
        "processing.y_bounds": [
          4100,
          13300
        ]
      }
    },
    "proxy_scaled": 0.6090758919304192,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.2994645509643856,
      "sam_fill_rate": 0.7256841404304356,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.1126744061218597
    },
    "recentre_residual_max_cm": 2.8,
    "full_pipeline": false,
    "rationale": "Distinct from round-1 Hough relaxation: leave detecting alone and retarget SAM geometry via y_bounds lower=4100 (mid-upper of allowed lo) with fixed upper 13300, while slightly increasing inter_radius and keeping curvature near the notebook default so joint enhancement still supports boundary correspondence without reopening stage-1.",
    "proposer": "Gemini-3.8 (fresh per-case agent)"
  },
  {
    "round": 3,
    "status": "ok",
    "overlay": {
      "denoising": {
        "mask_r_low": 2.3,
        "mask_r_high": 2.88,
        "z_step": 0.002,
        "grad_threshold": 0.14
      },
      "enhancing": {
        "curvature_threshold": 0.0008,
        "inter_radius": 0.075
      },
      "detecting": {
        "binary_threshold": 120,
        "hough_threshold_oblique": 50,
        "hough_threshold_horizontal": 50,
        "hough_threshold_vertical": 550,
        "maxLineGap_oblique": 55
      },
      "sam": {
        "processing.y_bounds": [
          3800,
          13300
        ]
      }
    },
    "proxy_scaled": 0.6182317099395084,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.30646071453346313,
      "sam_fill_rate": 0.739080150981285,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.10446936335762802
    },
    "recentre_residual_max_cm": 2.8,
    "full_pipeline": false,
    "rationale": "Third distinct lever: coverage-first. Soften denoise (slightly lower mask_r_low, widen mask_r_high within bounds, lower grad_threshold, modest z_step) and raise enhancing.inter_radius to rebuild left-half joint pixels. Use mid-relaxed detecting (binary 120, oblique 50, maxLineGap 55) rather than round-1's aggressive Hough, and nudge y_bounds lo to 3800 so the staggered crop still covers the denser recovered band\u2014without touching unfolding.",
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
`/home/boringtao/Projects/Proxy4Tun/data/sc-general/stage3/packets-gemini38/1-1/round3_proposal.json`

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
