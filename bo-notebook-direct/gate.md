# Single-instance validation gate — notebook-faithful baseline

Date: 2026-07-28.

**HARD RULE proof before scaling.** One holdout per family recipe with
notebook-mode params (adaptations off). Gate checks *mechanics* (pipeline
completes, mIoU finite); a low score is expected and acceptable.

## Cases

| Subset | Family | Params | Command lineage | mIoU | Unified sibling-anchor mIoU | Pass |
|---|---|---|---|---:|---:|:---:|
| **1-2** | t1&2 / staggered | `bo-notebook-direct/params/1-1` | `./venv/bin/python bo-notebook-direct/run_holdouts.py --subset 1-2 --force` | **0.176** | 0.821 | yes |
| **3-3** | t3 / continuous | `bo-notebook-direct/params/3-1-1` | `… --subset 3-3 --force` | **0.340** | 0.808 | yes |
| **4-2** | t4&5 / complex | `bo-notebook-direct/params/4-1` | `… --subset 4-2 --force` | **0.240** | 0.734 | yes |

## Pass criteria (per case)

| Check | Criterion | 1-2 | 3-3 | 4-2 |
|---|---|:---:|:---:|:---:|
| Pipeline exit | 0 | yes | yes | yes |
| `evaluation/performance.md` | exists | yes | yes | yes |
| mIoU | finite float | 0.176 | 0.340 | 0.240 |
| Output path | `data/notebook-direct/<id>/` (not anchors/baseline/bo) | yes | yes | yes |
| Wall-clock | recorded | 310 s | 221 s | 281 s |

Evidence paths:

- `data/notebook-direct/1-2/`, `bo-notebook-direct/logs/1-2.json`
- `data/notebook-direct/3-3/`, `bo-notebook-direct/logs/3-3.json`
- `data/notebook-direct/4-2/`, `bo-notebook-direct/logs/4-2.json`

## Observation

Notebook-mode already collapses mIoU by ~0.5–0.65 relative to the unified
sibling-anchor runs on the same holdouts. This is the expected motivation
baseline (static expert / notebook config transfers poorly).

## Verdict

**GATE: PASS — proceed to the remaining 24 holdouts.**
