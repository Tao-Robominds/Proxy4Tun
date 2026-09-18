# Fable 5.1 reflection — subset 1-3 (propose round 3)

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

- subset: `1-3`
- family: `t1&2`
- lining_mode: `staggered`
- stage1_unlocked: `False` (residual gate 10 cm)
- arm: `fable_fresh` / proposer: `Fable-5.1 (fresh per-case agent)`
- model: `claude-fable-5-1-thinking-high`

### Anchor (GT-blind)
```json
{
  "proxy_raw": 0.550144,
  "proxy_scaled": 0.550144,
  "band": "refine",
  "features": {
    "correspondence_f1@15": 0.186826,
    "sam_fill_rate": 0.732531,
    "ring_count_error": 0.0,
    "depth_nan_ratio": 0.109033
  },
  "recentre_residual_max_cm": 1.4,
  "orient_axis_corr": 0.9999842336199495,
  "ring_count": 10,
  "ring_count_error": 0.0,
  "labelmap_source": "results.pkl",
  "run_dir": "/home/boringtao/Projects/Proxy4Tun/data/bo/unified/1-3-family-proxy/runs/1-3-anchor"
}
```

### Intrinsics (GT-blind)
```json
{
  "orient_axis_corr": 0.9999842336199495,
  "orient_invariant_ok": 1.0,
  "recentre_residual_max_cm": 1.4,
  "denoise_retained_ratio": 0.7653250403055444,
  "depth_nan_ratio": 0.10903285620918383,
  "depth_outlier_ratio": 0.0042008620385453254,
  "det_real_detection_ratio": 0.9,
  "det_fallback_ratio": 0.1,
  "det_n_points": 10.0,
  "sam_fill_rate": 0.7325314614464593,
  "sam_ring_completeness": 0.8888888888888888,
  "sam_segment_size_cv": 1.3403191091625246,
  "sam_ontology_divergence": 0.2507391898933104
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
        "inter_radius": 0.075
      },
      "detecting": {
        "binary_threshold": 118,
        "hough_threshold_oblique": 44,
        "hough_threshold_horizontal": 65,
        "maxLineGap_oblique": 60
      }
    },
    "proxy_scaled": 0.5485286942268396,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.18273011482630108,
      "sam_fill_rate": 0.7348142161386132,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.10901596650288678
    },
    "recentre_residual_max_cm": 1.4,
    "full_pipeline": false,
    "rationale": "Coordinated stage-3 + stage-4 move aimed directly at correspondence_f1@15. (1) enhancing.inter_radius 0.06 -> 0.075 (+15 px -> ~15 px interpolation reach) bridges dashed joint points into continuous boundary traces before projection, raising joint contrast in the outlier map. (2) detecting.binary_threshold 127 -> 118 admits slightly fainter joint pixels after dilation. (3) detecting.hough_threshold_oblique -> 44 and detecting.maxLineGap_oblique -> 60 let the [5,10]/[-10,-5] deg accumulator accept the longer but still gapped oblique joints at the A/B boundaries (K +/- 648 px) and in the low-density columns; the angle filter and the K/AB distance-pattern gate limit spurious acceptances. (4) detecting.hough_threshold_horizontal -> 65 suppresses the unexplained horizontal fallback lines (orange in the overlay) that dilute correspondence precision; horizontal is fallback-only and did not rescue the single 'assume' prompt anyway. Vertical threshold untouched (10 lines == 10 rings). Denoising left at tunnel priors (retention healthy; experiences section 4). SAM y_bounds not changed: sam_fill_rate 0.73 losses coincide with the physical void bands at y~250 and y~2500, not with a graded per-class weakness, so SAM geometry is not the identified failure this round. Unfolding omitted (stage1_unlocked false, residual 1.4 cm). Expected signal: more cyan joint lines and more green label boundaries in the overlay, fewer orange horizontals, det_fallback_ratio -> 0, proxy up via correspondence_f1@15 while ring_count_error stays 0.",
    "proposer": "Fable-5.1 (fresh per-case agent)"
  },
  {
    "round": 2,
    "status": "ok",
    "overlay": {
      "enhancing": {
        "inter_radius": 0.05
      },
      "detecting": {
        "hough_threshold_oblique": 56,
        "hough_threshold_horizontal": 90,
        "maxLineGap_oblique": 30
      }
    },
    "proxy_scaled": 0.560582400731748,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.2059424975717962,
      "sam_fill_rate": 0.7325051866456749,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.10903044339399855
    },
    "recentre_residual_max_cm": 1.4,
    "full_pipeline": false,
    "rationale": "Round 2 reverses direction to a precision-first detection overlay while keeping the round-1 lesson: (1) detecting.hough_threshold_oblique -> 56 (above the 50 anchor) and detecting.maxLineGap_oblique -> 30 (below the 40 anchor) so only long, well-supported K-wedge joints (the ~100-200 px oblique traces at y~1090/1290 and 1510/1730) survive and short speckle-bridged segments in the dense columns are rejected; 56 is chosen, not higher, to keep the marginal ~100 px line at x~120 that was real in the anchor. (2) detecting.hough_threshold_horizontal -> 90 (bound max) to suppress the persistent unexplained horizontal fallback lines that lower correspondence precision and never contributed a correct prompt. (3) enhancing.inter_radius -> 0.05 (slightly below the 0.06 default; reverting the 0.075 increase that over-interpolated the dense region) to reduce interpolated speckle in the outlier map at source while leaving real joint traces, which are already continuous in those columns. (4) binary_threshold dropped from the overlay (reverts to anchor 127) - the outlier map is near-binary, so the round-1 change was inert. Vertical threshold unchanged (10 == 10). Denoising untouched (retention 0.77 healthy; experiences section 4). SAM y_bounds still untouched this round to keep attribution clean; if round 2 restores 10/10 pattern-consistent K prompts but F1 stays flat, round 3 should probe sam.processing.y_bounds for the fill-rate term instead of further Hough moves. Unfolding omitted (stage1_unlocked false, residual 1.4 cm). Expected signal: prompts return to two clean rows (~1190 / ~1620) with the x~1330 and x~120 rings corrected, det_fallback_ratio <= 0.1, fewer orange joint lines in the overlay, correspondence_f1@15 >= anchor and proxy back above 0.550.",
    "proposer": "Fable-5.1 (fresh per-case agent)"
  },
  {
    "round": 3,
    "status": "ok",
    "overlay": {
      "denoising": {
        "grad_threshold": 0.16
      },
      "enhancing": {
        "inter_radius": 0.05
      },
      "detecting": {
        "hough_threshold_oblique": 56,
        "hough_threshold_horizontal": 90,
        "maxLineGap_oblique": 30
      }
    },
    "proxy_scaled": 0.5671373345431867,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.2180907147760203,
      "sam_fill_rate": 0.7322009244525908,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.10903089579684579
    },
    "recentre_residual_max_cm": 1.4,
    "full_pipeline": false,
    "rationale": "Final round keeps the proven round-2 stage-3/stage-4 configuration unchanged (inter_radius 0.05; oblique threshold 56, maxLineGap 30, horizontal 90) so the gain is preserved, and adds exactly one upstream lever: denoising.grad_threshold 0.2 -> 0.16 (bounds [0.1, 0.25]). A stricter density-gradient gate preferentially removes low-density off-surface points adjacent to the dense lining surface - the scanner-near speckle - while leaving the surface and the real joint depth steps (which are handled by the stage-3 depth thresholds, not by this gate). Expected effect: a thinner speckle field in the outlier map so fewer horizontal accumulations reach the 90-vote threshold (fewer orange lines, higher correspondence precision), with the genuine oblique K joints untouched. Modest step (0.04) chosen to stay clear of over-gating: monitor denoise_retained_ratio (should stay >~0.72) and depth_nan_ratio (should stay ~0.11); if either degrades the proposal is rejected in favour of round 2. mask_r_low/high, z_step left at tunnel priors (experiences section 4). Vertical threshold untouched (10 == 10). binary_threshold left at anchor. Unfolding omitted (stage1_unlocked false, residual 1.4 cm). If this round does not beat 0.5606, round 2 should be the selected overlay for 1-3.",
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
`/home/boringtao/Projects/Proxy4Tun/data/sc-general/stage3/packets-fable-fresh/1-3/round3_proposal.json`

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
