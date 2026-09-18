# GPT-5.6 reflection — subset 4-3 (propose round 3)

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

- subset: `4-3`
- family: `t4&5`
- lining_mode: `complex`
- stage1_unlocked: `True` (residual gate 10 cm)
- arm: `gpt56` / proposer: `GPT-5.6 (fresh per-case agent)`
- model: `gpt-5.6-sol-medium`

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
      "denoising": {
        "mask_r_low": 3.62,
        "mask_r_high": 3.92
      },
      "detecting": {
        "hough_threshold_oblique": 38,
        "hough_threshold_horizontal": 36,
        "hough_threshold_vertical": 3000,
        "maxLineGap_oblique": 62,
        "maxLineGap_horizontal": 19,
        "pattern_tolerance": 14
      },
      "sam": {
        "segment_width": 1780,
        "K_height": 1240.0,
        "angle": 9.4
      }
    },
    "proxy_scaled": 0.5265480909611039,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.2018356917371538,
      "sam_fill_rate": 0.7187196558791239,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.24432326154863182
    },
    "recentre_residual_max_cm": 23.2,
    "full_pipeline": false,
    "rationale": "This balanced overlay lowers the oblique and horizontal Hough thresholds, bridges moderate gaps, and widens pattern tolerance while keeping the vertical detector comparatively selective. Mid-range segment width, K height, and angle should make prompts cover the large panels more evenly. Denoising remains central in its allowed band to avoid trading the current low outlier ratio for extra clutter.",
    "proposer": "GPT-5.6 (fresh per-case agent)"
  },
  {
    "round": 2,
    "status": "ok",
    "overlay": {
      "denoising": {
        "mask_r_low": 3.74,
        "mask_r_high": 4.01
      },
      "detecting": {
        "hough_threshold_oblique": 58,
        "hough_threshold_horizontal": 55,
        "hough_threshold_vertical": 3600,
        "maxLineGap_oblique": 41,
        "maxLineGap_horizontal": 10,
        "pattern_tolerance": 8
      },
      "sam": {
        "segment_width": 1560,
        "K_height": 1080.0,
        "angle": 7.8
      }
    },
    "proxy_scaled": 0.47643213496085207,
    "band": "reject",
    "features": {
      "correspondence_f1@15": 0.19688248336728503,
      "sam_fill_rate": 0.6047413823975706,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.32393566604159396
    },
    "recentre_residual_max_cm": 23.2,
    "full_pipeline": false,
    "rationale": "This proposal deliberately contrasts with the balanced round by raising line thresholds, shortening both gap limits, and tightening pattern tolerance. A smaller segment width and lower K height localize mask growth around reliable prompts, while a lower permitted angle favors the mostly shallow joint slopes visible in the overlay. The slightly tighter denoising band suppresses peripheral clutter without changing unfolding.",
    "proposer": "GPT-5.6 (fresh per-case agent)"
  },
  {
    "round": 3,
    "status": "ok",
    "overlay": {
      "denoising": {
        "mask_r_low": 3.53,
        "mask_r_high": 3.79
      },
      "detecting": {
        "hough_threshold_oblique": 27,
        "hough_threshold_horizontal": 29,
        "hough_threshold_vertical": 2400,
        "maxLineGap_oblique": 78,
        "maxLineGap_horizontal": 28,
        "pattern_tolerance": 19
      },
      "sam": {
        "segment_width": 2040,
        "K_height": 1440.0,
        "angle": 11.4
      }
    },
    "proxy_scaled": 0.48498968818240074,
    "band": "reject",
    "features": {
      "correspondence_f1@15": 0.12945029737623118,
      "sam_fill_rate": 0.7151507524062983,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.24934376911102016
    },
    "recentre_residual_max_cm": 23.2,
    "full_pipeline": false,
    "rationale": "This aggressive alternative lowers oblique and horizontal Hough thresholds, extends both line-gap limits, and nearly maximizes pattern tolerance. The vertical threshold stays well above its minimum to avoid destabilizing the already correct ten-ring layout. Larger segment width, K height, and angle accommodate the broad, sloped lower panels, while the denoising radii remain inside a narrow low-side band to retain faint boundary evidence.",
    "proposer": "GPT-5.6 (fresh per-case agent)"
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
`/home/boringtao/Projects/Proxy4Tun/data/sc-general/stage3/packets-gpt56/4-3/round3_proposal.json`

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
