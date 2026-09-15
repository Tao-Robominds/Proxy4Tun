# GPT-5.6 reflection — subset 1-5 (propose round 3)

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

- subset: `1-5`
- family: `t1&2`
- lining_mode: `staggered`
- stage1_unlocked: `False` (residual gate 10 cm)
- arm: `gpt56` / proposer: `GPT-5.6 (fresh per-case agent)`
- model: `gpt-5.6-sol-medium`

### Anchor (GT-blind)
```json
{
  "proxy_raw": 0.555111,
  "proxy_scaled": 0.555111,
  "band": "refine",
  "features": {
    "correspondence_f1@15": 0.200763,
    "sam_fill_rate": 0.729429,
    "ring_count_error": 0.0,
    "depth_nan_ratio": 0.117745
  },
  "recentre_residual_max_cm": 2.5,
  "orient_axis_corr": -0.9991614281123364,
  "ring_count": 10,
  "ring_count_error": 0.0,
  "labelmap_source": "results.pkl",
  "run_dir": "/home/boringtao/Projects/Proxy4Tun/data/bo/unified/1-5-family-proxy/runs/1-5-anchor"
}
```

### Intrinsics (GT-blind)
```json
{
  "orient_axis_corr": -0.9991614281123364,
  "orient_invariant_ok": 1.0,
  "recentre_residual_max_cm": 2.5,
  "denoise_retained_ratio": 0.7638200158043973,
  "depth_nan_ratio": 0.11774456253619453,
  "depth_outlier_ratio": 0.006866276013199325,
  "det_real_detection_ratio": 0.8,
  "det_fallback_ratio": 0.2,
  "det_n_points": 10.0,
  "sam_fill_rate": 0.7294291823548552,
  "sam_ring_completeness": 0.8888888888888888,
  "sam_segment_size_cv": 1.303208521951268,
  "sam_ontology_divergence": 0.19335931650162724
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
        "curvature_threshold": 0.002,
        "inter_radius": 0.05
      },
      "detecting": {
        "binary_threshold": 115,
        "hough_threshold_oblique": 45,
        "hough_threshold_horizontal": 45,
        "maxLineGap_oblique": 70
      },
      "sam": {
        "processing.y_bounds": [
          4000,
          13300
        ]
      }
    },
    "proxy_scaled": 0.5279137572416307,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.14973110388751132,
      "sam_fill_rate": 0.7336661553479291,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.11998168793127906
    },
    "recentre_residual_max_cm": 2.5,
    "full_pipeline": false,
    "rationale": "A moderate curvature threshold and neighborhood radius should consolidate faint joint responses without changing geometry. Lower horizontal and oblique Hough thresholds plus a larger oblique line gap target the missing and fragmented staggered seams visible in the diagnostics. The binary threshold is lowered conservatively to expose weak seams, while the vertical threshold is left untouched because ring count is exact. A central in-bounds SAM lower crop avoids spending prompt support on the damaged upper margin while retaining the full lower extent.",
    "proposer": "GPT-5.6 (fresh per-case agent)"
  },
  {
    "round": 2,
    "status": "ok",
    "overlay": {
      "enhancing": {
        "curvature_threshold": 0.0065,
        "inter_radius": 0.03
      },
      "detecting": {
        "binary_threshold": 150,
        "hough_threshold_oblique": 80,
        "hough_threshold_horizontal": 75,
        "maxLineGap_oblique": 30
      },
      "sam": {
        "processing.y_bounds": [
          3600,
          13300
        ]
      }
    },
    "proxy_scaled": 0.5710554947606463,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.23013541003143814,
      "sam_fill_rate": 0.7286938130432762,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.11728721067246319
    },
    "recentre_residual_max_cm": 2.5,
    "full_pipeline": false,
    "rationale": "This overlay deliberately moves away from Round 1's permissive detector. A higher curvature threshold and smaller interaction radius localize enhancement around stronger seams. Higher binary and transverse Hough thresholds reject weak texture, while a short oblique line gap prevents disconnected fragments from becoming long false joints. Vertical detection remains untouched because ten rings are still recovered exactly. Lowering the SAM crop start to 3600 restores upper lining context that the Round 1 crop may have excluded.",
    "proposer": "GPT-5.6 (fresh per-case agent)"
  },
  {
    "round": 3,
    "status": "ok",
    "overlay": {
      "enhancing": {
        "curvature_threshold": 0.0075,
        "inter_radius": 0.025
      },
      "detecting": {
        "binary_threshold": 155,
        "hough_threshold_oblique": 85,
        "hough_threshold_horizontal": 70,
        "maxLineGap_oblique": 25
      },
      "sam": {
        "processing.y_bounds": [
          3700,
          13300
        ]
      }
    },
    "proxy_scaled": 0.6097842077534261,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.301410632747391,
      "sam_fill_rate": 0.7276906986473295,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.11701010042847122
    },
    "recentre_residual_max_cm": 2.5,
    "full_pipeline": false,
    "rationale": "The proposal stays close to the successful Round 2 settings rather than reversing direction. Raising curvature and binary selectivity slightly, shrinking the interaction radius, increasing the oblique vote threshold, and shortening the line gap should further suppress textured false positives. Reducing only the horizontal Hough threshold from 75 to 70 provides a controlled recovery path for physical transverse seams. A lower crop of 3700 retains nearly all of Round 2's useful upper context while excluding a small amount of damaged margin. Vertical detection and unfolding remain untouched because orientation and ten-ring topology are already stable.",
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
`/home/boringtao/Projects/Proxy4Tun/data/sc-general/stage3/packets-gpt56/1-5/round3_proposal.json`

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
