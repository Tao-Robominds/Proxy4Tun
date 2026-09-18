# Stage 3 arm comparison — SC-general

Generated: 2026-09-13T18:36:00.540031

## Arms

- **anchor**: frozen SC-general holdout anchors (no refinement).
- **scgen-det**: deterministic Stage-3 recipes (`run_campaign.propose`).
- **fable**: Fable-5 (Cursor agent, live) GT-blind-by-protocol proposals.
- **legacy**: paper reflection campaign (`bo/proxy_scale/refined_scores.csv`, older proxy).

### Protocol caveat

Fable-5 proposals never read `offline_gt.json` / `performance.md` / band CSVs during the loop. The proposer has seen aggregate GT for these cases earlier in the session, so this arm is **GT-blind by protocol**, not by information barrier.

## Per-case table (full panel)

| subset | family | a_proxy | a_mIoU | det_round | det_mIoU | Δdet | fable_round | fable_mIoU | Δfable | legacy_arm | legacy_mIoU | Δlegacy |
|---|---|---:|---:|---|---:|---:|---|---:|---:|---|---:|---:|
| 4-3 | complex | 0.520 | 0.516 | round3 | 0.540 | 0.024 | round2 | 0.544 | 0.028 | cursor2_s1 | 0.544 | 0.028 |
| 4-2 | complex | 0.543 | 0.734 | round2 | 0.773 | 0.039 | round2 | 0.773 | 0.039 | nan | 0.734 | 0.000 |
| 4-1 | complex | 0.552 | 0.635 | round1 | 0.653 | 0.018 | round1 | 0.653 | 0.018 | cursor3 | 0.659 | 0.024 |
| 4-5 | complex | 0.609 | 0.750 | round1 | 0.775 | 0.025 | round2 | 0.771 | 0.021 | nan | 0.750 | 0.000 |
| 5-5 | complex | 0.610 | 0.775 | round2 | 0.770 | -0.005 | round2 | 0.781 | 0.006 | nan | 0.775 | 0.000 |
| 5-3 | complex | 0.681 | 0.762 | anchor | 0.762 | 0.000 | anchor | 0.762 | 0.000 | nan | 0.762 | 0.000 |
| 5-2 | complex | 0.683 | 0.793 | round2 | 0.781 | -0.012 | round2 | 0.781 | -0.012 | nan | 0.793 | 0.000 |
| 5-4 | complex | 0.692 | 0.760 | anchor | 0.760 | 0.000 | anchor | 0.760 | 0.000 | nan | 0.760 | 0.000 |
| 3-4 | continuous | 0.520 | 0.622 | anchor | 0.622 | 0.000 | anchor | 0.622 | 0.000 | cursor3 | 0.631 | 0.009 |
| 3-3 | continuous | 0.522 | 0.808 | anchor | 0.808 | 0.000 | anchor | 0.808 | 0.000 | nan | 0.808 | 0.000 |
| 3-7 | continuous | 0.540 | 0.845 | anchor | 0.845 | 0.000 | anchor | 0.845 | 0.000 | nan | 0.845 | 0.000 |
| 3-8 | continuous | 0.561 | 0.723 | anchor | 0.723 | 0.000 | round3 | 0.717 | -0.006 | nan | 0.723 | 0.000 |
| 3-10 | continuous | 0.589 | 0.853 | anchor | 0.853 | 0.000 | anchor | 0.853 | 0.000 | nan | 0.853 | 0.000 |
| 3-9 | continuous | 0.641 | 0.820 | anchor | 0.820 | 0.000 | anchor | 0.820 | 0.000 | nan | 0.820 | 0.000 |
| 3-6 | continuous | 0.681 | 0.836 | round2 | 0.835 | -0.001 | round2 | 0.835 | -0.001 | nan | 0.836 | 0.000 |
| 1-3 | staggered | 0.550 | 0.779 | round1 | 0.825 | 0.046 | round3 | 0.825 | 0.046 | nan | 0.779 | 0.000 |
| 1-5 | staggered | 0.555 | 0.549 | round3 | 0.693 | 0.144 | round3 | 0.892 | 0.343 | cursor2 | 0.782 | 0.233 |
| 1-1 | staggered | 0.607 | 0.787 | round1 | 0.784 | -0.003 | round1 | 0.790 | 0.003 | nan | 0.787 | 0.000 |
| 1-4 | staggered | 0.646 | 0.556 | round1 | 0.826 | 0.270 | round2 | 0.578 | 0.022 | cursor2 | 0.786 | 0.230 |
| 1-2 | staggered | 0.648 | 0.821 | round1 | 0.825 | 0.004 | round2 | 0.819 | -0.002 | nan | 0.821 | 0.000 |
| 2-4 | staggered | 0.676 | 0.835 | round1 | 0.816 | -0.019 | round3 | 0.816 | -0.019 | nan | 0.835 | 0.000 |
| 2-2 | staggered | 0.699 | 0.673 | round1 | 0.843 | 0.170 | round2 | 0.843 | 0.170 | cursor3 | 0.668 | -0.005 |

