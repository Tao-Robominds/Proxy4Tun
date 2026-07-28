# Single-instance validation gate — widened refinement campaign (arm `cursor3`)

Date: 2026-07-28. Representative case: **subset 3-4** (family t3/continuous),
chosen because it is GT-low (anchor mIoU 0.622 < 0.7), sits in the refine band
(scaled proxy 0.574), and fires the stage-1 unlock
(`recentre_residual_max_cm` 20.8 > 10, per `bo-full-stage/stage1_gate.md`).

## Scaled-proxy verification (pre-gate)

- `./venv/bin/python bo-proxy-scale/band_check.py` → `bo-proxy-scale/bands.json`
- Raw holdout proxies span [-0.092, 0.977]; clip to [0,1] changes no anchor score.
  Min-max scaling rejected (would un-flag GT-low anchors 1-4, 1-5, 2-2).
- Refine band [0.5, 0.7): **21/27 anchors**, containing **all 9** GT-low anchors
  (assertion in band_check.py passed). Band mean scaled proxy 0.656, mean GT mIoU 0.692.
- Live scorer cross-check: `score_scaled.py --subset 3-4 --anchor` → 0.5737,
  matches `bo-full-stage/holdout_scores.csv` (0.574).

## Lineage (commands)

```bash
./venv/bin/python bo-unified/reflect_pilot.py --subset 3-4 --round 1 --arm cursor3 \
  --overlay-json '{"denoising": {...widen r/theta...}, "enhancing": {"curvature_threshold": 0.0015},
                   "detecting": {...binary 110, hough 22/22/2200, gap 50, tol 18...},
                   "sam": {"segment_width": 1100, "K_height": 880, "angle": 7.0}}'   # sibling 3-5 winner recipe, stages 2-6
./venv/bin/python bo-unified/reflect_pilot.py --subset 3-4 --round 2 --arm cursor3 --full \
  --overlay-json '{"unfolding": {"random_seed": 0}}'                                  # stage-1 seed probe
./venv/bin/python bo-unified/reflect_pilot.py --subset 3-4 --round 3 --arm cursor3 --full \
  --overlay-json '{"unfolding": {"random_seed": 5}, ...round-1 recipe...}'            # combined
./venv/bin/python bo-proxy-scale/select_round.py --subset 3-4 --arm cursor3
```

Full overlays: `data/reflect/3-4/cursor3/round*/reflection_record.json`.
Selection record: `bo-proxy-scale/selections/3-4.json`.

## Metrics (frozen pooled lean proxy, clipped; GT mIoU offline only)

| Round | Overlay | Scaled proxy | Residual (cm) | mIoU (offline) |
|---|---|---:|---:|---:|
| anchor | — | 0.5737 | 20.8 | 0.622 |
| **round1** | widen recipe (2–6) | **0.5965** | 20.8 | **0.631** |
| round2 | stage-1 seed 0 (1–6) | 0.5512 | 22.8 | 0.605 |
| round3 | seed 5 + recipe (1–6) | 0.3951 | 23.2 | 0.571 |

Selected: **round1** (monotone accept satisfied; sole candidate within 0.01
margin; residual tiebreak trivial). Δ scaled proxy +0.023, Δ mIoU +0.009.

Note: neither alternative seed (0, 5) improved the anchor's 20.8 cm residual
(anchor already uses seed 1); the frozen proxy correctly down-ranked both
degraded stage-1 rounds (round3 fell into the reject band and its mIoU is
indeed the worst — the score tracked the degradation).

## Pass/fail vs plan criteria

- pipeline runs complete (3/3 rounds status ok): **PASS**
- scaled proxy computed by the frozen pooled scorer (not the legacy per-family
  model in reflect_pilot output): **PASS**
- selection rule executes (monotone accept + tiebreak on run-own residuals;
  anchor-backfill defect found and fixed in `select_round.py` before scaling): **PASS**
- selected round does not degrade mIoU vs anchor 0.622 (got 0.631): **PASS**

**GATE: PASS — proceed to the remaining 15 flagged subsets.**
