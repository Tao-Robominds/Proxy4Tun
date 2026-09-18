# Single-instance validation gate — bo-full-stage

**HARD RULE proof before scaling.** One full stages 1–6 trial on a representative continuous case with a perturbed stage-1 overlay.

## Case

- **subset / trial id:** `3-1-gate-seed1`
- **family:** continuous (t3)
- **stage-1 overlay:** `random_seed` 0 → 1 (all other params = anchor)
- **output:** `data/bo/full_stage/3-1-trials/runs/3-1-gate-seed1`

## Command

```bash
./venv/bin/python bo/full_stage/run_trials_full.py --case 3-1 --gate --force
```

## Metrics (pass criteria)

| Check | Criterion | Value | Pass |
|---|---|---:|:---:|
| Pipeline status | ok | ok | yes |
| mIoU parsed | finite | 0.850 | yes |
| `recentre_residual_max_cm` from log | finite | 9.4 | yes |
| `unfold_residual` = log1p(residual) | finite | 2.342 | yes |
| `orient_axis_corr` from artifacts | \|corr\| ≥ 0.6 | −0.999 | yes |
| `orient_invariant_ok` | 1 | 1 | yes |
| Lean features complete | all CANDIDATE finite | True | yes |
| Wall-clock (stages 1–6) | recorded | 258.1 s | yes |

## Residual → mIoU sanity (existing 4-3 seed probe)

From `data/bo/reflect/campaign_cursor2.md` (stages 1–6 unlocked on 4-3):

| Config | residual_cm | mIoU |
|---|---:|---:|
| seed 0 (anchor) | 23.2 | 0.516 |
| seed 1 | 5.2 | 0.554 |
| seed 5 | 9.7 | 0.544 |
| seed 2 | 3.0 | 0.270 |
| poly3 seed0 | 35.6 | 0.340 |

Directionally residual matters, but is not sufficient alone (seed 2: low residual, low mIoU) — so residual enters Evidence *alongside* downstream features.

## Verdict

**PASS.** Full-pipeline runner, stage-1 residual parse, orientation feature, and lean completeness all verified. Gate trial counts as the first of 3-1's 10 new stage-1-varied trials.

## Campaign sizing

~4.3–5.3 min/trial × ~55 new full trials ≈ **4–5 hours** sequential (plus ~27 cheap stage-1-only backfills).

## Follow-up smoke (2-1 near-anchor)

After discovering that a global `slice_spacing_factor∈[1.5,2.0]` collapses slice count on staggered tunnels (anchor uses 1.2), stage-1 ranges were made **family-specific**. Re-validated with:

```bash
# near-anchor overlay on 2-1
trial 2-1-smoke → status=ok mIoU≈0.87 residual parsed lean_ok
```

PASS — campaign relaunched with per-family unfolding spaces.
