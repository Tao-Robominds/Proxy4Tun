# T4/T5 5-1 — depth map improvement for mIoU

> **Historical.** Current promoted anchor is canonical-orientation
> (`data/anchors/5-1/`, mIoU 0.808). See
> [`orientation-sensitivity.md`](orientation-sensitivity.md).

**Case:** `5-1` (rings 110–119)  
**Params (at time of experiment):** `anchors/t4&5/5-1/`  
**Then-promoted artifacts:** recentre + detection tune (mIoU 0.681)

## Goal

Improve depth-map quality and segmentation mIoU — not cosmetic NaN removal.
Hole-fill is allowed only when it improves mIoU; margin trim was rejected after
it shifted the axial frame.

## Experiment arc

| Run | Depth NaN% | mIoU | Outcome |
|---|---:|---:|---|
| swapfalse (initial) | 38.8 | 0.403 | Baseline; large left voids |
| holefill | 0.0 (trimmed) | 0.347 | Failed — frame shift hurt alignment |
| swaptrue | 23.7 | 0.168 | Rejected permanently |
| recentre only | 18.9 | 0.206 | Depth fixed; 11 verticals misaligned rings |
| **recentre + det tune** | 18.9 | **0.681** | **Promoted anchor** |
| recentre + fill | 0.0 | 0.681 | No gain under geometric SAM — not kept |

## Root cause (white voids)

Left-end points had only ~23% inside the denoise band (r 3.65–3.9) because the
fitted centreline was off-centre (~25 cm sinusoidal residual in r vs θ).
`residual_recentre` in unfolding restored left-end in-band coverage to ~87%,
matching 4-1-style depth maps (~22% NaN).

## Detection fix

On the cleaner map, real Hough verticals produced 11 lines; geometric SAM
truncated to 10 rings and misaligned columns. Fix:

- `hough_threshold_vertical=5000` → force 10 synthetic ring-centre verticals
- Lower oblique/horizontal Hough thresholds (35 / 80 px)

Result: 8 anchor-type detections (midpoint/slope) vs 4 on swapfalse baseline.

## Anchor params (5-1/)

Unfolding: `swap_tunnel_centers=false`, `residual_recentre=true`  
Detecting: tuned thresholds above (see `parameters_detecting.json`)  
Enhancing: no hole-fill / trim (same as 4-1 baseline)

## Oracle ceiling (offline, not deployable)

Perfect per-ring K-Y from GT geometry on recentre depth → mIoU **0.814**, showing
remaining headroom is in detection, not depth cosmetics.

## Evidence

- Anchor artifacts: `data/anchors/5-1/`
- Full pipeline log: `logs/t45_5-1_recentre.log`
- Detection/SAM/eval: `logs/t45_5-1_recentre_det_{detect,sam,eval}.log`
- Lineage: `data/anchors/5-1/prepare_note.md`
- Archived superseded logs: `logs/archive/t45_5-1_*.log`

## Reproduce

```bash
# Stages 1–3 + eval from params (or copy state from anchor)
./venv/bin/python -m sam4tun.pipeline \
  data/subsets/5-1.txt data/5-1-repro \
  --profile t4\&5 \
  --params-dir anchors/t4\&5/5-1 \
  --overwrite
```

Pass gate used: mIoU > 0.403 (swapfalse baseline).
