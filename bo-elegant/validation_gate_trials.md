# Validation gate — single 3-1 trial (proxy v2 feature extract)

_Generated after `run_trials.py --case 3-1 --gate`_

## Case

- Case: `3-1` (continuous family train anchor)
- Lineage: stage-1 copied from `data/anchors/3-1`; stages 2–6 replayed with deployed `anchors/unified/params/3-1-1`
- Output: `data/bo-elegant/3-1-trials/runs/3-1-gate`

## Metrics

| Field | Value | Criterion |
|---|---|---|
| status | ok | == ok |
| mIoU | 0.850 | ≥ 0.80 (anchor parity) |
| lean_complete | True | True |
| det_row_residual_px | 2.93 | finite, single-digit healthy |
| det_row_y_std | 0.0 | finite (post-snap uniform Y) |
| phase_incoherence_deg | 1.2 | < 12° |
| det_real_detection_ratio | 0.0 | diagnostic only (snap regime) |

## Overall: **PASS**

Proceed to Sobol trial campaign on 3-1 (artifacts kept).
