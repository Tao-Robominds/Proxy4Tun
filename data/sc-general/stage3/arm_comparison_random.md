# Stage 3 arm comparison — SC-general (with random-overlay control)

Generated: 2026-09-16T00:15:56.474654

Arms: fable / gpt56 / gemini38 / random (k-matched uniform bounded overlays).
Selector and proxy are shared and GT-blind.

## Per-case table (22-case proxy-only panel)

| subset | family | a_mIoU | fable | Δf | gpt56 | Δg | gemini38 | Δm | random | Δr |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 4-3 | complex | 0.516 | 0.544 | 0.028 | 0.515 | -0.001 | 0.516 | 0.000 | 0.516 | 0.000 |
| 4-2 | complex | 0.734 | 0.773 | 0.039 | 0.643 | -0.091 | 0.744 | 0.010 | 0.738 | 0.004 |
| 4-1 | complex | 0.635 | 0.653 | 0.018 | 0.652 | 0.017 | 0.658 | 0.023 | 0.660 | 0.025 |
| 4-5 | complex | 0.750 | 0.771 | 0.021 | 0.777 | 0.027 | 0.780 | 0.030 | 0.750 | 0.000 |
| 5-5 | complex | 0.775 | 0.781 | 0.006 | 0.771 | -0.004 | 0.793 | 0.018 | 0.794 | 0.019 |
| 5-3 | complex | 0.762 | 0.762 | 0.000 | 0.762 | 0.000 | 0.762 | 0.000 | 0.762 | 0.000 |
| 5-2 | complex | 0.793 | 0.781 | -0.012 | 0.792 | -0.001 | 0.782 | -0.011 | 0.793 | 0.000 |
| 5-4 | complex | 0.760 | 0.760 | 0.000 | 0.759 | -0.001 | 0.760 | 0.000 | 0.752 | -0.008 |
| 3-4 | continuous | 0.622 | 0.622 | 0.000 | 0.627 | 0.005 | 0.692 | 0.070 | 0.622 | 0.000 |
| 3-3 | continuous | 0.808 | 0.808 | 0.000 | 0.806 | -0.002 | 0.808 | 0.000 | 0.691 | -0.117 |
| 3-7 | continuous | 0.845 | 0.845 | 0.000 | 0.845 | 0.000 | 0.845 | 0.000 | 0.814 | -0.031 |
| 3-8 | continuous | 0.723 | 0.717 | -0.006 | 0.723 | 0.000 | 0.728 | 0.005 | 0.723 | 0.000 |
| 3-10 | continuous | 0.853 | 0.853 | 0.000 | 0.853 | 0.000 | 0.854 | 0.001 | 0.853 | 0.000 |
| 3-9 | continuous | 0.820 | 0.820 | 0.000 | 0.820 | 0.000 | 0.817 | -0.003 | 0.820 | 0.000 |
| 3-6 | continuous | 0.836 | 0.835 | -0.001 | 0.837 | 0.001 | 0.841 | 0.005 | 0.805 | -0.031 |
| 1-3 | staggered | 0.779 | 0.825 | 0.046 | 0.780 | 0.001 | 0.867 | 0.088 | 0.786 | 0.007 |
| 1-5 | staggered | 0.549 | 0.892 | 0.343 | 0.887 | 0.338 | 0.613 | 0.064 | 0.867 | 0.318 |
| 1-1 | staggered | 0.787 | 0.790 | 0.003 | 0.787 | 0.000 | 0.763 | -0.024 | 0.791 | 0.004 |
| 1-4 | staggered | 0.556 | 0.578 | 0.022 | 0.809 | 0.253 | 0.556 | 0.000 | 0.811 | 0.255 |
| 1-2 | staggered | 0.821 | 0.819 | -0.002 | 0.821 | 0.000 | 0.842 | 0.021 | 0.825 | 0.004 |
| 2-4 | staggered | 0.835 | 0.816 | -0.019 | 0.776 | -0.059 | 0.835 | 0.000 | 0.784 | -0.051 |
| 2-2 | staggered | 0.673 | 0.843 | 0.170 | 0.672 | -0.001 | 0.839 | 0.166 | 0.592 | -0.081 |

### Panel means

| arm | mean selected mIoU | mean ΔmIoU | n refined |
|---|---:|---:|---:|
| anchor | 0.738 | 0.000 | 0 |
| fable | 0.768 | 0.030 | 15 |
| gpt56 | 0.760 | 0.022 | 15 |
| gemini38 | 0.759 | 0.021 | 18 |
| random | 0.752 | 0.014 | 16 |

## Region comparison (random arm)

| region | n | n_refined | n↑ | n↓ | mean a_mIoU | mean s_mIoU | Δmean | frac↑ |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| A: manuscript PoC (proxy∈[0.5,0.7] ∩ GT∈[0.5,0.7]) | 6 | 4 | 3 | 1 | 0.592 | 0.678 | 0.086 | 0.50 |
| B: proxy refine ∩ GT-good (proxy∈[0.5,0.7] ∩ GT≥0.7) | 16 | 12 | 5 | 5 | 0.793 | 0.780 | -0.013 | 0.31 |
| C: proxy refine ∩ GT-low (proxy∈[0.5,0.7] ∩ GT<0.5) | 0 | — | — | — | — | — | — | — |
| D: all label-free refine panel (proxy∈[0.5,0.7]) | 22 | 16 | 8 | 6 | 0.738 | 0.752 | 0.014 | 0.36 |
| E: mid-proxy / mid-GT tight (proxy∈[0.55,0.65] ∩ GT∈[0.5,0.7]) | 3 | 3 | 3 | 0 | 0.580 | 0.779 | 0.199 | 1.00 |
| F: high-proxy edge of band (proxy∈[0.65,0.7]) | 6 | 6 | 0 | 4 | 0.776 | 0.748 | -0.028 | 0.00 |
| G: low-proxy edge of band (proxy∈[0.5,0.55]) | 5 | 3 | 1 | 2 | 0.705 | 0.676 | -0.029 | 0.20 |
| H: reject band (proxy<0.5) — not refined | 3 | 0 | 0 | 0 | 0.522 | 0.522 | 0.000 | 0.00 |
| I: accept band (proxy≥0.7) — not refined | 2 | 0 | 0 | 0 | 0.843 | 0.843 | 0.000 | 0.00 |
| J: paper nine (legacy definition) | 9 | 4 | 3 | 1 | 0.569 | 0.626 | 0.057 | 0.33 |
| K: paper nine ∩ in this run's panel | 6 | 4 | 3 | 1 | 0.592 | 0.678 | 0.086 | 0.50 |

## Artifacts

- Random selections: `/home/boringtao/Projects/Proxy4Tun/data/sc-general/stage3/selections-random/`
- Random report: `/home/boringtao/Projects/Proxy4Tun/data/sc-general/stage3/report_random.md`
- Region CSV: `/home/boringtao/Projects/Proxy4Tun/data/sc-general/stage3/region_comparison_random.csv`
- Campaign: `/home/boringtao/Projects/Proxy4Tun/data/sc-general/stage3/campaign_random.md`

