# Gemini 3.8 reflection — subset 1-5 (propose round 3)

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

- subset: `1-5`
- family: `t1&2`
- lining_mode: `staggered`
- stage1_unlocked: `False` (residual gate 10 cm)
- arm: `gemini38` / proposer: `Gemini-3.8 (fresh per-case agent)`
- model: `inherit`

### Anchor (GT-blind)
```json
{
  "proxy_raw": 0.555111,
  "proxy_scaled": 0.555111,
  "band": "refine",
  "features": {
    "correspondence_f1@15": 0.200763,
    "sam_fill_rate": 0.729429,
    "ring_count_error": 0.0,
    "depth_nan_ratio": 0.117745
  },
  "recentre_residual_max_cm": 2.5,
  "orient_axis_corr": -0.9991614281123364,
  "ring_count": 10,
  "ring_count_error": 0.0,
  "labelmap_source": "results.pkl",
  "run_dir": "/home/boringtao/Projects/Proxy4Tun/data/bo/unified/1-5-family-proxy/runs/1-5-anchor"
}
```

### Intrinsics (GT-blind)
```json
{
  "orient_axis_corr": -0.9991614281123364,
  "orient_invariant_ok": 1.0,
  "recentre_residual_max_cm": 2.5,
  "denoise_retained_ratio": 0.7638200158043973,
  "depth_nan_ratio": 0.11774456253619453,
  "depth_outlier_ratio": 0.006866276013199325,
  "det_real_detection_ratio": 0.8,
  "det_fallback_ratio": 0.2,
  "det_n_points": 10.0,
  "sam_fill_rate": 0.7294291823548552,
  "sam_ring_completeness": 0.8888888888888888,
  "sam_segment_size_cv": 1.303208521951268,
  "sam_ontology_divergence": 0.19335931650162724
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
        "binary_threshold": 110,
        "hough_threshold_oblique": 45,
        "hough_threshold_horizontal": 45,
        "hough_threshold_vertical": 500,
        "maxLineGap_oblique": 60
      }
    },
    "proxy_scaled": 0.5491039577240833,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.1881553043604706,
      "sam_fill_rate": 0.7326783805141077,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.11774456253619453
    },
    "recentre_residual_max_cm": 2.5,
    "full_pipeline": false,
    "rationale": "Stage-1 is locked (residual 2.5 cm \u226a 10 cm gate); vertical ring columns already match (10 rings). The proxy bottleneck is staggered joint recall: more sensitive oblique/horizontal detection should explain physical seams so SAM boundaries can snap within 15 px and lift correspondence F1 without retuning unfolding.",
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
      }
    },
    "proxy_scaled": 0.6669656820715752,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.4038420259695762,
      "sam_fill_rate": 0.7364096127922651,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.12254996960196383
    },
    "recentre_residual_max_cm": 2.5,
    "full_pipeline": false,
    "rationale": "Experiences flag T1/T2 joint contrast as the causal driver for later detection, but depth_threshold_* are outside this campaign's knobs. Use enhancing (lower curvature_threshold, higher inter_radius) plus a mild denoise widen (mask_r_low\u2193, mask_r_high\u2191, softer grad_threshold) to densify joint points while leaving unfolding frozen.",
    "proposer": "Gemini-3.8 (fresh per-case agent)"
  },
  {
    "round": 3,
    "status": "ok",
    "overlay": {
      "detecting": {
        "binary_threshold": 130,
        "hough_threshold_oblique": 55,
        "hough_threshold_horizontal": 55,
        "hough_threshold_vertical": 550,
        "maxLineGap_oblique": 40
      },
      "sam": {
        "processing.y_bounds": [
          4000,
          13300
        ]
      }
    },
    "proxy_scaled": 0.6160214422998223,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.3126595576559345,
      "sam_fill_rate": 0.7285882954492633,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.11774456253619453
    },
    "recentre_residual_max_cm": 2.5,
    "full_pipeline": false,
    "rationale": "t1&2 allows flat sam.processing.y_bounds=[lo, 13300] with lo\u2208[3600,4400]. Raising lo to 4000 trims the noisy upper margin that produces unsupported red boundaries while keeping the full lower extent; modest detecting (binary 130, Hough mid, vertical 550) keeps 10-column prompts without the aggressive recall of round 1.",
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
`/home/boringtao/Projects/Proxy4Tun/data/sc-general/stage3/packets-gemini38/1-5/round3_proposal.json`

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
