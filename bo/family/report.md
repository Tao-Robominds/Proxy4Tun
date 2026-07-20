# Per-family mIoU proxy — held-out evaluation

_Generated 2026-07-20T08:48:47_

## Design

- Feature set: **B1+B2lean** (GT-free).
- Train within family; test on held-out sub-tunnels.
- Per held-out subset: sibling **anchor** config + one frozen **known-bad** config.
- Training cases: t1&2=`1-1+2-1`, t3=`3-1-1`, t4&5=`4-1+5-1`.

## Training (within-family)

| Family | n | train MAE | pooled MAE | pooled Spearman | alarm thr | low-mIoU floor |
|---|---:|---:|---:|---:|---:|---:|
| t1&2 | 80 | 0.046 | 0.075 | 0.814 | 0.694 | 0.665 |
| t3 | 35 | 0.188 | 0.188 | 0.725 | 0.346 | 0.102 |
| t4&5 | 73 | 0.017 | 0.086 | 0.932 | 0.564 | 0.596 |

### Leave-one-tunnel-out

- **t1&2** hold `1-1`: MAE=0.076, Spearman=0.705 (n_test=40)
- **t1&2** hold `2-1`: MAE=0.074, Spearman=0.721 (n_test=40)
- **t3**: single-tunnel training (no LOTO).
- **t4&5** hold `4-1`: MAE=0.059, Spearman=0.800 (n_test=40)
- **t4&5** hold `5-1`: MAE=0.119, Spearman=0.928 (n_test=33)

## Known-bad configs

| Family | Source trial | Training mIoU | Δ vs min sibling anchor |
|---|---|---:|---:|
| t1&2 | `2-1/2-1-t002` | 0.032 | 0.755 |
| t3 | `3-1-1/3-1-1-t025` | 0.043 | 0.807 |
| t4&5 | `4-1/4-1-t009` | 0.036 | 0.599 |

## Held-out calibration

| Family | config | n | MAE | Spearman | mean mIoU | mean proxy |
|---|---|---:|---:|---:|---:|---:|
| t1&2 | anchor | 8 | 0.076 | 0.167 | 0.781 | 0.804 |
| t1&2 | bad | 8 | 0.049 | -0.843 | 0.035 | 0.017 |
| t3 | anchor | 2 | 0.298 | 1.000 | 0.722 | 0.424 |
| t3 | bad | 2 | 0.082 | 1.000 | 0.028 | 0.111 |
| t4&5 | anchor | 15 | 0.094 | 0.717 | 0.577 | 0.625 |
| t4&5 | bad | 15 | 0.117 | 0.289 | 0.090 | -0.007 |

Overall MAE (ok runs): **0.099** (n=50).

## Alarm confusion (split by config)

| Family | config | TP | FP | TN | FN | precision | recall |
|---|---|---:|---:|---:|---:|---:|---:|
| t1&2 | anchor | 0 | 0 | 7 | 1 | — | 0.00 |
| t1&2 | bad | 8 | 0 | 0 | 0 | 1.00 | 1.00 |
| t3 | anchor | 0 | 0 | 2 | 0 | — | — |
| t3 | bad | 2 | 0 | 0 | 0 | 1.00 | 1.00 |
| t4&5 | anchor | 5 | 1 | 9 | 0 | 0.83 | 1.00 |
| t4&5 | bad | 15 | 0 | 0 | 0 | 1.00 | 1.00 |

Notable misclassifications:
- **FN** `1-5`/anchor: mIoU=0.490 below floor but proxy=0.784 (no alarm).
- **FP** `4-6`/anchor: mIoU=0.611 above floor but proxy=0.479 (alarm).

## Per-tunnel ranking (anchor vs bad)

Proxy preserves mIoU order on **25/25** pairs (accuracy=1.00).

