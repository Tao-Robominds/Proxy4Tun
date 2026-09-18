# Paper nine under the 4-feature SC-general proxy

Generated: 2026-09-13T18:36:00.545907

## Setup

- Proxy: SC-general `pruned_lean` (4 features).
- Proposer: **Fable-5.1** (Cursor agent, live); six dual-band cases reused from the earlier session arm; three reject-band cases (`3-2`, `3-5`, `4-4`) newly refined.
- Selection: monotone accept on scaled proxy (GT offline only).
- Of the nine, **3** sit in the proxy **reject** band (proxy < 0.5) and would be skipped by the label-free refine panel.
- Legacy Fable-5 / GPT-5.6 columns are the manuscript PoC selected mIoU values (older K-row proxy). Δ is recomputed vs the SC-general anchor mIoU. Note: some drafts mistyped 4-4 baseline as 0.647; the true anchor is 0.347.

## Per-case table

| Subset | Band | Baseline | Fable-5.1 | ΔFable-5.1 | Legacy Fable-5 | ΔLegF5 | Legacy GPT-5.6 | ΔGPT |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| 4-4 | reject | 0.347 | 0.368 | 0.021 | 0.700 | 0.353 | 0.422 | 0.075 |
| 1-5 | refine | 0.549 | 0.892 | 0.343 | 0.782 | 0.233 | 0.437 | -0.112 |
| 1-4 | refine | 0.556 | 0.578 | 0.022 | 0.786 | 0.230 | 0.556 | 0.000 |
| 3-2 | reject | 0.631 | 0.749 | 0.118 | 0.719 | 0.088 | 0.747 | 0.116 |
| 4-3 | refine | 0.516 | 0.544 | 0.028 | 0.544 | 0.028 | 0.516 | 0.000 |
| 4-1 | refine | 0.635 | 0.653 | 0.018 | 0.659 | 0.024 | 0.659 | 0.024 |
| 3-4 | refine | 0.622 | 0.622 | 0.000 | 0.631 | 0.009 | 0.622 | 0.000 |
| 3-5 | reject | 0.588 | 0.870 | 0.282 | 0.588 | 0.000 | 0.713 | 0.125 |
| 2-2 | refine | 0.673 | 0.843 | 0.170 | 0.668 | -0.005 | 0.586 | -0.087 |

| **Mean** | — | **0.569** | **0.680** | **0.111** | **0.675** | **0.107** | **0.584** | **0.016** |

### Round / proxy detail (Fable-5.1)

| Subset | Selected | a_proxy | s_proxy | Δproxy |
|---|---|---:|---:|---:|
| 4-4 | round3 | 0.453 | 0.516 | 0.062 |
| 1-5 | round3 | 0.555 | 0.684 | 0.129 |
| 1-4 | round2 | 0.646 | 0.722 | 0.076 |
| 3-2 | round3 | 0.454 | 0.468 | 0.015 |
| 4-3 | round2 | 0.520 | 0.573 | 0.052 |
| 4-1 | round1 | 0.552 | 0.621 | 0.069 |
| 3-4 | anchor | 0.520 | 0.520 | 0.000 |
| 3-5 | round1 | 0.439 | 0.671 | 0.232 |
| 2-2 | round2 | 0.699 | 0.757 | 0.058 |

## Reading

- Fable-5.1 under the 4-feature proxy is the new result of interest.
- Legacy Fable-5 / GPT-5.6 used a different (K-row) proxy and proposal loop; treat them as historical PoC columns, not matched ablations.
- Reject-band cases (`3-2`, `3-5`, `4-4`) were still refined here for parity with the manuscript nine; a strict label-free deployment gate would not admit them.

## Artefacts

- CSV: `/home/boringtao/Projects/Proxy4Tun/data/sc-general/stage3/paper_nine_comparison.csv`
- Selections: `/home/boringtao/Projects/Proxy4Tun/data/sc-general/stage3/selections-fable/`
- Campaign: `/home/boringtao/Projects/Proxy4Tun/data/sc-general/stage3/campaign_fable.md`

