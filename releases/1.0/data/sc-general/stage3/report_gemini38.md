# Stage 3 report — SC-general label-free self-refinement (arm `gemini38`)

Generated: 2026-09-14T11:43:30.940498

## Setup

- Proxy: `bo/sc_general/models.json` pruned_lean (`correspondence_f1@15`, `sam_fill_rate`, `ring_count_error`, `depth_nan_ratio`).
- Proposer: **Gemini-3.8 (fresh per-case agent)**.
- Panel: all 27 holdout anchors with **proxy ∈ [0.5, 0.7]** (no GT bound).
- Panel size: **22** cases; 3 rounds each; monotone-accept selection.
- Outputs under `data/<subset>-scgen-gemini38-refinement/`; summaries in `data/sc-general/stage3/`.

## Panel outcomes

| metric | value |
|---|---:|
| cases refined (selected ≠ anchor) | 18/22 |
| mean anchor proxy | 0.606 |
| mean selected proxy | 0.641 |
| mean anchor mIoU (offline) | 0.738 |
| mean selected mIoU (offline) | 0.759 |
| Δ mean mIoU | +0.021 |
| cases with mIoU↑ | 12 |
| cases with mIoU↓ | 3 |

### Harm on GT-good anchors (anchor mIoU ≥ 0.7)

- GT-good in panel: 16
- GT drops among them: **3** (mean Δ mIoU = -0.013)

### 27-subset means (replace refined selections into full holdout anchors)

- Anchor-only mean mIoU: **0.722** (paper reported 0.722)
- After refinement mean mIoU: **0.739** (paper reported 0.757)

### vs paper nine-case PoC

- Paper: 0.569 → 0.675 on 9 GT-filtered cases.
- Overlap still in this label-free band: ['1-4', '1-5', '2-2', '3-4', '4-1', '4-3']
- Overlap mean mIoU: 0.592 → 0.646

## Per-case table (panel)

| subset | family | anchor proxy | anchor mIoU | selected | sel proxy | sel mIoU | Δproxy | ΔmIoU |
|---|---|---:|---:|---|---:|---:|---:|---:|
| 4-3 | complex | 0.520 | 0.516 | anchor | 0.520 | 0.516 | +0.000 | +0.000 |
| 4-2 | complex | 0.543 | 0.734 | round3 | 0.662 | 0.744 | +0.118 | +0.010 |
| 4-1 | complex | 0.552 | 0.635 | round3 | 0.608 | 0.658 | +0.056 | +0.023 |
| 4-5 | complex | 0.609 | 0.750 | round1 | 0.622 | 0.780 | +0.013 | +0.030 |
| 5-5 | complex | 0.610 | 0.775 | round1 | 0.673 | 0.793 | +0.063 | +0.018 |
| 5-3 | complex | 0.681 | 0.762 | round1 | 0.684 | 0.762 | +0.004 | +0.000 |
| 5-2 | complex | 0.683 | 0.793 | round3 | 0.687 | 0.782 | +0.004 | -0.011 |
| 5-4 | complex | 0.692 | 0.760 | anchor | 0.692 | 0.760 | +0.000 | +0.000 |
| 3-4 | continuous | 0.520 | 0.622 | round1 | 0.553 | 0.692 | +0.034 | +0.070 |
| 3-3 | continuous | 0.522 | 0.808 | anchor | 0.522 | 0.808 | +0.000 | +0.000 |
| 3-7 | continuous | 0.540 | 0.845 | round1 | 0.556 | 0.845 | +0.016 | +0.000 |
| 3-8 | continuous | 0.561 | 0.723 | round1 | 0.561 | 0.728 | +0.000 | +0.005 |
| 3-10 | continuous | 0.589 | 0.853 | round2 | 0.606 | 0.854 | +0.017 | +0.001 |
| 3-9 | continuous | 0.641 | 0.820 | round1 | 0.651 | 0.817 | +0.010 | -0.003 |
| 3-6 | continuous | 0.681 | 0.836 | round3 | 0.714 | 0.841 | +0.033 | +0.005 |
| 1-3 | staggered | 0.550 | 0.779 | round2 | 0.692 | 0.867 | +0.142 | +0.088 |
| 1-5 | staggered | 0.555 | 0.549 | round2 | 0.667 | 0.613 | +0.112 | +0.064 |
| 1-1 | staggered | 0.607 | 0.787 | round3 | 0.618 | 0.763 | +0.012 | -0.024 |
| 1-4 | staggered | 0.646 | 0.556 | anchor | 0.646 | 0.556 | +0.000 | +0.000 |
| 1-2 | staggered | 0.648 | 0.821 | round3 | 0.700 | 0.842 | +0.052 | +0.021 |
| 2-4 | staggered | 0.676 | 0.835 | round2 | 0.708 | 0.835 | +0.032 | +0.000 |
| 2-2 | staggered | 0.699 | 0.673 | round2 | 0.757 | 0.839 | +0.058 | +0.166 |

## Direction agreement (refined cases)

- Refined cases: 18
- Proxy and GT move same direction: 12/18

## Artefacts

- Selections: `/home/boringtao/Projects/Proxy4Tun/data/sc-general/stage3/selections-gemini38/`
- CSV: `/home/boringtao/Projects/Proxy4Tun/data/sc-general/stage3/refined_scores_gemini38.csv`
- Campaign log: `/home/boringtao/Projects/Proxy4Tun/data/sc-general/stage3/campaign_gemini38.md`
- Gate: `/home/boringtao/Projects/Proxy4Tun/data/sc-general/stage3/gate_gemini38.md`

