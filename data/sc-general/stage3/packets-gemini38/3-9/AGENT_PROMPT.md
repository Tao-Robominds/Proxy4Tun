# Gemini 3.8 reflection — subset 3-9 (propose round 3)

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
- `data/sc-general/stage3/selections/`, `selections-fable/`, `selections-gpt56/`,
  Fable/GPT/deterministic refinement trees, or other cases' Gemini proposals
- `data/bo/`, `data/anchors/`, `data/baseline`

## State

- subset: `3-9`
- family: `t3`
- lining_mode: `continuous`
- stage1_unlocked: `False` (residual gate 10 cm)
- arm: `gemini38` / proposer: `Gemini-3.8 (fresh per-case agent)`
- model: `inherit`

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
        "mask_r_low": 2.85,
        "mask_r_high": 3.0,
        "mask_theta_low": 1.55,
        "mask_theta_high": 17.15
      },
      "enhancing": {
        "curvature_threshold": 0.0008
      },
      "detecting": {
        "binary_threshold": 127,
        "hough_threshold_oblique": 30,
        "hough_threshold_horizontal": 30,
        "hough_threshold_vertical": 1500,
        "maxLineGap_oblique": 30,
        "pattern_tolerance": 12,
        "uniform_k_snap": true
      },
      "sam": {
        "segment_width": 1200,
        "K_height": 820.0,
        "angle": 6.12
      }
    },
    "proxy_scaled": 0.6513762985056586,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.3805906508073969,
      "sam_fill_rate": 0.7285836050379835,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.126232335049755
    },
    "recentre_residual_max_cm": 2.8,
    "full_pipeline": false,
    "rationale": "Round 1 centres the overlay on T3 SAM priors with a mid-low K_height (820) inside [700,1000] to hug the observed central joint band and avoid empty-crop K_height near the upper bound. Pair with notebook-like Hough (oblique/horizontal 30, vertical 1500) and moderate pattern_tolerance so continuous K-row snap stays on the green/red tracks. Mild curvature and T3-ish r/theta denoise preserve joint contrast without reopening stage-1.",
    "proposer": "Gemini-3.8 (fresh per-case agent)"
  },
  {
    "round": 2,
    "status": "ok",
    "overlay": {
      "denoising": {
        "mask_r_low": 2.8,
        "mask_r_high": 3.05,
        "mask_theta_low": 1.3,
        "mask_theta_high": 17.5
      },
      "enhancing": {
        "curvature_threshold": 0.0005
      },
      "detecting": {
        "binary_threshold": 115,
        "hough_threshold_oblique": 24,
        "hough_threshold_horizontal": 24,
        "hough_threshold_vertical": 1200,
        "maxLineGap_oblique": 40,
        "pattern_tolerance": 8,
        "uniform_k_snap": true
      },
      "sam": {
        "segment_width": 1100,
        "K_height": 820.0,
        "angle": 5.2
      }
    },
    "proxy_scaled": 0.6215620364936054,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.320160568042767,
      "sam_fill_rate": 0.7429577464788732,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.12957808151453096
    },
    "recentre_residual_max_cm": 2.8,
    "full_pipeline": false,
    "rationale": "Distinct from round 1: detection-led recovery of the continuous green/red tracks (binary 115, oblique/horizontal 24, vertical 1200, maxLineGap 40, pattern_tolerance 8) plus a mid-band SAM crop (K_height=820, segment_width=1100, angle=5.2). K_height was raised from 740 after an empty-crop OpenCV resize failure.",
    "proposer": "Gemini-3.8 (fresh per-case agent)"
  },
  {
    "round": 3,
    "status": "ok",
    "overlay": {
      "denoising": {
        "mask_r_low": 2.9,
        "mask_r_high": 3.1,
        "mask_theta_low": 1.8,
        "mask_theta_high": 16.5
      },
      "enhancing": {
        "curvature_threshold": 0.0012
      },
      "detecting": {
        "binary_threshold": 140,
        "hough_threshold_oblique": 40,
        "hough_threshold_horizontal": 40,
        "hough_threshold_vertical": 1800,
        "maxLineGap_oblique": 20,
        "pattern_tolerance": 16,
        "uniform_k_snap": true
      },
      "sam": {
        "segment_width": 1350,
        "K_height": 880.0,
        "angle": 7.8
      }
    },
    "proxy_scaled": 0.5784979305747964,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.25750981388134764,
      "sam_fill_rate": 0.6960659373396667,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.11086420590446155
    },
    "recentre_residual_max_cm": 2.8,
    "full_pipeline": false,
    "rationale": "Third distinct axis: wider segments (1350) and higher taper (7.8\u00b0) to absorb inter-strip vertical offsets visible in the SC overlay, with K_height=880 (still below 1000 empty-crop risk) so the template covers the dual green/red joint tracks without ballooning into empty crop. Detection is stricter (binary 140, oblique/horizontal 40, vertical 1800, pattern_tolerance 16) and curvature higher (0.0012) to sharpen the central seam used for correspondence@15.",
    "proposer": "Gemini-3.8 (fresh per-case agent)"
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
`/home/boringtao/Projects/Proxy4Tun/data/sc-general/stage3/packets-gemini38/3-9/round3_proposal.json`

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
