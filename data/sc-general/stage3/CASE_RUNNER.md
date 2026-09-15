# Fable-fresh case runner protocol (PROPOSE ONLY)

You are a fresh Fable 5.1 reflective parameter agent for ONE subset of arm `fable_fresh`.

## Hard isolation
Read ONLY for your subset `SUBSET`:
- `data/sc-general/stage3/packets-fable-fresh/SUBSET/AGENT_PROMPT.md`
- `data/sc-general/stage3/packets-fable-fresh/SUBSET/context.json`
- images under that packet's `images/` and `sc_correspondence_overlay.png` if present
- ontology paths listed in context.ontology

Do NOT read evaluation/, offline_gt.json, performance.md, mIoU/GT labels, any selections*, other cases' proposals, data/refinement/, data/bo/, data/anchors/, data/baseline.

## Forbidden
- Do NOT run `--apply`, `--finish`, or `--slim`.
- Do NOT set `FABLE_FRESH_ALLOW_APPLY`.
- Do NOT start GPU / pipeline / SAM jobs.
- A separate serial apply queue owns all applies.

## Loop (propose only)
1. Run: `./venv/bin/python bo/sc_general/run_fable_fresh_campaign.py --emit SUBSET`
2. Read AGENT_PROMPT.md, context.json, and emit_meta.json. Determine `next_round`.
3. If `next_round` is null / > 3 / case already has three ok rounds, stop and say DONE_PROPOSALS.
4. If `packets-fable-fresh/SUBSET/roundN_proposal.json` already exists for next_round, do not rewrite unless emit says the prior apply invalidated it; then wait (stop) — the queue will apply it.
5. Otherwise write ONE JSON object to
   `data/sc-general/stage3/packets-fable-fresh/SUBSET/roundN_proposal.json`
   with keys: observation, rule, failure_mode, rationale, overlay, full.
   Stay in bounds. Omit unfolding if stage1_unlocked is false.
6. Print: `PROPOSAL_READY subset=SUBSET round=N path=...`
7. Stop. Do not apply. Do not loop into apply. A supervisor will re-invoke you after the apply completes if another round is needed.

Work from repo root `/home/boringtao/Projects/Proxy4Tun`. Use the local venv python. Never overwrite data/anchors or data/bo.
