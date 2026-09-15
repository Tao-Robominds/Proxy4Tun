# Gemini 3.8 reflection — subset 5-4 (propose round 3)

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

- subset: `5-4`
- family: `t4&5`
- lining_mode: `complex`
- stage1_unlocked: `False` (residual gate 10 cm)
- arm: `gemini38` / proposer: `Gemini-3.8 (fresh per-case agent)`
- model: `inherit`

### Anchor (GT-blind)
```json
{
  "proxy_raw": 0.692326,
  "proxy_scaled": 0.692326,
  "band": "refine",
  "features": {
    "correspondence_f1@15": 0.467401,
    "sam_fill_rate": 0.759939,
    "ring_count_error": 0.0,
    "depth_nan_ratio": 0.19849
  },
  "recentre_residual_max_cm": 2.1,
  "orient_axis_corr": -0.7738736413768053,
  "ring_count": 10,
  "ring_count_error": 0.0,
  "labelmap_source": "only_label.csv",
  "run_dir": "/home/boringtao/Projects/Proxy4Tun/data/bo/unified/5-4-family-proxy/runs/5-4-anchor"
}
```

### Intrinsics (GT-blind)
```json
{
  "orient_axis_corr": -0.7738736413768053,
  "orient_invariant_ok": 1.0,
  "recentre_residual_max_cm": 2.1,
  "denoise_retained_ratio": 0.771714565621628,
  "depth_nan_ratio": 0.19848996720212705,
  "depth_outlier_ratio": 0.00134290457193032,
  "det_real_detection_ratio": 0.7,
  "det_fallback_ratio": 0.3,
  "det_n_points": 10.0,
  "sam_fill_rate": 0.7599389968796842,
  "sam_ring_completeness": 1.0,
  "sam_segment_size_cv": 1.1070596715680279,
  "sam_ontology_divergence": 0.14195278326436073
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
        "hough_threshold_oblique": 40,
        "maxLineGap_oblique": 55,
        "pattern_tolerance": 12
      },
      "sam": {
        "segment_width": 1800,
        "K_height": 1227.0,
        "angle": 9.8
      }
    },
    "proxy_scaled": 0.6914538998202636,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.46580458414732695,
      "sam_fill_rate": 0.7599389968796842,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.19848996720212705
    },
    "recentre_residual_max_cm": 2.1,
    "full_pipeline": false,
    "rationale": "Anchor SAM to t4&5 notebook priors (segment_width 1800, K_height \u22481227 mm, angle 9.8\u00b0) so K crops sit on the white-dot clusters rather than empty dark bands. Mildly relax oblique Hough and pattern tolerance so taper joints feed the distance check without touching unfolding (stage1_unlocked=false).",
    "proposer": "Gemini-3.8 (fresh per-case agent)"
  },
  {
    "round": 2,
    "status": "ok",
    "overlay": {
      "detecting": {
        "binary_threshold": 115,
        "hough_threshold_oblique": 30,
        "hough_threshold_horizontal": 35,
        "maxLineGap_oblique": 70,
        "maxLineGap_horizontal": 15,
        "pattern_tolerance": 18
      },
      "sam": {
        "segment_width": 1950,
        "K_height": 1350.0,
        "angle": 11.0
      }
    },
    "proxy_scaled": 0.649542053849919,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.3890960819963321,
      "sam_fill_rate": 0.7599389968796842,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.19848996720212705
    },
    "recentre_residual_max_cm": 2.1,
    "full_pipeline": false,
    "rationale": "Detection-led round distinct from prior-anchored SAM: lower oblique/horizontal Hough thresholds, raise maxLineGap_oblique, and open pattern_tolerance so taper joints register before SAM. Pair with slightly wider segment_width and mid\u2013high K_height (still above empty-crop risk) and a modestly steeper angle than notebook 9.8\u00b0 to absorb observed slant.",
    "proposer": "Gemini-3.8 (fresh per-case agent)"
  },
  {
    "round": 3,
    "status": "ok",
    "overlay": {
      "denoising": {
        "mask_r_low": 3.55,
        "mask_r_high": 3.95
      },
      "enhancing": {
        "curvature_threshold": 0.00035
      },
      "detecting": {
        "hough_threshold_vertical": 2500,
        "hough_threshold_oblique": 45,
        "pattern_tolerance": 10
      },
      "sam": {
        "segment_width": 1650,
        "K_height": 1450.0,
        "angle": 8.0
      }
    },
    "proxy_scaled": 0.4838552305079739,
    "band": "reject",
    "features": {
      "correspondence_f1@15": 0.0835802376557293,
      "sam_fill_rate": 0.7646176781020204,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.19862573028393257
    },
    "recentre_residual_max_cm": 2.1,
    "full_pipeline": false,
    "rationale": "Third distinct axis: slight denoise widen + lower curvature_threshold to enrich joint contrast, keep verticals synthetic-friendly (high vertical threshold), and use a tall K_height (1450) with tighter segment_width (1650) and lower angle (8.0\u00b0) so K crops cover the white-dot tiers without empty dark-band crops.",
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
`/home/boringtao/Projects/Proxy4Tun/data/sc-general/stage3/packets-gemini38/5-4/round3_proposal.json`

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
