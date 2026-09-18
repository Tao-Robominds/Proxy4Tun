# Stage 3 GPT-5.6 gate — subset 3-4 round 1

Generated before scaling the 22-case GPT-5.6 campaign.

## Criteria
- Fresh GPT-5.6 agent proposal provenance (`model=gpt-5.6-sol-medium`, per-case agent id)
- Sanitized packet under `data/sc-general/stage3/packets-gpt56/3-4/`
- Valid family-bounded overlay (unknown/dead knobs rejected)
- Round completes with `status=ok` and a finite 4-feature `proxy_scaled`
- Output under `data/refinement/gpt56/3-4/` (not det/fable trees)
- No GT files read during proposal

## Context (GT-blind)
- family: t3 / continuous
- anchor proxy_scaled: **0.520** (band=refine)
- features: F1@15=0.244, fill=0.571, ring_count_error=0.0, nan=0.195
- residual: **20.8 cm** → `stage1_unlocked=true`
- packet: `data/sc-general/stage3/packets-gpt56/3-4/context.json`
- images attached from packet `images/` + SC correspondence overlay

## Round 1 CoT (agent)
- Agent id: `874c42b3-747e-4646-877c-dc7bd169f07f`
- Model: `gpt-5.6-sol-medium`
- Observation: high residual, fallback prompts, low F1, fragmented joints
- Rule: fix unfolding first; keep T3 radial/theta priors; relax Hough within bounds
- Failure mode: centre-curve residual + fragmented detection / fallback prompts
- Overlay: full 1–6 with seed 0, denser slices, cubic poly; moderate Hough; T3 SAM priors
- Proposal file: `packets-gpt56/3-4/round1_proposal.json`

## Execution
- Command:
  ```bash
  ./venv/bin/python bo/sc_general/run_gpt56_campaign.py --apply 3-4 --round 1 \
    --proposal-json data/sc-general/stage3/packets-gpt56/3-4/round1_proposal.json \
    --agent-id 874c42b3-747e-4646-877c-dc7bd169f07f
  ```
- Output: `data/refinement/gpt56/3-4/round1/`
- status=**ok**; proxy_scaled **0.296** (band=reject); residual 12.8 cm;
  F1@15=0.0; ring_count_error=1.0; elapsed ~208 s
- Record: `arm=gpt56`, `proposer=GPT-5.6 (fresh per-case agent)`, provenance.agent_id set

## Gate verdict: PASS
Plumbing, validation, scoring, and arm isolation work. Round-1 proxy regresses
(as with the Fable gate) — gate does not require mIoU/proxy lift on the first
proposal. Campaign proceeds with resumed agent for rounds 2–3, then the remaining
21 cases.
