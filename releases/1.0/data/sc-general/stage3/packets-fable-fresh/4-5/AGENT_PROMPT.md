# Fable 5.1 reflection — subset 4-5 (propose round 3)

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

- subset: `4-5`
- family: `t4&5`
- lining_mode: `complex`
- stage1_unlocked: `False` (residual gate 10 cm)
- arm: `fable_fresh` / proposer: `Fable-5.1 (fresh per-case agent)`
- model: `claude-fable-5-1-thinking-high`

### Anchor (GT-blind)
```json
{
  "proxy_raw": 0.609357,
  "proxy_scaled": 0.609357,
  "band": "refine",
  "features": {
    "correspondence_f1@15": 0.334208,
    "sam_fill_rate": 0.735359,
    "ring_count_error": 0.0,
    "depth_nan_ratio": 0.215522
  },
  "recentre_residual_max_cm": 3.4,
  "orient_axis_corr": 0.9810109979941607,
  "ring_count": 10,
  "ring_count_error": 0.0,
  "labelmap_source": "only_label.csv",
  "run_dir": "/home/boringtao/Projects/Proxy4Tun/data/bo/unified/4-5-family-proxy/runs/4-5-anchor"
}
```

### Intrinsics (GT-blind)
```json
{
  "orient_axis_corr": 0.9810109979941607,
  "orient_invariant_ok": 1.0,
  "recentre_residual_max_cm": 3.4,
  "denoise_retained_ratio": 0.7441345095804333,
  "depth_nan_ratio": 0.21552237876528763,
  "depth_outlier_ratio": 0.0010049970802387977,
  "det_real_detection_ratio": 0.6,
  "det_fallback_ratio": 0.4,
  "det_n_points": 10.0,
  "sam_fill_rate": 0.7353592515275288,
  "sam_ring_completeness": 1.0,
  "sam_segment_size_cv": 1.0538854727707543,
  "sam_ontology_divergence": 0.10294109747787984
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
        "maxLineGap_horizontal": 20,
        "pattern_tolerance": 15
      }
    },
    "proxy_scaled": 0.6555404385038113,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.41873519266104525,
      "sam_fill_rate": 0.7353592515275288,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.21552237876528763
    },
    "recentre_residual_max_cm": 3.4,
    "full_pipeline": false,
    "rationale": "Round 1 targets the single lowest lean feature (correspondence_f1@15 = 0.334) with a detection-only overlay so the effect is attributable. Lowering binary_threshold 127->110 keeps more faint joint pixels; oblique threshold 50->35 and maxLineGap 50->65 let broken joint runs vote as one line; horizontal threshold 50->40 and gap 10->20 recover the short horizontal block seams visible in the map; pattern_tolerance 15 gives the K/AB distance check room to accept real intersections instead of falling back. SAM geometry is left untouched this round (stage-5 tuning is only meaningful once detection is consistent, experiences \u00a77), and denoising stays at the T4/T5 prior band since the residual and retention are healthy. Expected: more real prompt points (det_real_detection_ratio up), more label boundaries supported by lines (F1 up), ring count unchanged, NaN unchanged.",
    "proposer": "Fable-5.1 (fresh per-case agent)"
  },
  {
    "round": 2,
    "status": "ok",
    "overlay": {
      "detecting": {
        "binary_threshold": 104,
        "hough_threshold_oblique": 28,
        "hough_threshold_horizontal": 32,
        "maxLineGap_oblique": 75,
        "maxLineGap_horizontal": 26,
        "pattern_tolerance": 18
      }
    },
    "proxy_scaled": 0.6251124832258024,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.3630449022704708,
      "sam_fill_rate": 0.7353592515275288,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.21552237876528763
    },
    "recentre_residual_max_cm": 3.4,
    "full_pipeline": false,
    "rationale": "Round 2 continues the single lever that demonstrably moved the proxy, with step sizes of roughly half the round-1 deltas so the response stays attributable and does not overshoot into spurious detections. binary_threshold 110->104 keeps a few more faint joint pixels in the Hough input without reaching the 100 floor; hough_threshold_oblique 35->28 and maxLineGap_oblique 65->75 let dotted joint runs of ~100 px accumulate to one vote-winning line even with 2-3 breaks; hough_threshold_horizontal 40->32 and maxLineGap_horizontal 20->26 recover more of the short horizontal block seams visible in the map (these support the many red horizontal label boundaries in the overlay); pattern_tolerance 15->18 gives the K/AB distance check a little more room so newly recovered intersections are accepted as real prompts (det_real_detection_ratio up, fallback down) rather than discarded. minLineLength (100 px, fixed) and the +-[5,10] deg angle gate remain the spurious-line guard. Denoising, enhancing and SAM are intentionally untouched: stages 1-3 are healthy, and the bit-identical sam_fill_rate across rounds shows SAM is on geometric fallback, so a template change would be an unmotivated confounder. Expected: more oblique + horizontal lines -> more label boundaries within 15 px -> correspondence_f1@15 rises again (target >= 0.5 to push proxy_scaled toward the 0.70 accept band); ring_count_error stays 0; depth_nan_ratio unchanged; sam_fill_rate may stay identical (fallback) or move slightly if more real prompts are accepted. Stop/revert criterion for round 3: if line count explodes (d9: prompt count >> 10 or many orange unexplained lines) and F1 falls, revert toward the round-1 values; if F1 rises but the proxy stays < 0.70, round 3 is the point to consider a small SAM-geometry step.",
    "proposer": "Fable-5.1 (fresh per-case agent)"
  },
  {
    "round": 3,
    "status": "ok",
    "overlay": {
      "detecting": {
        "binary_threshold": 110,
        "hough_threshold_oblique": 45,
        "hough_threshold_horizontal": 32,
        "maxLineGap_oblique": 40,
        "maxLineGap_horizontal": 26,
        "pattern_tolerance": 15
      }
    },
    "proxy_scaled": 0.6532127741967568,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.41447502138081066,
      "sam_fill_rate": 0.7353592515275288,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.21552237876528763
    },
    "recentre_residual_max_cm": 3.4,
    "full_pipeline": false,
    "rationale": "Round 3 is a decoupled, partial-factor step designed to beat R1 rather than to bracket it: (1) hough_threshold_oblique 28 -> 45 and maxLineGap_oblique 75 -> 40 tighten the oblique family beyond R1 (35/65) and back toward the T4 prior (50/50), so oblique votes must come from a continuous ~100 px tapered-edge run inside one ring; the cross-ring spurious segments of R2 should disappear, raising precision, while genuine K-block tapered edges (within a 370 px column, short gaps) are still admitted. (2) hough_threshold_horizontal 32 and maxLineGap_horizontal 26 stay at the R2 values: a within-ring seam is <= 370 px with minLineLength 105 fixed, so gap 26 cannot bridge across ring joints, and these knobs are the plausible source of the R1 recall gain. (3) binary_threshold reverts 104 -> 110 (R1, the best-known binarisation; 104 admits more V-texture noise into both accumulators). (4) pattern_tolerance reverts 18 -> 15 (R1); it only affects prompt acceptance and cannot move F1 while SAM is on fallback, so R1's value is the safe choice. hough_threshold_vertical, denoising, enhancing and SAM are untouched so any proxy move is attributable to the oblique/horizontal decoupling. Expected: fewer, shorter oblique lines (orange count down), horizontals unchanged or slightly up -> correspondence_f1@15 above the R1 0.419 and proxy_scaled above 0.656 (target >= 0.70); ring_count_error stays 0, depth_nan_ratio and sam_fill_rate remain identical. If instead F1 lands between R2 and R1, the R1 gain was oblique-driven and R1 remains the selection.",
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
`/home/boringtao/Projects/Proxy4Tun/data/sc-general/stage3/packets-fable-fresh/4-5/round3_proposal.json`

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
