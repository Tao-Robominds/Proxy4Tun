# GPT-5.6 medium

Same 15 admitted starts, frozen four-feature proxy, and selection rule.
0.770 is not a reproduced GPT-5.6 medium baseline; Release 1 attributes that
value to the deterministic arm on a 22-case panel.

## gpt56_medium (gpt-5.6-sol-medium)

- Start mean GT mIoU: 0.762
- Selected mean GT mIoU: 0.764
- Mean paired Δ: 0.002 (parent-tunnel 95% [0.000, 0.006])
- Improved/unchanged/harmed: 3/12/0; worst 0.000

## Selection policies

### gpt56_medium

- start: 0.762
- round1: 0.734
- uniform_round: 0.752
- max_proxy: 0.762
- monotone: 0.764
- oracle: 0.767
- Oracle recovery: 0.997; regret: 0.002

## Proposal stability

- gpt56_medium: valid 45/45; mean proposal mIoU 0.752; std Δ 0.047; share dropped >0.05 0.067

## Retrospective initial-GT strata

- gpt56_medium <0.5: n=0
- gpt56_medium [0.5,0.7]: n=3, mean Δ 0.000
- gpt56_medium >0.7: n=12, mean Δ 0.003

## Point-error fractions

- gpt56_medium selected: correct=0.870, FN=0.032, FP=0.047, swap=0.051

## All 27 subsets (non-admitted carry start)

- gpt56_medium: 0.001
