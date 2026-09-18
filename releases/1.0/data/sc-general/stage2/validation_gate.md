# Stage-2 validation gate — FAIL

- deployment_arm: `pruned_lean`
- lean_features: `['correspondence_f1@15', 'sam_fill_rate', 'ring_count_error', 'depth_nan_ratio']`

| check | result |
|---|---|
| lolo_spearman_ge_0.678 | PASS |
| holdout_spearman_or_mae | FAIL |
| pair_rank_27_27 | PASS |
| alarm_some_tau_in_0.4_0.6 | PASS |
| lean_has_sc_general | PASS |
| lean_no_krow | PASS |

## Observed vs published (bayes)

- LOFO Spearman: 0.828 (pub 0.678)
- Holdout Spearman: 0.817 (pub 0.827; CI95 [0.7614306337576849, 0.8640407114259268])
- Holdout MAE: 0.1087 (pub 0.086)
- PairRank: 27/27
- Alarm @0.5: TP=27 FP=3 (preferred=no)
- Passing tau in [0.4,0.6]: [0.4, 0.41, 0.42, 0.43]

