# BO-unified: unified proxy strategy

_Generated 2026-07-21T12:18:57_

## Design

- Pipeline: **anchors/unified** (staggered / continuous / complex via `parameters_family.json`).
- Feature set: **B1+B2lean** (GT-free).
- Training: reused historical `data/bo/<case>-bo-proxy` trials (no fresh BO campaigns).
- Proxies: **per-family** RidgeCV **and** one **pooled cross-family** RidgeCV (+ family one-hot).
- Holdouts: **24** scored subsets. Includes new T3 gaps `3-6`…`3-10` (rings 36–45; 1-ring overlap with `3-1`).
- Orientation / seed knobs frozen in unified params; BO overlays touch stages 2–6 only.
- Feature-set ablation (B1 / B2lean / one-hot / phase): [`ablation.md`](ablation.md).

## Training data provenance

- Rows: **225** from `data/bo/<case>-bo-proxy/manifest.json`.
- Justification: Unified pipeline passed parity gates vs the anchors these trials ran on (|ΔmIoU| ≤ 0.02 per anchors/unified/verification.md), so (features → mIoU) pairs remain valid proxy training data.
- Counts: `{'1-1': 40, '2-1': 40, '3-1': 35, '3-2': 37, '4-1': 40, '5-1': 33}`

## Training metrics

| Model | n | train MAE | Spearman | alarm thr | low floor |
|---|---:|---:|---:|---:|---:|
| family `t1&2` | 80 | 0.046 | 0.787 | 0.562 | 0.665 |
| family `t3` | 72 | 0.125 | 0.774 | 0.160 | 0.147 |
| family `t4&5` | 73 | 0.017 | 0.946 | 0.460 | 0.596 |
| **unified (pooled)** | 225 | 0.076 | 0.885 | 0.465 | 0.335 |

## Known-bad configs

| Family | Source trial | Training mIoU | Δ vs min sibling anchor |
|---|---|---:|---:|
| t1&2 | `2-1/2-1-t002` | 0.032 | 0.755 |
| t3 | `3-2/3-2-t029` | 0.027 | 0.604 |
| t4&5 | `4-1/4-1-t009` | 0.036 | 0.599 |

## Held-out calibration (family vs unified proxy)

| Family | config | n | MAE_family | MAE_unified | mean mIoU |
|---|---|---:|---:|---:|---:|
| t1&2 | anchor | 8 | 0.095 | 0.104 | 0.737 |
| t1&2 | bad | 8 | 0.066 | 0.091 | 0.046 |
| t3 | anchor | 8 | 0.295 | 0.337 | 0.762 |
| t3 | bad | 8 | 0.036 | 0.035 | 0.039 |
| t4&5 | anchor | 8 | 0.074 | 0.085 | 0.680 |
| t4&5 | bad | 8 | 0.097 | 0.073 | 0.046 |

Overall MAE — family: **0.110**, unified: **0.121** (n=48).
Old `bo/family` baseline to beat: pooled MAE **0.099**, ranking **26/26** (different holdout set; this run uses 24 available subsets).

## Ranking accuracy (anchor vs bad)

- Per-family proxy: **24/24** (acc=1.00)
- Unified proxy: **24/24** (acc=1.00)

## Validation gates

| Case | Kind | mIoU | Passed | Evidence |
|---|---|---:|---|---|
| 1-1 | train_parity | 0.8 | True | `gate_1-1.json` |
| 1-2 | holdout | 0.821 | True | `gate_1-2.json` |
| 3-1 | train_parity | 0.85 | True | `gate_3-1.json` |
| 3-10 | holdout | 0.853 | True | `gate_3-10.json` |
| 3-6 | holdout | 0.836 | True | `gate_3-6.json` |
| 4-3 | holdout | 0.516 | True | `gate_4-3.json` |
| 5-1 | train_parity | 0.818 | True | `gate_5-1.json` |

## Per-subset scores

