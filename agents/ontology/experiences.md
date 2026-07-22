# Experiences: how to observe and analyse pipeline artifacts

Distilled lessons from the experimental campaigns in this repository. This file
complements `sam4tun_ontology.yaml` (failure modes, diagnostic rules,
remediation actions) with **empirical evidence**: what the artifacts actually
looked like when things went wrong, which observations were misleading, and
what the measured effect of each fix was. A reflective agent should treat these
as calibrated priors when reading a run's artifacts.

Sources: `reports/orientation-sensitivity.md`,
`reports/critical-parameters-experiment.md`,
`reports/t3-3-1-1-corrected-vs-literal.md`, `reports/t45-5-1-depth-improvement.md`,
`reports/t45-4-1-swap-ab.md`, `reports/unified.md`, `bo-unified/report.md`,
`bo-unified/ablation.md`.

---

## 1. The single most important lesson: a beautiful depth map can score near zero

A circumferentially **mirrored** unroll is visually indistinguishable from a
correct one. On `3-1-1` a clean-looking depth map with excellent detected lines
and SAM masks scored mIoU **0.121** because every block landed at its mirror
position against the orientation-specific templates; the same centreline draw
with theta mirrored back scored **0.705** (`t3-3-1-1-corrected-vs-literal.md`).

**How to detect it (do not trust the depth-map image alone):**

- Orientation errors are **binary, not gradual**. mIoU either collapses to
  0.1–0.4 (Hough geometry mismatch) or the segmentation looks perfect but the
  **confusion matrix is a permutation matrix** — asymmetric classes swap with
  their mirror partners (pred B2 ↔ gt B1, pred A3 ↔ gt A1, while symmetric K
  and A2 stay correct). A permutation-shaped confusion matrix is an
  orientation bug, not a segmentation bug.
- Without labels, the proxy analogue is `sam_ontology_divergence` and the
  phase-coherence check: the phase alarm recovered the `1-5-anchor` label
  rotation that intrinsic features alone missed (`bo-unified/ablation.md`).
- The stage-1 invariant `corr(h, ring)` must match `h_ring_sign` with
  |corr| > 0.5; healthy runs show |corr| ≈ 0.98 on all five tunnels.
- `segment_order` is **coupled to theta handedness**. Any orientation change
  must be paired with a `segment_order` review; the two are only valid
  together (3-1-1 fix: reversed order → 0.335 → 0.850).

## 2. Seeds pin reproducibility, not correctness

`random_seed` makes runs bitwise repeatable but freezes whatever orientation
the seeded RANSAC produces — seeds 0–2 on `3-1-1` all reproduced the same
*wrong* h direction (mIoU 0.08–0.43). On `5-1`, seed choice alone moved mIoU
0.777 → 0.870 (seeds: unseeded 0.777, s0 0.870, s1 0.863, s2 0.818). Fix
correctness with canonical orientation first; treat residual seed sensitivity
as a symptom of a marginal centreline fit, not a tuning knob to sweep.

## 3. Depth map (`depth_map.png`, `depth_map_viridis.png`)

What to look for and what it means:

- **Large white voids / high NaN fraction concentrated at one end**: the
  fitted centreline is off-centre — an approximately sinusoidal residual in
  r vs theta pushes points out of the narrow denoise r-band. On `5-1`, only
  ~23% of left-end points fell inside the band (r 3.65–3.9) with a ~25 cm
  residual; `residual_recentre` restored in-band coverage to ~87% and NaN
  38.8% → 18.9%. On `3-1-1` the same defect discarded **46%** of lining
  points (lining-r std 0.085 → 0.019 after recentring, coverage 0.41 → 0.67).
  Remediation is `residual_recentre` in unfolding, **not** widening the
  denoise band and **not** hole-filling.
- **Do not chase cosmetic NaN removal.** Hole-fill to 0% NaN on `5-1`
  *reduced* mIoU (0.403 → 0.347) because the margin trim shifted the axial
  frame. Depth cosmetics only matter insofar as detection improves; the
  oracle experiment showed remaining headroom was in detection, not depth
  (perfect K-Y prompts on the same recentred map → 0.814).
- **Banding around specific rings** (density non-uniformity): `n_segment`
  window does not match the actual scan coverage. Notebook station-scale
  values (e.g. `[11, 11]` for a 50-ring scan) are invalid or empty on a
  10-ring subset; `3-1-1` needed `[2, 8]`, and `n_segment [1, 9]` was part
  of the best bounded `4-1` retune (0.634 → 0.661).
- **Low joint contrast** (ring seams barely visible): the two enhancing depth
  thresholds are the strongest confirmed causal knobs on T1/T2-like scans.
  Reverting `depth_threshold_high` 0.015 → 0.008 cost **−0.417 mIoU**;
  `depth_threshold_low` 0.005 → 0.003 cost **−0.266** (deterministic across
  3 repeats). If joints look washed out, move these first.
- Healthy references: recentre residual max ≲ 10 cm; ~19–22% NaN is normal
  for complex-family scans (4-1-style maps).

## 4. Denoised cloud / band selection

- Check the retained-point fraction (`denoise_retained_ratio` intrinsic) and
  whether discards are spatially uniform. A very low retention with
  downstream depth holes means over-gating (`f_over_gate`) — but first rule
  out the off-centre centreline of §3, which mimics over-gating while the
  band itself is correct.
- Geometry knobs (`mask_r_low/high`, `diameter`) had small isolated effects
  on `1-1` (reverting `mask_r_low` even gained +0.029) but are load-bearing
  for cross-tunnel transfer — keep them at tunnel priors rather than tuning
  them for a single scan.

