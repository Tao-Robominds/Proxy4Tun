# Archived: Pooled Cross-Family BO Experiment (superseded)

**Status:** archived — current work is the **per-family** proxy in [`family/report.md`](family/report.md).  
**Dates:** 2026-07-19 (pooled campaign + ablation); superseded 2026-07-20 by family BO.  
**Original artifacts** (still on disk, gitignored): `data/{1-1,3-1-1,5-1}-bo-proxy/`.

This file folds the former `report.md`, `design-rationale.md`, `analysis/summary.md`,
`ablation/report.md`, and the unused `scaleup-plan.md` into one record so those
paths can be deleted.

---

## 1. What this experiment was

R4 used BO to discover critical parameters. Anchors already exist, so **R5**
repurposed BO as a **dataset generator**: ~40 mixed EI/uncertainty trials per
family (1-1, 3-1-1, 5-1), harvest GT-free Tier-1 intrinsics, fit a Ridge mIoU
proxy. Unfolding frozen (canonical orientation); stage-1 copied from
`data/anchors/<case>/`.

| Case | Family | Dims | ok trials | mIoU range |
|------|--------|-----:|----------:|------------|
| 1-1 | t1&2 | 12 | 40 | 0.035–0.819 |
| 3-1-1 | t3 | 15 | 35 | 0.043–0.884 |
| 5-1 | t4&5 | 13 | 33 | 0.036–0.820 |

**108** successful trials total. Validation gates all PASS (ΔmIoU = 0 vs
promoted anchors).

Purpose shift vs R4: params known; goal is proxy discovery. Acquisition mixes
EI with uncertainty so mid/low quality is populated (pure EI would starve the
proxy). Per-metric guardrails dropped — single proxy-score alarm only.

---

## 2. Design highlights (methodology)

- **Aesthetic-metric trap:** form metrics can look good under fallback. Defenses:
  provenance-aware computation, sign-stability screen, partial correlation vs
  `det_real_detection_ratio`. Confirmed: `det_x_spacing_cv` raw Spearman +0.32
  vanishes to partial-r ≈ −0.07 after controlling for fallback.
- **Hierarchical model:** Tier-0 orientation gates → Tier-1 Ridge proxy → alarm.
- **Permutation blindness:** label-swap failures need Tier-0 / detection plumbing;
  the proxy cannot see them from form alone.
- **Implementation notes:** run ids must keep tunnel prefix (`5-1-t000`) for
  T4/T5 geometric SAM fallback; `random_seed` ported into t1&2 and t4&5 unfolding.

---

## 3. Pooled Ridge proxy (pre-block taxonomy)

Selected features after screens: denoise/depth ratios, detection provenance,
`det_y_std`, SAM fill/completeness/ontology.

| Metric | Value |
|--------|------:|
| In-sample MAE | 0.097 |
| In-sample Spearman | 0.740 |
| LOFO MAE (t1&2 / t3 / t4&5) | 0.067 / 0.204 / 0.070 |
| Permutation control | **pass** (real 0.067 ≪ null 0.307) |
| Free sibling \|err\| (2-1, 4-1) | 0.053, 0.053 |
| Best alarm F1 (held-out t1&2) | 0.88 |

Top Spearman: `sam_fill_rate` +0.66, `denoise_retained_ratio` +0.62,
`det_real_detection_ratio` +0.60 / `det_fallback_ratio` −0.60.

**Noise floor (full pipeline, varying seed):** 1-1 σ≈0.003, 5-1 σ≈0.012,
**3-1-1 σ≈0.26** (seed still swings quality 0.097–0.743). Campaigns used frozen
stage-1 so this variance did not pollute the BO dataset.

---

## 4. Three-block ablation (rev2)

Pre-registered:

| ID | Statement |
|----|-----------|
| H1 | B1+B2 predicts mIoU in the correct-alignment regime |
| H2 | Tier-1-only sets miss alignment collapses |
| H3 | Adding B3 (phase/order priors) flags collapses |

| Block | Role | Features |
|------:|------|----------|
| B1 | Coherence | spacing CV, y-std, ring-count err, SAM fill/completeness/size/ontology |
| B2 full | Evidence | retained, nan/outlier, midpoint, real/fallback, n_points |
| B2lean | Lean evidence | retained, nan, real, fallback (4 feats; perm-pass) |
| B3 | Attainable priors | phase offset, order match, boundary-evidence lag |

**rev2 decisions:** B3 scored only against a frozen per-tunnel clock table (no
same-run GT); stagger dropped; detection-only B3 substitute **rejected**
(boundary evidence invariant to label identity); `depth_outlier_ratio` drives
full-B2 perm failure → B2lean.

| Set | P1 Spearman | Perm | Separates rep0/rep2? |
|-----|------------:|:----:|:--------------------:|
| B1 | 0.45 | pass | no |
| B2 full | 0.55 | fail | no |
| B2lean | 0.75 | pass | no (blanket alarm on all t3) |
| B1+B2lean | **0.54** | **pass** | no* |
| B1+B2lean+B3 | 0.82 | pass | yes |

\* Historical T3 label-collapse is fixed in stage-4 `uniform_k_snap` (below),
not by the proxy.

**Hypothesis outcomes:** H1 supported in lean form; H2 supported (Tier-1 cannot
discriminate coherent-but-misaligned); H3 supported when a clock table exists —
but that prior is deployment-heavy, so the **deployable** choice became
**B1+B2lean**.

---

## 5. T3 `y_star` collapse — fixed in detection, not the proxy

Mechanism: `uniform_k_snap` sets every ring's K Y to `median(anchor detections)`.
SAM labels outward from that row. Seed-12 jumped `y_star` 1550 → 2902 px → mIoU
0.097.

**Fix:** clamp in [`anchors/t3/4_detection.py`](../anchors/t3/4_detection.py) to
design rows `[1123, 1553]` (`k_row_action=snap`). Validated: Gate A mIoU 0.850
accept; Gate B seed-12 snap → mIoU 0.740. This is T3 detection plumbing.

---

## 6. Why this design was superseded

1. Cross-family LOFO assumes transfer that family-specific training does not need.
2. Seed-perturbation scale-up for B3 rate estimates was designed but **not run**;
   B3 stayed optional and was dropped from the family-BO feature set.
3. **Per-family BO** (train within family on 1-1+2-1 / 3-1-1 / 4-1+5-1; test on
   all other subsets with sibling-anchor + known-bad configs) is the current
   claim surface — see [`family/report.md`](family/report.md).

**Carry-forward into family BO:** feature set **B1+B2lean**; empirical seed
pinning; T3 K-row clamp in anchors; campaign runner + intrinsics extractor.
