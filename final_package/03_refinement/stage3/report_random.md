# Stage 3 report — SC-general label-free self-refinement (arm `random`)

Generated: 2026-09-15T10:03:16.001935

## Setup

- Proxy: `bo/sc_general/models.json` pruned_lean (`correspondence_f1@15`, `sam_fill_rate`, `ring_count_error`, `depth_nan_ratio`).
- Proposer: **deterministic recipes**.
- Panel: all 27 holdout anchors with **proxy ∈ [0.5, 0.7]** (no GT bound).
- Panel size: **22** cases; 3 rounds each; monotone-accept selection.
- Outputs under `data/<subset>-scgen-refinement/`; summaries in `data/sc-general/stage3/`.

## Panel outcomes

| metric | value |
|---|---:|
| cases refined (selected ≠ anchor) | 16/22 |
| mean anchor proxy | 0.606 |
| mean selected proxy | 0.628 |
| mean anchor mIoU (offline) | 0.738 |
| mean selected mIoU (offline) | 0.752 |
| Δ mean mIoU | +0.014 |
| cases with mIoU↑ | 8 |
| cases with mIoU↓ | 6 |

### Harm on GT-good anchors (anchor mIoU ≥ 0.7)

- GT-good in panel: 16
- GT drops among them: **5** (mean Δ mIoU = -0.048)

### 27-subset means (replace refined selections into full holdout anchors)

- Anchor-only mean mIoU: **0.722** (paper reported 0.722)
- After refinement mean mIoU: **0.733** (paper reported 0.757)

### vs paper nine-case PoC

- Paper: 0.569 → 0.675 on 9 GT-filtered cases.
- Overlap still in this label-free band: ['1-4', '1-5', '2-2', '3-4', '4-1', '4-3']
- Overlap mean mIoU: 0.592 → 0.678

## Per-case table (panel)

| subset | family | anchor proxy | anchor mIoU | selected | sel proxy | sel mIoU | Δproxy | ΔmIoU |
|---|---|---:|---:|---|---:|---:|---:|---:|
| 4-3 | complex | 0.520 | 0.516 | anchor | 0.520 | 0.516 | +0.000 | +0.000 |
| 4-2 | complex | 0.543 | 0.734 | round1 | 0.634 | 0.738 | +0.090 | +0.004 |
| 4-1 | complex | 0.552 | 0.635 | round2 | 0.593 | 0.660 | +0.041 | +0.025 |
| 4-5 | complex | 0.609 | 0.750 | anchor | 0.609 | 0.750 | +0.000 | +0.000 |
| 5-5 | complex | 0.610 | 0.775 | round3 | 0.667 | 0.794 | +0.057 | +0.019 |
| 5-3 | complex | 0.681 | 0.762 | round2 | 0.681 | 0.762 | +0.000 | +0.000 |
| 5-2 | complex | 0.683 | 0.793 | round1 | 0.685 | 0.793 | +0.003 | +0.000 |
| 5-4 | complex | 0.692 | 0.760 | round1 | 0.715 | 0.752 | +0.022 | -0.008 |
| 3-4 | continuous | 0.520 | 0.622 | anchor | 0.520 | 0.622 | +0.000 | +0.000 |
| 3-3 | continuous | 0.522 | 0.808 | round2 | 0.523 | 0.691 | +0.001 | -0.117 |
| 3-7 | continuous | 0.540 | 0.845 | round1 | 0.542 | 0.814 | +0.002 | -0.031 |
| 3-8 | continuous | 0.561 | 0.723 | anchor | 0.561 | 0.723 | +0.000 | +0.000 |
| 3-10 | continuous | 0.589 | 0.853 | anchor | 0.589 | 0.853 | +0.000 | +0.000 |
| 3-9 | continuous | 0.641 | 0.820 | anchor | 0.641 | 0.820 | +0.000 | +0.000 |
| 3-6 | continuous | 0.681 | 0.836 | round2 | 0.712 | 0.805 | +0.030 | -0.031 |
| 1-3 | staggered | 0.550 | 0.779 | round1 | 0.588 | 0.786 | +0.037 | +0.007 |
| 1-5 | staggered | 0.555 | 0.549 | round3 | 0.639 | 0.867 | +0.084 | +0.318 |
| 1-1 | staggered | 0.607 | 0.787 | round3 | 0.636 | 0.791 | +0.029 | +0.004 |
| 1-4 | staggered | 0.646 | 0.556 | round2 | 0.699 | 0.811 | +0.053 | +0.255 |
| 1-2 | staggered | 0.648 | 0.821 | round1 | 0.654 | 0.825 | +0.006 | +0.004 |
| 2-4 | staggered | 0.676 | 0.835 | round3 | 0.701 | 0.784 | +0.025 | -0.051 |
| 2-2 | staggered | 0.699 | 0.673 | round1 | 0.709 | 0.592 | +0.010 | -0.081 |

## Direction agreement (refined cases)

- Refined cases: 16
- Proxy and GT move same direction: 8/16

## Artefacts

- Selections: `/home/boringtao/Projects/Proxy4Tun/data/sc-general/stage3/selections-random/`
- CSV: `/home/boringtao/Projects/Proxy4Tun/data/sc-general/stage3/refined_scores_random.csv`
- Campaign log: `/home/boringtao/Projects/Proxy4Tun/data/sc-general/stage3/campaign.md`
- Gate: `/home/boringtao/Projects/Proxy4Tun/data/sc-general/stage3/gate.md`

