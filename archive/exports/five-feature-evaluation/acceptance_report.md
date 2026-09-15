# Acceptance report — bo-bayes Bayesian exploration

- created_at: 2026-09-12T16:21:45.436838
- n_train: 120
- lean features: ['depth_nan_ratio', 'denoise_retained_ratio', 'sam_fill_rate', 'det_row_residual_px', 'det_row_gated']

## Hard constraints

- PoC panel identical: **PASS**
  - expected: `['1-4', '1-5', '2-2', '3-2', '3-4', '3-5', '4-1', '4-3', '4-4']`
  - observed: `['1-4', '1-5', '2-2', '3-2', '3-4', '3-5', '4-1', '4-3', '4-4']`
  - missing: `[]`
  - extra: `[]`
- Alarm 27/27 TP, 0 FP at τ=0.5: **PASS** (TP=27/27, FP=0/27)

## Structural checks

- lean_best_or_near_lolo: **PASS**
- coherence_gt_evidence: **PASS**
- perm_pass: **PASS**

## Drift vs published Sobol-only numbers

| Metric | Published | Bayes | Δ |
|---|---:|---:|---:|
| Train MAE | 0.129 | 0.098 | -0.031 |
| Train Spearman | 0.853 | 0.877 | +0.024 |
| LOLO MAE | 0.156 | 0.143 | -0.013 |
| LOLO Spearman | 0.717 | 0.678 | -0.039 |
| Holdout MAE | 0.071 | 0.086 | +0.015 |
| Holdout Spearman | 0.848 | 0.827 | -0.021 |
| Intercept | 0.478 | 0.350 | -0.128 |

### Coefficients (z-scored)

| Feature | Published | Bayes | Δ |
|---|---:|---:|---:|
| depth_nan_ratio | -0.174 | -0.078 | +0.096 |
| denoise_retained_ratio | -0.392 | -0.059 | +0.333 |
| sam_fill_rate | 0.471 | 0.187 | -0.284 |
| det_row_residual_px | -0.112 | -0.108 | +0.004 |
| det_row_gated | 0.127 | 0.102 | -0.025 |

## Ablation LOLO Spearman

- Evidence: 0.597
- Coherence: 0.726
- Evidence+Coherence: 0.614
- Lean: 0.678

## Overall: **ACCEPT**
