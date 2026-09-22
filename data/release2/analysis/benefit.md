# Benefit

Admitted panel: 15 subsets × 3 arms.

## fable

- Start mean GT mIoU: 0.762
- Selected mean GT mIoU: 0.769
- Mean paired Δ: 0.007 (parent-tunnel bootstrap 95% [-0.009, 0.053])
- Median Δ: 0.000; improved/unchanged/harmed: 4/8/3; worst -0.143

- complex: mean Δ 0.007 (n=5)
- continuous: mean Δ -0.021 (n=7)
- staggered: mean Δ 0.069 (n=3)

## gemini38

- Start mean GT mIoU: 0.762
- Selected mean GT mIoU: 0.776
- Mean paired Δ: 0.014 (parent-tunnel bootstrap 95% [-0.002, 0.054])
- Median Δ: 0.000; improved/unchanged/harmed: 4/6/5; worst -0.015

- complex: mean Δ 0.004 (n=5)
- continuous: mean Δ -0.004 (n=7)
- staggered: mean Δ 0.070 (n=3)

## random

- Start mean GT mIoU: 0.762
- Selected mean GT mIoU: 0.738
- Mean paired Δ: -0.024 (parent-tunnel bootstrap 95% [-0.033, 0.010])
- Median Δ: 0.000; improved/unchanged/harmed: 1/9/5; worst -0.115

- complex: mean Δ -0.019 (n=5)
- continuous: mean Δ -0.037 (n=7)
- staggered: mean Δ 0.000 (n=3)

## All 27 subsets (non-admitted carry start)

- random: mean Δ over 27 = -0.013
- fable: mean Δ over 27 = 0.004
- gemini38: mean Δ over 27 = 0.008

## Retrospective initial-GT strata (admitted only)

- fable <0.5: n=0
- fable [0.5,0.7]: n=3, mean Δ 0.068
- fable >0.7: n=12, mean Δ -0.009
- gemini38 <0.5: n=0
- gemini38 [0.5,0.7]: n=3, mean Δ 0.071
- gemini38 >0.7: n=12, mean Δ -0.001
- random <0.5: n=0
- random [0.5,0.7]: n=3, mean Δ -0.006
- random >0.7: n=12, mean Δ -0.028
