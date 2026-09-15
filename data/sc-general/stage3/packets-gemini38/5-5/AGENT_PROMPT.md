# Gemini 3.8 reflection — subset 5-5 (propose round 3)

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

- subset: `5-5`
- family: `t4&5`
- lining_mode: `complex`
- stage1_unlocked: `False` (residual gate 10 cm)
- arm: `gemini38` / proposer: `Gemini-3.8 (fresh per-case agent)`
- model: `inherit`

### Anchor (GT-blind)
```json
{
  "proxy_raw": 0.609798,
  "proxy_scaled": 0.609798,
  "band": "refine",
  "features": {
    "correspondence_f1@15": 0.316226,
    "sam_fill_rate": 0.756178,
    "ring_count_error": 0.0,
    "depth_nan_ratio": 0.193232
  },
  "recentre_residual_max_cm": 1.9,
  "orient_axis_corr": 0.9125884650166897,
  "ring_count": 10,
  "ring_count_error": 0.0,
  "labelmap_source": "only_label.csv",
  "run_dir": "/home/boringtao/Projects/Proxy4Tun/data/bo/unified/5-5-family-proxy/runs/5-5-anchor"
}
```

### Intrinsics (GT-blind)
```json
{
  "orient_axis_corr": 0.9125884650166897,
  "orient_invariant_ok": 1.0,
  "recentre_residual_max_cm": 1.9,
  "denoise_retained_ratio": 0.7673354664684634,
  "depth_nan_ratio": 0.19323166894404062,
  "depth_outlier_ratio": 0.001291584040276335,
  "det_real_detection_ratio": 0.8,
  "det_fallback_ratio": 0.2,
  "det_n_points": 10.0,
  "sam_fill_rate": 0.7561778560970978,
  "sam_ring_completeness": 1.0,
  "sam_segment_size_cv": 1.0460848905509348,
  "sam_ontology_divergence": 0.10887649245012132
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
        "K_height": 1220.0,
        "angle": 9.8
      }
    },
    "proxy_scaled": 0.6731943507071498,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.43225615957030794,
      "sam_fill_rate": 0.7561778560970978,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.19323166894404062
    },
    "recentre_residual_max_cm": 1.9,
    "full_pipeline": false,
    "rationale": "Primary t4&5 move: retune SAM toward T5 priors (segment_width\u22481800, K\u22481227 mm, angle\u22489.8\u00b0) so keystone crops cover textured blocks without empty-crop K into white-band gaps. Pair with modest pattern_tolerance and slightly relaxed oblique Hough so prompt spacing matches tapered K blocks.",
    "proposer": "Gemini-3.8 (fresh per-case agent)"
  },
  {
    "round": 2,
    "status": "ok",
    "overlay": {
      "enhancing": {
        "curvature_threshold": 0.0004
      },
      "detecting": {
        "binary_threshold": 115,
        "hough_threshold_oblique": 30,
        "hough_threshold_horizontal": 35,
        "maxLineGap_oblique": 70,
        "maxLineGap_horizontal": 15,
        "pattern_tolerance": 15
      },
      "sam": {
        "segment_width": 1700,
        "K_height": 1150.0,
        "angle": 8.5
      }
    },
    "proxy_scaled": 0.599779519005038,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.2992134442505735,
      "sam_fill_rate": 0.7543605393142794,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.1943432714072759
    },
    "recentre_residual_max_cm": 1.9,
    "full_pipeline": false,
    "rationale": "Distinct from prior-centered SAM retune: first recover oblique joint yield so unexplained orange seams become prompt-supporting lines. Use lower K_height (1150) and milder angle (8.5\u00b0) to keep crops on textured lining (anti empty-crop) while slightly narrower segment_width (1700) matches denser mid-column stagger.",
    "proposer": "Gemini-3.8 (fresh per-case agent)"
  },
  {
    "round": 3,
    "status": "ok",
    "overlay": {
      "denoising": {
        "mask_r_low": 3.6,
        "mask_r_high": 3.95
      },
      "detecting": {
        "hough_threshold_vertical": 2000,
        "hough_threshold_oblique": 45,
        "maxLineGap_oblique": 50,
        "pattern_tolerance": 10
      },
      "sam": {
        "segment_width": 1950,
        "K_height": 1080.0,
        "angle": 11.0
      }
    },
    "proxy_scaled": 0.6199364907191045,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.3367539816813488,
      "sam_fill_rate": 0.7523257570962136,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.19339164603066195
    },
    "recentre_residual_max_cm": 1.9,
    "full_pipeline": false,
    "rationale": "Third distinct axis: anti empty-crop K_height=1080 (lower third of [1000,1500]), wider segment_width=1950 and angle=11.0 for tapered keystones, light denoise band toward T5 radius prior, and elevated vertical Hough to keep the ten-ring grid stable while oblique pattern_tolerance stays moderate.",
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
`/home/boringtao/Projects/Proxy4Tun/data/sc-general/stage3/packets-gemini38/5-5/round3_proposal.json`

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
