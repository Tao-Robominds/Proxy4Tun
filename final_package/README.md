# Final package — Proxy4Tun SC-general

Intact research package for the manuscript claim:

1. **Calibration** — 120 parameter trials (32 Sobol + 8 GP × three families)
2. **Four-feature proxy** — frozen Ridge package + 54-run stress-test scores
3. **Refinement arms** — Fable 5.1 (fresh per-case; `fable_fresh`), GPT-5.6, Gemini 3.8, and the random-overlay control (legacy persistent-session Fable arm superseded)


Protected source trees (`data/bo/`, `data/anchors/`, `anchors/`) stay in place;
this directory only symlinks or copies them.

## Layout

| Dir | Contents |
|---|---|
| `01_calibration/` | Symlink to `data/bo/bayes`; copies of `training_table.csv`, `holdout_scores.csv` |
| `02_proxy/` | Copies of `models.json`, `ablation.json`, `data/sc-general/stage2/` |
| `03_refinement/` | Symlinks to `data/refinement/{fable_fresh,fable,gpt56,gemini38,random}`, `stage3`, exports |
| `04_inputs/` | Symlinks to subsets, anchors, ontology |

## Regeneration (high level)

```bash
# Rebuild stage-2 tables from bayes indices (does not re-run pipelines)
./venv/bin/python bo/sc_general/build_tables.py --split both
./venv/bin/python bo/sc_general/score_holdouts.py

# Random-overlay control arm
./venv/bin/python bo/sc_general/run_random_campaign.py --design
./venv/bin/python bo/sc_general/run_random_campaign.py --all
./venv/bin/python bo/sc_general/selector_policies.py --arms fable_fresh,gpt56,gemini38,random
./venv/bin/python bo/sc_general/plot_publish_figures.py
./venv/bin/python bo/sc_general/error_analysis_publish.py
```

See `SHA256SUMS` for frozen small-artifact digests.
See `archive/MANIFEST.md` for material moved out of the live tree.
See root `README.md` § Reproducing the paper for the full SC-general script list.
