# Proxy feature-set ablation (bo-unified)

_Generated 2026-07-21T13:13:16_

## Goal

Justify each component of the final GT-free mIoU proxy with holdout numbers: B1 (coherence), B2lean (evidence), family one-hot, and the phase-check alarm. Zero new pipeline runs — all fits use `training_table.csv` (225 trials) and the 48 holdout manifests.

## Feature sets

| Set | Features |
|---|---|
| `B1` | 7: `det_x_spacing_cv, det_y_std, det_ring_count_error, sam_fill_rate, sam_ring_completeness, sam_segment_size_cv, sam_ontology_divergence` |
| `B2lean` | 4: `denoise_retained_ratio, depth_nan_ratio, det_real_detection_ratio, det_fallback_ratio` |
| `B2` | 7: `denoise_retained_ratio, depth_nan_ratio, depth_outlier_ratio, det_midpoint_ratio, det_real_detection_ratio, det_fallback_ratio, det_n_points` |
| `B1+B2lean` | 11: `det_x_spacing_cv, det_y_std, det_ring_count_error, sam_fill_rate, sam_ring_completeness, sam_segment_size_cv, sam_ontology_divergence, denoise_retained_ratio, depth_nan_ratio, det_real_detection_ratio, det_fallback_ratio` |
| `B1+B2` | 14: `det_x_spacing_cv, det_y_std, det_ring_count_error, sam_fill_rate, sam_ring_completeness, sam_segment_size_cv, sam_ontology_divergence, denoise_retained_ratio, depth_nan_ratio, depth_outlier_ratio, det_midpoint_ratio, det_real_detection_ratio, det_fallback_ratio, det_n_points` |

## Holdout grid

Per-family = 3 RidgeCV models (one per family). Pooled = one RidgeCV on all training rows. `+oh` adds family one-hot.

| Label | n | MAE | MAE_anchor | MAE_bad | Spearman | Rank | Alarm P | Alarm R |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `per_family/B1` | 48 | 0.114 | 0.151 | 0.077 | 0.751 | 24/24 (1.00) | 0.96 | 0.93 |
| `pooled/B1` | 48 | 0.113 | 0.164 | 0.061 | 0.771 | 24/24 (1.00) | 0.92 | 0.96 |
| `pooled+oh/B1` | 48 | 0.112 | 0.156 | 0.068 | 0.709 | 24/24 (1.00) | 1.00 | 1.00 |
| `per_family/B2lean` | 48 | 0.101 | 0.177 | 0.024 | 0.703 | 24/24 (1.00) | 0.80 | 0.86 |
| `pooled/B2lean` | 48 | 0.121 | 0.169 | 0.073 | 0.726 | 24/24 (1.00) | 0.75 | 1.00 |
| `pooled+oh/B2lean` | 48 | 0.122 | 0.168 | 0.075 | 0.704 | 24/24 (1.00) | 0.77 | 1.00 |
| `per_family/B2` | 48 | 0.092 | 0.166 | 0.018 | 0.731 | 24/24 (1.00) | 1.00 | 0.86 |
| `pooled/B2` | 48 | 0.109 | 0.176 | 0.041 | 0.725 | 24/24 (1.00) | 0.77 | 1.00 |
| `pooled+oh/B2` | 48 | 0.116 | 0.182 | 0.049 | 0.690 | 24/24 (1.00) | 0.96 | 1.00 |
| `per_family/B1+B2lean` | 48 | 0.110 | 0.155 | 0.066 | 0.719 | 24/24 (1.00) | 1.00 | 0.89 |
| `pooled/B1+B2lean` | 48 | 0.122 | 0.174 | 0.070 | 0.693 | 24/24 (1.00) | 0.80 | 1.00 |
| `pooled+oh/B1+B2lean` | 48 | 0.121 | 0.175 | 0.066 | 0.701 | 24/24 (1.00) | 0.80 | 1.00 |
| `per_family/B1+B2` | 48 | 0.097 | 0.144 | 0.050 | 0.772 | 24/24 (1.00) | 1.00 | 0.86 |
| `pooled/B1+B2` | 48 | 0.114 | 0.178 | 0.050 | 0.738 | 24/24 (1.00) | 0.80 | 1.00 |
| `pooled+oh/B1+B2` | 48 | 0.113 | 0.171 | 0.054 | 0.703 | 24/24 (1.00) | 0.86 | 1.00 |

**Best per-family feature set by holdout MAE:** `B2` (MAE=0.092, rank=24/24).

### Family one-hot vs per-family (B1+B2lean)

| Variant | MAE | Rank |
|---|---:|---:|
| pooled (no one-hot) | 0.122 | 24/24 |
| pooled + family one-hot | 0.121 | 24/24 |
| **per-family** (separate models) | 0.110 | 24/24 |

### B2 full vs B2lean (per-family)

| Set | MAE | Rank |
|---|---:|---:|
| `B2lean` | 0.101 | 24/24 |
| `B2` | 0.092 | 24/24 |
| `B1+B2lean` | 0.110 | 24/24 |
| `B1+B2` | 0.097 | 24/24 |

B2lean drops `depth_outlier_ratio`, `det_midpoint_ratio`, and `det_n_points`
(family-conditional / regime-constant). On this holdout set full B2 edges
B2lean by ~0.01 MAE with identical ranking; the lean set remains attractive
when preferring fewer, less family-conditional features.

## Permutation control

Within-family mIoU shuffle, refit per-family `B1+B2lean`, 20 repeats (seed=0).

| | Real fit | Permutation mean ± std |
|---|---:|---:|
| Holdout MAE | **0.110** | 0.353 ± 0.013 |
| Ranking accuracy | **1.00** (24/24) | 0.50 ± 0.17 |

A large gap (real ≪ perm MAE, real ≫ perm ranking) confirms the fit is not a capacity artifact.

## Phase-alarm augmentation

For the deployment proxy (per-family `B1+B2lean`), final alarm =
`proxy_alarm OR phase_alarm` (phase applicable on t1&2 / t3 only).

| Variant | FP | FN | Precision | Recall | Recovered FNs |
|---|---:|---:|---:|---:|---|
| proxy only | 0 | 3 | 1.00 | 0.89 | — |
| proxy OR phase | 1 | 2 | 0.96 | 0.93 | `1-5-anchor` |

## Conclusion

- **Lowest holdout MAE:** per-family **`B2`** (0.092) and **`B1+B2`** (0.097). Every feature set ranks anchor vs bad **24/24**.
- **Deployment default remains per-family `B1+B2lean`** (MAE 0.110, rank 24/24, alarm P=1.00 / R=0.89):
  - Adds B1 coherence on top of evidence features (catches form / regularity failures that pure B2 may miss outside this holdout).
  - Perfect alarm precision (vs 0.80 for B2lean alone).
  - Only +0.018 MAE vs the B2 MAE winner, with fewer family-conditional features than full `B1+B2`.
- Per-family models beat a single pooled model (± family one-hot) — keep separate family proxies.
- Permutation control: real MAE 0.110 vs shuffled 0.353 — signal is genuine.
- **Phase-check** is retained as an OR-ed second alarm on t1&2/t3; recovers the `1-5-anchor` label-rotation FN that B1+B2lean alone misses (FN 3→2, +1 FP).

## Artifacts

- Scores: `bo-unified/family/ablation_scores.csv`
- Script: `bo-unified/ablation.py`
- Parent report: [`report.md`](report.md)

