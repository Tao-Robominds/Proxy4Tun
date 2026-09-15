# Disk preflight — Gemini 3.8 Stage-3 campaign

Generated before gemini38 arm plumbing / gate.

## Free disk
- Filesystem: `/` on `/dev/nvme0n1p2`
- Free before campaign: **196 GB** (well above 50 GB pause threshold)

## Protected trees (must not write)
- `data/bo/` (and aliases)
- `data/anchors/`
- `data/baseline`

## Prior arm evidence (must remain intact)
| path | md5 |
|---|---|
| `exports/sc-general-fable51-evaluation/22_panel_fable51.csv` | `2a822240d155ca024dab84a42dae29c5` |
| `exports/sc-general-gpt56-evaluation/22_panel_gpt56.csv` | `4e2a56abb3b4bf516caff118868abb6b` |
| `data/sc-general/stage3/refined_scores_fable.csv` | `aec1a037f3beaea4a7583a7b9b05fa1d` |
| `data/sc-general/stage3/refined_scores_gpt56.csv` | `bd2af6b2d0e1514f8630692d7bd8f65f` |

## Existing GPT-5.6 intermediates
- Slimmed `data/*-scgen-gpt56-refinement/` total ≈ **902 MB** (essentials retained).
- No further bulk reclaim required before Gemini campaign; per-case slim after each Gemini finish will keep growth bounded.

## Verdict
**PASS** — proceed with arm plumbing and 3-4 gate.
