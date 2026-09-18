# Fable 5.1 reflection — subset 3-4 (propose round 3)

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

- subset: `3-4`
- family: `t3`
- lining_mode: `continuous`
- stage1_unlocked: `True` (residual gate 10 cm)
- arm: `fable_fresh` / proposer: `Fable-5.1 (fresh per-case agent)`
- model: `claude-fable-5-1-thinking-high`

### Anchor (GT-blind)
```json
{
  "proxy_raw": 0.519691,
  "proxy_scaled": 0.519691,
  "band": "refine",
  "features": {
    "correspondence_f1@15": 0.243977,
    "sam_fill_rate": 0.570766,
    "ring_count_error": 0.0,
    "depth_nan_ratio": 0.194979
  },
  "recentre_residual_max_cm": 20.8,
  "orient_axis_corr": -0.9984156385609421,
  "ring_count": 10,
  "ring_count_error": 0.0,
  "labelmap_source": "results.pkl",
  "run_dir": "/home/boringtao/Projects/Proxy4Tun/data/bo/unified/3-4-family-proxy/runs/3-4-anchor"
}
```

### Intrinsics (GT-blind)
```json
{
  "orient_axis_corr": -0.9984156385609421,
  "orient_invariant_ok": 1.0,
  "recentre_residual_max_cm": 20.8,
  "denoise_retained_ratio": 0.6936518019734892,
  "depth_nan_ratio": 0.19497856422227988,
  "depth_outlier_ratio": 0.0007883432849587916,
  "det_real_detection_ratio": 0.0,
  "det_fallback_ratio": 1.0,
  "det_n_points": 10.0,
  "sam_fill_rate": 0.5707661034176089,
  "sam_ring_completeness": 0.8888888888888888,
  "sam_segment_size_cv": 0.6606793479372685,
  "sam_ontology_divergence": 0.1918493785939529
}
```

