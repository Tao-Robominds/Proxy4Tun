# Widened proxy-flagged refinement campaign (scaled proxy, arms cursor2/cursor3)

Date: 2026-07-28. PoC campaign extending proxy-driven self-refinement to every
GT-low holdout subset, with the frozen pooled lean proxy **clipped to [0,1]**
(scaled proxy) as the selection signal. Success criterion (user-set): an upward
trend in the refine band's scores, corroborated offline by GT mIoU; crossing
the 0.7 acceptance threshold is a bonus, not a requirement.

## 1. Scaled proxy and bands

- Raw frozen proxy over the 54 holdout runs spans [-0.092, 0.977]; clipping to
  [0,1] changes no anchor score. Min-max rescaling was checked and **rejected**:
  it would move GT-low anchors 1-4, 1-5, 2-2 above the 0.7 flag line.
- Bands on the scaled score: reject < 0.5, **refine [0.5, 0.7)**, accept >= 0.7.
- The refine band holds **21/27 anchors (0.574-0.699), including all 9 anchors
  with GT mIoU < 0.7** (`band_check.py`, assertion passed; `bands.json`).
- Per user decision, only the 9 GT-low subsets were refined; the 12 flagged but
  GT-healthy anchors were left as-is (monotone accept would protect them; a
  partial bonus run on 3-8 confirmed this - see section 5).

## 2. Protocol

- 3 reflection rounds per subset (Fable proposes coordinated multi-stage
  overlays; `bo-unified/reflect_pilot.py`, arm `cursor3`; recipes distilled in
  `run_subset.py`). Prior arm `cursor2` covers 4-4, 4-3, 1-5, 1-4, 3-5.
- Scoring: `score_scaled.py` = frozen pooled lean model (`bo-full-stage/models.json`)
  + clip. The legacy per-family score printed by reflect_pilot is ignored.
- Selection (`select_round.py`): best scaled proxy, **monotone accept** vs the
  anchor, residual tiebreak within 0.01 proxy (lower `recentre_residual_max_cm`
  wins; equal residuals -> higher proxy). GT mIoU is never used for selection.
- Stage-1 unlock (per `bo-full-stage/stage1_gate.md`): anchors with residual
  > 10 cm (3-4, 3-2, 3-8; earlier 4-3) may receive `unfolding` overlays and a
  full 1-6 rerun.
- Single-instance gate on 3-4 passed before scaling (`gate.md`).

## 3. Per-subset results (selection = best scaled proxy of 3 rounds)

| Subset | Initial proxy | Anchor mIoU | Selected | Proxy after | mIoU after | dProxy | dmIoU | Arm |
|---|---:|---:|---|---:|---:|---:|---:|---|
| 3-4 | 0.574 | 0.622 | round1 | 0.597 | 0.631 | +0.023 | +0.009 | cursor3 |
| 3-2 | 0.600 | 0.631 | round2 | **0.775** | **0.719** | +0.175 | +0.088 | cursor3 (stage-1 seed 0: residual 16.8->5.4 cm) |
| 3-5 | 0.620 | 0.588 | anchor kept | 0.620 | 0.588 | 0 | 0 | cursor2 (monotone accept) |
| 4-4 | 0.623 | 0.347 | round3 | 0.625 | **0.700** | +0.002 | +0.353 | cursor2 |
| 4-3 | 0.630 | 0.516 | round2 | 0.640 | 0.544 | +0.011 | +0.028 | cursor2_s1 (stage-1 unlocked) |
| 4-1 | 0.652 | 0.635 | round3 | 0.662 | 0.659 | +0.011 | +0.024 | cursor3 |
| 1-4 | 0.661 | 0.556 | round2 | 0.671 | **0.786** | +0.010 | +0.230 | cursor2 |
| 1-5 | 0.675 | 0.549 | round3 | 0.685 | **0.782** | +0.010 | +0.233 | cursor2 |
| 2-2 | 0.692 | 0.673 | round2 | **0.703** | 0.668 | +0.011 | -0.005 | cursor3 |

