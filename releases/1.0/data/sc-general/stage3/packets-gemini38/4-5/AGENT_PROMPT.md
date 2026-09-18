# Gemini 3.8 reflection — subset 4-5 (propose round 3)

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

- subset: `4-5`
- family: `t4&5`
- lining_mode: `complex`
- stage1_unlocked: `False` (residual gate 10 cm)
- arm: `gemini38` / proposer: `Gemini-3.8 (fresh per-case agent)`
- model: `inherit`

### Anchor (GT-blind)
```json
{
  "proxy_raw": 0.609357,
  "proxy_scaled": 0.609357,
  "band": "refine",
  "features": {
    "correspondence_f1@15": 0.334208,
    "sam_fill_rate": 0.735359,
    "ring_count_error": 0.0,
    "depth_nan_ratio": 0.215522
  },
  "recentre_residual_max_cm": 3.4,
  "orient_axis_corr": 0.9810109979941607,
  "ring_count": 10,
  "ring_count_error": 0.0,
  "labelmap_source": "only_label.csv",
  "run_dir": "/home/boringtao/Projects/Proxy4Tun/data/bo/unified/4-5-family-proxy/runs/4-5-anchor"
}
```

### Intrinsics (GT-blind)
```json
{
  "orient_axis_corr": 0.9810109979941607,
  "orient_invariant_ok": 1.0,
  "recentre_residual_max_cm": 3.4,
  "denoise_retained_ratio": 0.7441345095804333,
  "depth_nan_ratio": 0.21552237876528763,
  "depth_outlier_ratio": 0.0010049970802387977,
  "det_real_detection_ratio": 0.6,
  "det_fallback_ratio": 0.4,
  "det_n_points": 10.0,
  "sam_fill_rate": 0.7353592515275288,
  "sam_ring_completeness": 1.0,
  "sam_segment_size_cv": 1.0538854727707543,
  "sam_ontology_divergence": 0.10294109747787984
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
        "mask_r_low": 3.6,
        "mask_r_high": 3.95
      },
      "enhancing": {
        "curvature_threshold": 0.0008
      },
      "detecting": {
        "binary_threshold": 120,
        "hough_threshold_oblique": 40,
        "hough_threshold_horizontal": 35,
        "hough_threshold_vertical": 3000,
        "maxLineGap_oblique": 60,
        "maxLineGap_horizontal": 12,
        "pattern_tolerance": 12
      },
      "sam": {
        "segment_width": 1800,
        "K_height": 1220.0,
        "angle": 9.8
      }
    },
    "proxy_scaled": 0.622322610130644,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.353622556825344,
      "sam_fill_rate": 0.7402578916134278,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.21055414701923944
    },
    "recentre_residual_max_cm": 3.4,
    "full_pipeline": false,
    "rationale": "Re-anchor SAM to T4 prior taper (~9.8\u00b0) and mid K_height (~1220mm, well below empty-crop risk at the upper bound) with notebook segment_width=1800. Slightly loosen oblique Hough and pattern_tolerance so angled key joints become explainable without retuning stage-1.",
    "proposer": "Gemini-3.8 (fresh per-case agent)"
  },
  {
    "round": 2,
    "status": "ok",
    "overlay": {
      "denoising": {
        "mask_r_low": 3.55,
        "mask_r_high": 4.0
      },
      "enhancing": {
        "curvature_threshold": 0.0005
      },
      "detecting": {
        "binary_threshold": 110,
        "hough_threshold_oblique": 32,
        "hough_threshold_horizontal": 28,
        "hough_threshold_vertical": 2500,
        "maxLineGap_oblique": 75,
        "maxLineGap_horizontal": 18,
        "pattern_tolerance": 15
      },
      "sam": {
        "segment_width": 1600,
        "K_height": 1100.0,
        "angle": 8.0
      }
    },
    "proxy_scaled": 0.5773768400927489,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.2736115010179347,
      "sam_fill_rate": 0.7367970461717438,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.21195838913670592
    },
    "recentre_residual_max_cm": 3.4,
    "full_pipeline": false,
    "rationale": "Compact SAM geometry (width 1600, K_height 1100, angle 8.0) to avoid empty-crop K boxes around the longitudinal white strip, with looser oblique maxLineGap to reconnect fragmented angled joints that currently stay orange.",
    "proposer": "Gemini-3.8 (fresh per-case agent)"
  },
  {
    "round": 3,
    "status": "ok",
    "overlay": {
      "denoising": {
        "mask_r_low": 3.65,
        "mask_r_high": 3.9
      },
      "enhancing": {
        "curvature_threshold": 0.0012
      },
      "detecting": {
        "binary_threshold": 130,
        "hough_threshold_oblique": 50,
        "hough_threshold_horizontal": 40,
        "hough_threshold_vertical": 4000,
        "maxLineGap_oblique": 50,
        "maxLineGap_horizontal": 10,
        "pattern_tolerance": 8
      },
      "sam": {
        "segment_width": 2000,
        "K_height": 1250.0,
        "angle": 11.0
      }
    },
    "proxy_scaled": 0.6133072855683316,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.33995059053107946,
      "sam_fill_rate": 0.7353592515275288,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.2116013215884911
    },
    "recentre_residual_max_cm": 3.4,
    "full_pipeline": false,
    "rationale": "Hard vertical Hough (4000) stabilizes ring columns; wider segment_width=2000 improves crop coverage of irregular complex blocks; K_height=1250 stays mid-band (not empty-crop tall); angle=11.0 targets the strongly slanted unexplained key joints without retuning centreline.",
    "proposer": "Gemini-3.8 (fresh per-case agent)"
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
`/home/boringtao/Projects/Proxy4Tun/data/sc-general/stage3/packets-gemini38/4-5/round3_proposal.json`

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
