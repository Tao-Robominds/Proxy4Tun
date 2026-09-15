# Fable 5.1 reflection — subset 4-2 (propose round 3)

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

- subset: `4-2`
- family: `t4&5`
- lining_mode: `complex`
- stage1_unlocked: `False` (residual gate 10 cm)
- arm: `fable_fresh` / proposer: `Fable-5.1 (fresh per-case agent)`
- model: `claude-fable-5-1-thinking-high`

### Anchor (GT-blind)
```json
{
  "proxy_raw": 0.543511,
  "proxy_scaled": 0.543511,
  "band": "refine",
  "features": {
    "correspondence_f1@15": 0.213123,
    "sam_fill_rate": 0.731801,
    "ring_count_error": 0.0,
    "depth_nan_ratio": 0.209361
  },
  "recentre_residual_max_cm": 2.0,
  "orient_axis_corr": 0.9669973618747811,
  "ring_count": 10,
  "ring_count_error": 0.0,
  "labelmap_source": "only_label.csv",
  "run_dir": "/home/boringtao/Projects/Proxy4Tun/data/bo/unified/4-2-family-proxy/runs/4-2-anchor"
}
```

### Intrinsics (GT-blind)
```json
{
  "orient_axis_corr": 0.9669973618747811,
  "orient_invariant_ok": 1.0,
  "recentre_residual_max_cm": 2.0,
  "denoise_retained_ratio": 0.7418340341807801,
  "depth_nan_ratio": 0.2093606933058968,
  "depth_outlier_ratio": 0.0011176488861046538,
  "det_real_detection_ratio": 0.6,
  "det_fallback_ratio": 0.4,
  "det_n_points": 10.0,
  "sam_fill_rate": 0.7318014994277484,
  "sam_ring_completeness": 1.0,
  "sam_segment_size_cv": 1.091516694082548,
  "sam_ontology_divergence": 0.11759782036661469
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
        "hough_threshold_oblique": 35,
        "hough_threshold_horizontal": 40,
        "maxLineGap_oblique": 65,
        "maxLineGap_horizontal": 15,
        "pattern_tolerance": 12
      }
    },
    "proxy_scaled": 0.5773851068518312,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.27511968809368287,
      "sam_fill_rate": 0.7318014994277484,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.2093606933058968
    },
    "recentre_residual_max_cm": 2.0,
    "full_pipeline": false,
    "rationale": "Relax the oblique/horizontal Hough gates so the faint, dotted circumferential joints on this complex-family scan accumulate enough votes to be kept as real lines: oblique threshold 50->35 and maxLineGap_oblique 50->65 bridge the gaps between bolt-hole clusters along a joint; horizontal threshold 50->40 with maxLineGap_horizontal 10->15 makes the fallback path produce longer, more consistent segments where oblique still fails. Lower binary_threshold 127->110 so the weaker joint pixels in the outlier map survive binarisation and dilation before Hough. pattern_tolerance 12 px (moderate) lets the K/AB distance-pattern accept slightly irregular intersections instead of dropping them to 'assume'. Vertical accumulator kept at prior (ring count already exact). Denoising, enhancing and SAM geometry left untouched this round so the effect on det_real_detection_ratio and correspondence_f1@15 is attributable to detection alone; SAM template geometry (segment_width/K_height/angle) will be revisited in a later round only if prompts become real and per-block size CV stays high.",
    "proposer": "Fable-5.1 (fresh per-case agent)"
  },
  {
    "round": 2,
    "status": "ok",
    "overlay": {
      "detecting": {
        "binary_threshold": 100,
        "hough_threshold_oblique": 30,
        "hough_threshold_horizontal": 40,
        "maxLineGap_oblique": 75,
        "maxLineGap_horizontal": 15,
        "pattern_tolerance": 15
      }
    },
    "proxy_scaled": 0.5739732100439813,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.26887511719577695,
      "sam_fill_rate": 0.7318014994277484,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.2093606933058968
    },
    "recentre_residual_max_cm": 2.0,
    "full_pipeline": false,
    "rationale": "Take a second, moderate step along the direction that paid off in round 1 and add the missing pattern-tolerance lever. binary_threshold 110 -> 100 (bound) so the faintest joint outlier pixels survive binarisation and dilation, the only in-bounds substitute for lowering the stage-3 depth thresholds. hough_threshold_oblique 35 -> 30 and maxLineGap_oblique 65 -> 75 so dotted joint / bolt-row evidence within [5,10] deg accumulates into full-width segments on the four rings that still fall back (minLineLength is fixed, which caps spurious short lines). pattern_tolerance 12 -> 15 so K-bracketing intersections that miss the 245 px prior by a few tens of pixels are accepted as real centres instead of dropped to 'assume'; kept below the 20 px bound to limit false matches while more lines are present. Horizontal fallback gates (40 / 15) are kept at their round-1 values: fallback should not be made easier while the goal is to reduce it. hough_threshold_vertical left at prior (ring count already exact). Denoising, enhancing and SAM untouched so the round-2 delta remains attributable to detection; if det_real_detection_ratio rises and sam_segment_size_cv stays >1, round 3 can revisit SAM template geometry, otherwise round 3 backs off toward the round-1 settings.",
    "proposer": "Fable-5.1 (fresh per-case agent)"
  },
  {
    "round": 3,
    "status": "ok",
    "overlay": {
      "detecting": {
        "binary_threshold": 110,
        "hough_threshold_oblique": 35,
        "hough_threshold_horizontal": 40,
        "maxLineGap_oblique": 65,
        "maxLineGap_horizontal": 15,
        "pattern_tolerance": 20
      }
    },
    "proxy_scaled": 0.5773851068518312,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.27511968809368287,
      "sam_fill_rate": 0.7318014994277484,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.2093606933058968
    },
    "recentre_residual_max_cm": 2.0,
    "full_pipeline": false,
    "rationale": "Single-lever final round. Restore the Hough/binarisation gates to the round-1 optimum (binary_threshold 110, hough_threshold_oblique 35, maxLineGap_oblique 65, horizontal 40/15) because round 2 showed the extra relaxation only added bolt-row lines and cost proxy; then push the one lever not yet exhausted, pattern_tolerance, to its bound 12 -> 20 so the ~250-300 px K-bracketing intersections on the currently assumed rings are accepted as real (midpoint) centres instead of falling back. Relative to round 1 the only change is pattern_tolerance, so the delta is cleanly attributable; false-match risk from the wider tolerance is bounded because the tighter round-1 Hough gates keep the line set small (minLineLength fixed), merge_close_points still collapses near-duplicates, and the ring count/verticals are already exact. hough_threshold_vertical untouched (ring_count_error 0). Denoising, enhancing and SAM template geometry left at priors: sam_fill_rate has been invariant across rounds, NaN is family-normal, and det_real_detection_ratio has not yet risen, which the round-2 plan set as the precondition for touching SAM geometry. Expected signal: det_real_detection_ratio 0.6 -> >=0.7, correspondence_f1@15 >= round-1 0.275, sam_segment_size_cv falling below ~1.0; if instead f1 returns to ~0.275 with 'assume' count unchanged, round 1 remains the selected round.",
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
`/home/boringtao/Projects/Proxy4Tun/data/sc-general/stage3/packets-fable-fresh/4-2/round3_proposal.json`

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