### Focus-set means

| arm | mean selected mIoU | mean ΔmIoU | n refined |
|---|---:|---:|---:|
| anchor | 0.738 | 0.000 | 0 |
| scgen-det | 0.770 | 0.032 | 14 |
| fable | 0.768 | 0.030 | 15 |
| legacy (where present) | 0.761 | 0.024 | 22 |

## Region comparison (fable arm)

| region | n | n_refined | n↑ | n↓ | mean a_mIoU | mean s_mIoU | Δmean | frac↑ |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| A: manuscript PoC (proxy∈[0.5,0.7] ∩ GT∈[0.5,0.7]) | 6 | 5 | 5 | 0 | 0.592 | 0.689 | 0.097 | 0.833 |
| B: proxy refine ∩ GT-good (proxy∈[0.5,0.7] ∩ GT≥0.7) | 16 | 10 | 5 | 5 | 0.793 | 0.797 | 0.005 | 0.312 |
| C: proxy refine ∩ GT-low (proxy∈[0.5,0.7] ∩ GT<0.5) | 0 | — | — | — | — | — | — | — |
| D: all label-free refine panel (proxy∈[0.5,0.7]) | 22 | 15 | 10 | 5 | 0.738 | 0.768 | 0.030 | 0.455 |
| E: mid-proxy / mid-GT tight (proxy∈[0.55,0.65] ∩ GT∈[0.5,0.7]) | 3 | 3 | 3 | 0 | 0.580 | 0.708 | 0.128 | 1.000 |
| F: high-proxy edge of band (proxy∈[0.65,0.7]) | 6 | 4 | 1 | 3 | 0.776 | 0.799 | 0.023 | 0.167 |
| G: low-proxy edge of band (proxy∈[0.5,0.55]) | 5 | 2 | 2 | 0 | 0.705 | 0.718 | 0.013 | 0.400 |
| H: reject band (proxy<0.5) — not refined | 3 | 3 | 3 | 0 | 0.522 | 0.662 | 0.140 | 1.000 |
| I: accept band (proxy≥0.7) — not refined | 2 | 0 | 0 | 0 | 0.843 | 0.843 | 0.000 | 0.000 |
| J: paper nine (legacy definition) | 9 | 8 | 8 | 0 | 0.569 | 0.680 | 0.111 | 0.889 |
| K: paper nine ∩ in this run's panel | 6 | 5 | 5 | 0 | 0.592 | 0.689 | 0.097 | 0.833 |

## Artefacts

- Det selections: `/home/boringtao/Projects/Proxy4Tun/data/sc-general/stage3/selections/`
- Fable selections: `/home/boringtao/Projects/Proxy4Tun/data/sc-general/stage3/selections-fable/`
- Det report: `/home/boringtao/Projects/Proxy4Tun/data/sc-general/stage3/report.md`
- Fable report: `/home/boringtao/Projects/Proxy4Tun/data/sc-general/stage3/report_fable.md`
- Region CSV: `/home/boringtao/Projects/Proxy4Tun/data/sc-general/stage3/region_comparison_fable.csv`
- Campaign: `/home/boringtao/Projects/Proxy4Tun/data/sc-general/stage3/campaign_fable.md`

