# Fable 5.1 reflection — subset 3-9 (propose round 3)

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

- subset: `3-9`
- family: `t3`
- lining_mode: `continuous`
- stage1_unlocked: `False` (residual gate 10 cm)
- arm: `fable_fresh` / proposer: `Fable-5.1 (fresh per-case agent)`
- model: `claude-fable-5-1-thinking-high`

### Anchor (GT-blind)
```json
{
  "proxy_raw": 0.641294,
  "proxy_scaled": 0.641294,
  "band": "refine",
  "features": {
    "correspondence_f1@15": 0.363678,
    "sam_fill_rate": 0.728989,
    "ring_count_error": 0.0,
    "depth_nan_ratio": 0.130822
  },
  "recentre_residual_max_cm": 2.8,
  "orient_axis_corr": 0.9992437316181036,
  "ring_count": 10,
  "ring_count_error": 0.0,
  "labelmap_source": "results.pkl",
  "run_dir": "/home/boringtao/Projects/Proxy4Tun/data/bo/unified/3-9-family-proxy/runs/3-9-anchor"
}
```

### Intrinsics (GT-blind)
```json
{
  "orient_axis_corr": 0.9992437316181036,
  "orient_invariant_ok": 1.0,
  "recentre_residual_max_cm": 2.8,
  "denoise_retained_ratio": 0.7719211863424968,
  "depth_nan_ratio": 0.13082197231971604,
  "depth_outlier_ratio": 0.0009167071232825835,
  "det_real_detection_ratio": 0.0,
  "det_fallback_ratio": 1.0,
  "det_n_points": 10.0,
  "sam_fill_rate": 0.7289890931960742,
  "sam_ring_completeness": 1.0,
  "sam_segment_size_cv": 0.5622869625385611,
  "sam_ontology_divergence": 0.21181901599644315
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
        "hough_threshold_oblique": 25,
        "hough_threshold_horizontal": 25,
        "maxLineGap_oblique": 45,
        "uniform_k_snap": true
      },
      "sam": {
        "segment_width": 1200,
        "K_height": 840.0,
        "angle": 6.12
      }
    },
    "proxy_scaled": 0.6206847726243063,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.32635887918552614,
      "sam_fill_rate": 0.728182254514159,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.13082197231971604
    },
    "recentre_residual_max_cm": 2.8,
    "full_pipeline": false,
    "rationale": "Raise joint-line yield where SAM already places boundaries: lower binary_threshold 127->110 so more thin joint pixels survive binarisation, lower oblique/horizontal Hough thresholds to 25 (T3 prior 30) and raise maxLineGap_oblique to 45 so the fragmented K-edge obliques and the sparse 800/2300 joint rows form continuous lines. Keep vertical accumulator at its current synthetic-fallback regime (untouched) and keep uniform_k_snap on so the K row stays gated. Nudge sam.K_height 823.8->840 to match the measured edge separation, keeping segment_width 1200 and taper angle 6.12 at T3 priors so ring boundaries and taper stay consistent. Denoising and enhancing untouched (retention/NaN healthy; experiences sec.4 says keep band at priors). Expected: more cyan (explained) lines, A/B boundaries turn green, correspondence F1 rises; fill rate should not drop.",
    "proposer": "Fable-5.1 (fresh per-case agent)"
  },
  {
    "round": 2,
    "status": "ok",
    "overlay": {
      "detecting": {
        "binary_threshold": 135,
        "hough_threshold_oblique": 40,
        "hough_threshold_horizontal": 35,
        "maxLineGap_oblique": 40,
        "uniform_k_snap": true
      },
      "sam": {
        "segment_width": 1225,
        "K_height": 823.8,
        "angle": 6.12
      }
    },
    "proxy_scaled": 0.6467773779861794,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.37485976228614615,
      "sam_fill_rate": 0.7266802932755168,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.13082197231971604
    },
    "recentre_residual_max_cm": 2.8,
    "full_pipeline": false,
    "rationale": "Reverse the round-1 direction and tighten detection so only the long, boundary-consistent K-edge lines survive: binary_threshold 110->135 (slightly above the 127 default) so faint bolt-hole pixels drop out of the binarised outlier map before dilation; hough_threshold_oblique 25->40 so 40-60 px fragments no longer reach the accumulator while the multi-hundred-px K-edge obliques keep their votes; hough_threshold_horizontal 25->35 to prune the isolated horizontal stubs that were mostly orange; maxLineGap_oblique 45->40 (kept above the 30 prior) so the K-edge lines remain continuous rather than splitting back into fragments. Vertical accumulator and uniform_k_snap untouched to keep the 10 synthetic verticals and K-row gating identical. SAM: K_height back to the 823.8 mm T3 prior (the 840 nudge produced no measurable fill/F1 change; the SAM K boundary follows the depth discontinuity, not the template height), angle stays 6.12, and segment_width 1200->1225 mm to match the measured 245 px ring pitch so adjacent ring crops tile without the ~5 px gap. Denoising and enhancing untouched (experiences sec.4/7). Expected: fewer orange (unexplained) lines, unchanged cyan coverage on the K edges -> correspondence F1 back above the anchor 0.364; fill rate flat or slightly up; NaN and ring count unchanged.",
    "proposer": "Fable-5.1 (fresh per-case agent)"
  },
  {
    "round": 3,
    "status": "ok",
    "overlay": {
      "detecting": {
        "binary_threshold": 135,
        "hough_threshold_oblique": 45,
        "hough_threshold_horizontal": 35,
        "maxLineGap_oblique": 50,
        "uniform_k_snap": true
      },
      "sam": {
        "segment_width": 1225,
        "K_height": 823.8,
        "angle": 6.12
      }
    },
    "proxy_scaled": 0.6173910862189945,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.32104721595980434,
      "sam_fill_rate": 0.726738220155244,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.13082197231971604
    },
    "recentre_residual_max_cm": 2.8,
    "full_pipeline": false,
    "rationale": "Take one further, smaller step in the round-2 direction and pair it with line continuity: hough_threshold_oblique 40->45 so the 40-60 px bolt-hole fragments at x<150 fall below the accumulator while the multi-hundred-px K-edge segments (which survived 30->40 without losing right-end coverage) keep their votes; maxLineGap_oblique 40->50 so the ~20-40 px gaps between consecutive K-edge segments are bridged into continuous lines along both K boundaries, raising explained boundary length without adding new line loci (the higher threshold prevents the gap bridging from stitching bolt-hole texture into tilted false lines as in round 1). binary_threshold held at 135 (the 110->135 move already removed faint bolt-hole pixels; pushing higher risks thinning the sparse right-end K edges) and hough_threshold_horizontal held at 35 (the A/B rows cannot become long lines under the fixed horizontal minLineLength/maxLineGap priors, so moving it only trades left-edge stubs). hough_threshold_vertical and uniform_k_snap untouched to keep the 10 synthetic verticals and K-row gate identical; pattern_tolerance omitted because it is inert under the snap regime. SAM held at round-2 values: segment_width 1225 (matches the ~245 px ring pitch), K_height 823.8 (T3 prior; SAM K boundary follows the depth step, not the template), angle 6.12. Denoising and enhancing untouched. Expected: fewer orange fragments and longer cyan K-edge lines -> correspondence_f1@15 above 0.375; fill rate, NaN ratio and ring count unchanged; proxy above 0.647.",
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
`/home/boringtao/Projects/Proxy4Tun/data/sc-general/stage3/packets-fable-fresh/3-9/round3_proposal.json`

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