| Subset | Family | rank_ok | anchor mIoU | bad mIoU | anchor proxy | bad proxy |
|---|---|---|---:|---:|---:|---:|
| 1-2 | t1&2 | True | 0.817 | 0.037 | 0.766 | -0.079 |
| 1-3 | t1&2 | True | 0.745 | 0.037 | 0.823 | -0.059 |
| 1-4 | t1&2 | True | 0.828 | 0.035 | 0.789 | 0.015 |
| 1-5 | t1&2 | True | 0.490 | 0.038 | 0.784 | 0.012 |
| 2-2 | t1&2 | True | 0.845 | 0.032 | 0.808 | 0.086 |
| 2-3 | t1&2 | True | 0.796 | 0.034 | 0.823 | 0.074 |
| 2-4 | t1&2 | True | 0.833 | 0.034 | 0.827 | 0.063 |
| 2-5 | t1&2 | True | 0.892 | 0.033 | 0.815 | 0.025 |
| 3-1-2 | t3 | True | 0.638 | 0.027 | 0.372 | 0.104 |
| 3-1-3 | t3 | True | 0.806 | 0.030 | 0.476 | 0.117 |
| 4-10 | t4&5 | True | 0.247 | 0.094 | 0.486 | 0.080 |
| 4-2 | t4&5 | True | 0.725 | 0.150 | 0.756 | -0.001 |
| 4-3 | t4&5 | True | 0.279 | 0.120 | 0.503 | 0.023 |
| 4-4 | t4&5 | True | 0.671 | 0.136 | 0.789 | -0.056 |
| 4-5 | t4&5 | True | 0.786 | 0.042 | 0.698 | -0.039 |
| 4-6 | t4&5 | True | 0.611 | 0.114 | 0.479 | 0.095 |
| 4-7 | t4&5 | True | 0.815 | 0.075 | 0.781 | -0.079 |
| 4-8 | t4&5 | True | 0.256 | 0.220 | 0.368 | 0.150 |
| 4-9 | t4&5 | True | 0.078 | 0.088 | 0.192 | 0.213 |
| 5-2 | t4&5 | True | 0.789 | 0.039 | 0.722 | 0.066 |
| 5-3 | t4&5 | True | 0.759 | 0.058 | 0.776 | 0.023 |
| 5-4 | t4&5 | True | 0.760 | 0.048 | 0.803 | -0.063 |
| 5-5 | t4&5 | True | 0.781 | 0.040 | 0.762 | 0.003 |
| 5-6 | t4&5 | True | 0.671 | 0.074 | 0.733 | 0.004 |
| 5-7 | t4&5 | True | 0.423 | 0.049 | 0.531 | -0.530 |

## Per-subset scores

