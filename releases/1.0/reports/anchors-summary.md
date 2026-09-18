# Anchor summary

Promoted reference runs as of 2026-07-18 (**canonical orientation**). Artifacts:
`data/anchors/<case>/`. Parameters: `anchors/<family>/<case>/`.

See [`orientation-sensitivity.md`](orientation-sensitivity.md) for cleanup +
canonical-orientation lineage. Older experiment write-ups below are historical.

## Metrics

| Case | Profile | mIoU | OA | F1 | Schema | Key unfolding flags |
|---|---|---:|---:|---:|---|---|
| 1-1 | t1&2 | 0.787 | 0.902 | 0.878 | 6-class | `canonical_orientation=true` |
| 2-1 | t1&2 | 0.874 | 0.941 | 0.932 | 6-class | `canonical_orientation=true` |
| 3-1-1 | t3 | 0.850 | 0.920 | 0.917 | 6-class | `canonical_orientation=true`, `h_ring_sign=-1`, `random_seed=1`, `residual_recentre=true` |
| 4-1 | t4&5 | 0.635 | 0.801 | 0.775 | 7-class | `canonical_orientation=true`, geometric SAM |
| 5-1 | t4&5 | 0.808 | 0.901 | 0.893 | 7-class | `canonical_orientation=true`, `residual_recentre=true`, geometric SAM |

## Logs

| Case | Log |
|---|---|
| 1-1 | `1-1-canonical.log` |
| 2-1 | `2-1-canonical.log` |
| 3-1-1 | `3-1-1-canonical.log` (gate: `canonical-gate-proof.md`) |
| 4-1 | `4-1-canonical.log` |
| 5-1 | `5-1-canonical.log` |

Superseded experiment logs are in `logs/archive/` and older `logs/*best*` /
`logs/t45_*` / `logs/t3_*` names.

## Reports by family

- Orientation / cleanup (current): [`orientation-sensitivity.md`](orientation-sensitivity.md)
- Historical T1/T2 ablation: [`critical-parameters-experiment.md`](critical-parameters-experiment.md)
- Historical T1/T2 winners: [`experiments/1-1-best-observed/`](experiments/1-1-best-observed/), [`experiments/2-1-best-observed/`](experiments/2-1-best-observed/)
- Historical T3: [`t3-3-1-1-corrected-vs-literal.md`](t3-3-1-1-corrected-vs-literal.md)
- Historical T4/T5 4-1: [`t45-4-1-swap-ab.md`](t45-4-1-swap-ab.md)
- Historical T4/T5 5-1: [`t45-5-1-depth-improvement.md`](t45-5-1-depth-improvement.md)

## Usage

```bash
./venv/bin/python -m sam4tun.pipeline \
  data/subsets/<case>.txt data/<new-exp> \
  --profile <profile> \
  --params-dir anchors/<family>/<case> \
  --overwrite
```

Never write experiment output to `data/anchors/` or `data/baseline` / `data/bo`.
