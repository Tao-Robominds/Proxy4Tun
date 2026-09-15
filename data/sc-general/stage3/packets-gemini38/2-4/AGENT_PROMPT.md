# Gemini 3.8 reflection — subset 2-4 (propose round 3)

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

- subset: `2-4`
- family: `t1&2`
- lining_mode: `staggered`
- stage1_unlocked: `False` (residual gate 10 cm)
- arm: `gemini38` / proposer: `Gemini-3.8 (fresh per-case agent)`
- model: `inherit`

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
      "denoising": {
        "mask_r_low": 2.35,
        "mask_r_high": 2.82,
        "z_step": 0.002,
        "grad_threshold": 0.18
      },
      "enhancing": {
        "curvature_threshold": 0.0008,
        "inter_radius": 0.07
      },
      "detecting": {
        "binary_threshold": 110,
        "hough_threshold_oblique": 45,
        "hough_threshold_horizontal": 50,
        "hough_threshold_vertical": 500,
        "maxLineGap_oblique": 65
      },
      "sam": {
        "processing.y_bounds": [
          3900,
          13300
        ]
      }
    },
    "proxy_scaled": 0.6974264324244448,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.4433171652821742,
      "sam_fill_rate": 0.756864413374491,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.1064098364109042
    },
    "recentre_residual_max_cm": 1.7,
    "full_pipeline": false,
    "rationale": "Round 1 maximizes explained staggered joints: more permissive oblique Hough + larger maxLineGap to bridge discontinuous staggered seams, slightly lower binary threshold for joint pixels, modest inter_radius bump for joint contrast, and y_bounds lower=3900 to keep the staggered band inside SAM processing without over-trimming the top.",
    "proposer": "Gemini-3.8 (fresh per-case agent)"
  },
  {
    "round": 2,
    "status": "ok",
    "overlay": {
      "denoising": {
        "mask_r_low": 2.4,
        "mask_r_high": 2.85,
        "z_step": 0.0015,
        "grad_threshold": 0.2
      },
      "enhancing": {
        "curvature_threshold": 0.002,
        "inter_radius": 0.055
      },
      "detecting": {
        "binary_threshold": 127,
        "hough_threshold_oblique": 55,
        "hough_threshold_horizontal": 55,
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
    "proxy_scaled": 0.7084007362754263,
    "band": "accept",
    "features": {
      "correspondence_f1@15": 0.47011388385440744,
      "sam_fill_rate": 0.747650125807372,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.11204591694636366
    },
    "recentre_residual_max_cm": 1.7,
    "full_pipeline": false,
    "rationale": "Round 2 is SAM-window\u2013led and distinct from R1's permissive Hough: raise y_bounds lower to 4300 to trim soft top clutter and centre the staggered band, hold oblique Hough near notebook prior (55/45), use denser z_step for cleaner depth cues, and slightly raise curvature_threshold to reduce surface-noise false joints that create unsupported (red) boundaries.",
    "proposer": "Gemini-3.8 (fresh per-case agent)"
  },
  {
    "round": 3,
    "status": "ok",
    "overlay": {
      "denoising": {
        "mask_r_low": 2.45,
        "mask_r_high": 2.88,
        "z_step": 0.003,
        "grad_threshold": 0.22
      },
      "enhancing": {
        "curvature_threshold": 0.0012,
        "inter_radius": 0.04
      },
      "detecting": {
        "binary_threshold": 140,
        "hough_threshold_oblique": 75,
        "hough_threshold_horizontal": 70,
        "hough_threshold_vertical": 650,
        "maxLineGap_oblique": 55
      },
      "sam": {
        "processing.y_bounds": [
          4050,
          13300
        ]
      }
    },
    "proxy_scaled": 0.6860214318957727,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.4261245737175118,
      "sam_fill_rate": 0.7556551062229254,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.11452886312339403
    },
    "recentre_residual_max_cm": 1.7,
    "full_pipeline": false,
    "rationale": "Round 3 is the tighten-and-stabilize arm, opposite of R1's relax-oblique bet: higher oblique/horizontal thresholds, mid maxLineGap (55) to keep true staggered continuity without fragment spam, binary_threshold 140 to thin noise, reduced inter_radius to limit joint smear, and y_bounds lower=4050 as a compromise crop between R1 and R2.",
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
`/home/boringtao/Projects/Proxy4Tun/data/sc-general/stage3/packets-gemini38/2-4/round3_proposal.json`

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
