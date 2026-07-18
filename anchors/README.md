# Anchors — reference profiles and frozen runs

Anchors are the **promoted reference configurations** for each labelled tunnel
subset. Each anchor pairs:

1. **Parameter snapshots** under `anchors/<family>/<case-id>/` (or
   `anchors/t1&2/parameters/` for the shared T1/T2 HIGH baseline)
2. **Frozen pipeline artifacts** under `data/anchors/<case-id>/`
3. **Lineage notes** in `reports/` and `data/anchors/<case-id>/prepare_note.md`

Use anchors as the starting point for further research — not as overwrite
targets. New experiments go under `data/<experiment-name>/`.

## Layout

```
anchors/
├── sample/          # LOW / compact railway reference
├── t1&2/            # T1/T2 family scripts + per-case params
│   ├── parameters/  # shared HIGH defaults (CLI default for --profile t1&2)
│   ├── 1-1/
│   └── 2-1/
├── t3/              # T3 family (6-class rings)
│   └── 3-1-1/       # CLI default for --profile t3
└── t4&5/            # T4/T5 family (7-class rings, geometric SAM fallback)
    ├── 4-1/         # CLI default for --profile t4&5
    └── 5-1/

data/anchors/
├── 1-1/ … 5-1/      # full stage artifacts + evaluation/ for each anchor

agents/ontology/     # machine-readable ontology (not moved with anchors)
```

## Anchor index

| Case | Family | Params dir | mIoU | Log | Report |
|---|---|---|---:|---|---|
| `1-1` | t1&2 | `anchors/t1&2/1-1/` | 0.815 | `logs/1-1-best-observed-p3_ff7_02.log` | `reports/experiments/1-1-best-observed/` |
| `2-1` | t1&2 | `anchors/t1&2/2-1/` | 0.900 | `logs/2-1-best-observed.log` | `reports/experiments/2-1-best-observed/` |
| `3-1-1` | t3 | `anchors/t3/3-1-1/` | 0.881 | `logs/t3_3-1-1.log` | `reports/t3-3-1-1-corrected-vs-literal.md` |
| `4-1` | t4&5 | `anchors/t4&5/4-1/` | 0.741 | `logs/t45_4-1_swapfalse.log` | `reports/t45-4-1-swap-ab.md` |
| `5-1` | t4&5 | `anchors/t4&5/5-1/` | 0.681 | `logs/t45_5-1_recentre.log` | `reports/t45-5-1-depth-improvement.md` |

See [`data/anchors/README.md`](../data/anchors/README.md) for artifact contents
and [`reports/anchors-summary.md`](../reports/anchors-summary.md) for metrics
detail.

## Running from an anchor

Full pipeline (writes to a **new** output dir, not `data/anchors/`):

```bash
./venv/bin/python -m sam4tun.pipeline \
  data/subsets/5-1.txt data/5-1-myexperiment \
  --profile t4\&5 \
  --params-dir anchors/t4\&5/5-1 \
  --overwrite
```

Stage-by-stage:

```bash
export PROXY4TUN_OUT_ROOT="$PWD/data"
export PROXY4TUN_PARAMS_DIR="$PWD/anchors/t4&5/5-1"
./venv/bin/python anchors/t4\&5/4_detection.py my-tunnel-id
```

## Overrides

`PROXY4TUN_PARAMS_DIR` must point at a directory containing all five
`parameters_*.json` files. When unset, the CLI uses each profile's default
subdir (`parameters/`, `3-1-1/`, `4-1/`, etc.).

## Direction and unfolding flags

| Flag | When to use |
|---|---|
| `swap_tunnel_centers` | Validate per scan; flipping changed 2-1 mIoU 0.873→0.900 |
| `residual_recentre` | Required for T3; fixes off-centre left-end voids on T4/T5 (5-1) |
| `deterministic_theta_orientation` | T3 optional; keep off for T1/T2 until validated |

Ontology and priors: [`agents/ontology/`](../agents/ontology/).
