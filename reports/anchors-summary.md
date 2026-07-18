# Anchor summary

Promoted reference runs as of 2026-07-18. Artifacts:
`data/anchors/<case>/`. Parameters: `anchors/<family>/<case>/`.

## Metrics

| Case | Profile | mIoU | OA | F1 | Schema | Key unfolding flags |
|---|---|---:|---:|---:|---|---|
| 1-1 | t1&2 | 0.815 | 0.914 | 0.897 | 6-class | `swap_tunnel_centers=true` |
| 2-1 | t1&2 | 0.900 | 0.955 | 0.945 | 6-class | `swap_tunnel_centers=false` |
| 3-1-1 | t3 | 0.881 | 0.940 | 0.935 | 6-class | `residual_recentre=true` |
| 4-1 | t4&5 | 0.741 | 0.861 | 0.850 | 7-class | `swap=false`, geometric SAM |
| 5-1 | t4&5 | 0.681 | 0.842 | 0.802 | 7-class | `swap=false`, `residual_recentre=true` |

## Logs (kept in `logs/`)

| Case | Log |
|---|---|
| 1-1 | `1-1-best-observed-p3_ff7_02.log` |
| 2-1 | `2-1-best-observed.log` |
| 3-1-1 | `t3_3-1-1.log` |
| 4-1 | `t45_4-1_swapfalse.log` |
| 5-1 | `t45_5-1_recentre.log`, `t45_5-1_recentre_det_{detect,sam,eval}.log` |

Superseded experiment logs are in `logs/archive/`.

## Reports by family

- T1/T2 ablation: [`critical-parameters-experiment.md`](critical-parameters-experiment.md)
- T1/T2 winners: [`experiments/1-1-best-observed/`](experiments/1-1-best-observed/), [`experiments/2-1-best-observed/`](experiments/2-1-best-observed/)
- T3: [`t3-3-1-1-corrected-vs-literal.md`](t3-3-1-1-corrected-vs-literal.md)
- T4/T5 4-1: [`t45-4-1-swap-ab.md`](t45-4-1-swap-ab.md)
- T4/T5 5-1: [`t45-5-1-depth-improvement.md`](t45-5-1-depth-improvement.md)

## Usage

```bash
./venv/bin/python -m sam4tun.pipeline \
  data/subsets/<case>.txt data/<new-exp> \
  --profile <profile> \
  --params-dir anchors/<family>/<case> \
  --overwrite
```

Never write experiment output to `data/anchors/` or `data/baseline` / `data/bo`.
