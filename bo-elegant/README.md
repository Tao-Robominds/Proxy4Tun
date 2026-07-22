# bo-elegant — 3-anchor unified lean proxy

Retargets the BO+Ridge proxy stack onto three family anchors only
(`2-1` staggered, `3-1` continuous, `5-1` complex), with **one** unified
Evidence+Coherence feature set and **one** pooled Ridge proxy.

Historical `bo/`, `bo-unified/`, `data/bo`, `data/bo-unified`, and
`data/anchors` are left untouched. New pipeline outputs go under
`data/bo-elegant/` only; existing holdout runs are referenced via
`registry.json` (no large copies).

## Layout

| Path | Role |
|------|------|
| `features.py` | Lean Evidence / Coherence taxonomy + extraction wrapper |
| `build_registry.py` | Map 54 holdout runs → reuse path or `to_run` |
| `train_proxy.py` | Mini-ablation + permutation control + freeze |
| `sanity_and_gate.py` | Anchor recompute check + single-instance 3-3 gate |
| `run_missing.py` | Run the few missing holdout configs |
| `score_holdouts.py` | Score all registered runs + write `report.md` |
| `family/` | `models.json`, `ablation.json`, `holdout_scores.csv` |
| `paper/` | Paper figures (unchanged) |

## Workflow

```bash
# v1 (archived-table proxy) — see report.md top section
./venv/bin/python bo-elegant/build_registry.py
./venv/bin/python bo-elegant/train_proxy.py --train
./venv/bin/python bo-elegant/score_holdouts.py --score --report

# v2 (regime-neutral continuous fix) — deployment default
./venv/bin/python bo-elegant/run_trials.py --case 3-1 --gate   # single-instance first
./venv/bin/python bo-elegant/run_trials.py --case 3-1 --n 35
./venv/bin/python bo-elegant/run_trials.py --case 2-1 --n 12
./venv/bin/python bo-elegant/run_trials.py --case 5-1 --n 12
./venv/bin/python bo-elegant/train_proxy_v2.py --train
./venv/bin/python bo-elegant/score_holdouts_v2.py
```

Frozen model: `family/models_v2.json`. Review: `t3_review.md`. Gate: `validation_gate_3-6.md`.

## Feature design

**v2 candidate (regime-neutral):**

- **Evidence:** `depth_nan_ratio`, `denoise_retained_ratio`
- **Coherence:** `sam_fill_rate`, `sam_ontology_divergence`,
  `det_row_residual_px` (log1p of `k_row_gate.distance_px`, else 0),
  `det_row_gated`, `det_row_y_std`, `phase_incoherence_deg`

**Dropped from lean candidate:** `det_real_detection_ratio` — regime-confounded
under continuous `uniform_k_snap` (see `t3_review.md`). Kept as diagnostic only.
