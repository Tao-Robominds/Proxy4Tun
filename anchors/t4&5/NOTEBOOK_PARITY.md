# T4/T5 Notebook vs Anchor Parity Report

**Notebook:** `sam4tun/notebook/t4&5.ipynb`  
**Anchor:** `anchors/t4&5/` + `t45_geometry.py`  
**Parameter sets:** `4-1/` (CLI default), `5-1/` (rings 110–119)  
**Frozen runs (canonical):** `data/anchors/4-1/` (mIoU 0.635), `data/anchors/5-1/` (mIoU 0.808)  
**Parent index:** [`../NOTEBOOK_ANCHOR_PARITY.md`](../NOTEBOOK_ANCHOR_PARITY.md)

> Promoted cases use `canonical_orientation=true`. Pre-canonical mIoU 0.741 /
> 0.681 and `swap_tunnel_centers`-only recipes in the tables below are historical.

---

## 1. Implementation differences (untunable)

### 1.1 Stage map

| Stage | Notebook | Anchor |
|---|---|---|
| 1 Unfolding | Inline; top-tube filter hardcoded | `1_unfolding.py`; always `remove_top_tube` |
| 2 Denoising | `r` band 3.65–3.9 | Same algorithm, JSON params |
| 3 Enhancing | Upsample + asymmetric window | Same algorithm, JSON params |
| 4 Detection | Inline Hough + `assumed_y=200` fallback | Parameterized rho band + T12 assume ladder |
| 5 SAM | **Full SAM** per ring | **`geometric_segment` fallback** for tunnels 4/5, 7-class |
| 6 Evaluation | Inline | `6_evaluation.py` |

### 1.2 Unfolding

| Change | Notebook | Anchor |
|---|---|---|
| Top-tube filter | `top_n=10`, `radius=3.5` inline | `top_tube_top_n`, `top_tube_radius` |
| Axis swap | Commented out | `swap_tunnel_centers` (promoted: **false**) |
| Recentre | Absent | Optional; **`true` in `5-1/` only** |

### 1.3 Enhancing

Notebook and `4-1`/`5-1` JSON agree on upsample chain, outlier thresholds,
`coverage_mode: asymmetric_full`, `use_upsampled_surface`, `enable_outlier_interpolation`.

### 1.4 Detection

| Change | Notebook | Anchor |
|---|---|---|
| Vertical rho band | `W/2 + [2,5]×1850×res` inline | `vertical_rho_mode: w2_offset_band` |
| Oblique K-offset (T12) | `+θ`: `y−0.5K`; `−θ`: `y+0.5K` | **`+θ`: `y+0.5K`; `−θ`: `y−0.5K`** (shared `t12_pattern`) |
| Missing joints | `assumed_y = 200` | Alternating 1123/1553 + `check_distance_pattern` |
| Synthetic verticals | Real Hough only | **`5-1`:** `hough_threshold_vertical=5000` → 10 ring-centre lines |

### 1.5 SAM — geometric fallback

```python
# anchors/t4&5/5_sam.py
_use_geometric_fallback = _tunnel_prefix in ("4", "5") and segment_per_ring == 7
```

| Aspect | Notebook | Promoted anchor |
|---|---|---|
| Segmentation | `sam_segment` → `SamPredictor` per block | **`geometric_segment`** — circular tiling from detected K-Y |
| Geometry templates | Inline cell ~79 | `t45_geometry.py` (faithful extraction) |
| When SAM runs | Always | Only if tunnel prefix ∉ {4,5} or `segment_per_ring ≠ 7` |

This is the **largest behavioural gap** vs the notebook.

---

## 2. Parameter differences (tunable)

### 2.1 Shared notebook ↔ `4-1` / `5-1` (identical unless noted)

**Unfolding:** `diameter=7.5`, `slice_spacing_factor=1.8`, `polynomial_degree=2`,
`swap_tunnel_centers=false`, RANSAC suite, `delta=0.005`.

**Denoising:** `mask_r` 3.65–3.9, `y_step=0.1`, `z_step=0.001`, `grad_threshold=0.2`,
`smoothing_window_size=3`, `smoothing_offset=-0.005`.

