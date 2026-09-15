# bo-full-stage

Unified lean proxy with **all six pipeline stages tunable** and Evidence features that audit stage 1 (centreline residual + orientation agreement). No hard orientation/residual gates in the main protocol — those move to limitations / future reflective-agent work.

## Corrected campaign history

| Campaign | Trials / family | Total | Artifacts kept | Stage 1 |
|---|---:|---:|:---:|---|
| **v1** (`bo/elegant/family/training_table.csv`) | 40 / 40 / 40 | 120 | no (summary reuse) | frozen |
| **v2** (`bo/elegant/family/training_table_v2.csv`) | 14 / 40 / 21 | 75 | yes | frozen |
| **bo-full-stage** (this folder) | 40 / 40 / 40 | 120 | yes | **varied** |

v2 is the artifact-complete *subset* of the 40/family design (needed for gated row residual + phase). This campaign restores 40/family and, for the first time, varies stage 1.

## Reuse policy

- Reuse all 75 artifact-complete v2 trials (stage-1 features = anchor values, backfilled).
- Cap 3-1 reuse at 30 so every family gets ≥10 stage-1-varied trials.
- New full-pipeline runs: **2-1 +26, 3-1 +10, 5-1 +19 = 55** (not 120).

## Layout

```
bo/full_stage/
  README.md                 # this file
  gate.md                   # single-instance validation proof
  report.md                 # results narrative
  validation_gate.md        # holdout checks vs v2
  training_table.csv        # 120 rows, provenance columns
  models.json / ablation.json / holdout_scores.csv
  stage1_features.json      # per-subset residual + orientation
  run_trials_full.py        # stages 1–6 Sobol campaign
  backfill_stage1.py        # stage-1-only residual capture
  merge_training_table.py
  train_proxy.py
  score_holdouts.py
  run_campaign.sh

data/bo/full_stage/
  <case>-trials/            # new full-pipeline artifacts
  stage1-logs/<subset>/     # residual backfill
```

Never writes under `data/anchors`, `data/baseline`, or `data/bo`.

## Quick commands

```bash
# Single-instance gate (already passed — see gate.md)
./venv/bin/python bo/full_stage/run_trials_full.py --case 3-1 --gate

# Full top-up campaign
./bo/full_stage/run_campaign.sh

# Stage-1 residual backfill
./venv/bin/python bo/full_stage/backfill_stage1.py --train-only
./venv/bin/python bo/full_stage/backfill_stage1.py --all

# Merge → train → score
./venv/bin/python bo/full_stage/merge_training_table.py
./venv/bin/python bo/full_stage/train_proxy.py
./venv/bin/python bo/full_stage/ablation_study.py
./venv/bin/python bo/full_stage/score_holdouts.py
./venv/bin/python scripts/drawing/plot_proxy_fullstage.py
```

## Results (frozen)

See **[report.md](report.md)** for the full narrative. Headline holdout: Spearman **0.848**, MAE 0.071, bad-run flagging 27/27, FP 0/27. Lean features after prune: `depth_nan_ratio`, `denoise_retained_ratio`, `sam_fill_rate`, `det_row_residual_px`, `det_row_gated` (stage-1 candidates were pruned — see report).
