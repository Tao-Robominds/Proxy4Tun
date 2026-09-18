# Proxy4Tun Bayesian Optimization — consolidated experience report

_Consolidation date: 2026-09-12. Campaigns ran 2026-07-18 → 2026-08-03
(with analysis/figure touch-ups through Sep 2026)._

This document is the single narrative for every BO / proxy / refinement
campaign that previously lived as seven top-level folders. Code is under
[`bo/`](README.md); frozen artifacts under [`data/bo/`](../data/bo/MANIFEST.md).

## 1. Purpose and lineage

Goal: learn a **GT-free mIoU proxy** that ranks tunnel-lining segmentation
runs, flags known-bad configs, and later selects which holdouts enter a
self-refinement loop — without destroying the promoted anchors.

```
archive_v0 (Jul 18–20)     per-family GP BO on family-local anchors
        │  data/bo campaigns removed 2026-07-21
        ▼
unified (Jul 21)           retarget to anchors/unified; ingest historical trials
        │
        ├──────────────────────────────┐
        ▼                              ▼
elegant (Jul 22–23)              reflect_pilot → proxy_scale (Jul 28)
  3-anchor lean Ridge                  scaled-proxy refinement band
  v1 → v2 (regime-neutral)
        │
        ▼
full_stage (Jul 25–28)         paper five-feature lean proxy (stages 1–6)
        │
        ├──────────────────────────────┐
        ▼                              ▼
bayes (Aug 2–3)                notebook_direct (Jul 28)
  Sobol + GP acquisition         notebook-faithful baseline panel
```

| Date | Milestone |
|---|---|
| Jul 18–20 | First family BO + Ridge proxy (`archive_v0`) |
| Jul 21 | Unified pipeline + ingest; `data/bo` campaigns cleared |
| Jul 22–23 | Elegant 3-anchor lean proxy; T3 confound found; v2 fix |
| Jul 25–28 | Full-stage 40/family; paper lean features frozen |
| Jul 28 | Notebook baseline + proxy-scale refinement PoC |
| Aug 2–3 | Bayesian (Sobol+GP) redo; acceptance vs Sobol-only |
| Sep 6/12 | Figure regenerators / score helpers touch-ups |
| Sep 12 | Package + `data/bo/<phase>/` consolidation |

## 2. Per-phase results

### 2.1 archive_v0 (historical)

- **Question:** Can a per-family Ridge on BO intrinsics predict mIoU?
- **Space:** Family-local anchors (`t1&2`, `t3`, `t4&5`); stages 2–6.
- **Outcome:** Working family proxies and holdout gates; campaigns later
  removed (see `data/bo/archive_v0/REMOVED_SEE_BO_UNIFIED.txt`). Training
  rows lived on into `bo/unified/family/`.

### 2.2 unified

- **Question:** Does the same proxy stack transfer to `anchors/unified`?
- **Design:** Ingest historical trials (225 rows); no fresh BO by design.
  Per-family + pooled Ridge (B1+B2lean). Stages 2–6 overlays only.
- **Headline:** Train MAE **0.076**, pooled Spearman **0.885**; holdout MAE
  family **0.110** / unified **0.121**. Gate mIoUs: 1-1 **0.800**, 3-1
  **0.850**, 5-1 **0.818**.
- **Artifacts:** `data/bo/unified/` (63 G). Code: `bo/unified/`.

### 2.3 elegant

- **Question:** Can one pooled lean proxy on three train anchors (2-1, 3-1,
  5-1) generalize across the panel?
- **v1 confound:** `det_real_detection_ratio` tracked lining regime (T3
  continuous vs staggered/complex), not quality — continuous holdouts
  systematically underestimated (3-6 proxy 0.44).
- **v2 fix:** Drop regime feature; use row/phase coherence features.
  3-6 proxy lifts **0.44 → 0.80**. Train MAE 0.102, Spearman 0.815
  (artifact-complete subset).
- **Artifacts:** `data/bo/elegant/` (97 G). Deployment default:
  `bo/elegant/family/models_v2.json`.

### 2.4 full_stage (paper calibration)

- **Question:** Restore 40 trials/family with **all six stages** tunable,
  including stage-1 geometry in the candidate set.
- **Training:** 120 rows (reuses 75 elegant-v2 + 55 new full-pipeline).
- **Frozen lean features (5):**
  `depth_nan_ratio`, `denoise_retained_ratio`, `sam_fill_rate`,
  `det_row_residual_px`, `det_row_gated`.
- **Headline (published):** Holdout Spearman **0.848**, MAE **0.071**,
  alarm **27/27** TP at τ=0.5. Stage-1 candidates did not survive the
  coefficient threshold (kept in ablation; hard gates deferred to agents).
- **Artifacts:** `data/bo/full_stage/` (94 G). Tables:
  `bo/full_stage/{training_table.csv,holdout_scores.csv,models.json}`.

### 2.5 bayes

- **Question:** Replace Sobol-only exploration with Sobol init + GP
  (Matérn ν=2.5) uncertainty-max acquisition — same lean feature set.
