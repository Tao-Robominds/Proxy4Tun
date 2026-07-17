# Parameterized pipeline profiles

The CLI (`python -m sam4tun.pipeline`) runs stage scripts from each family
directory: `agents/t1&2/` for profiles `t1&2` / `t12`, `agents/t3/` for `t3`,
and `agents/sample/` for `sample`. Tunnel behaviour within a family is selected
by JSON parameters (`parameters/` or `--params-dir`).

## Profile layout

| Path | Role |
|---|---|
| `agents/sample/parameters/` | LOW / sample baseline (compact railway reference) |
| `agents/t1&2/` | T1/T2 stage scripts + canonical **HIGH** `parameters/` |
| `agents/t1&2/1-1/` | Per-case parameter snapshot for subset `1-1` |
| `agents/t1&2/2-1/` | Final parameter snapshot for subset `2-1` |
| `agents/t3/` | T3 stage scripts + `t3_geometry.py` |
| `agents/t3/3-1-1/` | Final T3 parameters (CLI default for `--profile t3`) |

## Direction selection

Unfolding requires `swap_tunnel_centers` (bool). It chooses whether the
min-bounding-rectangle axis endpoints are swapped before slicing. Validate
direction against ring metadata with `sam4tun/helpers/tunnel_direction.py`
(`orient_centers_by_ring`) when labels are available; otherwise try both
values on a short labelled span. On `2-1`, flipping this flag changed mIoU
from 0.873 to 0.900 under otherwise identical practical-minimum settings.

Optional unfolding flags (default **false** unless a profile sets them):

| Flag | Effect |
|---|---|
| `deterministic_theta_orientation` | Circumferential handedness from travel direction (removes Tz-sign coin flip). Useful for T3; keep off for T1/T2 until per-scan validation — enabling it mirrored the 2-1 archive. |
| `residual_recentre` | Post-unwrap centreline residual correction. Required for T3's narrow r-band; optional for T1/T2. |

## Overrides

Set `PROXY4TUN_PARAMS_DIR` to an absolute directory containing
`parameters_{unfolding,denoising,enhancing,detecting,sam}.json` to use a
non-default profile for a single run. When unset, each agent family uses its
local `parameters/` directory.