| Subset | Family | config | status | mIoU | proxy_f | proxy_u | |err_f| | |err_u| |
|---|---|---|---|---:|---:|---:|---:|---:|
| 1-2 | t1&2 | anchor | ok | 0.821 | 0.767 | 0.767 | 0.054 | 0.054 |
| 1-2 | t1&2 | bad | ok | 0.037 | -0.096 | 0.058 | 0.133 | 0.021 |
| 1-3 | t1&2 | anchor | ok | 0.779 | 0.837 | 0.822 | 0.058 | 0.043 |
| 1-3 | t1&2 | bad | ok | 0.121 | 0.213 | 0.261 | 0.092 | 0.140 |
| 1-4 | t1&2 | anchor | ok | 0.556 | 0.768 | 0.661 | 0.212 | 0.105 |
| 1-4 | t1&2 | bad | ok | 0.041 | -0.122 | -0.098 | 0.163 | 0.139 |
| 1-5 | t1&2 | anchor | ok | 0.549 | 0.745 | 0.776 | 0.196 | 0.227 |
| 1-5 | t1&2 | bad | ok | 0.037 | 0.041 | 0.083 | 0.004 | 0.046 |
| 2-2 | t1&2 | anchor | ok | 0.673 | 0.770 | 0.815 | 0.097 | 0.142 |
| 2-2 | t1&2 | bad | ok | 0.032 | 0.103 | 0.138 | 0.071 | 0.106 |
| 2-3 | t1&2 | anchor | ok | 0.800 | 0.794 | 0.759 | 0.006 | 0.041 |
| 2-3 | t1&2 | bad | ok | 0.034 | 0.074 | 0.140 | 0.040 | 0.106 |
| 2-4 | t1&2 | anchor | ok | 0.835 | 0.823 | 0.759 | 0.012 | 0.076 |
| 2-4 | t1&2 | bad | ok | 0.033 | 0.011 | 0.028 | 0.022 | 0.005 |
| 2-5 | t1&2 | anchor | ok | 0.886 | 0.760 | 0.746 | 0.126 | 0.140 |
| 2-5 | t1&2 | bad | ok | 0.033 | 0.036 | 0.196 | 0.003 | 0.163 |
| 3-10 | t3 | anchor | ok | 0.853 | 0.495 | 0.419 | 0.358 | 0.434 |
| 3-10 | t3 | bad | ok | 0.040 | 0.054 | 0.136 | 0.014 | 0.096 |
| 3-3 | t3 | anchor | ok | 0.808 | 0.576 | 0.518 | 0.232 | 0.290 |
| 3-3 | t3 | bad | ok | 0.031 | 0.069 | 0.066 | 0.038 | 0.035 |
| 3-4 | t3 | anchor | ok | 0.622 | 0.382 | 0.383 | 0.240 | 0.239 |
| 3-4 | t3 | bad | ok | 0.044 | 0.085 | 0.037 | 0.041 | 0.007 |
| 3-5 | t3 | anchor | ok | 0.588 | 0.352 | 0.360 | 0.236 | 0.228 |
| 3-5 | t3 | bad | ok | 0.038 | 0.031 | 0.120 | 0.007 | 0.082 |
| 3-6 | t3 | anchor | ok | 0.836 | 0.421 | 0.324 | 0.415 | 0.512 |
| 3-6 | t3 | bad | ok | 0.048 | -0.009 | 0.056 | 0.057 | 0.008 |
| 3-7 | t3 | anchor | ok | 0.845 | 0.581 | 0.528 | 0.264 | 0.317 |
| 3-7 | t3 | bad | ok | 0.031 | 0.111 | 0.072 | 0.080 | 0.041 |
| 3-8 | t3 | anchor | ok | 0.723 | 0.410 | 0.416 | 0.313 | 0.307 |
| 3-8 | t3 | bad | ok | 0.041 | 0.018 | 0.042 | 0.023 | 0.001 |
| 3-9 | t3 | anchor | ok | 0.820 | 0.519 | 0.452 | 0.301 | 0.368 |
| 3-9 | t3 | bad | ok | 0.037 | 0.061 | 0.050 | 0.024 | 0.013 |
| 4-2 | t4&5 | anchor | ok | 0.734 | 0.627 | 0.687 | 0.107 | 0.047 |
| 4-2 | t4&5 | bad | ok | 0.042 | -0.019 | -0.064 | 0.061 | 0.106 |
| 4-3 | t4&5 | anchor | ok | 0.516 | 0.621 | 0.682 | 0.105 | 0.166 |
| 4-3 | t4&5 | bad | ok | 0.042 | -0.100 | -0.047 | 0.142 | 0.089 |
| 4-4 | t4&5 | anchor | ok | 0.347 | 0.449 | 0.618 | 0.102 | 0.271 |
| 4-4 | t4&5 | bad | ok | 0.056 | -0.225 | 0.001 | 0.281 | 0.055 |
| 4-5 | t4&5 | anchor | ok | 0.750 | 0.622 | 0.688 | 0.128 | 0.062 |
| 4-5 | t4&5 | bad | ok | 0.042 | -0.043 | -0.060 | 0.085 | 0.102 |
| 5-2 | t4&5 | anchor | ok | 0.793 | 0.717 | 0.709 | 0.076 | 0.084 |
| 5-2 | t4&5 | bad | ok | 0.040 | 0.061 | -0.008 | 0.021 | 0.048 |
| 5-3 | t4&5 | anchor | ok | 0.762 | 0.778 | 0.725 | 0.016 | 0.037 |
| 5-3 | t4&5 | bad | ok | 0.057 | 0.033 | 0.043 | 0.024 | 0.014 |
| 5-4 | t4&5 | anchor | ok | 0.760 | 0.803 | 0.764 | 0.043 | 0.004 |
| 5-4 | t4&5 | bad | ok | 0.048 | -0.067 | -0.026 | 0.115 | 0.074 |
| 5-5 | t4&5 | anchor | ok | 0.775 | 0.763 | 0.780 | 0.012 | 0.005 |
| 5-5 | t4&5 | bad | ok | 0.040 | -0.001 | -0.059 | 0.041 | 0.099 |


## Notes

- **`3-10` redefined**: rings **36–45** (dense mid-scan; 1-ring overlap with `3-1` at ring 36). Replaces hung thin-tail window 107–116. Anchor mIoU=0.853, bad mIoU=0.040.
## Artifacts

- Code: `bo-unified/` (historical `bo/` untouched)
- Outputs: `data/bo-unified/`
- Models: `bo-unified/family/models.json`
- Bad configs: `bo-unified/family/bad_configs.json`
- Scores: `bo-unified/family/holdout_scores.csv`

