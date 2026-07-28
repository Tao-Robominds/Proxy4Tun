# Stage-1 geometry gate

Auxiliary gate outside the frozen lean Ridge proxy.

## Thresholds

- Orientation fail: `|orient_axis_corr| < 0.6`
- Residual high (unlock / diagnostic): `recentre_residual_max_cm > 10.0` cm
- Quality OR companion: **orientation only** (`proxy_alarm OR orient_fail`). Residual is **not** OR-ed into the quality alarm — any threshold that catches 4-3 also false-alarms high-mIoU anchors (3-8, 3-10).

## Training residual stats

- n=120, min=1.2, median=9.4, max=789.0
- fraction > 10.0 cm: 29.17% (35/120)

## Holdout alarm metrics (is_low = known-bad config)

| Variant | TP | FP | FN | Precision | Recall |
|---|---:|---:|---:|---:|---:|
| proxy only | 27 | 0 | 0 | 1.00 | 1.00 |
| proxy OR orient | 27 | 0 | 0 | 1.00 | 1.00 |
| proxy OR residual | 27 | 7 | 0 | 0.79 | 1.00 |
| proxy OR either | 27 | 7 | 0 | 0.79 | 1.00 |

## Holdout anchors with residual_high

| Subset | residual_cm | mIoU | proxy | unlock |
|---|---:|---:|---:|---|
| 3-5 | 56.6 | 0.588 | 0.620 | yes |
| 4-4 | 35.0 | 0.347 | 0.623 | yes |
| 3-8 | 24.0 | 0.723 | 0.665 | yes |
| 4-3 | 23.2 | 0.516 | 0.630 | yes |
| 3-4 | 20.8 | 0.622 | 0.574 | yes |
| 3-2 | 16.8 | 0.631 | 0.600 | yes |
| 3-10 | 10.2 | 0.853 | 0.903 | yes |

## Pass / fail vs plan criteria

- **flags_4-3_via_residual_high**: PASS
- **orient_false_alarms_on_27_anchors**: PASS (0)
- **proxy_OR_orient_preserves_anchor_FP0**: PASS
- **residual_as_quality_OR_zero_FP_on_mIoU>=0.7_anchors**: FAIL (2 FPs: 3-8(0.72), 3-10(0.85)) — residual kept as unlock/diagnostic only
- **overall_quality_gate**: PASS (orientation OR; residual unlock-only)

## Phase B unlock rule

Unlock stage-1 (`reflect_pilot.py --full` with `unfolding` overlays) when the subset's *anchor* fires `unlock_stage1` (residual > 10.0 cm or orientation fail).

Target subsets for the widened campaign: 3-4 (unlock), 3-2 (unlock), 4-1 (locked), 2-2 (locked).
## Residual threshold sweep (proxy OR residual)

| thr_cm | TP | FP | FN | Prec | Rec |
|---|---:|---:|---:|---:|---:|
| 10 | 27 | 7 | 0 | 0.79 | 1.00 |
| 15 | 27 | 6 | 0 | 0.82 | 1.00 |
| 20 | 27 | 5 | 0 | 0.84 | 1.00 |
| 25 | 27 | 2 | 0 | 0.93 | 1.00 |

