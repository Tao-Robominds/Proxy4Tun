# Plan 2: calibration records and frozen proxy

Budget: about 1.5 days. Compute 121-130 runs x 4.7 min = 9.5-10.5 h GPU
(staggered 40 x 5.6 min = 3.8 h, continuous 40 x 4.0 min = 2.7 h, complex
40 x 4.5 min = 3.0 h, plus failed-trial top-ups); GP refits negligible; proxy
comparison and permutations under 30 min; sampler port and validation code
about 3 h. Prerequisite: Plan 1 gate passed.

## Goal

Per family, 40 valid trials on the development subset (32 scrambled-Sobol +
8 sequential GP maximum-uncertainty acquisitions) with all ten measurements and
development GT mIoU recorded; compare PQ-only, SC-only, ten-feature and the
prespecified four-feature Ridge model with leave-one-family-out validation and
20 within-family permutations; refit and freeze the four-feature model on all
120 records.

## Source material

- Sampler to port: `releases/1.0/code/bayes/run_bayes_trials.py` (Sobol
  `scramble=True`, unit-to-bounds mapping with integer rounding and Boolean
  thresholding, radial-gate inversion reset to midpoint -/+ 0.02 m; GP =
  `ConstantKernel * Matern(nu=2.5) + WhiteKernel`, `normalize_y=True`,
  length-scale bounds (1e-2, 1e2), noise (1e-6, 1e-1), 3 optimiser restarts,
  refit after each valid trial; acquisition = max predictive std over a
  random pool of 2048 candidates). Manuscript Table `tab:bo-config`.
- Bounds: `bo/runtime/spaces.py` (`space_for_case`, `encode_params`,
  `decode_vector`); manuscript Table `tab:bo-bounds`. Bounds are frozen and
  copied into `configs/bounds/<family>.json` for the record.
- Ridge helpers: `bo/runtime/ridge.py` (`fit_ridge`,
  `leave_one_family_out_cv`, `permutation_control`, `predict`; alpha grid 25
  log-spaced in [1e-3, 1e3] by LOO CV on the fitting data; standardisation from
  training data; predictions clipped to [0, 1]).
- Reference proxy comparison driver: `bo/sc_general/train_proxy.py` (to be
  adapted; stale paths under `data/sc-general/`).

## Steps

### 1. Port the sampler to `bo/release2/calibrate.py` (2 h)

- Inputs: `--dev 2-1|3-1|5-1`, `--n-sobol 32 --n-gp 8`, `--seed <per family>`.
  Reference params from `configs/references/<family>/`; runner
  `bo/runtime/pipeline.run_stages` (Plan 1 wiring); measurements from
  `bo/release2/measure.py`.
- Trial ids `s000..` (Sobol) and `g000..` (GP). Each trial writes
  `data/release2/calibration/<dev>/runs/<trial>/` and `record.json`
  (`trial_id, acquisition, x_unit, x, overlay, measurements, gt_miou, valid,
  failure_reason, elapsed_s`). `manifest.json` per family is the resumable
  source of truth.
- Validity: stages 1-6 complete and all ten measurements finite. A failed
  trial is kept in the manifest with `valid=false` and `failure_reason`, and
  the next Sobol point (or a new GP acquisition) replaces it; `failures.csv`
  lists every failure.
- GP is fitted on valid trials only (Sobol + accepted GP), in normalised
  unit space, target = GT mIoU.

### 2. Single-instance gate (20 min)

`calibrate.py --dev 2-1 --gate`: one Sobol trial and one GP trial (GP fitted on
the Sobol trial plus the Plan 1 reference record and two extra Sobol seeds if
needed). Pass: both runs valid, overlay within bounds, ten measurements
finite, GT mIoU recorded, wall time within 1.5 x budget. Log to
`data/release2/calibration/GATE.md`. Stop on failure.

### 3. Bulk calibration (9.5-10.5 h GPU, sequential)

Run `2-1`, `3-1`, `5-1` in turn to 40 valid trials each. After each family,
append to `data/release2/calibration/records/training_table.csv` (one row per
valid trial: `family, dev, trial_id, acquisition, ten measurements, gt_miou`)
and a per-family summary (valid count, attempts, failures, mIoU range, wall
time). Expected mIoU range roughly 0.03-0.9, as in release 1.0; if a family
produces no trial below 0.3, note it (it affects Plan 3 overlay severity) but
do not resample.

### 4. Proxy comparison `bo/release2/fit_proxy.py` (1 h)

Feature sets: PQ (4), SC (6), ten, four (`correspondence_f1@15`,
`sam_fill_rate`, `ring_count_error`, `depth_nan_ratio`). For each:

- LOFO: fit on two families (80), evaluate on the third (40); scaling and
  alpha chosen inside the training split only. Report Spearman rho and MAE per
  fold and pooled.
- Permutation control: shuffle GT mIoU within family, 20 repeats, fixed seed;
  report the LOFO rho distribution against the unpermuted value.
- Outputs: `data/release2/proxy/lofo.csv`, `permutations.csv`,
  `comparison.md`. The four-feature set is prespecified; no feature selection
  on held-out folds this time.

### 5. Freeze the four-feature model (15 min)

Fit on all 120 records; record `alpha`, `intercept`, per-feature `mu, sigma,
w`, feature order, training-table sha256, and the git commit. Write
`configs/proxy/four_feature.json` (tracked) and a copy under
`data/release2/proxy/`. Add `bo/release2/score.py` that loads only this file,
computes the four measurements, returns the clipped score and the band
(`flag < 0.5`, `refine [0.5, 0.7]`, `accept > 0.7`). Everything downstream
reads this file; `bo/sc_general/models.json` (release 1.0) is not used.

## Deliverables

- `data/release2/calibration/records/training_table.csv` (120 rows),
  `failures.csv`, three manifests, `GATE.md`.
- `data/release2/proxy/{lofo.csv,permutations.csv,comparison.md}`.
- `configs/proxy/four_feature.json`, `bo/release2/score.py`.

## To-dos

- [ ] port-sampler: `bo/release2/calibrate.py` with manifest, validity, top-up, GP acquisition
- [ ] bounds-snapshot: `configs/bounds/<family>.json` from `bo/runtime/spaces.py`
- [ ] gate-calibration: one Sobol + one GP trial on 2-1, `GATE.md`
- [ ] bulk-2-1, bulk-3-1, bulk-5-1: 40 valid trials each, `training_table.csv`
- [ ] fit-compare: LOFO and permutations for PQ / SC / ten / four
- [ ] freeze-proxy: `configs/proxy/four_feature.json`, `bo/release2/score.py`
