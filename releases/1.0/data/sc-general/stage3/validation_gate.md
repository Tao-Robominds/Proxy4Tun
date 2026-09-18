# Stage-3 validation gate — SC-general label-free refinement

Date: 2026-09-13.

## Criteria

1. Single-instance gate on **3-4** PASS (`data/sc-general/stage3/gate.md`).
2. All **22** label-free band cases have a selection JSON (monotone accept; GT offline only).
3. Report numbers traceable to `data/sc-general/stage3/` and `data/<subset>-scgen-refinement/`.

## Results

| check | result |
|---|---|
| 3-4 gate | **PASS** |
| selections | **22/22** |
| panel mean mIoU | 0.738 → **0.770** (+0.032) |
| 27-subset mean mIoU | 0.722 → **0.748** (paper 0.722 → 0.757) |
| refined cases | 14/22 |
| GT-good harm (mIoU≥0.7) | 5/16, mean Δ −0.008 |
| direction agreement | 9/14 refined |

## Overall: **PASS**

Manuscript figure/table updates remain a separate follow-up.
