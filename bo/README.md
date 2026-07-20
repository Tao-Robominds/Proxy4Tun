# Family BO — GT-free mIoU proxy

Train one Ridge proxy **per family** on BO campaign trials, then evaluate on
held-out sub-tunnels (sibling-anchor + known-bad configs).

Artifacts go under `data/<case>-bo-proxy/` and `data/<subset>-family-proxy/`
(never write into `data/anchors/`, `data/baseline/`, or `data/bo/`).

The superseded cross-family pooled experiment is archived in
[`archive-pooled-experiment.md`](archive-pooled-experiment.md). Current results:
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
| `family/` | Gate, models, bad configs, holdout scores + report |

## Workflow

```bash
# 1. Single-instance holdout gate (required before scaling)
./venv/bin/python bo/run_holdout.py --gate

# 2. Training-tunnel campaigns (~40 trials each; resumable)
./venv/bin/python bo/run_bo.py --case 1-1 --campaign
./venv/bin/python bo/run_bo.py --case 2-1 --campaign
./venv/bin/python bo/run_bo.py --case 3-1-1 --campaign
./venv/bin/python bo/run_bo.py --case 4-1 --campaign
./venv/bin/python bo/run_bo.py --case 5-1 --campaign

# 3. Freeze known-bad configs + train per-family proxies (B1+B2lean)
./venv/bin/python bo/family_proxy.py --select-bad --train

# 4. Held-out evaluation (25 subsets × anchor + bad)
./venv/bin/python bo/run_holdout.py --all

# 5. Score + report
./venv/bin/python bo/family_proxy.py --score --report
```

## Feature set

Deployable proxy: **B1 + B2lean** (GT-free). Optional clock-table priors (B3)
were explored in the archived pooled experiment and are not part of this
workflow. T3 shared-K label collapse is handled in
`anchors/t3/4_detection.py` (detection plumbing), not by the proxy.