### Prior rounds (this arm only)
```json
[
  {
    "round": 1,
    "status": "ok",
    "overlay": {
      "unfolding": {
        "ransac_threshold": 0.85,
        "polynomial_degree": 2,
        "random_seed": 3
      },
      "detecting": {
        "binary_threshold": 115,
        "hough_threshold_oblique": 24,
        "hough_threshold_horizontal": 26,
        "hough_threshold_vertical": 2200,
        "maxLineGap_oblique": 45,
        "pattern_tolerance": 10,
        "uniform_k_snap": true
      },
      "sam": {
        "segment_width": 1225
      }
    },
    "proxy_scaled": 0.5326296011021863,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.2862663575448807,
      "sam_fill_rate": 0.535641383983399,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.1980870589398964
    },
    "recentre_residual_max_cm": 21.8,
    "full_pipeline": true,
    "rationale": "Round 1 of 3: fix upstream first. (1) Unfolding: tighten ransac_threshold 1.0 -> 0.85 so the deviating end-slice ellipse centre is treated as an outlier of the degree-2 curve instead of bending it, and re-roll random_seed (3) so the stage-1 fit is re-drawn under the tightened threshold; orientation is canonical/pinned so a re-roll cannot flip handedness. Keep polynomial_degree 2 (10 slice centres, cubic would overfit) and leave slice_spacing_factor alone so ring_count stays 10. (2) Detecting: binary_threshold 127 -> 115 keeps the fainter dotted seam pixels at y~780/2280/2950, hough_threshold_oblique 30 -> 24 and maxLineGap_oblique 30 -> 45 let those dotted seams accumulate into oblique segments, hough_threshold_horizontal 30 -> 26 gives the fallback a slightly better chance on the flattest seams; hough_threshold_vertical set high (2200) to remain in the synthetic 10-vertical regime so ring_count_error stays 0; pattern_tolerance 10 and uniform_k_snap true keep the K-row gate strict so the extra lines cannot move the propagated K row. Expected effect: more label boundaries explained by lines -> correspondence_f1@15 up. (3) SAM: segment_width 1200 -> 1225 mm matches the measured 245.3 px ring pitch so per-ring templates stop drifting across the 10 rings, which should lift sam_fill_rate without changing K_height / angle (left at priors). Denoising and enhancing untouched (r-band and theta gate at T3 priors; the confirmed causal depth thresholds are not in bounds). full=true because unfolding changes.",
    "proposer": "Fable-5.1 (fresh per-case agent)"
  },
  {
    "round": 2,
    "status": "ok",
    "overlay": {
      "enhancing": {
        "curvature_threshold": 0.0008
      },
      "detecting": {
        "binary_threshold": 108,
        "hough_threshold_oblique": 22,
        "hough_threshold_horizontal": 24,
        "hough_threshold_vertical": 2200,
        "maxLineGap_oblique": 55,
        "pattern_tolerance": 10,
        "uniform_k_snap": true
      },
      "sam": {
        "segment_width": 1200
      }
    },
    "proxy_scaled": 0.5296418734580287,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.26860384167358,
      "sam_fill_rate": 0.5537712277135476,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.18966031732842298
    },
    "recentre_residual_max_cm": 20.8,
    "full_pipeline": false,
    "rationale": "Round 2 of 3, stage 1 frozen (full=false, no unfolding keys). (1) Detecting: continue the direction that raised F1 but with a bounded step: binary_threshold 115 -> 108 and hough_threshold_oblique 24 -> 22 so the dotted y~780 / y~2280 seam pixels reach the accumulator, maxLineGap_oblique 45 -> 55 to bridge the gaps between bolt clusters along those seams, hough_threshold_horizontal 26 -> 24 for the flattest seam; hough_threshold_vertical stays 2200 (synthetic 10 verticals, ring_count_error 0), pattern_tolerance 10 and uniform_k_snap true keep the K-row gate strict so extra lines cannot move the propagated K row. (2) Enhancing: curvature_threshold 0.0005 -> 0.0008 to densify the near-flat lining around the many bolt-hole rims, closing small halos -> lower depth_nan_ratio and higher sam_fill_rate; kept well below the upper bound to avoid smoothing the joint seams the detector needs. (3) SAM: segment_width back to the T3 prior 1200 (1225 coincided with the fill-rate drop and templates are re-anchored per ring at each vertical, so the pitch mismatch is not cumulative); K_height and angle stay at priors since the detected K band (~170 px between green and red lines) and the per-ring oblique slope (~5-6 deg) agree with 823.8 mm / 6.12 deg. Denoising untouched (r-band and theta gate at T3 priors; the remaining voids are physical fixtures / floor).",
    "proposer": "Fable-5.1 (fresh per-case agent)"
  },
  {
    "round": 3,
    "status": "ok",
    "overlay": {
      "denoising": {
        "mask_r_high": 3.06
      },
      "enhancing": {
        "curvature_threshold": 0.0005
      },
      "detecting": {
        "binary_threshold": 115,
        "hough_threshold_oblique": 24,
        "hough_threshold_horizontal": 26,
        "hough_threshold_vertical": 2200,
        "maxLineGap_oblique": 45,
        "pattern_tolerance": 10,
        "uniform_k_snap": true
      },
      "sam": {
        "segment_width": 1200
      }
    },
    "proxy_scaled": 0.5033174486439538,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.20162561433459533,
      "sam_fill_rate": 0.5880066065303011,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.18489040930877423
    },
    "recentre_residual_max_cm": 20.8,
    "full_pipeline": false,
    "rationale": "Final round, stage 1 frozen (full=false). (1) Denoising: mask_r_high 3.0 -> 3.06 m to retain the deeper bolt-pocket and joint-groove points that currently become NaN halos; these pixels lie inside the SAM block templates, so recovering them should raise sam_fill_rate and denoise_retained_ratio and lower depth_nan_ratio together (the healthy, non-cosmetic pattern), and the extra depth contrast at groove bottoms feeds the joint-outlier enhancement rather than washing it out. mask_r_low and theta gates untouched. (2) Enhancing: curvature_threshold back to the 0.0005 prior (round-2 evidence: cosmetic). (3) Detecting: consolidate the round-1 settings that produced the best F1 (binary_threshold 115, hough_threshold_oblique 24, maxLineGap_oblique 45, hough_threshold_horizontal 26) instead of the saturated round-2 values that only added left-edge fragments; hough_threshold_vertical 2200 keeps the synthetic 10 verticals (ring_count_error 0); pattern_tolerance 10 and uniform_k_snap true keep the K-row gate strict. (4) SAM: segment_width 1200 (prior), K_height and angle at priors since the detected K band (~170 px) and per-ring oblique slope (~5-6 deg) match 823.8 mm / 6.12 deg. Expected: fill rate back above the anchor with F1 retained near the round-1 level, i.e. the first round where both coherence features move up on the same map.",
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
`/home/boringtao/Projects/Proxy4Tun/data/sc-general/stage3/packets-fable-fresh/3-4/round3_proposal.json`

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
