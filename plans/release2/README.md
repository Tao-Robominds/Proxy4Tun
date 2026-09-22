# Release 2 rerun: plan index

Branch `release2`. Clean rerun of the whole Proxy4Tun experiment following the
prospective manuscript (`paper/Proxy4Tun/main_claude.tex`, Methodology and
Appendices A-D). New results live only under `data/release2/`; everything from
the first run stays read-only under `releases/1.0/`, `anchors/`, `data/anchors/`.
Figures are deferred; every plan produces records and tables only.

| Plan | File | Deliverable | Budget |
|---|---|---|---|
| 1 | `plan1_pipeline_prep.md` | GT-free pipeline copy, family references, engineering metadata, single-instance gate on 2-1 / 3-1 / 5-1 | 0.5 day |
| 2 | `plan2_calibration_proxy.md` | 120 valid calibration records (32 Sobol + 8 GP per family), LOFO comparison of four feature sets, 20 permutations, frozen four-feature proxy | 1.5 days |
| 3 | `plan3_degradation_test.md` | 27 reference + 27 degraded runs, overlay selection from development trials, correlation / MAE / pair ranking / alarms | 1 day |
| 4 | `plan4_refinement_analysis.md` | 22-case panel x 4 arms x 3 attempts, benefit with parent-tunnel bootstrap, selector policies, error analysis | 3-4 days |

Total about 6-8 working days, of which about 36 h is GPU compute.

## Decisions taken (apply to all plans)

- One expert reference per family: `anchors/unified/params/2-1` (staggered),
  `3-1-1` (continuous), `5-1` (complex), copied to `configs/references/<family>/`
  and applied unchanged to all ten subsets of the family (including 1-x and 4-x,
  which had their own GT-tuned references in release 1.0).
- Development subsets 2-1, 3-1, 5-1 (calibration only). Evaluation panel: the
  other 27 subsets (1-1..1-5, 2-2..2-5; 3-2..3-10; 4-1..4-5, 5-2..5-5).
- Stages 1-5 never read the point-label column or the ring-index column.
  Travel direction comes from `data/subsets/tunnel_meta.json` (one drive-direction
  vector per parent tunnel, derived once and documented). Expected ring count
  comes from `data/subsets/<id>_rings_meta.json` (`n_rings_kept`).
- LLM arms: Fable 5.1 (`claude-fable-5-1-thinking-high`), GPT-5.6
  (`gpt-5.6-sol-medium`), Gemini 3.8 (`inherit`), one fresh Cursor sub-agent per
  case, resumed for attempts 2-3.
- Admission band for refinement is inclusive `[0.5, 0.7]` (the user's
  instruction), noted as a difference from the manuscript's `[0.5, 0.7)`.

## Time-budget basis

Stage 1-6 pipeline wall time on the single RTX 5060 (8 GB), from the
release-1.0 bayes manifests (168 runs): staggered median 338 s, continuous
241 s, complex 271 s; about 4.7 min per run, p90 under 6 min. Runs are strictly
sequential (two concurrent stage-5 SAM processes OOM the GPU). Measurement
replay adds under 10 s per run.

Rules for every plan:

- Single-instance gate first (hard rule). Record subset id, command, metric
  values, pass/fail criteria, evidence path, and measured wall time in the
  plan's `GATE.md` before any bulk run.
- If measured per-run time exceeds the budget by more than 50 %, stop and
  re-plan before scaling.
- Failed runs are logged (never silently dropped) and replaced only where the
  protocol says so (calibration top-up); in the refinement panel they consume
  the attempt.

## Shared output layout

```
data/release2/
  gate/GATE.md                       Plan 1 gate log
  references/<subset>/               27 + 3 reference runs (stages 1-6) + record.json
  calibration/<dev>/runs/<trial>/    Plan 2 trial runs + record.json
  calibration/records/               training_table.csv, manifest per family, failures.csv
  proxy/                             comparison tables, permutations, frozen model copy
  degradation/<subset>/              Plan 3 degraded runs + record.json
  degradation/records/               pairs.csv, overlay_selection.json, summary.md
  refinement/<arm>/<subset>/round<r>/ Plan 4 executed candidates
  refinement/records/                panel.csv, candidates.csv, selections/, policies.csv
  analysis/                          benefit.md, selection.md, errors.md, numbers.json
configs/references/<family>/         frozen family reference JSON snapshots
configs/proxy/four_feature.json      frozen release-2 proxy (Plan 2 output)
```

Run directories are gitignored; `record.json`, `records/*.csv`, `*.md`, and
`configs/` are tracked.
