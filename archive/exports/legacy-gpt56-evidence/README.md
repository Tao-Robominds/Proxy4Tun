# GPT-5.6 Isolated Refinement Campaign

Fresh per-subset GPT-5.6 Sol reflection on the nine GT-low refine-band subsets,
isolated from prior Fable / Cursor campaign outputs.

## Isolation

- Allowed: sanitized knowledge under `knowledge/`, per-subset packets, own prior rounds.
- Denied: `data/bo/reflect/**`, Fable recipes (`bo/proxy_scale/run_subset.py`),
  prior selections/reports, raw `experiences.md` §8, evaluation/GT during the loop.
- Artifacts: `data/<subset>-gpt56-refinement/round{1,2,3}/`
- Selection: frozen scaled proxy, monotone accept, residual tiebreak (`select_round.py`)

## Commands

```bash
# Build GT-blind packet
./venv/bin/python gpt56-refinement/build_packet.py --subset 3-4

# Run a validated overlay (after GPT proposes JSON)
./venv/bin/python gpt56-refinement/run_round.py --subset 3-4 --round 1 \
  --proposal-json gpt56-refinement/packets/3-4/round1_proposal.json

# Select best round (GT still offline)
./venv/bin/python gpt56-refinement/select_round.py --subset 3-4

# Aggregate after all nine
./venv/bin/python gpt56-refinement/make_report.py
```
