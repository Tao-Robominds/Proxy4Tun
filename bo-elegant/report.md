# bo-elegant report — 3-anchor unified lean proxy

_Generated 2026-07-22T16:09:07_

## Design

- Train anchors: `2-1, 3-1, 5-1` (108 archived trials).
- Selected feature set: **loo_sam_ring_completeness** → `['depth_nan_ratio', 'denoise_retained_ratio', 'det_real_detection_ratio', 'sam_fill_rate', 'sam_ontology_divergence']`.
- Taxonomy: Evidence = artifact/depth quality; Coherence = detection+segmentation form.
- One pooled RidgeCV (no family one-hot).

### Dropped up front (prior lessons)

- `depth_outlier_ratio`: permutation-control failure of full B2 (family-conditional)
- `det_fallback_ratio`: exact complement of det_real_detection_ratio; keep one
- `det_midpoint_ratio`: regime-constant / near-zero coef in pooled model
- `det_n_points`: regime-constant / near-zero coef
- `det_ring_count_error`: near-zero coef everywhere
- `det_x_spacing_cv`: near-zero coef everywhere
- `det_y_std`: near-zero coef everywhere
- `sam_segment_size_cv`: near-zero coef everywhere

### Frozen coefficients (standardized)

| Feature | Coef | Block |
|---|---:|---|
| `sam_fill_rate` | +0.1962 | Coherence |
| `det_real_detection_ratio` | +0.1355 | Coherence |
| `denoise_retained_ratio` | +0.0898 | Evidence |
| `depth_nan_ratio` | +0.0806 | Evidence |
| `sam_ontology_divergence` | +0.0200 | Coherence |

- Train MAE=0.100, Spearman=0.819, α=1
- Alarm threshold=0.442, low-mIoU floor=0.350

### Mini-ablation (training / LOLO)

| Set | n | train MAE | train Sp | LOLO MAE | LOLO Sp |
|---|---:|---:|---:|---:|---:|
| `Evidence` | 2 | 0.142 | 0.615 | 0.181 | 0.469 |
| `Coherence` | 4 | 0.104 | 0.814 | 0.166 | 0.779 |
| `Evidence+Coherence` | 6 | 0.101 | 0.816 | 0.167 | 0.789 |
| `loo_sam_ring_completeness` ← selected | 5 | 0.100 | 0.819 | 0.169 | 0.662 |
| `loo_sam_ontology_divergence` | 5 | 0.102 | 0.810 | 0.159 | 0.793 |

### Permutation control

- Real train MAE **0.100** vs shuffled 0.292 ± 0.009 (n=20, pass=True).

## Holdout evaluation

- Scored runs: 54 (ok=54).
- Pooled MAE=0.113, Spearman=0.719, Pearson=0.904
- Anchor>bad ranking: **27/27** (acc=1.00)

### Per-family

| Family | n | MAE | Spearman | MAE_anchor | MAE_bad |
|---|---:|---:|---:|---:|---:|
| complex | 18 | 0.080 | 0.918 | 0.074 | 0.086 |
| continuous | 18 | 0.168 | 0.739 | 0.312 | 0.024 |
| staggered | 18 | 0.089 | 0.762 | 0.096 | 0.083 |

### Bad-flagging alarm

- Precision=0.87, Recall=0.96 (TP=27, FP=4, FN=1)
- Threshold=0.442 (low-mIoU floor on train=0.350)

## Artifacts

- `bo-elegant/family/models.json`
- `bo-elegant/family/ablation.json`
- `bo-elegant/family/holdout_scores.csv`
- `bo-elegant/registry.json`

---

# Proxy v2 — regime-neutral continuous fix

_Generated 2026-07-22T21:00:20_

## Root cause addressed

See `bo-elegant/t3_review.md`. Deployed `uniform_k_snap` rewrites Types to
`propagated`, forcing `det_real_detection_ratio=0` on every healthy continuous
run and docking the v1 proxy by ~0.18. v2 drops that feature and adds
`det_row_residual_px`, `det_row_y_std`, `phase_incoherence_deg`.

