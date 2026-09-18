# GPT-5.6 reflection — subset 4-1 (propose round 3)

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
- `data/sc-general/stage3/selections/`, `selections-fable/`, Fable/deterministic
  refinement trees, or other cases' GPT proposals
- `data/bo/`, `data/anchors/`, `data/baseline`

## State

- subset: `4-1`
- family: `t4&5`
- lining_mode: `complex`
- stage1_unlocked: `False` (residual gate 10 cm)
- arm: `gpt56` / proposer: `GPT-5.6 (fresh per-case agent)`
- model: `gpt-5.6-sol-medium`

### Anchor (GT-blind)
```json
{
  "proxy_raw": 0.551819,
  "proxy_scaled": 0.551819,
  "band": "refine",
  "features": {
    "correspondence_f1@15": 0.225171,
    "sam_fill_rate": 0.748831,
    "ring_count_error": 0.0,
    "depth_nan_ratio": 0.223307
  },
  "recentre_residual_max_cm": 2.4,
  "orient_axis_corr": 0.9398124965718192,
  "ring_count": 10,
  "ring_count_error": 0.0,
  "labelmap_source": "only_label.csv",
  "run_dir": "/home/boringtao/Projects/Proxy4Tun/data/bo/unified/4-1-family-proxy/runs/4-1-anchor"
}
```

### Intrinsics (GT-blind)
```json
{
  "orient_axis_corr": 0.9398124965718192,
  "orient_invariant_ok": 1.0,
  "recentre_residual_max_cm": 2.4,
  "denoise_retained_ratio": 0.7583892868338517,
  "depth_nan_ratio": 0.22330735765617338,
  "depth_outlier_ratio": 0.0010889418251959948,
  "det_real_detection_ratio": 0.4,
  "det_fallback_ratio": 0.6,
  "det_n_points": 10.0,
  "sam_fill_rate": 0.7488305972058229,
  "sam_ring_completeness": 1.0,
  "sam_segment_size_cv": 1.0601700064349866,
  "sam_ontology_divergence": 0.10154601537508416
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
        "binary_threshold": 115,
        "hough_threshold_oblique": 32,
        "hough_threshold_horizontal": 30,
        "maxLineGap_oblique": 68,
        "maxLineGap_horizontal": 24,
        "pattern_tolerance": 12
      },
      "sam": {
        "segment_width": 1650
      }
    },
    "proxy_scaled": 0.5562523287915903,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.2327550173070701,
      "sam_fill_rate": 0.7498783735648481,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.22328257687193515
    },
    "recentre_residual_max_cm": 2.4,
    "full_pipeline": false,
    "rationale": "Lower horizontal and oblique Hough thresholds admit weaker visible joints, larger line gaps bridge fragmented evidence, and a moderate binary threshold plus tolerance keeps the change bounded. A slightly narrower SAM segment width then limits propagation across unsupported neighboring boundaries while preserving the established ten-ring structure.",
    "proposer": "GPT-5.6 (fresh per-case agent)"
  },
  {
    "round": 2,
    "status": "ok",
    "overlay": {
      "detecting": {
        "binary_threshold": 125,
        "hough_threshold_horizontal": 40,
        "maxLineGap_horizontal": 18,
        "pattern_tolerance": 9
      },
      "sam": {
        "segment_width": 1525,
        "K_height": 1100.0,
        "angle": 8.0
      }
    },
    "proxy_scaled": 0.6595193406036985,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.4230073170023036,
      "sam_fill_rate": 0.7473603992871702,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.22328257687193515
    },
    "recentre_residual_max_cm": 2.4,
    "full_pipeline": false,
    "rationale": "A reduced segment width and K height localize each prompt's influence, while a lower angle better matches the mostly shallow joint slopes visible in the diagnostics. Moderate horizontal sensitivity supplies additional evidence without the broad recall push of round 1.",
    "proposer": "GPT-5.6 (fresh per-case agent)"
  },
  {
    "round": 3,
    "status": "ok",
    "overlay": {
      "denoising": {
        "mask_r_low": 3.55,
        "mask_r_high": 4.0
      },
      "enhancing": {
        "curvature_threshold": 0.0005
      },
      "detecting": {
        "binary_threshold": 135,
        "hough_threshold_oblique": 42,
        "hough_threshold_horizontal": 45,
        "hough_threshold_vertical": 3000,
        "maxLineGap_oblique": 75,
        "maxLineGap_horizontal": 14,
        "pattern_tolerance": 16
      },
      "sam": {
        "segment_width": 1950,
        "K_height": 1400.0,
        "angle": 11.0
      }
    },
    "proxy_scaled": 0.478374074190554,
    "band": "reject",
    "features": {
      "correspondence_f1@15": 0.08713719742483554,
      "sam_fill_rate": 0.7547204674727389,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.22149171468872242
    },
    "recentre_residual_max_cm": 2.4,
    "full_pipeline": false,
    "rationale": "A broad bounded radial mask protects valid surfaces, a low curvature threshold retains subtle joint responses, and moderate Hough thresholds with long oblique bridging favor coherent evidence over isolated fragments. Wider SAM spacing and a steeper angle provide a deliberately different, conservative propagation hypothesis for the visible sloped joints.",
    "proposer": "GPT-5.6 (fresh per-case agent)"
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
`/home/boringtao/Projects/Proxy4Tun/data/sc-general/stage3/packets-gpt56/4-1/round3_proposal.json`

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
