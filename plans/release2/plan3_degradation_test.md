# Plan 3: paired degradation test on the 27 evaluation subsets

Budget: about 1 day. Compute 54 runs x 4.7 min = 4.3 h GPU (27 reference,
27 degraded); overlay selection, scoring, tables about 2 h. Prerequisite:
Plan 2 frozen proxy.

## Goal

Run each evaluation subset with its unmodified family reference and with a
degraded counterpart, score both with the frozen proxy, and report Spearman
correlation, MAE, strict pair rankings, and alarms below 0.5, overall and by
family and output group. The 27 reference runs are also the starting runs of
Plan 4.

## Steps

### 1. Degradation overlay selection (30 min)

- `bo/release2/select_degraded.py`: for each family, take the valid
  development trial with the lowest GT mIoU in
  `data/release2/calibration/records/training_table.csv`, load its
  `record.json`, and keep only the stage 2-5 keys that differ from the family
  reference (unfolding keys dropped so both pair members share the stage-1
  frame). Write `data/release2/degradation/records/overlay_selection.json`
  (`family, source_trial, source_gt_miou, overlay`) and a human-readable
  table. The overlay is applied unchanged to all nine subsets of the family.
- Selection is frozen before any evaluation-subset run.

### 2. Runner `bo/release2/run_pair.py` (45 min)

- `--subset ID --arm reference|degraded`. Reference: Plan 1
  `run_reference.py` into `data/release2/references/<subset>/` (reuse if
  already present from the gate). Degraded: stages 1-6 with
  reference + overlay into `data/release2/degradation/<subset>/`; stage 1 is
  re-run with identical unfolding parameters (same seed) so the frame matches;
  if stage 1 is deterministic per the Plan 1 gate, copy the stage-1
  checkpoint instead (`bo/runtime/pipeline.copy_checkpoint`).
- Each run writes `record.json` with measurements, proxy score, band, GT
  mIoU, elapsed time. GT is read only by stage 6 and stored in the record for
  offline analysis.

### 3. Single-instance gate (15 min)

One pair on `1-2` (staggered, not a development subset). Pass: both runs
valid, degraded overlay equals the frozen selection, stage-1 frames identical
(same `unwrapped.csv` hash or orientation line), proxy scores finite, wall
time within budget. Log to `data/release2/degradation/GATE.md`.

### 4. Bulk pairs (4.3 h GPU)

Remaining 26 pairs, sequential, family by family. Failures are logged in
`records/failures.csv` and retried once; a second failure is reported, not
replaced (the manuscript reports 54 completed runs; a shortfall must be
explicit).

### 5. Summary `bo/release2/summarise_degradation.py` (45 min)

`records/pairs.csv` (one row per run: subset, family, arm, four measurements,
score, band, gt_miou) and `summary.md`:

- Spearman rho and MAE between proxy score and GT mIoU over 54 runs; per
  family; per output group (reference vs degraded).
- Strict pair ranking: fraction of the 27 pairs with reference score >
  degraded score.
- Alarms at 0.5: precision and recall against the reference / degraded
  construction labels; per family.
- Intervals for rho: percentile bootstrap over subsets within family (pairs
  kept together, 2000 replicates) and the 5^5 parent-tunnel enumeration
  (`bo/runtime/clustered_stats.py`, paths repointed).
- Starting-band table for Plan 4: each reference run's score and band; the
  admitted list is the set with score in `[0.5, 0.7]` inclusive.

## Deliverables

- `data/release2/degradation/records/{overlay_selection.json,pairs.csv,failures.csv,summary.md}`, `GATE.md`.
- 27 reference runs under `data/release2/references/` with `record.json` (Plan 4 starts).

## To-dos

- [ ] select-overlays: lowest-mIoU valid development trial per family, stage 2-5 diff, frozen JSON
- [ ] run-pair: reference / degraded runner with shared stage-1 frame
- [ ] gate-pair: one pair on 1-2, `GATE.md`
- [ ] bulk-pairs: 26 remaining pairs, failures logged
- [ ] summarise: rho, MAE, pair ranking, alarms, intervals, admitted list
