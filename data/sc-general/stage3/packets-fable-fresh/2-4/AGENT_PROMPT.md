# Fable 5.1 reflection — subset 2-4 (propose round 3)

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

- subset: `2-4`
- family: `t1&2`
- lining_mode: `staggered`
- stage1_unlocked: `False` (residual gate 10 cm)
- arm: `fable_fresh` / proposer: `Fable-5.1 (fresh per-case agent)`
- model: `claude-fable-5-1-thinking-high`

### Anchor (GT-blind)
```json
{
  "proxy_raw": 0.676342,
  "proxy_scaled": 0.676342,
  "band": "refine",
  "features": {
    "correspondence_f1@15": 0.411668,
    "sam_fill_rate": 0.745003,
    "ring_count_error": 0.0,
    "depth_nan_ratio": 0.109191
  },
  "recentre_residual_max_cm": 1.7,
  "orient_axis_corr": -0.9997455372446109,
  "ring_count": 10,
  "ring_count_error": 0.0,
  "labelmap_source": "results.pkl",
  "run_dir": "/home/boringtao/Projects/Proxy4Tun/data/bo/unified/2-4-family-proxy/runs/2-4-anchor"
}
```

### Intrinsics (GT-blind)
```json
{
  "orient_axis_corr": -0.9997455372446109,
  "orient_invariant_ok": 1.0,
  "recentre_residual_max_cm": 1.7,
  "denoise_retained_ratio": 0.7693688879665898,
  "depth_nan_ratio": 0.10919078606422467,
  "depth_outlier_ratio": 0.0029708795925650843,
  "det_real_detection_ratio": 0.9,
  "det_fallback_ratio": 0.1,
  "det_n_points": 10.0,
  "sam_fill_rate": 0.7450027236647557,
  "sam_ring_completeness": 1.0,
  "sam_segment_size_cv": 1.3219664851130428,
  "sam_ontology_divergence": 0.22643770209071767
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
        "binary_threshold": 115,
        "hough_threshold_oblique": 45,
        "hough_threshold_horizontal": 40,
        "maxLineGap_oblique": 60
      }
    },
    "proxy_scaled": 0.6806087731498789,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.4193699810634234,
      "sam_fill_rate": 0.7452081658063344,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.10917412528728879
    },
    "recentre_residual_max_cm": 1.7,
    "full_pipeline": false,
    "rationale": "The proxy is in the refine band (0.676) and its only depressed lean feature that a bounded, GT-free change can move is correspondence_f1@15; ring count, residual, orientation and NaN are already at healthy values so nothing upstream should be touched. Make the joint evidence denser and the Hough stage slightly more permissive in a coordinated way: raise enhancing.inter_radius 0.06 -> 0.07 to interpolate more joint points in the sparse left columns; lower detecting.binary_threshold 127 -> 115 so more of the faint joint pixels survive binarisation; lower hough_threshold_horizontal 50 -> 40 so the visible dotted longitudinal joints become horizontal segments that support the many currently red B/A boundaries (precision and recall both rise); lower hough_threshold_oblique 50 -> 45 and raise maxLineGap_oblique 40 -> 60 so the dotted oblique K joints in rings 0, 1 and 9 join into full segments and the assumed column becomes a real detection. Spurious-line risk is bounded by the strict [5,10] deg angle filter, merge_close_points and the K/AB distance-pattern gate, and hough_threshold_vertical is deliberately left alone so the healthy 10-for-10 vertical count is not disturbed by the denser binary map. Denoising is left empty (retention and NaN healthy; mask_r stays at priors) and sam.y_bounds is left unchanged because the label map already spans the full depth map and there is no evidence linking fill rate to the SAM window. Expected signal: correspondence_f1@15 up, det_fallback_ratio 0.1 -> 0.0, ring_count_error stays 0, sam_fill_rate flat or slightly up; if ring count changes or oblique lines become noisy in round 2, back off binary_threshold first.",
    "proposer": "Fable-5.1 (fresh per-case agent)"
  },
  {
    "round": 2,
    "status": "ok",
    "overlay": {
      "denoising": {
        "mask_r_high": 2.85
      },
      "enhancing": {
        "inter_radius": 0.07
      },
      "detecting": {
        "hough_threshold_oblique": 40,
        "hough_threshold_horizontal": 40,
        "maxLineGap_oblique": 80
      }
    },
    "proxy_scaled": 0.6867280973877014,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.4286861174300738,
      "sam_fill_rate": 0.7489227257399289,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.10906758400319887
    },
    "recentre_residual_max_cm": 1.7,
    "full_pipeline": false,
    "rationale": "Widen only the upper radial gate: denoising.mask_r_high 2.79 -> 2.85 (+6 cm of headroom; prior outer 2.80, bound 2.90). This retains joint/recess points that are 15-75 mm deeper than the lining so enhance_outlier_points can flag them (depth_threshold_high 0.015 becomes reachable), which should thicken the joint lines in the binary map for both oblique (K) and horizontal (B/A) joints and sharpen joint contrast in the SAM depth input so mask edges land on the joints - the direct route to a higher correspondence_f1@15. mask_r_low stays 2.32 (rails/floor side unchanged). Keep the detection stage permissive so the extra joint evidence can be used: hough_threshold_oblique 40 (bound), maxLineGap_oblique 80 (bound) to bridge the dotted K joints in rings 0/1/9, hough_threshold_horizontal 40; keep inter_radius 0.07. Drop binary_threshold (dead knob on this scan, shown above). Ring count is pinned by the synthetic verticals, so the main risk is retaining out-of-band noise behind the lining (depth_outlier_ratio and NaN may shift slightly) and, if the widened band lets grout holes/bolt pockets act as extra 'joints', spurious oblique lines - the [6,9] deg angle filter and the K-row pattern gate limit that. Expected: correspondence_f1@15 up clearly (>0.45), det_fallback_ratio 0.1 -> 0.0 if ring 1 gets its oblique pair, denoise_retained_ratio slightly up, NaN flat or down, ring_count_error 0. If round 2 shows depth_outlier_ratio ballooning or the proxy dropping, round 3 should pull mask_r_high back to ~2.81 rather than revisit Hough.",
    "proposer": "Fable-5.1 (fresh per-case agent)"
  },
  {
    "round": 3,
    "status": "ok",
    "overlay": {
      "denoising": {
        "mask_r_high": 2.9,
        "grad_threshold": 0.25
      },
      "enhancing": {
        "inter_radius": 0.07
      },
      "detecting": {
        "hough_threshold_oblique": 40,
        "hough_threshold_horizontal": 40,
        "maxLineGap_oblique": 80
      }
    },
    "proxy_scaled": 0.696335945731631,
    "band": "refine",
    "features": {
      "correspondence_f1@15": 0.4464884336967219,
      "sam_fill_rate": 0.7488174107027055,
      "ring_count_error": 0.0,
      "depth_nan_ratio": 0.10950353528960818
    },
    "recentre_residual_max_cm": 1.7,
    "full_pipeline": false,
    "rationale": "Extend the only lever that produced a real gain and add the one untouched stage-2 lever that targets the sparse columns directly. (1) denoising.mask_r_high 2.85 -> 2.90 (bound): another 5 cm of depth headroom above the lining surface (r ~2.775), so recess points 7-12 cm deep that were still clipped can reach enhance_outlier_points and thicken the joint lines in the outlier map and the SAM depth input; round 2 showed this direction improves both correspondence_f1@15 and sam_fill_rate with no NaN or residual cost. (2) denoising.grad_threshold 0.2 -> 0.25 (bound): relax the density-difference test so cells whose density drops relative to their neighbours are less readily removed - in the left third of the map the recess points are locally sparser than the already-sparse lining and are the first casualties of this filter; keeping them is what rings 0, 1 and 9 need for their oblique pairs and what the horizontal joints need to become continuous segments. z_step is left at 0.001 so the bin geometry is unchanged and the effect is attributable to the threshold alone. mask_r_low stays 2.32 (rails/floor side untouched, no under-gate risk from below). (3) Detection stays at the round-2 permissive settings so the extra joint evidence can be consumed: hough_threshold_oblique 40, maxLineGap_oblique 80, hough_threshold_horizontal 40; inter_radius stays 0.07; binary_threshold and hough_threshold_vertical are not touched (dead knobs on this scan); sam.y_bounds is not touched (map height ~3100 px, the lower bound of 3600 is outside the map). Risks: under-gating behind the lining (grout/bolt pockets, cable brackets) could raise depth_outlier_ratio and add spurious oblique/horizontal candidates; the [5,10] deg angle filter, merge_close_points and the K/AB distance-pattern gate bound the prompt-level impact, and ring count is pinned by the synthetic verticals. Expected: correspondence_f1@15 > 0.44, sam_fill_rate >= 0.749, det_fallback_ratio 0.1 -> 0.0 if ring 1 gets an oblique line, denoise_retained_ratio slightly up, NaN flat, ring_count_error 0. If the proxy falls below round 2, the selector should keep round 2 (mask_r_high 2.85) - grad_threshold would then be the suspect, not the radial gate.",
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
`/home/boringtao/Projects/Proxy4Tun/data/sc-general/stage3/packets-fable-fresh/2-4/round3_proposal.json`

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
