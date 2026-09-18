# bo-unified — unified proxy strategy

Retargets the `bo/` GP+Ridge proxy stack onto `anchors/unified/`. Historical
`bo/` and `data/bo/` are left untouched.

## Layout

| Path | Role |
|------|------|
| `spaces.py` | Case registry (6 train + 24 holdouts), stage 2–6 Dim spaces |
| `param_io.py` | Param overlays + `parameters_family.json` passthrough |
| `pipeline.py` | Shared stage runner → `anchors/unified` |
| `run_bo.py` | Train-parity gates (full stages 1–6) |
| `run_holdout.py` | Sibling-anchor / known-bad holdout runs |
| `ingest.py` | Load historical `data/bo` trials; select known-bad |
| `family_proxy.py` | Per-family + pooled cross-family Ridge proxies |
| `family/` | Gates, models, scores, bad configs |
| `report.md` | Generated evaluation report |

Outputs: `data/bo-unified/` (never `data/bo`, `data/anchors`, `data/baseline`).

## Workflow

```bash
# 1. Ingest historical BO trials + freeze known-bad overlays
./venv/bin/python bo-unified/ingest.py --all

# 2. Train-parity gates (one per family)
./venv/bin/python bo-unified/run_bo.py --case 1-1 --gate
./venv/bin/python bo-unified/run_bo.py --case 3-1 --gate
./venv/bin/python bo-unified/run_bo.py --case 5-1 --gate

# 3. Holdout gates (one per family)
./venv/bin/python bo-unified/run_holdout.py --gate-subset 1-2
./venv/bin/python bo-unified/run_holdout.py --gate-subset 3-6
./venv/bin/python bo-unified/run_holdout.py --gate-subset 4-3

# 4. Full holdout campaign (24 × anchor+bad)
./venv/bin/python bo-unified/run_holdout.py --all

# 5. Train proxies, score, report
./venv/bin/python bo-unified/family_proxy.py --all-analysis
```

## Naming

- Cases use subset IDs (`3-1`, not `3-1-1`). Unified params for T3 still live at
  `anchors/unified/params/3-1-1/` (mapped in `spaces.PARAMS_CASE_ID`).
- Families stay `t1&2` / `t3` / `t4&5` for space compatibility; mode is
  `staggered` / `continuous` / `complex` via `parameters_family.json`.
