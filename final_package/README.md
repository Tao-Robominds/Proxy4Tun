# Final package — Proxy4Tun SC-general

Self-contained compact research package for manuscript claims (no symlinks to large run trees).

1. **Calibration** — tables for 120 trials; full run trees remain in protected `data/bo/bayes`
2. **Four-feature proxy** — frozen Ridge package + 54-run stress-test scores
3. **Refinement** — stage-3 selections/gates/campaign reports; compact per-round evidence under `data/refinement/`
4. **Inputs** — subset manifest, family anchor parameter snapshots, ontology
5. **Paper** — `main_claude.tex` + figures
6. **Exports** — panel CSV/JSON evaluation summaries

Protected source trees (`data/bo/`, `data/anchors/`, `anchors/`) stay in the repo and are not duplicated here.

Full forensic run trees (especially `data/refinement` ~95 GiB and `data/_archive`) live in cold storage:
`/media/boringtao/R4Tun/Proxy4Tun-cold-store/` — see root `LINEAGE.md`.

## Regeneration (compact)

```bash
./venv/bin/python bo/sc_general/selector_policies.py --arms fable_fresh,gpt56,gemini38,random
./venv/bin/python bo/sc_general/plot_publish_figures.py
./venv/bin/python bo/sc_general/error_analysis_publish.py
```

Full pipeline reruns use `data/subsets/` + `anchors/` into a new `data/<experiment-id>/`.
