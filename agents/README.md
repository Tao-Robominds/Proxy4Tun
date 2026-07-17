# Parameterized pipeline profiles

Agents under `agents/sample/` and `agents/t1&2/` are stage scripts that load
JSON parameter files and write artifacts through `sam4tun/helpers/pipeline_io.py`.

## Profile layout

| Path | Role |
|---|---|
| `agents/sample/parameters/` | LOW / sample baseline (compact railway reference) |
| `agents/t1&2/parameters/` | Canonical T1/T2 **HIGH** profile (default when unset) |
| `agents/t1&2/parameters-full/` | Snapshot of the HIGH profile used in ablation anchors |
| `agents/t1&2/1-1/` | Historical per-case parameter snapshot for subset `1-1` |
| `agents/t1&2/2-1/` | Historical overlays and practical-minimum evidence for `2-1` |

## Direction selection

Unfolding requires `swap_tunnel_centers` (bool). It chooses whether the
min-bounding-rectangle axis endpoints are swapped before slicing. Validate
direction against ring metadata with `sam4tun/helpers/tunnel_direction.py`
(`orient_centers_by_ring`) when labels are available; otherwise try both
values on a short labelled span. On `2-1`, flipping this flag changed mIoU
from 0.873 to 0.900 under otherwise identical practical-minimum settings.

## Overrides

Set `PROXY4TUN_PARAMS_DIR` to an absolute directory containing
`parameters_{unfolding,denoising,enhancing,detecting,sam}.json` to use a
non-default profile for a single run. When unset, each agent family uses its
local `parameters/` directory.
