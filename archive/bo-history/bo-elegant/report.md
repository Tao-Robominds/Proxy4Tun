# bo-elegant report — 3-anchor unified lean proxy

_Generated 2026-07-23T12:45:03_

## Design

- Train anchors: `2-1, 3-1, 5-1` (120 archived trials).
- Selected feature set: **loo_sam_ring_completeness+pruned** → `['depth_nan_ratio', 'denoise_retained_ratio', 'det_real_detection_ratio', 'sam_fill_rate']`.
- Taxonomy: Evidence = artifact/depth quality; Coherence = detection+segmentation form.
- One pooled RidgeCV (no family one-hot).

### Dropped up front (prior lessons)

- `det_real_detection_ratio`: regime-confounded under uniform_k_snap: healthy continuous runs rewrite Types to propagated so ratio=0 even when k_row_gate proves real anchors; docks every continuous holdout by ~0.18 proxy points
- `depth_outlier_ratio`: permutation-control failure of full B2 (family-conditional)
- `det_fallback_ratio`: exact complement of det_real_detection_ratio; keep diagnostic only
- `det_midpoint_ratio`: regime-constant / near-zero coef in pooled model
- `det_n_points`: regime-constant / near-zero coef
- `det_ring_count_error`: near-zero coef everywhere
- `det_x_spacing_cv`: near-zero coef everywhere
- `det_y_std`: sentinel 0 under all-propagated Types; replaced by det_row_y_std
- `sam_segment_size_cv`: near-zero coef everywhere
- `sam_ring_completeness`: redundant with sam_fill_rate in v1 ablation

### Frozen coefficients (standardized)

| Feature | Coef | Block |
|---|---:|---|
| `sam_fill_rate` | +0.1907 | Coherence |
| `det_real_detection_ratio` | +0.1198 | Evidence |
| `denoise_retained_ratio` | +0.0277 | Evidence |
| `depth_nan_ratio` | +0.0150 | Evidence |

- Train MAE=0.102, Spearman=0.815, α=1.778
- Alarm threshold=0.469, low-mIoU floor=0.364

### Mini-ablation (training / LOLO)

| Set | n | train MAE | train Sp | LOLO MAE | LOLO Sp |
|---|---:|---:|---:|---:|---:|
| `Evidence` | 3 | 0.108 | 0.806 | 0.138 | 0.741 |
| `Coherence` | 3 | 0.125 | 0.670 | 0.160 | 0.499 |
| `Evidence+Coherence` | 6 | 0.101 | 0.827 | 0.163 | 0.784 |
| `loo_sam_ring_completeness` ← selected | 5 | 0.101 | 0.828 | 0.179 | 0.630 |
| `loo_sam_ontology_divergence` | 5 | 0.102 | 0.818 | 0.155 | 0.785 |

### Permutation control

- Real train MAE **0.102** vs shuffled 0.291 ± 0.008 (n=20, pass=True).

## Holdout evaluation

- Scored runs: 54 (ok=54).
- Pooled MAE=0.112, Spearman=0.773, Pearson=0.917
- Anchor>bad ranking: **27/27** (acc=1.00)

### Per-family

| Family | n | MAE | Spearman | MAE_anchor | MAE_bad |
|---|---:|---:|---:|---:|---:|
| complex | 18 | 0.070 | 0.914 | 0.074 | 0.065 |
| continuous | 18 | 0.180 | 0.918 | 0.284 | 0.075 |
| staggered | 18 | 0.086 | 0.733 | 0.094 | 0.078 |

### Bad-flagging alarm

- Precision=0.87, Recall=0.96 (TP=27, FP=4, FN=1)
- Threshold=0.469 (low-mIoU floor on train=0.364)

## Artifacts

- `bo-elegant/family/models.json`
- `bo-elegant/family/ablation.json`
- `bo-elegant/family/holdout_scores.csv`
- `bo-elegant/registry.json`

---

# Proxy v2 — regime-neutral continuous fix

_Generated 2026-07-23T13:06:21_

## Root cause addressed

See `bo-elegant/t3_review.md`. Deployed `uniform_k_snap` rewrites Types to
`propagated`, forcing `det_real_detection_ratio=0` on every healthy continuous
run and docking the v1 proxy by ~0.18. v2 drops that feature and adds
`det_row_residual_px`, `det_row_y_std`, `phase_incoherence_deg`.

- Selected set: **loo_det_row_y_std+pruned** → `['sam_fill_rate', 'sam_ontology_divergence', 'det_row_residual_px', 'det_row_gated', 'depth_nan_ratio']`
- Train rows: 75 (`{'2-1': 14, '3-1': 40, '5-1': 21}`)
- Train MAE=0.112, Spearman=0.828
- Permutation: real 0.112 vs 0.286±0.013 (pass=True)

### Coefficients (standardized)

| Feature | Coef | Block |
|---|---:|---|
| `sam_fill_rate` | +0.3175 | Coherence |
| `det_row_residual_px` | -0.1479 | Coherence |
| `det_row_gated` | +0.1376 | Coherence |
| `depth_nan_ratio` | +0.0426 | Evidence |
| `sam_ontology_divergence` | +0.0243 | Coherence |

## Holdout v1 vs v2

| Metric | v1 | v2 |
|---|---:|---:|
| Pooled MAE | 0.112 | 0.071 |
| Spearman | 0.773 | 0.810 |
| Ranking | 27/27 | 27/27 |

### Per-family MAE_anchor

| Family | v1 MAE_a | v2 MAE_a |
|---|---:|---:|
| complex | 0.074 | 0.094 |
| continuous | 0.284 | 0.084 |
| staggered | 0.094 | 0.101 |

### v2 alarm: P=1.00 R=1.00 (TP=27, FP=0, FN=0)

### 3-6 gate: **PASS** (continuous MAE_anchor=0.084)

## Artifacts

- `bo-elegant/family/models_v2.json`
- `bo-elegant/family/holdout_scores_v2.csv`
- `bo-elegant/validation_gate_3-6.md`
- `bo-elegant/t3_review.md`
