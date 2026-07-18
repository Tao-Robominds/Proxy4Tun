# Tunnel 3 anchor profiles

Family-owned stage scripts. Geometry: [`t3_geometry.py`](t3_geometry.py). Priors:
[`agents/ontology/tunnel_priors.yaml`](../../agents/ontology/tunnel_priors.yaml).

Frozen run: [`data/anchors/3-1-1/`](../../data/anchors/3-1-1/).

## Profiles

| Path | Role |
|---|---|
| `3-1-1/` | CLI default for `--profile t3`; anchor mIoU 0.881 |

## T3 settings

- Unfolding: diameter `5.9`, `residual_recentre` recommended
- Denoising: radial band `2.85–3.0` + theta gate
- Detection: `prompt_logic: t3_inherit`, optional `uniform_k_snap`
- SAM: notebook T3 template coordinates via `t3_geometry.py`

## Run

```bash
./venv/bin/python -m sam4tun.pipeline \
  data/subsets/3-1-1.txt data/3-1-1-repro \
  --profile t3 \
  --overwrite
```

See [`reports/t3-3-1-1-corrected-vs-literal.md`](../../reports/t3-3-1-1-corrected-vs-literal.md).
