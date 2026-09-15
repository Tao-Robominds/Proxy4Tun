# bo/ — consolidated Bayesian-optimization package

Single tracked package for all Proxy4Tun BO / proxy / refinement campaign code
that previously lived as seven top-level folders (`bo/`, `bo-unified/`,
`bo-elegant/`, `bo-full-stage/`, `bo-bayes/`, `bo-proxy-scale/`,
`bo-notebook-direct/`).

Artifact trees live under [`data/bo/<phase>/`](../data/bo/MANIFEST.md)
(frozen). Path constants: [`bo/paths.py`](paths.py).

## Package map

| Sub-package | Role |
|---|---|
| [`archive_v0/`](archive_v0/) | Historical first family-BO code (Jul 18–20); campaigns removed |
| [`unified/`](unified/) | Unified-pipeline proxy, ingest, holdouts, `reflect_pilot` |
| [`elegant/`](elegant/) | 3-anchor lean Ridge proxy (v1 → regime-neutral v2) |
| [`full_stage/`](full_stage/) | Paper five-feature lean proxy; stages 1–6 tunable |
| [`bayes/`](bayes/) | Sobol + GP uncertainty acquisition redo; manuscript figure regen |
| [`proxy_scale/`](proxy_scale/) | Scaled-proxy band selection for self-refinement |
| [`notebook_direct/`](notebook_direct/) | Notebook-faithful baseline on the 27-subset panel |

## Docs

- **Full experience report:** [`REPORT.md`](REPORT.md)
- Per-phase READMEs / gates / reports inside each sub-package
- Data inventory: [`data/bo/MANIFEST.md`](../data/bo/MANIFEST.md)

## New campaigns

Do **not** write under `data/bo/`. Example:

```bash
export PROXY4TUN_BO_DATA_ROOT="$PWD/data/my-bo-exp"
./venv/bin/python -m bo.bayes.run_bayes_trials --case 3-1 --n0 8 --n-gp 4
```

Or run any existing runner with its `--out` / study root pointed at
`data/<experiment-id>/`.
