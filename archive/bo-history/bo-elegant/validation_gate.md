# Validation gate — subset 3-3

_Generated 2026-07-22T15:55:24_

## Case

- Subset: `3-3` (continuous family holdout)
- Lineage: reused `data/bo-unified/3-3-family-proxy/runs/3-3-{anchor,bad}`
- Proxy: frozen lean Ridge from `bo-elegant/family/models.json`
- Features: `['depth_nan_ratio', 'denoise_retained_ratio', 'det_real_detection_ratio', 'sam_fill_rate', 'sam_ontology_divergence']`

## Metrics

| Kind | mIoU | proxy | path |
|---|---:|---:|---|
| anchor | 0.808 | 0.5391 | `data/bo-unified/3-3-family-proxy/runs/3-3-anchor` |
| bad | 0.031 | 0.0547 | `data/bo-unified/3-3-family-proxy/runs/3-3-bad` |

- Proxy gap (anchor − bad) = **0.4844**

## Pass / fail criteria

- `features_recomputable`: **PASS** (True)
- `intrinsics_match`: **PASS** (True)
- `anchor_gt_bad_proxy`: **PASS** (True)
- `proxy_gap_ge_0_1`: **PASS** (True)
- `miou_anchor_ge_0_5`: **PASS** (True)
- `miou_bad_le_0_2`: **PASS** (True)

## Overall: **PASS**

### Feature values (recomputed)

**anchor**
- `depth_nan_ratio`: 0.11387375767737186
- `denoise_retained_ratio`: 0.81787798500355
- `det_real_detection_ratio`: 0.0
- `sam_fill_rate`: 0.7799747173013317
- `sam_ontology_divergence`: 0.2503766921544423

**bad**
- `depth_nan_ratio`: 0.9472989194127125
- `denoise_retained_ratio`: 0.024278317488354375
- `det_real_detection_ratio`: 0.0
- `sam_fill_rate`: 0.01929450880565224
- `sam_ontology_divergence`: 0.6095853527194398
