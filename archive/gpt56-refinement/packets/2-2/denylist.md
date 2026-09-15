# Denylist — GPT-5.6 isolated refinement

The agent must NOT read, search, open, or cite:

1. `data/bo/reflect/**` (all prior Fable / Cursor reflection arms)
2. `bo/proxy_scale/run_subset.py` (hardcoded Fable recipes)
3. `bo/proxy_scale/selections/**`, `refined_scores.csv`, `report.md`, `gate.md`
4. `data/bo/reflect/campaign_cursor2.md` and any campaign CoT logs
5. `agents/ontology/experiences.md` raw file (use sanitized snapshot only)
6. Paper PoC result sections / figures with prior campaign numbers
7. Any `evaluation/` directory or `performance.md` (GT mIoU)
8. Prior agent transcripts under `.cursor/projects/**/agent-transcripts/`
9. Other subsets’ GPT-5.6 packets or results (no cross-subset transfer)
10. Any file whose name contains `cursor2`, `cursor3`, `fable`, or `cursor2_s1`

GT mIoU is withheld until after all three overlays are frozen and selected.
