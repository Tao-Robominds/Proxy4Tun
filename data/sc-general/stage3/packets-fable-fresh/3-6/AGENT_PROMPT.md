# Fable 5.1 reflection — subset 3-6 (propose round 3)

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

- subset: `3-6`
- family: `t3`
- lining_mode: `continuous`
- stage1_unlocked: `False` (residual gate 10 cm)
- arm: `fable_fresh` / proposer: `Fable-5.1 (fresh per-case agent)`
- model: `claude-fable-5-1-thinking-high`

### Anchor (GT-blind)
```json
{
  "proxy_raw": 0.681391,
  "proxy_scaled": 0.681391,
  "band": "refine",
  "features": {
    "correspondence_f1@15": 0.467009,
    "sam_fill_rate": 0.649052,
    "ring_count_error": 0.0,
    "depth_nan_ratio": 0.105203
  },
  "recentre_residual_max_cm": 3.2,
  "orient_axis_corr": -0.9998273166785221,
  "ring_count": 10,
  "ring_count_error": 0.0,
  "labelmap_source": "results.pkl",
  "run_dir": "/home/boringtao/Projects/Proxy4Tun/data/bo/unified/3-6-family-proxy/runs/3-6-anchor"
}
```

### Intrinsics (GT-blind)
```json
{
  "orient_axis_corr": -0.9998273166785221,
  "orient_invariant_ok": 1.0,
  "recentre_residual_max_cm": 3.2,
  "denoise_retained_ratio": 0.6947482510592177,
  "depth_nan_ratio": 0.1052027439356335,
  "depth_outlier_ratio": 0.0011429524394758353,
  "det_real_detection_ratio": 0.0,
  "det_fallback_ratio": 1.0,
  "det_n_points": 10.0,
  "sam_fill_rate": 0.6490524518014911,
  "sam_ring_completeness": 1.0,
  "sam_segment_size_cv": 0.4615271364828772,
  "sam_ontology_divergence": 0.20053605374706296
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
        "maxLineGap_oblique": 42,
        "pattern_tolerance": 12,
        "uniform_k_snap": true
      },
      "sam": {
        "segment_width": 1200,
        "K_height": 823.8,
        "angle": 6.12
      }
    },
    "proxy_scaled": 0.6706771432467075,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.44739977477422294,
      "sam_fill_rate": 0.6490524518014911,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.1052027439356335
    },
    "recentre_residual_max_cm": 3.2,
    "full_pipeline": false,
    "rationale": "Lower binary_threshold (127 -> 110) and oblique/horizontal Hough thresholds (30 -> 24) with a larger oblique maxLineGap (30 -> 42) to recover continuous joint lines across the bolt-pocket rows at y~800 and y~2350 and to lengthen the K-row oblique segments, which should raise recall of label boundaries within 15 px; pattern_tolerance 12 px keeps the K/AB distance check permissive enough for the added lines without accepting spurious intersections. On the SAM side pin K_height and taper angle to the T3 priors (823.8 mm, 6.12 deg) so the K block template height matches the detected joint pair (~170 px = 850 mm) and the lower K boundary moves up to the detected line; segment_width stays at the 1200 mm prior. Unfolding is untouched (stage1 locked); denoising is left at the anchor band because retention and NaN are healthy.",
    "proposer": "Fable-5.1 (fresh per-case agent)"
  },
  {
    "round": 2,
    "status": "ok",
    "overlay": {
      "detecting": {
        "binary_threshold": 135,
        "hough_threshold_oblique": 38,
        "hough_threshold_horizontal": 34,
        "maxLineGap_oblique": 36,
        "pattern_tolerance": 10,
        "uniform_k_snap": true
      },
      "sam": {
        "segment_width": 1200,
        "K_height": 760.0,
        "angle": 6.12
      }
    },
    "proxy_scaled": 0.7442190838660616,
    "band": "accept",
    "features": {
      "correspondence_f1@15": 0.5808465137458513,
      "sam_fill_rate": 0.6513745196571091,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.1052027439356335
    },
    "recentre_residual_max_cm": 3.2,
    "full_pipeline": false,
    "rationale": "Reverse the detection direction relative to the anchor instead of merely reverting: binary_threshold 127 -> 135 and hough_threshold_oblique/horizontal 30 -> 38/34 suppress the weak pocket-edge fragments that were unexplained in the overlay, while maxLineGap_oblique 36 (slightly above the 30 anchor, below round-1's 42) keeps the strong K-row joints bridged across the bolt pockets as long segments rather than splitting them; the two K-row families are the highest-contrast lines in the map and survive the higher vote count, so the 10 real K-row anchors for the snap gate are retained. pattern_tolerance 10 px keeps the K/AB distance check at single-digit-to-10 px scale (healthy per \u00a75) so only pattern-consistent intersections feed the gate. On SAM, keep segment_width 1200 and angle 6.12 (vertical spacing ~240 px = 1200 mm matches, taper only affects x-boundaries) but reduce K_height 823.8 -> 760 mm (152 px): the template becomes ~13 px shorter on each side than the detected pair, so the B2 template starts inside the pocket band and its prompts compete for it, pulling the K/B2 label boundary up from ~1675 toward the detected ~1630 line and shifting the B2/A3 boundary from ~2350 toward the detected ~2300 row. Both moves target correspondence_f1@15 (the only feature that moved in round 1) without touching the healthy evidence features; unfolding is untouched (stage 1 locked) and denoising/enhancing stay at anchor because retention, NaN and joint contrast are all healthy.",
    "proposer": "Fable-5.1 (fresh per-case agent)"
  },
  {
    "round": 3,
    "status": "ok",
    "overlay": {
      "detecting": {
        "binary_threshold": 135,
        "hough_threshold_oblique": 42,
        "hough_threshold_horizontal": 34,
        "maxLineGap_oblique": 40,
        "pattern_tolerance": 10,
        "uniform_k_snap": true
      },
      "sam": {
        "segment_width": 1200,
        "K_height": 760.0,
        "angle": 6.12
      }
    },
    "proxy_scaled": 0.743353156173783,
    "band": "accept",
    "features": {
      "correspondence_f1@15": 0.5792600333235791,
      "sam_fill_rate": 0.6513778040529444,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.1052027439356335
    },
    "recentre_residual_max_cm": 3.2,
    "full_pipeline": false,
    "rationale": "Hold SAM exactly at the round-2 values (segment_width 1200, K_height 760.0, angle 6.12) because that configuration executed cleanly and produced the best proxy so far, whereas K_height 720 caused a stage-5 SAM failure; no stage-5 change is made this round. Hold binary_threshold 135, hough_threshold_horizontal 34 and pattern_tolerance 10 (K/AB gate at the healthy ~10 px scale, per \u00a75) and keep uniform_k_snap true (continuous-family regime). Make one small, coherent stage-4 precision step: raise hough_threshold_oblique 38 -> 42 (~10%, well inside [20, 60]) so the residual short oblique stubs (~40-50 px, low vote count) drop out, while the true K-row joints, which are 100-250 px per ring and collinear across same-orientation rings, keep far more than 42 accumulator votes and survive; and raise maxLineGap_oblique 36 -> 40 (inside [10, 60], still below round-1's 42 that was paired with a too-low threshold) so the lower K-row segments that are currently split by the ~35-40 px bolt pockets are linked back into single long segments instead of 2-3 fragments per ring. Together these should reduce the count of short unexplained line pieces (precision side of correspondence_f1@15) without removing the upper K-row family that the label boundary already explains, and without disturbing the 10 K-row snap anchors (the snap row is defined by the strong upper/lower joint pair, not the stubs). Expected outcome: correspondence_f1@15 flat-to-up, sam_fill_rate, depth_nan_ratio and ring_count_error unchanged (SAM inputs are identical apart from the prompt-line set). If F1 drops, round 2 remains the selected candidate; the step is small enough that a regression should be minor. Unfolding is omitted (stage 1 locked); denoising and enhancing stay at anchor because retention, NaN and joint contrast are healthy and none of the evidence features moved in rounds 1-2.",
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
`/home/boringtao/Projects/Proxy4Tun/data/sc-general/stage3/packets-fable-fresh/3-6/round3_proposal.json`

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
