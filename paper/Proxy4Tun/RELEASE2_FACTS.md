# Release 2 fact ledger (manuscript only)

Canonical sources under `data/release2/`. Do not use any other experiment tree.

## Proxy (four features)
- Features: `correspondence_f1@15`, `sam_fill_rate`, `ring_count_error`, `depth_nan_ratio`
- Source: `proxy/four_feature.json` (α=10, intercept=0.358867, n_train=120)
- Weights: +0.0872, +0.0939, −0.0386, −0.0545
- Training fit (frozen package on 120 rows): MAE≈0.100, Spearman≈0.877
- LOFO (`proxy/lofo.csv`, set=four): Spearman 0.809, MAE 0.129
- Permutation null (four): unpermuted 0.809; perm mean −0.121 (std 0.082, n=20)
- PQ/SC/ten LOFO: 0.615/0.166; 0.758/0.147; 0.686/0.165

## Degradation (27 pairs / 54 runs)
- Source: `degradation/records/summary.md`, `pairs.csv`
- Spearman ρ=0.791; MAE=0.106; bootstrap 95% CI [0.715, 0.862]
- Strict pair ranking: **27/27**
- Alarm at 0.5: precision 0.931, recall 1.000 (degraded 27/27; reference flagged 2/27)
- Reference mean GT mIoU (27): 0.762; degraded mean ≈0.039

## Self-refinement (15 admitted × 3 rounds × 4 arms)
- Admission: reference proxy score ∈ [0.5, 0.7] (15 subsets listed in summary.md)
- Shared start mean GT mIoU: **0.762**
- Selected means: Fable **0.769**, Gemini **0.776**, GPT-5.6 medium **0.764**, random **0.738**
- Mean Δ / bootstrap 95% CI (parent-tunnel): Fable +0.007 [−0.009, 0.053]; Gemini +0.014 [−0.002, 0.054]; GPT +0.002 [0.000, 0.006]; random −0.024 [−0.033, 0.010]
- Up/same/down: Fable 4/8/3; Gemini 4/6/5; GPT 3/12/0; random 1/9/5
- Selection: max proxy among start∪valid; ties within 0.01 keep earlier
- Policies (monotone / round1 / oracle recovery): random 0.738 / 0.505 / 0.966; Fable 0.769 / 0.725 / 0.982; Gemini 0.776 / 0.737 / 0.993; GPT 0.764 / 0.734 / 0.997

## Proposal safety (45 valid proposals/arm)
- Share of proposals with ΔmIoU < −0.05: random 0.711; Fable 0.200; Gemini 0.111; GPT 0.067
- Proposal Δ std (population): random 0.284; Fable 0.079; Gemini 0.060; GPT 0.046

## Error / rotation limit
- Start swap fraction ≈0.052; selected swap ≈0.044–0.051 by arm
- Proxy-above-start precision: random 0.200; Fable 0.462; Gemini 0.346
- Case 1-5: start mIoU 0.676, phase 24.2°, score 0.641 → Fable/Gemini selected ≈0.88 with phase ≈14°

## Banned stale claims
- 22-case / nine-case GT-filtered panels; initial-GT [0.5,0.7] concentration
- five-feature lean; 0.738→0.768; 0.569→0.675; 0.456/0.722/0.757
- holdout ρ=0.817/0.827, MAE=0.109/0.086; “no false alarms”
- stage-1 annotation / unlock framing
