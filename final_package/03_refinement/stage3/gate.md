# Single-instance validation gate — SC-general Stage 3 refinement

Date: 2026-09-12. Representative case: **subset 3-4** (family t3 / continuous),
same case as `bo/proxy_scale/gate.md`. Chosen because it sits in the label-free
refine band (proxy ∈ [0.5, 0.7]) and fires the stage-1 unlock
(`recentre_residual_max_cm` 20.8 > 10).

## Criteria (from Stage-3 plan)

1. `score_scaled.py --subset 3-4 --anchor` reproduces Stage-2 holdout proxy
   **0.5196911758815168** to 1e-6.
2. One real round completes under `data/3-4-scgen-refinement/round1/`.
3. Round is scored with finite lean-4 features and a valid band.

## Lineage

```bash
./venv/bin/python bo/sc_general/score_scaled.py --subset 3-4 --anchor
./venv/bin/python bo/sc_general/refine_pilot.py --subset 3-4 --context
./venv/bin/python bo/sc_general/refine_pilot.py --subset 3-4 --round 1 \
  --overlay-json '{"denoising":{"mask_r_low":2.7,"mask_r_high":3.12,"mask_theta_low":1.0,"mask_theta_high":18.5},"enhancing":{"curvature_threshold":0.0015},"detecting":{"binary_threshold":110,"hough_threshold_oblique":22,"hough_threshold_horizontal":22,"hough_threshold_vertical":2200,"maxLineGap_oblique":50,"pattern_tolerance":18,"uniform_k_snap":true},"sam":{"segment_width":1100,"K_height":880,"angle":7.0}}'
```

Outputs:
- Anchor score log: `data/sc-general/stage3/gate_score_anchor.json.log`
- Context: `data/sc-general/stage3/packets/3-4/context.json`
- Round: `data/3-4-scgen-refinement/round1/` (+ `reflection_record.json`)

## Metrics (SC-general pruned_lean; GT held out)

| Step | proxy_scaled | band | F1@15 | fill | depth_nan | residual cm |
|---|---:|---|---:|---:|---:|---:|
| anchor | **0.519691** | refine | 0.244 | 0.571 | 0.195 | 20.8 |
| round1 | 0.488713 | reject | 0.170 | 0.603 | 0.190 | 20.8 |

Anchor delta vs Stage-2 holdout: **0.00e+00** (PASS).

Round1 status=`ok`, elapsed ≈ 192 s, all lean features finite, band assigned
(reject). The widen recipe lowered correspondence F1 and therefore the new
proxy — expected possible outcome; proves the SC-general scorer tracks the
new features (not a silent failure).

## Pass/fail

| check | result |
|---|---|
| anchor proxy matches Stage-2 to 1e-6 | **PASS** |
| round1 pipeline status ok | **PASS** |
| finite lean features + band | **PASS** |

**GATE: PASS — proceed to the remaining panel (22 cases × 3 rounds).**
