# GPT-5.6 reflection — subset 5-4 (propose round 3)

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

- subset: `5-4`
- family: `t4&5`
- lining_mode: `complex`
- stage1_unlocked: `False` (residual gate 10 cm)
- arm: `gpt56` / proposer: `GPT-5.6 (fresh per-case agent)`
- model: `gpt-5.6-sol-medium`

### Anchor (GT-blind)
```json
{
  "proxy_raw": 0.692326,
  "proxy_scaled": 0.692326,
  "band": "refine",
  "features": {
    "correspondence_f1@15": 0.467401,
    "sam_fill_rate": 0.759939,
    "ring_count_error": 0.0,
    "depth_nan_ratio": 0.19849
  },
  "recentre_residual_max_cm": 2.1,
  "orient_axis_corr": -0.7738736413768053,
  "ring_count": 10,
  "ring_count_error": 0.0,
  "labelmap_source": "only_label.csv",
  "run_dir": "/home/boringtao/Projects/Proxy4Tun/data/bo/unified/5-4-family-proxy/runs/5-4-anchor"
}
```

### Intrinsics (GT-blind)
```json
{
  "orient_axis_corr": -0.7738736413768053,
  "orient_invariant_ok": 1.0,
  "recentre_residual_max_cm": 2.1,
  "denoise_retained_ratio": 0.771714565621628,
  "depth_nan_ratio": 0.19848996720212705,
  "depth_outlier_ratio": 0.00134290457193032,
  "det_real_detection_ratio": 0.7,
  "det_fallback_ratio": 0.3,
  "det_n_points": 10.0,
  "sam_fill_rate": 0.7599389968796842,
  "sam_ring_completeness": 1.0,
  "sam_segment_size_cv": 1.1070596715680279,
  "sam_ontology_divergence": 0.14195278326436073
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
        "curvature_threshold": 0.00065
      },
      "detecting": {
        "binary_threshold": 118,
        "hough_threshold_oblique": 34,
        "hough_threshold_horizontal": 30,
        "hough_threshold_vertical": 2600,
        "maxLineGap_oblique": 62,
        "maxLineGap_horizontal": 24,
        "pattern_tolerance": 14
      },
      "sam": {
        "segment_width": 1800,
        "K_height": 1240.0,
        "angle": 9.0
      }
    },
    "proxy_scaled": 0.7103465872845497,
    "band": "accept",
    "features": {
      "correspondence_f1@15": 0.49993812702760826,
      "sam_fill_rate": 0.7599389968796842,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.19731867326731048
    },
    "recentre_residual_max_cm": 2.1,
    "full_pipeline": false,
    "rationale": "Use a moderately permissive binary threshold, lower horizontal and oblique Hough votes, bridge longer horizontal gaps, and allow modest pattern tolerance. Keep SAM geometry near the middle of the allowed t4&5 range so the proposal primarily tests whether stronger seam continuity improves correspondence.",
    "proposer": "GPT-5.6 (fresh per-case agent)"
  },
  {
    "round": 2,
    "status": "ok",
    "overlay": {
      "denoising": {
        "mask_r_low": 3.62,
        "mask_r_high": 3.92
      },
      "enhancing": {
        "curvature_threshold": 0.0011
      },
      "detecting": {
        "binary_threshold": 138,
        "hough_threshold_oblique": 46,
        "hough_threshold_horizontal": 42,
        "hough_threshold_vertical": 3400,
        "maxLineGap_oblique": 48,
        "maxLineGap_horizontal": 17,
        "pattern_tolerance": 10
      },
      "sam": {
        "segment_width": 1580,
        "K_height": 1080.0,
        "angle": 10.8
      }
    },
    "proxy_scaled": 0.6419482336213735,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.37487533888998537,
      "sam_fill_rate": 0.7578080870103606,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.19485446185896388
    },
    "recentre_residual_max_cm": 2.1,
    "full_pipeline": false,
    "rationale": "A narrower segment width and lower K_height impose a denser, more regular partition, while a slightly steeper angle follows the visible oblique seam family. Detection is kept selective enough to avoid turning the dense surface texture into prompts.",
    "proposer": "GPT-5.6 (fresh per-case agent)"
  },
  {
    "round": 3,
    "status": "ok",
    "overlay": {
      "denoising": {
        "mask_r_low": 3.72,
        "mask_r_high": 4.02
      },
      "enhancing": {
        "curvature_threshold": 0.00175
      },
      "detecting": {
        "binary_threshold": 154,
        "hough_threshold_oblique": 61,
        "hough_threshold_horizontal": 57,
        "hough_threshold_vertical": 4550,
        "maxLineGap_oblique": 72,
        "maxLineGap_horizontal": 28,
        "pattern_tolerance": 7
      },
      "sam": {
        "segment_width": 2040,
        "K_height": 1430.0,
        "angle": 7.6
      }
    },
    "proxy_scaled": 0.5168667205300026,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.1490354478696714,
      "sam_fill_rate": 0.754090645351764,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.19813231303329107
    },
    "recentre_residual_max_cm": 2.1,
    "full_pipeline": false,
    "rationale": "This conservative alternative raises binary and Hough thresholds, uses a higher curvature cutoff, and requires coherent gap-bridged oblique structure. A wider SAM segment width tests whether fewer, cleaner prompts reduce fragmentation and ontology divergence.",
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
`/home/boringtao/Projects/Proxy4Tun/data/sc-general/stage3/packets-gpt56/5-4/round3_proposal.json`

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
