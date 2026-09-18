# Gemini 3.8 reflection — subset 1-4 (propose round 3)

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

- subset: `1-4`
- family: `t1&2`
- lining_mode: `staggered`
- stage1_unlocked: `False` (residual gate 10 cm)
- arm: `gemini38` / proposer: `Gemini-3.8 (fresh per-case agent)`
- model: `inherit`

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
      "detecting": {
        "binary_threshold": 115,
        "hough_threshold_oblique": 45,
        "hough_threshold_horizontal": 45,
        "hough_threshold_vertical": 520,
        "maxLineGap_oblique": 60
      }
    },
    "proxy_scaled": 0.6054802428291137,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.32054994782817336,
      "sam_fill_rate": 0.6983460057511969,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.14983039763025083
    },
    "recentre_residual_max_cm": 1.9,
    "full_pipeline": false,
    "rationale": "stage1_unlocked=false and residual is fine, so skip unfolding. Vertical structure is already correct; the proxy bottleneck is joint\u2194boundary correspondence under staggered offsets. Lowering binary/horizontal/oblique thresholds and raising maxLineGap_oblique should recover more real joint segments that currently appear as unexplained orange lines, improving prompt loci without inventing extra rings.",
    "proposer": "Gemini-3.8 (fresh per-case agent)"
  },
  {
    "round": 2,
    "status": "ok",
    "overlay": {
      "enhancing": {
        "curvature_threshold": 0.00035,
        "inter_radius": 0.07
      },
      "detecting": {
        "binary_threshold": 120,
        "hough_threshold_oblique": 50,
        "hough_threshold_horizontal": 48,
        "maxLineGap_oblique": 50
      }
    },
    "proxy_scaled": 0.6219776995528858,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.3544448754178903,
      "sam_fill_rate": 0.6978004014742626,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.15886859418282548
    },
    "recentre_residual_max_cm": 1.9,
    "full_pipeline": false,
    "rationale": "Depth_threshold_low/high are the empirically strongest t1&2 knobs but are outside this packet's writable bounds, so use the available enhancing pair to densify joint support. Slightly lower curvature_threshold keeps more high-curvature seam points; a modestly larger inter_radius fills staggered joint gaps. Mild Hough relax then harvests the improved outlier map without flooding spurious lines.",
    "proposer": "Gemini-3.8 (fresh per-case agent)"
  },
  {
    "round": 3,
    "status": "ok",
    "overlay": {
      "denoising": {
        "grad_threshold": 0.18,
        "z_step": 0.002
      },
      "detecting": {
        "hough_threshold_vertical": 600,
        "binary_threshold": 130
      },
      "sam": {
        "processing.y_bounds": [
          4000,
          13300
        ]
      }
    },
    "proxy_scaled": 0.5947875075192546,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.29585064363950275,
      "sam_fill_rate": 0.7026602113368274,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.14195602315445302
    },
    "recentre_residual_max_cm": 1.9,
    "full_pipeline": false,
    "rationale": "Distinct from rounds 1\u20132: keep detection mostly conservative and move the circumferential window so staggered K/AB templates land on the lining rather than clipping edge joints. y_bounds=[4000,13300] recentres the crop; a slightly stricter vertical Hough (600) suppresses the extra orange mid-column verticals seen in detected_lines; light grad/z_step polish reduces salt-noise that inflates segment-size CV without chasing NaN to zero.",
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
`/home/boringtao/Projects/Proxy4Tun/data/sc-general/stage3/packets-gemini38/1-4/round3_proposal.json`

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
