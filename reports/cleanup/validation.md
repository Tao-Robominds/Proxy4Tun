# Cleanup validation (2026-09-18)

- Holdout: Spearman 0.817, MAE 0.109, pair rank 1.0 (n=27)
- Selector arms: fable_fresh 0.751 Δ+0.013; gpt56 0.760; gemini38 0.759; random 0.752 — all VERIFY OK
- `error_analysis_publish.py` regenerated `paper/Proxy4Tun/figs/error_maps.pdf` from compact `data/refinement/`
- Cold store: `/home/boringtao/Proxy4Tun-cold-store/` with `zstd -t` + spot-extract of `data-_archive` and `data-refinement`
- Tag `v1.0-aic-submission` unchanged at `0f267587`
- Manuscript compile: see `paper/Proxy4Tun/main_claude.pdf` page count in this commit's notes
