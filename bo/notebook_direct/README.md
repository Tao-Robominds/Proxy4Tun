# Notebook-faithful baseline on 27 holdout subsets

Apply the **notebook-mode parameter overlay** (expert-tuned notebook
literals + all parametric adaptations off) to the 27 held-out subsets via
the original per-family anchor stage scripts.

This is **not** a re-execution of the `.ipynb` cells (hardcoded paths /
case constants). It is the closest parametric reconstruction of
`sam4tun/notebook/t1&2.ipynb`, `t3.ipynb`, `t4&5.ipynb` that the protected
anchor runners can express. See
[`anchors/NOTEBOOK_ANCHOR_PARITY.md`](../anchors/NOTEBOOK_ANCHOR_PARITY.md).

## What is turned off / restored

| Knob | Notebook-mode value |
|---|---|
| `canonical_orientation` | `false` |
| `deterministic_theta_orientation` | `false` |
| `residual_recentre` | `false` |
| `random_seed` | removed |
| `swap_tunnel_centers` | T1/T2: `false`; T3: `true`; T4/T5: `false` |
| T3 `uniform_k_snap` | `false` |
| T3 `mirror_k_geometry` | `false` |
| T3 `use_upsampled_surface` | `false` |
| T3 `enable_outlier_interpolation` | `false` |
| T3 `segment_order` | restored to standard (non-reversed) |
| T1/T2 literals | notebook column of `t1&2/NOTEBOOK_PARITY.md` |
| T5 detection retune | restored to 4-1 / notebook thresholds |

## Untunable caveats (remain at anchor behaviour)

These cannot be reverted without editing protected `anchors/` scripts:

1. **T4/T5 geometric SAM fallback** — hardcoded in `anchors/t4&5/5_sam.py`
   (`tunnel_prefix in {4,5}` and `segment_per_ring==7`). No JSON key.
2. **T3 `mask_theta` column fix** — notebook applied high bound to `r`;
   anchor keeps `mask_theta_high_column: "theta"`.
3. **T1/T2 oblique K-offset sign fix** in shared `4_detection.py`.
4. **T3 `n_segment` window** — notebook `[11,11]` is a 50-ring station index;
   holdouts are 10-ring slices, so overlays keep subset-scale `[2,8]`.
5. Pipeline shell (`state.pkl`, `6_evaluation.py`) — orchestration only.

## Layout

```
bo/notebook_direct/
  params/{1-1,2-1,3-1-1,4-1,5-1}/   # notebook-mode overlays (never edit anchors/)
  run_holdouts.py                   # campaign driver
  gate.md                           # single-instance validation evidence
  report.md / scores.csv            # comparison vs unified 0.722
data/bo/notebook_direct/<subset>/      # run artifacts (never data/anchors|baseline|bo)
```

## Sibling mapping

| Holdout | Profile | Params dir |
|---|---|---|
| `1-*` | `t1&2` | `bo/notebook_direct/params/1-1` |
| `2-*` | `t1&2` | `bo/notebook_direct/params/2-1` |
| `3-*` | `t3` | `bo/notebook_direct/params/3-1-1` |
| `4-*` | `t4&5` | `bo/notebook_direct/params/4-1` |
| `5-*` | `t4&5` | `bo/notebook_direct/params/5-1` |
