# Release 1.0

Snapshot of experiment results moved out of the live tree on 2026-09-18 so the
pipeline can be rerun from scratch.

| Path | Contents |
|---|---|
| `data/anchors/` | Frozen full-pipeline anchor runs (1-1 … 5-1) |
| `data/bo/` | All consolidated BO phase artifacts |
| `data/refinement/` | Compact refinement labels and JSON |
| `data/sc-general/` | Stage-2 scores and stage-3 selections |
| `exports/` | Manuscript evaluation panels |
| `reports/` | Experiment reports from this release |
| `logs/` | Pipeline logs |
| `LINEAGE.md` | Claim-to-artifact map for this release |
| `code/` | Older BO packages and drawing scripts |

Live inputs and code stay at the repository root: `anchors/` (parameter
profiles), `data/subsets/`, `bo/`, `sam4tun/`, `agents/`, `scripts/`.
New runs go under `data/<experiment-id>/`, not back into this snapshot.

Full forensic archives of the pre-compact refinement tree and `data/_archive`
remain at `/home/boringtao/Proxy4Tun-cold-store/`.
