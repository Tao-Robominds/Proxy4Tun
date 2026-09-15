# GPT-5.6 reflection — subset 4-5 (propose round 3)

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

- subset: `4-5`
- family: `t4&5`
- lining_mode: `complex`
- stage1_unlocked: `False` (residual gate 10 cm)
- arm: `gpt56` / proposer: `GPT-5.6 (fresh per-case agent)`
- model: `gpt-5.6-sol-medium`

### Anchor (GT-blind)
```json
{
  "proxy_raw": 0.609357,
  "proxy_scaled": 0.609357,
  "band": "refine",
  "features": {
    "correspondence_f1@15": 0.334208,
    "sam_fill_rate": 0.735359,
    "ring_count_error": 0.0,
    "depth_nan_ratio": 0.215522
  },
  "recentre_residual_max_cm": 3.4,
  "orient_axis_corr": 0.9810109979941607,
  "ring_count": 10,
  "ring_count_error": 0.0,
  "labelmap_source": "only_label.csv",
  "run_dir": "/home/boringtao/Projects/Proxy4Tun/data/bo/unified/4-5-family-proxy/runs/4-5-anchor"
}
```

### Intrinsics (GT-blind)
```json
{
  "orient_axis_corr": 0.9810109979941607,
  "orient_invariant_ok": 1.0,
  "recentre_residual_max_cm": 3.4,
  "denoise_retained_ratio": 0.7441345095804333,
  "depth_nan_ratio": 0.21552237876528763,
  "depth_outlier_ratio": 0.0010049970802387977,
  "det_real_detection_ratio": 0.6,
  "det_fallback_ratio": 0.4,
  "det_n_points": 10.0,
  "sam_fill_rate": 0.7353592515275288,
  "sam_ring_completeness": 1.0,
  "sam_segment_size_cv": 1.0538854727707543,
  "sam_ontology_divergence": 0.10294109747787984
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
        "mask_r_low": 3.55,
        "mask_r_high": 3.95
      },
      "enhancing": {
        "curvature_threshold": 0.00055
      },
      "detecting": {
        "binary_threshold": 112,
        "hough_threshold_oblique": 30,
        "hough_threshold_horizontal": 28,
        "hough_threshold_vertical": 2600,
        "maxLineGap_oblique": 68,
        "maxLineGap_horizontal": 24,
        "pattern_tolerance": 13
      },
      "sam": {
        "segment_width": 1800,
        "K_height": 1250.0,
        "angle": 9.0
      }
    },
    "proxy_scaled": 0.6471408860740564,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.3991615706194045,
      "sam_fill_rate": 0.740731524108406,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.21147846349082092
    },
    "recentre_residual_max_cm": 3.4,
    "full_pipeline": false,
    "rationale": "This proposal targets line recall directly: a lower curvature threshold and binary threshold expose faint seams, lower horizontal/oblique Hough thresholds admit shorter evidence, and larger line gaps reconnect broken seams. SAM changes remain modest because ring_count_error is zero and completeness is one.",
    "proposer": "GPT-5.6 (fresh per-case agent)"
  },
  {
    "round": 2,
    "status": "ok",
    "overlay": {
      "denoising": {
        "mask_r_low": 3.72,
        "mask_r_high": 4.02
      },
      "enhancing": {
        "curvature_threshold": 0.00145
      },
      "detecting": {
        "binary_threshold": 148,
        "hough_threshold_oblique": 58,
        "hough_threshold_horizontal": 55,
        "hough_threshold_vertical": 4100,
        "maxLineGap_oblique": 42,
        "maxLineGap_horizontal": 10,
        "pattern_tolerance": 7
      },
      "sam": {
        "segment_width": 1980,
        "K_height": 1380.0,
        "angle": 7.8
      }
    },
    "proxy_scaled": 0.48766498178042594,
    "band": "reject",
    "features": {
      "correspondence_f1@15": 0.12393226426923254,
      "sam_fill_rate": 0.7167652078273786,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.22401206912960567
    },
    "recentre_residual_max_cm": 3.4,
    "full_pipeline": false,
    "rationale": "This is a precision-oriented alternative to round 1. Higher binary and Hough thresholds, shorter allowed gaps, and tighter pattern tolerance reject isolated clutter. A slightly larger SAM segment width and lower angle encourage fewer, more stable subdivisions without changing the correct ten-ring topology.",
    "proposer": "GPT-5.6 (fresh per-case agent)"
  },
  {
    "round": 3,
    "status": "ok",
    "overlay": {
      "denoising": {
        "mask_r_low": 3.62,
        "mask_r_high": 3.88
      },
      "enhancing": {
        "curvature_threshold": 0.0009
      },
      "detecting": {
        "binary_threshold": 130,
        "hough_threshold_oblique": 42,
        "hough_threshold_horizontal": 40,
        "hough_threshold_vertical": 3300,
        "maxLineGap_oblique": 56,
        "maxLineGap_horizontal": 17,
        "pattern_tolerance": 10
      },
      "sam": {
        "segment_width": 1560,
        "K_height": 1470.0,
        "angle": 11.2
      }
    },
    "proxy_scaled": 0.4603351906332144,
    "band": "reject",
    "features": {
      "correspondence_f1@15": 0.05874328377320207,
      "sam_fill_rate": 0.7376634096112066,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.2113663966529371
    },
    "recentre_residual_max_cm": 3.4,
    "full_pipeline": false,
    "rationale": "This proposal centers the detector rather than maximizing recall or precision, then changes SAM geometry more strongly. Smaller segment width localizes prompt influence, higher K_height emphasizes consistent horizontal organization, and a larger angle accommodates the visibly sloped interior seams.",
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
`/home/boringtao/Projects/Proxy4Tun/data/sc-general/stage3/packets-gpt56/4-5/round3_proposal.json`

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
