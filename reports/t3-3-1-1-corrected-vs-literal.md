# T3 Agent: Corrected vs Literal on `3-1-1`

> **Current anchor:** params `anchors/t3/3-1-1/`, artifacts `data/anchors/3-1-1/`,
> log `logs/t3_3-1-1.log`, mIoU **0.881**. Historical paths below use pre-anchor names.

## Scope

Build `anchors/t3` from `sam4tun/notebook/t3.ipynb` and compare two
reproducible variants on labelled subset `3-1-1` (642,638 points, rings
27–36). Direction was held constant (`swap_tunnel_centers: true`, Spearman
ρ on raw axis ≈ −1.0).

Primary metric: semantic mIoU. Supporting: OA, F1, mAP.

## Single-instance gate (corrected)

| Criterion | Result |
|---|---|
| Case | `3-1-1` |
| Command | `python -m sam4tun.pipeline … --profile t3 --params-dir agents/t3/variants/corrected --overwrite` |
| Stages 1–6 | Pass |
| Eval rows | 642,638 |
| Rings | 27–36 |
| T3 params active | Yes (theta gate, T3 geometry, uniform-K snap) |
| mIoU > 0.30 | **0.480** Pass |
| Evidence | `data/3-1-1-corrected/`, log `logs/t3_3-1-1_corrected.log` |

Gate logged in `agents/t3/3-1-1/gate_corrected.json` before the literal run.

## Performance comparison

| Variant | OA | F1 | mIoU | mAP |
|---|---:|---:|---:|---:|
| **Corrected-intent** | **0.631** | **0.638** | **0.480** | **0.120** |
| Literal notebook | 0.304 | 0.162 | 0.121 | 0.000 |
| Δ (corrected − literal) | +0.327 | +0.476 | +0.359 | +0.120 |

### Per-class IoU

| Class | Corrected | Literal |
|---|---:|---:|
| Background | 0.450 | 0.635 |
| K | 0.639 | 0.002 |
| B1 | 0.485 | 0.000 |
| A1 | 0.222 | 0.000 |
| A2 | 0.522 | 0.212 |
| A3 | 0.426 | 0.000 |
| B2 | 0.619 | 0.001 |

Literal collapses almost all lining classes; corrected recovers usable
K/B/A segmentation on this 10-ring span.

## Implementation differences (material)

See also `agents/t3/variants/comparison_diff.json`.

| Stage | Corrected | Literal (notebook-effective) | Impact on `3-1-1` |
|---|---|---|---|
| Denoising theta high clause | `theta > 17.15` | `r > 17.15` (typo) | Small on this scan (theta gate removed 1,525 pts when corrected) |
| Enhancing surface | Use upsampled cloud | Discard upsample; project `pred==7` | Large — depth map quality |
| Enhancing joints | Outlier points + interpolation | Outliers only, no interpolation | Large — joint contrast for Hough |
| `n_segment` | `[2, 8]` for 10-ring span | `[11, 11]` (50-ring notebook) | Coverage window invalid/empty on short span |
| Detection | T3 inherit-Y + **uniform-K snap** | Inherit-Y only | Stabilises prompt centres across rings |
| SAM K geometry | T3 templates + **X mirror** | T3 templates, no mirror | Aligns K prompts with T3 orientation |

## Post-hoc unfolding fixes (2026-07-17)

Two unfolding defects were found after the first comparison; both are
subset-scale failure modes the notebook never hit on full 50-ring scans.
Evidence: `agents/t3/3-1-1/depth_map_fix.json`,
`agents/t3/3-1-1/theta_orientation_fix.json`.

1. **Centreline residual recentring** (`residual_recentre`, corrected
   profile): the degree-2 centreline misses ring-to-ring snaking by up to
   ~28 cm on 10 rings, so `r` swings sinusoidally and the narrow 2.85–3.0
   denoising band discarded 46% of points (large white holes in the depth
   map). Fitting and subtracting `r0 + a·cosφ + b·sinφ` per 0.5 m axial bin
   cut lining-r std 0.085 → 0.019 and raised coverage 0.41 → 0.67.
2. **Deterministic theta orientation**
   (`deterministic_theta_orientation`, **both** variants): the notebook's
   mirror-side convention depends on the sign of the centreline z-slope,
   which is RANSAC noise on short subsets. The first literal run mirrored
   circumferentially (`theta_literal ≈ 18.59 − theta_corrected`, corr
   −0.977), so its clean-looking depth map scored mIoU 0.121 — every block
   landed at its mirror position against the orientation-specific T3
   templates. The fix takes handedness from the horizontal travel
   direction (pinned by `swap_tunnel_centers`).

