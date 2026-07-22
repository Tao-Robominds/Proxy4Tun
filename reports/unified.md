# Unified pipeline report

**Date:** 2026-07-20 (runs) / 2026-07-21 (this report)  
**Branch:** `unified`  
**Artifacts:** `data/unified/<case>/`  
**Logs (organised):** [`reports/unified/logs/`](unified/logs/)  
**Params:** `unified/params/<case>/`  
**Runner:** `./venv/bin/python unified/run_unified.py --case <case> --overwrite`

Naming: T3 cases use subset IDs **`3-1` / `3-2` / `3-3`** (former `3-1-1` / `3-1-2` / `3-1-3`). Log copies and this report use the new names; on-disk experiment trees under `data/unified/` may still say `3-1-1` until renamed.

## Summary vs frozen anchors

Pass: stages 1–6 complete and \|ΔmIoU\| ≤ 0.02 vs `data/anchors/<case>/` (4-1 noted separately).

| Case | Mode | Anchor mIoU | Unified mIoU | Δ | Status | Evidence log |
|------|------|------------:|-------------:|--:|--------|---|
| 1-1 | staggered | 0.787 | **0.800** | +0.013 | PASS | [`1-1-gate.log`](unified/logs/1-1-gate.log) |
| 2-1 | staggered | 0.874 | **0.875** | +0.001 | PASS | [`2-1-run.log`](unified/logs/2-1-run.log) |
| 3-1 | continuous | 0.850 | **0.850** | 0.000 | PASS | [`3-1-rerun.log`](unified/logs/3-1-rerun.log) |
| 4-1 | complex | 0.635 | **0.661** | +0.026 | PASS* | [`improve-4-1/F_clean.log`](unified/logs/improve-4-1/F_clean.log) |
| 5-1 | complex | 0.808 | **0.818** | +0.010 | PASS | [`5-1-seed2.log`](unified/logs/5-1-seed2.log) |

\*4-1 parity-only run was 0.634; current tree is the improved F-config (see §4-1).

### Current evaluation on disk (`data/unified/<case>/evaluation/`)

| Case | Schema | OA | F1 | mIoU |
|------|--------|---:|---:|-----:|
| 1-1 | 6-class | 0.906 | 0.888 | 0.800 |
| 2-1 | 6-class | 0.942 | 0.933 | 0.875 |
| 3-1 | 6-class | 0.920 | 0.917 | 0.850 |
| 4-1 | 7-class | 0.814 | 0.794 | 0.661 |
| 5-1 | 7-class | 0.904 | 0.899 | 0.818 |

---

## Per-case runs

### 1-1 (staggered)

| Field | Value |
|---|---|
| Log | [`1-1-gate.log`](unified/logs/1-1-gate.log) |
| Orientation | corr=−0.9860, `h_ring_sign=+1` → swapped centres; theta pinned |
| Result | mIoU **0.800** (anchor 0.787) |

### 2-1 (staggered)

| Field | Value |
|---|---|
| Log | [`2-1-run.log`](unified/logs/2-1-run.log) |
| Orientation | corr=−0.9861, `h_ring_sign=+1` → swapped centres; theta pinned |
| Result | mIoU **0.875** (anchor 0.874) |

### 3-1 (continuous; former `3-1-1`)

Input: `data/subsets/3-1.txt` (rings 27–36). Sibling windows: `3-2` (former `3-1-2`), `3-3` (former `3-1-3`) — not re-run in this campaign.

| Run | Log | Seed | Notes | mIoU |
|---|---|---:|---|---:|
| First (broken RANSAC path) | [`3-1-run.log`](unified/logs/3-1-run.log) | 1 | Hard-cap RANSAC on continuous → wrong centreline / h-range | 0.371 |
| Rerun (mode-gated RANSAC) | [`3-1-rerun.log`](unified/logs/3-1-rerun.log) | 1 | K-row gate OK (y\*=1550.1 vs design 1553, Δ=2.9px) | **0.850** |

Orientation (both): corr=−0.9940, `h_ring_sign=-1` → kept centres; theta pinned.

**Fix retained:** RANSAC loop is mode-gated — staggered/continuous use legacy iteration update; complex keeps t4&5 hard-cap.

### 4-1 (complex)