- Selected set: **loo_det_row_y_std+pruned** → `['sam_fill_rate', 'sam_ontology_divergence', 'det_row_residual_px', 'det_row_gated', 'depth_nan_ratio']`
- Train rows: 63 (`{'2-1': 14, '3-1': 35, '5-1': 14}`)
- Train MAE=0.122, Spearman=0.829
- Permutation: real 0.122 vs 0.291±0.016 (pass=True)

### Coefficients (standardized)

| Feature | Coef | Block |
|---|---:|---|
| `sam_fill_rate` | +0.3755 | Coherence |
| `det_row_residual_px` | -0.1799 | Coherence |
| `det_row_gated` | +0.1696 | Coherence |
| `depth_nan_ratio` | +0.0902 | Evidence |
| `sam_ontology_divergence` | +0.0434 | Coherence |

## Holdout v1 vs v2

| Metric | v1 | v2 |
|---|---:|---:|
| Pooled MAE | 0.113 | 0.094 |
| Spearman | 0.719 | 0.808 |
| Ranking | 27/27 | 27/27 |

### Per-family MAE_anchor

| Family | v1 MAE_a | v2 MAE_a |
|---|---:|---:|
| complex | 0.074 | 0.099 |
| continuous | 0.312 | 0.108 |
| staggered | 0.096 | 0.102 |

### v2 alarm: P=1.00 R=1.00 (TP=27, FP=0, FN=0)

### 3-6 gate: **PASS** (continuous MAE_anchor=0.108)

## Artifacts

- `bo-elegant/family/models_v2.json`
- `bo-elegant/family/holdout_scores_v2.csv`
- `bo-elegant/validation_gate_3-6.md`
- `bo-elegant/t3_review.md`

---

# Consolidated ablation study

_Generated 2026-07-23T00:37:08_

Zero new pipeline runs. All variants refit on the v2 training table
(n=63) and scored on the same 54 holdout runs.
Harness gate: frozen v2 numbers reproduced (`ablation_harness_gate.md`).

Columns: MAE / Spearman / MAE_anchor / MAE_anchor(continuous) / Rank / Alarm P/R.

## A. Regime-swap (headline)

v1 features include strategy-confounded `det_real_detection_ratio`;
v2 replaces it with gate-conditional `det_row_residual_px` + `det_row_gated`.

| Variant | n_feat | MAE | Sp | MAE_a | MAE_a_cont | Rank | Alarm P/R | Note |
|---|---:|---:|---:|---:|---:|---|---|---|
| `A_v1_features_refit` | 5 | 0.094 | 0.719 | 0.130 | 0.222 | 27/27 | 1.00/1.00 | controlled: v1 feats on v2 table |
| `A_v2_lean_refit` | 5 | 0.094 | 0.808 | 0.103 | 0.108 | 27/27 | 1.00/1.00 | controlled: v2 lean on v2 table |
| `A_frozen_v1` | 5 | 0.113 | 0.719 | 0.161 | 0.312 | 27/27 | 0.87/0.96 | deployed v1 |
| `A_frozen_v2` | 5 | 0.094 | 0.808 | 0.103 | 0.108 | 27/27 | 1.00/1.00 | deployed v2 |

Continuous MAE_anchor: v1-features 0.222 → v2-lean 0.108 (frozen v1 0.312 → frozen v2 0.108).

## B. Unified vs per-family

All on v2 lean-5 features. Per-family n_train = `{'complex': 14, 'continuous': 35, 'staggered': 14}` — the 3-anchor design starves
family-specific models (staggered/complex ≈14 rows).

| Variant | n_feat | MAE | Sp | MAE_a | MAE_a_cont | Rank | Alarm P/R | Note |
|---|---:|---:|---:|---:|---:|---|---|---|
| `B_pooled` | 5 | 0.094 | 0.808 | 0.103 | 0.108 | 27/27 | 1.00/1.00 | one Ridge |
| `B_per_family` | 5 | 0.091 | 0.807 | 0.087 | 0.064 | 27/27 | 1.00/0.83 | 3 RidgeCVs |
| `B_pooled_onehot` | 8 | 0.081 | 0.808 | 0.093 | 0.099 | 27/27 | 1.00/1.00 | + family one-hot |

