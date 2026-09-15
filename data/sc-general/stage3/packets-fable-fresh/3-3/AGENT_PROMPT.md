# Fable 5.1 reflection — subset 3-3 (propose round 3)

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

- subset: `3-3`
- family: `t3`
- lining_mode: `continuous`
- stage1_unlocked: `False` (residual gate 10 cm)
- arm: `fable_fresh` / proposer: `Fable-5.1 (fresh per-case agent)`
- model: `claude-fable-5-1-thinking-high`

### Anchor (GT-blind)
```json
{
  "proxy_raw": 0.52158,
  "proxy_scaled": 0.52158,
  "band": "refine",
  "features": {
    "correspondence_f1@15": 0.112841,
    "sam_fill_rate": 0.779975,
    "ring_count_error": 0.0,
    "depth_nan_ratio": 0.113874
  },
  "recentre_residual_max_cm": 2.7,
  "orient_axis_corr": 0.99996584722565,
  "ring_count": 10,
  "ring_count_error": 0.0,
  "labelmap_source": "results.pkl",
  "run_dir": "/home/boringtao/Projects/Proxy4Tun/data/bo/unified/3-3-family-proxy/runs/3-3-anchor"
}
```

### Intrinsics (GT-blind)
```json
{
  "orient_axis_corr": 0.99996584722565,
  "orient_invariant_ok": 1.0,
  "recentre_residual_max_cm": 2.7,
  "denoise_retained_ratio": 0.81787798500355,
  "depth_nan_ratio": 0.11387375767737186,
  "depth_outlier_ratio": 0.0007244705635925862,
  "det_real_detection_ratio": 0.0,
  "det_fallback_ratio": 1.0,
  "det_n_points": 10.0,
  "sam_fill_rate": 0.7799747173013317,
  "sam_ring_completeness": 1.0,
  "sam_segment_size_cv": 0.5941911494447767,
  "sam_ontology_divergence": 0.2503766921544423
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
        "hough_threshold_horizontal": 45,
        "hough_threshold_vertical": 2000,
        "maxLineGap_oblique": 50,
        "pattern_tolerance": 12,
        "uniform_k_snap": true
      }
    },
    "proxy_scaled": 0.5554790235434068,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.1753798973342327,
      "sam_fill_rate": 0.7789772628881154,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.11387375767737186
    },
    "recentre_residual_max_cm": 2.7,
    "full_pipeline": false,
    "rationale": "Relax the oblique Hough path so the K-edge joints are traced across all 10 rings and the fainter A/B joints get a chance to appear: lower binary_threshold 127->110 so faint outlier pixels along joints survive binarisation, lower hough_threshold_oblique to 24 so shorter tapered joint segments in the mid-image rings pass the accumulator, and raise maxLineGap_oblique to 50 so segments bridge the ~40-60 px cable brackets and bolt-hole gaps that currently fragment the K edges (minLineLength is left at anchor so isolated bolt-blob pairs 240 px apart still cannot merge into a false line). To protect precision, raise hough_threshold_horizontal to 45 so horizontal bolt-hole rows (which are not label boundaries) do not enter the joint-line set now that the binary map is denser, and pin hough_threshold_vertical at 2000 so the denser binary map cannot admit extra real verticals and break the currently exact 10-for-10 ring count (synthetic ring-centre verticals remain). Keep uniform_k_snap true (continuous strategy) and set pattern_tolerance 12 px so the recovered K-edge pairs (measured ~160 px vs 165 px prior) are accepted as real K-row anchors, tightening the gate residual instead of relying purely on propagation. Denoising, enhancing and SAM are intentionally left at anchor this round: the theta/r band is at tunnel priors and tightening theta would only remove partial-A lining (cosmetic NaN gain, real coverage loss); curvature_threshold up would over-smooth joints; SAM geometry (segment_width 240 px, K_height 165 px, taper) already agrees with the observed line spacing and should be revisited only after the correspondence delta from detection is known. Expected proxy effect: correspondence_f1@15 up via more supported joint lines; ring_count_error stays 0; depth_nan_ratio unchanged; sam_fill_rate roughly unchanged.",
    "proposer": "Fable-5.1 (fresh per-case agent)"
  },
  {
    "round": 2,
    "status": "ok",
    "overlay": {
      "detecting": {
        "binary_threshold": 110,
        "hough_threshold_oblique": 20,
        "hough_threshold_horizontal": 45,
        "hough_threshold_vertical": 2000,
        "maxLineGap_oblique": 60,
        "pattern_tolerance": 12,
        "uniform_k_snap": true
      }
    },
    "proxy_scaled": 0.5564527420759965,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.17697298547798565,
      "sam_fill_rate": 0.7793582350598299,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.11387375767737186
    },
    "recentre_residual_max_cm": 2.7,
    "full_pipeline": false,
    "rationale": "Finish the detection lever before touching SAM: take hough_threshold_oblique to its lower bound (20) and maxLineGap_oblique to its upper bound (60) so the fragmented K-edge bracket signal in the middle rings (x~1000-1800) can accumulate enough votes and bridge the ~50-60 px bracket gaps to form segments; an offline permissive Hough on the round-1 outlier map at these settings yielded 13 oblique segments (vs ~8 now) of which 11 lie within ~10 px of the template K edges and only 1-2 sit on bolt rows, so expected precision cost is small relative to the recall gain. Keep the round-1 guards (horizontal 45 so bolt rows do not enter as horizontal lines, vertical 2000 so the exact 10/10 ring count is preserved, snap on, tolerance 12 which already accepted 3 real K anchors at 3.9 px residual). Denoising/enhancing stay at anchor (stages 1-3 healthy; theta tightening would only drop partial-A lining). SAM stays at anchor this round so the round-2 delta is attributable to detection alone; round 3 will then either lock in the best detection set and test a minimal SAM width alignment (measured ring pitch 241.7 px = 1208 mm vs 1200 mm template) or revert if precision fell. Expected: correspondence_f1@15 up modestly, other lean features unchanged.",
    "proposer": "Fable-5.1 (fresh per-case agent)"
  },
  {
    "round": 3,
    "status": "ok",
    "overlay": {
      "detecting": {
        "binary_threshold": 110,
        "hough_threshold_oblique": 20,
        "hough_threshold_horizontal": 45,
        "hough_threshold_vertical": 2000,
        "maxLineGap_oblique": 60,
        "pattern_tolerance": 12,
        "uniform_k_snap": true
      },
      "sam": {
        "segment_width": 1208,
        "angle": 7.0
      }
    },
    "proxy_scaled": 0.5904632480913411,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.23754971302462086,
      "sam_fill_rate": 0.7827246437044348,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.11387375767737186
    },
    "recentre_residual_max_cm": 2.7,
    "full_pipeline": false,
    "rationale": "Lock the round-2 detecting set (binary 110, oblique 20, horizontal 45, vertical 2000, gap 60, tolerance 12, snap on) so the exact 10/10 ring count, bolt-row guards and best-so-far line yield are preserved, and use the final round for the minimal SAM geometry alignment that round 2 deferred: set sam.segment_width to 1208 mm so each ring template spans the measured 241.7 px pitch instead of 240 px (closing the ~1.7 px inter-ring template gap that leaves thin unlabelled seams between adjacent ring masks and slightly under-covers the ring margins), and set sam.angle to 7.0 deg so the K wedge template edges follow the measured +/-7 deg oblique K-edge lines rather than the 6.12 deg prior, bringing the SAM-derived K boundaries closer to the detected lines at the ring margins where the 15 px correspondence test is tightest. K_height stays at anchor (823.8 mm) because the measured K-edge spacing (~164 px = 820 mm) already matches within ~1 px. Denoising and enhancing stay at anchor: theta tightening would remove partial A1/A3 lining for a cosmetic NaN gain and shift the K-row design position, and raising curvature_threshold risks joint over-smoothing that would erode the few supported K-edge lines. Expected effect: sam_fill_rate up slightly (seam closure), correspondence_f1@15 flat to slightly up (K boundaries better co-linear with detected lines), ring_count_error 0 and depth_nan_ratio unchanged; if the SAM change is neutral, the round-2 detecting configuration remains the best candidate for selection.",
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
`/home/boringtao/Projects/Proxy4Tun/data/sc-general/stage3/packets-fable-fresh/3-3/round3_proposal.json`

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
