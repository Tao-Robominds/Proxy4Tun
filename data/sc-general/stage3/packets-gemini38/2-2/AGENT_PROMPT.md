# Gemini 3.8 reflection — subset 2-2 (propose round 3)

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

- subset: `2-2`
- family: `t1&2`
- lining_mode: `staggered`
- stage1_unlocked: `False` (residual gate 10 cm)
- arm: `gemini38` / proposer: `Gemini-3.8 (fresh per-case agent)`
- model: `inherit`

### Anchor (GT-blind)
```json
{
  "proxy_raw": 0.699142,
  "proxy_scaled": 0.699142,
  "band": "refine",
  "features": {
    "correspondence_f1@15": 0.455,
    "sam_fill_rate": 0.743164,
    "ring_count_error": 0.0,
    "depth_nan_ratio": 0.111005
  },
  "recentre_residual_max_cm": 1.5,
  "orient_axis_corr": -0.9998899225490308,
  "ring_count": 10,
  "ring_count_error": 0.0,
  "labelmap_source": "results.pkl",
  "run_dir": "/home/boringtao/Projects/Proxy4Tun/data/bo/unified/2-2-family-proxy/runs/2-2-anchor"
}
```

### Intrinsics (GT-blind)
```json
{
  "orient_axis_corr": -0.9998899225490308,
  "orient_invariant_ok": 1.0,
  "recentre_residual_max_cm": 1.5,
  "denoise_retained_ratio": 0.7711390480524585,
  "depth_nan_ratio": 0.11100505152955387,
  "depth_outlier_ratio": 0.003969557138198945,
  "det_real_detection_ratio": 0.9,
  "det_fallback_ratio": 0.1,
  "det_n_points": 10.0,
  "sam_fill_rate": 0.7431639534162133,
  "sam_ring_completeness": 0.8888888888888888,
  "sam_segment_size_cv": 1.1492356762263811,
  "sam_ontology_divergence": 0.16496563728120134
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
        "grad_threshold": 0.15,
        "z_step": 0.002
      },
      "enhancing": {
        "curvature_threshold": 0.0008,
        "inter_radius": 0.05
      },
      "detecting": {
        "binary_threshold": 115,
        "hough_threshold_oblique": 45,
        "hough_threshold_horizontal": 55,
        "hough_threshold_vertical": 500,
        "maxLineGap_oblique": 60
      },
      "sam": {
        "processing.y_bounds": [
          3900,
          13300
        ]
      }
    },
    "proxy_scaled": 0.7208574032061854,
    "band": "accept",
    "features": {
      "correspondence_f1@15": 0.49264088572800957,
      "sam_fill_rate": 0.745931158595867,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.10908252811888819
    },
    "recentre_residual_max_cm": 1.5,
    "full_pipeline": false,
    "rationale": "Round-1 detection-led path: lower binary/oblique thresholds and widen oblique gaps to recover staggered zig-zag joints that currently appear as orange unexplained lines, with mild enhancing support and a modest y_bounds lower nudge. No unfolding (stage1_unlocked=false); full=false.",
    "proposer": "Gemini-3.8 (fresh per-case agent)"
  },
  {
    "round": 2,
    "status": "ok",
    "overlay": {
      "denoising": {
        "mask_r_low": 2.35,
        "mask_r_high": 2.85,
        "grad_threshold": 0.18
      },
      "enhancing": {
        "curvature_threshold": 0.0004,
        "inter_radius": 0.04
      },
      "detecting": {
        "binary_threshold": 130,
        "hough_threshold_oblique": 55,
        "hough_threshold_horizontal": 50,
        "hough_threshold_vertical": 550,
        "maxLineGap_oblique": 45
      },
      "sam": {
        "processing.y_bounds": [
          4300,
          13300
        ]
      }
    },
    "proxy_scaled": 0.7569000450659074,
    "band": "accept",
    "features": {
      "correspondence_f1@15": 0.5576144896139683,
      "sam_fill_rate": 0.7470326624330307,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.10790651714084432
    },
    "recentre_residual_max_cm": 1.5,
    "full_pipeline": false,
    "rationale": "Round-2 SAM-geometry path: raise processing.y_bounds lower to 4300 to recentre the staggered template stack, sensitize curvature enhancement, and keep Hough near mid-prior (not the R1 relax). Mild radial mask retune only. Distinct from R1\u2019s detection-first relax. No unfolding; full=false.",
    "proposer": "Gemini-3.8 (fresh per-case agent)"
  },
  {
    "round": 3,
    "status": "ok",
    "overlay": {
      "denoising": {
        "mask_r_low": 2.25,
        "mask_r_high": 2.88,
        "z_step": 0.0015,
        "grad_threshold": 0.12
      },
      "enhancing": {
        "curvature_threshold": 0.0012,
        "inter_radius": 0.06
      },
      "detecting": {
        "binary_threshold": 120,
        "hough_threshold_oblique": 50,
        "hough_threshold_horizontal": 60,
        "hough_threshold_vertical": 450,
        "maxLineGap_oblique": 70
      },
      "sam": {
        "processing.y_bounds": [
          4100,
          13300
        ]
      }
    },
    "proxy_scaled": 0.7157462421090537,
    "band": "accept",
    "features": {
      "correspondence_f1@15": 0.48667655655806746,
      "sam_fill_rate": 0.7353618931386137,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.10419617841474517
    },
    "recentre_residual_max_cm": 1.5,
    "full_pipeline": false,
    "rationale": "Round-3 coverage/retention path: widen radial gate toward more lining retention, denser z_step, larger oblique gap (70) at notebook-like oblique threshold (50), vertical slightly softer (450), and y_bounds=4100 between R1 and R2. Distinct multi-stage combination. No unfolding; full=false.",
    "proposer": "Gemini-3.8 (fresh per-case agent)"
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
`/home/boringtao/Projects/Proxy4Tun/data/sc-general/stage3/packets-gemini38/2-2/round3_proposal.json`

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
