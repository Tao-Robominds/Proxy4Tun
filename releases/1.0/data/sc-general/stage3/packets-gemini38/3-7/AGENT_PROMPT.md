# Gemini 3.8 reflection — subset 3-7 (propose round 3)

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

- subset: `3-7`
- family: `t3`
- lining_mode: `continuous`
- stage1_unlocked: `False` (residual gate 10 cm)
- arm: `gemini38` / proposer: `Gemini-3.8 (fresh per-case agent)`
- model: `inherit`

### Anchor (GT-blind)
```json
{
  "proxy_raw": 0.539694,
  "proxy_scaled": 0.539694,
  "band": "refine",
  "features": {
    "correspondence_f1@15": 0.171748,
    "sam_fill_rate": 0.766799,
    "ring_count_error": 0.0,
    "depth_nan_ratio": 0.164506
  },
  "recentre_residual_max_cm": 3.6,
  "orient_axis_corr": -0.9991211319489915,
  "ring_count": 10,
  "ring_count_error": 0.0,
  "labelmap_source": "results.pkl",
  "run_dir": "/home/boringtao/Projects/Proxy4Tun/data/bo/unified/3-7-family-proxy/runs/3-7-anchor"
}
```

### Intrinsics (GT-blind)
```json
{
  "orient_axis_corr": -0.9991211319489915,
  "orient_invariant_ok": 1.0,
  "recentre_residual_max_cm": 3.6,
  "denoise_retained_ratio": 0.7976920114616173,
  "depth_nan_ratio": 0.16450624232718375,
  "depth_outlier_ratio": 0.000299478779485916,
  "det_real_detection_ratio": 0.0,
  "det_fallback_ratio": 1.0,
  "det_n_points": 10.0,
  "sam_fill_rate": 0.7667991671398826,
  "sam_ring_completeness": 1.0,
  "sam_segment_size_cv": 0.6717568636337622,
  "sam_ontology_divergence": 0.24785280773585067
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
        "binary_threshold": 120,
        "hough_threshold_oblique": 28,
        "hough_threshold_horizontal": 28,
        "hough_threshold_vertical": 1500,
        "maxLineGap_oblique": 35,
        "pattern_tolerance": 12,
        "uniform_k_snap": true
      },
      "sam": {
        "segment_width": 1200,
        "K_height": 824.0,
        "angle": 6.1
      }
    },
    "proxy_scaled": 0.555607812361023,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.20092533657889042,
      "sam_fill_rate": 0.7666947332693675,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.16450624232718375
    },
    "recentre_residual_max_cm": 3.6,
    "full_pipeline": false,
    "rationale": "Round-1 detection-first: lower Hough oblique/horizontal toward T3 notebook priors and widen maxLineGap so more real joint ticks appear across rings; keep uniform_k_snap on for continuous; pin SAM to T3 K\u2248824 / width 1200 / angle\u22486.1 (mid-band, not empty-crop extremes). Mild denoise theta toward T3 prior; leave curvature near default. No unfolding (stage1_unlocked=false).",
    "proposer": "Gemini-3.8 (fresh per-case agent)"
  },
  {
    "round": 2,
    "status": "ok",
    "overlay": {
      "denoising": {
        "mask_r_low": 2.8,
        "mask_r_high": 3.05,
        "mask_theta_low": 1.4,
        "mask_theta_high": 17.5
      },
      "enhancing": {
        "curvature_threshold": 0.00045
      },
      "detecting": {
        "binary_threshold": 130,
        "hough_threshold_oblique": 35,
        "hough_threshold_horizontal": 32,
        "hough_threshold_vertical": 1600,
        "maxLineGap_oblique": 28,
        "pattern_tolerance": 10,
        "uniform_k_snap": true
      },
      "sam": {
        "segment_width": 1280,
        "K_height": 880.0,
        "angle": 7.5
      }
    },
    "proxy_scaled": 0.5209495501687984,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.13400855628171573,
      "sam_fill_rate": 0.7758065884718062,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.16723991792048334
    },
    "recentre_residual_max_cm": 3.6,
    "full_pipeline": false,
    "rationale": "Round-2 SAM-geometry focus distinct from round-1: slightly wider segment_width (1280), modestly taller but still filled K_height (880), stronger taper angle (7.5\u00b0) to follow the observed green/red joint slopes. Detection kept stricter than round-1 (higher Hough thresholds, tighter gap) so extra width does not invite spurious lines. Denoise r-band slightly looser on the outer side for coverage; curvature unchanged mid. full=false, no unfolding.",
    "proposer": "Gemini-3.8 (fresh per-case agent)"
  },
  {
    "round": 3,
    "status": "ok",
    "overlay": {
      "denoising": {
        "mask_r_low": 2.88,
        "mask_r_high": 3.02,
        "mask_theta_low": 1.8,
        "mask_theta_high": 16.5
      },
      "enhancing": {
        "curvature_threshold": 0.0003
      },
      "detecting": {
        "binary_threshold": 110,
        "hough_threshold_oblique": 22,
        "hough_threshold_horizontal": 24,
        "hough_threshold_vertical": 1400,
        "maxLineGap_oblique": 45,
        "pattern_tolerance": 16,
        "uniform_k_snap": true
      },
      "sam": {
        "segment_width": 1080,
        "K_height": 780.0,
        "angle": 5.0
      }
    },
    "proxy_scaled": 0.5068091613596719,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.1264480388600135,
      "sam_fill_rate": 0.7419177974896708,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.17120173690435683
    },
    "recentre_residual_max_cm": 3.6,
    "full_pipeline": false,
    "rationale": "Round-3 joint-enhancement path: lower curvature_threshold and binary_threshold to densify joint pixels; more permissive oblique Hough (threshold 22, maxLineGap 45) with looser pattern_tolerance (16). SAM uses compact segment_width 1080, K_height 780 (near lower filled prior, not empty), milder angle 5.0\u00b0. Slightly tighter theta gate to cut floor clutter. Distinct from round-1 (prior-pinned SAM + mid Hough) and round-2 (wide/tall/strong-taper SAM).",
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
`/home/boringtao/Projects/Proxy4Tun/data/sc-general/stage3/packets-gemini38/3-7/round3_proposal.json`

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
