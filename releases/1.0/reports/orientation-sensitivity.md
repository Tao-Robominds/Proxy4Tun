# Pipeline sensitivity report: orientation, randomness, and label alignment

**Scope.** Lessons from the 2026-07 anchor cleanup, the intermediate runs in
`data/cleanup/`, and the canonical-orientation promotion now living in
`anchors/<family>/<case>/` + `data/anchors/`. The cleanup removed experimental
leftovers from the stage scripts (depth hole-fill hooks, dead theta gates,
unused SAM fallbacks). Re-running all five tunnels exposed a class of failures
that had nothing to do with the removed code: **the pipeline's output frame
was not pinned**, and downstream stages silently assumed a specific
orientation.

## 1. The failure class: orientation is decided three separate times

The unrolled (theta, h) frame that everything downstream consumes is fixed by
three independent decisions inside `1_unfolding.py`:

| Decision | Mechanism | Failure mode |
|---|---|---|
| h direction (axial) | `argmin` over the two short edges of the min-area bounding rectangle, then `swap_tunnel_centers` | The two short edges are near-equal in length; which one `argmin` picks depends on floating-point noise in the hull. A code change anywhere upstream can flip it permanently. `swap_tunnel_centers` then flips it again — its correct value depends on the arbitrary `argmin` outcome, so a frozen `true`/`false` is not portable across code versions. |
| theta handedness (circumferential) | legacy: sign of `cross(AB, BC).z` ∝ −Tz of the fitted centreline | On short subsets the grade Tz ≈ 0, so the sign is decided by **RANSAC sampling noise** — the mirror flips at random between runs. This caused 4-1 to swing between mIoU 0.74 and 0.16 with identical params. |
| theta zero / band position | ellipse fit + `residual_recentre` | Less catastrophic: degrades the r-band and NaN fraction rather than mirroring the map. |

**Key observation: orientation errors are not gradual.** A flip produces either
a near-total detection failure (Hough geometry mismatch, mIoU collapses to
0.1–0.4) or — more insidiously — a **clean label permutation** (see §3) where
segmentation quality is perfect but asymmetric classes swap with their mirror
partners. Watch for confusion matrices that are a permutation matrix: that is
an orientation bug, not a segmentation bug.

## 2. What seeding does and does not fix

`random_seed` (added to `anchors/t3/1_unfolding.py`) pins `random`, `np.random`
and all `RANSACRegressor(random_state=...)` calls. This makes runs **bitwise
repeatable**, which is necessary for debugging, but:

- It does **not** make the orientation *correct* — it freezes whichever
  orientation the seeded RANSAC happens to produce. Seeds 0–2 on 3-1-1 all
  reproduced the same *wrong* h direction (mIoU 0.08–0.43).
- Reproducibility and correctness are separate requirements. Fix correctness
  with explicit orientation pinning first, then add a seed for repeatability.

## 3. The 3-1-1 case study (0.335 → 0.850)

1. All recent runs had the h axis reversed vs. the frozen anchor
   (`corr = −0.999` on h between runs). Root cause: the bounding-rect
   `argmin` outcome had flipped since the anchor era, so the frozen
   `swap_tunnel_centers: true` now produced the *wrong* direction.
   Setting it to `false` restored the anchor's direction vector
   (`[-8.56, 8.53]`).
2. With h fixed and `deterministic_theta_orientation: true`, the depth map,
   detected lines, and SAM masks were visually excellent — but mIoU was 0.335.
   The confusion matrix was a clean mirror permutation: pred B2 ↔ gt B1,
   pred A3 ↔ gt A1 (K and A2, the symmetric blocks, were correct).
3. Cause: theta now runs mirrored relative to the anchor map, and the SAM
   stage tiles blocks in a hardcoded circumferential order. Fix: reverse
   `segment_order` in `parameters_sam.json` to `[K, B2, A3, A2, A1, B1]`.
   mIoU: 0.850 (vs prior legacy frozen 0.881; residual gap is background-edge IoU only).

**Lesson: `segment_order` is coupled to theta handedness.** Any change to
orientation handling must be accompanied by a `segment_order` review. The two
parameters are only valid as a pair.

## 4. Key finding: in the notebooks, the human *was* the canonicalization step

