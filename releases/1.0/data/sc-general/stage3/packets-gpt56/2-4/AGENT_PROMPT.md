# GPT-5.6 reflection — subset 2-4 (propose round 3)

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

- subset: `2-4`
- family: `t1&2`
- lining_mode: `staggered`
- stage1_unlocked: `False` (residual gate 10 cm)
- arm: `gpt56` / proposer: `GPT-5.6 (fresh per-case agent)`
- model: `gpt-5.6-sol-medium`

### Anchor (GT-blind)
```json
{
  "proxy_raw": 0.676342,
  "proxy_scaled": 0.676342,
  "band": "refine",
  "features": {
    "correspondence_f1@15": 0.411668,
    "sam_fill_rate": 0.745003,
    "ring_count_error": 0.0,
    "depth_nan_ratio": 0.109191
  },
  "recentre_residual_max_cm": 1.7,
  "orient_axis_corr": -0.9997455372446109,
  "ring_count": 10,
  "ring_count_error": 0.0,
  "labelmap_source": "results.pkl",
  "run_dir": "/home/boringtao/Projects/Proxy4Tun/data/bo/unified/2-4-family-proxy/runs/2-4-anchor"
}
```

### Intrinsics (GT-blind)
```json
{
  "orient_axis_corr": -0.9997455372446109,
  "orient_invariant_ok": 1.0,
  "recentre_residual_max_cm": 1.7,
  "denoise_retained_ratio": 0.7693688879665898,
  "depth_nan_ratio": 0.10919078606422467,
  "depth_outlier_ratio": 0.0029708795925650843,
  "det_real_detection_ratio": 0.9,
  "det_fallback_ratio": 0.1,
  "det_n_points": 10.0,
  "sam_fill_rate": 0.7450027236647557,
  "sam_ring_completeness": 1.0,
  "sam_segment_size_cv": 1.3219664851130428,
  "sam_ontology_divergence": 0.22643770209071767
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
        "curvature_threshold": 0.0015,
        "inter_radius": 0.06
      },
      "detecting": {
        "binary_threshold": 110,
        "hough_threshold_oblique": 45,
        "hough_threshold_horizontal": 50,
        "maxLineGap_oblique": 70
      },
      "sam": {
        "processing.y_bounds": [
          4000,
          13300
        ]
      }
    },
    "proxy_scaled": 0.6727928137671442,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.4043693443454776,
      "sam_fill_rate": 0.744626598531815,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.10658074382477072
    },
    "recentre_residual_max_cm": 1.7,
    "full_pipeline": false,
    "rationale": "A moderately larger enhancement neighborhood should join locally coherent joint evidence, while lower binary and Hough thresholds plus a larger oblique line gap should recover weak, interrupted repeated boundaries. The bounded SAM crop removes peripheral structure that can inflate unequal masks. Stage 1 remains untouched because it is locked and its residual and orientation diagnostics already pass.",
    "proposer": "GPT-5.6 (fresh per-case agent)"
  },
  {
    "round": 2,
    "status": "ok",
    "overlay": {
      "denoising": {
        "z_step": 0.004,
        "grad_threshold": 0.2
      },
      "enhancing": {
        "curvature_threshold": 0.005,
        "inter_radius": 0.03
      },
      "detecting": {
        "binary_threshold": 145,
        "hough_threshold_oblique": 75,
        "hough_threshold_horizontal": 70,
        "maxLineGap_oblique": 35
      },
      "sam": {
        "processing.y_bounds": [
          3600,
          13300
        ]
      }
    },
    "proxy_scaled": 0.65948888171992,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.38000092873176006,
      "sam_fill_rate": 0.7455464190293377,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.10773313322556963
    },
    "recentre_residual_max_cm": 1.7,
    "full_pipeline": false,
    "rationale": "This proposal is deliberately different from round 1. Higher gradient, curvature, binary, and Hough thresholds favor structurally repeated joints over surface texture, while the smaller interaction radius and shorter oblique gap reduce false bridging. Lowering the flat SAM crop start from 4000 to 3600 restores more of the allowed informative span to test whether the nearly unchanged fill was crop-limited. Unfolding remains omitted because stage 1 is locked and its geometry is stable.",
    "proposer": "GPT-5.6 (fresh per-case agent)"
  },
  {
    "round": 3,
    "status": "ok",
    "overlay": {
      "denoising": {
        "mask_r_low": 2.35,
        "mask_r_high": 2.8,
        "z_step": 0.002,
        "grad_threshold": 0.13
      },
      "enhancing": {
        "curvature_threshold": 0.0025,
        "inter_radius": 0.045
      },
      "detecting": {
        "binary_threshold": 125,
        "hough_threshold_oblique": 60,
        "hough_threshold_horizontal": 60,
        "maxLineGap_oblique": 50
      },
      "sam": {
        "processing.y_bounds": [
          4100,
          13300
        ]
      }
    },
    "proxy_scaled": 0.6865134130864957,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.4245728724402446,
      "sam_fill_rate": 0.7525195195974164,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.10396734266192233
    },
    "recentre_residual_max_cm": 1.7,
    "full_pipeline": false,
    "rationale": "This round centers the search between the two failed extremes. Mild denoising should reduce isolated texture without removing weak joints; moderate enhancement preserves local continuity; Hough thresholds of 60 and an intermediate oblique gap balance support and fragmentation. A flat y-bound starting at 4100 focuses SAM near the stable central lining span without the wider 3600 crop or the prior 4000 setting. Unfolding is omitted because stage 1 is locked and its residual, orientation, and ring count are already stable.",
    "proposer": "GPT-5.6 (fresh per-case agent)"
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
`/home/boringtao/Projects/Proxy4Tun/data/sc-general/stage3/packets-gpt56/2-4/round3_proposal.json`

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