- **Campaign:** 40 ok trials/case (target 32 Sobol + 8 GP in gate; full
  campaign 24+16). Best mIoU: 2-1 **0.838**, 3-1 **0.622**, 5-1 **0.833**.
- **Acceptance vs published Sobol-only:** PoC panel identical **PASS**;
  alarm 27/27 **PASS**. Holdout MAE drift **0.071 → 0.086**; train Spearman
  **0.853 → 0.877**. Clustered Spearman CI ≈ **[0.75, 0.89]**.
- **Artifacts:** `data/bo/bayes/` (200 G). Figure regen:
  `bo/bayes/plot_figures.py` → `paper/Proxy4Tun/figs/`.

### 2.6 proxy_scale + reflect

- **Question:** Can the frozen proxy select a refine band and drive
  multi-round agent overlays without GT?
- **Rule:** Clip proxy to [0,1]; refine band **[0.5, 0.7)**; 3 rounds;
  monotone accept vs anchor.
- **Gains (examples):** 4-4 **+0.353** mIoU; large lifts on 1-4 / 1-5;
  4-3 failed to beat anchor in some arms.
- **Artifacts:** `data/bo/reflect/` (72 G). Selections/reports:
  `bo/proxy_scale/`. Parallel blind redo: `gpt56-refinement/`
  (denies reading proxy_scale recipes).

### 2.7 notebook_direct

- **Question:** What does a notebook-faithful (parametric adaptations off)
  baseline score on the 27-subset panel?
- **Headline:** Mean mIoU **0.456** vs unified sibling-anchor **0.722**
  (Δ **−0.265**). Confirms the Bayesian/unified stack is not a free lunch
  from the original notebook knobs.
- **Artifacts:** `data/bo/notebook_direct/` (33 G).

## 3. Manuscript figures ↔ producers

| Figure (under `paper/Proxy4Tun/figs/`) | Producer |
|---|---|
| `proxy_training_fullstage.pdf` | `bo/bayes/plot_figures.py` (bayes tables) or `scripts/drawing/plot_proxy_fullstage.py` (full_stage tables) |
| `proxy_holdout_fullstage.pdf` | same |
| `ablation_results.pdf` | `bo/bayes/plot_ablation_results.py` |
| `refinement_results.pdf` | `bo/bayes/plot_refinement_results.py` |
| Early motivation/pipeline PDFs | `bo/elegant/paper/figs/` (historical copies) |

Paper headline numbers (0.848 / 0.071 / 27/27) are the **full_stage**
Sobol-only calibration; bayes is the exploration-method variant with
documented drift.

## 4. Lessons and failure modes

1. **Regime confound beats quality signal.** A detection-ratio feature that
   correlates with lining type (T3 continuous) destroyed holdout ranking
   until removed (elegant v1 → v2).
2. **Artifact completeness matters.** Gated row residual / phase features
   need kept depth & detection artifacts; that forced the elegant-v2
   subset and the full_stage backfill.
3. **Stage-1 is high leverage but not free.** Varying unfolding helped
   coverage; lean pruning still dropped stage-1 features. Residual >10 cm
   unlock is an agent policy, not a proxy coefficient.
4. **Proxy ≠ GT.** Refinement must be monotone in the proxy; 4-3 shows
   agent rounds can fail to beat the sibling anchor.
5. **Exploration method drift is real.** Sobol+GP kept the PoC panel and
   alarm, but moved holdout MAE by +0.015 — report both, freeze one for
   the paper body.

## 5. Storage inventory

| Path | Size | Role |
|---|---:|---|
| `data/bo/bayes` | 200 G | Bayesian trials |
| `data/bo/elegant` | 97 G | Lean trials + holdouts |
| `data/bo/full_stage` | 94 G | Full-pipeline trials |
| `data/bo/reflect` | 72 G | Reflection rounds |
| `data/bo/unified` | 63 G | Unified holdouts |
| `data/bo/notebook_direct` | 33 G | Notebook baseline |
| `data/bo/archive_v0` | 8 K | Removed-campaign marker |
| **Total** | **≈ 559 G** | Frozen |

**Pruning candidates (not deleted):** `state.pkl`, `.npy`, preview PNGs
inside trial `runs/` — especially under `bayes/`. Keep params, manifests,
intrinsics, evaluation, and anything referenced by registries / scores.

## 6. How to run a new campaign

```bash
# Never write under data/bo/ — it is protected by pipeline_io.
export PROXY4TUN_BO_DATA_ROOT="$PWD/data/my-bo-exp"
mkdir -p "$PROXY4TUN_BO_DATA_ROOT"

# Example: small bayes smoke (after single-instance gate per project rules)
./venv/bin/python bo/bayes/run_bayes_trials.py \
  --case 3-1 --n0 4 --n-gp 2 --seed 0
```

Path helpers: `bo.paths.DATA_ROOT` respects `PROXY4TUN_BO_DATA_ROOT`.
Symlinks `data/bo-unified` → `data/bo/unified` (etc.) keep ~700 embedded
strings in historical CSV/JSON valid without rewriting result files.
