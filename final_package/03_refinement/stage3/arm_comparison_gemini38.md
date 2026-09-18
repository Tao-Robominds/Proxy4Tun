# Stage 3 arm comparison — SC-general (with Gemini 3.8)

Generated: 2026-09-14T11:43:31.877090

## Arms

- **anchor**: frozen SC-general holdout anchors (no refinement).
- **scgen-det**: deterministic Stage-3 recipes (`run_campaign.propose`).
- **fable**: Fable-5.1 (Cursor agent, live) GT-blind-by-protocol proposals.
- **gpt56**: GPT-5.6 (fresh per-case agent) with sanitized packets.
- **gemini38**: Gemini 3.8 (fresh per-case agent, `model=inherit`) with sanitized packets and the same information barrier as GPT-5.6.

## Per-case table (22-case proxy-only panel)

| subset | family | a_proxy | a_mIoU | det | Δdet | fable | Δfable | gpt56 | Δgpt56 | gemini38 | Δgemini |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 4-3 | complex | 0.520 | 0.516 | 0.540 | 0.024 | 0.544 | 0.028 | 0.515 | -0.001 | 0.516 | 0.000 |
| 4-2 | complex | 0.543 | 0.734 | 0.773 | 0.039 | 0.773 | 0.039 | 0.643 | -0.091 | 0.744 | 0.010 |
| 4-1 | complex | 0.552 | 0.635 | 0.653 | 0.018 | 0.653 | 0.018 | 0.652 | 0.017 | 0.658 | 0.023 |
| 4-5 | complex | 0.609 | 0.750 | 0.775 | 0.025 | 0.771 | 0.021 | 0.777 | 0.027 | 0.780 | 0.030 |
| 5-5 | complex | 0.610 | 0.775 | 0.770 | -0.005 | 0.781 | 0.006 | 0.771 | -0.004 | 0.793 | 0.018 |
| 5-3 | complex | 0.681 | 0.762 | 0.762 | 0.000 | 0.762 | 0.000 | 0.762 | 0.000 | 0.762 | 0.000 |
| 5-2 | complex | 0.683 | 0.793 | 0.781 | -0.012 | 0.781 | -0.012 | 0.792 | -0.001 | 0.782 | -0.011 |
| 5-4 | complex | 0.692 | 0.760 | 0.760 | 0.000 | 0.760 | 0.000 | 0.759 | -0.001 | 0.760 | 0.000 |
| 3-4 | continuous | 0.520 | 0.622 | 0.622 | 0.000 | 0.622 | 0.000 | 0.627 | 0.005 | 0.692 | 0.070 |
| 3-3 | continuous | 0.522 | 0.808 | 0.808 | 0.000 | 0.808 | 0.000 | 0.806 | -0.002 | 0.808 | 0.000 |
| 3-7 | continuous | 0.540 | 0.845 | 0.845 | 0.000 | 0.845 | 0.000 | 0.845 | 0.000 | 0.845 | 0.000 |
| 3-8 | continuous | 0.561 | 0.723 | 0.723 | 0.000 | 0.717 | -0.006 | 0.723 | 0.000 | 0.728 | 0.005 |
| 3-10 | continuous | 0.589 | 0.853 | 0.853 | 0.000 | 0.853 | 0.000 | 0.853 | 0.000 | 0.854 | 0.001 |
| 3-9 | continuous | 0.641 | 0.820 | 0.820 | 0.000 | 0.820 | 0.000 | 0.820 | 0.000 | 0.817 | -0.003 |
| 3-6 | continuous | 0.681 | 0.836 | 0.835 | -0.001 | 0.835 | -0.001 | 0.837 | 0.001 | 0.841 | 0.005 |
| 1-3 | staggered | 0.550 | 0.779 | 0.825 | 0.046 | 0.825 | 0.046 | 0.780 | 0.001 | 0.867 | 0.088 |
| 1-5 | staggered | 0.555 | 0.549 | 0.693 | 0.144 | 0.892 | 0.343 | 0.887 | 0.338 | 0.613 | 0.064 |
| 1-1 | staggered | 0.607 | 0.787 | 0.784 | -0.003 | 0.790 | 0.003 | 0.787 | 0.000 | 0.763 | -0.024 |
| 1-4 | staggered | 0.646 | 0.556 | 0.826 | 0.270 | 0.578 | 0.022 | 0.809 | 0.253 | 0.556 | 0.000 |
| 1-2 | staggered | 0.648 | 0.821 | 0.825 | 0.004 | 0.819 | -0.002 | 0.821 | 0.000 | 0.842 | 0.021 |
| 2-4 | staggered | 0.676 | 0.835 | 0.816 | -0.019 | 0.816 | -0.019 | 0.776 | -0.059 | 0.835 | 0.000 |
| 2-2 | staggered | 0.699 | 0.673 | 0.843 | 0.170 | 0.843 | 0.170 | 0.672 | -0.001 | 0.839 | 0.166 |

