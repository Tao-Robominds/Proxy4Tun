# Pipeline sensitivity report: orientation, randomness, and label alignment

**Scope.** Lessons from the 2026-07 anchor cleanup and the re-verification runs
in `data/cleanup/`. The cleanup removed experimental leftovers from the
`anchors/` stage scripts (depth hole-fill hooks, dead theta gates, unused SAM
fallbacks). Re-running all five tunnels exposed a class of failures that had
nothing to do with the removed code: **the pipeline's output frame is not
pinned**, and downstream stages silently assume a specific orientation.

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
   mIoU: 0.850 (anchor 0.881; residual gap is background-edge IoU only).

**Lesson: `segment_order` is coupled to theta handedness.** Any change to
orientation handling must be accompanied by a `segment_order` review. The two
parameters are only valid as a pair.

## 4. General solution for future development

Ideally, orientation should be *derived from the data*, not frozen as booleans:

1. **Pin h explicitly**: choose the bounding-rect end deterministically from a
   data property (e.g. always start from the end with lower mean ring index,
   or the geographically southern/western end), not from `argmin` tie-breaking
   plus a compensating `swap_tunnel_centers` flag.
2. **Pin theta explicitly**: `deterministic_theta_orientation: true` everywhere
   (derive handedness from the travel direction, never from the Tz sign of a
   RANSAC fit).
3. **Self-check after unfolding**: verify orientation invariants before
   heavier stages run, e.g. correlation of h with ring index must be positive;
   the K-block (or other known asymmetric feature) must sit on the expected
   theta side. Fail fast with a clear message instead of producing a mirrored
   map.
4. **Seed all stochastic components** (`random_seed`) so accepted runs can be
   reproduced bitwise.
5. **Freeze anchors as (code + params + artifacts) triples.** The 3-1-1 and
   4-1 regressions were code/config drift: frozen params were only correct
   relative to the code revision that froze them. When stage code changes,
   re-verify each anchor and re-freeze the params if orientation semantics
   moved.

## 5. Parameter tuning guide (post-cleanup)

Tune in this order — later knobs are meaningless while earlier ones are wrong:

1. **Orientation block** (binary, decide once per tunnel):
   `swap_tunnel_centers`, `deterministic_theta_orientation` (always `true`),
   `segment_order` (must match the resulting theta handedness), `random_seed`.
   Validation: depth map visually matches expected layout; confusion matrix is
   diagonal, not a permutation.
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

Per-tunnel state after this cleanup (see `data/cleanup/README.md` for the
artifact tree): 1-1 = 0.789, 2-1 = 0.903, 3-1-1 = 0.850, 4-1 = 0.636,
5-1 = 0.689. The 4-1 anchor value (0.741) predates orientation pinning and was
only reachable when unpinned RANSAC happened to land on the favourable mirror;
recovering it deterministically requires re-tuning the detection/SAM stages on
the pinned orientation (step 4–5 above).
