# Gemini 3.8 reflection — subset 5-2 (propose round 3)

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

- subset: `5-2`
- family: `t4&5`
- lining_mode: `complex`
- stage1_unlocked: `False` (residual gate 10 cm)
- arm: `gemini38` / proposer: `Gemini-3.8 (fresh per-case agent)`
- model: `inherit`

### Anchor (GT-blind)
```json
{
  "proxy_raw": 0.682908,
  "proxy_scaled": 0.682908,
  "band": "refine",
  "features": {
    "correspondence_f1@15": 0.452805,
    "sam_fill_rate": 0.751179,
    "ring_count_error": 0.0,
    "depth_nan_ratio": 0.193998
  },
  "recentre_residual_max_cm": 2.1,
  "orient_axis_corr": 0.8418715723827292,
  "ring_count": 10,
  "ring_count_error": 0.0,
  "labelmap_source": "only_label.csv",
  "run_dir": "/home/boringtao/Projects/Proxy4Tun/data/bo/unified/5-2-family-proxy/runs/5-2-anchor"
}
```

### Intrinsics (GT-blind)
```json
{
  "orient_axis_corr": 0.8418715723827292,
  "orient_invariant_ok": 1.0,
  "recentre_residual_max_cm": 2.1,
  "denoise_retained_ratio": 0.7623915847687736,
  "depth_nan_ratio": 0.1939982824150022,
  "depth_outlier_ratio": 0.0012904843554376751,
  "det_real_detection_ratio": 0.6,
  "det_fallback_ratio": 0.4,
  "det_n_points": 10.0,
  "sam_fill_rate": 0.7511792176693792,
  "sam_ring_completeness": 1.0,
  "sam_segment_size_cv": 1.0878136310564073,
  "sam_ontology_divergence": 0.1373509792086076
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
        "curvature_threshold": 0.0005
      },
      "detecting": {
        "binary_threshold": 120,
        "hough_threshold_oblique": 40,
        "hough_threshold_horizontal": 45,
        "hough_threshold_vertical": 5000,
        "maxLineGap_oblique": 55,
        "maxLineGap_horizontal": 12,
        "pattern_tolerance": 14
      },
      "sam": {
        "segment_width": 1800,
        "K_height": 1227.0,
        "angle": 9.8
      }
    },
    "proxy_scaled": 0.684127466478409,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.4550376635173361,
      "sam_fill_rate": 0.7511792176693792,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.1939982824150022
    },
    "recentre_residual_max_cm": 2.1,
    "full_pipeline": false,
    "rationale": "Set SAM to T4/T5 notebook priors (segment_width=1800, K_height=1227, angle=9.8) so K crops sit on textured chevron bands visible in detected_lines. Force synthetic verticals (complex-family stable) while moderately relaxing oblique Hough and raising pattern_tolerance so joint loci better support boundaries at @15px. Leave unfolding untouched (stage1_unlocked=false).",
    "proposer": "Gemini-3.8 (fresh per-case agent)"
  },
  {
    "round": 2,
    "status": "ok",
    "overlay": {
      "denoising": {
        "mask_r_low": 3.65,
        "mask_r_high": 3.95
      },
      "enhancing": {
        "curvature_threshold": 0.0004
      },
      "detecting": {
        "binary_threshold": 110,
        "hough_threshold_oblique": 35,
        "hough_threshold_horizontal": 40,
        "hough_threshold_vertical": 2000,
        "maxLineGap_oblique": 65,
        "maxLineGap_horizontal": 15,
        "pattern_tolerance": 18
      },
      "sam": {
        "segment_width": 1950,
        "K_height": 1100.0,
        "angle": 11.0
      }
    },
    "proxy_scaled": 0.6759056753825918,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.44123352068245986,
      "sam_fill_rate": 0.7494677867155899,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.19503760381000143
    },
    "recentre_residual_max_cm": 2.1,
    "full_pipeline": false,
    "rationale": "Drop K_height to 1100 so SAM crops remain inside speckled lining zones rather than the empty mid-strip. Widen segment_width to 1950 and raise angle to 11.0 for complex taper. Lower binary/oblique thresholds and widen maxLineGap_oblique to lift real joint yield; nudge denoise toward the T5 radius prior (3.65\u20133.95).",
    "proposer": "Gemini-3.8 (fresh per-case agent)"
  },
  {
    "round": 3,
    "status": "ok",
    "overlay": {
      "denoising": {
        "mask_r_low": 3.6,
        "mask_r_high": 3.9
      },
      "enhancing": {
        "curvature_threshold": 0.0007
      },
      "detecting": {
        "binary_threshold": 135,
        "hough_threshold_oblique": 55,
        "hough_threshold_horizontal": 55,
        "hough_threshold_vertical": 5000,
        "maxLineGap_oblique": 45,
        "maxLineGap_horizontal": 10,
        "pattern_tolerance": 10
      },
      "sam": {
        "segment_width": 1650,
        "K_height": 1300.0,
        "angle": 8.0
      }
    },
    "proxy_scaled": 0.6871552474243696,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.4597218754161959,
      "sam_fill_rate": 0.751602748470555,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.192292940655025
    },
    "recentre_residual_max_cm": 2.1,
    "full_pipeline": false,
    "rationale": "Narrow segment_width to 1650 and use K_height=1300 (above prior but well under 1500 empty-crop risk) with shallower angle=8.0 to reduce bleed across adjacent blocks. Tighten oblique/horizontal Hough and raise binary_threshold to cut orange unexplained joints; keep vertical at 5000 for complex-family synthetic stability. Denoise at the notebook radius band 3.60\u20133.90.",
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
`/home/boringtao/Projects/Proxy4Tun/data/sc-general/stage3/packets-gemini38/5-2/round3_proposal.json`

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
