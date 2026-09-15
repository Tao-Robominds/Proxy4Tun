# Stage 3 Fable-5.1 fresh gate — subset 3-4 (3 rounds)

Generated before scaling the 22-case `fable_fresh` campaign.

## Criteria
- Fresh Fable 5.1 agent proposal provenance (`model=claude-fable-5-1-thinking-high`, per-case agent id)
- Sanitized packet under `data/sc-general/stage3/packets-fable-fresh/3-4/`
- Valid family-bounded overlay (unknown/dead knobs rejected)
- All three rounds complete with `status=ok` and a finite 4-feature `proxy_scaled`
- Selection JSON written under `selections-fable-fresh/`
- Output under `data/refinement/fable_fresh/3-4/` (not legacy fable / gpt / gemini / random trees)
- No GT files read during proposal

## Context (GT-blind)
- family: t3 / continuous
- anchor proxy_scaled: **0.520** (band=refine)
- features: F1@15=0.244, fill=0.571, ring_count_error=0.0, nan=0.195
- residual: **20.8 cm** → `stage1_unlocked=true`
- packet: `data/sc-general/stage3/packets-fable-fresh/3-4/context.json`
- agent id: `dda9350d-e500-4cfd-b2f7-b8afd09ce9d1`

## Round results
| round | status | proxy_scaled | band | residual_cm | elapsed_s | full |
|---|---|---:|---|---:|---:|---|
| 1 | ok | 0.533 | refine | 21.8 | 194 | true |
| 2 | ok | 0.530 | refine | 20.8 | 190 | false |
| 3 | ok | 0.503 | refine | 20.8 | 186 | false |

## Selection
- selected **round2** Δproxy=+0.010 ΔmIoU=-0.021
- reason: best proxy among admissible candidates (start eligible)
- file: `data/sc-general/stage3/selections-fable-fresh/3-4.json`

## Commands
```bash
./venv/bin/python bo/sc_general/run_fable_fresh_campaign.py --emit 3-4
# fresh subagent wrote round{1,2,3}_proposal.json (resumed for R2–R3)
./venv/bin/python bo/sc_general/run_fable_fresh_campaign.py --apply 3-4 --round N \
  --proposal-json data/sc-general/stage3/packets-fable-fresh/3-4/roundN_proposal.json \
  --agent-id dda9350d-e500-4cfd-b2f7-b8afd09ce9d1
./venv/bin/python bo/sc_general/run_fable_fresh_campaign.py --finish 3-4
```

## Gate verdict: PASS
Plumbing, validation, scoring, selection, slim, and arm isolation work.
Campaign proceeds with a fresh per-case agent for the remaining 21 panel cases.
