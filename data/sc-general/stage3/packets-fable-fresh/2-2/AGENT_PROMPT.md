# Fable 5.1 reflection — subset 2-2 (propose round 3)

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

- subset: `2-2`
- family: `t1&2`
- lining_mode: `staggered`
- stage1_unlocked: `False` (residual gate 10 cm)
- arm: `fable_fresh` / proposer: `Fable-5.1 (fresh per-case agent)`
- model: `claude-fable-5-1-thinking-high`

### Anchor (GT-blind)
```json
{
  "proxy_raw": 0.699142,
  "proxy_scaled": 0.699142,
  "band": "refine",
  "features": {
    "correspondence_f1@15": 0.455,
    "sam_fill_rate": 0.743164,
    "ring_count_error": 0.0,
    "depth_nan_ratio": 0.111005
  },
  "recentre_residual_max_cm": 1.5,
  "orient_axis_corr": -0.9998899225490308,
  "ring_count": 10,
  "ring_count_error": 0.0,
  "labelmap_source": "results.pkl",
  "run_dir": "/home/boringtao/Projects/Proxy4Tun/data/bo/unified/2-2-family-proxy/runs/2-2-anchor"
}
```

### Intrinsics (GT-blind)
```json
{
  "orient_axis_corr": -0.9998899225490308,
  "orient_invariant_ok": 1.0,
  "recentre_residual_max_cm": 1.5,
  "denoise_retained_ratio": 0.7711390480524585,
  "depth_nan_ratio": 0.11100505152955387,
  "depth_outlier_ratio": 0.003969557138198945,
  "det_real_detection_ratio": 0.9,
  "det_fallback_ratio": 0.1,
  "det_n_points": 10.0,
  "sam_fill_rate": 0.7431639534162133,
  "sam_ring_completeness": 0.8888888888888888,
  "sam_segment_size_cv": 1.1492356762263811,
  "sam_ontology_divergence": 0.16496563728120134
}
```

