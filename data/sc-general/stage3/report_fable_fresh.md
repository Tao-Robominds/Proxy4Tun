# Stage 3 report — SC-general label-free self-refinement (arm `fable_fresh`)

Generated: 2026-09-16T00:21:31.267850

## Setup

- Proxy: `bo/sc_general/models.json` pruned_lean (`correspondence_f1@15`, `sam_fill_rate`, `ring_count_error`, `depth_nan_ratio`).
- Proposer: **Fable-5.1 (fresh per-case agent)**.
- Panel: all 27 holdout anchors with **proxy ∈ [0.5, 0.7]** (no GT bound).
- Panel size: **22** cases; 3 rounds each; monotone-accept selection.
- Outputs under `data/refinement/fable_fresh/<subset>/`; summaries in `data/sc-general/stage3/`.

## Panel outcomes

| metric | value |
|---|---:|
| cases refined (selected ≠ anchor) | 21/22 |
| mean anchor proxy | 0.606 |
| mean selected proxy | 0.631 |
| mean anchor mIoU (offline) | 0.738 |
| mean selected mIoU (offline) | 0.751 |
| Δ mean mIoU | +0.013 |
| cases with mIoU↑ | 9 |
| cases with mIoU↓ | 9 |

### Harm on GT-good anchors (anchor mIoU ≥ 0.7)

- GT-good in panel: 16
- GT drops among them: **8** (mean Δ mIoU = -0.034)

### 27-subset means (replace refined selections into full holdout anchors)

- Anchor-only mean mIoU: **0.722** (paper reported 0.722)
- After refinement mean mIoU: **0.732** (paper reported 0.757)

### vs paper nine-case PoC

- Paper: 0.569 → 0.675 on 9 GT-filtered cases.
- Overlap still in this label-free band: ['1-4', '1-5', '2-2', '3-4', '4-1', '4-3']
- Overlap mean mIoU: 0.592 → 0.676

## Per-case table (panel)

| subset | family | anchor proxy | anchor mIoU | selected | sel proxy | sel mIoU | Δproxy | ΔmIoU |
|---|---|---:|---:|---|---:|---:|---:|---:|
| 4-3 | complex | 0.520 | 0.516 | round2 | 0.541 | 0.516 | +0.021 | +0.000 |
| 4-2 | complex | 0.543 | 0.734 | round1 | 0.577 | 0.539 | +0.034 | -0.195 |
| 4-1 | complex | 0.552 | 0.635 | round3 | 0.556 | 0.650 | +0.004 | +0.015 |
| 4-5 | complex | 0.609 | 0.750 | round1 | 0.655 | 0.784 | +0.046 | +0.034 |
| 5-5 | complex | 0.610 | 0.775 | round3 | 0.645 | 0.772 | +0.035 | -0.003 |
| 5-3 | complex | 0.681 | 0.762 | round2 | 0.686 | 0.761 | +0.006 | -0.001 |
| 5-2 | complex | 0.683 | 0.793 | round3 | 0.699 | 0.793 | +0.016 | +0.000 |
| 5-4 | complex | 0.692 | 0.760 | round3 | 0.709 | 0.760 | +0.016 | +0.000 |
| 3-4 | continuous | 0.520 | 0.622 | round2 | 0.530 | 0.601 | +0.010 | -0.021 |
| 3-3 | continuous | 0.522 | 0.808 | round3 | 0.591 | 0.812 | +0.069 | +0.004 |
| 3-7 | continuous | 0.540 | 0.845 | round1 | 0.544 | 0.846 | +0.004 | +0.001 |
| 3-8 | continuous | 0.561 | 0.723 | anchor | 0.561 | 0.723 | +0.000 | +0.000 |
| 3-10 | continuous | 0.589 | 0.853 | round1 | 0.619 | 0.852 | +0.030 | -0.001 |
| 3-9 | continuous | 0.641 | 0.820 | round2 | 0.647 | 0.818 | +0.005 | -0.002 |
| 3-6 | continuous | 0.681 | 0.836 | round2 | 0.744 | 0.820 | +0.063 | -0.016 |
| 1-3 | staggered | 0.550 | 0.779 | round3 | 0.567 | 0.780 | +0.017 | +0.001 |
| 1-5 | staggered | 0.555 | 0.549 | round2 | 0.622 | 0.886 | +0.067 | +0.337 |
| 1-1 | staggered | 0.607 | 0.787 | round2 | 0.645 | 0.786 | +0.038 | -0.001 |
| 1-4 | staggered | 0.646 | 0.556 | round2 | 0.650 | 0.557 | +0.004 | +0.001 |
| 1-2 | staggered | 0.648 | 0.821 | round2 | 0.653 | 0.835 | +0.005 | +0.014 |
| 2-4 | staggered | 0.676 | 0.835 | round3 | 0.696 | 0.783 | +0.020 | -0.052 |
| 2-2 | staggered | 0.699 | 0.673 | round2 | 0.753 | 0.846 | +0.054 | +0.173 |

## Direction agreement (refined cases)

- Refined cases: 21
- Proxy and GT move same direction: 9/21

## Artefacts

- Selections: `/home/boringtao/Projects/Proxy4Tun/data/sc-general/stage3/selections-fable-fresh/`
- CSV: `/home/boringtao/Projects/Proxy4Tun/data/sc-general/stage3/refined_scores_fable_fresh.csv`
- Campaign log: `/home/boringtao/Projects/Proxy4Tun/data/sc-general/stage3/campaign_fable_fresh.md`
- Gate: `/home/boringtao/Projects/Proxy4Tun/data/sc-general/stage3/gate_fable_fresh.md`

