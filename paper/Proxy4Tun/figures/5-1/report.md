# Subset 5-1 — three quality levels

Source: `data/bo-elegant/5-1-trials/runs/` (no new pipeline runs).

| Level | Trial | mIoU | nan | fill | Look |
|-------|-------|------|-----|------|------|
| best | 5-1-t006 | 0.819 | 0.199 | 0.751 | Teal/purple, bolts visible (same as 5-2-anchor) |
| mid | 5-1-t010 | 0.554 | 0.226 | 0.675 | More white patches, fewer row lines |
| low | 5-1-t002 | 0.036 | 0.962 | 0.016 | Mostly white, almost no detections |

## Image files

| Level | Depth map | Detected lines |
|-------|-----------|----------------|
| best | [`best_depth_map.png`](best_depth_map.png) | [`best_detected_lines.png`](best_detected_lines.png) |
| mid | [`mid_depth_map.png`](mid_depth_map.png) | [`mid_detected_lines.png`](mid_detected_lines.png) |
| low | [`low_depth_map.png`](low_depth_map.png) | [`low_detected_lines.png`](low_detected_lines.png) |
