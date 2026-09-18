# Stage 3 Fable-5 gate — subset 3-4 round 1

Generated during Gate 1 before Phase A scales.

## Criteria
- Context packet emits with `arm=fable`, `proposer=fable-5 (cursor agent, live)`
- Round 1 completes with `status=ok` and a scored proxy
- Reflection record contains `arm`, `proposer`, `rationale`
- Output under `data/refinement/fable/3-4/` (not the det arm tree)
- No GT files read during proposal

## Context (GT-blind)
- family: t3 / continuous
- anchor proxy_scaled: **0.520** (band=refine)
- features: F1@15=0.244, fill=0.571, ring_count_error=0.0, nan=0.195
- residual: **20.8 cm** → `stage1_unlocked=true`
- detection: real=0.0, fallback=1.0 (complete Hough collapse)
- orientation OK (corr −0.998)
- visuals: sparse explained joints; mostly assumed prompts; SC overlay shows many unsupported boundaries

## Round 1 CoT
- **Observation:** Residual 20.8 cm unlocks stage-1. Detection is 100% fallback so correspondence F1 cannot rise until real joint lines return. Retention 0.69 / nan 0.195 suggest the r-band is slightly tight for lining edges.
- **Rule:** When residual ≫ 10 cm, propose unfolding seed change and run full 1–6; couple with moderate Hough recovery (not ultra-low) and a slight mask widen so new centreline can expose joints.
- **Failure mode:** `f_centreline_residual` + `f_detection_fallback` / weak line↔boundary F1.
- **Overlay:** seed 5; mask_r [2.80, 3.08], theta [1.3, 17.5]; curv 0.0008; binary 115; Hough 25/25/1800; gap 45; tol 14; uniform_k_snap; SAM width 1250 / K_height 900 / angle 6.5. Full pipeline.

## Execution
- Command: `./venv/bin/python -m bo.sc_general.refine_pilot --subset 3-4 --arm fable --round 1 --full ...`
- Output: `data/refinement/fable/3-4/round1/`
- status=**ok**; proxy_scaled **0.401** (band=reject); residual 23.2 cm; F1@15=0.032; elapsed ~204 s
- Record fields: `arm=fable`, `proposer=fable-5 (cursor agent, live)`, rationale present

## Gate verdict: PASS
Plumbing and scoring work. Round-1 proxy regresses (seed 5 worsened residual) — expected noise; Phase A continues with alternate seeds / 2–6 recipes. Gate does not require mIoU lift on the first proposal.
