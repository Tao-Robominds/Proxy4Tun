# Gemini 3.8 reflection — subset 1-3 (propose round 3)

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

- subset: `1-3`
- family: `t1&2`
- lining_mode: `staggered`
- stage1_unlocked: `False` (residual gate 10 cm)
- arm: `gemini38` / proposer: `Gemini-3.8 (fresh per-case agent)`
- model: `inherit`

### Anchor (GT-blind)
```json
{
  "proxy_raw": 0.550144,
  "proxy_scaled": 0.550144,
  "band": "refine",
  "features": {
    "correspondence_f1@15": 0.186826,
    "sam_fill_rate": 0.732531,
    "ring_count_error": 0.0,
    "depth_nan_ratio": 0.109033
  },
  "recentre_residual_max_cm": 1.4,
  "orient_axis_corr": 0.9999842336199495,
  "ring_count": 10,
  "ring_count_error": 0.0,
  "labelmap_source": "results.pkl",
  "run_dir": "/home/boringtao/Projects/Proxy4Tun/data/bo/unified/1-3-family-proxy/runs/1-3-anchor"
}
```

### Intrinsics (GT-blind)
```json
{
  "orient_axis_corr": 0.9999842336199495,
  "orient_invariant_ok": 1.0,
  "recentre_residual_max_cm": 1.4,
  "denoise_retained_ratio": 0.7653250403055444,
  "depth_nan_ratio": 0.10903285620918383,
  "depth_outlier_ratio": 0.0042008620385453254,
  "det_real_detection_ratio": 0.9,
  "det_fallback_ratio": 0.1,
  "det_n_points": 10.0,
  "sam_fill_rate": 0.7325314614464593,
  "sam_ring_completeness": 0.8888888888888888,
  "sam_segment_size_cv": 1.3403191091625246,
  "sam_ontology_divergence": 0.2507391898933104
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
        "mask_r_low": 2.35,
        "mask_r_high": 2.82,
        "z_step": 0.002,
        "grad_threshold": 0.18
      },
      "enhancing": {
        "curvature_threshold": 0.0008,
        "inter_radius": 0.055
      },
      "detecting": {
        "binary_threshold": 120,
        "hough_threshold_oblique": 48,
        "hough_threshold_horizontal": 48,
        "hough_threshold_vertical": 520,
        "maxLineGap_oblique": 50
      },
      "sam": {
        "processing.y_bounds": [
          3900,
          13300
        ]
      }
    },
    "proxy_scaled": 0.6759078166399262,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.41883285627253297,
      "sam_fill_rate": 0.7358194900166267,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.11815415821501014
    },
    "recentre_residual_max_cm": 1.4,
    "full_pipeline": false,
    "rationale": "Balanced multi-stage overlay: slightly densify joint enhancement, gently lower oblique/horizontal Hough thresholds and widen maxLineGap so staggered seams are more complete without flooding the white-seam artifact, keep vertical Hough near the T1 prior (500), and set sam.processing.y_bounds lower mid-band [3900,13300] to better frame the staggered template crop. Mild denoise grad/z_step tweak to keep retention while sharpening edges. Expected proxy lift via correspondence_f1 without sacrificing fill/ring count.",
    "proposer": "Gemini-3.8 (fresh per-case agent)"
  },
  {
    "round": 2,
    "status": "ok",
    "overlay": {
      "denoising": {
        "mask_r_low": 2.45,
        "mask_r_high": 2.8,
        "z_step": 0.0015,
        "grad_threshold": 0.22
      },
      "enhancing": {
        "curvature_threshold": 0.0012,
        "inter_radius": 0.045
      },
      "detecting": {
        "binary_threshold": 140,
        "hough_threshold_oblique": 65,
        "hough_threshold_horizontal": 70,
        "hough_threshold_vertical": 600,
        "maxLineGap_oblique": 30
      },
      "sam": {
        "processing.y_bounds": [
          4200,
          13300
        ]
      }
    },
    "proxy_scaled": 0.69214976956429,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.44772616601708215,
      "sam_fill_rate": 0.7316701734767447,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.11053294557259523
    },
    "recentre_residual_max_cm": 1.4,
    "full_pipeline": false,
    "rationale": "Conservative overlay prioritizes precision: higher binary_threshold and elevated oblique/horizontal Hough thresholds, shorter maxLineGap, slightly higher vertical threshold to avoid extra verticals, tighter denoise (higher grad_threshold, prior-like mask_r_high), and a higher y_bounds lower edge [4200,13300] to shrink SAM crops away from noisy top fringe. Enhancing stays near defaults with modest curvature raise to avoid over-enhancing artifact ridges. Distinct from the balanced round by trading recall for cleaner prompt geometry.",
    "proposer": "Gemini-3.8 (fresh per-case agent)"
  },
  {
    "round": 3,
    "status": "ok",
    "overlay": {
      "denoising": {
        "mask_r_low": 2.25,
        "mask_r_high": 2.88,
        "z_step": 0.003,
        "grad_threshold": 0.12
      },
      "enhancing": {
        "curvature_threshold": 0.0004,
        "inter_radius": 0.07
      },
      "detecting": {
        "binary_threshold": 105,
        "hough_threshold_oblique": 42,
        "hough_threshold_horizontal": 42,
        "hough_threshold_vertical": 450,
        "maxLineGap_oblique": 75
      },
      "sam": {
        "processing.y_bounds": [
          3650,
          13300
        ]
      }
    },
    "proxy_scaled": 0.6370478188692228,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.34410378034170613,
      "sam_fill_rate": 0.7522559543953538,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.1301433889413054
    },
    "recentre_residual_max_cm": 1.4,
    "full_pipeline": false,
    "rationale": "Recall-oriented overlay: lower binary and oblique/horizontal Hough thresholds, maximize maxLineGap_oblique within bounds, slightly lower vertical threshold toward 450, widen inter_radius and drop curvature_threshold to densify joint cloud, mildly widen radial gate (lower mask_r_low, higher mask_r_high) and soften grad_threshold, and push sam.processing.y_bounds to the low end [3650,13300] to expand axial crop over staggered A/B interfaces. Intentionally opposite of the conservative round: accept more lines/noise to recover correspondence recall.",
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
`/home/boringtao/Projects/Proxy4Tun/data/sc-general/stage3/packets-gemini38/1-3/round3_proposal.json`

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
