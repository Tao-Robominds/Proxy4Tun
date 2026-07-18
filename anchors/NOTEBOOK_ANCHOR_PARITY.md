# Notebook vs Anchor Parity — Master Report

**Document ID:** `anchors/NOTEBOOK_ANCHOR_PARITY.md`  
**Date:** 2026-07-18  
**Scope:** Compare SAM4Tun reference notebooks under `sam4tun/notebook/` with
parameterized anchor families under `anchors/`.

## Purpose

Anchors are promoted, reproducible ports of the notebooks. This report
catalogues every material difference in two categories:

1. **Implementation** — structural or algorithmic changes that are not
   exposed as JSON knobs (*untunable* in the sense that changing them requires
   code edits, not parameter files).
2. **Parameters** — tunable values externalized to `parameters_*.json`, including
   value mismatches vs notebook literals.

Parameters that exist **only in anchors** (no named notebook equivalent) are
highlighted in each family report.

## Family reports

| Family | Notebook | Anchor scripts | Default params | Detail report |
|---|---|---|---|---|
| T1/T2 | `sam4tun/notebook/t1&2.ipynb` | `anchors/t1&2/` | `parameters/`, `1-1/`, `2-1/` | [`t1&2/NOTEBOOK_PARITY.md`](t1&2/NOTEBOOK_PARITY.md) |
| T3 | `sam4tun/notebook/t3.ipynb` | `anchors/t3/` | `3-1-1/` | [`t3/NOTEBOOK_PARITY.md`](t3/NOTEBOOK_PARITY.md) |
| T4/T5 | `sam4tun/notebook/t4&5.ipynb` | `anchors/t4&5/` | `4-1/`, `5-1/` | [`t4&5/NOTEBOOK_PARITY.md`](t4&5/NOTEBOOK_PARITY.md) |

## Cross-family implementation themes

| Theme | T1/T2 | T3 | T4/T5 |
|---|---|---|---|
| Pipeline state (`state.pkl`, stage I/O) | Yes | Yes | Yes |
| Evaluation stage (`6_evaluation.py`) | Yes | Yes | Yes |
| `swap_tunnel_centers` as JSON flag | Yes | Yes | Yes |
| `deterministic_theta_orientation` | Optional (off) | **On** in `3-1-1` | Optional (off) |
| `residual_recentre` | Optional (off) | **On** in `3-1-1` | **On** in `5-1` only |
| Detection vertical-line fallback | Yes | Yes | Yes |
| Geometric SAM fallback | No | No | **Yes** (tunnels 4/5, 7-class) |
| Dedicated geometry module | No | `t3_geometry.py` | `t45_geometry.py` |

## Cross-family anchor-only parameters (summary)

Parameters present in anchor JSON or `params.get(...)` defaults but **not**
named in the corresponding notebook:

| Parameter | Families | Stage |
|---|---|---|
| `swap_tunnel_centers` | All | Unfolding |
| `deterministic_theta_orientation` | All | Unfolding |
| `residual_recentre`, `recentre_*` | All (code); enabled T3 `3-1-1`, T4/T5 `5-1` | Unfolding |
| `mask_theta_high_column` | T3 | Denoising |
| `coverage_mode`, `use_upsampled_surface`, `enable_outlier_interpolation`, `curvature_outlier_min`, `ring_spacing_factor` | T3, T4/T5 | Enhancing |
| `prompt_logic`, `uniform_k_snap`, `vertical_rho_mode`, `vertical_rho_*`, `pattern_tolerance` | T3, T4/T5 | Detection |
| `segment_order`, `use_original_label_distributions`, `geometry_profile`, `mirror_k_geometry`, `segment_loop_extra`, `crop_taper_mm`, `processing.*` | All | SAM |
| `slice_filter_mode`, `top_tube_*` | T4/T5 | Unfolding (`top_tube_*` only; filter is hardcoded) |
| `prompt_points` tree (T1/T2 SAM JSON) | T1/T2 | SAM |

## Highest-impact divergences (all families)

1. **T1/T2 detection** — oblique K-height offset signs inverted in anchor
   `t12_pattern` vs notebook Algorithm 4.
2. **T3 denoising** — notebook applies high angular gate on column `r` instead
   of `theta` (`mask_theta` line uses `r > 17.15`).
3. **T3 short subsets** — `residual_recentre`, `deterministic_theta_orientation`,
   and `uniform_k_snap` are required for labelled 10-ring runs; absent from notebook.
4. **T4/T5 SAM** — promoted anchors use **geometric fallback**, not full SAM,
   for tunnel IDs prefixed `4` or `5` with seven segments per ring.
5. **T4/T5 5-1** — `residual_recentre=true` and detection retune
   (`hough_threshold_vertical=5000` for synthetic ring columns).

## Methodology

- Notebook literals extracted from `.ipynb` source cells (grep + cell review).
- Anchor values taken from `parameters_*.json` and stage script `params.get`
  defaults.
- “Match” means same numeric value or equivalent formula; “anchor-only” means
  no named notebook parameter.
- Per-case overrides (`1-1/` vs `2-1/`, `4-1/` vs `5-1/`) documented in family
  reports where they differ from shared defaults.

## Related documents

- Anchor index: [`README.md`](README.md)
- Frozen runs: [`../data/anchors/README.md`](../data/anchors/README.md)
- Experiment lineage: [`../reports/anchors-summary.md`](../reports/anchors-summary.md)
