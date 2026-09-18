# Gemini 3.8 reflection — subset 4-1 (propose round 3)

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

- subset: `4-1`
- family: `t4&5`
- lining_mode: `complex`
- stage1_unlocked: `False` (residual gate 10 cm)
- arm: `gemini38` / proposer: `Gemini-3.8 (fresh per-case agent)`
- model: `inherit`

### Anchor (GT-blind)
```json
{
  "proxy_raw": 0.551819,
  "proxy_scaled": 0.551819,
  "band": "refine",
  "features": {
    "correspondence_f1@15": 0.225171,
    "sam_fill_rate": 0.748831,
    "ring_count_error": 0.0,
    "depth_nan_ratio": 0.223307
  },
  "recentre_residual_max_cm": 2.4,
  "orient_axis_corr": 0.9398124965718192,
  "ring_count": 10,
  "ring_count_error": 0.0,
  "labelmap_source": "only_label.csv",
  "run_dir": "/home/boringtao/Projects/Proxy4Tun/data/bo/unified/4-1-family-proxy/runs/4-1-anchor"
}
```

### Intrinsics (GT-blind)
```json
{
  "orient_axis_corr": 0.9398124965718192,
  "orient_invariant_ok": 1.0,
  "recentre_residual_max_cm": 2.4,
  "denoise_retained_ratio": 0.7583892868338517,
  "depth_nan_ratio": 0.22330735765617338,
  "depth_outlier_ratio": 0.0010889418251959948,
  "det_real_detection_ratio": 0.4,
  "det_fallback_ratio": 0.6,
  "det_n_points": 10.0,
  "sam_fill_rate": 0.7488305972058229,
  "sam_ring_completeness": 1.0,
  "sam_segment_size_cv": 1.0601700064349866,
  "sam_ontology_divergence": 0.10154601537508416
}
```

### Prior rounds (this arm only)
```json
[
  {
    "round": 1,
    "status": "ok",
    "overlay": {
      "sam": {
        "segment_width": 1800,
        "K_height": 1227.0,
        "angle": 9.8
      }
    },
    "proxy_scaled": 0.5644755167715193,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.2478053788037397,
      "sam_fill_rate": 0.7498783735648481,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.22328257687193515
    },
    "recentre_residual_max_cm": 2.4,
    "full_pipeline": false,
    "rationale": "Round 1 pins SAM crops to T4 notebook priors (segment_width=1800, K_height\u22481227, angle=9.8). Keep K_height at prior\u2014not high\u2014to avoid empty-crop into white bands. Omit unfolding (stage1_unlocked=false); full=false.",
    "proposer": "Gemini-3.8 (fresh per-case agent)"
  },
  {
    "round": 2,
    "status": "ok",
    "overlay": {
      "detecting": {
        "hough_threshold_oblique": 35,
        "maxLineGap_oblique": 65,
        "pattern_tolerance": 12
      },
      "sam": {
        "segment_width": 1750,
        "K_height": 1200.0,
        "angle": 10.5
      }
    },
    "proxy_scaled": 0.5591372536055437,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.238035105935311,
      "sam_fill_rate": 0.7498783735648481,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.22328257687193515
    },
    "recentre_residual_max_cm": 2.4,
    "full_pipeline": false,
    "rationale": "Distinct from round 1: prioritize recovering real oblique joints that can explain SC boundaries, then slightly raise angle (10.5) and keep K_height at 1200 (below prior) to reduce empty-crop risk on white bands. Mild pattern_tolerance widen helps distance-pattern match. full=false; no unfolding.",
    "proposer": "Gemini-3.8 (fresh per-case agent)"
  },
  {
    "round": 3,
    "status": "ok",
    "overlay": {
      "detecting": {
        "pattern_tolerance": 8,
        "hough_threshold_horizontal": 40,
        "maxLineGap_horizontal": 15
      },
      "sam": {
        "segment_width": 1950,
        "K_height": 1150.0,
        "angle": 8.5
      }
    },
    "proxy_scaled": 0.6082611962626933,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.3285372946097015,
      "sam_fill_rate": 0.748681601485044,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.22328257687193515
    },
    "recentre_residual_max_cm": 2.4,
    "full_pipeline": false,
    "rationale": "Distinct from rounds 1\u20132: widen segment_width to 1950 and drop K_height to 1150 (explicitly anti-empty-crop) with angle 8.5 (shallower taper) plus tighter pattern_tolerance=8. Optional slight horizontal Hough relax to stabilize blue joint loci used as crop anchors. full=false; stage1 locked.",
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
`/home/boringtao/Projects/Proxy4Tun/data/sc-general/stage3/packets-gemini38/4-1/round3_proposal.json`

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
