# Release 3: rotation-aware proxy and conditional rerun

Self-contained under `data/release3/`. Release 2 remains frozen.

| Stage | Status | Notes |
|---|---|---|
| Inputs copy | done | `data/release3/inputs/{references,calibration,degradation}` |
| Feature gate | done | `rotation_advantage` selected; `GATE_FEATURE.md` |
| Five-feature proxy | done | `configs/proxy/five_feature.json` |
| Degradation re-score | done | rho 0.825, MAE 0.139, 27/27; admitted N=24 |
| Refinement gate | in progress | random 1-1 passed; Fable attempt pending |
| Panel | pending | 24 × 4 arms × 3 rounds |
| Analysis | pending | benefit + vs Release 2 |
