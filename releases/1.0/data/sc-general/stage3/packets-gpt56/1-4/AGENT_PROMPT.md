# GPT-5.6 reflection — subset 1-4 (propose round 3)

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

- subset: `1-4`
- family: `t1&2`
- lining_mode: `staggered`
- stage1_unlocked: `False` (residual gate 10 cm)
- arm: `gpt56` / proposer: `GPT-5.6 (fresh per-case agent)`
- model: `gpt-5.6-sol-medium`

### Anchor (GT-blind)
```json
{
  "proxy_raw": 0.646304,
  "proxy_scaled": 0.646304,
  "band": "refine",
  "features": {
    "correspondence_f1@15": 0.39509,
    "sam_fill_rate": 0.698703,
    "ring_count_error": 0.0,
    "depth_nan_ratio": 0.14983
  },
  "recentre_residual_max_cm": 1.9,
  "orient_axis_corr": -0.9949699843931424,
  "ring_count": 10,
  "ring_count_error": 0.0,
  "labelmap_source": "results.pkl",
  "run_dir": "/home/boringtao/Projects/Proxy4Tun/data/bo/unified/1-4-family-proxy/runs/1-4-anchor"
}
```

### Intrinsics (GT-blind)
```json
{
  "orient_axis_corr": -0.9949699843931424,
  "orient_invariant_ok": 1.0,
  "recentre_residual_max_cm": 1.9,
  "denoise_retained_ratio": 0.7219901144907218,
  "depth_nan_ratio": 0.14983039763025083,
  "depth_outlier_ratio": 0.002298421906424316,
  "det_real_detection_ratio": 0.7,
  "det_fallback_ratio": 0.3,
  "det_n_points": 10.0,
  "sam_fill_rate": 0.6987025605698844,
  "sam_ring_completeness": 1.0,
  "sam_segment_size_cv": 1.5457569103686017,
  "sam_ontology_divergence": 0.2747016575820716
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
        "inter_radius": 0.06
      },
      "detecting": {
        "binary_threshold": 120,
        "hough_threshold_oblique": 50,
        "hough_threshold_horizontal": 50,
        "maxLineGap_oblique": 35
      },
      "sam": {
        "processing.y_bounds": [
          4000,
          13300
        ]
      }
    },
    "proxy_scaled": 0.6537518560947613,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.4095936759714984,
      "sam_fill_rate": 0.6990354168809856,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.1525641648958373
    },
    "recentre_residual_max_cm": 1.9,
    "full_pipeline": false,
    "rationale": "A lower curvature threshold and larger interaction radius retain and connect faint joint responses. Moderately lower horizontal and oblique Hough thresholds improve real-line recovery, while a smaller oblique line gap avoids bridging unrelated fragments; a slightly lower binary threshold supports the faint responses. Raising the SAM lower y bound to 4000 excludes more of the noisy upper fringe while retaining the lining body. All values stay within the packet bounds and unfolding is omitted because stage1_unlocked is false.",
    "proposer": "GPT-5.6 (fresh per-case agent)"
  },
  {
    "round": 2,
    "status": "ok",
    "overlay": {
      "denoising": {
        "mask_r_low": 2.3,
        "mask_r_high": 2.8,
        "z_step": 0.005,
        "grad_threshold": 0.16
      },
      "detecting": {
        "binary_threshold": 110,
        "hough_threshold_oblique": 42,
        "hough_threshold_horizontal": 42,
        "hough_threshold_vertical": 650,
        "maxLineGap_oblique": 65
      },
      "sam": {
        "processing.y_bounds": [
          4200,
          13300
        ]
      }
    },
    "proxy_scaled": 0.6882704583289929,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.45213901323356764,
      "sam_fill_rate": 0.7404286305978972,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.1523223601885479
    },
    "recentre_residual_max_cm": 1.9,
    "full_pipeline": false,
    "rationale": "Moderate denoising radii, z-step, and gradient threshold provide a cleaner edge field after the slight increase in missing depth. The horizontal and oblique Hough thresholds are moved near their sensitive bounds to recover faint cross-ring joints, while the vertical threshold is raised to 650 to suppress redundant vertical responses. A longer oblique line gap reconnects fragmented joint evidence rather than repeating Round 1's short-gap strategy. The SAM lower bound is raised to 4200 to further exclude the noisy upper fringe. This is a different bounded overlay from Round 1, with no unfolding and full remaining false.",
    "proposer": "GPT-5.6 (fresh per-case agent)"
  },
  {
    "round": 3,
    "status": "ok",
    "overlay": {
      "denoising": {
        "mask_r_low": 2.35,
        "mask_r_high": 2.85,
        "z_step": 0.0045,
        "grad_threshold": 0.18
      },
      "enhancing": {
        "curvature_threshold": 0.003,
        "inter_radius": 0.07
      },
      "detecting": {
        "binary_threshold": 115,
        "hough_threshold_oblique": 55,
        "hough_threshold_horizontal": 40,
        "hough_threshold_vertical": 720,
        "maxLineGap_oblique": 50
      },
      "sam": {
        "processing.y_bounds": [
          4400,
          13300
        ]
      }
    },
    "proxy_scaled": 0.682822660987501,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.43479627899489665,
      "sam_fill_rate": 0.7398237800519967,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.13210584322672958
    },
    "recentre_residual_max_cm": 1.9,
    "full_pipeline": false,
    "rationale": "Round 3 locally refines the successful Round 2 neighborhood with slightly stronger gradient rejection and centered mask radii. A moderate enhancement radius preserves continuity without repeating Round 1's exact settings. Raising the oblique Hough threshold and shortening its line gap reduces duplicate or over-bridged sloped candidates, while setting the horizontal threshold to its lower bound favors the scarce horizontal joints. A higher vertical threshold further limits dominant seam texture. Moving the flat SAM lower bound to 4400 continues the crop trend that accompanied the Round 2 fill gain. Every value is bounded; unfolding is absent and full is false.",
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
`/home/boringtao/Projects/Proxy4Tun/data/sc-general/stage3/packets-gpt56/1-4/round3_proposal.json`

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
