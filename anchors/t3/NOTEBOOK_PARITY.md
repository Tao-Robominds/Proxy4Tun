# T3 Notebook vs Anchor Parity Report

**Notebook:** `sam4tun/notebook/t3.ipynb`  
**Anchor:** `anchors/t3/` + `t3_geometry.py`  
**Parameter set:** `3-1-1/` (CLI default for `--profile t3`)  
**Frozen run:** `data/anchors/3-1-1/` (mIoU 0.881)  
**Parent index:** [`../NOTEBOOK_ANCHOR_PARITY.md`](../NOTEBOOK_ANCHOR_PARITY.md)

---

## 1. Implementation differences (untunable)

### 1.1 Pipeline shell

Same as T1/T2: `state.pkl`, stage scripts, `6_evaluation.py`, JSON params,
`Agg` matplotlib, CLI `tunnel_id`.

### 1.2 Unfolding

| Change | Notebook | Anchor `3-1-1` |
|---|---|---|
| Centre swap | Always `center2,center1 = center1,center2` | `swap_tunnel_centers: true` (equivalent) |
| Theta orientation | Legacy `cross(AB,BC).z` | **`deterministic_theta_orientation: true`** |
| Residual recentre | **Absent** | **`residual_recentre: true`** — per-h-bin fit `r = r₀ + a·cos φ + b·sin φ` |

On short labelled subsets (e.g. `3-1-1`, 10 rings), recentre and deterministic
θ are required for in-band coverage; literal notebook execution fails badly
(mIoU ~0.12 vs ~0.88 corrected).

### 1.3 Denoising — theta gate column bug

Notebook (line ~3122):

```python
mask_theta = (df_point_cloud['theta'] < 1.55) | (df_point_cloud['r'] > 17.15)
```

Anchor (`parameters_denoising.json`):

```json
"mask_theta_high_column": "theta"
```

The notebook applies the upper bound to **`r`**, not **`theta`**. Anchor fixes
this with an explicit column selector.

### 1.4 Enhancing

| Change | Notebook | Anchor |
|---|---|---|
| Depth-map source | `df_point_cloud[pred == 7]` only | **`use_upsampled_surface: true`** — full upsampled cloud |
| Outlier interpolation | `interpolate_points` defined, **not called** | **`enable_outlier_interpolation: true`** |
| `n_segment` window | `[11, 11]` (50-ring station) | **`[2, 8]`** (10-ring subset) |
| OOM guard | None | Subsample outlier pairs to 2,800 |

### 1.5 Detection

| Change | Notebook | Anchor |
|---|---|---|
| Prompt assembly | Inline T3 inherit-Y only | `prompt_logic: t3_inherit` (+ shared `t12_pattern` branch) |
| K-offset signs (T3) | `+θ`: `y−0.5K`; `−θ`: `y+0.5K` | Same under `t3_inherit` |
| Y-drift guard | 10% inherit previous Y | Same |
| First-ring failure | `raise ValueError` | Image mid-Y + warning |
| **`uniform_k_snap`** | **Absent** | **Median K-Y over all rings** when enabled |

### 1.6 SAM — `t3_geometry.py`

| Change | Notebook | Anchor |
|---|---|---|
| Geometry | Inline cell ~77 arrays | `t3_geometry.py` (`template_vertices_mm`, `prompt_points_mm`) |
| K-block mirror | **Absent** | **`mirror_k_geometry: true`** — X-mirror about image centre |
| Profile selector | N/A | `geometry_profile: "t3"` |

Coordinates match notebook cell 77 (per module docstring).

---

## 2. Parameter differences (tunable)

### 2.1 Values matching notebook (promoted `3-1-1`)

Unfolding: `diameter=5.9`, `polynomial_degree=2`, RANSAC suite, `delta=0.005`, …  
Denoising: `mask_r` 2.85–3.0, `mask_theta` 1.55–17.15 (on **theta** in anchor), grid steps.  
Enhancing: upsample `0.08/0.04/0.02`, depths `0.01/0.01`, `inter_radius=0.06`.  
Detection: T3 Hough literals (30/40/30, vertical 1500, K/AB 823.8/3346.68).  
SAM: 6 segments, width 1200, angle 6.12°, `y_bounds` [4500, 14000].

### 2.2 Values diverging from notebook

| Parameter | Notebook | Anchor `3-1-1` | Effect |
|---|---|---|---|
| `n_segment_start` / `end` | `[11, 11]` | **`2` / `8`** | Subset ring window |
| `use_upsampled_surface` | false (pred==7) | **true** | Depth coverage |
| `enable_outlier_interpolation` | false | **true** | Joint contrast for Hough |
| `deterministic_theta_orientation` | — | **true** | Stable θ on short spans |
| `residual_recentre` | — | **true** | Radial band retention |
| `uniform_k_snap` | — | **true** | Stable K prompts |
| `mirror_k_geometry` | — | **true** | K template alignment |

---

## 3. Anchor-only parameters (highlighted)

| Parameter | In `3-1-1` JSON | Notebook |
|---|---|---|
| **`deterministic_theta_orientation`** | `true` | Absent |
| **`residual_recentre`** | `true` | Absent |
| **`recentre_bin_size`** | `0.5` | Absent |
| **`recentre_r_tolerance`** | `0.35` | Absent |
| **`recentre_min_bin_points`** | `500` | Absent |
| **`mask_theta_high_column`** | `"theta"` | Absent (uses `r` by mistake) |
| **`coverage_mode`** | `asymmetric_full` | Inline formula only |
| **`use_upsampled_surface`** | `true` | Opposite behaviour |
| **`enable_outlier_interpolation`** | `true` | Dead code |
| **`curvature_outlier_min`** | `0.01` | Inline filter only |
| **`ring_spacing_factor`** | `1.2` | Hardcoded `1.2` |
| **`prompt_logic`** | `t3_inherit` | Inline path only |
| **`uniform_k_snap`** | `true` | **Absent** |
| **`vertical_rho_mode`** | `band` | Inline band only |
| **`vertical_rho_min_factor`** / **`max_factor`** | `14.0` / `15.2` | Inline |
| **`geometry_profile`** | `t3` | Absent |
| **`mirror_k_geometry`** | `true` | **Absent** |
| **`segment_order`** | explicit list | Implicit |
| **`use_original_label_distributions`** | `true` | Hardcoded |
| **`processing.*`** | nested object | Values inline |
| **`swap_tunnel_centers`** | `true` | Always swapped (not parametric) |

---

## 4. Conclusions

- Core T3 algorithms in the anchor match the notebook for **full station-scale**
  tunnels when notebook literals are used.
- On **short labelled subsets**, five anchor additions are mandatory:
  theta-column fix, `residual_recentre`, `deterministic_theta_orientation`,
  `uniform_k_snap`, and `mirror_k_geometry`.
- `anchors/t3/3-1-1/` is the corrected-intent profile; literal notebook replay is
  not a valid baseline on `3-1-1`-scale data without manual fixes.

**See also:** `reports/t3-3-1-1-corrected-vs-literal.md`
