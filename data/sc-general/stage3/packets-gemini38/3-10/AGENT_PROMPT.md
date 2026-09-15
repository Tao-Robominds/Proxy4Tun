# Gemini 3.8 reflection — subset 3-10 (propose round 3)

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

- subset: `3-10`
- family: `t3`
- lining_mode: `continuous`
- stage1_unlocked: `True` (residual gate 10 cm)
- arm: `gemini38` / proposer: `Gemini-3.8 (fresh per-case agent)`
- model: `inherit`

### Anchor (GT-blind)
```json
{
  "proxy_raw": 0.588697,
  "proxy_scaled": 0.588697,
  "band": "refine",
  "features": {
    "correspondence_f1@15": 0.287265,
    "sam_fill_rate": 0.697553,
    "ring_count_error": 0.0,
    "depth_nan_ratio": 0.142028
  },
  "recentre_residual_max_cm": 10.2,
  "orient_axis_corr": -0.9990592937874491,
  "ring_count": 10,
  "ring_count_error": 0.0,
  "labelmap_source": "results.pkl",
  "run_dir": "/home/boringtao/Projects/Proxy4Tun/data/bo/unified/3-10-family-proxy/runs/3-10-anchor"
}
```

### Intrinsics (GT-blind)
```json
{
  "orient_axis_corr": -0.9990592937874491,
  "orient_invariant_ok": 1.0,
  "recentre_residual_max_cm": 10.2,
  "denoise_retained_ratio": 0.7404734761200185,
  "depth_nan_ratio": 0.14202755710717666,
  "depth_outlier_ratio": 0.0008614399729785715,
  "det_real_detection_ratio": 0.0,
  "det_fallback_ratio": 1.0,
  "det_n_points": 10.0,
  "sam_fill_rate": 0.697552574768962,
  "sam_ring_completeness": 1.0,
  "sam_segment_size_cv": 0.5772969297747274,
  "sam_ontology_divergence": 0.2235725711106475
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
        "ransac_threshold": 0.95,
        "slice_spacing_factor": 1.15,
        "polynomial_degree": 2,
        "random_seed": 3
      },
      "denoising": {
        "mask_r_low": 2.82,
        "mask_r_high": 3.05,
        "mask_theta_low": 1.4,
        "mask_theta_high": 17.5
      },
      "enhancing": {
        "curvature_threshold": 0.0004
      },
      "sam": {
        "segment_width": 1200,
        "K_height": 824.0,
        "angle": 6.1
      }
    },
    "proxy_scaled": 0.5176943165226883,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.4023431917553809,
      "sam_fill_rate": 0.547351654659972,
      "ring_count_error": 1.0,
      "depth_nan_ratio": 0.14670479549124602
    },
    "recentre_residual_max_cm": 4.7,
    "full_pipeline": true,
    "rationale": "stage1_unlocked with residual just over gate justifies a full stages-1\u20136 replay. Slightly tighten RANSAC, keep degree-2, and change random_seed to re-fit the centre curve; set slice_spacing_factor mid-band. Widen T3 r/theta gates modestly toward prior outer coverage to raise retention without hole-fill. Hold SAM at T3-prior mid values (segment_width=1200, K_height\u2248824, angle\u22486.1) \u2014 avoid empty-crop K_height extremes.",
    "proposer": "Gemini-3.8 (fresh per-case agent)"
  },
  {
    "round": 2,
    "status": "ok",
    "overlay": {
      "denoising": {
        "mask_r_low": 2.85,
        "mask_r_high": 3.0,
        "mask_theta_low": 1.55,
        "mask_theta_high": 17.2
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
        "segment_width": 1180,
        "K_height": 850.0,
        "angle": 6.5
      }
    },
    "proxy_scaled": 0.605958085326715,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.3199996344655763,
      "sam_fill_rate": 0.6968612802289762,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.14413438773670448
    },
    "recentre_residual_max_cm": 10.2,
    "full_pipeline": false,
    "rationale": "Relax oblique/horizontal Hough and raise maxLineGap_oblique so continuous joint tracks survive binarisation; keep vertical threshold at T3-like 1500 given ring_count already matches. Enable uniform_k_snap with moderate pattern_tolerance. Nudge SAM angle slightly above T3 prior (6.5\u00b0) and K_height to mid-band 850 (not floor/ceiling) with segment_width\u22481180 to better seat crops on the tracked K strip without empty crops. Leave unfolding frozen (full=false).",
    "proposer": "Gemini-3.8 (fresh per-case agent)"
  },
  {
    "round": 3,
    "status": "ok",
    "overlay": {
      "enhancing": {
        "curvature_threshold": 0.00035
      },
      "detecting": {
        "binary_threshold": 130,
        "hough_threshold_oblique": 32,
        "hough_threshold_horizontal": 30,
        "maxLineGap_oblique": 30,
        "pattern_tolerance": 8,
        "uniform_k_snap": true
      },
      "sam": {
        "segment_width": 1280,
        "K_height": 880.0,
        "angle": 7.2
      }
    },
    "proxy_scaled": 0.5785721113368258,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.2730731615462832,
      "sam_fill_rate": 0.6921192422441603,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.146356263284766
    },
    "recentre_residual_max_cm": 10.2,
    "full_pipeline": false,
    "rationale": "Distinct from rounds 1\u20132: hold denoise near defaults and focus on SAM seating. Widen segment_width to 1280 so crops cover the textured K strip; set K_height=880 (mid-high, not 700/1000 empty-crop poles); raise angle to 7.2\u00b0 to match visible oblique taper. Support with slightly stricter binary_threshold and tighter pattern_tolerance plus uniform_k_snap so prompts stay on the continuous K-row. full=false (no unfolding).",
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
`/home/boringtao/Projects/Proxy4Tun/data/sc-general/stage3/packets-gemini38/3-10/round3_proposal.json`

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
