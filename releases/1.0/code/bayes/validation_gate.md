# Single-instance validation gate — bo-bayes

**Status: PASSED** (2026-08-02)

## Case / sample id
- Train anchor: **3-1** (continuous family)

## Command / lineage
```bash
./venv/bin/python bo/bayes/run_bayes_trials.py --case 3-1 --gate --seed 0
```
- Sobol trial: `data/bo/bayes/3-1-trials/runs/3-1-gate-s000`
- GP trial: `data/bo/bayes/3-1-trials/runs/3-1-gate-g000`
- JSON evidence: `data/bo/bayes/3-1-trials/validation_gate.json`

## Metric values
| Trial | Acquisition | status | mIoU | lean_complete | elapsed_s |
|---|---|---|---:|---|---:|
| 3-1-gate-s000 | sobol_init | ok | 0.239 | True | 257.1 |
| 3-1-gate-s001 | sobol_init (GP warmup) | ok | 0.326 | True | 260.8 |
| 3-1-gate-s002 | sobol_init (GP warmup) | ok | 0.195 | True | 256.1 |
| 3-1-gate-g000 | gp_uncertainty_sigma=0.0571 | ok | 0.214 | True | 237.0 |

## Pass/fail criteria (all required)
- sobol status ok + finite mIoU + lean-complete features
- GP fit succeeds (≥3 ok trials)
- GP-acquired trial status ok + finite mIoU + lean-complete features

All criteria **passed**. Full campaign may proceed.
