# Validation gate — bo-full-stage

- n_holdout = 54
- lean features = ['depth_nan_ratio', 'denoise_retained_ratio', 'sam_fill_rate', 'det_row_residual_px', 'det_row_gated']
- alarm τ = 0.495

## Metrics

| Metric | full-stage | v2 |
|---|---:|---:|
| Spearman | 0.848 | 0.810 |
| MAE | 0.071 | 0.071 |
| MAE complex | 0.076 | 0.080 |
| MAE continuous | 0.064 | 0.066 |
| MAE staggered | 0.071 | 0.067 |

Flagging: TP=27/27, FP=0/27

## 4-3 residual response

proxy(residual=23.2cm)=0.630, proxy(5.2cm)=0.630, Δ=+0.000 (FAIL rises when residual drops)

## Checks

- PASS: holdout Spearman ≥ v2 (0.848 vs v2 0.810)
- PASS: holdout MAE not much worse (0.071 vs v2 0.071)
- PASS: known-bad flagging recall (27/27)
- PASS: anchor false alarms limited (0/27)

**Overall: PASS**