All initial proxies lie in the refine band. Full round tables:
`selections/<subset>_<arm>.json`; per-run artifacts `data/reflect/<subset>/<arm>/`.

Notes:
- 4-3: rounds 1 and 2 are 0.0005 apart in proxy (both residual 5.2 cm); the
  tiebreak selects round2 (+0.028). Round1 reaches +0.038 - within selection
  noise. Either way every stage-1-unlocked round beats the locked-stage
  ceiling (cursor2 best: -0.008).
- 2-2 (see section 4) is the one selection miss: its true best round
  (mIoU 0.86) was excluded by monotone accept; loss capped at -0.005.

## 4. Headline numbers

| Scope | Proxy before | Proxy after | mIoU before | mIoU after |
|---|---:|---:|---:|---:|
| 9 refined (GT-low) | 0.636 | 0.664 | 0.569 | **0.675** (+0.107) |
| 21-anchor refine band | 0.656 | 0.668 | 0.692 | 0.737 |
| 27-subset panel | - | - | 0.722 | **0.757** (+0.035) |

- Mid-band trend: **upward** on both axes; proxy +0.028 mean on refined
  subsets, corroborated by mIoU +0.107 (no proxy-only inflation).
- 7/9 refined subsets improve mIoU; 3-5 is held at its anchor by monotone
  accept (0); 2-2 is -0.005 (proxy mis-ranking within MAE, below).
- Band crossings into accept (>= 0.7 scaled proxy): 3-2 and 2-2.
- Stage-1 unlock credited: 3-2 (residual 16.8 -> 5.4 cm, mIoU +0.088) and 4-3
  (23.2 -> 5.2 cm, +0.028); on 3-4 the alternative seeds degraded the
  centreline and the proxy correctly down-ranked them.

## 5. Failure analysis: 2-2 (pruned-feature blind spot)

The lean model reads only five features (fill rate +0.471 dominant). 2-2's
round1 achieved mIoU 0.86 by fixing row regularity and phase coherence
(det_row_y_std 56.6 -> 15.0 px, phase incoherence 14.5 -> 2.6 deg) - features
**pruned** from the lean set - while its visible features dipped slightly
(fill 0.743 -> 0.736). Its proxy landed 0.0028 below the anchor and monotone
accept excluded it; round2, which nudged the visible features without real
gains, was selected (-0.005 mIoU). All scores involved differ by < 0.013,
far inside the holdout MAE (0.071). This is the coherence-side analogue of the
4-3 stage-1 blind spot. Mitigation (future work / paper note): on regular
linings the existing phase-coherence alarm signal could act as a secondary
selection criterion, exactly as the residual tiebreak already does for
stage-1 overlays; it would have selected round1 here.

Bonus observation (3-8, GT-healthy, run before the campaign was narrowed to
GT-low subsets): all three rounds degraded quality (worst mIoU 0.336) and
monotone accept kept the anchor - the guard works on healthy runs.

## 6. Manuscript-ready numbers

- Refined subsets: mean mIoU 0.569 -> 0.675 (+0.107); 7/9 improved, one held
  at anchor by monotone accept, one -0.005.
- Panel (27 held-out subsets): 0.722 -> 0.757.
- Gains range +0.009 to +0.353 (excluding the two non-positive cases).
- 3-2 crosses both thresholds: GT mIoU 0.631 -> 0.719 and scaled proxy
  0.600 -> 0.775 (accept zone).
- Selection remained GT-free throughout; GT mIoU used only for offline
  evaluation, as at calibration time.

## Lineage

```bash
./venv/bin/python bo-proxy-scale/band_check.py                      # bands.json
./venv/bin/python bo-proxy-scale/run_subset.py --subset <s>         # cursor3 trios
./venv/bin/python bo-proxy-scale/select_round.py --subset <s> --arm <arm>
./venv/bin/python bo-proxy-scale/make_report.py                     # refined_scores.csv + summary
```
