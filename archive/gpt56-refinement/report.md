# GPT-5.6 Isolated Refinement Campaign — Report

Model: **GPT-5.6 Sol**. Arm: `gpt56`.
Isolation: sanitized domain knowledge; Fable recipes/logs denied;
GT mIoU withheld until after proxy selection.
Stage-1 policy: residual > 10 cm unlocks unfolding overlays.

## Headline

| Scope | n | Mean mIoU |
|---|---:|---:|
| Anchor | 9 | 0.569 |
| GPT-5.6 selected | 9 | **0.584** |
| Prior Fable selected | 9 | 0.659 |
| Mean ΔmIoU (GPT-5.6) | 9 | +0.016 |
| Mean ΔmIoU (Fable) | 9 | +0.091 |

## Per-subset

| Subset | Anchor proxy | Anchor mIoU | Selected | GPT mIoU | Δ | Fable mIoU | Fable Δ |
|---|---:|---:|---|---:|---:|---:|---:|
| 3-4 | 0.574 | 0.622 | anchor | 0.622 | +0.000 | 0.631 | +0.009 |
| 3-2 | 0.600 | 0.631 | round3 | 0.747 | +0.116 | 0.719 | +0.088 |
| 3-5 | 0.620 | 0.588 | round1 | 0.713 | +0.125 | 0.628 | +0.040 |
| 4-4 | 0.623 | 0.347 | round1 | 0.422 | +0.075 | 0.700 | +0.353 |
| 4-3 | 0.630 | 0.516 | anchor | 0.516 | +0.000 | 0.554 | +0.038 |
| 4-1 | 0.652 | 0.635 | round1 | 0.659 | +0.024 | 0.655 | +0.020 |
| 1-4 | 0.661 | 0.556 | round3 | 0.556 | +0.000 | 0.596 | +0.040 |
| 1-5 | 0.674 | 0.549 | round1 | 0.437 | -0.112 | 0.782 | +0.233 |
| 2-2 | 0.692 | 0.673 | round1 | 0.586 | -0.087 | 0.668 | -0.005 |

## Notes

- Selection used scaled frozen pooled proxy only (monotone accept + residual tiebreak).
- Prior Fable column is the published 9-candidate table for comparison, not an input.
- Artifacts: `data/<subset>-gpt56-refinement/`; selections: `gpt56-refinement/selections/`.
