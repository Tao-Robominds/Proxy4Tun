# Gemini 3.8 reflection — subset 4-2 (propose round 3)

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

- subset: `4-2`
- family: `t4&5`
- lining_mode: `complex`
- stage1_unlocked: `False` (residual gate 10 cm)
- arm: `gemini38` / proposer: `Gemini-3.8 (fresh per-case agent)`
- model: `inherit`

### Anchor (GT-blind)
```json
{
  "proxy_raw": 0.543511,
  "proxy_scaled": 0.543511,
  "band": "refine",
  "features": {
    "correspondence_f1@15": 0.213123,
    "sam_fill_rate": 0.731801,
    "ring_count_error": 0.0,
    "depth_nan_ratio": 0.209361
  },
  "recentre_residual_max_cm": 2.0,
  "orient_axis_corr": 0.9669973618747811,
  "ring_count": 10,
  "ring_count_error": 0.0,
  "labelmap_source": "only_label.csv",
  "run_dir": "/home/boringtao/Projects/Proxy4Tun/data/bo/unified/4-2-family-proxy/runs/4-2-anchor"
}
```

### Intrinsics (GT-blind)
```json
{
  "orient_axis_corr": 0.9669973618747811,
  "orient_invariant_ok": 1.0,
  "recentre_residual_max_cm": 2.0,
  "denoise_retained_ratio": 0.7418340341807801,
  "depth_nan_ratio": 0.2093606933058968,
  "depth_outlier_ratio": 0.0011176488861046538,
  "det_real_detection_ratio": 0.6,
  "det_fallback_ratio": 0.4,
  "det_n_points": 10.0,
  "sam_fill_rate": 0.7318014994277484,
  "sam_ring_completeness": 1.0,
  "sam_segment_size_cv": 1.091516694082548,
  "sam_ontology_divergence": 0.11759782036661469
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
        "hough_threshold_oblique": 40,
        "maxLineGap_oblique": 60,
        "pattern_tolerance": 12
      },
      "sam": {
        "segment_width": 1720,
        "K_height": 1180.0,
        "angle": 10.5
      }
    },
    "proxy_scaled": 0.544716398809186,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.215593240265055,
      "sam_fill_rate": 0.7312675694096163,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.2093606933058968
    },
    "recentre_residual_max_cm": 2.0,
    "full_pipeline": false,
    "rationale": "Round-1 hypothesis: K trapezoid crops are slightly too wide and under-tapered relative to visible oblique joints. Narrow segment_width toward measured column pitch, keep K_height near the T4 prior (1227) but slightly lower to avoid empty-crop padding, raise angle for the observed K wedges, and gently relax oblique Hough so real K joints support the retuned template.",
    "proposer": "Gemini-3.8 (fresh per-case agent)"
  },
  {
    "round": 2,
    "status": "ok",
    "overlay": {
      "enhancing": {
        "curvature_threshold": 0.00035
      },
      "detecting": {
        "binary_threshold": 115,
        "hough_threshold_oblique": 30,
        "hough_threshold_horizontal": 35,
        "maxLineGap_oblique": 72,
        "maxLineGap_horizontal": 18,
        "pattern_tolerance": 16
      },
      "sam": {
        "segment_width": 1800,
        "K_height": 1230.0,
        "angle": 9.8
      }
    },
    "proxy_scaled": 0.576081566507264,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.2732941543000086,
      "sam_fill_rate": 0.7318014994277484,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.2108369876417932
    },
    "recentre_residual_max_cm": 2.0,
    "full_pipeline": false,
    "rationale": "Round-2 hypothesis (orthogonal to R1): unexplained orange joints and assumed prompts are a detection-yield problem. Soften binary + lower oblique/horizontal Hough thresholds, widen maxLineGap to bridge occlusion gaps, loosen pattern_tolerance, and leave segment_width/K_height/angle near notebook priors so any proxy lift is attributable to better joint support\u2014not an empty-crop K_height swing.",
    "proposer": "Gemini-3.8 (fresh per-case agent)"
  },
  {
    "round": 3,
    "status": "ok",
    "overlay": {
      "denoising": {
        "mask_r_low": 3.58,
        "mask_r_high": 3.95
      },
      "detecting": {
        "hough_threshold_oblique": 45,
        "hough_threshold_vertical": 2500,
        "maxLineGap_oblique": 55,
        "pattern_tolerance": 8
      },
      "sam": {
        "segment_width": 1900,
        "K_height": 1280.0,
        "angle": 11.2
      }
    },
    "proxy_scaled": 0.6617932173877332,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.4274451915283511,
      "sam_fill_rate": 0.7353677198667747,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.20832905814151056
    },
    "recentre_residual_max_cm": 2.0,
    "full_pipeline": false,
    "rationale": "Round-3 hypothesis (distinct corner): K tapers need a steeper angle and a slightly taller but still filled crop, with wider segment_width and stricter pattern_tolerance so distance matching locks onto the taller K. Raise hough_threshold_vertical toward synthetic verticals to stabilize ring columns, nudge denoise band slightly outward for lining retention without chasing NaN cosmetics.",
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
`/home/boringtao/Projects/Proxy4Tun/data/sc-general/stage3/packets-gemini38/4-2/round3_proposal.json`

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