### Prior rounds (this arm only)
```json
[
  {
    "round": 1,
    "status": "ok",
    "overlay": {
      "enhancing": {
        "curvature_threshold": 0.0004,
        "inter_radius": 0.07
      },
      "detecting": {
        "binary_threshold": 118,
        "hough_threshold_oblique": 46,
        "hough_threshold_horizontal": 60,
        "maxLineGap_oblique": 28
      }
    },
    "proxy_scaled": 0.7424791975333035,
    "band": "accept",
    "features": {
      "correspondence_f1@15": 0.5346041869790231,
      "sam_fill_rate": 0.7429979521337112,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.1115458924281693
    },
    "recentre_residual_max_cm": 1.5,
    "full_pipeline": false,
    "rationale": "Keep stages 1-3 frozen (no unfolding since stage1_unlocked is false; no denoising changes because retention and NaN are healthy and radial band should stay at tunnel priors). In enhancing, raise inter_radius 0.06 -> 0.07 so more interpolated joint points populate the outlier map (denser, more continuous oblique joint traces), and lower curvature_threshold 0.0005 -> 0.0004 so fewer discontinuity points are absorbed into the smooth-surface upsampling, preserving joint edges. In detecting, lower binary_threshold 127 -> 118 and hough_threshold_oblique 50 -> 46 to lift oblique line yield in the faint columns (x~120 should get a real detection instead of an assumed centre), and cut maxLineGap_oblique 40 -> 28 so oblique segments are not bridged across the ~240 px column pitch, which is the mechanism behind the mis-paired K centre at x~1325. Raise hough_threshold_horizontal 50 -> 60 so the spurious horizontal fallback lines at the top and bottom margins do not seed false intersections once oblique thresholds are relaxed. Expected GT-free signals: det_fallback_ratio 0.1 -> 0.0, det_n_points stays 10 with all K midpoints on the two staggered rows (~1205 / ~1640), correspondence_f1@15 rising above 0.455 and sam_fill_rate rising as the two shifted K/A stacks align with the joint lines; proxy should move from 0.699 into the accept band. If line yield instead becomes spurious (extra intersections), back off binary_threshold toward 127 in round 2 while keeping the reduced maxLineGap.",
    "proposer": "Fable-5.1 (fresh per-case agent)"
  },
  {
    "round": 2,
    "status": "ok",
    "overlay": {
      "enhancing": {
        "curvature_threshold": 0.0004,
        "inter_radius": 0.08
      },
      "detecting": {
        "binary_threshold": 108,
        "hough_threshold_oblique": 41,
        "hough_threshold_horizontal": 70,
        "maxLineGap_oblique": 28
      }
    },
    "proxy_scaled": 0.753007390235513,
    "band": "accept",
    "features": {
      "correspondence_f1@15": 0.5537639783713123,
      "sam_fill_rate": 0.7432001530728337,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.11152235233532252
    },
    "recentre_residual_max_cm": 1.5,
    "full_pipeline": false,
    "rationale": "Keep everything that worked in round 1 (maxLineGap_oblique 28 to stay within one column pitch, curvature_threshold 0.0004, unfolding and denoising frozen) and push joint evidence and oblique sensitivity one more step so the sparse left column produces a real intersection: enhancing.inter_radius 0.07 -> 0.08 (bound max; more interpolated joint points along the faint edge-column joints), detecting.binary_threshold 118 -> 108 (let weaker outlier-map pixels survive binarisation before dilation), detecting.hough_threshold_oblique 46 -> 41 (fewer votes needed for a 100 px oblique segment). To offset the extra permissiveness, raise hough_threshold_horizontal 60 -> 70 so the bottom-margin horizontal fallback lines do not multiply. Expected GT-free signals: det_fallback_ratio 0.1 -> 0.0 with det_n_points 10 and the x~120 midpoint landing near y~1204, correspondence_f1@15 rising above 0.535, sam_ontology_divergence falling back toward the anchor's 0.165 as ring 0's K/A stack aligns, fill rate roughly flat. If instead extra oblique intersections appear on other columns (det_y_std drifting away from ~215 or det_n_points > 10), round 3 should restore binary_threshold to 118 and keep only the inter_radius change.",
    "proposer": "Fable-5.1 (fresh per-case agent)"
  },
  {
    "round": 3,
    "status": "ok",
    "overlay": {
      "enhancing": {
        "curvature_threshold": 0.0003,
        "inter_radius": 0.08
      },
      "detecting": {
        "binary_threshold": 100,
        "hough_threshold_oblique": 40,
        "hough_threshold_horizontal": 80,
        "maxLineGap_oblique": 36
      }
    },
    "proxy_scaled": 0.7083826024134123,
    "band": "accept",
    "features": {
      "correspondence_f1@15": 0.4716592692342488,
      "sam_fill_rate": 0.74461814533645,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.11224105171322471
    },
    "recentre_residual_max_cm": 1.5,
    "full_pipeline": false,
    "rationale": "Final-round push aimed only at the edge column, keeping every structural choice that has held for two rounds (unfolding and denoising frozen, inter_radius 0.08, one oblique pair per column). Enhancing: curvature_threshold 0.0004 -> 0.0003 (bound minimum) so that even fewer joint-adjacent high-curvature points are absorbed into smooth-surface upsampling, preserving the depth step that the outlier enhancement keys on; this is the last in-bounds analogue of r_lower_depth_threshold and its previous step cost nothing in NaN (0.1110 -> 0.1115). Detecting: binary_threshold 108 -> 100 (bound minimum) and hough_threshold_oblique 41 -> 40 (bound minimum) to let the weakest edge-column pixels survive binarisation and vote; maxLineGap_oblique 28 -> 36, a deliberate but bounded increase (15% of the 240 px column pitch, still below the anchor's 40 that produced a bridged line in the dense scanner column) so sparse collinear speckle in x 60-240 can chain into a 100 px segment while a segment still cannot span two columns. To offset the lower binary threshold, hough_threshold_horizontal 70 -> 80 so horizontal fallback lines at the cable-bracket rows (y~450/880/1960/2400) and margins do not multiply; horizontals are fallback-only and none currently contribute to prompts. Expected GT-free signals: det_fallback_ratio 0.1 -> 0.0 with det_n_points 10 and the x~120 midpoint landing near y~1204 (even row), correspondence_f1@15 rising above 0.554, sam_ontology_divergence falling as ring 0's K/A stack aligns, sam_fill_rate flat (~0.743), depth_nan_ratio ~0.112, det_y_std ~215 px preserved. Failure signature to watch: det_n_points > 10 or an off-row midpoint in the dense x~1325 column would indicate the wider gap re-enabled bridging (f_spurious_lines / f_pattern_mismatch); in that case round 2 (maxLineGap 28) remains the better configuration and should be selected.",
    "proposer": "Fable-5.1 (fresh per-case agent)"
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
`/home/boringtao/Projects/Proxy4Tun/data/sc-general/stage3/packets-fable-fresh/2-2/round3_proposal.json`

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
