# Tunnel 4&5 anchor profiles

Family stage scripts for T4/T5 (7-block rings, diameter 7.5 m). Geometry
helpers: [`t45_geometry.py`](t45_geometry.py). Priors:
[`agents/ontology/tunnel_priors.yaml`](../../agents/ontology/tunnel_priors.yaml) `&t45`.

Frozen runs: [`data/anchors/4-1/`](../../data/anchors/4-1/),
[`data/anchors/5-1/`](../../data/anchors/5-1/) (canonical orientation).

## Profiles

| Path | Role |
|---|---|
| `4-1/` | CLI default for `--profile t4&5`; anchor mIoU 0.635 |
| `5-1/` | Rings 110–119; recentre + detection tune; anchor mIoU 0.808 |

## T4/T5 settings

- Unfolding: diameter `7.5`, poly degree `2`, `canonical_orientation=true`,
  top-tube slice filter (`top_tube_radius` / `top_tube_top_n`)
- Denoising: radial band `3.65–3.9` (no theta gate)
- Enhancing: upsample `0.09/0.045/0.0225`, depths `0.0065/0.013`, `n_segment [5,14]`
- Detection: Hough on `depth_map_outlier`; 5-1 uses synthetic 10 verticals (`hough_threshold_vertical=5000`)
- SAM: 7 segments, geometric fallback for tunnels 4/5 (`geometry_profile: t45`)

## Run

```bash
./venv/bin/python -m sam4tun.pipeline \
  data/subsets/5-1.txt data/5-1-myexp \
  --profile t4\&5 \
  --params-dir anchors/t4\&5/5-1 \
  --overwrite
```

See [`reports/orientation-sensitivity.md`](../../reports/orientation-sensitivity.md)
(current). Historical: [`reports/t45-4-1-swap-ab.md`](../../reports/t45-4-1-swap-ab.md),
[`reports/t45-5-1-depth-improvement.md`](../../reports/t45-5-1-depth-improvement.md).
