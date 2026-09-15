# Fable 5.1 reflection — subset 3-8 (propose round 3)

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

- subset: `3-8`
- family: `t3`
- lining_mode: `continuous`
- stage1_unlocked: `True` (residual gate 10 cm)
- arm: `fable_fresh` / proposer: `Fable-5.1 (fresh per-case agent)`
- model: `claude-fable-5-1-thinking-high`

### Anchor (GT-blind)
```json
{
  "proxy_raw": 0.561281,
  "proxy_scaled": 0.561281,
  "band": "refine",
  "features": {
    "correspondence_f1@15": 0.302212,
    "sam_fill_rate": 0.59695,
    "ring_count_error": 0.0,
    "depth_nan_ratio": 0.182088
  },
  "recentre_residual_max_cm": 24.0,
  "orient_axis_corr": 0.9995216099864935,
  "ring_count": 10,
  "ring_count_error": 0.0,
  "labelmap_source": "results.pkl",
  "run_dir": "/home/boringtao/Projects/Proxy4Tun/data/bo/unified/3-8-family-proxy/runs/3-8-anchor"
}
```

### Intrinsics (GT-blind)
```json
{
  "orient_axis_corr": 0.9995216099864935,
  "orient_invariant_ok": 1.0,
  "recentre_residual_max_cm": 24.0,
  "denoise_retained_ratio": 0.7258077773485341,
  "depth_nan_ratio": 0.18208811279684348,
  "depth_outlier_ratio": 0.0008981363284279751,
  "det_real_detection_ratio": 0.0,
  "det_fallback_ratio": 1.0,
  "det_n_points": 10.0,
  "sam_fill_rate": 0.596949720945907,
  "sam_ring_completeness": 0.8888888888888888,
  "sam_segment_size_cv": 0.6767146840216215,
  "sam_ontology_divergence": 0.19893838940867875
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
        "random_seed": 0,
        "ransac_threshold": 0.9
      },
      "denoising": {
        "mask_r_low": 2.85,
        "mask_r_high": 3.05,
        "mask_theta_low": 1.55,
        "mask_theta_high": 17.15
      },
      "enhancing": {
        "curvature_threshold": 0.0005
      },
      "detecting": {
        "binary_threshold": 118,
        "hough_threshold_oblique": 24,
        "hough_threshold_horizontal": 22,
        "hough_threshold_vertical": 1500,
        "maxLineGap_oblique": 42,
        "pattern_tolerance": 10,
        "uniform_k_snap": true
      },
      "sam": {
        "segment_width": 1200,
        "K_height": 823.8,
        "angle": 6.12
      }
    },
    "proxy_scaled": 0.37410147712792724,
    "band": "reject",
    "features": {
      "correspondence_f1@15": 0.06793489572493028,
      "sam_fill_rate": 0.46382571243044196,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.29341296529647
    },
    "recentre_residual_max_cm": 39.4,
    "full_pipeline": true,
    "rationale": "Round 1 spends the budget on stages 1-4 per the empirical tuning order. Unfolding: raise the centre-curve polynomial degree to 3 with a pinned seed (0) and a slightly tighter RANSAC threshold so the fitted curve can follow the end-of-span bend that leaves a 24 cm residual; stage1 is unlocked so the pilot will run --full. Denoising: keep the t3 prior inner radius (2.85) but open the outer gate a little (3.0 -> 3.05) so bolt-pocket/joint-row points and any remaining mildly off-centre end points are retained instead of punched out as NaN; theta gates stay at the t3 prior. Enhancing: keep curvature at the notebook default. Detecting: lower the binary threshold (127 -> 118) and the oblique/horizontal Hough thresholds (30 -> 24 / 22), raise oblique maxLineGap (30 -> 42) so the fragmented joint rows at ~800/~2300 and the left half of the K row yield continuous lines that the SAM boundaries can be matched against; pattern_tolerance 10 px and uniform_k_snap kept on because continuous lining needs the snapped K row. SAM geometry is left at the t3 priors (1200 mm, 823.8 mm, 6.12 deg) because per section 6 SAM knobs are only worth tuning once coverage and detection are healthy. Expected: lower depth_nan_ratio and higher sam_fill_rate from the recentred left end, higher correspondence_f1@15 from denser joint lines; residual itself should drop toward the 10 cm gate.",
    "proposer": "Fable-5.1 (fresh per-case agent)"
  },
  {
    "round": 2,
    "status": "ok",
    "overlay": {
      "denoising": {
        "mask_r_low": 2.78,
        "mask_r_high": 3.1,
        "mask_theta_low": 1.55,
        "mask_theta_high": 17.15
      },
      "enhancing": {
        "curvature_threshold": 0.0005
      },
      "detecting": {
        "binary_threshold": 112,
        "hough_threshold_oblique": 22,
        "hough_threshold_horizontal": 20,
        "hough_threshold_vertical": 1500,
        "maxLineGap_oblique": 40,
        "pattern_tolerance": 10,
        "uniform_k_snap": true
      },
      "sam": {
        "segment_width": 1200,
        "K_height": 823.8,
        "angle": 6.12
      }
    },
    "proxy_scaled": 0.5166872969912764,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.2175955496554776,
      "sam_fill_rate": 0.59319749139001,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.169279745918914
    },
    "recentre_residual_max_cm": 24.0,
    "full_pipeline": false,
    "rationale": "Round 2 is a recovery round: omit unfolding entirely (full=false) so the pilot replays stages 2-6 on the frozen anchor stage-1, discarding the degree-3 centreline that caused the round-1 collapse; with the anchor map straight and ring_count_error 0, the remaining losses are at ring 0 and in line yield. Denoising: widen the radial gate moderately from the t3 prior [2.85, 3.0] to [2.78, 3.10] (band 15 -> 32 cm, still inside bounds and well short of the limits) so ring-0 lining points displaced by the 24 cm end residual are retained instead of punched out as NaN; the t3 theta gate stays at the prior [1.55, 17.15] so the rail/floor region is still removed, and the density/gradient filter guards against under-gate leakage. This is a deliberate, bounded departure from 'keep band at priors' because the prescribed remedy (better centreline) was tried in round 1 and made things worse. Enhancing: curvature_threshold kept at the default 0.0005. Detecting: lower binary_threshold 127 -> 112 so the dotted joint rows survive binarisation and dilate into continuous strokes; lower hough_threshold_oblique 30 -> 22 and hough_threshold_horizontal 30 -> 20; raise maxLineGap_oblique 30 -> 40, which bridges the 10-30 px gaps between joint dots but stays below the ~50 px gaps between bolt pockets in a row so pocket rows do not become spurious lines; hough_threshold_vertical 1500 kept (it gave exactly 10 verticals for 10 rings on the anchor), pattern_tolerance 10 and uniform_k_snap true kept for the continuous K-row snap. SAM: t3 priors (1200 mm, 823.8 mm, 6.12 deg) untouched. Expected on the frozen stage-1: depth_nan_ratio below the anchor's 0.18 (ring-0 void shrinks), sam_fill_rate above 0.60 as ring-0 masks get valid pixels, correspondence_f1@15 above 0.30 from more accepted lines along the joint rows, ring_count_error stays 0, residual stays 24 cm (not penalised by the lean proxy). Target: back above the anchor 0.561 and into the upper refine band; round 3 can then either tighten detection if spurious pocket lines appear or revisit stage 1 with degree 2 / looser RANSAC.",
    "proposer": "Fable-5.1 (fresh per-case agent)"
  },
  {
    "round": 3,
    "status": "ok",
    "overlay": {
      "denoising": {
        "mask_r_low": 2.85,
        "mask_r_high": 3.0,
        "mask_theta_low": 1.55,
        "mask_theta_high": 17.15
      },
      "enhancing": {
        "curvature_threshold": 0.0005
      },
      "detecting": {
        "binary_threshold": 127,
        "hough_threshold_oblique": 40,
        "hough_threshold_horizontal": 40,
        "hough_threshold_vertical": 1500,
        "maxLineGap_oblique": 45,
        "pattern_tolerance": 10,
        "uniform_k_snap": true
      },
      "sam": {
        "segment_width": 1200,
        "K_height": 823.8,
        "angle": 6.12
      }
    },
    "proxy_scaled": 0.5483360269939598,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.27852100999793966,
      "sam_fill_rate": 0.5969456111654515,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.18208811279684348
    },
    "recentre_residual_max_cm": 24.0,
    "full_pipeline": false,
    "rationale": "Round 3 is a precision round on the frozen anchor stage-1 (full=false). Denoising: revert to the t3 priors [2.85, 3.0] and theta [1.55, 17.15], the band the anchor scored 0.561 with; the round-2 widening gained ~1 pt of NaN and nothing in fill, and it fed spurious outlier points, so it fails the r_tighten_hough precondition. Enhancing: curvature_threshold at the default 0.0005. Detecting: binary_threshold back to the default 127 so faint pocket edges do not survive binarisation; hough_threshold_oblique raised to 40 (anchor 30, round 2 22) so a line needs >= 40 collinear votes, which a ~40 px bolt-pocket edge cannot supply but the ~1000 px K-row seam can; maxLineGap_oblique raised to 45 (anchor 30) so the dotted K seam, including its sparser left half (x < 1000) that produced no lines on the anchor, is bridged into long continuous lines that carry more votes and cover more of the K label boundaries within 15 px; 45 stays well below the ~85 px clear gap between adjacent bolt pockets in a row, so pocket rows cannot chain into a line. hough_threshold_horizontal raised to 40 to drop the short unexplained horizontals (the true joint rows at ~770/~2300 are dotted with gaps above the fixed 10 px horizontal maxLineGap, so they only ever produce short fragments that fall outside the 15 px tolerance and cost precision). hough_threshold_vertical kept at 1500 (10 verticals for 10 rings), pattern_tolerance 10 and uniform_k_snap true kept for the continuous K-row snap, which also guarantees prompts even if line yield drops. SAM: t3 priors (1200 mm, 823.8 mm, 6.12 deg) untouched. Expected vs anchor: depth_nan_ratio ~0.18 and sam_fill_rate ~0.60 unchanged (same band, same stage-1), ring_count_error 0, correspondence_f1@15 above the anchor 0.30 from higher precision (fewer unexplained fragments) and higher K-row recall (longer lines), pushing proxy above 0.561 into the upper refine band. If the tightened threshold instead removes the K-row lines entirely, the snap regime keeps the prompts and the run degrades toward, not below, the anchor's line set, so downside is bounded and the anchor remains selectable.",
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
`/home/boringtao/Projects/Proxy4Tun/data/sc-general/stage3/packets-fable-fresh/3-8/round3_proposal.json`

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
