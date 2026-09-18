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
| [`bo/`](bo/README.md) | Canonical Bayesian-optimization code (proxy, campaigns, plots) |
| [`bo/sc_general/`](bo/sc_general/) | Frozen four-feature proxy + refinement campaign runners |
| [`data/bo/`](data/bo/MANIFEST.md) | **Frozen BO artifacts** — all phases under `data/bo/<phase>/` (do not overwrite) |
| `data/refinement/<arm>/<case>/` | Compact refinement labels and JSON (full trees in cold store) |
| `data/sc-general/` | Stage-2 holdout scores and stage-3 selections / packets |
| `data/subsets/` | Labelled point-cloud inputs (`*.txt`) |
| `exports/sc-general-random-evaluation/` | Canonical panel CSV/JSON for the manuscript |
| [`agents/ontology/`](agents/ontology/) | Segment schema and tunnel priors |
| `sam4tun/` | CLI, helpers, modular stages, SAM vendor tree |
| [`reports/`](reports/anchors-summary.md) | Experiment reports and winner manifests |
| `logs/` | Pipeline logs for anchor and key experiment runs |
| `paper/Proxy4Tun/` | **Canonical manuscript** — `main_claude.tex` + `figs/` |

## Anchor quick reference

Promoted defaults use **canonical orientation** (`canonical_orientation: true`).
See [`reports/orientation-sensitivity.md`](reports/orientation-sensitivity.md).

| Case | Profile | Params | mIoU |
|---|---|---|---:|
| 1-1 | `t1&2` | `anchors/t1&2/1-1/` | 0.787 |
| 2-1 | `t1&2` | `anchors/t1&2/2-1/` | 0.874 |
| 3-1-1 | `t3` | `anchors/t3/3-1-1/` | 0.850 |
| 4-1 | `t4&5` | `anchors/t4&5/4-1/` | 0.635 |
| 5-1 | `t4&5` | `anchors/t4&5/5-1/` | 0.808 |

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

**Protected paths:** `data/baseline`, `data/bo/` (all consolidated BO phases),
and `data/anchors/` must not be overwritten by routine experiments. See
[`bo/REPORT.md`](bo/REPORT.md) for the BO lineage and how to start a new
campaign under `data/<experiment-id>/`.

## Environment variables

| Variable | Effect |
|---|---|
| `PROXY4TUN_OUT_ROOT` | Artifact root (CLI default: repo `data/`) |
| `PROXY4TUN_INPUT_TXT` | Absolute path to the N×6 point-cloud TXT |
| `PROXY4TUN_PARAMS_DIR` | Directory with `parameters_*.json` |
| `MPLBACKEND` | Prefer `Agg` for headless runs |

## Documentation

- Anchors: [`anchors/README.md`](anchors/README.md), [`data/anchors/README.md`](data/anchors/README.md)
- BO experiments: [`bo/README.md`](bo/README.md), [`bo/REPORT.md`](bo/REPORT.md), [`data/bo/MANIFEST.md`](data/bo/MANIFEST.md)
- Summary metrics: [`reports/anchors-summary.md`](reports/anchors-summary.md)
- Orientation / cleanup lessons: [`reports/orientation-sensitivity.md`](reports/orientation-sensitivity.md)
- Historical ablations (pre-canonical): [`reports/critical-parameters-experiment.md`](reports/critical-parameters-experiment.md), [`reports/t3-3-1-1-corrected-vs-literal.md`](reports/t3-3-1-1-corrected-vs-literal.md), [`reports/t45-5-1-depth-improvement.md`](reports/t45-5-1-depth-improvement.md)
- Winner manifests: [`reports/experiments/`](reports/experiments/)

## Tests

```bash
./venv/bin/python -m pytest tests/test_pipeline_runtime.py tests/test_t3_runtime.py tests/test_t45_runtime.py -q
```

## Reproducing the paper (SC-general)

Compact evidence lives in `data/sc-general/`, `data/refinement/`, and `exports/`. Core scripts:

```bash
./venv/bin/python bo/sc_general/build_tables.py --split both
./venv/bin/python bo/sc_general/score_holdouts.py
./venv/bin/python bo/sc_general/selector_policies.py --arms fable_fresh,gpt56,gemini38,random
./venv/bin/python bo/sc_general/plot_publish_figures.py
./venv/bin/python bo/sc_general/error_analysis_publish.py
./venv/bin/python scripts/drawing/plot_concept_figures.py
```

Refinement campaign (fresh Fable 5.1 arm):

```bash
./venv/bin/python bo/sc_general/run_fable_fresh_campaign.py --status
# proposals come from fresh per-case agents; apply/finish via the same script
```

Manuscript: `paper/Proxy4Tun/main_claude.tex`. Submission tag: `v1.0-aic-submission` (immutable). Historical `archive/` and `final_package/` snapshots: tag `cleanup-2026-09-18` (see `LINEAGE.md`).

Reproduction modes:
- **Compile paper** — `paper/Proxy4Tun/main_claude.tex` + local `figs/`
- **Compact numerical verification** — `data/sc-general/`, `data/refinement/`, `exports/`, and selector/holdout scripts (no full pipeline)
- **Full pipeline rerun** — `data/subsets/` + `anchors/` into a new `data/<experiment-id>/` (never overwrite protected trees)
- **Historical / cold-storage replay** — `/home/boringtao/Proxy4Tun-cold-store/` (see `LINEAGE.md`)
