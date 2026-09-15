# GPT-5.6 reflection — subset 3-7 (propose round 3)

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

- subset: `3-7`
- family: `t3`
- lining_mode: `continuous`
- stage1_unlocked: `False` (residual gate 10 cm)
- arm: `gpt56` / proposer: `GPT-5.6 (fresh per-case agent)`
- model: `gpt-5.6-sol-medium`

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
      "enhancing": {
        "curvature_threshold": 0.0004
      },
      "detecting": {
        "binary_threshold": 110,
        "hough_threshold_oblique": 20,
        "hough_threshold_horizontal": 20,
        "maxLineGap_oblique": 60,
        "pattern_tolerance": 15,
        "uniform_k_snap": true
      },
      "sam": {
        "segment_width": 1400,
        "K_height": 900.0,
        "angle": 4.0
      }
    },
    "proxy_scaled": 0.5106087460671086,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.12123890233783682,
      "sam_fill_rate": 0.7644232965856651,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.16857814484577904
    },
    "recentre_residual_max_cm": 3.6,
    "full_pipeline": false,
    "rationale": "Lower curvature and binary thresholds retain faint seam evidence; minimum horizontal/oblique Hough thresholds plus a larger oblique gap join fragmented central-joint responses. A moderate pattern tolerance and uniform K snapping preserve the correct ten-ring periodicity, while wider SAM segments improve continuity across damaged columns. K_height remains at 900, above the required 800 floor, and unfolding is omitted because stage1_unlocked is false.",
    "proposer": "GPT-5.6 (fresh per-case agent)"
  },
  {
    "round": 2,
    "status": "ok",
    "overlay": {
      "denoising": {
        "mask_r_low": 2.85,
        "mask_r_high": 3.05,
        "mask_theta_low": 1.5,
        "mask_theta_high": 17.0
      },
      "enhancing": {
        "curvature_threshold": 0.001
      },
      "detecting": {
        "binary_threshold": 130,
        "hough_threshold_oblique": 40,
        "hough_threshold_horizontal": 40,
        "maxLineGap_oblique": 35,
        "pattern_tolerance": 12,
        "uniform_k_snap": true
      },
      "sam": {
        "segment_width": 1200,
        "K_height": 875.0,
        "angle": 6.5
      }
    },
    "proxy_scaled": 0.5180948448002312,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.1258294184722258,
      "sam_fill_rate": 0.7686071785231745,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.15004132394769515
    },
    "recentre_residual_max_cm": 3.6,
    "full_pipeline": false,
    "rationale": "Mild radial and angular masking limits damaged-edge and grazing-angle clutter without aggressively reducing the retained surface. Mid-range horizontal and oblique Hough thresholds require stronger consensus than round 1, while a moderate binary threshold, shorter line-gap bridge, and pattern tolerance of 12 avoid over-joining isolated responses. Uniform K snapping keeps the reliable ten-ring spacing; K_height is conservatively set to 875, and moderate SAM width and angle avoid repeating the round-1 extremes.",
    "proposer": "GPT-5.6 (fresh per-case agent)"
  },
  {
    "round": 3,
    "status": "ok",
    "overlay": {
      "denoising": {
        "mask_r_low": 2.78,
        "mask_r_high": 3.12,
        "mask_theta_low": 1.5,
        "mask_theta_high": 17.0
      },
      "enhancing": {
        "curvature_threshold": 0.0007
      },
      "detecting": {
        "binary_threshold": 120,
        "hough_threshold_oblique": 30,
        "hough_threshold_horizontal": 30,
        "maxLineGap_oblique": 45,
        "pattern_tolerance": 18,
        "uniform_k_snap": true
      },
      "sam": {
        "segment_width": 1150,
        "K_height": 950.0,
        "angle": 5.5
      }
    },
    "proxy_scaled": 0.5005095977437621,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.09495619892262643,
      "sam_fill_rate": 0.7711462270000718,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.1568182376711992
    },
    "recentre_residual_max_cm": 3.6,
    "full_pipeline": false,
    "rationale": "A radial interval of 2.78 to 3.12 retains more usable surface than round 2 while remaining bounded. Hough thresholds of 30, a gap of 45, and pattern tolerance 18 form an intermediate detector that can connect coherent fragments without returning to round-1 permissiveness. Moderate enhancement and binarization avoid both previous extremes. Uniform K snapping preserves the reliable ten-ring periodicity, while K_height 950 tests a higher prompt prior with the requested segment width of 1150.",
    "proposer": "GPT-5.6 (fresh per-case agent)"
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
`/home/boringtao/Projects/Proxy4Tun/data/sc-general/stage3/packets-gpt56/3-7/round3_proposal.json`

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
