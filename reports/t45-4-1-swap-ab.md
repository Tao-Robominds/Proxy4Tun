# T4/T5 4-1 — swap A/B gate

**Case:** `4-1` (rings subset, profile `t4&5`)  
**Params:** `anchors/t4&5/4-1/`  
**Promoted anchor:** `data/anchors/4-1/` (from swap=false run)

## Swap comparison (2026-07-17)

| `swap_tunnel_centers` | Output (historical) | mIoU | OA | F1 |
|---:|---|---:|---:|---:|
| false | `data/4-1-swapfalse` | **0.741** | 0.861 | 0.850 |
| true | `data/4-1-swaptrue` | 0.494 | 0.715 | 0.645 |

**Winner:** `swap_tunnel_centers=false` — clear margin; still below the 0.80
aspirational bar shared with T1/T2/T3 anchors.

## Follow-ups tried (did not beat swap=false)

| Config | mIoU |
|---|---:|
| det_theta + residual_recentre | 0.635 |
| n_segment [1, 9] | 0.659 |
| residual_recentre only | 0.635 |

## Detection note

Both swap variants used synthetic 10 vertical lines (no Hough verticals on
sparse outlier map). SAM used geometric fallback (7-class), not full SAM masks.

## Evidence

- Gate record: `anchors/t4&5/4-1/gate_swap_ab.json`
- Log: `logs/t45_4-1_swapfalse.log`
- Evaluation: `data/anchors/4-1/evaluation/performance.md`

## Reproduce

```bash
./venv/bin/python -m sam4tun.pipeline \
  data/subsets/4-1.txt data/4-1-repro \
  --profile t4\&5 \
  --params-dir anchors/t4\&5/4-1 \
  --overwrite
```
