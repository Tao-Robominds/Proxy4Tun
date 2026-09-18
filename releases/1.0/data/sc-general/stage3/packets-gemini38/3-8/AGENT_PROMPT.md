# Gemini 3.8 reflection — subset 3-8 (propose round 3)

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

- subset: `3-8`
- family: `t3`
- lining_mode: `continuous`
- stage1_unlocked: `True` (residual gate 10 cm)
- arm: `gemini38` / proposer: `Gemini-3.8 (fresh per-case agent)`
- model: `inherit`

### Anchor (GT-blind)
```json
{
  "proxy_raw": 0.561281,
  "proxy_scaled": 0.561281,
  "band": "refine",
  "features": {
    "correspondence_f1@15": 0.302212,
    "sam_fill_rate": 0.59695,
    "ring_count_error": 0.0,
    "depth_nan_ratio": 0.182088
  },
  "recentre_residual_max_cm": 24.0,
  "orient_axis_corr": 0.9995216099864935,
  "ring_count": 10,
  "ring_count_error": 0.0,
  "labelmap_source": "results.pkl",
  "run_dir": "/home/boringtao/Projects/Proxy4Tun/data/bo/unified/3-8-family-proxy/runs/3-8-anchor"
}
```

### Intrinsics (GT-blind)
```json
{
  "orient_axis_corr": 0.9995216099864935,
  "orient_invariant_ok": 1.0,
  "recentre_residual_max_cm": 24.0,
  "denoise_retained_ratio": 0.7258077773485341,
  "depth_nan_ratio": 0.18208811279684348,
  "depth_outlier_ratio": 0.0008981363284279751,
  "det_real_detection_ratio": 0.0,
  "det_fallback_ratio": 1.0,
  "det_n_points": 10.0,
  "sam_fill_rate": 0.596949720945907,
  "sam_ring_completeness": 0.8888888888888888,
  "sam_segment_size_cv": 0.6767146840216215,
  "sam_ontology_divergence": 0.19893838940867875
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
        "random_seed": 2,
        "ransac_threshold": 0.95,
        "slice_spacing_factor": 1.12,
        "polynomial_degree": 2
      }
    },
    "proxy_scaled": 0.5614595937038465,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.44941629503771824,
      "sam_fill_rate": 0.5913028826000115,
      "ring_count_error": 1.0,
      "depth_nan_ratio": 0.11714402542609148
    },
    "recentre_residual_max_cm": 2.2,
    "full_pipeline": true,
    "rationale": "R1 is a modest stage-1 probe only: alternate random_seed with slightly tighter ransac_threshold and mild slice densification (polynomial_degree stays 2). No denoise widen (residual mimics over-gating). Downstream knobs deferred until residual is addressed; full=true required because unfolding is touched.",
    "proposer": "Gemini-3.8 (fresh per-case agent)"
  },
  {
    "round": 2,
    "status": "ok",
    "overlay": {
      "denoising": {
        "mask_r_low": 2.82,
        "mask_r_high": 3.05,
        "mask_theta_low": 1.4,
        "mask_theta_high": 17.3
      },
      "enhancing": {
        "curvature_threshold": 0.0007
      },
      "detecting": {
        "binary_threshold": 118,
        "hough_threshold_oblique": 28,
        "hough_threshold_horizontal": 28,
        "hough_threshold_vertical": 1600,
        "maxLineGap_oblique": 42,
        "pattern_tolerance": 12,
        "uniform_k_snap": true
      },
      "sam": {
        "segment_width": 1220,
        "K_height": 880.0,
        "angle": 6.2
      }
    },
    "proxy_scaled": 0.5406201688144624,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.2642345086064329,
      "sam_fill_rate": 0.594755098182655,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.17878995760582916
    },
    "recentre_residual_max_cm": 24.0,
    "full_pipeline": false,
    "rationale": "No unfolding (full=false). Align denoise r/theta near T3 priors; lower binary and oblique/horizontal Hough with slightly larger maxLineGap to explain more central joint pixels; keep uniform_k_snap and mid vertical threshold. SAM: segment_width=1220, K_height=880 (mid-band, not 700 empty-crop risk), angle=6.2 near T3 taper 6.12\u00b0.",
    "proposer": "Gemini-3.8 (fresh per-case agent)"
  },
  {
    "round": 3,
    "status": "ok",
    "overlay": {
      "denoising": {
        "mask_r_low": 2.88,
        "mask_r_high": 3.08,
        "mask_theta_low": 1.55,
        "mask_theta_high": 17.0
      },
      "enhancing": {
        "curvature_threshold": 0.00045
      },
      "detecting": {
        "binary_threshold": 135,
        "hough_threshold_oblique": 40,
        "hough_threshold_horizontal": 38,
        "hough_threshold_vertical": 1800,
        "maxLineGap_oblique": 30,
        "pattern_tolerance": 15,
        "uniform_k_snap": true
      },
      "sam": {
        "segment_width": 1300,
        "K_height": 940.0,
        "angle": 7.0
      }
    },
    "proxy_scaled": 0.484367686282144,
    "band": "reject",
    "features": {
      "correspondence_f1@15": 0.16199376354536454,
      "sam_fill_rate": 0.5836340322699961,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.16613117139174102
    },
    "recentre_residual_max_cm": 24.0,
    "full_pipeline": false,
    "rationale": "Stages 2\u20136 only (full=false). Slightly tighter denoise and higher binary/Hough than R2 to cut orange unexplained clutter; pattern_tolerance a bit looser for continuous snap. SAM alternative: wider segment_width=1300, K_height=940 (still inside bounds, away from empty-crop floor), angle=7.0 to follow the observed K-row slope.",
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
`/home/boringtao/Projects/Proxy4Tun/data/sc-general/stage3/packets-gemini38/3-8/round3_proposal.json`

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
