# GPT-5.6 reflection — subset 5-2 (propose round 3)

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

- subset: `5-2`
- family: `t4&5`
- lining_mode: `complex`
- stage1_unlocked: `False` (residual gate 10 cm)
- arm: `gpt56` / proposer: `GPT-5.6 (fresh per-case agent)`
- model: `gpt-5.6-sol-medium`

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
        "curvature_threshold": 0.0008
      },
      "detecting": {
        "binary_threshold": 118,
        "hough_threshold_oblique": 34,
        "hough_threshold_horizontal": 32,
        "maxLineGap_oblique": 66,
        "maxLineGap_horizontal": 22,
        "pattern_tolerance": 15
      },
      "sam": {
        "segment_width": 1800,
        "K_height": 1225.0,
        "angle": 9.0
      }
    },
    "proxy_scaled": 0.6904103715733427,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.4656824502552945,
      "sam_fill_rate": 0.7511792176693792,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.1917468804759794
    },
    "recentre_residual_max_cm": 2.1,
    "full_pipeline": false,
    "rationale": "This balanced proposal lowers line-evidence barriers and permits longer gap bridging while retaining a mid-range SAM geometry. It targets correspondence without aggressively changing the already-correct ring count.",
    "proposer": "GPT-5.6 (fresh per-case agent)"
  },
  {
    "round": 2,
    "status": "ok",
    "overlay": {
      "denoising": {
        "mask_r_low": 3.62,
        "mask_r_high": 3.9
      },
      "enhancing": {
        "curvature_threshold": 0.00135
      },
      "detecting": {
        "binary_threshold": 148,
        "hough_threshold_oblique": 55,
        "hough_threshold_horizontal": 52,
        "hough_threshold_vertical": 3300,
        "maxLineGap_oblique": 42,
        "maxLineGap_horizontal": 12,
        "pattern_tolerance": 8
      },
      "sam": {
        "segment_width": 1580,
        "K_height": 1080.0,
        "angle": 7.8
      }
    },
    "proxy_scaled": 0.6582118696378261,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.4068822367335582,
      "sam_fill_rate": 0.7491964622960867,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.18949842162297068
    },
    "recentre_residual_max_cm": 2.1,
    "full_pipeline": false,
    "rationale": "This conservative alternative raises binary and Hough thresholds, shortens accepted gaps, and uses smaller, less tilted SAM geometry. It tests whether cleaner boundaries improve correspondence and segment balance while preserving the established topology.",
    "proposer": "GPT-5.6 (fresh per-case agent)"
  },
  {
    "round": 3,
    "status": "ok",
    "overlay": {
      "enhancing": {
        "curvature_threshold": 0.00035
      },
      "detecting": {
        "binary_threshold": 105,
        "hough_threshold_oblique": 27,
        "hough_threshold_horizontal": 28,
        "hough_threshold_vertical": 1450,
        "maxLineGap_oblique": 78,
        "maxLineGap_horizontal": 28,
        "pattern_tolerance": 19
      },
      "sam": {
        "segment_width": 2050,
        "K_height": 1450.0,
        "angle": 11.5
      }
    },
    "proxy_scaled": 0.48565735850217584,
    "band": "reject",
    "features": {
      "correspondence_f1@15": 0.09242356603190455,
      "sam_fill_rate": 0.7511792176693792,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.19566554064195768
    },
    "recentre_residual_max_cm": 2.1,
    "full_pipeline": false,
    "rationale": "This recall-focused alternative uses permissive line thresholds, long gap bridging, and larger, steeper SAM support. The proposal deliberately leaves denoising unchanged so the test isolates evidence recovery and prompt propagation under the existing depth retention.",
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
`/home/boringtao/Projects/Proxy4Tun/data/sc-general/stage3/packets-gpt56/5-2/round3_proposal.json`

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
