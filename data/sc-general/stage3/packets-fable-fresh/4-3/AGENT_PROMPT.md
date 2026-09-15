# Fable 5.1 reflection — subset 4-3 (propose round 3)

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

- subset: `4-3`
- family: `t4&5`
- lining_mode: `complex`
- stage1_unlocked: `True` (residual gate 10 cm)
- arm: `fable_fresh` / proposer: `Fable-5.1 (fresh per-case agent)`
- model: `claude-fable-5-1-thinking-high`

### Anchor (GT-blind)
```json
{
  "proxy_raw": 0.520218,
  "proxy_scaled": 0.520218,
  "band": "refine",
  "features": {
    "correspondence_f1@15": 0.191402,
    "sam_fill_rate": 0.71707,
    "ring_count_error": 0.0,
    "depth_nan_ratio": 0.245204
  },
  "recentre_residual_max_cm": 23.2,
  "orient_axis_corr": 0.986044276927073,
  "ring_count": 10,
  "ring_count_error": 0.0,
  "labelmap_source": "only_label.csv",
  "run_dir": "/home/boringtao/Projects/Proxy4Tun/data/bo/unified/4-3-family-proxy/runs/4-3-anchor"
}
```

### Intrinsics (GT-blind)
```json
{
  "orient_axis_corr": 0.986044276927073,
  "orient_invariant_ok": 1.0,
  "recentre_residual_max_cm": 23.2,
  "denoise_retained_ratio": 0.7254553472672002,
  "depth_nan_ratio": 0.2452039067112422,
  "depth_outlier_ratio": 0.0009887966197817434,
  "det_real_detection_ratio": 0.6,
  "det_fallback_ratio": 0.4,
  "det_n_points": 10.0,
  "sam_fill_rate": 0.7170697542593042,
  "sam_ring_completeness": 1.0,
  "sam_segment_size_cv": 1.0756001699898754,
  "sam_ontology_divergence": 0.10079588005915159
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
        "polynomial_degree": 3,
        "ransac_threshold": 0.9,
        "slice_spacing_factor": 1.8,
        "random_seed": 0
      },
      "denoising": {
        "mask_r_low": 3.65,
        "mask_r_high": 3.9
      },
      "enhancing": {
        "curvature_threshold": 0.0005
      },
      "detecting": {
        "binary_threshold": 127,
        "hough_threshold_oblique": 40,
        "hough_threshold_horizontal": 40,
        "hough_threshold_vertical": 5000,
        "maxLineGap_oblique": 60,
        "maxLineGap_horizontal": 10,
        "pattern_tolerance": 15
      },
      "sam": {
        "segment_width": 1800,
        "K_height": 1226.97,
        "angle": 9.8
      }
    },
    "proxy_scaled": 0.4513916465828539,
    "band": "reject",
    "features": {
      "correspondence_f1@15": 0.09155506750011519,
      "sam_fill_rate": 0.7113163298820973,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.3065097116670472
    },
    "recentre_residual_max_cm": 35.6,
    "full_pipeline": true,
    "rationale": "Round 1 is spent on the upstream defect only, keeping stages 2-5 at tunnel priors so the proxy delta is attributable. Unfolding: raise polynomial_degree 2 -> 3 so the centre curve can follow a curved/settling T4 axis, and tighten ransac_threshold to 0.9 (lower end of the band) so contaminated ellipse centres near the tube/void slices are excluded from the fit; slice_spacing_factor 1.8 (mid-band) keeps ring_count at 10; random_seed 0 pins reproducibility (not used as a tuning knob). Denoising kept at the T4 prior band 3.65/3.90 (no band widening, per section 3). Enhancing curvature_threshold at the 0.0005 default. Detection: keep hough_threshold_vertical at 5000 to force synthetic ring-centre verticals (10 lines = 10 rings already correct; must not regress to 11), and only mildly relax the oblique/horizontal Hough (threshold 40, maxLineGap_oblique 60, pattern_tolerance 15) because a cleaner recentred map should yield sharper joints and the 40% 'assume' prompts should drop. SAM kept at T4 priors (segment_width 1800, K_height 1226.97, angle 9.8). Success criteria for this round: recentre_residual_max_cm <= 10, depth_nan_ratio in 0.19-0.22, det_real_detection_ratio >= 0.7, ring count still 10, proxy rising above 0.55.",
    "proposer": "Fable-5.1 (fresh per-case agent)"
  },
  {
    "round": 2,
    "status": "ok",
    "overlay": {
      "denoising": {
        "mask_r_low": 3.65,
        "mask_r_high": 3.9
      },
      "enhancing": {
        "curvature_threshold": 0.0005
      },
      "detecting": {
        "binary_threshold": 127,
        "hough_threshold_oblique": 30,
        "hough_threshold_horizontal": 30,
        "hough_threshold_vertical": 5000,
        "maxLineGap_oblique": 75,
        "maxLineGap_horizontal": 20,
        "pattern_tolerance": 18
      },
      "sam": {
        "segment_width": 1975,
        "K_height": 1226.97,
        "angle": 9.8
      }
    },
    "proxy_scaled": 0.5407740836902515,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.22902550578357173,
      "sam_fill_rate": 0.7170697542593042,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.2452039067112422
    },
    "recentre_residual_max_cm": 23.2,
    "full_pipeline": false,
    "rationale": "Round 2 abandons unfolding (no 'unfolding' key, full=false) so stages 2-6 replay on the frozen anchor checkpoint whose residual (23.2 cm) beats the round-1 re-roll (35.6 cm); this restores the anchor's depth_nan_ratio 0.245 and isolates the delta to stages 4-5. Denoising stays at the T4 prior band 3.65/3.90 and enhancing at curvature_threshold 0.0005 (no band widening, no unverified curvature effect). Detection: keep hough_threshold_vertical 5000 (synthetic ring-centre verticals, 10 lines = 10 rings, must not regress) and binary_threshold 127; relax the oblique Hough to threshold 30 with maxLineGap_oblique 75 so the long dotted block joints (visible in the outlier map but broken into <50 px runs) accumulate into lines within the [5,10] deg angle filter; relax horizontal to threshold 30 / maxLineGap_horizontal 20 so fallback prompts come from real circumferential joints instead of 'assume'; widen pattern_tolerance 15 -> 18 px because the 23 cm off-centre distortion stretches K/AB spacings by several px across the map (K_height_pixel 245, AB_height_pixel 745). SAM: set segment_width 1975 mm (= 395 px, the actual synthetic ring-cell width on this 3956 px map) so adjacent ring templates meet instead of leaving ~36 px unclaimed strips per ring; keep K_height 1226.97 and angle 9.8 at T4 priors because there is no GT-blind evidence of a block-height or taper mismatch. Expected GT-blind effects: correspondence_f1@15 back above the anchor's 0.19 (more supported boundaries via more detected joint lines and real prompts), det_real_detection_ratio >= 0.7, sam_fill_rate > 0.72, depth_nan_ratio back to 0.245, ring_count 10, proxy back into the refine band and above the anchor 0.520. Risk: extra oblique lines could add spurious intersections; the distance-pattern check with tolerance 18 px and the fixed synthetic verticals bound that risk.",
    "proposer": "Fable-5.1 (fresh per-case agent)"
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
        "curvature_threshold": 0.0005
      },
      "detecting": {
        "binary_threshold": 127,
        "hough_threshold_oblique": 25,
        "hough_threshold_horizontal": 25,
        "hough_threshold_vertical": 5000,
        "maxLineGap_oblique": 80,
        "maxLineGap_horizontal": 25,
        "pattern_tolerance": 20
      },
      "sam": {
        "segment_width": 1815,
        "K_height": 1226.97,
        "angle": 9.8
      }
    },
    "proxy_scaled": 0.5282988258033436,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.2061928596832498,
      "sam_fill_rate": 0.7170697542593042,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.2452039067112422
    },
    "recentre_residual_max_cm": 23.2,
    "full_pipeline": false,
    "rationale": "Round 3 is the last round, so it continues the one direction that measurably raised the proxy and undoes the one premise that was wrong, keeping every other knob fixed so the delta stays attributable. Stage 1: omitted (full=false), replay on the frozen anchor checkpoint (residual 23.2 cm, depth_nan_ratio 0.245 preserved). Denoising: T4 prior 3.65/3.90 unchanged (no band widening; the white bands are structural). Enhancing: curvature_threshold 0.0005 unchanged (surface up-sampling only; it does not sharpen joints). Detection: hough_threshold_vertical 5000 and binary_threshold 127 unchanged (ring count lock; binarisation not shown to be live on the outlier map). Move the oblique Hough to the low end of the band, threshold 30 -> 25 with maxLineGap_oblique 75 -> 80, so the long dotted block joints visible in the outlier map (currently broken into sub-threshold runs) accumulate into lines within the [5,10] deg filter \u2014 round 2 showed this direction converts 'assume' prompts into real ones and raised correspondence by +0.04. Move the horizontal Hough to threshold 25 with maxLineGap_horizontal 20 -> 25 so the near-horizontal joints around y ~2950-3000 and ~3450 (already partially caught as blue segments) are caught along their full length and provide 'midpoint' prompts instead of 'assume'. Raise pattern_tolerance 18 -> 20 (band top) because the off-centre draw distorts the theta scale by up to ~46 px at the worst theta, so genuine K/AB intersections near the map ends fail the distance-pattern check at 18 px; the fixed synthetic verticals plus merge_close_points bound the spurious-intersection risk. SAM: segment_width 1975 -> 1815 mm (= 363 px, the actual ring-cell width on the 3631 px frozen anchor map; T4 prior is 1800) so templates tile the cells exactly instead of overlapping neighbours by ~32 px; K_height 1226.97 and angle 9.8 stay at T4 priors (the K/AB pixel priors reproduce the 4711 px circumference; no GT-blind evidence of a block-height or taper mismatch). Expected GT-blind effects: more oblique/horizontal lines that are explained by boundaries (cyan) in the SC overlay, det_real_detection_ratio >= 0.7 (<= 3 'assume' prompts), correspondence_f1@15 above 0.229, ring_count 10, depth_nan_ratio 0.245 and sam_fill_rate ~0.717 unchanged (the proxy gain must come from correspondence), proxy above the round-2 0.541 and staying in the refine band. Risk: at the band floor the oblique Hough may add spurious lines from bracket/void edges (f_spurious_lines); ring count is locked by the synthetic verticals and prompts are still gated by the K/AB pattern, so the downside is bounded to a few misplaced prompts; if correspondence falls below 0.229 the round-2 overlay remains the selection candidate.",
    "proposer": "Fable-5.1 (fresh per-case agent)"
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
`/home/boringtao/Projects/Proxy4Tun/data/sc-general/stage3/packets-fable-fresh/4-3/round3_proposal.json`

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