The expert-tuned notebooks (`sam4tun/notebook/t1&2.ipynb`, `t3.ipynb`,
`t4&5.ipynb`) contain **no orientation handling at all**: no
`swap_tunnel_centers` (that knob was invented during productionization to
reproduce the notebook's historical output), no deterministic theta, no random
seeds, and a single hardcoded `block_to_label`. Yet they produced correct
results — because the author executed cells interactively, looked at the
depth-map plot, and wrote every downstream constant (block order, K-geometry
mirroring, `y_bounds`, prompt coordinates) to match whatever orientation that
one execution happened to produce. Correctness was enforced by eyeballs, not
code. If a rerun had flipped the frame, the author would have silently
re-adjusted the constants, leaving no trace.

Productionization inherited the constants without inheriting the human. That
is the root cause of every orientation regression in this report: the frozen
booleans encode one lucky execution, and nothing in the pipeline re-checked
them. **Replacing that invisible human glance with an explicit, data-derived
canonicalization step is therefore one of the key improvements over the
expert-tuned process** — it converts tacit expert knowledge ("the map looks
right") into a mechanical invariant the pipeline enforces on every run.

## 5. Implemented solution: canonical orientation (2026-07)

All three family `1_unfolding.py` scripts support
`canonical_orientation: true`. That flag is **on in every promoted case**
under `anchors/<family>/<case>/` (the code default remains `false` only so
ad-hoc param dirs without the key keep the legacy path).

- **h direction from the data**: the input cloud's `ring` column is monotonic
  along the tunnel. The bounding-rect centre pair is oriented so that travel
  runs toward increasing ring index. `swap_tunnel_centers` is ignored — the
  `argmin` tie-break can no longer flip the frame across code versions.
- **theta handedness from travel direction**: `deterministic_theta_orientation`
  is forced on, so the RANSAC Tz-sign lottery is out of the loop. Because both
  axes derive from the same travel direction, flipping h rotates the map 180°
  instead of mirroring it — which is why one standard `segment_order` works
  across tunnels.
- **`h_ring_sign` (+1 default / -1)**: declares which way the tuned downstream
  geometry expects h to run relative to ring index. Unlike
  `swap_tunnel_centers`, its meaning is defined by the data, not by code
  internals, so it stays valid across code changes.
- **Post-unwrap invariant**: `corr(h, ring)` must match `h_ring_sign`
  (|corr| > 0.5) or the stage exits with an error instead of producing a
  mirrored map. Observed |corr| is ~0.98 on all five tunnels.

**Promoted** as the default anchors: params in `anchors/<family>/<case>/`,
artifacts in `data/anchors/<case>/` (gate proof: `logs/canonical-gate-proof.md`).
Pre-canonical frozen trees were removed.

| Case  | Promoted mIoU | Prior legacy frozen | Settings beyond defaults |
|-------|---------------|---------------------|--------------------------|
| 1-1   | 0.787         | 0.815               | none |
| 2-1   | 0.874         | 0.900               | none |
| 3-1-1 | 0.850         | 0.881               | `h_ring_sign: -1`, reversed `segment_order`, `random_seed: 1` |
| 4-1   | 0.635         | 0.741               | none |
| 5-1   | 0.808         | 0.681               | none — **beats the prior frozen run**; the canonical frame suits the geometric tiler better |

3-1-1 keeps `h_ring_sign: -1` because its downstream T3 geometry (detection
offsets, recentre band) was tuned on the anchor-era frame; in the +1 frame the
recentre residual triples (30 cm vs 9 cm) and mIoU drops to 0.43. That is a
quality coupling, not an orientation bug — re-tuning stages 2–5 in the +1
frame would remove the exception.

Remaining practices that still apply:

1. **Seed all stochastic components** (`random_seed`) so accepted runs can be
   reproduced bitwise (reproducibility is separate from correctness).
2. **Freeze anchors as (code + params + artifacts) triples.** The 3-1-1 and
   4-1 regressions were code/config drift: frozen params were only correct
   relative to the code revision that froze them. When stage code changes,
   re-verify each anchor and re-freeze the params if orientation semantics
   moved.

## 6. Parameter tuning guide (post-cleanup)

Tune in this order — later knobs are meaningless while earlier ones are wrong:

1. **Orientation block** (decide once per tunnel):
   `canonical_orientation: true` + `random_seed`; only add `h_ring_sign: -1`
   (with the matching reversed `segment_order`) when downstream geometry was
   tuned on a legacy frame. `swap_tunnel_centers` is legacy-only.
   Validation: the canonical invariant passes in the stage-1 log; confusion
   matrix is diagonal, not a permutation.
2. **Centreline / unroll quality**: `polynomial_degree`, `num_samples_factor`,
   `residual_recentre` + `recentre_*` (T3: without recentre the narrow r-band
   discards ~46% of lining points on short subsets). Validation: recentre
   residual max ≲ 10 cm; low NaN fraction in the depth map.
3. **Band selection** (denoising): `mask_r_low/high`, theta gates. Validation:
   point-retention fraction, class balance of retained points.
4. **Detection**: Hough/rho settings. Validation: `detected_lines.png` —
   ring boundaries and K-Y lines land on visible seams.
5. **SAM geometry**: `segment_width`, `K_height`/`AB_height`, `angle`,
   `y_bounds`. Only tune when steps 1–4 are validated; per-class IoU
   differences (not permutations) are the signal here.

Per-tunnel state: see the promoted table in §5 (`data/anchors/`). Intermediate
cleanup-era runs remain under `data/cleanup/` for lineage only. The prior
legacy 4-1 value (0.741) was only reachable when unpinned RANSAC happened to
land on the favourable mirror; recovering it deterministically requires
re-tuning detection/SAM on the pinned orientation (steps 4–5 above).
