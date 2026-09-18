# Stage 2 report — SC-general scale / freeze / holdout

**Gate: FAIL** (holdout fidelity). Frozen candidate package is at
`bo/sc_general/models.json` (deployment arm `pruned_lean`) but Stage 3 is
**blocked** pending a decision on the holdout bar.

Generated from:

- tables: `data/sc-general/stage2/{training_table,holdout_table,replay_audit}.csv`
- table gate: `data/sc-general/stage2/gate.md` (**PASS** — 174/174 replay match, lean-10 finite)
- train: `bo/sc_general/{models,ablation}.json`, `data/sc-general/stage2/train_summary.json`
- holdout: `data/sc-general/stage2/{holdout_scores,holdout_metrics,band_check,validation_gate}.*`
- arm comparison: `data/sc-general/stage2/arm_holdout_comparison.json`

Provenance: paper’s 120 + 54 = **bo-bayes** (`bo/bayes/training_table.csv`,
`bo/bayes/holdout_scores.csv`), not `bo/full_stage`.

---

## 1. Feature-table gate (bulk audit)

| check | result |
|---|---|
| training rows | 120/120 |
| holdout rows | 54/54 |
| replay prompt match | **174/174 PASS** |
| lean-10 finite | **PASS** |
| label-map sources | results.pkl 116, only_label.csv 58 |
| ring_count sources | log 172, state.pkl 2 (anchor loads) |

Lean-10 pool (K-row trio removed):

`depth_nan_ratio`, `denoise_retained_ratio`, `unfold_residual`, `orient_agreement`,
`ring_count_error`, `correspondence_f1@15`, `boundary_explained_edge@25`,
`chamfer_sym_px`, `sam_fill_rate`, `phase_incoherence_deg`.

---

## 2. Train / ablation (vs published bayes lean)

Published bayes numbers from `bo/bayes/acceptance_report.md`:
train **0.098 / 0.877**, LOFO **0.143 / 0.678**.

| arm | n | train MAE / Spearman | LOFO MAE / Spearman |
|---|---:|---|---|
| P(e) PQ-5 | 5 | 0.099 / 0.864 | 0.223 / 0.718 |
| P(c) SC-5 | 5 | 0.093 / 0.884 | 0.140 / **0.806** |
| P(e+c) lean-10 | 10 | 0.081 / 0.915 | 0.197 / 0.794 |
| legacy lean (K-row) | 5 | 0.098 / **0.877** | 0.143 / **0.678** |
| **pruned_lean (deploy)** | 4 | 0.086 / 0.904 | **0.112 / 0.828** |

Legacy arm reproduces the published train/LOFO numbers exactly → pipeline
sanity check OK.

**Deployment rule** (LOFO Spearman, require ≥1 PQ and ≥1 SC): selected
`pruned_lean` =

`correspondence_f1@15`, `sam_fill_rate`, `ring_count_error`, `depth_nan_ratio`

- RidgeCV α = 10.0, intercept = 0.350
- coef (scaled): F1 +0.082, fill +0.080, ring_err −0.045, depth_nan −0.064
- permutation control: **PASS** (real MAE 0.086 ≪ perm 0.196)
- contains SC-general (`correspondence_f1@15`); **no** K-row feature

### Delta sensitivity (full lean-10, F1/edge @8/@15/@25)

| delta | LOFO Spearman |
|---|---:|
| @8 | 0.789 |
| @15 (default) | 0.794 |
| @25 | 0.803 |

Stable; @25 slightly best on LOFO. Frozen package keeps δ=15 as planned.

### Leave-one-feature-out on lean-10 (LOFO Spearman after drop)

Worst drops (most harmful to remove): `orient_agreement` (0.757),
`depth_nan_ratio` (0.780), `boundary_explained_edge@25` (0.780).
Safest to remove: `unfold_residual` (0.807), `ring_count_error` (0.801),
`correspondence_f1@15` (0.800). Pruning kept F1 + fill + ring_err + depth_nan.

---

## 3. Holdout (54 = 27 anchor + 27 bad)

Published: MAE **0.086**, Spearman **0.827**, PairRank 27/27, alarm @0.5 TP27/FP0.

### Deployed `pruned_lean`