| Subset | Family | config | status | mIoU | proxy | |err| | alarm | low? |
|---|---|---|---|---:|---:|---:|---|---|
| 1-2 | t1&2 | anchor | ok | 0.817 | 0.766 | 0.051 | False | False |
| 1-2 | t1&2 | bad | ok | 0.037 | -0.079 | 0.116 | True | True |
| 1-3 | t1&2 | anchor | ok | 0.745 | 0.823 | 0.078 | False | False |
| 1-3 | t1&2 | bad | ok | 0.037 | -0.059 | 0.096 | True | True |
| 1-4 | t1&2 | anchor | ok | 0.828 | 0.789 | 0.039 | False | False |
| 1-4 | t1&2 | bad | ok | 0.035 | 0.015 | 0.020 | True | True |
| 1-5 | t1&2 | anchor | ok | 0.490 | 0.784 | 0.294 | False | True |
| 1-5 | t1&2 | bad | ok | 0.038 | 0.012 | 0.026 | True | True |
| 2-2 | t1&2 | anchor | ok | 0.845 | 0.808 | 0.037 | False | False |
| 2-2 | t1&2 | bad | ok | 0.032 | 0.086 | 0.054 | True | True |
| 2-3 | t1&2 | anchor | ok | 0.796 | 0.823 | 0.027 | False | False |
| 2-3 | t1&2 | bad | ok | 0.034 | 0.074 | 0.040 | True | True |
| 2-4 | t1&2 | anchor | ok | 0.833 | 0.827 | 0.006 | False | False |
| 2-4 | t1&2 | bad | ok | 0.034 | 0.063 | 0.029 | True | True |
| 2-5 | t1&2 | anchor | ok | 0.892 | 0.815 | 0.077 | False | False |
| 2-5 | t1&2 | bad | ok | 0.033 | 0.025 | 0.008 | True | True |
| 3-1-2 | t3 | anchor | ok | 0.638 | 0.372 | 0.266 | False | False |
| 3-1-2 | t3 | bad | ok | 0.027 | 0.104 | 0.077 | True | True |
| 3-1-3 | t3 | anchor | ok | 0.806 | 0.476 | 0.330 | False | False |
| 3-1-3 | t3 | bad | ok | 0.030 | 0.117 | 0.087 | True | True |
| 4-10 | t4&5 | anchor | ok | 0.247 | 0.486 | 0.239 | True | True |
| 4-10 | t4&5 | bad | ok | 0.094 | 0.080 | 0.014 | True | True |
| 4-2 | t4&5 | anchor | ok | 0.725 | 0.756 | 0.031 | False | False |
| 4-2 | t4&5 | bad | ok | 0.150 | -0.001 | 0.151 | True | True |
| 4-3 | t4&5 | anchor | ok | 0.279 | 0.503 | 0.224 | True | True |
| 4-3 | t4&5 | bad | ok | 0.120 | 0.023 | 0.097 | True | True |
| 4-4 | t4&5 | anchor | ok | 0.671 | 0.789 | 0.118 | False | False |
| 4-4 | t4&5 | bad | ok | 0.136 | -0.056 | 0.192 | True | True |
| 4-5 | t4&5 | anchor | ok | 0.786 | 0.698 | 0.088 | False | False |
| 4-5 | t4&5 | bad | ok | 0.042 | -0.039 | 0.081 | True | True |
| 4-6 | t4&5 | anchor | ok | 0.611 | 0.479 | 0.132 | True | False |
| 4-6 | t4&5 | bad | ok | 0.114 | 0.095 | 0.019 | True | True |
| 4-7 | t4&5 | anchor | ok | 0.815 | 0.781 | 0.034 | False | False |
| 4-7 | t4&5 | bad | ok | 0.075 | -0.079 | 0.154 | True | True |
| 4-8 | t4&5 | anchor | ok | 0.256 | 0.368 | 0.112 | True | True |
| 4-8 | t4&5 | bad | ok | 0.220 | 0.150 | 0.070 | True | True |
| 4-9 | t4&5 | anchor | ok | 0.078 | 0.192 | 0.114 | True | True |
| 4-9 | t4&5 | bad | ok | 0.088 | 0.213 | 0.125 | True | True |
| 5-2 | t4&5 | anchor | ok | 0.789 | 0.722 | 0.067 | False | False |
| 5-2 | t4&5 | bad | ok | 0.039 | 0.066 | 0.027 | True | True |
| 5-3 | t4&5 | anchor | ok | 0.759 | 0.776 | 0.017 | False | False |
| 5-3 | t4&5 | bad | ok | 0.058 | 0.023 | 0.035 | True | True |
| 5-4 | t4&5 | anchor | ok | 0.760 | 0.803 | 0.043 | False | False |
| 5-4 | t4&5 | bad | ok | 0.048 | -0.063 | 0.111 | True | True |
| 5-5 | t4&5 | anchor | ok | 0.781 | 0.762 | 0.019 | False | False |
| 5-5 | t4&5 | bad | ok | 0.040 | 0.003 | 0.037 | True | True |
| 5-6 | t4&5 | anchor | ok | 0.671 | 0.733 | 0.062 | False | False |
| 5-6 | t4&5 | bad | ok | 0.074 | 0.004 | 0.070 | True | True |
| 5-7 | t4&5 | anchor | ok | 0.423 | 0.531 | 0.108 | True | True |
| 5-7 | t4&5 | bad | ok | 0.049 | -0.530 | 0.579 | True | True |

## Limitations

- Only two quality levels per held-out tunnel (anchor + one known-bad); not a full ranking study.
- t3 trained on a single tunnel (`3-1-1`); 3-1-1 geometry params (`segment_order`, `h_ring_sign`) may not transfer — alarm should catch that.
- Known-bad configs are frozen from training-tunnel BO archives; transfer of *that specific failure mode* is assumed.
- Sibling-anchor params are the honest deployment baseline, not per-tunnel retuning.

## Confidence

**Moderate** based on holdout MAE=0.099, ranking accuracy=1.0, and the single-tunnel t3 caveat.