Historical reference (`bo-unified/ablation.md`, different era): per-family
B1+B2lean MAE=0.11, rank 24/24; pooled MAE=0.122.

## C. Block ablation

Evidence = depth/artifact quality; Coherence = detection+SAM form (regime-neutral).
Narrative: Coherence predicts; Evidence audits (cosmetic-fix anti-pattern).

| Variant | n_feat | MAE | Sp | MAE_a | MAE_a_cont | Rank | Alarm P/R | Note |
|---|---:|---:|---:|---:|---:|---|---|---|
| `C_Evidence` | 2 | 0.072 | 0.768 | 0.109 | 0.105 | 27/27 | 1.00/1.00 | depth_nan + retention |
| `C_Coherence` | 6 | 0.097 | 0.789 | 0.093 | 0.088 | 27/27 | 1.00/1.00 | fill/onto/gate/phase/y_std |
| `C_Evidence+Coherence` | 8 | 0.100 | 0.797 | 0.097 | 0.101 | 27/27 | 1.00/1.00 | full candidate |

## D. Leanness

| Variant | n_feat | MAE | Sp | MAE_a | MAE_a_cont | Rank | Alarm P/R | Note |
|---|---:|---:|---:|---:|---:|---|---|---|
| `D_lean5` | 5 | 0.094 | 0.808 | 0.103 | 0.108 | 27/27 | 1.00/1.00 | frozen v2 set |
| `D_candidate8` | 8 | 0.100 | 0.797 | 0.097 | 0.101 | 27/27 | 1.00/1.00 | full v2 candidate |
| `D_tier1_gate17` | 17 | 0.091 | 0.780 | 0.115 | 0.107 | 27/27 | 1.00/1.00 | 14 Tier-1 + 3 gate feats |

### Leave-one-out (lean-5)

| Variant | MAE | Sp | MAE_a_cont | Rank |
|---|---:|---:|---:|---|
| `D_loo_depth_nan_ratio` | 0.083 | 0.811 | 0.098 | 27/27 |
| `D_loo_det_row_gated` | 0.090 | 0.786 | 0.123 | 27/27 |
| `D_loo_det_row_residual_px` | 0.093 | 0.788 | 0.115 | 27/27 |
| `D_loo_sam_fill_rate` | 0.089 | 0.815 | 0.088 | 27/27 |
| `D_loo_sam_ontology_divergence` | 0.063 | 0.826 | 0.096 | 27/27 |

## Controls

### Permutation (within-family mIoU shuffle, 20 reps)

| Variant | real MAE | perm MAE | pass |
|---|---:|---:|---|
| `A_v2_lean_refit` | 0.122 | 0.291±0.016 | True |
| `B_pooled` | 0.122 | 0.291±0.016 | True |
| `C_Evidence+Coherence` | 0.123 | 0.293±0.017 | True |
| `D_lean5` | 0.122 | 0.291±0.016 | True |
| `D_tier1_gate17` | 0.089 | 0.277±0.023 | True |
| `A_v1_features_refit` | 0.120 | 0.285±0.014 | True |

### Alarm-threshold sensitivity (lean-5)

| Step | threshold | P | R | TP/FP/FN |
|---|---:|---:|---:|---|
| thr_minus_1q | 0.296 | 1.00 | 1.00 | 27/0/0 |
| thr_base | 0.430 | 1.00 | 1.00 | 27/0/0 |
| thr_plus_1q | 0.514 | 1.00 | 1.00 | 27/0/0 |

## Artifacts

- `bo-elegant/family/ablation_study.csv`
- `bo-elegant/family/ablation_study.json`
- `bo-elegant/ablation_harness_gate.md`
