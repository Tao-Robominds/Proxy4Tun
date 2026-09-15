# Stage 3 Gemini 3.8 gate — subset 3-4 round 1

Generated before scaling the 22-case Gemini 3.8 campaign.

## Criteria
- Fresh Gemini 3.8 agent proposal provenance (`model=inherit`, per-case agent id)
- Sanitized packet under `data/sc-general/stage3/packets-gemini38/3-4/`
- Valid family-bounded overlay (unknown/dead knobs rejected)
- Round completes with `status=ok` and a finite 4-feature `proxy_scaled`
- Output under `data/refinement/gemini38/3-4/` (not det/fable/gpt56 trees)
- No GT files read during proposal

## Context (GT-blind)
- family: t3 / continuous
- anchor proxy_scaled: **0.520** (band=refine)
- features: F1@15=0.244, fill=0.571, ring_count_error=0.0, nan=0.195
- residual: **20.8 cm** → `stage1_unlocked=true`
- packet: `data/sc-general/stage3/packets-gemini38/3-4/context.json`
- images attached from packet `images/` + SC correspondence overlay

## Round 1 CoT (agent)
- Agent id: `ce41a8ef-d7e8-4b58-b0ad-9161c2caa60e`
- Model: `inherit` (Gemini 3.8 session engine)
- Observation: high residual (20.8 cm), low F1, unsupported boundaries; orientation OK
- Rule: fix unfolding first when residual ≫ 10 cm; keep T3 SAM mid-priors
- Failure mode: `f_curve_overfit`
- Overlay: full unfolding (slice 1.1, ransac 1.05, poly 3, seed 3) + SAM mid-priors
- Proposal file: `packets-gemini38/3-4/round1_proposal.json`

## Execution
- Command:
  ```bash
  ./venv/bin/python bo/sc_general/run_gemini38_campaign.py --apply 3-4 --round 1 \
    --proposal-json data/sc-general/stage3/packets-gemini38/3-4/round1_proposal.json \
    --agent-id ce41a8ef-d7e8-4b58-b0ad-9161c2caa60e
  ```
- Output: `data/refinement/gemini38/3-4/round1/`
- status=**ok**; proxy_scaled **0.553** (band=refine); residual **6.3 cm**;
  F1@15=0.456; ring_count_error=1.0; elapsed ~204 s
- Record: `arm=gemini38`, `proposer=Gemini-3.8 (fresh per-case agent)`, provenance.agent_id set

## Gate verdict: PASS
Plumbing, validation, scoring, and arm isolation work. Round-1 proxy improved
and residual dropped below the 10 cm lock. Campaign proceeds with resumed agent
for rounds 2–3, then the remaining 21 cases.
