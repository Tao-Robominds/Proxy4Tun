# Allowlist — GPT-5.6 isolated refinement

The agent may read ONLY:

1. `gpt56-refinement/packets/<subset>/packet.json`
2. `gpt56-refinement/packets/<subset>/images/*` (listed PNGs only)
3. `gpt56-refinement/packets/<subset>/AGENT_PROMPT.md`
4. `gpt56-refinement/packets/<subset>/allowlist.md` and `denylist.md`
5. `gpt56-refinement/knowledge/experiences_sanitized.md`
6. `gpt56-refinement/knowledge/sam4tun_ontology.yaml`
7. `gpt56-refinement/knowledge/tunnel_priors.yaml`
8. For rounds 2–3 of the **same** subset only: that subset’s own prior
   `data/<subset>-gpt56-refinement/round*/agent_feedback.json` and
   proposal JSON (never other subsets, never Fable arms)

The agent may write ONLY a JSON proposal (observation, failure_mode,
rationale, overlay). Pipeline execution is performed by the campaign harness.
