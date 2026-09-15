# Notebook-faithful baseline — report

Date: 2026-07-28.

Notebook-mode parameter overlays from
`bo-notebook-direct/params/` run through the original per-family
anchor stage scripts on the 27-subset panel that yields the
unified mean **0.722**. See `README.md` for caveats
(geometric SAM fallback, T3 mask-column fix, etc. remain).

## 1. Headline numbers

| Scope | n | Mean mIoU |
|---|---:|---:|
| Notebook-faithful (ok runs) | 27 | **0.456** |
| Unified sibling-anchor (full panel) | 27 | **0.722** |
| After proxy-selected refinement | 27 | **0.757** |
| Unified on same subsets as notebook-ok | 27 | 0.722 |
| Δ (notebook − unified), paired | 27 | **-0.265** |

Failures / missing: **0** (none).

## 2. Per-family means (notebook-ok only)

| Family | n | Notebook | Unified | Δ |
|---|---:|---:|---:|---:|
| staggered | 9 | 0.348 | 0.743 | -0.395 |
| continuous | 9 | 0.567 | 0.747 | -0.181 |
| complex | 9 | 0.454 | 0.675 | -0.221 |

## 3. Per-subset results

| Subset | Family | Notebook | Unified | Refined | Δ nb−un | Status |
|---|---|---:|---:|---:|---:|---|
| 1-1 | staggered | 0.389 | 0.787 | 0.787 | -0.398 | ok |
| 1-2 | staggered | 0.176 | 0.821 | 0.821 | -0.645 | ok |
| 1-3 | staggered | 0.249 | 0.779 | 0.779 | -0.530 | ok |
| 1-4 | staggered | 0.137 | 0.556 | 0.786 | -0.419 | ok |
| 1-5 | staggered | 0.439 | 0.549 | 0.782 | -0.110 | ok |
| 2-2 | staggered | 0.446 | 0.673 | 0.668 | -0.227 | ok |
| 2-3 | staggered | 0.410 | 0.800 | 0.800 | -0.390 | ok |
| 2-4 | staggered | 0.483 | 0.835 | 0.835 | -0.352 | ok |
| 2-5 | staggered | 0.406 | 0.886 | 0.886 | -0.480 | ok |
| 3-2 | continuous | 0.152 | 0.631 | 0.719 | -0.479 | ok |
| 3-3 | continuous | 0.340 | 0.808 | 0.808 | -0.468 | ok |
| 3-4 | continuous | 0.264 | 0.622 | 0.631 | -0.358 | ok |
| 3-5 | continuous | 0.862 | 0.588 | 0.588 | +0.274 | ok |
| 3-6 | continuous | 0.890 | 0.836 | 0.836 | +0.054 | ok |
| 3-7 | continuous | 0.887 | 0.845 | 0.845 | +0.042 | ok |
| 3-8 | continuous | 0.463 | 0.723 | 0.723 | -0.260 | ok |
| 3-9 | continuous | 0.353 | 0.820 | 0.820 | -0.467 | ok |
| 3-10 | continuous | 0.888 | 0.853 | 0.853 | +0.035 | ok |
| 4-1 | complex | 0.635 | 0.635 | 0.659 | +0.000 | ok |
| 4-2 | complex | 0.240 | 0.734 | 0.734 | -0.494 | ok |
| 4-3 | complex | 0.104 | 0.516 | 0.544 | -0.412 | ok |
| 4-4 | complex | 0.800 | 0.347 | 0.700 | +0.453 | ok |
| 4-5 | complex | 0.786 | 0.750 | 0.750 | +0.036 | ok |
| 5-2 | complex | 0.233 | 0.793 | 0.793 | -0.560 | ok |
| 5-3 | complex | 0.737 | 0.762 | 0.762 | -0.025 | ok |
| 5-4 | complex | 0.172 | 0.760 | 0.760 | -0.588 | ok |
| 5-5 | complex | 0.379 | 0.775 | 0.775 | -0.396 | ok |

## Manuscript-ready sentence

Applying the notebook-faithful expert configuration (parametric adaptations disabled) to the same 27-subset panel yields mean mIoU **0.456**, versus **0.722** under the unified sibling-anchor pipeline and **0.757** after proxy-selected self-refinement (paired Δ notebook−unified **-0.265**).

## Caveats

- Geometric SAM fallback on tunnels 4/5 remains (hardcoded).
- T3 theta-column fix and T1/T2 oblique sign fix remain.
- T3 `n_segment` kept at subset-scale `[2,8]` (not notebook `[11,11]`).
