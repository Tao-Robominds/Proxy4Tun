# Fable 5.1 reflection — subset 1-2 (propose round 3)

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

- subset: `1-2`
- family: `t1&2`
- lining_mode: `staggered`
- stage1_unlocked: `False` (residual gate 10 cm)
- arm: `fable_fresh` / proposer: `Fable-5.1 (fresh per-case agent)`
- model: `claude-fable-5-1-thinking-high`

### Anchor (GT-blind)
```json
{
  "proxy_raw": 0.647823,
  "proxy_scaled": 0.647823,
  "band": "refine",
  "features": {
    "correspondence_f1@15": 0.367509,
    "sam_fill_rate": 0.722929,
    "ring_count_error": 0.0,
    "depth_nan_ratio": 0.101505
  },
  "recentre_residual_max_cm": 3.5,
  "orient_axis_corr": 0.9999355849000731,
  "ring_count": 10,
  "ring_count_error": 0.0,
  "labelmap_source": "results.pkl",
  "run_dir": "/home/boringtao/Projects/Proxy4Tun/data/bo/unified/1-2-family-proxy/runs/1-2-anchor"
}
```

### Intrinsics (GT-blind)
```json
{
  "orient_axis_corr": 0.9999355849000731,
  "orient_invariant_ok": 1.0,
  "recentre_residual_max_cm": 3.5,
  "denoise_retained_ratio": 0.7585160833227094,
  "depth_nan_ratio": 0.10150520930740327,
  "depth_outlier_ratio": 0.005202745247880946,
  "det_real_detection_ratio": 0.8,
  "det_fallback_ratio": 0.2,
  "det_n_points": 10.0,
  "sam_fill_rate": 0.7229286883173068,
  "sam_ring_completeness": 0.8888888888888888,
  "sam_segment_size_cv": 1.3381961231118245,
  "sam_ontology_divergence": 0.2397912045632986
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
        "binary_threshold": 110,
        "hough_threshold_oblique": 42,
        "maxLineGap_oblique": 60,
        "hough_threshold_horizontal": 60,
        "hough_threshold_vertical": 560
      }
    },
    "proxy_scaled": 0.6065693631761999,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.2904389236450993,
      "sam_fill_rate": 0.7260798324684363,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.10149715575305655
    },
    "recentre_residual_max_cm": 3.5,
    "full_pipeline": false,
    "rationale": "The proxy's dominant deficit is correspondence_f1@15 (0.37); fill rate, NaN and ring count are already in healthy range. F1 is limited by recall of joint lines on the left half of the map, so the coordinated move is: (1) enhancing.inter_radius 0.06 -> 0.075 so sparse joint points on the far rings are bridged into continuous lines in the outlier map; (2) detecting.binary_threshold 127 -> 110 so those fainter interpolated joint pixels survive binarisation; (3) detecting.hough_threshold_oblique 50 -> 42 and maxLineGap_oblique 40 -> 60 so fragmented obliques on those rings are accepted, replacing the 'assume' and horizontal fallbacks with real K-edge detections; (4) detecting.hough_threshold_horizontal 50 -> 60 to suppress the void-edge horizontals that currently add spurious intersections without explaining any label boundary; (5) detecting.hough_threshold_vertical raised to 560 as a guard, because extra binarised joint mass from (1)-(3) could otherwise push the vertical accumulator above 10 lines - the 10/10 vertical count is the asset most worth protecting. Denoising is left untouched (band selection healthy, retention 0.76, per experiences \u00a74 keep at tunnel priors) and unfolding is omitted because stage1_unlocked is false. Expected proxy signal: correspondence_f1@15 up via more supported boundaries and more explained lines, det_real_detection_ratio 0.8 -> 1.0, sam_fill_rate roughly unchanged or slightly up as prompts move from assumed to detected positions; ring_count_error must stay 0.",
    "proposer": "Fable-5.1 (fresh per-case agent)"
  },
  {
    "round": 2,
    "status": "ok",
    "overlay": {
      "enhancing": {
        "inter_radius": 0.075
      },
      "detecting": {
        "binary_threshold": 130,
        "hough_threshold_oblique": 42,
        "maxLineGap_oblique": 30,
        "hough_threshold_horizontal": 60,
        "hough_threshold_vertical": 560
      }
    },
    "proxy_scaled": 0.6531394930555477,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.377121973443556,
      "sam_fill_rate": 0.7231601518986284,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.10149715575305655
    },
    "recentre_residual_max_cm": 3.5,
    "full_pipeline": false,
    "rationale": "Disentangle the two effects of round 1: keep the recall-side changes that rescued ring 2 (enhancing.inter_radius 0.075, hough_threshold_oblique 42) and reverse the precision-side changes that created the spurious centre obliques. maxLineGap_oblique goes from 60 to 30 (below the anchor's 40 and below the ~50-60 px bolt-hole pitch) so dashed feature rows can no longer be fused into lines while genuine, continuous K joints (now densified by the larger inter_radius) still pass; binary_threshold goes back to 130 (slightly above the 127 default) so shallow intra-block features are cut before Hough. hough_threshold_horizontal stays 60 and hough_threshold_vertical stays 560 - both behaved (no spurious horizontal prompts, 10/10 verticals). Denoising untouched; SAM untouched; unfolding omitted (stage1 locked). Expected: the number of unexplained (orange) joint lines drops back to or below anchor level, ring 6 returns to the 1605 row (det_y_std back to ~210 -> two-row pattern, midpoint ratio stays high), ring 2 keeps its real detection, so correspondence_f1@15 should exceed the anchor's 0.368 rather than merely recover it; ring_count_error must stay 0.",
    "proposer": "Fable-5.1 (fresh per-case agent)"
  },
  {
    "round": 3,
    "status": "ok",
    "overlay": {
      "enhancing": {
        "inter_radius": 0.08
      },
      "detecting": {
        "binary_threshold": 120,
        "hough_threshold_oblique": 40,
        "maxLineGap_oblique": 30,
        "hough_threshold_horizontal": 40,
        "hough_threshold_vertical": 560
      }
    },
    "proxy_scaled": 0.6413435499436362,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.35563228145237347,
      "sam_fill_rate": 0.7229589928042518,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.10149670833337061
    },
    "recentre_residual_max_cm": 3.5,
    "full_pipeline": false,
    "rationale": "Final round: selection keeps the best of rounds 1-3, so the value of this round lies in a decisive recall move, not another small precision hedge. Coordinated overlay: (1) enhancing.inter_radius 0.075 -> 0.08 (bound) so far-ring joint traces are interpolated into denser dotted lines before projection - it cannot bridge bolt holes (pitch 0.25-0.30 m >> 0.08 m). (2) detecting.hough_threshold_oblique 42 -> 40 (bound) so the second K edge on rings 3-4 and the ring-1 K edges, which currently fall just under the accumulator, are accepted; minLineLength 100 and maxLineGap_oblique 30 (kept) guarantee that only continuous >=100 px joints qualify. (3) detecting.hough_threshold_horizontal 60 -> 40 (bound): this is the main lever - the B/A and A/A joints are 5 of the 7 boundaries per ring and are unsupported on half the rings; the horizontal path's maxLineGap is fixed at 10 px, so lowering votes admits sparse straight joints but cannot fuse dashed bolt rows, and the void-edge horizontals are already present at 60 so precision on that path cannot get materially worse. (4) detecting.binary_threshold 130 -> 120: partially reopen the depth cut so the fainter far-ring joint pixels (the centreline residual of up to 3.5 cm shifts their grey level) survive binarisation; the round-1 bolt-hole obliques needed maxLineGap 60 to form and are blocked at 30, and the vertical guard already held 10/10 at binary 110. (5) detecting.hough_threshold_vertical stays 560 (proven at both 110 and 130 binarisation; the 2750 px ring joints vote far above it, so a 10/10 count is preserved). Expected proxy signal: correspondence_f1@15 up through more explained horizontals and K edges on rings 1-4 and 10 (recall), with the oblique set remaining K-edge-only (precision held); det_real_detection_ratio 0.9 -> 1.0 if ring 1 gets a real or horizontal-fallback prompt on the 1605 row; sam_fill_rate ~0.72 unchanged or slightly up as ring 1's K block moves onto its row; depth_nan_ratio unchanged (stages 1-3 untouched); ring_count_error must stay 0.",
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
`/home/boringtao/Projects/Proxy4Tun/data/sc-general/stage3/packets-fable-fresh/1-2/round3_proposal.json`

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
