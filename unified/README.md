# Unified multi-family pipeline

One set of stage scripts for all three tunnel families, selected by
`family_mode` in `parameters_family.json`:

| Mode | Family | Cases |
|------|--------|-------|
| `staggered` | t1&2 | `1-1`, `2-1` |
| `continuous` | t3 | `3-1-1` |
| `complex` | t4&5 | `4-1`, `5-1` |

Mode only fills *missing* parameter keys; explicit JSON always wins, so the
snapshots under `unified/params/<case>/` reproduce the corresponding
`anchors/<family>/<case>/` behaviour.

## Layout

```
unified/
  family_io.py          # mode loader + defaults
  1_unfolding.py … 6_evaluation.py
  t12_geometry.py / t3_geometry.py / t45_geometry.py
  params/<case>/        # parameters_*.json + parameters_family.json
  run_unified.py        # CLI runner → data/unified/<case>/
```

`anchors/` and `data/anchors/` are read-only. Outputs go to `data/unified/`.

## Usage

```bash
# Single-instance gate (required before scaling)
./venv/bin/python unified/run_unified.py --case 1-1 --overwrite

# Remaining first-subsets
./venv/bin/python unified/run_unified.py --case 2-1 --overwrite
./venv/bin/python unified/run_unified.py --case 3-1-1 --overwrite
./venv/bin/python unified/run_unified.py --case 4-1 --overwrite
./venv/bin/python unified/run_unified.py --case 5-1 --overwrite
```

Case `3-1-1` reads input from `data/subsets/3-1.txt` (same ring window as the
frozen anchor) and writes to `data/unified/3-1-1/`.

Verification vs `data/anchors/`: [`verification.md`](verification.md).
Gate proofs: [`gate_1-1.json`](gate_1-1.json), [`gate_4-1-improve.json`](gate_4-1-improve.json).
