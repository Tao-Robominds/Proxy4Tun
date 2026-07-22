# Validation gate — subset 3-6 (proxy v2)

_Generated 2026-07-22T21:00:20_

## Case

- Worst v1 underestimate: `3-6-anchor` (mIoU 0.836, v1 proxy 0.384)
- v2 features: `['sam_fill_rate', 'sam_ontology_divergence', 'det_row_residual_px', 'det_row_gated', 'depth_nan_ratio']`

## 3-6 metrics

- mIoU = 0.836
- proxy_v1 = 0.383905203903479
- proxy_v2 = 0.8093222666424914
- det_row_residual_px = 1.8841492652576053
- phase_incoherence_deg = 0.8
- det_real_detection_ratio (diagnostic) = 0.0

## Continuous MAE_anchor = 0.108 (target ≤ 0.15; v1 was 0.31)

## Pass / fail criteria

- `continuous_MAE_anchor_le_0_15`: **PASS** (True)
- `pooled_spearman_ge_0_72`: **PASS** (True)
- `ranking_27_27`: **PASS** (True)
- `staggered_complex_MAE_within_0_04_of_v1`: **PASS** (True)
- `continuous_v1_fps_cleared`: **PASS** (True)
- `no_new_fn_explosion`: **PASS** (True)

## Family MAE notes: {
  "staggered": {
    "mae_v1": 0.08943390649593108,
    "mae_v2": 0.0829932384726137,
    "delta": -0.006440668023317386
  },
  "complex": {
    "mae_v1": 0.0801867676619349,
    "mae_v2": 0.09624455801513374,
    "delta": 0.016057790353198834
  }
}

## Continuous alarm FPs under v2: []

## Overall: **PASS**
