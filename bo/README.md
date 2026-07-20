# Family BO — GT-free mIoU proxy

Train one Ridge proxy **per family** on BO campaign trials, then evaluate on
held-out sub-tunnels (sibling-anchor + known-bad configs).

All family-BO experiment data lives under **`data/bo/`**:

| Path | Contents |
|------|----------|
| `data/bo/<case>-bo-proxy/` | Training-tunnel BO campaigns |
| `data/bo/<subset>-family-proxy/` | Held-out anchor + known-bad runs |
| `data/bo/logs/` | Campaign / holdout / gate logs |

Never write into `data/anchors/` or `data/baseline/`. Results:
[`family/report.md`](family/report.md).

## Modules

| File | Role |
|------|------|
| `intrinsics.py` | Tier-0 gates + Tier-1 GT-free metrics |
| `spaces.py` | Per-family search spaces + holdout case maps |
| `param_io.py` | Parameter overlay materialization |
| `blocks.py` | B1 coherence / B2lean evidence feature sets |
| `run_bo.py` | Validation gate + GP campaign (training tunnels) |
| `run_holdout.py` | Held-out subset runner (sibling anchor + known-bad) |
| `family_proxy.py` | Per-family Ridge train / bad-config select / score |
| `phase_check.py` | GT-free cross-ring phase-coherence check (label rotation) |
| `family/` | Gate, models, bad configs, holdout scores + report |

## Training / holdout cases

| Family | Train | Hold out |
|--------|-------|----------|
| t1&2 | `1-1`, `2-1` | `1-2`…`1-5`, `2-2`…`2-5` |
| t3 | `3-1`, `3-2` | `3-3`, `3-4`, `3-5` |
| t4&5 | `4-1`, `5-1` | `4-2`…`4-10`, `5-2`…`5-7` |

T3 subsets are ring windows of the combined scan `data/3-1.txt`
(see [`data/subsets/README.md`](../data/subsets/README.md)). Case `3-1` reuses
protected params/`data/anchors/3-1-1` via `frozen_anchor` (no rename of
protected trees). New T3 windows: `scripts/extract_t3_subsets.py`.

## Workflow

```bash
# 1. Single-instance holdout gate (required before scaling)
./venv/bin/python bo/run_holdout.py --gate                 # 1-2
./venv/bin/python bo/run_holdout.py --gate-subset 3-4      # new T3 window

# 2. Training-tunnel campaigns (~40 trials each; resumable)
./venv/bin/python bo/run_bo.py --case 1-1 --campaign
./venv/bin/python bo/run_bo.py --case 2-1 --campaign
./venv/bin/python bo/run_bo.py --case 3-1 --campaign
./venv/bin/python bo/run_bo.py --case 3-2 --campaign
./venv/bin/python bo/run_bo.py --case 4-1 --campaign
./venv/bin/python bo/run_bo.py --case 5-1 --campaign

# 3. Freeze known-bad configs + train per-family proxies (B1+B2lean)
./venv/bin/python bo/family_proxy.py --select-bad --train

# 4. Held-out evaluation (subsets × anchor + bad)
./venv/bin/python bo/run_holdout.py --all
# or T3 only:
./venv/bin/python bo/run_holdout.py --all --family t3

# 5. Score + report
./venv/bin/python bo/family_proxy.py --score --report

# 6. Phase-coherence check (t1&2/t3 only; catches block-label rotation)
./venv/bin/python bo/phase_check.py --all data/bo --json-out bo/family/phase_check.json
```

## Feature set

Deployable proxy: **B1 + B2lean** (GT-free). T3 shared-K label collapse is
handled in `anchors/t3/4_detection.py` (detection plumbing), not by the proxy.
Cross-ring phase coherence (`phase_check.py`) catches block-label rotation
on t1&2/t3 (regular stagger); not applicable to t4&5.
