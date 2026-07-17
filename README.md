# Proxy4Tun

Parameterized SAM4Tun tunnel-lining segmentation pipeline: unfold → denoise →
enhance → detect → SAM → evaluate.

## Setup (local venv only)

```bash
# Use the existing project venv — do not create a new environment.
source venv/bin/activate

# Optional editable install for the `sam4tun` console script:
pip install -e ".[test]"
```

Requires Python ≥ 3.11. SAM weights are local
(`sam4tun/segment-anything/sam_vit_h_4b8939.pth`) and are not committed.

## Layout

| Path | Purpose |
|---|---|
| `agents/sample/` | LOW / sample parameterized stages + `parameters/` |
| `agents/t1&2/` | T1/T2 parameterized stages; default HIGH in `parameters/` |
| `agents/ontology/` | Machine-readable ontology + tunnel priors |
| `sam4tun/` | Modular stage scripts, helpers, SAM vendor tree |
| `data/subsets/` | Local labelled subset clouds (gitignored) |
| `data/<tunnel_id>/` | Default artifact root for new CLI runs |
| `reports/` | Experiment reports and lightweight winner manifests |

See [`agents/README.md`](agents/README.md) for profile naming.

## Safe run examples

Dry-run (resolve paths / params, enforce overwrite gates):

```bash
./venv/bin/python -m sam4tun.pipeline data/subsets/1-1.txt data/1-1 \
  --profile t1&2 --dry-run
```

Full run (creates `data/<tunnel_id>/`; refuse if non-empty unless flagged):

```bash
./venv/bin/python -m sam4tun.pipeline data/subsets/1-1.txt data/1-1 \
  --profile t1&2 --overwrite
```

Resume / allow existing output directory:

```bash
./venv/bin/python -m sam4tun.pipeline data/subsets/2-1.txt data/2-1 \
  --profile t1&2 --params-dir agents/t1\&2/2-1/practical-minimum-opus4.6-flipdir \
  --resume
```

Stage-by-stage (legacy agent scripts):

```bash
export PROXY4TUN_OUT_ROOT="$PWD/data"
export PROXY4TUN_INPUT_TXT="$PWD/data/subsets/1-1.txt"
# unset PROXY4TUN_PARAMS_DIR  → uses agents/t1&2/parameters/
./venv/bin/python agents/t1\&2/1_unfolding.py 1-1
```

**Protected paths:** `data/baseline` and `data/bo` are never written by
`prepare_output_dir` / `ensure_dir`, even with `--overwrite`.

## Environment variables

| Variable | Effect |
|---|---|
| `PROXY4TUN_OUT_ROOT` | Artifact root (CLI sets this to repo `data/` by default) |
| `PROXY4TUN_INPUT_TXT` | Absolute path to the Nx6 point-cloud TXT |
| `PROXY4TUN_PARAMS_DIR` | Directory with `parameters_*.json` (overrides profile default) |
| `MPLBACKEND` | Prefer `Agg` for headless runs |

## Output / overwrite rules

- New CLI default artifacts: `data/<tunnel_id>/`.
- Existing non-empty output dirs require `--overwrite` or `--resume`.
- Legacy modular scripts under `sam4tun/` still default to `sam4tun/data/`
  unless `PROXY4TUN_OUT_ROOT` is set.
- Do not overwrite prior experiment trees such as `data/baseline` or `data/bo`.

## Documentation

- Critical-parameter ablation: [`reports/critical-parameters-experiment.md`](reports/critical-parameters-experiment.md)
- Winner manifests: [`reports/experiments/`](reports/experiments/)
- Ontology: [`agents/ontology/`](agents/ontology/)
- Subsets: [`data/subsets/README.md`](data/subsets/README.md)

## Tests

```bash
./venv/bin/python -m pytest tests/test_pipeline_runtime.py -q
```
