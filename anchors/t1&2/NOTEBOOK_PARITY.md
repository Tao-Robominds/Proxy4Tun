# T1/T2 Notebook vs Anchor Parity Report

**Notebook:** `sam4tun/notebook/t1&2.ipynb`  
**Anchor:** `anchors/t1&2/` (`1_unfolding.py` … `6_evaluation.py`)  
**Parameter sets:** `parameters/` (HIGH default), `1-1/`, `2-1/`  
**Frozen runs (canonical):** `data/anchors/1-1/` (mIoU 0.787), `data/anchors/2-1/` (mIoU 0.874)  
**Parent index:** [`../NOTEBOOK_ANCHOR_PARITY.md`](../NOTEBOOK_ANCHOR_PARITY.md)

> Promoted cases use `canonical_orientation=true`. Legacy `swap_tunnel_centers`
> values in tables below are historical / ignored when canonical is on.

---

## 1. Implementation differences (untunable)

### 1.1 Orchestration and I/O

| Aspect | Notebook | Anchor |
|---|---|---|
| Input | In-kernel `loadtxt` / DataFrames | `PROXY4TUN_INPUT_TXT`, `ensure_dir(tunnel_id)` |
| Cross-stage data | Variables in notebook kernel | `state.pkl` (`df_point_cloud`, `depth_map*`, `pixel_to_point`, `df_loc`, …) |
| Artifacts | Sparse CSV/PNG; `results.pkl` | Per-stage CSVs, `depth_map.npy`, `evaluation/` |
| Parameters | Hardcoded per cell | `parameters_*.json` via `PROXY4TUN_PARAMS_DIR` |
| Evaluation | Ends at point-cloud projection | Dedicated `6_evaluation.py` (semantic IoU, mAP, plots) |

### 1.2 Stage 1 — Unfolding

| Change | Notebook | Anchor |
|---|---|---|
| Centre swap | No swap of short-edge centres | `swap_tunnel_centers` (bool) |
| Theta handedness | `cross(AB, BC).z` (legacy) | Optional `deterministic_theta_orientation` using travel tangent `T` |
| Residual recentre | Absent | Optional `residual_recentre` (per-h-bin ellipse fit on `r`) |

### 1.3 Stage 2 — Denoising

Algorithm unchanged (radial mask → grid → gradient cutoff → smooth → `pred=0`).
Anchor externalizes `default_cutoff_z` and removes debug per-slice prints.

### 1.4 Stage 3 — Enhancing

Same function graph (`enhance_segment_surface`, `enhance_outlier_points`,
`project_to_depth_map_inter`). Anchor saves `depth_map.npy` and sets colormap
limits from denoise `mask_r_low/high` instead of fixed `2.70/2.80`.

### 1.5 Stage 4 — Detection

**Material sign fix (T12 pattern):**

| Case | Notebook (Algorithm 4) | Anchor `4_detection.py` |
|---|---|---|
| `positive_slope` only | `y − 0.5·K_px` | `y + 0.5·K_px` |
| `negative_slope` only | `y + 0.5·K_px` | `y − 0.5·K_px` |

**Other detection additions:**

| Feature | Notebook | Anchor |
|---|---|---|
| Vertical-line fallback | None | Synthetic ring-centre verticals when Hough fails |
| T3 uniform K snap | N/A | Guard for `tunnel_id.startswith("3-")` in shared script |
| Assume fallback | Alternating 1123/1553 ladder | Same + `check_distance_pattern` |

### 1.6 Stage 5 — SAM

| Feature | Notebook | Anchor |
|---|---|---|
| `y_bounds` bolt filter | Hardcoded `[4200, 13100]` | JSON `processing.y_bounds` |
| `segment_order` / label map | Implicit `K…B2` dict | JSON `segment_order`, `use_original_label_distributions` |
| 7-segment reverse trigger | N/A | `segment_per_ring == 7` branch in shared `5_sam.py` |
| Geometric fallback | Absent | Not used for T1/T2 (6-class default) |
| Ring visualization | All ring pixels coloured | `assigned_mask` overlay |

---

## 2. Parameter differences (tunable)

Legend: **NB** = notebook literal; **P** = `parameters/`; **1-1** / **2-1** = per-case dirs.

### 2.1 Unfolding

