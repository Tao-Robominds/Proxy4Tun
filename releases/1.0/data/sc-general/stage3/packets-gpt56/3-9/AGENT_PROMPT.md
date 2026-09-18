# GPT-5.6 reflection — subset 3-9 (propose round 3)

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

- subset: `3-9`
- family: `t3`
- lining_mode: `continuous`
- stage1_unlocked: `False` (residual gate 10 cm)
- arm: `gpt56` / proposer: `GPT-5.6 (fresh per-case agent)`
- model: `gpt-5.6-sol-medium`

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
      "denoising": {
        "mask_r_low": 2.8,
        "mask_r_high": 3.1,
        "mask_theta_low": 1.5,
        "mask_theta_high": 18.0
      },
      "enhancing": {
        "curvature_threshold": 0.0005
      },
      "detecting": {
        "binary_threshold": 110,
        "hough_threshold_oblique": 25,
        "hough_threshold_horizontal": 25,
        "maxLineGap_oblique": 50,
        "pattern_tolerance": 15,
        "uniform_k_snap": true
      },
      "sam": {
        "segment_width": 1200,
        "K_height": 900.0,
        "angle": 6.0
      }
    },
    "proxy_scaled": 0.5295084280902446,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.15482503844440915,
      "sam_fill_rate": 0.7352038198639546,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.12772436330245496
    },
    "recentre_residual_max_cm": 2.8,
    "full_pipeline": false,
    "rationale": "A slightly broader denoising mask and lower curvature cutoff retain weak joint evidence. Lower binary and horizontal/oblique Hough thresholds, a larger oblique line gap, and moderate pattern tolerance should reconnect the fragmented K trace; uniform K snapping keeps the ten prompts aligned. K_height=900 satisfies the requested minimum while covering the disturbed joint neighborhood, and segment_width=1200 with a 6-degree angle matches the observed shallow joint trend without changing the already-valid ring count or locked unfolding.",
    "proposer": "GPT-5.6 (fresh per-case agent)"
  },
  {
    "round": 2,
    "status": "ok",
    "overlay": {
      "denoising": {
        "mask_r_low": 2.9,
        "mask_r_high": 3.0,
        "mask_theta_low": 2.0,
        "mask_theta_high": 16.0
      },
      "enhancing": {
        "curvature_threshold": 0.0012
      },
      "detecting": {
        "binary_threshold": 145,
        "hough_threshold_oblique": 45,
        "hough_threshold_horizontal": 45,
        "maxLineGap_oblique": 25,
        "pattern_tolerance": 8,
        "uniform_k_snap": false
      },
      "sam": {
        "segment_width": 1100,
        "K_height": 850.0,
        "angle": 5.0
      }
    },
    "proxy_scaled": 0.5918859635203122,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.30124228863344504,
      "sam_fill_rate": 0.6613098095033184,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.11608858833972369
    },
    "recentre_residual_max_cm": 2.8,
    "full_pipeline": false,
    "rationale": "Hough thresholds of 45 restore selectivity without reaching the extreme upper bound, while binary_threshold=145, maxLineGap_oblique=25, and pattern_tolerance=8 explicitly reverse Round 1's permissive detector. Tighter denoising and a higher curvature threshold suppress weak clutter. Disabling uniform snapping avoids forcing all ring prompts onto a potentially biased inferred line, and segment_width=1100 with the minimum allowed K_height=850 limits propagation from unsupported joint regions.",
    "proposer": "GPT-5.6 (fresh per-case agent)"
  },
  {
    "round": 3,
    "status": "ok",
    "overlay": {
      "denoising": {
        "mask_r_low": 2.85,
        "mask_r_high": 3.05,
        "mask_theta_low": 1.8,
        "mask_theta_high": 17.0
      },
      "enhancing": {
        "curvature_threshold": 0.0009
      },
      "detecting": {
        "binary_threshold": 130,
        "hough_threshold_oblique": 38,
        "hough_threshold_horizontal": 40,
        "maxLineGap_oblique": 35,
        "pattern_tolerance": 11,
        "uniform_k_snap": true
      },
      "sam": {
        "segment_width": 1250,
        "K_height": 950.0,
        "angle": 5.5
      }
    },
    "proxy_scaled": 0.5848249996494934,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.2649148984351411,
      "sam_fill_rate": 0.710415252974959,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.11862563175153537
    },
    "recentre_residual_max_cm": 2.8,
    "full_pipeline": false,
    "rationale": "Binary threshold 130, Hough thresholds 38/40, a 35-pixel oblique gap, and pattern tolerance 11 form a distinct intermediate detector intended to recover genuine fragments without recreating Round 1's spurious connectivity. Moderate denoising and curvature settings preserve visible joint evidence. Uniform K snapping is retained only with these stricter line constraints, while K_height=950 and segment_width=1250 give SAM robust context around the disrupted K band; angle 5.5 follows the shallow observed trend.",
    "proposer": "GPT-5.6 (fresh per-case agent)"
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
`/home/boringtao/Projects/Proxy4Tun/data/sc-general/stage3/packets-gpt56/3-9/round3_proposal.json`

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
