# Anchors — reference profiles and frozen runs

Anchors are the **promoted reference configurations** for each labelled tunnel
subset. Each anchor pairs:

1. **Parameter snapshots** under `anchors/<family>/<case-id>/` (or
   `anchors/t1&2/parameters/` for the shared T1/T2 HIGH baseline)
2. **Frozen pipeline artifacts** under `data/anchors/<case-id>/`
3. **Lineage notes** in `reports/` and `data/anchors/<case-id>/prepare_note.md`

Defaults use **canonical orientation** (`canonical_orientation: true`): h is
derived from ring-index correlation and theta from travel direction. See
[`reports/orientation-sensitivity.md`](../reports/orientation-sensitivity.md).

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
```

## Anchor index

| Case | Family | Params dir | mIoU | Notes |
|---|---|---|---:|---|
| `1-1` | t1&2 | `anchors/t1&2/1-1/` | 0.787 | canonical defaults |
| `2-1` | t1&2 | `anchors/t1&2/2-1/` | 0.874 | canonical defaults |
| `3-1-1` | t3 | `anchors/t3/3-1-1/` | 0.850 | `h_ring_sign: -1`, reversed `segment_order`, `random_seed: 1` |
| `4-1` | t4&5 | `anchors/t4&5/4-1/` | 0.635 | canonical defaults |
| `5-1` | t4&5 | `anchors/t4&5/5-1/` | 0.808 | canonical defaults |

See [`data/anchors/README.md`](../data/anchors/README.md) for artifact contents.

**Notebook parity:** [`NOTEBOOK_ANCHOR_PARITY.md`](NOTEBOOK_ANCHOR_PARITY.md) —
formal comparison of notebooks vs anchors (implementation + parameters).

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

## Orientation flags (current defaults)

| Flag | Role |
|---|---|
| `canonical_orientation` | **Default on** for promoted cases. Derives h from ring index; forces deterministic theta. Ignores `swap_tunnel_centers`. |
| `h_ring_sign` | `+1` (default) or `-1` when downstream geometry was tuned on a legacy frame (3-1-1). |
| `residual_recentre` | Required for T3; also used on T4/T5 where enabled. |
| `random_seed` | Optional bitwise reproducibility (set on 3-1-1). |
| `swap_tunnel_centers` | Legacy only; ignored when `canonical_orientation` is true. |

Ontology and priors: [`agents/ontology/`](../agents/ontology/).
