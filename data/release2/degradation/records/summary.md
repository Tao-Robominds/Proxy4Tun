# Degradation summary

Completed runs: 54 / 54.

- Spearman rho: 0.791
- MAE: 0.106
- Subset bootstrap 95% interval (2000, pairs kept, stratified by family): [0.715, 0.862]
- Parent-tunnel enumeration (3125 = 5^5 ordered resamples): [0.745, 0.869]

## By family and arm

- complex: rho 0.788, MAE 0.063 (n=18)
- continuous: rho 0.924, MAE 0.124 (n=18)
- staggered: rho 0.798, MAE 0.130 (n=18)
- degraded: rho 0.006, MAE 0.078 (n=27)
- reference: rho 0.319, MAE 0.133 (n=27)

Strict pair ranking: 27/27 pairs with reference score > degraded score.

## Alarms at 0.5

- Overall precision 0.931, recall 1.000 (degraded flagged 27/27, reference flagged 2/27).
- complex: precision 1.000, recall 1.000 (degraded 9/9, reference 0/9).
- continuous: precision 0.818, recall 1.000 (degraded 9/9, reference 2/9).
- staggered: precision 1.000, recall 1.000 (degraded 9/9, reference 0/9).

## Plan 4 starting bands

Admitted starts are reference runs with score in [0.5, 0.7] inclusive.

| subset | family | score | band | gt_miou |
| --- | --- | ---: | --- | ---: |
| 1-1 | staggered | 0.614 | refine | 0.784 |
| 1-2 | staggered | 0.720 | accept | 0.809 |
| 1-3 | staggered | 0.647 | refine | 0.827 |
| 1-4 | staggered | 0.709 | accept | 0.853 |
| 1-5 | staggered | 0.641 | refine | 0.676 |
| 2-2 | staggered | 0.726 | accept | 0.615 |
| 2-3 | staggered | 0.748 | accept | 0.795 |
| 2-4 | staggered | 0.723 | accept | 0.835 |
| 2-5 | staggered | 0.710 | accept | 0.893 |
| 3-10 | continuous | 0.603 | refine | 0.853 |
| 3-2 | continuous | 0.460 | flag | 0.631 |
| 3-3 | continuous | 0.535 | refine | 0.808 |
| 3-4 | continuous | 0.526 | refine | 0.622 |
| 3-5 | continuous | 0.441 | flag | 0.588 |
| 3-6 | continuous | 0.697 | refine | 0.836 |
| 3-7 | continuous | 0.555 | refine | 0.845 |
| 3-8 | continuous | 0.571 | refine | 0.723 |
| 3-9 | continuous | 0.659 | refine | 0.820 |
| 4-1 | complex | 0.650 | refine | 0.741 |
| 4-2 | complex | 0.697 | refine | 0.787 |
| 4-3 | complex | 0.621 | refine | 0.554 |
| 4-4 | complex | 0.615 | refine | 0.784 |
| 4-5 | complex | 0.705 | accept | 0.808 |
| 5-2 | complex | 0.706 | accept | 0.793 |
| 5-3 | complex | 0.704 | accept | 0.762 |
| 5-4 | complex | 0.717 | accept | 0.760 |
| 5-5 | complex | 0.630 | refine | 0.775 |

Admitted (15): 1-1, 1-3, 1-5, 3-10, 3-3, 3-4, 3-6, 3-7, 3-8, 3-9, 4-1, 4-2, 4-3, 4-4, 5-5.
