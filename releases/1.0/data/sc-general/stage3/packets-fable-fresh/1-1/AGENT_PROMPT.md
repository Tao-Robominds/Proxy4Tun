# Fable 5.1 reflection — subset 1-1 (propose round 3)

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

- subset: `1-1`
- family: `t1&2`
- lining_mode: `staggered`
- stage1_unlocked: `False` (residual gate 10 cm)
- arm: `fable_fresh` / proposer: `Fable-5.1 (fresh per-case agent)`
- model: `claude-fable-5-1-thinking-high`

### Anchor (GT-blind)
```json
{
  "proxy_raw": 0.606657,
  "proxy_scaled": 0.606657,
  "band": "refine",
  "features": {
    "correspondence_f1@15": 0.29438,
    "sam_fill_rate": 0.722949,
    "ring_count_error": 0.0,
    "depth_nan_ratio": 0.107366
  },
  "recentre_residual_max_cm": 2.8,
  "orient_axis_corr": -0.999934241125118,
  "ring_count": 10,
  "ring_count_error": 0.0,
  "labelmap_source": "results.pkl",
  "run_dir": "/home/boringtao/Projects/Proxy4Tun/data/anchors/1-1"
}
```

### Intrinsics (GT-blind)
```json
{
  "orient_axis_corr": -0.999934241125118,
  "orient_invariant_ok": 1.0,
  "recentre_residual_max_cm": 2.8,
  "denoise_retained_ratio": 0.7531270323506135,
  "depth_nan_ratio": 0.10736613189903915,
  "depth_outlier_ratio": 0.0032266563656320134,
  "det_real_detection_ratio": 0.7,
  "det_fallback_ratio": 0.3,
  "det_n_points": 10.0,
  "sam_fill_rate": 0.7229494457484911,
  "sam_ring_completeness": 0.8888888888888888,
  "sam_segment_size_cv": 1.2876045298188923,
  "sam_ontology_divergence": 0.21232044530496946
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
        "curvature_threshold": 0.0004,
        "inter_radius": 0.07
      },
      "detecting": {
        "binary_threshold": 115,
        "hough_threshold_oblique": 42,
        "hough_threshold_horizontal": 45,
        "maxLineGap_oblique": 60
      }
    },
    "proxy_scaled": 0.5542801150998174,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.20021556044461883,
      "sam_fill_rate": 0.7240266239875198,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.11324789184151514
    },
    "recentre_residual_max_cm": 2.8,
    "full_pipeline": false,
    "rationale": "Keep denoising at tunnel priors (retention and NaN are healthy; experiences \u00a74 says geometry knobs are load-bearing for transfer, not per-scan tuning). Slightly lower enhancing.curvature_threshold (0.0005 -> 0.0004) so more boundary points qualify as joint candidates, and raise enhancing.inter_radius (0.06 -> 0.07) so joint interpolation bridges the sparse left-half seams into continuous lines. In detection, lower binary_threshold (127 -> 115) so faint enhanced-joint pixels survive binarisation, lower hough_threshold_oblique (50 -> 42) and hough_threshold_horizontal (50 -> 45) to accept shorter/weaker seam evidence, and raise maxLineGap_oblique (40 -> 60) to link fragmented oblique seams. hough_threshold_vertical is left unchanged because vertical count already equals ring count (10/10) and altering it risks the 11-for-10 truncation failure. sam is left unchanged: fill_rate 0.72 and ring_completeness 0.89 are coherence symptoms of the missing prompts, and SAM geometry should only be tuned after detection is real rather than fallback. Expected GT-free signal: det_fallback_ratio 0.3 -> ~0.0-0.1, correspondence_f1@15 up from 0.294, sam_fill_rate up, ring_count_error stays 0. Risk: more spurious lines on the already-dense right half; the moderate deltas (not bound extremes) hedge this, and a rise in det_n_points beyond ~10-12 in the next round would signal f_spurious_lines and call for backing off binary_threshold/oblique threshold.",
    "proposer": "Fable-5.1 (fresh per-case agent)"
  },
  {
    "round": 2,
    "status": "ok",
    "overlay": {
      "denoising": {
        "mask_r_high": 2.86
      }
    },
    "proxy_scaled": 0.6448592477820705,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.36375535489027944,
      "sam_fill_rate": 0.7241578353955479,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.10751362939291995
    },
    "recentre_residual_max_cm": 2.8,
    "full_pipeline": false,
    "rationale": "Single-stage, attributable move: raise denoising.mask_r_high 2.78 -> 2.86 (inside [2.7, 2.9]; covers r_lining 2.75 + 0.028 residual + a few cm of joint recess, still below the 2.9 bound to limit far-wall noise). Points beyond the lining surface are mostly multipath/noise, so the risk of background leakage is low and would show up as a rise in depth_outlier_ratio and det_n_points, which I will watch. mask_r_low is left at 2.33 (experiences \u00a74: inner gate is load-bearing for transfer; the inner clutter is not the failure here). Enhancing and detecting overlays from round 1 are dropped so they revert to anchor values: the round-1 detection relaxation lowered F1 by shifting prompt y-positions without adding real detections, and reverting isolates the effect of the gate change. SAM unchanged (fill_rate/ring_completeness are downstream symptoms). Expected GT-free signal: denoise_retained_ratio up from 0.753, depth_nan_ratio down from 0.107, outlier map gains joint pixels on the left half, det_fallback_ratio 0.3 -> lower, correspondence_f1@15 back above 0.294, ring_count_error stays 0. If retained ratio rises but F1 does not, round 3 will combine the wider gate with detection/enhancement tuning now that the upstream precondition is met.",
    "proposer": "Fable-5.1 (fresh per-case agent)"
  },
  {
    "round": 3,
    "status": "ok",
    "overlay": {
      "denoising": {
        "mask_r_high": 2.86
      },
      "detecting": {
        "binary_threshold": 135,
        "hough_threshold_oblique": 60,
        "maxLineGap_oblique": 30
      }
    },
    "proxy_scaled": 0.6411193883992303,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.3545843550515629,
      "sam_fill_rate": 0.7288456611550961,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.10751362939291995
    },
    "recentre_residual_max_cm": 2.8,
    "full_pipeline": false,
    "rationale": "Coordinated two-stage overlay that keeps the proven round-2 gate and tightens detection in the opposite direction to round 1. (1) denoising.mask_r_high stays 2.86 (round-2 value; the only move so far with a positive attributable effect). (2) detecting.binary_threshold 127 -> 135 so faint speckle in the dense band drops out of the binarised outlier map while the strong joint pixels (which survive at 127 with margin) are retained; not pushed to the 160 bound because the left half is already faint. (3) detecting.hough_threshold_oblique 50 -> 60 so an oblique line needs more supporting pixels (a real seam spanning a segment width ~240 px easily clears this; a 60-100 px speckle chain does not). (4) detecting.maxLineGap_oblique 40 -> 30 so unrelated fragments are no longer bridged into one long false seam. Enhancing is left at anchor values: the round-1 enhancing changes are confounded with the detection relaxation and cannot be credited, and re-adding them would re-introduce the suspect. hough_threshold_horizontal and hough_threshold_vertical unchanged (horizontal is fallback-only; vertical count is already 10/10). SAM y_bounds unchanged: fill_rate/ring_completeness are downstream of prompt placement. All values inside bounds (binary [100,160], oblique [40,90], maxLineGap [20,80], mask_r_high [2.7,2.9]); stage1_unlocked is false so no unfolding keys. Expected GT-free signal: fewer orange (unexplained) oblique lines on the overlay, prompt y-positions clustering onto the K/AB rows, correspondence_f1@15 >= 0.364, det_n_points stays 10, ring_count_error 0, sam_fill_rate not falling. Risk: if det_fallback_ratio rises above 0.3 (real oblique detections lost), the tightening was too strong and the round-2 overlay (mask_r_high 2.86 only) remains the fallback selection.",
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
`/home/boringtao/Projects/Proxy4Tun/data/sc-general/stage3/packets-fable-fresh/1-1/round3_proposal.json`

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
