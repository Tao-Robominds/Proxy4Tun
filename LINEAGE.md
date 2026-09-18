# Proxy4Tun lineage

Maps manuscript claims to frozen artifacts, producer scripts, and cold-storage
archives. Compact verification does not require restoring cold archives.

| Item | Value |
|---|---|
| Canonical manuscript | `paper/Proxy4Tun/main_claude.tex` |
| Immutable submission tag | `v1.0-aic-submission` |
| Pre-cleanup freeze tag | `pre-cleanup-2026-09-18` |
| Cold store URI | `/home/boringtao/Proxy4Tun-cold-store/` |
| Protected (never relocated) | `anchors/`, `data/anchors/`, `data/bo/` (+ `data/bo-*` aliases) |

## Claim → artifact

| Claim (paper) | Primary artifact | Producer | Notes |
|---|---|---|---|
| 120 calibration runs (32 Sobol + 8 GP × 3 families) | `data/bo/bayes/` + `data/sc-general/stage2/training_table.csv` | `bo/bayes/*`, `bo/sc_general/build_tables.py` | Protected BO tree |
| Four-feature Ridge proxy | `bo/sc_general/models.json`, `ablation.json` | `bo/sc_general/train_proxy.py` / ablation | Copied in `final_package/02_proxy/` |
| Holdout Spearman 0.817 / MAE 0.109 / 27/27 ranking | `data/sc-general/stage2/holdout_scores.csv` | `bo/sc_general/score_holdouts.py` | 54 runs (27 anchor + 27 bad) |
| Refinement panel 0.738 → 0.751–0.760 (LLMs) / 0.752 (random) | `exports/sc-general-random-evaluation/panel_all_arms.csv` | `bo/sc_general/selector_policies.py` | 22 cases × 4 arms |
| Error maps / point-level composition | `paper/Proxy4Tun/figs/error_maps.pdf`, `error_analysis_numbers.json` | `bo/sc_general/error_analysis_publish.py` | Needs `data/refinement/` evidence + holdout paths |
| Concept / result figures | `paper/Proxy4Tun/figs/*.pdf` | `scripts/drawing/plot_concept_figures.py`, `bo/sc_general/plot_publish_figures.py`, `bo/bayes/plot_*.py` | Output under `paper/Proxy4Tun/figs/` |

## Local compact evidence

| Path | Role |
|---|---|
| `final_package/` | Checksummed copies of tables, models, selections, paper, exports |
| `data/sc-general/stage2/` | Training + holdout score tables |
| `data/sc-general/stage3/` | Selections, gates, campaign reports, proposal packets |
| `data/refinement/` | Post-cleanup: compact labels/JSON only (full trees cold-stored) |
| `exports/sc-general-random-evaluation/` | Canonical panel CSV/JSON |
| `data/subsets/` | Input TXT definitions for optional full reruns |

## Cold-store components

Local cold store (exFAT external volume was corrupt and unused):

`/home/boringtao/Proxy4Tun-cold-store/`

Restore:

```bash
COLD=/home/boringtao/Proxy4Tun-cold-store
sha256sum -c "$COLD/checksums/data-refinement.sha256"
zstd -t "$COLD/components/data-refinement.tar.zst"
zstd -d -c "$COLD/components/data-refinement.tar.zst" | tar -C /path/to/restore -xf -
```

| Archive | Source | Status |
|---|---|---|
| `components/data-refinement.tar.zst` | full `data/refinement/` | verified spot-extract + `zstd -t` |
| `components/data-_archive.tar.zst` | `data/_archive/` | verified spot-extract + `zstd -t` |

Checksums: `$COLD/checksums/*.sha256`.

Live `data/refinement/` is the compact label/JSON evidence set needed for
`error_analysis_publish.py`. Full run trees are only in the archive above.

## BO phase index (protected `data/bo/`)

| Phase | Status | Referenced by |
|---|---|---|
| `unified` / `elegant` | Historical family BO | Holdout bad-run paths in `holdout_scores.csv` |
| `full_stage` / `bayes` | Calibration lineage | Stage-2 tables |
| `reflect` / `notebook_direct` / `archive_v0` | Historical | `bo/REPORT.md` |
| Live method code | `bo/` (+ `bo/sc_general/`) | All current scripts |

Duplicate pre-consolidation code roots are under `archive/bo-history/`.

## Reproduction modes

1. **Compile paper** — TeX + `paper/Proxy4Tun/figs/`
2. **Compact numerical verification** — `final_package/` + selector/holdout scripts
3. **Full pipeline rerun** — new `data/<experiment-id>/` only
4. **Cold replay** — restore component archive, then re-run analysis scripts
