# Fable 5.1 reflection — subset 1-5 (propose round 3)

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

- subset: `1-5`
- family: `t1&2`
- lining_mode: `staggered`
- stage1_unlocked: `False` (residual gate 10 cm)
- arm: `fable_fresh` / proposer: `Fable-5.1 (fresh per-case agent)`
- model: `claude-fable-5-1-thinking-high`

### Anchor (GT-blind)
```json
{
  "proxy_raw": 0.555111,
  "proxy_scaled": 0.555111,
  "band": "refine",
  "features": {
    "correspondence_f1@15": 0.200763,
    "sam_fill_rate": 0.729429,
    "ring_count_error": 0.0,
    "depth_nan_ratio": 0.117745
  },
  "recentre_residual_max_cm": 2.5,
  "orient_axis_corr": -0.9991614281123364,
  "ring_count": 10,
  "ring_count_error": 0.0,
  "labelmap_source": "results.pkl",
  "run_dir": "/home/boringtao/Projects/Proxy4Tun/data/bo/unified/1-5-family-proxy/runs/1-5-anchor"
}
```

### Intrinsics (GT-blind)
```json
{
  "orient_axis_corr": -0.9991614281123364,
  "orient_invariant_ok": 1.0,
  "recentre_residual_max_cm": 2.5,
  "denoise_retained_ratio": 0.7638200158043973,
  "depth_nan_ratio": 0.11774456253619453,
  "depth_outlier_ratio": 0.006866276013199325,
  "det_real_detection_ratio": 0.8,
  "det_fallback_ratio": 0.2,
  "det_n_points": 10.0,
  "sam_fill_rate": 0.7294291823548552,
  "sam_ring_completeness": 0.8888888888888888,
  "sam_segment_size_cv": 1.303208521951268,
  "sam_ontology_divergence": 0.19335931650162724
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
        "inter_radius": 0.07
      },
      "detecting": {
        "binary_threshold": 135,
        "hough_threshold_oblique": 65,
        "hough_threshold_horizontal": 65,
        "maxLineGap_oblique": 25
      }
    },
    "proxy_scaled": 0.5963478271382726,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.2773381042475027,
      "sam_fill_rate": 0.727196113977595,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.11773151676172088
    },
    "recentre_residual_max_cm": 2.5,
    "full_pipeline": false,
    "rationale": "Correspondence F1 is the feature dragging the proxy into the refine band while evidence features (NaN, retention, ring count) are already healthy, so the round-1 budget goes to prompt-centre quality. Raising hough_threshold_oblique 50->65 and cutting maxLineGap_oblique 40->25 demands more collinear support and prevents bridging across ring joints and bolt-hole gaps, so the long multi-ring oblique lines are rejected while ring-local joints (~240 px, 7.5 deg taper) remain detectable. Raising hough_threshold_horizontal 50->65 suppresses the horizontal fallbacks that lock onto bolt-hole rows and void edges. binary_threshold 127->135 removes weak dilated speckle from the noise cloud around x~1600, y~1450 before Hough. inter_radius 0.06->0.07 mildly densifies interpolated joint points so the sparse left half still yields real detections under the stricter thresholds; it is kept small to avoid re-amplifying noise on the right half. Vertical threshold, denoising geometry (kept at priors per experiences section 4) and unfolding (stage1_unlocked=false) are left untouched. Expected effect: fewer spurious oblique/horizontal lines, prompt centres for rings 4-9 return to the +-435 px stagger seen in rings 0-3, label boundaries align with joint lines, correspondence_f1@15 and sam_fill_rate rise. Risk: det_real_detection_ratio may dip slightly if more rings fall to pattern-assumed centres, but the assumed centres on rings 0-1 were already more consistent than the corrupted midpoints.",
    "proposer": "Fable-5.1 (fresh per-case agent)"
  },
  {
    "round": 2,
    "status": "ok",
    "overlay": {
      "enhancing": {
        "inter_radius": 0.08
      },
      "detecting": {
        "binary_threshold": 150,
        "hough_threshold_oblique": 80,
        "hough_threshold_horizontal": 80,
        "maxLineGap_oblique": 20
      }
    },
    "proxy_scaled": 0.6216492004593013,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.3237647700092291,
      "sam_fill_rate": 0.7269427787849208,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.11771442229861748
    },
    "recentre_residual_max_cm": 2.5,
    "full_pipeline": false,
    "rationale": "Round 1 proved that trading weak oblique/horizontal candidates for pattern-consistent centres raises correspondence F1 without touching NaN, ring count or fill rate, so round 2 exploits the same axis with a bigger step: hough_threshold_oblique 65 -> 80 and hough_threshold_horizontal 65 -> 80 require substantially more collinear votes (a true joint spans a full ring width, ~240 px at 0.005 m/px, so it still clears the bar), maxLineGap_oblique 25 -> 20 forbids bridging across bolt-hole gaps, and binary_threshold 135 -> 150 removes the low-intensity dilated speckle that feeds the accumulator in the right half. inter_radius 0.07 -> 0.08 (upper bound) densifies interpolated joint points so real joints, especially in the sparse left half, keep enough support and rings do not fall back to horizontal-only detection. Expected: rings 4/7/8/9 either yield ring-local joints consistent with the ~432 px two-position stagger or drop to pattern-assumed centres that already match it; label boundaries then align with joint lines, correspondence_f1@15 rises again and sam_fill_rate holds or improves. If this over-tightens (det_real_detection_ratio falls sharply and F1 drops), round 3 will step back to intermediate thresholds and instead try the radial gate (mask_r_low toward the 2.7 prior) to remove protruding non-lining points upstream.",
    "proposer": "Fable-5.1 (fresh per-case agent)"
  },
  {
    "round": 3,
    "status": "ok",
    "overlay": {
      "denoising": {
        "mask_r_low": 2.5
      },
      "enhancing": {
        "inter_radius": 0.08
      },
      "detecting": {
        "binary_threshold": 155,
        "hough_threshold_oblique": 90,
        "hough_threshold_horizontal": 90,
        "maxLineGap_oblique": 20
      }
    },
    "proxy_scaled": 0.5694515587069744,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.22170404674616007,
      "sam_fill_rate": 0.7293334263003766,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.10364181948751568
    },
    "recentre_residual_max_cm": 2.5,
    "full_pipeline": false,
    "rationale": "Round 3 keeps the whole round-2 detection configuration (the best measured so far) and makes two coordinated moves. (1) Final increment on the confirmed axis: hough_threshold_oblique 80 -> 90 and hough_threshold_horizontal 80 -> 90 (upper bounds), binary_threshold 150 -> 155. A genuine joint spans a full ring width (~240 px at 0.005 m/px) and, after dilation, comfortably exceeds 90 collinear votes, whereas speckle chains and bolt-hole rows do not; joint pixels are deep (bright in the outlier map) so 155 still keeps them while trimming more shallow speckle. Binary is stopped at 155 rather than 160 to leave margin against clipping mid-grey joint pixels. maxLineGap_oblique 20 and inter_radius 0.08 are already at their bounds and are retained so left-half joints keep enough interpolated support and no ring falls to horizontal-only detection. (2) Upstream source removal: denoising.mask_r_low -> 2.5 removes points more than 25 cm inside the lining surface (r_lining ~2.75 m) before stage 3, so the speckle that has been feeding the accumulator is not merely out-voted but absent. Both moves push the same failure chain from opposite ends, so the expected effect is the same sign as rounds 1-2: rings 4/7/8/9 either yield ring-local joints on the ~432 px stagger or fall to pattern-assumed centres that already match it, label boundaries align with joint lines, and correspondence_f1@15 rises toward 0.4 while depth_nan_ratio, ring_count_error and sam_fill_rate hold. Attribution rule for reading the result: F1 up with NaN flat = both moves valid; F1 down with det_real_detection_ratio collapsing = Hough over-tightened (revert to 80/80/150); NaN up or fill rate down = radial gate over-cut (revert mask_r_low).",
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
`/home/boringtao/Projects/Proxy4Tun/data/sc-general/stage3/packets-fable-fresh/1-5/round3_proposal.json`

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
