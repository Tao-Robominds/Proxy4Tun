# Tunnel subsets (~100MB per sub-tunnel; T3 windows are smaller)

Subsets are extracted from full tunnel point clouds. **For each sub-tunnel**
(e.g. `1-2`, `3-1`, `4-1`, `5-1`, …), one subsection is written under
`data/subsets/` with the same filename.

- **Size**: typically ~100 MB for t1&2 / t4&5 (subsampled from the source when
  larger). T3 ring-window subsets are smaller (~13–33 MB) because each keeps
  only 10 consecutive rings after a global stride subsample of `data/3-1.txt`.
- **Naming**: `1-1.txt` … `5-7.txt`. T3 sections of the combined scan are
  `3-1` … `3-10` (not `3-1-1`). The raw combined file lives at `data/3-1.txt`
  (repo root `data/`, not `data/subsets/`).

## T3 ring windows (from `data/3-1.txt`)

Ten 10-ring windows. `3-1`…`3-5` are fixed; `3-6`…`3-10` fill the
remaining gaps. `3-10` uses rings 36–45 (1-ring overlap with `3-1` at
ring 36) after the thin tail 107–116 hung in unfolding. Leftover rings
(not in any window): 21–26, 56, 107–119.

| Subset | Rings | Role |
|--------|-------|------|
| `3-1` | 27–36 | train (promoted sibling / former `3-1-1`) — fixed |
| `3-2` | 46–55 | train (former `3-1-2`) — fixed |
| `3-3` | 77–86 | holdout (former `3-1-3`) — fixed |
| `3-4` | 57–66 | holdout — fixed |
| `3-5` | 97–106 | holdout — fixed |
| `3-6` | 1–10 | gap (early) |
| `3-7` | 11–20 | gap (early) |
| `3-8` | 67–76 | gap (between 3-4 and 3-3) |
| `3-9` | 87–96 | gap (between 3-3 and 3-5) |
| `3-10` | 36–45 | gap (dense mid; 1-ring overlap with `3-1`) |

```bash
# Generate / refresh gap windows 3-6 … 3-10 only (leaves 3-1…3-5 untouched)
./venv/bin/python scripts/extract_t3_subsets.py

# Optional: refresh a specific id (including fixed ones)
./venv/bin/python scripts/extract_t3_subsets.py --windows 3-8
```

## Drive direction (engineering metadata)

`tunnel_meta.json` stores the unit XY direction along which stage-1 unfolded
`h` must increase. It is derived once by `scripts/build_tunnel_meta.py` from
the Seg2Tunnel ring-index column and the family frame (`h_ring_sign` +1 for
staggered and complex, −1 for continuous), then treated as project metadata.
Only tunnel 3 (one combined scan) shares a heading across subsets. The other
tunnels keep one vector per subset, because each cloud's long axis points a
different way. Pipeline stages 1–5 read the vector for the subset they are
running and do not read the per-point ring column. Expected ring counts for
the ring-count residual come from each subset's `*_rings_meta.json`
(`n_rings_kept`), not from counting ring ids at runtime.

```bash
./venv/bin/python scripts/build_tunnel_meta.py
```

## How to run the pipeline on a subset

The BO / holdout runners set `PROXY4TUN_INPUT_TXT` to `data/subsets/<id>.txt`.

```bash
./venv/bin/python bo/run_holdout.py --subset 3-4 --config anchor
./venv/bin/python bo/run_bo.py --case 3-1 --campaign
```
