# Label-free orientation gate (swap: ring-metadata → geometry)

## Why

The Tier-0 validity gate (`orient_invariant_ok`) previously checked
`corr(h, ring)` on `unwrapped.csv`. The `ring` column is annotation metadata
carried in from the benchmark subset files — so, as implemented, the gate
could not run on a truly unlabeled tunnel. It never fed the proxy score
(no trained weight uses it), but it was a deployment-dependency worth
removing.

## What changed (`bo-unified/intrinsics.py`)

- New `compute_orient_axis()`: the gate invariant is now
  `|corr(h, t)| >= 0.6`, where `t` is the projection of the (x, y, z) cloud
  onto its first principal axis (SVD on a 50k-point subsample, seed 0).
  For a canonical unwrap, `h` *is* the axial coordinate, so |corr| ≈ 1.
  No annotation columns are read.
- Axis sign is made deterministic (largest-|component| positive). An
  optional `h_axis_sign` in `parameters_unfolding.json` adds a direction
  check. Note the sign is **per-case** (world-frame dependent), not
  per-family: e.g. 1-2 gives +1 while 2-1 gives −1 under the same family
  params. No `h_axis_sign` values are currently recorded, so the gate is
  magnitude-only.
- `compute_orient_from_unwrapped()` (ring-based) is kept as a legacy
  diagnostic (`orient_h_ring_corr`); it degrades gracefully when the ring
  column is absent. It no longer sets `orient_invariant_ok`.
- New Tier-0 key: `orient_axis_corr`.

## Rejected alternatives

- `corr(h, scan/row order)`: fails on 3-6, whose subset file has ring 10
  appended out of order (corr −0.56, marginal vs threshold).
- Family-level expected axis sign: invalid, sign varies per subset within
  a family (world-frame dependent).

## Verification (read-only recompute; stored artifacts untouched)

- 134 runs checked: all 63 training trials (2-1/3-1/5-1 campaigns), all
  registered holdout runs with `unwrapped.csv`, and the 3 frozen anchors.
- `|orient_axis_corr|` min **0.774** (curved complex tunnels), max 1.000 —
  all above the 0.6 threshold; straight tunnels sit at ≈1.0.
- Invariant pass: **134/134**, identical to the ring-based gate's verdicts,
  so no training row, holdout score, or report number changes.
- End-to-end `extract_intrinsics` on 2-1-t000 reproduces every stored
  non-orientation metric exactly.

## Paper wording

"Run validity is established by a label-free canonical-orientation check:
the unwrapped axial coordinate must be affine-consistent with the tunnel
axis estimated from the point cloud itself (|corr| ≥ 0.6). Ring metadata is
not used."
