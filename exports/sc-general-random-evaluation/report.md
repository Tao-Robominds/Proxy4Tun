# Selector policies and cluster-bootstrap CIs

Panel: 22 proxy-admitted cases. Bootstrap: 100000 parent-tunnel resamples, seed 0.

## Panel means

| arm | start | selected | mean Δ | median Δ | up/same/down | worst |
|---|---:|---:|---:|---:|---|---:|
| fable_fresh | 0.738 | 0.751 | +0.013 | +0.000 | 9/4/9 | -0.195 |
| gpt56 | 0.738 | 0.760 | +0.022 | +0.000 | 7/7/8 | -0.091 |
| gemini38 | 0.738 | 0.759 | +0.021 | +0.003 | 12/7/3 | -0.024 |
| random | 0.738 | 0.752 | +0.014 | +0.000 | 8/8/6 | -0.117 |

## Selector policies (mean mIoU)

| arm | start | random round | round1 | max-proxy | monotone | oracle | recovery |
|---|---:|---:|---:|---:|---:|---:|---:|
| fable_fresh | 0.738 | 0.734 | 0.714 | 0.751 | 0.751 | 0.765 | 49% |
| gpt56 | 0.738 | 0.706 | 0.683 | 0.760 | 0.760 | 0.770 | 69% |
| gemini38 | 0.738 | 0.715 | 0.692 | 0.757 | 0.759 | 0.765 | 78% |
| random | 0.738 | 0.535 | 0.508 | 0.752 | 0.752 | 0.769 | 47% |

## Cluster-bootstrap 95% CI (mean Δ)

- **fable_fresh**: +0.013 [-0.017, +0.052]
- **gpt56**: +0.022 [-0.014, +0.077]
- **gemini38**: +0.021 [+0.009, +0.044]
- **random**: +0.014 [-0.028, +0.078]

## Pairwise differences

- **fable_fresh - gpt56**: -0.009 [-0.033, +0.025]
- **fable_fresh - gemini38**: -0.008 [-0.033, +0.019]
- **fable_fresh - random**: -0.001 [-0.038, +0.043]
- **gpt56 - gemini38**: +0.001 [-0.049, +0.048]
- **gpt56 - random**: +0.008 [-0.010, +0.022]
- **gemini38 - random**: +0.007 [-0.049, +0.066]
