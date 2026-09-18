# GPT-5.6 reflection — subset 5-5 (propose round 3)

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

- subset: `5-5`
- family: `t4&5`
- lining_mode: `complex`
- stage1_unlocked: `False` (residual gate 10 cm)
- arm: `gpt56` / proposer: `GPT-5.6 (fresh per-case agent)`
- model: `gpt-5.6-sol-medium`

### Anchor (GT-blind)
```json
{
  "proxy_raw": 0.609798,
  "proxy_scaled": 0.609798,
  "band": "refine",
  "features": {
    "correspondence_f1@15": 0.316226,
    "sam_fill_rate": 0.756178,
    "ring_count_error": 0.0,
    "depth_nan_ratio": 0.193232
  },
  "recentre_residual_max_cm": 1.9,
  "orient_axis_corr": 0.9125884650166897,
  "ring_count": 10,
  "ring_count_error": 0.0,
  "labelmap_source": "only_label.csv",
  "run_dir": "/home/boringtao/Projects/Proxy4Tun/data/bo/unified/5-5-family-proxy/runs/5-5-anchor"
}
```

### Intrinsics (GT-blind)
```json
{
  "orient_axis_corr": 0.9125884650166897,
  "orient_invariant_ok": 1.0,
  "recentre_residual_max_cm": 1.9,
  "denoise_retained_ratio": 0.7673354664684634,
  "depth_nan_ratio": 0.19323166894404062,
  "depth_outlier_ratio": 0.001291584040276335,
  "det_real_detection_ratio": 0.8,
  "det_fallback_ratio": 0.2,
  "det_n_points": 10.0,
  "sam_fill_rate": 0.7561778560970978,
  "sam_ring_completeness": 1.0,
  "sam_segment_size_cv": 1.0460848905509348,
  "sam_ontology_divergence": 0.10887649245012132
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
        "curvature_threshold": 0.0008
      },
      "detecting": {
        "binary_threshold": 120,
        "hough_threshold_oblique": 38,
        "hough_threshold_horizontal": 32,
        "hough_threshold_vertical": 2800,
        "maxLineGap_oblique": 60,
        "maxLineGap_horizontal": 22,
        "pattern_tolerance": 12
      },
      "sam": {
        "segment_width": 1750,
        "K_height": 1250.0,
        "angle": 9.5
      }
    },
    "proxy_scaled": 0.6411483936564466,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.3692846482092852,
      "sam_fill_rate": 0.7610789961060415,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.18825702287054552
    },
    "recentre_residual_max_cm": 1.9,
    "full_pipeline": false,
    "rationale": "This proposal makes a balanced sensitivity adjustment: modest denoising and enhancement, lower Hough barriers with bridgeable gaps, and central SAM geometry. It avoids changing the already-correct ring topology while targeting the weakest proxy term.",
    "proposer": "GPT-5.6 (fresh per-case agent)"
  },
  {
    "round": 2,
    "status": "ok",
    "overlay": {
      "denoising": {
        "mask_r_low": 3.7,
        "mask_r_high": 3.85
      },
      "enhancing": {
        "curvature_threshold": 0.0016
      },
      "detecting": {
        "binary_threshold": 148,
        "hough_threshold_oblique": 56,
        "hough_threshold_horizontal": 52,
        "hough_threshold_vertical": 4200,
        "maxLineGap_oblique": 42,
        "maxLineGap_horizontal": 10,
        "pattern_tolerance": 7
      },
      "sam": {
        "segment_width": 1550,
        "K_height": 1080.0,
        "angle": 8.0
      }
    },
    "proxy_scaled": 0.5885088566004436,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.27696834918265106,
      "sam_fill_rate": 0.752477370322196,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.18761964450373095
    },
    "recentre_residual_max_cm": 1.9,
    "full_pipeline": false,
    "rationale": "This is the precision-focused alternative. Stricter detection and shorter gap closure suppress isolated fragments, while narrower SAM geometry limits damage from any remaining false prompt. The vertical threshold stays conservative because the ten ring instances are already correct.",
    "proposer": "GPT-5.6 (fresh per-case agent)"
  },
  {
    "round": 3,
    "status": "ok",
    "overlay": {
      "denoising": {
        "mask_r_low": 3.5,
        "mask_r_high": 4.05
      },
      "enhancing": {
        "curvature_threshold": 0.0003
      },
      "detecting": {
        "binary_threshold": 104,
        "hough_threshold_oblique": 27,
        "hough_threshold_horizontal": 27,
        "hough_threshold_vertical": 1800,
        "maxLineGap_oblique": 78,
        "maxLineGap_horizontal": 29,
        "pattern_tolerance": 19
      },
      "sam": {
        "segment_width": 2050,
        "K_height": 1450.0,
        "angle": 11.5
      }
    },
    "proxy_scaled": 0.5177263028047773,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.14308883511393433,
      "sam_fill_rate": 0.7650791349572114,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.19268519333516276
    },
    "recentre_residual_max_cm": 1.9,
    "full_pipeline": false,
    "rationale": "This is the recall-focused alternative. Lower thresholds, permissive gap bridging, and wider pattern tolerance seek continuous joint hypotheses through missing-depth intervals; larger SAM width and height scales compensate for sparse prompts. The settings remain bounded and stage 1 stays locked.",
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
`/home/boringtao/Projects/Proxy4Tun/data/sc-general/stage3/packets-gpt56/5-5/round3_proposal.json`

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
