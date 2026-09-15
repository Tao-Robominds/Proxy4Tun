# GPT-5.6 reflection — subset 1-3 (propose round 3)

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

- subset: `1-3`
- family: `t1&2`
- lining_mode: `staggered`
- stage1_unlocked: `False` (residual gate 10 cm)
- arm: `gpt56` / proposer: `GPT-5.6 (fresh per-case agent)`
- model: `gpt-5.6-sol-medium`

### Anchor (GT-blind)
```json
{
  "proxy_raw": 0.550144,
  "proxy_scaled": 0.550144,
  "band": "refine",
  "features": {
    "correspondence_f1@15": 0.186826,
    "sam_fill_rate": 0.732531,
    "ring_count_error": 0.0,
    "depth_nan_ratio": 0.109033
  },
  "recentre_residual_max_cm": 1.4,
  "orient_axis_corr": 0.9999842336199495,
  "ring_count": 10,
  "ring_count_error": 0.0,
  "labelmap_source": "results.pkl",
  "run_dir": "/home/boringtao/Projects/Proxy4Tun/data/bo/unified/1-3-family-proxy/runs/1-3-anchor"
}
```

### Intrinsics (GT-blind)
```json
{
  "orient_axis_corr": 0.9999842336199495,
  "orient_invariant_ok": 1.0,
  "recentre_residual_max_cm": 1.4,
  "denoise_retained_ratio": 0.7653250403055444,
  "depth_nan_ratio": 0.10903285620918383,
  "depth_outlier_ratio": 0.0042008620385453254,
  "det_real_detection_ratio": 0.9,
  "det_fallback_ratio": 0.1,
  "det_n_points": 10.0,
  "sam_fill_rate": 0.7325314614464593,
  "sam_ring_completeness": 0.8888888888888888,
  "sam_segment_size_cv": 1.3403191091625246,
  "sam_ontology_divergence": 0.2507391898933104
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
        "inter_radius": 0.07
      },
      "detecting": {
        "binary_threshold": 115,
        "hough_threshold_oblique": 45,
        "maxLineGap_oblique": 60
      },
      "sam": {
        "processing.y_bounds": [
          3600,
          13300
        ]
      }
    },
    "proxy_scaled": 0.5468201654654041,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.1783956718390941,
      "sam_fill_rate": 0.7372519921553955,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.10902184773990094
    },
    "recentre_residual_max_cm": 1.4,
    "full_pipeline": false,
    "rationale": "Raising inter_radius should connect nearby joint samples before projection. A slightly lower binary and oblique Hough threshold together with a larger oblique line gap should recover faint, broken staggered seams without changing the vertical threshold that already yields the exact ring count. Setting y_bounds to [3600, 13300] uses the permitted t1&2 lower extent to improve mask coverage. The changes are deliberately moderate to limit spurious intersections.",
    "proposer": "GPT-5.6 (fresh per-case agent)"
  },
  {
    "round": 2,
    "status": "ok",
    "overlay": {
      "enhancing": {
        "curvature_threshold": 0.0003
      },
      "detecting": {
        "binary_threshold": 135,
        "hough_threshold_oblique": 60,
        "hough_threshold_horizontal": 60,
        "maxLineGap_oblique": 35
      },
      "sam": {
        "processing.y_bounds": [
          4000,
          13300
        ]
      }
    },
    "proxy_scaled": 0.5584773809607314,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.2030842395531044,
      "sam_fill_rate": 0.736192592187766,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.11647231943018957
    },
    "recentre_residual_max_cm": 1.4,
    "full_pipeline": false,
    "rationale": "This overlay is deliberately different from round 1. The minimum curvature threshold limits surface interpolation across sharp seam structure. Raising the binary and Hough thresholds and shortening the allowed oblique gap rejects the weak fragments introduced by the relaxed detector, while a moderate horizontal threshold retains fallback support. Moving the SAM lower bound to 4000 trades the round-1 marginal fill gain for cleaner, more geometrically supported masks. Vertical detection remains untouched because ring count is already exact.",
    "proposer": "GPT-5.6 (fresh per-case agent)"
  },
  {
    "round": 3,
    "status": "ok",
    "overlay": {
      "enhancing": {
        "curvature_threshold": 0.0004
      },
      "detecting": {
        "binary_threshold": 140,
        "hough_threshold_oblique": 65,
        "hough_threshold_horizontal": 65,
        "maxLineGap_oblique": 30
      },
      "sam": {
        "processing.y_bounds": [
          4200,
          13300
        ]
      }
    },
    "proxy_scaled": 0.5703904743185979,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.2264802736926521,
      "sam_fill_rate": 0.7323801185939408,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.11568302726270038
    },
    "recentre_residual_max_cm": 1.4,
    "full_pipeline": false,
    "rationale": "An intermediate curvature threshold of 0.0004 should recover some surface continuity while remaining close to round 2's seam-preserving minimum. Slightly stronger binary and Hough thresholds with a shorter line gap continue filtering weak bridged responses visible near the sparse map ends. Raising the flat SAM lower bound from 4000 to 4200 follows the improvement from 3600 to 4000 but leaves margin below the allowed 4400 endpoint. Vertical detection and denoising remain unchanged because ring count is exact and there is no evidence of radial-gate failure.",
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
`/home/boringtao/Projects/Proxy4Tun/data/sc-general/stage3/packets-gpt56/1-3/round3_proposal.json`

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
