# Proxy4Tun

Parameterized SAM4Tun tunnel-lining segmentation pipeline: unfold → denoise →
enhance → detect → SAM → evaluate.

## Setup (local venv only)

```bash
source venv/bin/activate
pip install -e ".[test]"   # optional editable install
```

Requires Python ≥ 3.11. SAM weights are local
(`sam4tun/segment-anything/sam_vit_h_4b8939.pth`) and are not committed.

## Layout

| Path | Purpose |
|---|---|
| [`anchors/`](anchors/README.md) | **Reference profiles** — stage scripts + `parameters_*.json` per tunnel family |
| [`data/anchors/`](data/anchors/README.md) | **Frozen anchor runs** — full artifacts for 1-1 … 5-1 (do not overwrite) |
| `data/subsets/` | Labelled point-cloud inputs (`*.txt`) |
| `data/<experiment>/` | New experiment outputs |
| [`agents/ontology/`](agents/ontology/) | Segment schema and tunnel priors |
| `sam4tun/` | CLI, helpers, modular stages, SAM vendor tree |
| [`reports/`](reports/anchors-summary.md) | Experiment reports and winner manifests |
| `logs/` | Pipeline logs for anchor and key experiment runs |

## Anchor quick reference

| Case | Profile | Params | mIoU |
|---|---|---|---:|
| 1-1 | `t1&2` | `anchors/t1&2/1-1/` | 0.815 |
| 2-1 | `t1&2` | `anchors/t1&2/2-1/` | 0.900 |
| 3-1-1 | `t3` | `anchors/t3/3-1-1/` | 0.881 |
| 4-1 | `t4&5` | `anchors/t4&5/4-1/` | 0.741 |
| 5-1 | `t4&5` | `anchors/t4&5/5-1/` | 0.681 |

## Safe run examples

Dry-run:

```bash
./venv/bin/python -m sam4tun.pipeline data/subsets/1-1.txt data/1-1-test \
  --profile t1&2 --dry-run
```

Full run from an anchor profile:

```bash
./venv/bin/python -m sam4tun.pipeline data/subsets/5-1.txt data/5-1-exp \
  --profile t4\&5 \
  --params-dir anchors/t4\&5/5-1 \
  --overwrite
```

Stage-by-stage:

```bash
export PROXY4TUN_OUT_ROOT="$PWD/data"
export PROXY4TUN_PARAMS_DIR="$PWD/anchors/t1&2/1-1"
./venv/bin/python anchors/t1\&2/1_unfolding.py my-tunnel-id
```

**Protected paths:** `data/baseline`, `data/bo`, and `data/anchors/` must not
be overwritten by routine experiments.

## Environment variables

| Variable | Effect |
|---|---|
| `PROXY4TUN_OUT_ROOT` | Artifact root (CLI default: repo `data/`) |
| `PROXY4TUN_INPUT_TXT` | Absolute path to the N×6 point-cloud TXT |
| `PROXY4TUN_PARAMS_DIR` | Directory with `parameters_*.json` |
| `MPLBACKEND` | Prefer `Agg` for headless runs |

## Documentation

- Anchors: [`anchors/README.md`](anchors/README.md), [`data/anchors/README.md`](data/anchors/README.md)
- Summary metrics: [`reports/anchors-summary.md`](reports/anchors-summary.md)
- T1/T2 ablation: [`reports/critical-parameters-experiment.md`](reports/critical-parameters-experiment.md)
- T3 parity: [`reports/t3-3-1-1-corrected-vs-literal.md`](reports/t3-3-1-1-corrected-vs-literal.md)
- T4/T5 5-1 depth work: [`reports/t45-5-1-depth-improvement.md`](reports/t45-5-1-depth-improvement.md)
- Winner manifests: [`reports/experiments/`](reports/experiments/)

## Tests

```bash
./venv/bin/python -m pytest tests/test_pipeline_runtime.py tests/test_t3_runtime.py tests/test_t45_runtime.py -q
```
