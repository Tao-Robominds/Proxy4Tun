# Tunnel 3 parameterized agent

Family-owned stage scripts (not shared with T1/T2). Geometry helpers live in
[`t3_geometry.py`](t3_geometry.py). Priors come from
[`sam4tun/notebook/t3.ipynb`](../../sam4tun/notebook/t3.ipynb) and
[`agents/ontology/tunnel_priors.yaml`](../ontology/tunnel_priors.yaml).

## Profiles

| Path | Role |
|---|---|
| `3-1-1/` | Final T3 parameters (also the CLI default for `--profile t3`) |

## Important T3 twists

- Unfolding: diameter `5.9`, polynomial degree `2`, `swap_tunnel_centers` validated per scan
- Optional `deterministic_theta_orientation` / `residual_recentre`
- Denoising: radial band `2.85–3.0` plus theta gate `1.55–17.15`
- Enhancing: asymmetric full-station coverage window; optional upsampling / outlier interpolation
- Detection: T3 Hough settings, K/AB heights, inherit-Y prompt logic, optional uniform-K snap
- SAM: notebook T3 template/prompt coordinates (`t3_geometry.py`), optional K mirror

## Run

```bash
./venv/bin/python -m sam4tun.pipeline \
  data/subsets/3-1-1.txt data/3-1-1 \
  --profile t3 \
  --overwrite
```