| Run | Log | Seed | Orientation / notes | mIoU |
|---|---|---:|---|---:|
| Parity | [`4-1-run.log`](unified/logs/4-1-run.log) | — | corr=+0.9834, kept centres | 0.634 |
| Forced `h_ring_sign=-1` | [`4-1-swap-centers.log`](unified/logs/4-1-swap-centers.log) | 0 | swapped centres — label collapse | 0.134 |
| Improve F (winner) | [`F_clean.log`](unified/logs/improve-4-1/F_clean.log) / [`F_nseg1-9_recentre.log`](unified/logs/improve-4-1/F_nseg1-9_recentre.log) | 0 | `n_segment[1,9]` + `residual_recentre` | **0.661** |

Legacy unpinned swap=false reference: mIoU 0.741. Target for improve campaign: **0.70** — not reached.

### 5-1 (complex) — seed sweep

Unseeded run is stochastic; frozen params omit `random_seed`.

| Run | Log | Seed | mIoU |
|---|---|---:|---:|
| Unseeded | [`5-1-run.log`](unified/logs/5-1-run.log) | — | 0.777 |
| Seed 0 | [`5-1-seed0.log`](unified/logs/5-1-seed0.log) | 0 | 0.870 |
| Seed 1 | [`5-1-seed1.log`](unified/logs/5-1-seed1.log) | 1 | 0.863 |
| Seed 2 (pinned) | [`5-1-seed2.log`](unified/logs/5-1-seed2.log) | 2 | **0.818** |

Seed 2 chosen for anchor parity (|Δ| ≤ 0.02 vs 0.808). Seeds 0/1 beat the anchor but are not the parity pick.

---

## 4-1 improve campaign

Target mIoU ≥ 0.70. Baseline unified 0.634; legacy swap=false 0.741.  
Full table: [`improve-4-1/results.json`](unified/logs/improve-4-1/results.json). Winner among bounded retunes: **F** at 0.661.

### Early seed / mirror sweeps (`results.json`)

| Tag family | Best mIoU | Outcome |
|---|---:|---|
| A (seed 0–5, 10, 42) | 0.638 (seed42) | Stuck ~0.63; seed5 collapsed to 0.355 |
| B (`h_ring_sign=-1`) | ~0.14 | Label collapse |
| C (mirror K) | ≤0.164 | Fail / collapse |

### Follow-up logs (D–G)

| Tag | Log | mIoU | Note |
|---|---|---:|---|
| D | [`D_theta_sign-1.log`](unified/logs/improve-4-1/D_theta_sign-1.log) | 0.164 | theta sign flip — collapse |
| E | [`E_theta-1_revorder.log`](unified/logs/improve-4-1/E_theta-1_revorder.log) | 0.164 | + reverse `segment_order` — still collapse |
| F | [`F_nseg1-9_recentre.log`](unified/logs/improve-4-1/F_nseg1-9_recentre.log) / [`F_clean.log`](unified/logs/improve-4-1/F_clean.log) | **0.661** | Best bounded retune |
| F_final | [`F_final.log`](unified/logs/improve-4-1/F_final.log) | 0.539 | Worse than clean F |
| G | [`G_theta-1_revcirc_nseg.log`](unified/logs/improve-4-1/G_theta-1_revcirc_nseg.log) | 0.641 | Below F |

Further gains need detection/SAM redesign, not more orientation knobs.

---

## Log index

| Organised path | Source |
|---|---|
| `reports/unified/logs/1-1-gate.log` | `data/unified/1-1-gate.log` |
| `reports/unified/logs/2-1-run.log` | `data/unified/2-1-run.log` |
| `reports/unified/logs/3-1-run.log` | `data/unified/3-1-1-run.log` (ids rewritten → `3-1`) |
| `reports/unified/logs/3-1-rerun.log` | `data/unified/3-1-1-rerun.log` (ids rewritten → `3-1`) |
| `reports/unified/logs/4-1-run.log` | `data/unified/4-1-run.log` |
| `reports/unified/logs/4-1-swap-centers.log` | `data/unified/4-1-swap-centers.log` |
| `reports/unified/logs/5-1-run.log` | `data/unified/5-1-run.log` |
| `reports/unified/logs/5-1-seed{0,1,2}.log` | `data/unified/5-1-seed{0,1,2}.log` |
| `reports/unified/logs/improve-4-1/*` | `data/unified/improve-4-1/*` |

Related: [`anchors/unified/verification.md`](../anchors/unified/verification.md), subset rename note in [`data/subsets/README.md`](../data/subsets/README.md).
