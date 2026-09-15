# Single-instance gate — per-family refit

- Family: `staggered` (representative of 40-row family fit)
- Command: `./venv/bin/python bo/full_stage/per_family_refit.py --gate`
- n_train=40, n_holdout=18
- lean features: ['depth_nan_ratio', 'denoise_retained_ratio', 'sam_fill_rate', 'det_row_residual_px', 'det_row_gated']

## Metrics

| Metric | Value |
|---|---:|
| MAE | 0.061 |
| Spearman | 0.720 |
| Rank (anchor>bad) | 9/9 |
| Alarm P/R | 1.00/1.00 (TP=9 FP=0 FN=0) |

## Pass criteria

- PASS: finite_mae
- PASS: rank_perfect_or_near
- PASS: n_train_40

**Overall: PASS**
