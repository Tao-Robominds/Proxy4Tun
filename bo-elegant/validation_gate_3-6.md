# Validation gate — subset 3-6 (proxy v2)

_Generated 2026-07-23T13:06:21_

## Case

- Worst v1 underestimate: `3-6-anchor` (mIoU 0.836, v1 proxy 0.384)
- v2 features: `['sam_fill_rate', 'sam_ontology_divergence', 'det_row_residual_px', 'det_row_gated', 'depth_nan_ratio']`

## 3-6 metrics

- mIoU = 0.836
- proxy_v1 = 0.4415167682586871
- proxy_v2 = 0.7995032133283096
- det_row_residual_px = 1.8841492652576053
- phase_incoherence_deg = 0.8
- det_real_detection_ratio (diagnostic) = 0.0

## Continuous MAE_anchor = 0.084 (target ≤ 0.15; v1 was 0.31)

## Pass / fail criteria

- `continuous_MAE_anchor_le_0_15`: **PASS** (True)
- `pooled_spearman_ge_0_72`: **PASS** (True)
- `ranking_27_27`: **PASS** (True)
- `staggered_complex_MAE_within_0_04_of_v1`: **PASS** (True)
- `continuous_v1_fps_cleared`: **PASS** (True)
- `no_new_fn_explosion`: **PASS** (True)

## Family MAE notes: {
  "staggered": {
    "mae_v1": 0.08591631115401538,
    "mae_v2": 0.06694389110126034,
    "delta": -0.01897242005275504
  },
  "complex": {
    "mae_v1": 0.06977033341482611,
    "mae_v2": 0.07960604744389255,
    "delta": 0.009835714029066439
  }
}

## Continuous alarm FPs under v2: []

## Overall: **PASS**