| metric | SC-general | published |
|---|---:|---:|
| MAE | 0.109 | 0.086 |
| Spearman | 0.817 | 0.827 |
| bootstrap CI95 (subset) | [0.761, 0.864] | — |
| PairRank | **27/27** | 27/27 |
| Alarm @0.5 | TP27 / **FP3** | TP27 / FP0 |
| Alarm 27/27 & 0 FP | τ ∈ {0.40…0.43} | τ=0.5 |

Per-family holdout MAE: staggered 0.126, continuous 0.122, complex **0.078**.

Pooled vs per-family Wilcoxon (subset MAE n=27): unified 0.109, per-family 0.100,
W=128, p=0.148 (ns).

False positives at τ=0.5 (anchors with proxy < 0.5): **3-2**, **3-5**, **4-4**
— exactly the three paper-panel cases that fell out of the refine band.

### Stage-2 gate checklist (`validation_gate.md`)

| check | result |
|---|---|
| LOFO Spearman ≥ 0.678 | **PASS** (0.828) |
| holdout Spearman ≥ 0.827 **or** MAE ≤ 0.086 | **FAIL** (0.817 / 0.109) |
| PairRank 27/27 | **PASS** |
| alarm 27/27 & 0 FP at some τ ∈ [0.4, 0.6] | **PASS** (τ≤0.43; 0.5 preferred = no) |
| lean has ≥1 SC-general | **PASS** |
| lean has no K-row | **PASS** |

**Overall: FAIL** on holdout fidelity only.

### All arms on holdout (decision table)

| arm | hold MAE / Sp | PairRank | alarm @0.5 | τ with 27/0 in [0.4,0.6] | clears hold bar? |
|---|---|---|---|---|---|
| P(e) | 0.130 / 0.812 | 27/27 | TP27 FP1 | yes (≤0.48) | no |
| P(c) | 0.103 / **0.824** | 27/27 | TP27 FP7 | **none** | no (closest Sp) |
| P(e+c) | 0.104 / 0.809 | 27/27 | TP27 FP5 | yes (≤0.44) | no |
| pruned_lean | 0.109 / 0.817 | 27/27 | TP27 FP3 | yes (≤0.43) | no |
| legacy_lean | **0.086 / 0.827** | 27/27 | TP27 FP0 | yes incl. 0.5 | **yes** (baseline) |

**No SC-general arm meets the published holdout MAE/Spearman bar.** Closest
rank correlation is P(c) at 0.824; closest calibrated alarm behaviour among SC
arms is pruned_lean / P(e) with a lowered τ.

---

## 4. Refine-band check for Stage 3

Criteria: anchor proxy ∈ [0.5, 0.7] and GT mIoU < 0.7.

| | cases |
|---|---|
| in band (n=6) | 1-4, 1-5, 2-2, 3-4, 4-1, 4-3 |
| ∩ paper nine | **1-4, 1-5, 2-2, 3-4, 4-1, 4-3** |
| paper only (out) | **3-2, 3-5, 4-4** (same three as alarm FP @0.5) |
| new only | ∅ |

`band_check.json` written. Stage 3 panel would shrink from 9 → 6 under the
frozen candidate unless the intercept/τ or feature set is revised.

---

## 5. Decision needed (Stage 3 blocked)

Options (do not start Stage 3 until one is chosen):

1. **Soften holdout gate** — accept pruned_lean (Sp 0.817, CI covers 0.827;
   LOFO +0.15 vs published; family-agnostic SC) and proceed with τ≈0.43 alarm
   and the 6-case refine panel.
2. **Redeploy P(c)** — best hold Spearman among SC arms (0.824) but **no**
   alarm τ in [0.4, 0.6] with 0 FP; would need recalibrated threshold outside
   the preferred window or a different alarm feature.
3. **Keep lean-10 / tune prune** — try alternate prune objective (holdout
   Spearman / MAE on a nested split, or force-keep edge/chamfer) and re-freeze.
4. **Reject SC-general for deployment** — keep legacy K-row lean for the paper’s
   calibrated numbers; use SC-general only as an ablation / complex-family
   diagnostic.

Recommend discussing (1) vs (3): LOFO and permutation strongly favour the new
SC signal; the miss is ~0.01 Spearman and ~0.023 MAE on holdout, with
intercept shift explaining the τ=0.5 FP trio.
