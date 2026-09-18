# Random-arm single-instance gate

**Case:** 1-5 round 1  
**Date:** 2026-09-15T05:38:19.638545  
**Command:**
```bash
./venv/bin/python bo/sc_general/run_random_campaign.py --design
./venv/bin/python bo/sc_general/run_random_campaign.py --gate
```

## Pass criteria

| Criterion | Value | Pass |
|---|---|---|
| status == ok | `ok` | yes |
| four features finite | `{'correspondence_f1@15': 0.3450296408248732, 'sam_fill_rate': 0.7268553897643285, 'ring_count_error': 0.0, 'depth_nan_ratio': 0.11483973982445583}` | yes |
| proxy_scaled in [0,1] | `0.63384023065052` | yes |
| offline_gt.json present | mIoU=0.615 | yes |
| output under data/refinement/random/1-5/round1/ | `/home/boringtao/Projects/Proxy4Tun/data/refinement/random/1-5/round1` | yes |
| knobs in bounds (validator) | k=6; ['denoising.grad_threshold', 'detecting.binary_threshold', 'detecting.hough_threshold_vertical', 'denoising.z_step', 'enhancing.inter_radius', 'detecting.hough_threshold_horizontal'] | yes |

## Verdict

**PASS.** Scale to the full 22×3 panel.