### Updated comparison (same orientation for both variants)

The decisive experiment is the **controlled swap**: take the exact
`data/3-1-1-literal` unwrapped cloud (same stochastic centreline draw),
mirror theta only (`theta' = π·D − theta`), and rerun stages 2–6 with
unchanged literal parameters.

| Variant | OA | F1 | mIoU | mAP | mAP@50 |
|---|---:|---:|---:|---:|---:|
| **Corrected + recentring** (`data/3-1-1-corrected-fix`) | 0.823 | **0.840** | **0.734** | **0.341** | **0.646** |
| **Literal, theta mirrored only** (`data/3-1-1-literal-swapped`) | **0.838** | 0.824 | 0.705 | 0.313 | 0.496 |
| Literal, full rerun w/ orient fix (`data/3-1-1-literal-orientfix`) | 0.642 | 0.646 | 0.484 | 0.071 | 0.191 |
| Corrected, pre-fix (`data/3-1-1-corrected`) | 0.631 | 0.638 | 0.480 | 0.120 | 0.300 |
| Literal, mirrored (`data/3-1-1-literal`) | 0.304 | 0.162 | 0.121 | 0.000 | 0.000 |

Reading:

1. The original 0.480-vs-0.121 result was almost entirely the orientation
   coin flip. With orientation corrected on the same centreline draw, the
   literal profile reaches **0.705** — the notebook parameter
   inconsistencies cost only ~0.03 mIoU on this subset (0.734 vs 0.705).
2. The `literal-orientfix` full rerun (0.484) is **confounded**: rerunning
   stage 1 re-rolled the stochastic RANSAC centreline and drew a poor fit
   (steep spurious z-slope, degraded depth map). It should not be used for
   variant attribution.
3. The dominant performance factors on short subsets are therefore
   (a) circumferential orientation and (b) centreline quality — both
   unfolding-stage properties that the notebook leaves to chance. The
   deterministic orientation flag removes the coin flip; residual
   recentring removes the dependence on a lucky centreline draw.

## Conclusions

1. Canonical T3 profile should be the **corrected-intent** set under
   `agents/t3/parameters/`.
2. Literal notebook reproduction is **not** a viable baseline on short
   labelled subsets like `3-1-1`: notebook station-scale assumptions
   (`n_segment=[11,11]`, vertical rho band for long spans) and dead
   upsampling/interpolation paths destroy lining IoU.
3. Direction for `3-1-1` is `swap_tunnel_centers: true` by ring-metadata
   orientation; held fixed for this comparison.
4. Corrected mIoU 0.480 is an **anchor**, not a tuned optimum. Further
   T3 work (prompt geometry, depth thresholds, coverage) should start
   from the corrected profile and beat this gate before panel sweeps.
   **Update 2026-07-17:** with the unfolding fixes the corrected anchor is
   now **0.734** (`data/3-1-1-corrected-fix`); see the post-hoc section.
5. Both unfolding fixes must stay enabled for subset-scale runs; the
   deterministic orientation applies to every profile (a mirrored map is
   visually indistinguishable but scores near zero against T3 geometry).

## Known limitations (documented, intentionally not fixed)

1. **Axis identification on near-square footprints.** The tunnel axis is
   chosen as the short edge of the minimum bounding rectangle of the XY
   footprint. Our 10-ring subsets are ~12 m x 5.9 m, so the pick is
   unambiguous, and we commit to 10-ring subsets going forward. But for
   spans short enough that the footprint approaches square (~5 rings for
   T3), `argmin(edges)` could select the wrong edge pair and the axis
   would be 90 degrees wrong. Neither `deterministic_theta_orientation`
   nor `residual_recentre` protects against this. If very short subsets
   are ever needed, add an explicit axis sanity check (e.g. verify ring
   metadata varies along the chosen axis).
2. **Axial direction (`swap_tunnel_centers`) is still a per-scan input.**
   The deterministic orientation flag removes the circumferential mirror
   coin flip *given* an axial direction, but choosing that direction still
   relies on per-scan validation (ring-metadata Spearman check). Deferred
   to a later reflective-agent solution.

## Archives

| Variant | Local archive | Tracked manifest |
|---|---|---|
| Corrected | `data/ablation/3-1-1-corrected/` | `reports/experiments/3-1-1-corrected/` |
| Literal | `data/ablation/3-1-1-literal/` | `reports/experiments/3-1-1-literal/` |
| Scratch runs | `data/3-1-1-corrected/`, `data/3-1-1-literal/` | — |
| Logs | `logs/t3_3-1-1_corrected.log`, `logs/t3_3-1-1_literal.log` | — |
