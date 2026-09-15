# Fable 5.1 reflection — subset 3-10 (propose round 3)

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
- `data/sc-general/stage3/selections/`, `selections-fable/`, `selections-fable-fresh/`,
  `selections-gpt56/`, `selections-gemini38/`, `selections-random/`
- any other cases' proposals, or `data/refinement/` trees for any arm
- `data/bo/`, `data/anchors/`, `data/baseline`

## State

- subset: `3-10`
- family: `t3`
- lining_mode: `continuous`
- stage1_unlocked: `True` (residual gate 10 cm)
- arm: `fable_fresh` / proposer: `Fable-5.1 (fresh per-case agent)`
- model: `claude-fable-5-1-thinking-high`

### Anchor (GT-blind)
```json
{
  "proxy_raw": 0.588697,
  "proxy_scaled": 0.588697,
  "band": "refine",
  "features": {
    "correspondence_f1@15": 0.287265,
    "sam_fill_rate": 0.697553,
    "ring_count_error": 0.0,
    "depth_nan_ratio": 0.142028
  },
  "recentre_residual_max_cm": 10.2,
  "orient_axis_corr": -0.9990592937874491,
  "ring_count": 10,
  "ring_count_error": 0.0,
  "labelmap_source": "results.pkl",
  "run_dir": "/home/boringtao/Projects/Proxy4Tun/data/bo/unified/3-10-family-proxy/runs/3-10-anchor"
}
```

### Intrinsics (GT-blind)
```json
{
  "orient_axis_corr": -0.9990592937874491,
  "orient_invariant_ok": 1.0,
  "recentre_residual_max_cm": 10.2,
  "denoise_retained_ratio": 0.7404734761200185,
  "depth_nan_ratio": 0.14202755710717666,
  "depth_outlier_ratio": 0.0008614399729785715,
  "det_real_detection_ratio": 0.0,
  "det_fallback_ratio": 1.0,
  "det_n_points": 10.0,
  "sam_fill_rate": 0.697552574768962,
  "sam_ring_completeness": 1.0,
  "sam_segment_size_cv": 0.5772969297747274,
  "sam_ontology_divergence": 0.2235725711106475
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
        "binary_threshold": 110,
        "hough_threshold_oblique": 24,
        "hough_threshold_horizontal": 24,
        "maxLineGap_oblique": 45,
        "uniform_k_snap": true
      },
      "sam": {
        "segment_width": 1220
      }
    },
    "proxy_scaled": 0.6189325416971054,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.34338772120396893,
      "sam_fill_rate": 0.6959718954406902,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.14202755710717666
    },
    "recentre_residual_max_cm": 10.2,
    "full_pipeline": false,
    "rationale": "Round 1 targets the weakest lean feature (correspondence F1) by raising true-joint line yield: a lower binary_threshold (127 -> 110) keeps the faint dotted outlier pixels along the A/B joints, lower oblique/horizontal Hough thresholds (30 -> 24) let the left rings' K edges and the y~800 / y~2300 joint rows reach the accumulator, and a larger oblique maxLineGap (30 -> 45) bridges the dotted rows into long segments that can be matched to the label boundaries. Thresholds are kept moderate (not the 20 floor) to limit spurious lines on the bolt-hole rows that sit ~80-100 px from the K edges. The K-row snap and the vertical accumulator are unchanged so ring_count_error stays 0 and the prompt row stays pinned. segment_width is nudged 1200 -> 1220 mm to match the ~1.22 m ring pitch and close the inter-column gutters, a small fill-rate gain. Unfolding is deliberately not touched: the residual is only 0.2 cm over the gate, orientation is pinned, and re-rolling stage 1 would confound attribution of the detection change.",
    "proposer": "Fable-5.1 (fresh per-case agent)"
  },
  {
    "round": 2,
    "status": "ok",
    "overlay": {
      "detecting": {
        "binary_threshold": 100,
        "hough_threshold_oblique": 22,
        "hough_threshold_horizontal": 20,
        "maxLineGap_oblique": 60,
        "uniform_k_snap": true
      },
      "sam": {
        "segment_width": 1220
      }
    },
    "proxy_scaled": 0.5764525789292108,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.26533451449825385,
      "sam_fill_rate": 0.6965863794762333,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.14202755710717666
    },
    "recentre_residual_max_cm": 10.2,
    "full_pipeline": false,
    "rationale": "Round 2 pushes the same detection lever one step further to recover the two long AB joint rows and the missing left-side upper-K-edge obliques. binary_threshold 110 -> 100 (bound floor) keeps the faintest joint outlier pixels so the dotted rows at y~810 and y~2320 densify enough for the fixed 10 px horizontal gap to bridge them; hough_threshold_horizontal 24 -> 20 (floor) lets the resulting runs vote in; hough_threshold_oblique 24 -> 22 (moderate, not floor) targets the faint upper-K-edge dots in rings 1-5 while limiting spurious obliques on the dense bolt-pocket column of ring 10; maxLineGap_oblique 45 -> 60 (ceiling) lets the K-edge segments span the bolt-pocket interruptions so each ring gets one long edge line instead of fragments. Spurious-line risk is contained: bolt pockets are ~30 px squares spaced one ring pitch apart, below minLineLength for both Hough paths and far beyond the 10 px horizontal gap. uniform_k_snap stays true and the vertical accumulator is untouched so the 10 verticals and the pinned prompt row are preserved (ring_count_error 0). segment_width stays 1220 mm (matches the measured 244 px pitch). K_height/angle are not changed because the K template edges already coincide with the detected obliques (cyan in the overlay). Unfolding is deliberately not included again: residual is only 0.2 cm over the gate, orientation is pinned, and a --full rerun would confound attribution of the detection change; if round 2 plateaus, round 3 can revisit.",
    "proposer": "Fable-5.1 (fresh per-case agent)"
  },
  {
    "round": 3,
    "status": "ok",
    "overlay": {
      "detecting": {
        "binary_threshold": 110,
        "hough_threshold_oblique": 24,
        "hough_threshold_horizontal": 24,
        "maxLineGap_oblique": 60,
        "uniform_k_snap": true
      },
      "sam": {
        "segment_width": 1220
      }
    },
    "proxy_scaled": 0.5828488627138813,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.27718965984683874,
      "sam_fill_rate": 0.6962872227747189,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.14202755710717666
    },
    "recentre_residual_max_cm": 10.2,
    "full_pipeline": false,
    "rationale": "Round 3 is a single-lever isolation of the one round-2 change the artifacts credit with higher true-line yield: return every detection knob to the round-1 setting that produced the best proxy (binary_threshold 110, hough_threshold_oblique 24, hough_threshold_horizontal 24, uniform_k_snap true) and carry forward only maxLineGap_oblique 60 (ceiling). Mechanism: HoughLinesP votes come from pixels, not from bridged gaps, so restoring the round-1 binarisation and oblique vote threshold removes the low-vote 50-100 px bolt-pocket segments that appeared in round 2, while the larger gap still lets each ring's K-edge dots span the ~30 px bolt-pocket interruptions and emerge as one long segment per ring (round 2 recovered ring 5's upper edge this way). Longer, fewer segments per edge raise the fraction of lines explained by a template boundary (precision) and keep the round-1 boundary support (recall), which is what correspondence_f1@15 rewards. Expected outcome is at or above round 1 (0.619); if the gap change alone is neutral, the round-1 baseline is reproduced and selection keeps round 1. hough_threshold_horizontal returns to 24 because 20 produced no additional horizontal segments (the fixed 10 px gap is binding), so the lower value only adds noise risk. hough_threshold_vertical is untouched so the 10 verticals and the propagated prompt row (ring_count_error 0) are preserved. segment_width stays at 1220 mm so the only difference from round 1 is the oblique gap; fill rate has been flat within 0.002 across 1200/1220 and is not the lever here. K_height and angle are left at prior because the template K edges already lie within ~15 px of the detected obliques. Unfolding is not included: residual 10.2 cm is 0.2 cm over the gate, orientation is pinned, and a --full rerun would confound attribution in the final round.",
    "proposer": "Fable-5.1 (fresh per-case agent)"
  }
]
```

