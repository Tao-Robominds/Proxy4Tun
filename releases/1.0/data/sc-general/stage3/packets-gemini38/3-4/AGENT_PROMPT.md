# Gemini 3.8 reflection — subset 3-4 (propose round 3)

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

- subset: `3-4`
- family: `t3`
- lining_mode: `continuous`
- stage1_unlocked: `True` (residual gate 10 cm)
- arm: `gemini38` / proposer: `Gemini-3.8 (fresh per-case agent)`
- model: `inherit`

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
        "ransac_threshold": 1.05,
        "slice_spacing_factor": 1.1,
        "polynomial_degree": 3,
        "random_seed": 3
      },
      "sam": {
        "segment_width": 1200,
        "K_height": 850.0,
        "angle": 6.12
      }
    },
    "proxy_scaled": 0.553373801139945,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.45579955921949944,
      "sam_fill_rate": 0.58484732986067,
      "ring_count_error": 1.0,
      "depth_nan_ratio": 0.16451926261320376
    },
    "recentre_residual_max_cm": 6.3,
    "full_pipeline": true,
    "rationale": "Round-1 modest move: denser ellipse sampling (slice_spacing_factor 1.10), slightly more permissive RANSAC (1.05), cubic centreline (polynomial_degree 3), and a fresh seed (3) to shrink the 20.8 cm residual under --full; keep SAM at T3 mid-priors (segment_width 1200, K_height 850, angle 6.12) so geometry stays mid-range and is not the lever while stage-1 is reopened.",
    "proposer": "Gemini-3.8 (fresh per-case agent)"
  },
  {
    "round": 2,
    "status": "ok",
    "overlay": {
      "detecting": {
        "binary_threshold": 125,
        "hough_threshold_oblique": 26,
        "hough_threshold_horizontal": 26,
        "hough_threshold_vertical": 2200,
        "maxLineGap_oblique": 40,
        "pattern_tolerance": 8,
        "uniform_k_snap": true
      },
      "sam": {
        "segment_width": 1100,
        "K_height": 780.0,
        "angle": 5.5
      }
    },
    "proxy_scaled": 0.5628837406360391,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.31174663137373765,
      "sam_fill_rate": 0.5935035785372464,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.19497856422227988
    },
    "recentre_residual_max_cm": 20.8,
    "full_pipeline": false,
    "rationale": "Round-2 distinct from R1 unfolding: keep full=false and omit unfolding. Raise hough_threshold_vertical to 2200 (within [800,2500]; experiences used 5000) to suppress the extra vertical/prompt, keep uniform_k_snap on for continuous, modestly tighten pattern_tolerance and ease oblique/horizontal slightly so joint tracks cover the right side; shift SAM from R1 mid-priors toward slightly narrower segment_width and lower K_height/angle to re-align the K band without extreme crops.",
    "proposer": "Gemini-3.8 (fresh per-case agent)"
  },
  {
    "round": 3,
    "status": "ok",
    "overlay": {
      "enhancing": {
        "curvature_threshold": 0.0006
      },
      "detecting": {
        "binary_threshold": 115,
        "hough_threshold_oblique": 30,
        "hough_threshold_horizontal": 30,
        "hough_threshold_vertical": 2400,
        "maxLineGap_oblique": 30,
        "pattern_tolerance": 12,
        "uniform_k_snap": true
      },
      "sam": {
        "segment_width": 1250,
        "K_height": 900.0,
        "angle": 6.5
      }
    },
    "proxy_scaled": 0.4529436081348239,
    "band": "reject",
    "features": {
      "correspondence_f1@15": 0.13684119503653425,
      "sam_fill_rate": 0.5388006606530301,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.19278155051994858
    },
    "recentre_residual_max_cm": 20.8,
    "full_pipeline": false,
    "rationale": "Round-3 distinct hybrid: full=false (no unfolding). Hold ring count with vertical Hough 2400 (above R2's 2200), return oblique/horizontal/maxLineGap to T3 priors (~30) and loosen pattern_tolerance to 12 so joint spacing can recover F1 without inviting an 11th prompt; add enhancing.curvature_threshold=0.0006 (untouched in R1/R2) to sharpen joints; move SAM opposite R2's narrow/low crop toward slightly wider priors (segment_width 1250, K_height 900, angle 6.5) to re-align boundaries to the sloping K band while staying mid-range.",
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
`/home/boringtao/Projects/Proxy4Tun/data/sc-general/stage3/packets-gemini38/3-4/round3_proposal.json`

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
