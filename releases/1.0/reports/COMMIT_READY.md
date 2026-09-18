# Commit ready (not created)

Proposed message:

```
Reorganise around final package; add random-overlay control arm

Consolidate SC-general refinement under final_package/, archive legacy
trees, and add a sparsity-matched random control (66 runs) with shared
selector statistics and manuscript updates.
```

Staged highlights:
- `bo/sc_general/` (shared validator, random campaign, selector_policies)
- `exports/sc-general-*-evaluation/` including random arm
- `final_package/` manifest + symlinks/copies
- `archive/` (gpt56-refinement, paper_old, legacy exports)
- `paper/Proxy4Tun_manuscript/` publish tex + evidence tables
- README / `bo/paths.py` layout fixes

Not staged (gitignored under `/data/*`):
- `data/refinement/{fable,gpt56,gemini38,random}/`
- `data/sc-general/stage3/` (gate, design, selections, logs)
- `data/_archive/`

Left unstaged on purpose:
- `paper/R4Tun/` local edits unrelated to this plan
- latex build intermediates if present

Say the word to create the commit.