## 5. Detection (`detected_lines.png`, `initial_prompt_points.png`)

- **Count the vertical lines against the expected ring count.** On `5-1` the
  cleaner recentred map yielded **11** Hough verticals for **10** rings; the
  geometric SAM stage truncated and misaligned every column (mIoU 0.206
  despite a good depth map). Fix: force synthetic ring-centre verticals
  (`hough_threshold_vertical=5000`) and lower oblique/horizontal thresholds
  (35 / 80 px) → 0.681. More detected lines is not better; **consistency
  with ring count** is what matters (`det_ring_count_error` intrinsic).
- Distinguish **real detections vs fallback**: `det_real_detection_ratio` and
  `det_fallback_ratio`. Complex-family scans (`4-*`) often run entirely on
  synthetic verticals + geometric SAM fallback; in that regime Hough
  parameter tuning is unidentifiable (the `1-1` study could not measure any
  detection effect for exactly this reason — do not conclude the knobs are
  harmless).
- Spacing regularity: prompt x-spacing CV (`det_x_spacing_cv`) and y-std
  (`det_y_std`) against the K/AB block-height pattern. On `3-1` the K-row
  gate accepted y* = 1550.1 vs design 1553 (Δ = 2.9 px) — single-digit pixel
  agreement is the healthy scale.

## 6. Segmentation (`segmentation_results.png`) and evaluation

- Per-class IoU patterns are diagnostic:
  - **Permutation** (classes swapped in mirror pairs) → orientation, §1.
  - **Uniform collapse of all lining classes** with background OK → upstream
    coverage/detection failure, not SAM parameters (literal `3-1-1`: every
    lining class ≈ 0.00 while background 0.635).
  - **Graded per-class differences** (all classes present, some weak) → this
    is the only regime where SAM geometry (`segment_width`, `K_height`/
    `AB_height`, `y_bounds`, `taper_angle`) is worth tuning.
- `sam_fill_rate`, `sam_ring_completeness`, `sam_segment_size_cv` are the
  GT-free views of the same signals.

## 7. Tuning order (empirically enforced)

Later knobs are meaningless while earlier ones are wrong
(`orientation-sensitivity.md` §6):

1. **Orientation** (canonical flag, `h_ring_sign` + matching `segment_order`).
   Validate: stage-1 invariant passes; no permutation signature.
2. **Centreline / unroll quality** (`residual_recentre`, polynomial degree).
   Validate: recentre residual ≲ 10 cm; NaN fraction in family-normal range.
3. **Band selection** (denoising `mask_r_low/high`, theta gates). Validate:
   retention fraction, spatially uniform discards.
4. **Detection** (Hough thresholds, synthetic verticals). Validate: line
   count == ring count; spacing matches block pattern.
5. **SAM geometry**. Only after 1–4; graded per-class IoU is the signal.

Corollary for a 3-round reflection budget: spend the first round confirming
stages 1–3 are healthy before touching detection/SAM parameters.

## 8. Known per-case context for the reflection targets

- **`4-4`, `4-3` (t4&5, complex)**: family runs on geometric SAM fallback with
  synthetic verticals. The `4-1` improve campaign showed orientation knob
  flips collapse mIoU (`h_ring_sign=-1` → 0.13–0.16) and the best bounded
  retune was `n_segment [1, 9]` + `residual_recentre` (+0.027). Expect
  gains from coverage/centreline and detection-pattern parameters, not from
  orientation or Hough sweeps. Legacy 0.741 on `4-1` was a lucky unpinned
  mirror — not reachable by parameter tuning on the pinned frame.
- **`1-4`, `1-5` (t1&2, staggered)**: depth thresholds are the dominant causal
  knobs (§3). `1-5` is the known label-rotation case that only the phase
  alarm catches — check the permutation signature before tuning anything.
- **`3-5` (t3, continuous)**: T3 short subsets are most sensitive to
  centreline quality and the recentre band; without recentring the narrow
  r-band discards ~46% of lining points. Note the t3 family proxy
  systematically **underestimates** good anchors (holdout MAE_anchor 0.295,
  e.g. `3-6` true 0.836 vs proxy 0.421) — on t3, trust the proxy **delta**
  between rounds, not its absolute value.

## 9. Proxy score: how to read it during reflection

- The per-family B1+B2lean proxy ranks anchor vs bad 24/24 and its alarm has
  precision 1.00, but absolute calibration varies by family (t1&2 anchor MAE
  0.095, t4&5 0.074, t3 0.295). Use it as a **directional** improvement
  signal; corroborate any claimed improvement against the artifacts
  themselves (line count, NaN fraction, permutation signature).
- A proxy *increase* driven purely by evidence features (retention, NaN,
  detection ratios) while B1 coherence features degrade is suspect —
  cosmetic fixes (hole-fill) produced exactly this pattern and lost mIoU.

## 10. Anti-patterns observed in past campaigns

- Trusting visual depth-map quality as a success signal (§1).
- Chasing NaN% to zero (§3, `5-1` hole-fill regression).
- Sweeping seeds to find a lucky orientation instead of pinning it (§2).
- Tuning Hough/SAM while an upstream coverage defect is active (§7).
- Flipping `swap_tunnel_centers` / `h_ring_sign` as a generic "try both"
  move on canonical-orientation runs — on pinned frames it produces label
  collapse (0.13–0.16), never improvement.
- Rerunning stage 1 mid-comparison: it re-rolls the centreline and confounds
  attribution (the `literal-orientfix` confound). Keep stage-1 artifacts
  frozen and replay stages 2–6 when comparing parameter overlays.