**Enhancing:** upsample `0.09/0.045/0.0225`, depths `0.0065/0.013`,
`n_segment` [5, 14], `inter_radius=0.06`, `window_size=9`,
`ring_spacing_factor=1.8`, `curvature_outlier_min=0.01`.

**Detection (4-1 baseline):** Hough 50/100/50 oblique, 50/105/10 horizontal,
vertical 800, `K_height=1226.97`, `AB_height=3726.88`.

**SAM:** 7 segments, width 1800, K/AB/angle as notebook, `padding=150`,
`crop_margin=50`, `y_bounds=[4200, 13100]`.

### 2.2 Profile delta: `4-1/` vs `5-1/`

| Parameter | `4-1/` | `5-1/` |
|---|---:|---:|
| `residual_recentre` | false | **true** |
| `hough_threshold_oblique` | 50 | **35** |
| `minLineLength_oblique` | 100 | **80** |
| `maxLineGap_oblique` | 50 | **60** |
| `hough_threshold_horizontal` | 50 | **35** |
| `minLineLength_horizontal` | 105 | **80** |
| `maxLineGap_horizontal` | 10 | **15** |
| `hough_threshold_vertical` | 800 | **5000** |

All other stage JSON files are identical between profiles.

### 2.3 Notebook vs anchor value notes

| Item | Notebook | Anchor |
|---|---|---|
| `n_segment` in function default | `[10, 21]` doc (50-ring) | `n_segment_start/end` → `[5, 14]` |
| Detection assume | `y = 200` | Structured ladder |
| SAM execution | Neural | Geometric on 4/5 |

---

## 3. Anchor-only parameters (highlighted)

| Parameter | In JSON | Notebook | Notes |
|---|---|---|---|
| **`swap_tunnel_centers`** | yes | commented swap only | Gate: false wins (`gate_swap_ab.json`) |
| **`top_tube_radius`** | `3.5` | inline | T4/T5 top-tube slice filter |
| **`top_tube_top_n`** | `10` | inline | |
| **`deterministic_theta_orientation`** | `false` | absent | Available, off |
| **`residual_recentre`** | 4-1: false; **5-1: true** | **absent** | Fixes left-end voids on 5-1 |
| **`recentre_*`** | code defaults | absent | |
| **`coverage_mode`** | `asymmetric_full` | inline window | |
| **`use_upsampled_surface`** | `true` | same behaviour | Named in JSON |
| **`enable_outlier_interpolation`** | `true` | enabled inline | Named in JSON |
| **`curvature_outlier_min`** | `0.01` | inline | |
| **`ring_spacing_factor`** | `1.8` | inline `1.8` | |
| **`vertical_rho_mode`** | `w2_offset_band` | inline formula | |
| **`vertical_rho_spacing_mm`** | `1850` | inline | |
| **`vertical_rho_min_factor`** / **`max_factor`** | `2.0` / `5.0` | inline | |
| **`prompt_logic`** | `t12_pattern` | inline only | |
| **`uniform_k_snap`** | `false` | absent | |
| **`pattern_tolerance`** | `10` | absent | |
| **`geometry_profile`** | `t45` | absent | Selects `t45_geometry` |
| **`segment_order`** | 7-class list | implicit | Used by geometric fallback |
| **`mirror_k_geometry`** | `false` | absent | |
| **`segment_loop_extra`** | `1` | `+1` in loop | |
| **`crop_taper_mm`** | `1000` | inline taper | |
| **`use_original_label_distributions`** | `true` | hardcoded | |
| **`processing.y_bounds`** | `[4200, 13100]` | commented inline | |
| **Geometric SAM fallback** | **absent** | hardcoded behaviour | Not a JSON key |

---

## 4. Conclusions

- `t45_geometry.py` faithfully ports notebook cell 79 template coordinates.
- Promoted anchors are **not** literal notebook reproduction: they use
  **geometric SAM** and (for 5-1) **residual recentre** plus detection retune.
- `4-1/` matches notebook numerics closely; `5-1/` diverges only on recentre
  and Hough thresholds.
- Depth-map hole-fill exists in code but is **off** in promoted parameters;
  mIoU-gated experiments did not justify enabling it.

**See also:** `reports/t45-4-1-swap-ab.md`, `reports/t45-5-1-depth-improvement.md`