### Parameter bounds (ONLY these keys; reject anything else)
- `unfolding.ransac_threshold` (float): [0.8, 1.2]
- `unfolding.slice_spacing_factor` (float): [1.05, 1.35]
- `unfolding.polynomial_degree` (int): [2, 3]
- `unfolding.random_seed` (int): [0, 7]
- `denoising.mask_r_low` (float): [2.7, 3.0]
- `denoising.mask_r_high` (float): [2.9, 3.15]
- `denoising.mask_theta_low` (float): [1.0, 2.5]
- `denoising.mask_theta_high` (float): [15.0, 19.0]
- `enhancing.curvature_threshold` (float): [0.0002, 0.002]
- `detecting.binary_threshold` (int): [100, 160]
- `detecting.hough_threshold_oblique` (int): [20, 60]
- `detecting.hough_threshold_horizontal` (int): [20, 60]
- `detecting.hough_threshold_vertical` (int): [800, 2500]
- `detecting.maxLineGap_oblique` (int): [10, 60]
- `detecting.pattern_tolerance` (int): [5, 20]
- `detecting.uniform_k_snap` (bool): [0.0, 1.0]
- `sam.segment_width` (int): [1000, 1400]
- `sam.K_height` (float): [700.0, 1000.0]
- `sam.angle` (float): [4.0, 9.0]

## Required output

Write a single JSON object to:
`/home/boringtao/Projects/Proxy4Tun/data/sc-general/stage3/packets-fable-fresh/3-10/round3_proposal.json`

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
