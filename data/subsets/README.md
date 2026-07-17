# Tunnel subsets (~100MB per sub-tunnel)

Local labelled / subsampled point clouds under `data/subsets/`. Files are
gitignored; keep them on the workstation only.

## Naming

- Pattern: `<tunnel>-<span>.txt`, e.g. `1-1.txt`, `2-1.txt`, `5-7.txt`.
- Family map: `1-*`→T1, `2-*`→T2, `3-*`→T3, `4-*`→T4, `5-*`→T5
  (see `agents/ontology/tunnel_priors.yaml`).
- Combined `3-1.txt` is skipped; use `3-1-1`, `3-1-2`, `3-1-3`.
- Optional ring metadata: `<id>_rings_meta.json` beside the cloud.

## How to run the pipeline on a subset

From the repo root, with the local `venv`:

```bash
./venv/bin/python -m sam4tun.pipeline data/subsets/1-1.txt data/1-1 \
  --profile t1&2 --dry-run

./venv/bin/python -m sam4tun.pipeline data/subsets/1-1.txt data/1-1 \
  --profile t1&2 --overwrite
```

Or stage-by-stage:

```bash
export PROXY4TUN_OUT_ROOT="$PWD/data"
export PROXY4TUN_INPUT_TXT="$PWD/data/subsets/2-1.txt"
export PROXY4TUN_PARAMS_DIR="$PWD/agents/t1&2/parameters"
./venv/bin/python agents/t1\&2/1_unfolding.py 2-1
# … then 2_denoising.py … 6_evaluation.py with the same tunnel id
```

Artifacts land under `data/<tunnel_id>/`. Do not point outputs at
`data/baseline` or `data/bo`.
