# Gemini 3.8 reflection — subset 4-3 (propose round 3)

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

- subset: `4-3`
- family: `t4&5`
- lining_mode: `complex`
- stage1_unlocked: `True` (residual gate 10 cm)
- arm: `gemini38` / proposer: `Gemini-3.8 (fresh per-case agent)`
- model: `inherit`

### Anchor (GT-blind)
```json
{
  "proxy_raw": 0.520218,
  "proxy_scaled": 0.520218,
  "band": "refine",
  "features": {
    "correspondence_f1@15": 0.191402,
    "sam_fill_rate": 0.71707,
    "ring_count_error": 0.0,
    "depth_nan_ratio": 0.245204
  },
  "recentre_residual_max_cm": 23.2,
  "orient_axis_corr": 0.986044276927073,
  "ring_count": 10,
  "ring_count_error": 0.0,
  "labelmap_source": "only_label.csv",
  "run_dir": "/home/boringtao/Projects/Proxy4Tun/data/bo/unified/4-3-family-proxy/runs/4-3-anchor"
}
```

### Intrinsics (GT-blind)
```json
{
  "orient_axis_corr": 0.986044276927073,
  "orient_invariant_ok": 1.0,
  "recentre_residual_max_cm": 23.2,
  "denoise_retained_ratio": 0.7254553472672002,
  "depth_nan_ratio": 0.2452039067112422,
  "depth_outlier_ratio": 0.0009887966197817434,
  "det_real_detection_ratio": 0.6,
  "det_fallback_ratio": 0.4,
  "det_n_points": 10.0,
  "sam_fill_rate": 0.7170697542593042,
  "sam_ring_completeness": 1.0,
  "sam_segment_size_cv": 1.0756001699898754,
  "sam_ontology_divergence": 0.10079588005915159
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
        "ransac_threshold": 1.05,
        "slice_spacing_factor": 1.75,
        "polynomial_degree": 2,
        "random_seed": 3
      },
      "denoising": {
        "mask_r_low": 3.58,
        "mask_r_high": 3.95
      },
      "sam": {
        "segment_width": 1800,
        "K_height": 1227.0,
        "angle": 9.8
      }
    },
    "proxy_scaled": 0.4895528109443288,
    "band": "reject",
    "features": {
      "correspondence_f1@15": 0.12329833767352613,
      "sam_fill_rate": 0.7262288825382598,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.2256114015557184
    },
    "recentre_residual_max_cm": 4.5,
    "full_pipeline": true,
    "rationale": "R1 spends the unlocked stage-1 budget on a modest centreline retune (seed + mild RANSAC/spacing) with full=true so residual can drop, then pins SAM crops to T4 priors (segment_width\u22481800, K_height\u22481227, angle\u22489.8) so trapezoidal K/AB blocks match slanted joints without empty-crop heights.",
    "proposer": "Gemini-3.8 (fresh per-case agent)"
  },
  {
    "round": 2,
    "status": "ok",
    "overlay": {
      "detecting": {
        "binary_threshold": 120,
        "hough_threshold_oblique": 35,
        "hough_threshold_horizontal": 40,
        "hough_threshold_vertical": 5000,
        "maxLineGap_oblique": 55,
        "maxLineGap_horizontal": 12,
        "pattern_tolerance": 12
      },
      "sam": {
        "segment_width": 1900,
        "K_height": 1300.0,
        "angle": 10.5
      }
    },
    "proxy_scaled": 0.5072226096186503,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.1676184438562228,
      "sam_fill_rate": 0.7170697542593042,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.2452039067112422
    },
    "recentre_residual_max_cm": 23.2,
    "full_pipeline": false,
    "rationale": "R2 is detection-led on a frozen unroll: relax oblique Hough and widen maxLineGap to recover slanted joints, keep vertical threshold high for stable synthetic ring centres, and use a slightly wider/taller SAM crop with stronger taper (angle 10.5) so trapezoidal panels cover the orange unexplained seams without touching unfolding.",
    "proposer": "Gemini-3.8 (fresh per-case agent)"
  },
  {
    "round": 3,
    "status": "ok",
    "overlay": {
      "enhancing": {
        "curvature_threshold": 0.0004
      },
      "detecting": {
        "hough_threshold_oblique": 45,
        "hough_threshold_horizontal": 45,
        "maxLineGap_oblique": 50,
        "pattern_tolerance": 8
      },
      "sam": {
        "segment_width": 1700,
        "K_height": 1150.0,
        "angle": 8.5
      }
    },
    "proxy_scaled": 0.5156093695525675,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.1841556126898351,
      "sam_fill_rate": 0.715236189172348,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.24593536132320326
    },
    "recentre_residual_max_cm": 23.2,
    "full_pipeline": false,
    "rationale": "R3 isolates SAM crop geometry: narrower segment_width=1700 and K_height=1150 (above empty-crop risk, below oversized 1300) with angle=8.5 for gentler taper, plus mild enhancing curvature and near-prior oblique detection so local masks hug real prompt-centred panels without re-running stage-1.",
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
`/home/boringtao/Projects/Proxy4Tun/data/sc-general/stage3/packets-gemini38/4-3/round3_proposal.json`

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
