# Critical Parameters Experiment

> **Historical.** Current promoted `1-1` / `2-1` anchors use canonical
> orientation (mIoU 0.787 / 0.874). See
> [`orientation-sensitivity.md`](orientation-sensitivity.md) and
> [`anchors-summary.md`](anchors-summary.md).

## Scope

This report documents the parameter-transfer experiments for the six-stage
SAM4Tun pipeline on the labelled `1-1` and `2-1` subsets. The primary
selection metric is semantic mean IoU (mIoU); OA, F1, and instance mAP are
reported as supporting metrics.

The preserved winners are archived locally as:

- `data/anchors/1-1/`
- `data/anchors/2-1/`

Tracked lightweight lineage (parameter snapshots, evaluation summaries,
manifests) lives under:

- `reports/experiments/1-1-best-observed/`
- `reports/experiments/2-1-best-observed/`

## Methodology

### Reference configurations

The study used the sample profile as the LOW configuration and the
`memory+state+knowledge` Opus 4.6 settings as the HIGH configuration. The
full `2^20` parameter space was not searched.

For `1-1`, a fixed post-unfolding checkpoint removed centreline/RANSAC
variation from downstream comparisons. The experiment then used:

1. HIGH and LOW anchor runs.
2. Whole-stage reversions.
3. Mechanism-group reversions.
4. One-factor reversions.
5. A 16-run Resolution-IV fractional-factorial screen.
6. Three repeats of HIGH, LOW, and the two depth-threshold reversions.

The phase-0 gate passed before bulk screening:

| Case | HIGH mIoU | LOW mIoU | Gain | Gate |
|---|---:|---:|---:|---|
| `1-1` | 0.784 | 0.276 | +0.508 | Pass |

The gate required HIGH mIoU ≥ 0.70, HIGH–LOW mIoU ≥ 0.15, and agreement
within 0.05 of the prior HIGH run.

### Practical-minimum transfer test

The `2-1` transfer used sample defaults except for the practical adaptive
minimum populated from the `2-1` Opus 4.6 profile:

| Category | Retained adaptive parameters |
|---|---|
| Geometry | `diameter`, `mask_r_low`, `mask_r_high` |
| Density and coverage | three `upsampling_stage*_target_distance` values, `n_segment_start`, `n_segment_end` |
| Joint/outlier handling | `depth_threshold_low`, `depth_threshold_high` |
| Direction | `swap_tunnel_centers` |

The `2-1` experiment also tested both tunnel-axis directions. The only
change in the flipped run was `swap_tunnel_centers: true → false`.

## Results

### Critical-parameter evidence on 1-1

Whole-stage reversion established enhancing as the dominant source of gain.

| Reverted stage | ΔmIoU vs HIGH | ΔmAP vs HIGH | Interpretation |
|---|---:|---:|---|
| Enhancing | −0.441 | −0.373 | Dominant |
| Denoising | +0.024 | +0.070 | Minor / trade-off |
| Detecting | −0.001 | 0.000 | No measurable effect in this scan |
| SAM crop | 0.000 | 0.000 | No measurable effect in this scan |

One-factor reversions identify the two enhancing depth thresholds as the
only confirmed critical parameters:

| Parameter reverted to LOW | HIGH value | LOW value | ΔmIoU | ΔmAP |
|---|---:|---:|---:|---:|
| `depth_threshold_high` | 0.015 | 0.008 | −0.417 | −0.310 |
| `depth_threshold_low` | 0.005 | 0.003 | −0.266 | −0.269 |
| `grad_threshold` | 0.15 | 0.20 | −0.014 | −0.098 |
| `mask_r_low` | 2.33 | 2.70 | +0.029 | +0.068 |

The confirmation repeats were deterministic from the same post-unfolding
checkpoint: HIGH mIoU was 0.784 for all three repeats; reverting
`depth_threshold_high` yielded 0.367 and reverting `depth_threshold_low`
yielded 0.518 in all three repeats.

### Best observed 1-1 run

The highest observed 1-1 mIoU came from fractional-factorial row
`p3_ff7_02`, archived locally as `data/ablation/1-1/` with tracked
metadata in `reports/experiments/1-1-best-observed/`.

| Metric | Best observed 1-1 |
|---|---:|
| OA | 0.914 |
| F1 | 0.897 |
| mIoU | 0.815 |
| mAP | 0.4850 |

Its relevant parameter values were:

| Parameter | Value |
|---|---|
| `mask_r_low`, `mask_r_high` | 2.70, 2.78 |
| `y_step`, `z_step` | 0.4, 0.001 |
| `grad_threshold` | 0.15 |
| Three upsampling distances | 0.08, 0.03, 0.015 |
| `depth_threshold_low`, `depth_threshold_high` | 0.005, 0.015 |
| `inter_radius` | 0.03 |
| `n_segment_start`, `n_segment_end` | 0, 5 |

This is the **best observed screening run**, not a fully independently
replicated optimum. The two depth thresholds, rather than the entire row,
are the confirmed causal findings.

### Practical-minimum transfer to 2-1

| Configuration | OA | F1 | mIoU | mAP |
|---|---:|---:|---:|---:|
| Full Opus 4.6 reference | 0.9489 | 0.9434 | 0.8940 | Not reported |
| Practical minimum, original direction | 0.942 | 0.930 | 0.873 | 0.7405 |
| Practical minimum, flipped direction | **0.955** | **0.945** | **0.900** | **0.7950** |

The original practical-minimum profile was within 0.021 mIoU of the full
Opus reference, inside the predeclared 0.03 tolerance. Flipping direction
increased mIoU by 0.027 and mAP by 0.0545, producing the best 2-1 result,
archived as `data/ablation/2-1/` with tracked metadata in
`reports/experiments/2-1-best-observed/`.

## Conclusions

1. Keep `depth_threshold_low` and `depth_threshold_high` as mandatory
   adaptive controls. They are the only parameters with a confirmed large
   causal effect on `1-1`.
2. Keep physical geometry controls (`diameter`, `mask_r_low`,
   `mask_r_high`) and coverage/density controls (three upsampling distances
   and `n_segment`) in the practical adaptive interface. They support
   transfer even when their isolated `1-1` effects were small.
3. Infer or validate tunnel direction per scan (`swap_tunnel_centers` and
   `helpers/tunnel_direction.py`). The `2-1` flip changed mIoU from 0.873
   to 0.900 using otherwise identical practical-minimum settings.
4. Do not promote the Hough/detection or SAM crop settings to universally
   critical based on `1-1`: vertical-line fallback made their effects
   unidentifiable in that case.
5. The practical-minimum profile transferred to `2-1` successfully, but a
   broader confirmation panel is required before treating it as universal.

## Reproducibility evidence

- 1-1 study: `data/1-1-ablation-study-20260716_141415/` (local)
- 1-1 best archive: `data/ablation/1-1/` (local artifacts)
- 2-1 best archive: `data/ablation/2-1/` (local artifacts)
- Tracked manifests: `reports/experiments/1-1-best-observed/manifest.json`,
  `reports/experiments/2-1-best-observed/manifest.json`
- 1-1 winner log: `logs/1-1-best-observed-p3_ff7_02.log` (local)
- 2-1 winner log: `logs/2-1-best-observed.log` (local)
- Study tooling snapshot: `reports/critical-parameters-experiment/`
