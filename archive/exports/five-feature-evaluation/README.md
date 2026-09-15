# Five-feature evaluation exports

Frozen lean set: `depth_nan_ratio`, `denoise_retained_ratio`, `sam_fill_rate`,
`det_row_residual_px`, `det_row_gated` (from `bo/bayes`).

## Files

| File | Contents |
|---|---|
| `54_stress_test_holdout_scores.csv` | 54 paired stress-test runs (27 anchor + 27 bad): mIoU, proxy, features |
| `54_stress_test_clustered_stats.json` | Holdout MAE, subset-bootstrap Spearman + 95% CI, Wilcoxon vs per-family |
| `27_panel_baseline_and_refined.csv` | All 27 holdout subsets: baseline vs selected (9 refined, 18 kept) |
| `five_feature_models.json` | Frozen Ridge package |
| `acceptance_report.md` | Bayes acceptance / drift vs earlier Sobol numbers |
| `refinement_report.md` | Proxy-scale refinement campaign summary |

## Quick checks (verified on copy)

- Stress-test: MAE **0.086**, Spearman **0.827**, CI95 **[0.749, 0.887]**, PairRank **27/27**, alarm@0.5 **TP 27 / FP 0**
- 27-panel: baseline mean mIoU **0.722** → selected **0.757**; nine refined **0.569 → 0.675**
