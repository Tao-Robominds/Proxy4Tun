# Release 2 Plan 1 gate

Single-instance proof before any bulk run. Command for each subset:

```bash
./venv/bin/python -u bo/release2/run_reference.py --subset <id>
```

Pass criteria: stages 1-6 exit 0; metadata orientation line and label-free
invariant `|corr(h, axis)| >= 0.5` with the expected sign; ten measurements
finite; `ring_count_error` against `n_rings_kept`; GT mIoU within 0.01 of the
release-1.0 reference; `only_label.csv` has no GT columns; stages 1-5 logs
have no ring-column reads.

Release-1.0 references (`bo/runtime/spaces.UNIFIED_REF_MIOU`): 2-1 0.875,
3-1 0.850, 5-1 0.818.

## 2-1 (staggered) — pass

- Output: `data/release2/references/2-1/`
- Record: `data/release2/references/2-1/record.json`
- Wall time: 283.1 s
- GT mIoU: 0.873 (reference 0.875, delta -0.002, within 0.01)
- Invariant: corr(h, axis) = -0.9999, expected sign -1
- Ring count: detected 10, expected 10, error 0
- `only_label.csv` columns: `pred_labels`, `pred_rings`
- Ring-column reads in the log: 0

| Measurement | Value |
|---|---|
| unfold_residual | 0.0 |
| orient_agreement | 0.9999 |
| denoise_retained_ratio | 0.7506 |
| depth_nan_ratio | 0.1260 |
| ring_count_error | 0 |
| boundary_explained_edge@25 | 0.8891 |
| correspondence_f1@15 | 0.5088 |
| chamfer_sym_px | 45.04 |
| sam_fill_rate | 0.7201 |
| phase_incoherence_deg | 2.4 |

`unfold_residual` is 0 because the staggered reference does not run residual
recentring; the value is finite.

## 3-1 (continuous) — pass

- Output: `data/release2/references/3-1/`
- Record: `data/release2/references/3-1/record.json`
- Wall time: 223.2 s
- GT mIoU: 0.850 (reference 0.850, delta 0.000, within 0.01)
- Invariant: corr(h, axis) = -0.9989, expected sign -1
- Ring count: detected 10, expected 10, error 0
- `only_label.csv` columns: `pred_labels`, `pred_rings`
- Ring-column reads in the log: 0

| Measurement | Value |
|---|---|
| unfold_residual | 2.3418 |
| orient_agreement | 0.9989 |
| denoise_retained_ratio | 0.7266 |
| depth_nan_ratio | 0.1623 |
| ring_count_error | 0 |
| boundary_explained_edge@25 | 0.4773 |
| correspondence_f1@15 | 0.3437 |
| chamfer_sym_px | 94.71 |
| sam_fill_rate | 0.6735 |
| phase_incoherence_deg | 1.2 |

## 5-1 (complex) — pass

- Output: `data/release2/references/5-1/`
- Record: `data/release2/references/5-1/record.json`
- Wall time: 268.7 s
- GT mIoU: 0.818 (reference 0.818, delta 0.000, within 0.01)
- Invariant: corr(h, axis) = +0.7995, expected sign +1
- Ring count: detected 10, expected 10, error 0
- `only_label.csv` columns: `pred_labels`, `pred_rings`
- Ring-column reads in the log: 0

| Measurement | Value |
|---|---|
| unfold_residual | 3.0204 |
| orient_agreement | 0.7995 |
| denoise_retained_ratio | 0.7629 |
| depth_nan_ratio | 0.2084 |
| ring_count_error | 0 |
| boundary_explained_edge@25 | 0.5942 |
| correspondence_f1@15 | 0.4462 |
| chamfer_sym_px | 64.56 |
| sam_fill_rate | 0.7524 |
| phase_incoherence_deg | 21.9 |

## Measured wall time

| Subset | Seconds | Budget |
|---|---|---|
| 2-1 | 283.1 | 338 s |
| 3-1 | 223.2 | 241 s |
| 5-1 | 268.7 | 271 s |

Mean 258 s (4.3 min), under the 4.7 min planning figure and within 50% of budget. Plans 2-4 can keep the published time budget.

Gate result: all three families pass. Plan 2 may start.

