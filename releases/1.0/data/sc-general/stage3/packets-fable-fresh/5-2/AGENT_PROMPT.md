# Fable 5.1 reflection — subset 5-2 (propose round 3)

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

- subset: `5-2`
- family: `t4&5`
- lining_mode: `complex`
- stage1_unlocked: `False` (residual gate 10 cm)
- arm: `fable_fresh` / proposer: `Fable-5.1 (fresh per-case agent)`
- model: `claude-fable-5-1-thinking-high`

### Anchor (GT-blind)
```json
{
  "proxy_raw": 0.682908,
  "proxy_scaled": 0.682908,
  "band": "refine",
  "features": {
    "correspondence_f1@15": 0.452805,
    "sam_fill_rate": 0.751179,
    "ring_count_error": 0.0,
    "depth_nan_ratio": 0.193998
  },
  "recentre_residual_max_cm": 2.1,
  "orient_axis_corr": 0.8418715723827292,
  "ring_count": 10,
  "ring_count_error": 0.0,
  "labelmap_source": "only_label.csv",
  "run_dir": "/home/boringtao/Projects/Proxy4Tun/data/bo/unified/5-2-family-proxy/runs/5-2-anchor"
}
```

### Intrinsics (GT-blind)
```json
{
  "orient_axis_corr": 0.8418715723827292,
  "orient_invariant_ok": 1.0,
  "recentre_residual_max_cm": 2.1,
  "denoise_retained_ratio": 0.7623915847687736,
  "depth_nan_ratio": 0.1939982824150022,
  "depth_outlier_ratio": 0.0012904843554376751,
  "det_real_detection_ratio": 0.6,
  "det_fallback_ratio": 0.4,
  "det_n_points": 10.0,
  "sam_fill_rate": 0.7511792176693792,
  "sam_ring_completeness": 1.0,
  "sam_segment_size_cv": 1.0878136310564073,
  "sam_ontology_divergence": 0.1373509792086076
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
        "binary_threshold": 115,
        "hough_threshold_oblique": 35,
        "maxLineGap_oblique": 65,
        "hough_threshold_horizontal": 45,
        "pattern_tolerance": 12
      }
    },
    "proxy_scaled": 0.6872429628308712,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.46113417238127696,
      "sam_fill_rate": 0.7511792176693792,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.19503760381000143
    },
    "recentre_residual_max_cm": 2.1,
    "full_pipeline": false,
    "rationale": "The 40% fallback rate means SAM templates are placed at assumed heights on 4 rings, which is the cheapest source of the unsupported label boundaries in the SC overlay. To convert fallbacks into real detections without touching healthy stages: (1) slightly lower enhancing.curvature_threshold 0.0005 -> 0.0004 so more joint-boundary points qualify for the outlier map and the dashed taper joints become more continuous; (2) lower detecting.binary_threshold 127 -> 115 so fainter joint pixels survive binarisation; (3) relax oblique Hough (threshold 50 -> 35, maxLineGap 50 -> 65) so bolt-hole-interrupted joint traces are bridged into full oblique segments, mirroring the 5-1 fix that lowered oblique/horizontal thresholds after ring-consistent verticals were in place; (4) modestly lower the horizontal threshold 50 -> 45 so the fallback remains usable but is no longer the dominant path; (5) raise pattern_tolerance to 12 px so real intersections that miss the K/AB pattern by a few pixels are accepted instead of being replaced by 'assume'. hough_threshold_vertical is left untouched because 10 verticals already match 10 rings; denoising mask_r is left at tunnel priors (section 4: geometry knobs are load-bearing for transfer, not per-scan tuning); unfolding is omitted because stage1_unlocked is false; SAM geometry is left for round 2 once det_real_detection_ratio and correspondence_f1@15 confirm the prompts improved. Expected GT-free signal: det_real_detection_ratio up from 0.6, det_fallback_ratio down from 0.4, correspondence_f1@15 up from 0.45, sam_segment_size_cv down from 1.09, with ring_count_error staying 0 and NaN ratio unchanged.",
    "proposer": "Fable-5.1 (fresh per-case agent)"
  },
  {
    "round": 2,
    "status": "ok",
    "overlay": {
      "enhancing": {
        "curvature_threshold": 0.0004
      },
      "detecting": {
        "binary_threshold": 110,
        "hough_threshold_oblique": 35,
        "maxLineGap_oblique": 65,
        "hough_threshold_horizontal": 32,
        "maxLineGap_horizontal": 28,
        "pattern_tolerance": 15
      }
    },
    "proxy_scaled": 0.6930995275794218,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.4718530586343308,
      "sam_fill_rate": 0.7511792176693792,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.19503760381000143
    },
    "recentre_residual_max_cm": 2.1,
    "full_pipeline": false,
    "rationale": "Round 1 confirmed that relaxing the oblique branch alone cannot recover rings whose K joints leave no oblique trace in the outlier map; those rings must be recovered through the horizontal K/AB distance pattern instead. Overlays are applied to the anchor parameters, so the round-1 detection settings are restated and extended: (1) detecting.maxLineGap_horizontal 10 -> 28 so the dotted horizontal joint traces (gaps of roughly 15-25 px between enhanced outlier pixels) are bridged into segments longer than the 105 px minLineLength; (2) detecting.hough_threshold_horizontal 45 -> 32 so sparser dotted traces reach the accumulator threshold once bridged, while staying above the bound floor to avoid bolt-hole rows (bolt marks are ~40-60 px apart and would still exceed the gap) being read as lines; (3) detecting.binary_threshold 115 -> 110 so slightly fainter joint pixels in the low-density left rings survive binarisation and feed both Hough branches; (4) detecting.pattern_tolerance 12 -> 15 px so bridged lines whose fitted y is a few pixels off the ideal K (245 px) / AB (745 px) spacing are still accepted by check_distance_pattern instead of dropping to 'assume'; (5) oblique branch kept at round-1 values (threshold 35, maxLineGap 65) because it already yields the real K pairs in the central rings and further relaxation only added tiny spurious red stubs; (6) enhancing.curvature_threshold kept at 0.0004 for continuity so the between-round delta is attributable to the horizontal-branch change; (7) hough_threshold_vertical untouched (10 verticals = 10 rings); (8) denoising and sam untouched (geometry knobs are load-bearing for transfer, and measured K/ring pitch match the priors); unfolding omitted because stage1_unlocked is false. Expected GT-free signal: det_fallback_ratio down from 0.4 (fewer 'assume' types, more 'midpoint'/pattern-derived centres), det_n_points still 10, correspondence_f1@15 up from 0.46 as the edge-ring label boundaries move onto the horizontal joints, sam_segment_size_cv down from 1.09, sam_fill_rate >= 0.75, ring_count_error 0, NaN ratio unchanged; proxy expected to move from 0.687 toward the 0.70 accept threshold. Failure signature to watch: if det_n_points rises above 10 or spurious blue lines appear on bolt-hole rows, the horizontal threshold went too low and round 3 should raise it back toward 40 while keeping maxLineGap_horizontal.",
    "proposer": "Fable-5.1 (fresh per-case agent)"
  },
  {
    "round": 3,
    "status": "ok",
    "overlay": {
      "enhancing": {
        "curvature_threshold": 0.0004
      },
      "detecting": {
        "binary_threshold": 105,
        "hough_threshold_oblique": 35,
        "maxLineGap_oblique": 65,
        "hough_threshold_horizontal": 28,
        "maxLineGap_horizontal": 30,
        "pattern_tolerance": 20
      }
    },
    "proxy_scaled": 0.6985248389937473,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.48178265020111755,
      "sam_fill_rate": 0.7511792176693792,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.19503760381000143
    },
    "recentre_residual_max_cm": 2.1,
    "full_pipeline": false,
    "rationale": "Overlays are applied to the anchor parameters, so all round-2 settings are restated and pushed one step further along the direction that produced +0.006 proxy / +0.011 correspondence_f1 in round 2, using the remaining bounded headroom and the fact that the round-2 spurious-line signature did not appear: (1) detecting.maxLineGap_horizontal 28 -> 30 (bound ceiling) so the dotted traces in the x=540 and x=180 rings, which currently stop 30-60 px short of the vertical, are bridged across the last gap and actually intersect the ring-centre vertical; bolt-hole glyphs are ~60-100 px apart so they still exceed the gap and are not bridged; (2) detecting.hough_threshold_horizontal 32 -> 28 so the sparser left-end traces reach the accumulator threshold once bridged; kept 3 votes above the 25 floor because a 105 px minLineLength window over a bolt-glyph row collects only ~2 glyphs (~20 votes) and must stay below threshold; (3) detecting.pattern_tolerance 15 -> 20 (bound ceiling) so the x=3420 pair (~730 px vs AB 745 px) and any K pair off by 15-20 px are accepted by check_distance_pattern instead of dropping to 'assume'; 20 px = 10 cm = 2.7% of AB height, small relative to the 245 px K / 745 px AB separation, so chance matches remain unlikely with 1-3 lines per ring; (4) detecting.binary_threshold 110 -> 105 so slightly fainter outlier pixels in the low-density left rings (visibly sparser in depth_map_viridis) survive binarisation and feed both Hough branches; (5) oblique branch held at round-1/2 values (threshold 35, maxLineGap 65): it already yields the real K pairs in the central rings and further relaxation only produced short spurious stubs in round 1; (6) enhancing.curvature_threshold held at 0.0004 so the between-round delta stays attributable to the horizontal/pattern change; (7) hough_threshold_vertical untouched (10 verticals = 10 rings, ring_count_error 0); (8) denoising untouched (mask_r geometry knobs are load-bearing for transfer and retention 0.76 is healthy) and sam untouched (sam_fill_rate is pinned by the NaN stripes across all rounds, K-pair spacing ~245 px and ring pitch 360 px match the T5 priors, so segment_width/K_height/angle are not the limiting factor and would confound attribution in the final round); unfolding omitted because stage1_unlocked is false. Expected GT-free signal: det_fallback_ratio down from 0.4 (one or more of the four 'assume' rings converting to pattern-derived centres), det_n_points still 10, correspondence_f1@15 up from 0.472 as edge-ring label boundaries move onto the horizontal joints, sam_segment_size_cv down from 1.09, sam_fill_rate ~ 0.75, ring_count_error 0, NaN ratio unchanged, proxy moving from 0.693 toward the 0.70 accept threshold. Failure signature: if det_n_points exceeds 10 or blue segments appear on bolt-glyph rows, the horizontal threshold/tolerance went too far and the round-2 configuration should be selected instead.",
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
`/home/boringtao/Projects/Proxy4Tun/data/sc-general/stage3/packets-fable-fresh/5-2/round3_proposal.json`

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