### Panel means

| arm | mean selected mIoU | mean ΔmIoU | n refined |
|---|---:|---:|---:|
| anchor | 0.738 | 0.000 | 0 |
| scgen-det | 0.770 | 0.032 | 14 |
| fable | 0.768 | 0.030 | 15 |
| gpt56 | 0.760 | 0.022 | 15 |
| gemini38 | 0.759 | 0.021 | 18 |

### Dual mid-band (retrospective only)

| arm | mean mIoU | mean ΔmIoU |
|---|---:|---:|
| anchor | 0.592 | 0.000 |
| scgen-det | 0.696 | 0.104 |
| fable | 0.689 | 0.097 |
| gpt56 | 0.694 | 0.102 |
| gemini38 | 0.646 | 0.054 |

## Family outcomes (gemini38)

| family | n | mean a_mIoU | mean gemini38 | Δmean | n refined |
|---|---:|---:|---:|---:|---:|
| complex | 8 | 0.716 | 0.724 | 0.009 | 6 |
| continuous | 7 | 0.787 | 0.798 | 0.011 | 6 |
| staggered | 7 | 0.714 | 0.759 | 0.045 | 6 |

## Harm on GT-good anchors (gemini38; anchor mIoU ≥ 0.7)

- GT-good in panel: 16
- GT drops among them: **3** (mean Δ = -0.013)

## Region comparison (gemini38 arm)

| region | n | n_refined | n↑ | n↓ | mean a_mIoU | mean s_mIoU | Δmean | frac↑ |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| A: manuscript PoC (proxy∈[0.5,0.7] ∩ GT∈[0.5,0.7]) | 6 | 4 | 4 | 0 | 0.592 | 0.646 | 0.054 | 0.667 |
| B: proxy refine ∩ GT-good (proxy∈[0.5,0.7] ∩ GT≥0.7) | 16 | 14 | 8 | 3 | 0.793 | 0.801 | 0.009 | 0.500 |
| C: proxy refine ∩ GT-low (proxy∈[0.5,0.7] ∩ GT<0.5) | 0 | — | — | — | — | — | — | — |
| D: all label-free refine panel (proxy∈[0.5,0.7]) | 22 | 18 | 12 | 3 | 0.738 | 0.759 | 0.021 | 0.545 |
| E: mid-proxy / mid-GT tight (proxy∈[0.55,0.65] ∩ GT∈[0.5,0.7]) | 3 | 2 | 2 | 0 | 0.580 | 0.609 | 0.029 | 0.667 |
| F: high-proxy edge of band (proxy∈[0.65,0.7]) | 6 | 5 | 2 | 1 | 0.776 | 0.803 | 0.027 | 0.333 |
| G: low-proxy edge of band (proxy∈[0.5,0.55]) | 5 | 3 | 2 | 0 | 0.705 | 0.721 | 0.016 | 0.400 |
| H: reject band (proxy<0.5) — not refined | 3 | 0 | 0 | 0 | 0.522 | 0.522 | 0.000 | 0.000 |
| I: accept band (proxy≥0.7) — not refined | 2 | 0 | 0 | 0 | 0.843 | 0.843 | 0.000 | 0.000 |
| J: paper nine (legacy definition) | 9 | 4 | 4 | 0 | 0.569 | 0.604 | 0.036 | 0.444 |
| K: paper nine ∩ in this run's panel | 6 | 4 | 4 | 0 | 0.592 | 0.646 | 0.054 | 0.667 |

## Artefacts

- Det selections: `/home/boringtao/Projects/Proxy4Tun/data/sc-general/stage3/selections/`
- Fable selections: `/home/boringtao/Projects/Proxy4Tun/data/sc-general/stage3/selections-fable/`
- GPT-5.6 selections: `/home/boringtao/Projects/Proxy4Tun/data/sc-general/stage3/selections-gpt56/`
- Gemini 3.8 selections: `/home/boringtao/Projects/Proxy4Tun/data/sc-general/stage3/selections-gemini38/`
- Gemini 3.8 report: `/home/boringtao/Projects/Proxy4Tun/data/sc-general/stage3/report_gemini38.md`
- Region CSV: `/home/boringtao/Projects/Proxy4Tun/data/sc-general/stage3/region_comparison_gemini38.csv`
- Campaign: `/home/boringtao/Projects/Proxy4Tun/data/sc-general/stage3/campaign_gemini38.md`