| Parameter | NB | P | 1-1 | 2-1 |
|---|---:|---:|---:|---:|
| `diameter` | 5.5 | 5.5 | 5.5 | 5.5 |
| `polynomial_degree` | 3 | 3 | 3 | 3 |
| `slice_spacing_factor` | 1.2 | 1.2 | 1.2 | 1.2 |
| `swap_tunnel_centers` | — (no swap) | **true** | **true** | **false** |

### 2.2 Denoising — notebook vs JSON mismatch

| Parameter | NB | P / 1-1 | 2-1 |
|---|---:|---:|---:|
| `mask_r_low` / `mask_r_high` | **2.7 / 2.8** | 2.33 / 2.78 | 2.32 / 2.79 |
| `y_step` | 0.5 | 0.4 | **0.5** |
| `z_step` | 0.001 | 0.005 | **0.001** |
| `grad_threshold` | 0.2 | 0.15 | **0.2** |
| `smoothing_window_size` | **3** | 5 | **3** |
| `smoothing_offset` | −0.003 | −0.002 | **−0.003** |
| `default_cutoff_z` | 2.7 | 2.75 | **2.7** |

Notebook radial band does not match any anchor profile; **`2-1`** is closest on
grid/smoothing parameters.

### 2.3 Enhancing

| Parameter | NB | P / 1-1 | 2-1 |
|---|---:|---:|---:|
| `upsampling_stage{1,2,3}_target_distance` | **0.08 / 0.04 / 0.02** | 0.06 / 0.03 / 0.015 | same as P |
| `curvature_threshold` | 0.0005 | 0.005 | **0.0005** |
| `depth_threshold_low` / `high` | **0.003 / 0.008** | 0.005 / 0.015 | same |
| `inter_radius` | 0.06 | 0.03 | **0.06** |
| `n_segment_start` / `end` | 0 / 5 | 0 / 5 | 0 / 5 |

### 2.4 Detecting

| Parameter | NB | P / 1-1 | 2-1 |
|---|---:|---:|---:|
| `binary_threshold` | 127 | 125 | **127** |
| `hough_threshold_oblique` | 50 | 65 | **50** |
| `hough_threshold_vertical` | 500 | 600 | **500** |
| `maxLineGap_oblique` | 40 | 45 | **40** |
| Angle ranges | [6,9], [−9,−6] | same | same |

### 2.5 SAM

| Parameter | NB | P / 1-1 | 2-1 |
|---|---:|---:|---:|
| `segment_per_ring` | 6 | 6 | 6 |
| `K_height` / `AB_height` | 1079.92 / 3239.77 | same | same |
| `processing.y_bounds` | [4200, 13100] | [3800, 13300] | **[4200, 13100]** |

---

## 3. Anchor-only parameters (highlighted)

No named equivalent in the notebook:

| Parameter | Stage | Default (P) | Purpose |
|---|---|---|---|
| **`swap_tunnel_centers`** | unfolding | `true` | Swap tunnel axis endpoints before slicing |
| **`deterministic_theta_orientation`** | unfolding | off (code default) | Pin θ handedness to travel direction |
| **`residual_recentre`** | unfolding | off | Per-bin centreline radius correction |
| **`recentre_bin_size`** | unfolding | 0.5 | Recentre axial bin width (m) |
| **`recentre_r_tolerance`** | unfolding | 0.35 | Recentre fit radial tolerance (m) |
| **`recentre_min_bin_points`** | unfolding | 500 | Min points per recentre bin |
| **`segment_order`** | SAM | `["K","B1",…,"B2"]` | Explicit block naming |
| **`use_original_label_distributions`** | SAM | `true` | Use `segment_order` for `block_to_label` |
| **`processing.mask_eps`** | SAM | 0.001 | SAM mask logit epsilon |
| **`prompt_points`** | SAM | nested JSON | Documents prompt geometry (values still inline in code) |

---

## 4. Conclusions

- Anchor scripts preserve the T1/T2 algorithm chain with **parameterized I/O**
  and **evaluation**.
- The notebook is numerically closest to **`2-1`** for denoising, enhancing
  (curvature/inter_radius), detecting, and SAM `y_bounds`.
- The largest **implementation** delta is detection **oblique K-offset sign**
  (anchor corrects notebook T12 convention used in shared `4_detection.py`).
- **`1-1` vs `2-1`** differ mainly on `swap_tunnel_centers` and denoising grid
  values; both diverge from notebook on `mask_r` band and upsampling distances.
