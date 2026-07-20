# Tunnel 3 anchor profiles

Family-owned stage scripts. Geometry: [`t3_geometry.py`](t3_geometry.py). Priors:
[`agents/ontology/tunnel_priors.yaml`](../../agents/ontology/tunnel_priors.yaml).

Frozen run: [`data/anchors/3-1-1/`](../../data/anchors/3-1-1/) (canonical orientation).

## Profiles

| Path | Role |
|---|---|
| `3-1-1/` | CLI default for `--profile t3`; anchor mIoU 0.850 |

## T3 settings

- Unfolding: diameter `5.9`, `canonical_orientation=true`, `h_ring_sign=-1`,
  `random_seed=1`, `residual_recentre=true`
- Denoising: radial band `2.85–3.0` + theta gate
- Detection: `prompt_logic: t3_inherit`, optional `uniform_k_snap`
- SAM: notebook T3 template coordinates via `t3_geometry.py`;
  `segment_order: [K, B2, A3, A2, A1, B1]` (paired with `h_ring_sign=-1`)

## `uniform_k_snap` K-Y clamp (detection plumbing)

With `uniform_k_snap=true`, all rings share one K prompt Y
(`median` of anchor detections). That Y is clamped to the design rows
already used by the assume path:

| Parameter | Default | Meaning |
|-----------|---------|---------|
| `k_row_pattern` | `[1123.0, 1553.0]` | Allowed shared K rows (px) |
| `k_row_tolerance` | `200.0` | Max distance before clamp/fail |
| `k_row_action` | `"snap"` | `snap` / `fail` / `warn` |

Writes `k_row_gate.json` beside `initial_points.csv`. Not part of the
mIoU proxy — just T3 detection. Prefer `random_seed=10` for full-pipeline
runs. Regression check: `./venv/bin/python bo/test_ystar_gate.py`.

## Run

```bash
./venv/bin/python -m sam4tun.pipeline \
  data/subsets/3-1-1.txt data/3-1-1-repro \
  --profile t3 \
  --overwrite
```

See [`reports/orientation-sensitivity.md`](../../reports/orientation-sensitivity.md)
(current) and
[`reports/t3-3-1-1-corrected-vs-literal.md`](../../reports/t3-3-1-1-corrected-vs-literal.md)
(historical).
