# Stage 3 report — SC-general label-free self-refinement

Generated: 2026-09-13T01:48:23.270916

## Setup

- Proxy: `bo/sc_general/models.json` pruned_lean (`correspondence_f1@15`, `sam_fill_rate`, `ring_count_error`, `depth_nan_ratio`).
- Panel: all 27 holdout anchors with **proxy ∈ [0.5, 0.7]** (no GT bound).
- Panel size: **22** cases; 3 rounds each; monotone-accept selection.
- Outputs under `data/<subset>-scgen-refinement/`; summaries in `data/sc-general/stage3/`.

## Panel outcomes

| metric | value |
|---|---:|
| cases refined (selected ≠ anchor) | 14/22 |
| mean anchor proxy | 0.606 |
| mean selected proxy | 0.647 |
| mean anchor mIoU (offline) | 0.738 |
| mean selected mIoU (offline) | 0.770 |
| Δ mean mIoU | +0.032 |
| cases with mIoU↑ | 9 |
| cases with mIoU↓ | 5 |

### Harm on GT-good anchors (anchor mIoU ≥ 0.7)

- GT-good in panel: 16
- GT drops among them: **5** (mean Δ mIoU = -0.008)

### 27-subset means (replace refined selections into full holdout anchors)

- Anchor-only mean mIoU: **0.722** (paper reported 0.722)
- After refinement mean mIoU: **0.748** (paper reported 0.757)

### vs paper nine-case PoC

- Paper: 0.569 → 0.675 on 9 GT-filtered cases.
- Overlap still in this label-free band: ['1-4', '1-5', '2-2', '3-4', '4-1', '4-3']
- Overlap mean mIoU: 0.592 → 0.696

## Per-case table (panel)

| subset | family | anchor proxy | anchor mIoU | selected | sel proxy | sel mIoU | Δproxy | ΔmIoU |
|---|---|---:|---:|---|---:|---:|---:|---:|
| 4-3 | complex | 0.520 | 0.516 | round3 | 0.592 | 0.540 | +0.071 | +0.024 |
| 4-2 | complex | 0.543 | 0.734 | round2 | 0.687 | 0.773 | +0.143 | +0.039 |
| 4-1 | complex | 0.552 | 0.635 | round1 | 0.621 | 0.653 | +0.069 | +0.018 |
| 4-5 | complex | 0.609 | 0.750 | round1 | 0.639 | 0.775 | +0.029 | +0.025 |
| 5-5 | complex | 0.610 | 0.775 | round2 | 0.668 | 0.770 | +0.058 | -0.005 |
| 5-3 | complex | 0.681 | 0.762 | anchor | 0.681 | 0.762 | +0.000 | +0.000 |
| 5-2 | complex | 0.683 | 0.793 | round2 | 0.703 | 0.781 | +0.020 | -0.012 |
| 5-4 | complex | 0.692 | 0.760 | anchor | 0.692 | 0.760 | +0.000 | +0.000 |
| 3-4 | continuous | 0.520 | 0.622 | anchor | 0.520 | 0.622 | +0.000 | +0.000 |
| 3-3 | continuous | 0.522 | 0.808 | anchor | 0.522 | 0.808 | +0.000 | +0.000 |
| 3-7 | continuous | 0.540 | 0.845 | anchor | 0.540 | 0.845 | +0.000 | +0.000 |
| 3-8 | continuous | 0.561 | 0.723 | anchor | 0.561 | 0.723 | +0.000 | +0.000 |
| 3-10 | continuous | 0.589 | 0.853 | anchor | 0.589 | 0.853 | +0.000 | +0.000 |
| 3-9 | continuous | 0.641 | 0.820 | anchor | 0.641 | 0.820 | +0.000 | +0.000 |
| 3-6 | continuous | 0.681 | 0.836 | round2 | 0.725 | 0.835 | +0.044 | -0.001 |
| 1-3 | staggered | 0.550 | 0.779 | round1 | 0.680 | 0.825 | +0.130 | +0.046 |
| 1-5 | staggered | 0.555 | 0.549 | round3 | 0.657 | 0.693 | +0.102 | +0.144 |
| 1-1 | staggered | 0.607 | 0.787 | round1 | 0.628 | 0.784 | +0.021 | -0.003 |
| 1-4 | staggered | 0.646 | 0.556 | round1 | 0.714 | 0.826 | +0.068 | +0.270 |
| 1-2 | staggered | 0.648 | 0.821 | round1 | 0.701 | 0.825 | +0.053 | +0.004 |
| 2-4 | staggered | 0.676 | 0.835 | round1 | 0.709 | 0.816 | +0.033 | -0.019 |
| 2-2 | staggered | 0.699 | 0.673 | round1 | 0.757 | 0.843 | +0.058 | +0.170 |

## Direction agreement (refined cases)

- Refined cases: 14
- Proxy and GT move same direction: 9/14

## Artefacts

- Selections: `/home/boringtao/Projects/Proxy4Tun/data/sc-general/stage3/selections/`
- CSV: `/home/boringtao/Projects/Proxy4Tun/data/sc-general/stage3/refined_scores.csv`
- Campaign log: `/home/boringtao/Projects/Proxy4Tun/data/sc-general/stage3/campaign.md`
- Gate: `/home/boringtao/Projects/Proxy4Tun/data/sc-general/stage3/gate.md`

