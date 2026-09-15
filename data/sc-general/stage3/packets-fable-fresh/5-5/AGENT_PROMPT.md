# Fable 5.1 reflection — subset 5-5 (propose round 3)

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

- subset: `5-5`
- family: `t4&5`
- lining_mode: `complex`
- stage1_unlocked: `False` (residual gate 10 cm)
- arm: `fable_fresh` / proposer: `Fable-5.1 (fresh per-case agent)`
- model: `claude-fable-5-1-thinking-high`

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
      "enhancing": {
        "curvature_threshold": 0.0004
      },
      "detecting": {
        "binary_threshold": 110,
        "hough_threshold_oblique": 35,
        "maxLineGap_oblique": 70
      }
    },
    "proxy_scaled": 0.6093917466833614,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.3159042898336717,
      "sam_fill_rate": 0.7561778560970978,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.1943432714072759
    },
    "recentre_residual_max_cm": 1.9,
    "full_pipeline": false,
    "rationale": "Lower detecting.binary_threshold 127 -> 110 so more faint joint pixels survive binarisation before dilation (the only in-bounds analogue of r_lower_depth_threshold). Relax the oblique HoughLinesP path: hough_threshold_oblique 50 -> 35 (the value that recovered 5-1's detection in past campaigns) and maxLineGap_oblique 50 -> 70 to bridge the dotted joint traces into full K-taper lines, so positive/negative-slope intersections replace horizontal midpoints as prompt centres. Horizontal Hough is left at prior so it still acts as fallback rather than competing. Nudge enhancing.curvature_threshold 0.0005 -> 0.0004 so slightly fewer joint-edge points are treated as flat surface during densification, preserving joint discontinuities in the projected map; the change is small enough to keep depth_nan_ratio in the family-normal band. Vertical Hough, denoising band (tunnel priors, load-bearing for transfer) and SAM geometry (segment_width 1800 mm matches the measured 361 px pitch; K_height/angle at T5 priors) are intentionally unchanged so the proxy delta is attributable to detection. Expected signal: det_real_detection_ratio and oblique yield rise, prompt y-positions follow the K/AB pattern, correspondence_f1@15 increases with sam_fill_rate held near 0.76; a proxy rise driven only by evidence features with fill rate dropping would be treated as suspect.",
    "proposer": "Fable-5.1 (fresh per-case agent)"
  },
  {
    "round": 2,
    "status": "ok",
    "overlay": {
      "detecting": {
        "pattern_tolerance": 15
      }
    },
    "proxy_scaled": 0.609798035918693,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.3162260435797977,
      "sam_fill_rate": 0.7561778560970978,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.19323166894404062
    },
    "recentre_residual_max_cm": 1.9,
    "full_pipeline": false,
    "rationale": "Set detecting.pattern_tolerance = 15 px. Measured true K pairs deviate 7-10 px from the 245.4 px K prior (four clean rings: 255, 253, 254, 252 px), so 15 keeps every genuine pairing with a 5+ px margin, while the spurious pairings in rings 1620 (208 px) and 2340 (188/202 px) deviate by 37-57 px and are rejected; those rings should then fall back to the true 9-deg edges (centres ~2139 and ~1399 instead of 2118 and 1421), moving all 12 of their block boundaries inside the 15 px tolerance. Everything else stays at the anchor: oblique Hough and binarisation are left at prior because round 1 proved them non-identifiable here and tightening them would remove the genuine 136-173 px single edges of rings 540/3060 before the ~190 px spurious segments; the round-1 curvature nudge is dropped (it only raised NaN); horizontal Hough is untouched so the SC joint-line set is the same as the anchor and any proxy change is attributable to the prompt fix; denoising band and SAM geometry stay at tunnel priors (segment_width 1800 mm = measured 360 px pitch; K/AB heights fit the good rings). full=false (stage1_unlocked is false). Expected signal: prompt y for rings 1620/2340 shifts by about +20/-22 px, det_real_detection_ratio stays 0.8, ring_count 10, sam_fill_rate ~0.756, correspondence_f1@15 rises from 0.316 toward ~0.40-0.45 (up to 12 more supported boundaries of 70 and ~10 more explained joint lines). If the prompt set is again unchanged, the tolerance is not applied to K-pair validation and round 3 should switch to the horizontal joint path / assume-ring coverage rather than the oblique path.",
    "proposer": "Fable-5.1 (fresh per-case agent)"
  },
  {
    "round": 3,
    "status": "ok",
    "overlay": {
      "detecting": {
        "hough_threshold_horizontal": 40,
        "maxLineGap_horizontal": 20
      },
      "sam": {
        "K_height": 1265.0
      }
    },
    "proxy_scaled": 0.6453365765382837,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.3812699030530834,
      "sam_fill_rate": 0.7561778560970978,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.19323166894404062
    },
    "recentre_residual_max_cm": 1.9,
    "full_pipeline": false,
    "rationale": "Switch to the horizontal joint path as planned in round 2. detecting.hough_threshold_horizontal 50 -> 40 and detecting.maxLineGap_horizontal 10 -> 20: the joints in the outlier map are dotted traces with gaps of 10-20 px between bolt-pocket-free segments, so doubling the gap lets the existing 105 px minLineLength be met by traces that currently break into sub-threshold pieces, and a moderate threshold drop (40, not 25-35) adds votes for faint joints without letting the rows of bolt-pocket marks (isolated 10-20 px blobs on ~250 px spacing) accumulate into spurious horizontals. Expected: more blue lines at true circumferential joints in rings 180/540/900 and the second half-map of every ring, raising the supported-boundary count in the five already-aligned rings and the explained-line count, so correspondence_f1@15 rises from 0.316 while sam_fill_rate stays ~0.756 and ring_count stays 10 (verticals untouched at prior). Because the horizontal set was never a prompt source here (all 8 real prompts come from oblique pairs), the prompt centres should be unchanged and any proxy delta is attributable to the joint-line set plus the template edit. sam.K_height 1226.97 -> 1265.0 mm (253 px) aligns the K template with the measured 252-255 px K pairs; this moves the K edges and the adjoining B1/B2 outer edges by ~4 px each, small enough not to disturb fill rate but enough to bring boundaries sitting at 12-18 px off a joint inside the 15 px tolerance. segment_width (1800 mm = measured 360 px pitch) and angle (9.8 deg; measured 9.0-9.2 deg differs by <5 px across a ring) stay at priors; denoising band stays at tunnel priors (load-bearing for transfer). full=false; unfolding omitted (stage1_unlocked is false). Suspect-signal check: if the proxy rises while sam_fill_rate drops or the joint-line count explodes with precision falling (mostly orange lines inside blocks), the horizontal relaxation is over-shooting and the anchor should be preferred at selection.",
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
`/home/boringtao/Projects/Proxy4Tun/data/sc-general/stage3/packets-fable-fresh/5-5/round3_proposal.json`

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
