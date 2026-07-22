# T3 Continuous Family Proxy Underestimate — Technical Review

**Scope.** Why the v1 lean proxy (`bo-elegant/family/models.json`) systematically under-scores healthy continuous (tunnel-3) runs, despite strong mIoU.  
**Primary exhibits.** `data/anchors/3-1/` (mIoU 0.850); `data/bo-unified/3-6-family-proxy/runs/3-6-anchor/` (mIoU 0.836, proxy 0.384); `data/bo-unified/3-8-family-proxy/runs/3-8-anchor/` (mIoU 0.723, proxy 0.378).  
**Params.** Deployed continuous stack: `anchors/unified/params/3-1-1/`. Notebook reference: `sam4tun/notebook/t3.ipynb`.

---

## Executive finding

Deployed t3 detection runs with `uniform_k_snap=true`. After measuring real K-row anchors, stage 4 **rewrites every `Type` to `propagated`**. Intrinsics then read `det_real_detection_ratio=0.0` for every healthy continuous holdout, even when `k_row_gate.json` proves anchors existed (`n_anchor_ys=10` on 3-6, `6` on 3-8).

The frozen Ridge puts **+0.1355** on standardized `det_real_detection_ratio` (scaler mean 0.486). At `x=0`, contribution is **−0.181**. Counterfactual: setting `det_real=0.8` (staggered-like) lifts 3-6 proxy **0.384 → 0.682** (+0.298) without changing other features. That single confound explains most of the continuous-family MAE_anchor = **0.312** vs staggered 0.096 / complex 0.074 (`bo-elegant/report.md`).

**Action.** Drop `det_real_detection_ratio` for the lean candidate set (keep as diagnostic only). Add regime-neutral signals from `k_row_gate.json` + `phase_check.py`: `det_row_residual_px`, `det_row_y_std`, `phase_incoherence_deg`.

---

## Stage 1 — Centreline / unfolding

| Item | Notebook `t3.ipynb` | Deployed `parameters_unfolding.json` |
|---|---|---|
| Diameter / RANSAC / poly | Hard-coded `diameter=5.9`, RANSAC+polyfit in-notebook | Same geometry knobs; `diameter=5.9`, `polynomial_degree=2` |
| Residual recentre | **Absent** | **`residual_recentre=true`** |
| Orientation | Manual / legacy | `canonical_orientation=true`, `h_ring_sign=-1` |

**Recentre residuals (logs).**

| Run | Residual recentre | `recentre_residual_max_cm` |
|---|---|---|
| 3-6-anchor | 24/24 bins, max=**3.2 cm**, median=1.7 cm | 3.2 |
| 3-8-anchor | 25/25 bins, max=**24.0 cm**, median=3.8 cm | 24.0 |

3-8’s larger residual co-moves with worse depth/SAM (`depth_nan_ratio=0.182`, `sam_fill_rate=0.597`) vs 3-6 (`0.105`, `0.649`), but both remain high-mIoU. Centreline quality is a tier-0 signal; not in the lean proxy.

**`n_segment`** is an enhancing parameter. Deployed: `n_segment_start/end = 2/8`. For ~10-ring subsets both notebook and pipeline windows cover nearly the full station — not the proxy bug.

---

## Stages 2–3 — Denoise / enhance / joint contrast

Denoising / enhancing match notebook intent (`mask_r [2.85, 3.0]`, `depth_threshold_*=0.01`). Continuous lining joints are weaker / more oblique-dominated than staggered. Hough thresholds match the notebook; stage 4 **does** land anchors (`k_row_gate.n_anchor_ys`), then erases Type provenance. Joint contrast is a **secondary** story; the proxy reads “no real detections” for an instrumentation reason.

---

## Stage 4 — Detection: `uniform_k_snap` vs unmeasured fallback

**Deployed** (`anchors/unified/params/3-1-1/parameters_detecting.json`):
`uniform_k_snap=true`, `k_row_pattern=[1123, 1553]`, `k_row_tolerance=200`, `k_row_action=snap`, `prompt_logic=t3_inherit`.

**Logic** (`anchors/unified/4_detection.py`):
1. Per-ring: midpoint / ±slope / horizontal / else `assume`.
2. If `uniform_k_snap` and real anchors exist: `y_star = median(anchor_Y)` → gate vs design row → rewrite all points to `("propagated", (x, y_star_used))`.
3. Persist `k_row_gate.json` with the pre-rewrite evidence.

**Artifact truth table.**

| Artifact | 3-6-anchor | 3-8-anchor |
|---|---|---|
| `initial_points.csv` Types | 10× `propagated` | 10× `propagated` |
| `distance_px` | **5.58** | **9.25** |
| `action_taken` | **accept** | **accept** |
| `n_anchor_ys` | **10** | **6** |
| `anchor_y_std` | **1.62** | **5.16** |
| `det_real_detection_ratio` | **0.0** | **0.0** |

| Regime | Pre-snap Types | Post-snap CSV | `det_real` | True quality signal |
|---|---|---|---|---|
| Verified snap (healthy t3) | real anchors present | all `propagated` | 0 | `distance_px`, `anchor_y_std` |
| Unmeasured fallback | all `assume` | all `assume` | 0 | no gate / design-row lottery |
| Staggered healthy | real Types preserved | real Types | ~0.7–0.9 | Type ratio itself |

Healthy continuous runs are forced into the same feature value as pure fallback — the **regime confound**.

---

## Stage 5 — SAM / fill-rate

`sam_fill_rate` for continuous holdout anchors spans **0.538–0.780**. Once `det_real` is stuck at 0, the proxy almost tracks fill alone. Fill remains useful; it cannot recover the −0.18 `det_real` penalty.

| Run | mIoU | fill | ontology |
|---|---:|---:|---:|
| 3-6 | 0.836 | 0.649 | 0.201 |
| 3-8 | 0.723 | 0.597 | 0.199 |

---

## Proxy docking story (v1)

Continuous holdout: every continuous **anchor** has `det_real_detection_ratio=0.0`. Worst: 3-6 abs_err **0.452**, 3-8 **0.345**. Family MAE_anchor = 0.312; 4 false alarms (3-4, 3-5, 3-6, 3-8).

Training table still has some 3-1 trials with `det_real∈{0.7,0.8}` (non-snap configs). Holdout deployed anchors never do → train/serve skew.

---

## `phase_check.py` applicability to t3

`APPLICABLE_FAMILIES = {"t1&2", "t3"}`. Measured: 3-1 = 1.2°, 3-6 = 0.8°, 3-8 = 2.5° — all healthy. Correctly marks good runs as phase-coherent; complementary to K-row gate residuals.

---

## Recommended feature surgery

| Change | Rationale |
|---|---|
| **Drop `det_real_detection_ratio`** from lean candidate | Regime-constant 0 under snap; −0.18 systematic bias |
| **Add `det_row_residual_px`** | `k_row_gate.distance_px` or design-pattern residual (all families) |
| **Add `det_row_y_std`** | Pre-snap anchor scatter / prompt Y std |
| **Add `phase_incoherence_deg`** | From `phase_check.py`; applicable t1&2/t3 |

Prefer reading `k_row_gate.json` when present; fall back to design-pattern residual from `initial_points.csv` + detecting params for non-t3.
