# SC-general one-instance gate
Generated 2026-09-12T18:07:26.084767
Case: `/home/boringtao/Projects/Proxy4Tun/data/anchors/5-1` (complex family; label map via only_label.csv fallback)
Command: `./venv/bin/python bo/sc_general/pilot.py --gate`

## 1. Hough replay reproduces stored prompt points
- rows replayed/stored: 10/10
- max |dx|, |dy|: 2.27e-13, 0.00e+00 px (criterion <= 1 px)
- type agreement: 1.00 (criterion 1.00)
- ring_count 10 from state.pkl
- **PASS**

## 2. Fallback label map coverage (complex has no results.pkl)
- source: only_label.csv; direct-evidence coverage 0.077; after 25 px fill 0.901
- labelled (>0) fraction 0.885 vs stored sam_fill_rate 0.753
- criterion: filled coverage >= 0.80 and labelled fraction > 0.5 x fill rate
- **PASS**

## 3. results.pkl composition vs reprojected labels (3-1, both routes exist)
- evidence pixels: 453611
- label agreement (non-background): 0.9983 (criterion >= 0.98)
- ring agreement: 0.9361 (criterion >= 0.90)
- **PASS**

## 4. All candidate features finite
- 49 numeric features; non-finite (excluding sam_score*, N/A for complex): none
- **PASS**

## Feature values on the gate case

| feature | value |
|---|---|
| n_oblique_lines | 31.0000 |
| n_horizontal_lines | 68.0000 |
| line_px | 21493.0000 |
| boundary_px | 20974.0000 |
| boundary_bg_px | 81706.0000 |
| boundary_ring_px | 41621.0000 |
| line_explained@8 | 0.4028 |
| line_explained_obl@8 | 0.3363 |
| line_explained_hor@8 | 0.4464 |
| boundary_explained_line@8 | 0.1467 |
| boundary_explained_edge@8 | 0.2051 |
| correspondence_f1@8 | 0.2150 |
| line_explained@15 | 0.6752 |
| line_explained_obl@15 | 0.6197 |
| line_explained_hor@15 | 0.7116 |
| boundary_explained_line@15 | 0.2757 |
| boundary_explained_edge@15 | 0.4049 |
| correspondence_f1@15 | 0.3916 |
| line_explained@25 | 0.8273 |
| line_explained_obl@25 | 0.8884 |
| line_explained_hor@25 | 0.7873 |
| boundary_explained_line@25 | 0.3441 |
| boundary_explained_edge@25 | 0.5522 |
| correspondence_f1@25 | 0.4861 |
| chamfer_line_to_bnd_px | 16.4265 |
| chamfer_bnd_to_line_px | 114.2246 |
| chamfer_sym_px | 65.3255 |
| chamfer_median_line_to_bnd_px | 10.0499 |
| bnd_edge_dist_mean_px | 33.1588 |
| prompt_k_hit | 0.8000 |
| prompt_k_hit_real | 0.8571 |
| prompt_real_frac | 0.7000 |
| prompt_block_hit | 0.8000 |
| transition_valid_frac | 1.0000 |
| transition_pairs | 7.0000 |
| ring_label_completeness | 1.0000 |
| ring_label_presence | 1.0000 |
| mask_fragmentation | 0.7143 |
| mask_rectangularity | 0.7618 |
| block_height_dispersion | 0.0647 |
| n_rings_labelled | 10.0000 |
| rings_expected | 10.0000 |
| boundary_straightness_px | 1.7016 |
| sam_score_mean | nan |
| sam_score_min | nan |
| sam_score_p10 | nan |
| labelmap_coverage_known | 0.0773 |
| labelmap_coverage_filled | 0.9013 |
| vertical_fallback | 1.0000 |

## Overall: **PASS**
