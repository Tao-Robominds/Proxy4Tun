# Fable 5.1 reflection — subset 5-3 (propose round 3)

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

- subset: `5-3`
- family: `t4&5`
- lining_mode: `complex`
- stage1_unlocked: `False` (residual gate 10 cm)
- arm: `fable_fresh` / proposer: `Fable-5.1 (fresh per-case agent)`
- model: `claude-fable-5-1-thinking-high`

### Anchor (GT-blind)
```json
{
  "proxy_raw": 0.680653,
  "proxy_scaled": 0.680653,
  "band": "refine",
  "features": {
    "correspondence_f1@15": 0.458619,
    "sam_fill_rate": 0.736776,
    "ring_count_error": 0.0,
    "depth_nan_ratio": 0.201357
  },
  "recentre_residual_max_cm": 3.5,
  "orient_axis_corr": -0.8773629680874642,
  "ring_count": 10,
  "ring_count_error": 0.0,
  "labelmap_source": "only_label.csv",
  "run_dir": "/home/boringtao/Projects/Proxy4Tun/data/bo/unified/5-3-family-proxy/runs/5-3-anchor"
}
```

### Intrinsics (GT-blind)
```json
{
  "orient_axis_corr": -0.8773629680874642,
  "orient_invariant_ok": 1.0,
  "recentre_residual_max_cm": 3.5,
  "denoise_retained_ratio": 0.7488301283104651,
  "depth_nan_ratio": 0.2013572349021065,
  "depth_outlier_ratio": 0.0013759294357778102,
  "det_real_detection_ratio": 0.7,
  "det_fallback_ratio": 0.3,
  "det_n_points": 10.0,
  "sam_fill_rate": 0.7367757097474392,
  "sam_ring_completeness": 1.0,
  "sam_segment_size_cv": 1.013794842616219,
  "sam_ontology_divergence": 0.09703285217926161
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
        "maxLineGap_oblique": 70,
        "hough_threshold_horizontal": 45,
        "maxLineGap_horizontal": 15,
        "pattern_tolerance": 15
      }
    },
    "proxy_scaled": 0.6794128686767513,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.45679878975987986,
      "sam_fill_rate": 0.7367757097474392,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.20254292688203396
    },
    "recentre_residual_max_cm": 3.5,
    "full_pipeline": false,
    "rationale": "Coordinated enhancing+detecting overlay to convert fallback prompt rows into real oblique-joint detections and tighten prompt y alignment. (1) enhancing.curvature_threshold 0.0005 -> 0.0004: midpoint insertion only bridges neighbours with near-identical curvature, so densification stops short of joint discontinuities and the outlier map keeps crisper joint traces. (2) detecting.binary_threshold 127 -> 110: admits the fainter joint pixels visible as dotted traces in the outlier map. (3) detecting.hough_threshold_oblique 50 -> 35 and maxLineGap_oblique 50 -> 70: the joint traces are broken into short dashes; a lower accumulator vote and larger gap let HoughLinesP stitch them into oblique segments within the [5,10] deg window (35 was the value that recovered detection on the sibling 5-1 case). (4) hough_threshold_horizontal 50 -> 45 and maxLineGap_horizontal 10 -> 15: keep horizontal fallback usable but not dominant. (5) pattern_tolerance -> 15 px: K/AB pixel pattern is 245/745 px at 5 mm/px; a moderate tolerance accepts real intersections that are a few px off the design pattern instead of discarding them into the 'assume' path. hough_threshold_vertical is left unchanged because 10 verticals already match 10 rings; denoising mask_r stays at T5 priors (retention and NaN are healthy; \u00a74 warns against per-scan band tuning); sam.* stays at T5 priors (segment_width 1800, K_height 1226.97, angle 9.8). Expected signal: det_real_detection_ratio up from 0.70, correspondence_f1@15 up, sam_fill_rate held or improved, proxy crossing 0.70. Unfolding omitted because stage1_unlocked is false.",
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
        "binary_threshold": 100,
        "hough_threshold_oblique": 28,
        "maxLineGap_oblique": 80,
        "hough_threshold_horizontal": 45,
        "maxLineGap_horizontal": 15,
        "pattern_tolerance": 20
      },
      "sam": {
        "K_height": 1250.0,
        "angle": 9.0
      }
    },
    "proxy_scaled": 0.6863248577494596,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.469449349914798,
      "sam_fill_rate": 0.7367757097474392,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.20254292688203396
    },
    "recentre_residual_max_cm": 3.5,
    "full_pipeline": false,
    "rationale": "Round 1 relaxed Hough moderately (35/70, binary 110) and gained clean K pairs but did not change a single prompt row, so the same knobs are pushed to the evidence-safe edge to reach the edge rings: detecting.hough_threshold_oblique 35 -> 28 and maxLineGap_oblique 70 -> 80 so the short dashed K-edge traces on rings 0/1/9 can accumulate enough votes and be stitched; detecting.binary_threshold 110 -> 100 admits the fainter joint pixels on the partially covered edge rings. Round 1 produced zero spurious obliques at 35/70/110, so there is headroom before f_spurious_lines; the [5,10] deg window and the pattern check remain as guards. detecting.pattern_tolerance 15 -> 20 because the measured joint lattice (250-252 px/unit) differs from the 245 px design by 5-7 px per unit, i.e. 15-20 px over an AB block - a 15 px tolerance can reject genuine K/AB intersections into the 'assume' path, which is exactly the observed fallback pattern. Horizontal Hough stays at the round-1 values (45/15) and enhancing.curvature_threshold stays at 0.0004 so the only detection deltas are the oblique push and the tolerance. Stage 5: sam.K_height 1226.97 -> 1250 mm (=250 px) matches the measured K-edge pair separation (242-256 px, lattice unit 250-252) and shifts the B1/B2 template boundaries onto the detected joint rows; sam.angle 9.8 -> 9.0 deg matches the fitted oblique slopes (8.1-9.5 deg, mean ~8.9) so the K trapezoid edges align with the red/green lines. segment_width stays 1800 (measured ring pitch 362 px = 1810 mm). Expected GT-blind signal: det_fallback_ratio 0.30 -> <=0.20 if any edge ring converts, correspondence_f1@15 up via more green K/B boundaries, sam_fill_rate held or up, proxy moving from 0.68 toward the 0.70 accept band. If prompts are again unchanged, round 3 should treat rings 1 and 9 as K-in-void cases and stop tuning Hough. Unfolding omitted (stage1_unlocked false).",
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
        "binary_threshold": 100,
        "hough_threshold_oblique": 28,
        "maxLineGap_oblique": 80,
        "hough_threshold_horizontal": 32,
        "maxLineGap_horizontal": 25,
        "pattern_tolerance": 20
      },
      "sam": {
        "K_height": 1250.0,
        "angle": 9.0
      }
    },
    "proxy_scaled": 0.6840250857804038,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.4652402281509906,
      "sam_fill_rate": 0.7367757097474392,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.20254292688203396
    },
    "recentre_residual_max_cm": 3.5,
    "full_pipeline": false,
    "rationale": "Final round: keep the round-2 configuration (best proxy 0.686; binary 100, oblique 28/80, pattern_tolerance 20, curvature 0.0004, K_height 1250, angle 9.0) and change ONLY the horizontal Hough pair, so the attribution is clean: detecting.hough_threshold_horizontal 45 -> 32 and detecting.maxLineGap_horizontal 15 -> 25. With 3x3 dilation each joint dot contributes ~9 votes, so 32 votes needs ~4 collinear dots within the fixed 105 px minLineLength, and a 25 px gap bridges the dot spacing seen along the dotted A/B joint rows that currently carry no blue line; 32 stays above the T3 operating point (30) and well above the bound floor (25). Expected GT-blind signal: more horizontal lines that land on the K lattice of the seven real-prompt rings, converting red (unsupported) label boundaries to green and lifting correspondence_f1@15 by roughly +0.02-0.04 (each extra supported row in each central ring is ~1.4% of the 70 boundaries), which is the +0.014 proxy needed to cross the 0.70 accept band; precision of the new lines should be high because rounds 1-2 showed that every horizontal found in a real-prompt ring lies on the measured lattice. Horizontal lines do not drive prompt centres here (ring 1 already had a horizontal crossing its vertical and still fell back to 'assume'), so prompt geometry, ring count (10/10) and fill rate are expected to be unchanged; the downside is bounded to a small precision loss if a few noise lines appear in the joint-poor edge rings. Oblique Hough, binary threshold and pattern_tolerance are frozen at round-2 values because the edge-ring traces lack pixel support to reach the ring-centre verticals (round-2 lesson: treat rings 0/1/9 as K-in-void and stop tuning oblique Hough). sam.K_height 1250 and angle 9.0 are retained as measured (251.8 px, ~8.9 deg); segment_width stays 1800 (measured 1803 mm). Denoising left at T5 priors; unfolding omitted (stage1_unlocked false, residual 3.5 cm).",
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
`/home/boringtao/Projects/Proxy4Tun/data/sc-general/stage3/packets-fable-fresh/5-3/round3_proposal.json`

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
