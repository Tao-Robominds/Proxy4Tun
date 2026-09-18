# Stage 3 report — SC-general label-free self-refinement (arm `gpt56`)

Generated: 2026-09-15T05:30:34.016074

## Setup

- Proxy: `bo/sc_general/models.json` pruned_lean (`correspondence_f1@15`, `sam_fill_rate`, `ring_count_error`, `depth_nan_ratio`).
- Proposer: **GPT-5.6 (fresh per-case agent)**.
- Panel: all 27 holdout anchors with **proxy ∈ [0.5, 0.7]** (no GT bound).
- Panel size: **22** cases; 3 rounds each; monotone-accept selection.
- Outputs under `data/<subset>-scgen-gpt56-refinement/`; summaries in `data/sc-general/stage3/`.

## Panel outcomes

| metric | value |
|---|---:|
| cases refined (selected ≠ anchor) | 15/22 |
| mean anchor proxy | 0.606 |
| mean selected proxy | 0.629 |
| mean anchor mIoU (offline) | 0.738 |
| mean selected mIoU (offline) | 0.760 |
| Δ mean mIoU | +0.022 |
| cases with mIoU↑ | 7 |
| cases with mIoU↓ | 8 |

### Harm on GT-good anchors (anchor mIoU ≥ 0.7)

- GT-good in panel: 16
- GT drops among them: **6** (mean Δ mIoU = -0.026)

### 27-subset means (replace refined selections into full holdout anchors)

- Anchor-only mean mIoU: **0.722** (paper reported 0.722)
- After refinement mean mIoU: **0.739** (paper reported 0.757)

### vs paper nine-case PoC

- Paper: 0.569 → 0.675 on 9 GT-filtered cases.
- Overlap still in this label-free band: ['1-4', '1-5', '2-2', '3-4', '4-1', '4-3']
- Overlap mean mIoU: 0.592 → 0.694

## Per-case table (panel)

| subset | family | anchor proxy | anchor mIoU | selected | sel proxy | sel mIoU | Δproxy | ΔmIoU |
|---|---|---:|---:|---|---:|---:|---:|---:|
| 4-3 | complex | 0.520 | 0.516 | round1 | 0.526 | 0.515 | +0.006 | -0.001 |
| 4-2 | complex | 0.543 | 0.734 | round1 | 0.653 | 0.643 | +0.109 | -0.091 |
| 4-1 | complex | 0.552 | 0.635 | round2 | 0.659 | 0.652 | +0.108 | +0.017 |
| 4-5 | complex | 0.609 | 0.750 | round1 | 0.647 | 0.777 | +0.038 | +0.027 |
| 5-5 | complex | 0.610 | 0.775 | round1 | 0.641 | 0.771 | +0.031 | -0.004 |
| 5-3 | complex | 0.681 | 0.762 | anchor | 0.681 | 0.762 | +0.000 | +0.000 |
| 5-2 | complex | 0.683 | 0.793 | round1 | 0.690 | 0.792 | +0.007 | -0.001 |
| 5-4 | complex | 0.692 | 0.760 | round1 | 0.710 | 0.759 | +0.018 | -0.001 |
| 3-4 | continuous | 0.520 | 0.622 | round3 | 0.535 | 0.627 | +0.016 | +0.005 |
| 3-3 | continuous | 0.522 | 0.808 | round1 | 0.525 | 0.806 | +0.004 | -0.002 |
| 3-7 | continuous | 0.540 | 0.845 | anchor | 0.540 | 0.845 | +0.000 | +0.000 |
| 3-8 | continuous | 0.561 | 0.723 | anchor | 0.561 | 0.723 | +0.000 | +0.000 |
| 3-10 | continuous | 0.589 | 0.853 | anchor | 0.589 | 0.853 | +0.000 | +0.000 |
| 3-9 | continuous | 0.641 | 0.820 | anchor | 0.641 | 0.820 | +0.000 | +0.000 |
| 3-6 | continuous | 0.681 | 0.836 | round3 | 0.707 | 0.837 | +0.025 | +0.001 |
| 1-3 | staggered | 0.550 | 0.779 | round3 | 0.570 | 0.780 | +0.020 | +0.001 |
| 1-5 | staggered | 0.555 | 0.549 | round3 | 0.610 | 0.887 | +0.055 | +0.338 |
| 1-1 | staggered | 0.607 | 0.787 | anchor | 0.607 | 0.787 | +0.000 | +0.000 |
| 1-4 | staggered | 0.646 | 0.556 | round2 | 0.688 | 0.809 | +0.042 | +0.253 |
| 1-2 | staggered | 0.648 | 0.821 | anchor | 0.648 | 0.821 | +0.000 | +0.000 |
| 2-4 | staggered | 0.676 | 0.835 | round3 | 0.686 | 0.776 | +0.010 | -0.059 |
| 2-2 | staggered | 0.699 | 0.673 | round2 | 0.712 | 0.672 | +0.013 | -0.001 |

## Direction agreement (refined cases)

- Refined cases: 15
- Proxy and GT move same direction: 7/15

## Artefacts

- Selections: `/home/boringtao/Projects/Proxy4Tun/data/sc-general/stage3/selections-gpt56/`
- CSV: `/home/boringtao/Projects/Proxy4Tun/data/sc-general/stage3/refined_scores_gpt56.csv`
- Campaign log: `/home/boringtao/Projects/Proxy4Tun/data/sc-general/stage3/campaign_gpt56.md`
- Gate: `/home/boringtao/Projects/Proxy4Tun/data/sc-general/stage3/gate_gpt56.md`

