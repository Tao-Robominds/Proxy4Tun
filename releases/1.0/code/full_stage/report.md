# bo-full-stage report

## Story in one paragraph

We restore the **40 trials per family** design with artifact-complete runs, make **all six pipeline stages tunable**, and put stage-1 geometry (centreline residual, orientation agreement) into the Evidence candidate set — no hard orientation/residual gates in the main protocol. The frozen lean proxy is trained on 120 rows (40×3), reuses all 75 artifact-complete v2 trials, and adds 55 new full-pipeline trials that vary stage 1. Holdout ranking and bad-run flagging match or beat v2. Lean pruning kept five features; the two stage-1 candidates did not survive the coefficient threshold — they remain in the candidate set and in the ablation, and hard gates over them are deferred to future reflective agents.

## Corrected campaign history

| Campaign | Trials / family (2-1 / 3-1 / 5-1) | Total | Artifacts | Stage 1 |
|---|---:|---:|:---:|---|
| v1 (`bo/elegant/.../training_table.csv`) | 40 / 40 / 40 | 120 | no | frozen |
| v2 (`.../training_table_v2.csv`) | 14 / 40 / 21 | 75 | yes | frozen |
| **bo-full-stage** | **40 / 40 / 40** | **120** | yes | **varied** |

v2 is the artifact-complete *subset* of the 40/family design (needed for gated row residual + phase). This campaign restores 40/family and varies stage 1.

## Provenance of the 120 training rows

| Case | Reused v2 (frozen stage-1) | New full 1–6 (stage-1 varied) | Total |
|---|---:|---:|---:|
| 2-1 | 14 | 26 | 40 |
| 3-1 | 30 (10 excluded for balance) | 10 | 40 |
| 5-1 | 21 | 19 | 40 |

Excluded 3-1 rows: `excluded_for_balance.json`. Stage-1 residuals for reused rows come from one stage-1-only log per subset (`stage1_features.json`); orientation is recomputed from `unwrapped.csv`.

## Candidate features (all stages)

**Evidence** (input / artifact quality, stages 1–3):

- `depth_nan_ratio` — empty / white areas on the depth map
- `denoise_retained_ratio` — how much of the cloud survives the radial mask
- `unfold_residual` — `log1p(recentre_residual_max_cm)` (stage 1)
- `orient_agreement` — `|corr(h, PCA tunnel axis)|` (stage 1, label-free)

**Coherence** (detection / segmentation plausibility, stages 4–5):

- `sam_fill_rate`, `sam_ontology_divergence`
- `det_row_residual_px`, `det_row_gated`, `det_row_y_std`
- `phase_incoherence_deg`

## Frozen lean proxy

After Ridge + 10%-of-max coefficient prune (keep ≥1 Evidence and ≥1 Coherence):

```
ŷ = 0.478
    − 0.174 · z(depth_nan_ratio)
    − 0.392 · z(denoise_retained_ratio)
    + 0.471 · z(sam_fill_rate)
    − 0.112 · z(det_row_residual_px)
    + 0.127 · z(det_row_gated)
```

| Metric | Value |
|---|---:|
| n_train | 120 |
| Train MAE | 0.129 |
| Train Spearman | 0.853 |
| Permutation control | PASS |
| Alarm τ | 0.495 |

Stage-1 features were **candidates**; pruning dropped both (`unfold_residual`, `orient_agreement`). Ablation: full candidate Spearman 0.876 vs no-stage1 0.845; stage1-only Spearman 0.212. Downstream coherence already carries most of the ranking signal when stage-1 variance is limited to 55 of 120 rows.

## Holdout validation (vs v2)

| Metric | full-stage | v2 |
|---|---:|---:|
| Spearman | **0.848** | 0.810 |
| MAE | 0.071 | 0.071 |
| Known-bad flagged | **27/27** | — |
| Anchor false alarms | **0/27** | — |

**Overall validation: PASS** (`validation_gate.md`).

### Unified vs per-family (same lean features)

Refit on the balanced 120-row table (40 per family); gate first on staggered
(`family_refit_gate.md`), then all three (`family_refit.json`).

| Model | Holdout MAE | Spearman | Rank | Alarm P/R |
|---|---:|---:|---|---|
| Lean unified (pooled) | 0.071 | 0.848 | 27/27 | 1.00 / 1.00 |
| Lean per-family | 0.057 | 0.872 | 27/27 | 1.00 / 0.96 |

Per-family edges fidelity (+0.014 MAE); pooled keeps perfect alarm recall.
Deploy unified. Earlier v2-era unbalanced fits (14/35/14) had already shown
starved per-family models hurt recall more than they helped MAE
(`bo/elegant/family/ablation_study.json` B_pooled vs B_per_family).

`denoise_retained_ratio` weight (−0.39): high retention = under-filtering;
effective denoising must remove non-lining clutter.

### 4-3 residual response (limitation)

Swapping residual 23.2 → 5.2 cm on the 4-3-anchor feature vector does **not** move the lean proxy (Δ = 0), because residual was pruned. Fixing stage-1 still requires the reflective agent to *propose* unfolding changes from the raw residual / ontology — the lean score alone will not select those wins. That is the honest limit of this freeze; hard residual/orientation gates remain future work for a more advanced agent.

## Reflection protocol (uniform stages 1–6)

Budget: ≤3 rounds. Observe GT-free intrinsics + artifacts → diagnose via ontology → coordinated multi-stage overlay (now including unfolding when residual ≫ 10 cm) → re-score with the proxy → reveal GT mIoU only at verification. See `data/bo/reflect/campaign_cursor2.md` for the logged campaign (4/5 improved when selecting by proxy under the older stages-2–6 freeze; 4-3 needed stage-1).

## Single-instance gate

Proven before scaling: `gate.md` — `3-1-gate-seed1` full 1–6 with `random_seed=1`, residual 9.4 cm, lean complete, ~258 s. Family-safe stage-1 Sobol ranges validated with `2-1-smoke` after an initial too-wide `slice_spacing_factor` caused slice-count crashes.

## Files

- `training_table.csv`, `models.json`, `ablation.json`, `holdout_scores.csv`
- `stage1_features.json`, `excluded_for_balance.json`
- `gate.md`, `validation_gate.md`, `family_refit_gate.md`, `family_refit.json`
- `per_family_refit.py`, `README.md`
- Paper snippet: `paper/Proxy4Tun/sections/sec_ablation_results.tex`
- Artifacts: `data/bo/full_stage/<case>-trials/`, `data/bo/full_stage/stage1-logs/`
