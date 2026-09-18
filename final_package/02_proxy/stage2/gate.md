# Stage-2 feature-table gate
Generated 2026-09-12T18:48:52.833967
Command: `./venv/bin/python bo/sc_general/build_tables.py`

## Counts
- training rows: 120 (expect 120)
- holdout rows: 54 (expect 54)
- lean-10: `['depth_nan_ratio', 'denoise_retained_ratio', 'unfold_residual', 'orient_agreement', 'ring_count_error', 'correspondence_f1@15', 'boundary_explained_edge@25', 'chamfer_sym_px', 'sam_fill_rate', 'phase_incoherence_deg']`

## Replay prompt match
- 174/174 exact (criterion: all)
- **PASS**

## Lean-10 finite
- all lean-10 features finite on all rows
- **PASS**

## Label-map sources
```
{
  "results.pkl": 116,
  "only_label.csv": 58
}
```

## Ring-count sources
```
{
  "log": 172,
  "state.pkl": 2
}
```

## Complex-family label sources (train)
```
{
  "only_label.csv": 40
}
```

## Overall: **PASS**
