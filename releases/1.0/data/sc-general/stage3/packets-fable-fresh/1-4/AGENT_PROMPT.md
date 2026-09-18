# Fable 5.1 reflection — subset 1-4 (propose round 3)

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

- subset: `1-4`
- family: `t1&2`
- lining_mode: `staggered`
- stage1_unlocked: `False` (residual gate 10 cm)
- arm: `fable_fresh` / proposer: `Fable-5.1 (fresh per-case agent)`
- model: `claude-fable-5-1-thinking-high`

### Anchor (GT-blind)
```json
{
  "proxy_raw": 0.646304,
  "proxy_scaled": 0.646304,
  "band": "refine",
  "features": {
    "correspondence_f1@15": 0.39509,
    "sam_fill_rate": 0.698703,
    "ring_count_error": 0.0,
    "depth_nan_ratio": 0.14983
  },
  "recentre_residual_max_cm": 1.9,
  "orient_axis_corr": -0.9949699843931424,
  "ring_count": 10,
  "ring_count_error": 0.0,
  "labelmap_source": "results.pkl",
  "run_dir": "/home/boringtao/Projects/Proxy4Tun/data/bo/unified/1-4-family-proxy/runs/1-4-anchor"
}
```

### Intrinsics (GT-blind)
```json
{
  "orient_axis_corr": -0.9949699843931424,
  "orient_invariant_ok": 1.0,
  "recentre_residual_max_cm": 1.9,
  "denoise_retained_ratio": 0.7219901144907218,
  "depth_nan_ratio": 0.14983039763025083,
  "depth_outlier_ratio": 0.002298421906424316,
  "det_real_detection_ratio": 0.7,
  "det_fallback_ratio": 0.3,
  "det_n_points": 10.0,
  "sam_fill_rate": 0.6987025605698844,
  "sam_ring_completeness": 1.0,
  "sam_segment_size_cv": 1.5457569103686017,
  "sam_ontology_divergence": 0.2747016575820716
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
        "inter_radius": 0.08
      },
      "detecting": {
        "binary_threshold": 115,
        "hough_threshold_oblique": 40,
        "maxLineGap_oblique": 60,
        "hough_threshold_horizontal": 60
      }
    },
    "proxy_scaled": 0.6269877031734474,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.3600618784625549,
      "sam_fill_rate": 0.6980153038498764,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.14978859736083178
    },
    "recentre_residual_max_cm": 1.9,
    "full_pipeline": false,
    "rationale": "The proxy is in the refine band (0.646) and the weakest lean feature is correspondence_f1@15 (0.395), i.e. label boundaries do not sit on detected joints. Since orientation, centreline and band selection all validate, the tuning-order rule says the first legitimate target is detection. Raising inter_radius 0.06 -> 0.08 lets enhance_outlier_points bridge sparse joint points into denser, more continuous oblique traces in the outlier map; lowering binary_threshold to 115 keeps those fainter joint pixels after binarisation; lowering hough_threshold_oblique to 40 and raising maxLineGap_oblique to 60 lets HoughLinesP accept the dotted +-5-10 deg joints so more rings receive real positive/negative-slope intersections instead of 'assume' fallbacks. hough_threshold_horizontal is raised to 60 to suppress bolt-row horizontals that add no prompt information. Expected GT-free effect: det_real_detection_ratio 0.7 -> >=0.9, det_fallback_ratio -> <=0.1, correspondence_f1@15 up from 0.395, sam_fill_rate and segment_size_cv improving as K blocks land on true joints. Ring count must stay 10 (vertical threshold unchanged); if spurious oblique lines appear (prompt count inflation, d9) the next round should back off binary_threshold/hough_threshold_oblique toward 127/50.",
    "proposer": "Fable-5.1 (fresh per-case agent)"
  },
  {
    "round": 2,
    "status": "ok",
    "overlay": {
      "enhancing": {
        "inter_radius": 0.06,
        "curvature_threshold": 0.0003
      },
      "detecting": {
        "binary_threshold": 127,
        "hough_threshold_oblique": 60,
        "maxLineGap_oblique": 30,
        "hough_threshold_horizontal": 50
      }
    },
    "proxy_scaled": 0.6499515101453421,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.40583681916991776,
      "sam_fill_rate": 0.6977777801715664,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.15934840791371002
    },
    "recentre_residual_max_cm": 1.9,
    "full_pipeline": false,
    "rationale": "Round 1 is a clean negative result: more oblique lines were not better, consistent with experiences sec.5 (consistency beats count). Round 2 therefore explicitly reverts the relaxation (inter_radius back to 0.06, binary_threshold back to 127, hough_threshold_horizontal back to 50) and moves the oblique detector to the conservative side: hough_threshold_oblique 60 and maxLineGap_oblique 30 so only well-supported +-5-10 deg traces survive, suppressing the bolt-row and margin false positives that produced off-lattice midpoints. Fewer but truer intersections should keep every prompt on the two K-row loci (y~1185 / y~1615 px) and let the 'assume' fill-in reproduce the staggered pattern faithfully. In parallel, curvature_threshold is lowered from the 0.0005 default to 0.0003 so fewer near-joint points are densified as surface, sharpening joint traces without changing the depth map coverage (NaN should stay ~0.15). Expected GT-free effect: correspondence_f1@15 back above the anchor 0.395, det_fallback_ratio <= 0.3 with no off-row midpoints, ring_count_error 0, sam_fill_rate >= 0.70. If f1 does not recover, round 3 should treat detection as saturated and hold the anchor detection while probing the SAM row geometry.",
    "proposer": "Fable-5.1 (fresh per-case agent)"
  },
  {
    "round": 3,
    "status": "ok",
    "overlay": {
      "denoising": {
        "grad_threshold": 0.25
      },
      "enhancing": {
        "inter_radius": 0.06,
        "curvature_threshold": 0.0003
      },
      "detecting": {
        "binary_threshold": 135,
        "hough_threshold_oblique": 75,
        "maxLineGap_oblique": 20,
        "hough_threshold_horizontal": 50
      }
    },
    "proxy_scaled": 0.6455370722299918,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.39739837209628814,
      "sam_fill_rate": 0.6977460026273027,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.15836089378852536
    },
    "recentre_residual_max_cm": 1.9,
    "full_pipeline": false,
    "rationale": "Round 2 shows the conservative direction is the right one, so round 3 keeps its enhancing settings (inter_radius 0.06, curvature_threshold 0.0003) and pushes the detector further toward high-confidence traces: hough_threshold_oblique 75, maxLineGap_oblique 20 and binary_threshold 135 should reject the fragmented bracket-row trace while the strongest true joints (e.g. the 750-1000 px green joint and the 1470-1650 px red joint) remain, and any ring that loses its real line falls back to the K-row lattice rather than to an off-row point. denoising.grad_threshold is raised 0.2 -> 0.25 so the density/gradient test removes more protruding non-lining structure before projection, attacking the same false trace upstream; radial band, z_step and the vertical accumulator are left alone (retention healthy, 10/10 rings). Expected GT-free effect: no prompt outside the y~1185 / y~1615 rows, correspondence_f1@15 > 0.406, sam_fill_rate >= 0.70, ring_count_error 0, NaN staying in the 0.15-0.17 band, retention >= 0.68. Regression signature to watch: retention falling well below 0.7 or NaN rising above 0.2 would mean the gate is now over-tight and round 2 should be preferred.",
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
`/home/boringtao/Projects/Proxy4Tun/data/sc-general/stage3/packets-fable-fresh/1-4/round3_proposal.json`

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
