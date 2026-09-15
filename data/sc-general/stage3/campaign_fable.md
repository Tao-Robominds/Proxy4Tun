# SC-general Stage-3 Fable-5 refinement campaign

GT-blind-by-protocol reflective loop. Proxy = pruned_lean SC-general.
Proposer = Fable-5 (Cursor agent, live).
Panel Phase A = dual band proxy∩GT ∈ [0.5, 0.7]: 1-4, 1-5, 2-2, 3-4, 4-1, 4-3.
Selection = monotone accept on scaled proxy; GT revealed offline only.

Caveat: proposer does not read offline_gt / performance.md / band CSVs during
the loop, but has seen aggregate GT for these cases earlier in the session.

---

## 3-4 (t3) — Gate + Phase A

### Anchor (GT-blind)
- proxy_scaled 0.520 / band refine
- F1@15=0.244 fill=0.571 nan=0.195 residual=20.8 cm (unlocked)
- det real=0.0 fallback=1.0

### Round 1 CoT
- Observation: residual 20.8 cm + total Hough fallback; F1 cannot rise without real joints and a better centreline.
- Rule: unlock unfolding seed; couple with moderate Hough recovery + slight mask widen.
- Failure mode: f_centreline_residual + f_detection_fallback.
- Overlay: unfolding.random_seed=5; denoising mask_r [2.80,3.08] theta [1.3,17.5]; enhancing curv 0.0008; detecting binary 115, Hough 25/25/1800, gap 45, tol 14, uniform_k_snap; sam width 1250, K_height 900, angle 6.5. --full.

### Round 1 result
| Round | Proxy | Band | Residual | F1@15 | Note |
|---|---:|---|---:|---:|---|
| anchor | 0.520 | refine | 20.8 | 0.244 | |
| R1 | 0.401 | reject | 23.2 | 0.032 | seed 5 + Hough; residual worse, F1 collapsed |

### Round 2 result
| Round | Proxy | Band | Residual | F1@15 | Note |
|---|---:|---|---:|---:|---|
| R2 | 0.496 | reject | 22.8 | 0.209 | seed 0 alone; still below anchor |

### Round 3 result
| Round | Proxy | Band | Residual | F1@15 | Note |
|---|---:|---|---:|---:|---|
| R3 | 0.370 | reject | 20.8 | 0.000 | 2–6 detection widen; F1 collapsed |

### Selection
- monotone accept → **anchor** (no round beat 0.520)
- delta_proxy 0.0; offline ΔmIoU 0.0

---
## 1-5 (t1&2)

### Anchor (GT-blind)
- proxy 0.555 / refine; F1=0.201 fill=0.729 nan=0.118 residual=2.5 (locked)
- real=0.8 fallback=0.2; size_cv=1.30 ont_div=0.193
- Detection strong — bottleneck is SAM crop / template irregularity, not Hough collapse.

### Round 1 CoT
- Observation: low F1 with healthy detection → line↔boundary mismatch from SAM y-crop / segment sizing; high size_cv.
- Rule: raise y_bounds lower toward K band; tighten spurious obliques; widen inter_radius + mild mask/curv retune.
- Failure mode: f_template_mismatch / K-row crop.
- Overlay: mask_r [2.40,2.85] z_step 0.003 grad 0.18; curv 0.006 inter 0.055; Hough 75/75/700 gap 35; y_bounds [4200,13300].

### Round 1 result
| Round | Proxy | Band | F1@15 | Note |
|---|---:|---|---:|---|
| anchor | 0.555 | refine | 0.201 | |
| R1 | **0.634** | refine | 0.341 | y_bounds+Hough; clear proxy↑ |

### Round 2 CoT
- Observation: R1 unlocked F1 (+0.14). Push further toward K band (higher y_bounds lower) and slightly stronger vertical Hough; mild mask widen.
- Failure mode: residual K-crop / size irregularity.
- Overlay: mask [2.30,2.80] z 0.004 grad 0.16; curv 0.005 inter 0.06; Hough 80/80/750 gap 40; y_bounds [4300,13300].

### Round 2 result
| Round | Proxy | Band | F1@15 | Note |
|---|---:|---|---:|---|
| R2 | **0.646** | refine | 0.361 | further y_bounds; best so far |

### Round 3 CoT
- Observation: R2 best. Probe denser lining (lower z_step) + slightly lower y_bounds again vs over-crop; keep strong Hough.
- Failure mode: depth/lining density vs crop tradeoff.
- Overlay: mask [2.35,2.82] z 0.002 grad 0.20; curv 0.004 inter 0.05; Hough 70/70/650 gap 30; y_bounds [4100,13300].

### Round 3 result
| Round | Proxy | Band | F1@15 | Note |
|---|---:|---|---:|---|
| R3 | **0.684** | refine | 0.434 | denser z_step; best proxy |

### Selection
- monotone accept → **round3** (proxy 0.684, Δproxy +0.129)

---

## 1-4 (t1&2)

### Anchor (GT-blind)
- proxy 0.646 / refine; F1=0.395 fill=0.699 nan=0.150 residual=1.9 (locked)
- real=0.7 fallback=0.3; size_cv=1.55 ont_div=0.275 — high size irregularity / template fit.

### Round 1 CoT
- Observation: same family as 1-5; high size_cv/ontology_div. Start from the 1-5 R3-style recipe that unlocked F1.
- Failure mode: f_template_mismatch / size irregularity.
- Overlay: mask [2.35,2.82] z 0.002 grad 0.20; curv 0.004 inter 0.05; Hough 70/70/650 gap 30; y_bounds [4100,13300].

### Round 1 result
| Round | Proxy | Band | F1@15 | Note |
|---|---:|---|---:|---|
| anchor | 0.646 | refine | 0.395 | |
| R1 | **0.720** | accept | 0.506 | crossed accept |

### Round 2 CoT
- Observation: R1 crossed accept. Probe stronger y_bounds (4300) + Hough like 1-5 R2.
- Overlay: mask [2.30,2.80] z 0.004 grad 0.16; curv 0.005 inter 0.06; Hough 80/80/750 gap 40; y_bounds [4300,13300].

### Round 3 CoT
- Observation: alternate milder Hough / wider gap + mid y_bounds (legacy 1-4 R2-ish depth high).
- Overlay: mask [2.40,2.85] z 0.003 grad 0.18; curv 0.006 inter 0.055; Hough 75/75/700 gap 35; y_bounds [4200,13300]; also raise depth via slightly higher grad.

### Round 2/3 results + selection
- R2 proxy **0.722** (best); R3 0.714
- selected **round2** Δproxy +0.076

---

## 2-2 (t1&2)

### Anchor (GT-blind)
- proxy 0.699 / refine (near accept); F1=0.455 fill=0.743 nan=0.111 residual=1.5 locked
- real=0.9 fallback=0.1; size_cv=1.15 ont_div=0.165 — already strong.

### Round 1 CoT
- Observation: near-accept; gentle nudge — slight y_bounds raise + mild Hough tighten to lift F1 without disrupting healthy detection.
- Failure mode: residual template / size irregularity at the accept edge.
- Overlay: mask [2.35,2.82] z 0.002 grad 0.18; curv 0.003 inter 0.055; Hough 60/60/600 gap 35; y_bounds [4300,13100].

### 2-2 results
| Round | Proxy | Band | F1 | Note |
|---|---:|---|---:|---|
| anchor | 0.699 | refine | 0.455 | |
| R1 | 0.741 | accept | 0.529 | gentle nudge |
| R2 | **0.757** | accept | 0.558 | 1-5-style |
| R3 | 0.739 | accept | 0.530 | denser z |
Selected **round2** Δproxy +0.058

---

## 4-1 (t4&5)

### Anchor (GT-blind)
- proxy 0.552 / refine; F1=0.225 fill=0.749 nan=0.223 residual=2.4 locked
- real=0.4 fallback=0.6 — detection sparse; complex irregular K.

### Round 1 CoT
- Observation: fallback 0.6 dominates; need wider mask + hard vertical Hough + looser gaps + live SAM sizes (4-4 cursor2 recipe family).
- Failure mode: f_detection_sparse / complex layout mismatch.
- Overlay: mask [3.55,3.95]; curv 0.001; Hough obl 40 / horiz 30 / vert 3500; gaps 70/20; tol 12; SAM K_height 1150 width 1700 angle 9.5.

### 4-1 results
| Round | Proxy | Band | F1 | Note |
|---|---:|---|---:|---|
| anchor | 0.552 | refine | 0.225 | |
| R1 | **0.621** | refine | 0.347 | cursor2-style |
| R2 | 0.599 | refine | 0.309 | milder |
| R3 | 0.498 | reject | 0.117 | too aggressive |
Selected **round1** Δproxy +0.069

---

## 4-3 (t4&5)

### Anchor (GT-blind)
- proxy 0.520 / refine; F1=0.191 fill=0.717 nan=0.245 residual=**23.2** unlocked
- real=0.6 fallback=0.4; seed currently 0.

### Round 1 CoT
- Observation: residual 23.2 cm is the binding defect; probe seed 1 alone (full 1–6) before retuning 2–6.
- Failure mode: f_centreline_residual.
- Overlay: unfolding.random_seed=1. --full.

### 4-3 results
| Round | Proxy | Band | Residual | F1 | Note |
|---|---:|---|---:|---:|---|
| anchor | 0.520 | refine | 23.2 | 0.191 | seed 0 |
| R1 | 0.571 | refine | **5.2** | 0.278 | seed 1 |
| R2 | **0.573** | refine | 5.2 | 0.277 | seed1 + 2–6 |
| R3 | 0.542 | refine | 9.7 | 0.223 | seed 5 |
Selected **round2** Δproxy +0.052 (residual tiebreak vs R1 within margin)

---

## Phase A summary (dual band, 6 cases)

| subset | selected | a_proxy | s_proxy | Δproxy | ΔmIoU (offline) |
|---|---|---:|---:|---:|---:|
| 1-4 | round2 | 0.646 | 0.722 | +0.076 | (see selection) |
| 1-5 | round3 | 0.555 | 0.684 | +0.129 | |
| 2-2 | round2 | 0.699 | 0.757 | +0.058 | |
| 3-4 | anchor | 0.520 | 0.520 | 0.000 | |
| 4-1 | round1 | 0.552 | 0.621 | +0.069 | |
| 4-3 | round2 | 0.520 | 0.573 | +0.052 | |

5/6 cases refined by monotone-accept proxy; 3-4 stayed at anchor.


---

# Phase B start 2026-09-13T12:25:20.632587
Cases: 1-1, 1-2, 1-3, 2-4, 3-10, 3-3, 3-6, 3-7, 3-8, 3-9, 4-2, 4-5, 5-2, 5-3, 5-4, 5-5

## 1-1 (t1&2) — Phase B

### Anchor (GT-blind)
- proxy 0.607 / refine; F1=0.294 fill=0.723 nan=0.107 residual=2.8 unlocked=False

### Round 1 CoT
- Observation: F1=0.294 fill=0.723; detection mostly real. Low/mid F1 with healthy fill → SAM crop / template irregularity.
- Failure mode: f_template_mismatch / K-row crop
- Rationale: 1-5 R3-style: denser z_step + mid Hough + y_bounds 4100.
- Overlay: `{"denoising":{"mask_r_low":2.35,"mask_r_high":2.82,"z_step":0.002,"grad_threshold":0.2},"enhancing":{"curvature_threshold":0.004,"inter_radius":0.05},"detecting":{"binary_threshold":125,"hough_threshold_oblique":70,"hough_threshold_horizontal":70,"hough_threshold_vertical":650,"maxLineGap_oblique":30},"sam":{"processing.y_bounds":[4100,13300]}}`
- full=False
### Round 1 result
- status=ok proxy=0.6294032201237094 band=refine residual=2.8 elapsed=284.1s

### Round 2 CoT
- Observation: After R1 history; push stronger y_bounds/Hough. F1 was 0.294.
- Failure mode: residual K-crop / size irregularity
- Rationale: 1-5 R2-style: y_bounds 4300 + stronger Hough.
- Overlay: `{"denoising":{"mask_r_low":2.3,"mask_r_high":2.8,"z_step":0.004,"grad_threshold":0.16},"enhancing":{"curvature_threshold":0.005,"inter_radius":0.06},"detecting":{"binary_threshold":115,"hough_threshold_oblique":80,"hough_threshold_horizontal":80,"hough_threshold_vertical":750,"maxLineGap_oblique":40},"sam":{"processing.y_bounds":[4300,13300]}}`
- full=False
### Round 2 result
- status=ok proxy=0.6179136505074105 band=refine residual=2.8 elapsed=284.7s

### Round 3 CoT
- Observation: Alternate milder mid recipe; F1=0.294.
- Failure mode: depth/lining density vs crop tradeoff
- Rationale: 1-5 R1-style mid recipe for diversity.
- Overlay: `{"denoising":{"mask_r_low":2.4,"mask_r_high":2.85,"z_step":0.003,"grad_threshold":0.18},"enhancing":{"curvature_threshold":0.006,"inter_radius":0.055},"detecting":{"binary_threshold":120,"hough_threshold_oblique":75,"hough_threshold_horizontal":75,"hough_threshold_vertical":700,"maxLineGap_oblique":35},"sam":{"processing.y_bounds":[4200,13300]}}`
- full=False
### Round 3 result
- status=ok proxy=0.6277551583766743 band=refine residual=2.8 elapsed=299.3s

### Selection
- selected **round1** Δproxy=+0.023 ΔmIoU=0.003
- reason: best proxy 0.6294; 2 within 0.01 margin; residual tiebreak -> round1

## 1-2 (t1&2) — Phase B

### Anchor (GT-blind)
- proxy 0.648 / refine; F1=0.368 fill=0.723 nan=0.102 residual=3.5 unlocked=False

### Round 1 CoT
- Observation: F1=0.368 fill=0.723; detection mostly real. Low/mid F1 with healthy fill → SAM crop / template irregularity.
- Failure mode: f_template_mismatch / K-row crop
- Rationale: 1-5 R3-style: denser z_step + mid Hough + y_bounds 4100.
- Overlay: `{"denoising":{"mask_r_low":2.35,"mask_r_high":2.82,"z_step":0.002,"grad_threshold":0.2},"enhancing":{"curvature_threshold":0.004,"inter_radius":0.05},"detecting":{"binary_threshold":125,"hough_threshold_oblique":70,"hough_threshold_horizontal":70,"hough_threshold_vertical":650,"maxLineGap_oblique":30},"sam":{"processing.y_bounds":[4100,13300]}}`
- full=False
### Round 1 result
- status=ok proxy=0.7100032268534022 band=accept residual=3.5 elapsed=291.9s

### Round 2 CoT
- Observation: After R1 history; push stronger y_bounds/Hough. F1 was 0.368.
- Failure mode: residual K-crop / size irregularity
- Rationale: 1-5 R2-style: y_bounds 4300 + stronger Hough.
- Overlay: `{"denoising":{"mask_r_low":2.3,"mask_r_high":2.8,"z_step":0.004,"grad_threshold":0.16},"enhancing":{"curvature_threshold":0.005,"inter_radius":0.06},"detecting":{"binary_threshold":115,"hough_threshold_oblique":80,"hough_threshold_horizontal":80,"hough_threshold_vertical":750,"maxLineGap_oblique":40},"sam":{"processing.y_bounds":[4300,13300]}}`
- full=False
### Round 2 result
- status=ok proxy=0.7137436726919641 band=accept residual=3.5 elapsed=284.9s

### Round 3 CoT
- Observation: Alternate milder mid recipe; F1=0.368.
- Failure mode: depth/lining density vs crop tradeoff
- Rationale: 1-5 R1-style mid recipe for diversity.
- Overlay: `{"denoising":{"mask_r_low":2.4,"mask_r_high":2.85,"z_step":0.003,"grad_threshold":0.18},"enhancing":{"curvature_threshold":0.006,"inter_radius":0.055},"detecting":{"binary_threshold":120,"hough_threshold_oblique":75,"hough_threshold_horizontal":75,"hough_threshold_vertical":700,"maxLineGap_oblique":35},"sam":{"processing.y_bounds":[4200,13300]}}`
- full=False
### Round 3 result
- status=ok proxy=0.700970009236072 band=accept residual=3.5 elapsed=288.6s

### Selection
- selected **round2** Δproxy=+0.066 ΔmIoU=-0.002
- reason: best proxy 0.7137; 2 within 0.01 margin; residual tiebreak -> round2

## 1-3 (t1&2) — Phase B

### Anchor (GT-blind)
- proxy 0.550 / refine; F1=0.187 fill=0.733 nan=0.109 residual=1.4 unlocked=False

### Round 1 CoT
- Observation: F1=0.187 fill=0.733; detection mostly real. Low/mid F1 with healthy fill → SAM crop / template irregularity.
- Failure mode: f_template_mismatch / K-row crop
- Rationale: 1-5 R3-style: denser z_step + mid Hough + y_bounds 4100.
- Overlay: `{"denoising":{"mask_r_low":2.35,"mask_r_high":2.82,"z_step":0.002,"grad_threshold":0.2},"enhancing":{"curvature_threshold":0.004,"inter_radius":0.05},"detecting":{"binary_threshold":125,"hough_threshold_oblique":70,"hough_threshold_horizontal":70,"hough_threshold_vertical":650,"maxLineGap_oblique":30},"sam":{"processing.y_bounds":[4100,13300]}}`
- full=False
### Round 1 result
- status=ok proxy=0.6564294745102695 band=refine residual=1.4 elapsed=280.9s

### Round 2 CoT
- Observation: After R1 history; push stronger y_bounds/Hough. F1 was 0.187.
- Failure mode: residual K-crop / size irregularity
- Rationale: 1-5 R2-style: y_bounds 4300 + stronger Hough.
- Overlay: `{"denoising":{"mask_r_low":2.3,"mask_r_high":2.8,"z_step":0.004,"grad_threshold":0.16},"enhancing":{"curvature_threshold":0.005,"inter_radius":0.06},"detecting":{"binary_threshold":115,"hough_threshold_oblique":80,"hough_threshold_horizontal":80,"hough_threshold_vertical":750,"maxLineGap_oblique":40},"sam":{"processing.y_bounds":[4300,13300]}}`
- full=False
### Round 2 result
- status=ok proxy=0.652348695400416 band=refine residual=1.4 elapsed=277.2s

### Round 3 CoT
- Observation: Alternate milder mid recipe; F1=0.187.
- Failure mode: depth/lining density vs crop tradeoff
- Rationale: 1-5 R1-style mid recipe for diversity.
- Overlay: `{"denoising":{"mask_r_low":2.4,"mask_r_high":2.85,"z_step":0.003,"grad_threshold":0.18},"enhancing":{"curvature_threshold":0.006,"inter_radius":0.055},"detecting":{"binary_threshold":120,"hough_threshold_oblique":75,"hough_threshold_horizontal":75,"hough_threshold_vertical":700,"maxLineGap_oblique":35},"sam":{"processing.y_bounds":[4200,13300]}}`
- full=False
### Round 3 result
- status=ok proxy=0.6797866612722561 band=refine residual=1.4 elapsed=292.5s

### Selection
- selected **round3** Δproxy=+0.130 ΔmIoU=0.046
- reason: best proxy 0.6798; 1 within 0.01 margin; residual tiebreak -> round3

## 2-4 (t1&2) — Phase B

### Anchor (GT-blind)
- proxy 0.676 / refine; F1=0.412 fill=0.745 nan=0.109 residual=1.7 unlocked=False

### Round 1 CoT
- Observation: F1=0.412 fill=0.745; detection mostly real. Low/mid F1 with healthy fill → SAM crop / template irregularity.
- Failure mode: f_template_mismatch / K-row crop
- Rationale: 1-5 R3-style: denser z_step + mid Hough + y_bounds 4100.
- Overlay: `{"denoising":{"mask_r_low":2.35,"mask_r_high":2.82,"z_step":0.002,"grad_threshold":0.2},"enhancing":{"curvature_threshold":0.004,"inter_radius":0.05},"detecting":{"binary_threshold":125,"hough_threshold_oblique":70,"hough_threshold_horizontal":70,"hough_threshold_vertical":650,"maxLineGap_oblique":30},"sam":{"processing.y_bounds":[4100,13300]}}`
- full=False
### Round 1 result
- status=ok proxy=0.7082873398180248 band=accept residual=1.7 elapsed=297.5s

### Round 2 CoT
- Observation: After R1 history; push stronger y_bounds/Hough. F1 was 0.412.
- Failure mode: residual K-crop / size irregularity
- Rationale: 1-5 R2-style: y_bounds 4300 + stronger Hough.
- Overlay: `{"denoising":{"mask_r_low":2.3,"mask_r_high":2.8,"z_step":0.004,"grad_threshold":0.16},"enhancing":{"curvature_threshold":0.005,"inter_radius":0.06},"detecting":{"binary_threshold":115,"hough_threshold_oblique":80,"hough_threshold_horizontal":80,"hough_threshold_vertical":750,"maxLineGap_oblique":40},"sam":{"processing.y_bounds":[4300,13300]}}`
- full=False
### Round 2 result
- status=ok proxy=0.6766986450822549 band=refine residual=1.7 elapsed=288.9s

### Round 3 CoT
- Observation: Alternate milder mid recipe; F1=0.412.
- Failure mode: depth/lining density vs crop tradeoff
- Rationale: 1-5 R1-style mid recipe for diversity.
- Overlay: `{"denoising":{"mask_r_low":2.4,"mask_r_high":2.85,"z_step":0.003,"grad_threshold":0.18},"enhancing":{"curvature_threshold":0.006,"inter_radius":0.055},"detecting":{"binary_threshold":120,"hough_threshold_oblique":75,"hough_threshold_horizontal":75,"hough_threshold_vertical":700,"maxLineGap_oblique":35},"sam":{"processing.y_bounds":[4200,13300]}}`
- full=False
### Round 3 result
- status=ok proxy=0.7089366669076484 band=accept residual=1.7 elapsed=302.2s

### Selection
- selected **round3** Δproxy=+0.033 ΔmIoU=-0.019
- reason: best proxy 0.7089; 2 within 0.01 margin; residual tiebreak -> round3

## 3-10 (t3) — Phase B

### Anchor (GT-blind)
- proxy 0.589 / refine; F1=0.287 fill=0.698 nan=0.142 residual=10.2 unlocked=True

### Round 1 CoT
- Observation: Residual 10.2 cm unlocked; fallback=1.00 F1=0.287. Centreline first.
- Failure mode: f_centreline_residual (+ detection fallback)
- Rationale: Probe seed 5 alone (full 1–6).
- Overlay: `{"unfolding":{"random_seed":5}}`
- full=True
### Round 1 result
- status=ok proxy=0.5741108562196884 band=refine residual=6.8 elapsed=203.0s

### Round 2 CoT
- Observation: Combine seed 1 with detection recovery; F1=0.287.
- Failure mode: f_centreline_residual + f_detection_fallback
- Rationale: Seed 1 + moderate Hough recovery + slight mask widen.
- Overlay: `{"unfolding":{"random_seed":1},"denoising":{"mask_r_low":2.8,"mask_r_high":3.08,"mask_theta_low":1.3,"mask_theta_high":17.5},"enhancing":{"curvature_threshold":0.0008},"detecting":{"binary_threshold":115,"hough_threshold_oblique":25,"hough_threshold_horizontal":25,"hough_threshold_vertical":1800,"maxLineGap_oblique":45,"pattern_tolerance":14,"uniform_k_snap":true},"sam":{"segment_width":1250,"K_height":900,"angle":6.5}}`
- full=True
### Round 2 result
- status=ok proxy=0.5786138808911578 band=refine residual=10.2 elapsed=199.9s

### Round 3 CoT
- Observation: Alternate seed 5; F1=0.287.
- Failure mode: f_centreline_residual
- Rationale: Seed 5 alone for centreline diversity.
- Overlay: `{"unfolding":{"random_seed":5}}`
- full=True
### Round 3 result
- status=ok proxy=0.5741108562196884 band=refine residual=6.8 elapsed=199.3s

### Selection
- selected **anchor** Δproxy=+0.000 ΔmIoU=0.0
- reason: monotone accept: no round beat anchor scaled proxy

## 3-3 (t3) — Phase B

### Anchor (GT-blind)
- proxy 0.522 / refine; F1=0.113 fill=0.780 nan=0.114 residual=2.7 unlocked=False

### Round 1 CoT
- Observation: F1=0.113 fill=0.780 fallback=1.00. Uniform-K continuous; correspondence weak when Hough falls back.
- Failure mode: f_detection_fallback / low line↔boundary F1
- Rationale: Moderate Hough recovery + slight mask widen; keep uniform_k_snap.
- Overlay: `{"denoising":{"mask_r_low":2.85,"mask_r_high":3.05,"mask_theta_low":1.5,"mask_theta_high":17.0},"enhancing":{"curvature_threshold":0.0008},"detecting":{"binary_threshold":120,"hough_threshold_oblique":35,"hough_threshold_horizontal":35,"hough_threshold_vertical":1600,"maxLineGap_oblique":40,"pattern_tolerance":12,"uniform_k_snap":true},"sam":{"segment_width":1200,"K_height":900,"angle":6.0}}`
- full=False
### Round 1 result
- status=ok proxy=0.500869921161066 band=refine residual=2.7 elapsed=199.8s

### Round 2 CoT
- Observation: Widen retention + lower binary; F1=0.113.
- Failure mode: f_depth_incomplete or weak edges
- Rationale: Wider mask + lower binary + looser Hough to catch more joints.
- Overlay: `{"denoising":{"mask_r_low":2.75,"mask_r_high":3.12,"mask_theta_low":1.2,"mask_theta_high":18.0},"enhancing":{"curvature_threshold":0.0012},"detecting":{"binary_threshold":105,"hough_threshold_oblique":28,"hough_threshold_horizontal":28,"hough_threshold_vertical":2000,"maxLineGap_oblique":55,"pattern_tolerance":15,"uniform_k_snap":true},"sam":{"segment_width":1150,"K_height":850,"angle":7.0}}`
- full=False
### Round 2 result
- status=ok proxy=0.5116162868378004 band=refine residual=2.7 elapsed=201.7s

### Round 3 CoT
- Observation: Alternate cleaner edges / larger SAM; F1=0.113.
- Failure mode: f_sam_crop_mismatch
- Rationale: Higher binary + larger SAM window.
- Overlay: `{"denoising":{"mask_r_low":2.9,"mask_r_high":3.1,"mask_theta_low":1.8,"mask_theta_high":16.5},"enhancing":{"curvature_threshold":0.0005},"detecting":{"binary_threshold":140,"hough_threshold_oblique":45,"hough_threshold_horizontal":40,"hough_threshold_vertical":1800,"maxLineGap_oblique":30,"pattern_tolerance":10,"uniform_k_snap":true},"sam":{"segment_width":1300,"K_height":950,"angle":5.0}}`
- full=False
### Round 3 result
- status=ok proxy=0.46969481867477103 band=reject residual=2.7 elapsed=175.6s

### Selection
- selected **anchor** Δproxy=+0.000 ΔmIoU=0.0
- reason: monotone accept: no round beat anchor scaled proxy

## 3-6 (t3) — Phase B

### Anchor (GT-blind)
- proxy 0.681 / refine; F1=0.467 fill=0.649 nan=0.105 residual=3.2 unlocked=False

### Round 1 CoT
- Observation: F1=0.467 fill=0.649 fallback=1.00. Uniform-K continuous; correspondence weak when Hough falls back.
- Failure mode: f_detection_fallback / low line↔boundary F1
- Rationale: Moderate Hough recovery + slight mask widen; keep uniform_k_snap.
- Overlay: `{"denoising":{"mask_r_low":2.85,"mask_r_high":3.05,"mask_theta_low":1.5,"mask_theta_high":17.0},"enhancing":{"curvature_threshold":0.0008},"detecting":{"binary_threshold":120,"hough_threshold_oblique":35,"hough_threshold_horizontal":35,"hough_threshold_vertical":1600,"maxLineGap_oblique":40,"pattern_tolerance":12,"uniform_k_snap":true},"sam":{"segment_width":1200,"K_height":900,"angle":6.0}}`
- full=False
### Round 1 result
- status=ok proxy=0.6636754611673852 band=refine residual=3.2 elapsed=193.2s

### Round 2 CoT
- Observation: Widen retention + lower binary; F1=0.467.
- Failure mode: f_depth_incomplete or weak edges
- Rationale: Wider mask + lower binary + looser Hough to catch more joints.
- Overlay: `{"denoising":{"mask_r_low":2.75,"mask_r_high":3.12,"mask_theta_low":1.2,"mask_theta_high":18.0},"enhancing":{"curvature_threshold":0.0012},"detecting":{"binary_threshold":105,"hough_threshold_oblique":28,"hough_threshold_horizontal":28,"hough_threshold_vertical":2000,"maxLineGap_oblique":55,"pattern_tolerance":15,"uniform_k_snap":true},"sam":{"segment_width":1150,"K_height":850,"angle":7.0}}`
- full=False
### Round 2 result
- status=ok proxy=0.7254487120491958 band=accept residual=3.2 elapsed=200.6s

### Round 3 CoT
- Observation: Alternate cleaner edges / larger SAM; F1=0.467.
- Failure mode: f_sam_crop_mismatch
- Rationale: Higher binary + larger SAM window.
- Overlay: `{"denoising":{"mask_r_low":2.9,"mask_r_high":3.1,"mask_theta_low":1.8,"mask_theta_high":16.5},"enhancing":{"curvature_threshold":0.0005},"detecting":{"binary_threshold":140,"hough_threshold_oblique":45,"hough_threshold_horizontal":40,"hough_threshold_vertical":1800,"maxLineGap_oblique":30,"pattern_tolerance":10,"uniform_k_snap":true},"sam":{"segment_width":1300,"K_height":950,"angle":5.0}}`
- full=False
### Round 3 result
- status=ok proxy=0.5779209272451818 band=refine residual=3.2 elapsed=174.4s

### Selection
- selected **round2** Δproxy=+0.044 ΔmIoU=-0.001
- reason: best proxy 0.7254; 1 within 0.01 margin; residual tiebreak -> round2

## 3-7 (t3) — Phase B

### Anchor (GT-blind)
- proxy 0.540 / refine; F1=0.172 fill=0.767 nan=0.165 residual=3.6 unlocked=False

### Round 1 CoT
- Observation: F1=0.172 fill=0.767 fallback=1.00. Uniform-K continuous; correspondence weak when Hough falls back.
- Failure mode: f_detection_fallback / low line↔boundary F1
- Rationale: Moderate Hough recovery + slight mask widen; keep uniform_k_snap.
- Overlay: `{"denoising":{"mask_r_low":2.85,"mask_r_high":3.05,"mask_theta_low":1.5,"mask_theta_high":17.0},"enhancing":{"curvature_threshold":0.0008},"detecting":{"binary_threshold":120,"hough_threshold_oblique":35,"hough_threshold_horizontal":35,"hough_threshold_vertical":1600,"maxLineGap_oblique":40,"pattern_tolerance":12,"uniform_k_snap":true},"sam":{"segment_width":1200,"K_height":900,"angle":6.0}}`
- full=False
### Round 1 result
- status=ok proxy=0.5288884362483405 band=refine residual=3.6 elapsed=189.5s

### Round 2 CoT
- Observation: Widen retention + lower binary; F1=0.172.
- Failure mode: f_depth_incomplete or weak edges
- Rationale: Wider mask + lower binary + looser Hough to catch more joints.
- Overlay: `{"denoising":{"mask_r_low":2.75,"mask_r_high":3.12,"mask_theta_low":1.2,"mask_theta_high":18.0},"enhancing":{"curvature_threshold":0.0012},"detecting":{"binary_threshold":105,"hough_threshold_oblique":28,"hough_threshold_horizontal":28,"hough_threshold_vertical":2000,"maxLineGap_oblique":55,"pattern_tolerance":15,"uniform_k_snap":true},"sam":{"segment_width":1150,"K_height":850,"angle":7.0}}`
- full=False
### Round 2 result
- status=ok proxy=0.5251551190930569 band=refine residual=3.6 elapsed=190.2s

### Round 3 CoT
- Observation: Alternate cleaner edges / larger SAM; F1=0.172.
- Failure mode: f_sam_crop_mismatch
- Rationale: Higher binary + larger SAM window.
- Overlay: `{"denoising":{"mask_r_low":2.9,"mask_r_high":3.1,"mask_theta_low":1.8,"mask_theta_high":16.5},"enhancing":{"curvature_threshold":0.0005},"detecting":{"binary_threshold":140,"hough_threshold_oblique":45,"hough_threshold_horizontal":40,"hough_threshold_vertical":1800,"maxLineGap_oblique":30,"pattern_tolerance":10,"uniform_k_snap":true},"sam":{"segment_width":1300,"K_height":950,"angle":5.0}}`
- full=False
### Round 3 result
- status=ok proxy=0.4805559233410175 band=reject residual=3.6 elapsed=169.8s

### Selection
- selected **anchor** Δproxy=+0.000 ΔmIoU=0.0
- reason: monotone accept: no round beat anchor scaled proxy

## 3-8 (t3) — Phase B

### Anchor (GT-blind)
- proxy 0.561 / refine; F1=0.302 fill=0.597 nan=0.182 residual=24.0 unlocked=True

### Round 1 CoT
- Observation: Residual 24.0 cm unlocked; fallback=1.00 F1=0.302. Centreline first.
- Failure mode: f_centreline_residual (+ detection fallback)
- Rationale: Probe seed 1 alone (full 1–6).
- Overlay: `{"unfolding":{"random_seed":1}}`
- full=True
### Round 1 result
- status=ok proxy=0.5612813887349734 band=refine residual=24.0 elapsed=216.3s

### Round 2 CoT
- Observation: Combine seed 1 with detection recovery; F1=0.302.
- Failure mode: f_centreline_residual + f_detection_fallback
- Rationale: Seed 1 + moderate Hough recovery + slight mask widen.
- Overlay: `{"unfolding":{"random_seed":1},"denoising":{"mask_r_low":2.8,"mask_r_high":3.08,"mask_theta_low":1.3,"mask_theta_high":17.5},"enhancing":{"curvature_threshold":0.0008},"detecting":{"binary_threshold":115,"hough_threshold_oblique":25,"hough_threshold_horizontal":25,"hough_threshold_vertical":1800,"maxLineGap_oblique":45,"pattern_tolerance":14,"uniform_k_snap":true},"sam":{"segment_width":1250,"K_height":900,"angle":6.5}}`
- full=True
### Round 2 result
- status=ok proxy=0.5470823262603915 band=refine residual=24.0 elapsed=218.8s

### Round 3 CoT
- Observation: Alternate seed 5; F1=0.302.
- Failure mode: f_centreline_residual
- Rationale: Seed 5 alone for centreline diversity.
- Overlay: `{"unfolding":{"random_seed":5}}`
- full=True
### Round 3 result
- status=ok proxy=0.5896981461976125 band=refine residual=25.3 elapsed=199.0s

### Selection
- selected **round3** Δproxy=+0.028 ΔmIoU=-0.006
- reason: best proxy 0.5897; 1 within 0.01 margin; residual tiebreak -> round3

## 3-9 (t3) — Phase B

### Anchor (GT-blind)
- proxy 0.641 / refine; F1=0.364 fill=0.729 nan=0.131 residual=2.8 unlocked=False

### Round 1 CoT
- Observation: F1=0.364 fill=0.729 fallback=1.00. Uniform-K continuous; correspondence weak when Hough falls back.
- Failure mode: f_detection_fallback / low line↔boundary F1
- Rationale: Moderate Hough recovery + slight mask widen; keep uniform_k_snap.
- Overlay: `{"denoising":{"mask_r_low":2.85,"mask_r_high":3.05,"mask_theta_low":1.5,"mask_theta_high":17.0},"enhancing":{"curvature_threshold":0.0008},"detecting":{"binary_threshold":120,"hough_threshold_oblique":35,"hough_threshold_horizontal":35,"hough_threshold_vertical":1600,"maxLineGap_oblique":40,"pattern_tolerance":12,"uniform_k_snap":true},"sam":{"segment_width":1200,"K_height":900,"angle":6.0}}`
- full=False

---

# Phase B start 2026-09-13T14:16:21.446747
Cases: 3-9, 4-2, 4-5, 5-2, 5-3, 5-4, 5-5

## 3-9 (t3) — Phase B

### Anchor (GT-blind)
- proxy 0.641 / refine; F1=0.364 fill=0.729 nan=0.131 residual=2.8 unlocked=False

### Round 1 CoT
- Observation: F1=0.364 fill=0.729 fallback=1.00. Uniform-K continuous; correspondence weak when Hough falls back.
- Failure mode: f_detection_fallback / low line↔boundary F1
- Rationale: Moderate Hough recovery + slight mask widen; keep uniform_k_snap.
- Overlay: `{"denoising":{"mask_r_low":2.85,"mask_r_high":3.05,"mask_theta_low":1.5,"mask_theta_high":17.0},"enhancing":{"curvature_threshold":0.0008},"detecting":{"binary_threshold":120,"hough_threshold_oblique":35,"hough_threshold_horizontal":35,"hough_threshold_vertical":1600,"maxLineGap_oblique":40,"pattern_tolerance":12,"uniform_k_snap":true},"sam":{"segment_width":1200,"K_height":900,"angle":6.0}}`
- full=False
### Round 1 result
- status=ok proxy=0.6334242890428845 band=refine residual=2.8 elapsed=193.9s

### Round 2 CoT
- Observation: Widen retention + lower binary; F1=0.364.
- Failure mode: f_depth_incomplete or weak edges
- Rationale: Wider mask + lower binary + looser Hough to catch more joints.
- Overlay: `{"denoising":{"mask_r_low":2.75,"mask_r_high":3.12,"mask_theta_low":1.2,"mask_theta_high":18.0},"enhancing":{"curvature_threshold":0.0012},"detecting":{"binary_threshold":105,"hough_threshold_oblique":28,"hough_threshold_horizontal":28,"hough_threshold_vertical":2000,"maxLineGap_oblique":55,"pattern_tolerance":15,"uniform_k_snap":true},"sam":{"segment_width":1150,"K_height":850,"angle":7.0}}`
- full=False
### Round 2 result
- status=ok proxy=0.5678868303608329 band=refine residual=2.8 elapsed=195.9s

### Round 3 CoT
- Observation: Alternate cleaner edges / larger SAM; F1=0.364.
- Failure mode: f_sam_crop_mismatch
- Rationale: Higher binary + larger SAM window.
- Overlay: `{"denoising":{"mask_r_low":2.9,"mask_r_high":3.1,"mask_theta_low":1.8,"mask_theta_high":16.5},"enhancing":{"curvature_threshold":0.0005},"detecting":{"binary_threshold":140,"hough_threshold_oblique":45,"hough_threshold_horizontal":40,"hough_threshold_vertical":1800,"maxLineGap_oblique":30,"pattern_tolerance":10,"uniform_k_snap":true},"sam":{"segment_width":1300,"K_height":950,"angle":5.0}}`
- full=False
### Round 3 result
- status=ok proxy=0.5482665093104201 band=refine residual=2.8 elapsed=174.3s

### Selection
- selected **anchor** Δproxy=+0.000 ΔmIoU=0.0
- reason: monotone accept: no round beat anchor scaled proxy

## 4-2 (t4&5) — Phase B

### Anchor (GT-blind)
- proxy 0.544 / refine; F1=0.213 fill=0.732 nan=0.209 residual=2.0 unlocked=False

### Round 1 CoT
- Observation: F1=0.213 fallback=0.40. Complex irregular K; widen mask and raise vertical Hough hard.
- Failure mode: f_detection_sparse / complex layout mismatch
- Rationale: 4-4 cursor2 coordinated: widen mask, hard vertical, live SAM sizes.
- Overlay: `{"denoising":{"mask_r_low":3.55,"mask_r_high":3.95},"enhancing":{"curvature_threshold":0.001},"detecting":{"binary_threshold":120,"hough_threshold_oblique":40,"hough_threshold_horizontal":30,"hough_threshold_vertical":3500,"maxLineGap_oblique":70,"maxLineGap_horizontal":20,"pattern_tolerance":12},"sam":{"K_height":1150,"segment_width":1700,"angle":9.5}}`
- full=False
### Round 1 result
- status=ok proxy=0.6430508034944254 band=refine residual=2.0 elapsed=274.0s

### Round 2 CoT
- Observation: Milder vertical + wider SAM; F1=0.213.
- Failure mode: over-aggressive vertical or SAM crop
- Rationale: Milder vertical 2500 + larger SAM window.
- Overlay: `{"denoising":{"mask_r_low":3.6,"mask_r_high":4.0},"enhancing":{"curvature_threshold":0.0008},"detecting":{"binary_threshold":110,"hough_threshold_oblique":35,"hough_threshold_horizontal":35,"hough_threshold_vertical":2500,"maxLineGap_oblique":60,"maxLineGap_horizontal":15,"pattern_tolerance":14},"sam":{"K_height":1300,"segment_width":1900,"angle":10.0}}`
- full=False
### Round 2 result
- status=ok proxy=0.6847414633752518 band=refine residual=2.0 elapsed=255.5s

### Round 3 CoT
- Observation: Aggressive vertical + max widen; F1=0.213.
- Failure mode: sparse detection ceiling
- Rationale: Aggressive vertical 4000 + edge-widen mask + larger K_height.
- Overlay: `{"denoising":{"mask_r_low":3.5,"mask_r_high":4.05},"enhancing":{"curvature_threshold":0.0015},"detecting":{"binary_threshold":130,"hough_threshold_oblique":45,"hough_threshold_horizontal":40,"hough_threshold_vertical":4000,"maxLineGap_oblique":75,"maxLineGap_horizontal":25,"pattern_tolerance":10},"sam":{"K_height":1400,"segment_width":2000,"angle":8.5}}`
- full=False
### Round 3 result
- status=ok proxy=0.49115980580387364 band=reject residual=2.0 elapsed=269.2s

### Selection
- selected **round2** Δproxy=+0.141 ΔmIoU=0.039
- reason: best proxy 0.6847; 1 within 0.01 margin; residual tiebreak -> round2

## 4-5 (t4&5) — Phase B

### Anchor (GT-blind)
- proxy 0.609 / refine; F1=0.334 fill=0.735 nan=0.216 residual=3.4 unlocked=False

### Round 1 CoT
- Observation: F1=0.334 fallback=0.40. Complex irregular K; widen mask and raise vertical Hough hard.
- Failure mode: f_detection_sparse / complex layout mismatch
- Rationale: 4-4 cursor2 coordinated: widen mask, hard vertical, live SAM sizes.
- Overlay: `{"denoising":{"mask_r_low":3.55,"mask_r_high":3.95},"enhancing":{"curvature_threshold":0.001},"detecting":{"binary_threshold":120,"hough_threshold_oblique":40,"hough_threshold_horizontal":30,"hough_threshold_vertical":3500,"maxLineGap_oblique":70,"maxLineGap_horizontal":20,"pattern_tolerance":12},"sam":{"K_height":1150,"segment_width":1700,"angle":9.5}}`
- full=False
### Round 1 result
- status=ok proxy=0.6388830809287048 band=refine residual=3.4 elapsed=269.1s

### Round 2 CoT
- Observation: Milder vertical + wider SAM; F1=0.334.
- Failure mode: over-aggressive vertical or SAM crop
- Rationale: Milder vertical 2500 + larger SAM window.
- Overlay: `{"denoising":{"mask_r_low":3.6,"mask_r_high":4.0},"enhancing":{"curvature_threshold":0.0008},"detecting":{"binary_threshold":110,"hough_threshold_oblique":35,"hough_threshold_horizontal":35,"hough_threshold_vertical":2500,"maxLineGap_oblique":60,"maxLineGap_horizontal":15,"pattern_tolerance":14},"sam":{"K_height":1300,"segment_width":1900,"angle":10.0}}`
- full=False
### Round 2 result
- status=ok proxy=0.6583941677209102 band=refine residual=3.4 elapsed=253.4s

### Round 3 CoT
- Observation: Aggressive vertical + max widen; F1=0.334.
- Failure mode: sparse detection ceiling
- Rationale: Aggressive vertical 4000 + edge-widen mask + larger K_height.
- Overlay: `{"denoising":{"mask_r_low":3.5,"mask_r_high":4.05},"enhancing":{"curvature_threshold":0.0015},"detecting":{"binary_threshold":130,"hough_threshold_oblique":45,"hough_threshold_horizontal":40,"hough_threshold_vertical":4000,"maxLineGap_oblique":75,"maxLineGap_horizontal":25,"pattern_tolerance":10},"sam":{"K_height":1400,"segment_width":2000,"angle":8.5}}`
- full=False
### Round 3 result
- status=ok proxy=0.520412904567422 band=refine residual=3.4 elapsed=269.1s

### Selection
- selected **round2** Δproxy=+0.049 ΔmIoU=0.021
- reason: best proxy 0.6584; 1 within 0.01 margin; residual tiebreak -> round2

## 5-2 (t4&5) — Phase B

### Anchor (GT-blind)
- proxy 0.683 / refine; F1=0.453 fill=0.751 nan=0.194 residual=2.1 unlocked=False

### Round 1 CoT
- Observation: F1=0.453 fallback=0.40. Complex irregular K; widen mask and raise vertical Hough hard.
- Failure mode: f_detection_sparse / complex layout mismatch
- Rationale: 4-4 cursor2 coordinated: widen mask, hard vertical, live SAM sizes.
- Overlay: `{"denoising":{"mask_r_low":3.55,"mask_r_high":3.95},"enhancing":{"curvature_threshold":0.001},"detecting":{"binary_threshold":120,"hough_threshold_oblique":40,"hough_threshold_horizontal":30,"hough_threshold_vertical":3500,"maxLineGap_oblique":70,"maxLineGap_horizontal":20,"pattern_tolerance":12},"sam":{"K_height":1150,"segment_width":1700,"angle":9.5}}`
- full=False
### Round 1 result
- status=ok proxy=0.6243169574419272 band=refine residual=2.1 elapsed=262.7s

### Round 2 CoT
- Observation: Milder vertical + wider SAM; F1=0.453.
- Failure mode: over-aggressive vertical or SAM crop
- Rationale: Milder vertical 2500 + larger SAM window.
- Overlay: `{"denoising":{"mask_r_low":3.6,"mask_r_high":4.0},"enhancing":{"curvature_threshold":0.0008},"detecting":{"binary_threshold":110,"hough_threshold_oblique":35,"hough_threshold_horizontal":35,"hough_threshold_vertical":2500,"maxLineGap_oblique":60,"maxLineGap_horizontal":15,"pattern_tolerance":14},"sam":{"K_height":1300,"segment_width":1900,"angle":10.0}}`
- full=False
### Round 2 result
- status=ok proxy=0.7005449546986331 band=accept residual=2.1 elapsed=259.9s

### Round 3 CoT
- Observation: Aggressive vertical + max widen; F1=0.453.
- Failure mode: sparse detection ceiling
- Rationale: Aggressive vertical 4000 + edge-widen mask + larger K_height.
- Overlay: `{"denoising":{"mask_r_low":3.5,"mask_r_high":4.05},"enhancing":{"curvature_threshold":0.0015},"detecting":{"binary_threshold":130,"hough_threshold_oblique":45,"hough_threshold_horizontal":40,"hough_threshold_vertical":4000,"maxLineGap_oblique":75,"maxLineGap_horizontal":25,"pattern_tolerance":10},"sam":{"K_height":1400,"segment_width":2000,"angle":8.5}}`
- full=False
### Round 3 result
- status=ok proxy=0.5267792106767738 band=refine residual=2.1 elapsed=278.6s

### Selection
- selected **round2** Δproxy=+0.018 ΔmIoU=-0.012
- reason: best proxy 0.7005; 1 within 0.01 margin; residual tiebreak -> round2

## 5-3 (t4&5) — Phase B

### Anchor (GT-blind)
- proxy 0.681 / refine; F1=0.459 fill=0.737 nan=0.201 residual=3.5 unlocked=False

### Round 1 CoT
- Observation: F1=0.459 fallback=0.30. Complex irregular K; widen mask and raise vertical Hough hard.
- Failure mode: f_detection_sparse / complex layout mismatch
- Rationale: 4-4 cursor2 coordinated: widen mask, hard vertical, live SAM sizes.
- Overlay: `{"denoising":{"mask_r_low":3.55,"mask_r_high":3.95},"enhancing":{"curvature_threshold":0.001},"detecting":{"binary_threshold":120,"hough_threshold_oblique":40,"hough_threshold_horizontal":30,"hough_threshold_vertical":3500,"maxLineGap_oblique":70,"maxLineGap_horizontal":20,"pattern_tolerance":12},"sam":{"K_height":1150,"segment_width":1700,"angle":9.5}}`
- full=False
### Round 1 result
- status=ok proxy=0.6675353030748981 band=refine residual=3.5 elapsed=274.7s

### Round 2 CoT
- Observation: Milder vertical + wider SAM; F1=0.459.
- Failure mode: over-aggressive vertical or SAM crop
- Rationale: Milder vertical 2500 + larger SAM window.
- Overlay: `{"denoising":{"mask_r_low":3.6,"mask_r_high":4.0},"enhancing":{"curvature_threshold":0.0008},"detecting":{"binary_threshold":110,"hough_threshold_oblique":35,"hough_threshold_horizontal":35,"hough_threshold_vertical":2500,"maxLineGap_oblique":60,"maxLineGap_horizontal":15,"pattern_tolerance":14},"sam":{"K_height":1300,"segment_width":1900,"angle":10.0}}`
- full=False
### Round 2 result
- status=ok proxy=0.6584511784099962 band=refine residual=3.5 elapsed=257.3s

### Round 3 CoT
- Observation: Aggressive vertical + max widen; F1=0.459.
- Failure mode: sparse detection ceiling
- Rationale: Aggressive vertical 4000 + edge-widen mask + larger K_height.
- Overlay: `{"denoising":{"mask_r_low":3.5,"mask_r_high":4.05},"enhancing":{"curvature_threshold":0.0015},"detecting":{"binary_threshold":130,"hough_threshold_oblique":45,"hough_threshold_horizontal":40,"hough_threshold_vertical":4000,"maxLineGap_oblique":75,"maxLineGap_horizontal":25,"pattern_tolerance":10},"sam":{"K_height":1400,"segment_width":2000,"angle":8.5}}`
- full=False
### Round 3 result
- status=ok proxy=0.5391974960274328 band=refine residual=3.5 elapsed=267.7s

### Selection
- selected **anchor** Δproxy=+0.000 ΔmIoU=0.0
- reason: monotone accept: no round beat anchor scaled proxy

## 5-4 (t4&5) — Phase B

### Anchor (GT-blind)
- proxy 0.692 / refine; F1=0.467 fill=0.760 nan=0.198 residual=2.1 unlocked=False

### Round 1 CoT
- Observation: F1=0.467 fallback=0.30. Complex irregular K; widen mask and raise vertical Hough hard.
- Failure mode: f_detection_sparse / complex layout mismatch
- Rationale: 4-4 cursor2 coordinated: widen mask, hard vertical, live SAM sizes.
- Overlay: `{"denoising":{"mask_r_low":3.55,"mask_r_high":3.95},"enhancing":{"curvature_threshold":0.001},"detecting":{"binary_threshold":120,"hough_threshold_oblique":40,"hough_threshold_horizontal":30,"hough_threshold_vertical":3500,"maxLineGap_oblique":70,"maxLineGap_horizontal":20,"pattern_tolerance":12},"sam":{"K_height":1150,"segment_width":1700,"angle":9.5}}`
- full=False
### Round 1 result
- status=ok proxy=0.6869361703375827 band=refine residual=2.1 elapsed=270.4s

### Round 2 CoT
- Observation: Milder vertical + wider SAM; F1=0.467.
- Failure mode: over-aggressive vertical or SAM crop
- Rationale: Milder vertical 2500 + larger SAM window.
- Overlay: `{"denoising":{"mask_r_low":3.6,"mask_r_high":4.0},"enhancing":{"curvature_threshold":0.0008},"detecting":{"binary_threshold":110,"hough_threshold_oblique":35,"hough_threshold_horizontal":35,"hough_threshold_vertical":2500,"maxLineGap_oblique":60,"maxLineGap_horizontal":15,"pattern_tolerance":14},"sam":{"K_height":1300,"segment_width":1900,"angle":10.0}}`
- full=False
### Round 2 result
- status=ok proxy=0.6828935293547586 band=refine residual=2.1 elapsed=257.5s

### Round 3 CoT
- Observation: Aggressive vertical + max widen; F1=0.467.
- Failure mode: sparse detection ceiling
- Rationale: Aggressive vertical 4000 + edge-widen mask + larger K_height.
- Overlay: `{"denoising":{"mask_r_low":3.5,"mask_r_high":4.05},"enhancing":{"curvature_threshold":0.0015},"detecting":{"binary_threshold":130,"hough_threshold_oblique":45,"hough_threshold_horizontal":40,"hough_threshold_vertical":4000,"maxLineGap_oblique":75,"maxLineGap_horizontal":25,"pattern_tolerance":10},"sam":{"K_height":1400,"segment_width":2000,"angle":8.5}}`
- full=False
### Round 3 result
- status=ok proxy=0.5505661264600892 band=refine residual=2.1 elapsed=268.3s

### Selection
- selected **anchor** Δproxy=+0.000 ΔmIoU=0.0
- reason: monotone accept: no round beat anchor scaled proxy

## 5-5 (t4&5) — Phase B

### Anchor (GT-blind)
- proxy 0.610 / refine; F1=0.316 fill=0.756 nan=0.193 residual=1.9 unlocked=False

### Round 1 CoT
- Observation: F1=0.316 fallback=0.20. Complex irregular K; widen mask and raise vertical Hough hard.
- Failure mode: f_detection_sparse / complex layout mismatch
- Rationale: 4-4 cursor2 coordinated: widen mask, hard vertical, live SAM sizes.
- Overlay: `{"denoising":{"mask_r_low":3.55,"mask_r_high":3.95},"enhancing":{"curvature_threshold":0.001},"detecting":{"binary_threshold":120,"hough_threshold_oblique":40,"hough_threshold_horizontal":30,"hough_threshold_vertical":3500,"maxLineGap_oblique":70,"maxLineGap_horizontal":20,"pattern_tolerance":12},"sam":{"K_height":1150,"segment_width":1700,"angle":9.5}}`
- full=False
### Round 1 result
- status=ok proxy=0.6421601312957144 band=refine residual=1.9 elapsed=263.3s

### Round 2 CoT
- Observation: Milder vertical + wider SAM; F1=0.316.
- Failure mode: over-aggressive vertical or SAM crop
- Rationale: Milder vertical 2500 + larger SAM window.
- Overlay: `{"denoising":{"mask_r_low":3.6,"mask_r_high":4.0},"enhancing":{"curvature_threshold":0.0008},"detecting":{"binary_threshold":110,"hough_threshold_oblique":35,"hough_threshold_horizontal":35,"hough_threshold_vertical":2500,"maxLineGap_oblique":60,"maxLineGap_horizontal":15,"pattern_tolerance":14},"sam":{"K_height":1300,"segment_width":1900,"angle":10.0}}`
- full=False
### Round 2 result
- status=ok proxy=0.7038119681236421 band=accept residual=1.9 elapsed=263.7s

### Round 3 CoT
- Observation: Aggressive vertical + max widen; F1=0.316.
- Failure mode: sparse detection ceiling
- Rationale: Aggressive vertical 4000 + edge-widen mask + larger K_height.
- Overlay: `{"denoising":{"mask_r_low":3.5,"mask_r_high":4.05},"enhancing":{"curvature_threshold":0.0015},"detecting":{"binary_threshold":130,"hough_threshold_oblique":45,"hough_threshold_horizontal":40,"hough_threshold_vertical":4000,"maxLineGap_oblique":75,"maxLineGap_horizontal":25,"pattern_tolerance":10},"sam":{"K_height":1400,"segment_width":2000,"angle":8.5}}`
- full=False
### Round 3 result
- status=ok proxy=0.548734370569035 band=refine residual=1.9 elapsed=273.8s

### Selection
- selected **round2** Δproxy=+0.094 ΔmIoU=0.006
- reason: best proxy 0.7038; 1 within 0.01 margin; residual tiebreak -> round2

---

## Phase B complete
All 16 remaining in-band cases finished; 22/22 fable selections present.
Panel mean mIoU 0.738 → 0.768 (15/22 refined). Dual-band 0.592 → 0.689.
Reports: report_fable.md, arm_comparison.md, region_comparison_fable.csv.
Disk note: mid-run ENOSPC recovered by slimmed round intermediates (kept reflection_record/only_label/evaluation/intrinsics).

---

# Paper nine under 4-feature SC-general proxy — Fable-5.1

Proposer label updated to `fable-5.1 (cursor agent, live)`.
Six dual-band cases already completed earlier in this session under the prior
label `fable-5`; same agent/session, reused as-is for the paper-nine table.
Now refining the three reject-band paper-nine cases: **3-2, 3-5, 4-4**.

Note: under the 4-feature pruned_lean proxy these three have proxy < 0.5, so
the label-free refine panel would skip them; we still run them for parity with
the manuscript's nine-case feasibility set.

## 3-2 (t3) — paper nine / reject band

### Anchor (GT-blind)
- proxy 0.454 / reject; F1=0.057 fill=0.677 nan=0.159 residual=16.8 unlocked
- real=0.0 fallback=1.0; seed currently 1
- SC overlay: mostly assumed prompts; sparse explained joints

### Round 1 CoT
- Observation: residual 16.8 cm + total Hough fallback; F1 cannot rise until centreline improves.
- Rule: unlocked residual → probe alternate seed alone (full 1–6) before retuning 2–6.
- Failure mode: f_centreline_residual + f_detection_fallback.
- Overlay: unfolding.random_seed=0. --full.

### Round 1 result
| Round | Proxy | Band | Residual | F1 | Note |
|---|---:|---|---:|---:|---|
| anchor | 0.454 | reject | 16.8 | 0.057 | seed 1 |
| R1 | 0.473 | reject | **5.4** | 0.070 | seed 0; residual↓ |

### Round 2 CoT
- Observation: seed 0 fixed residual. Couple with moderate Hough recovery to lift F1 from fallback.
- Overlay: seed 0 + mask [2.80,3.08] theta [1.3,17.5]; curv 0.0008; binary 115; Hough 25/25/1800; gap 45; tol 14; uniform_k_snap; SAM 1250/900/6.5. --full.

### 3-2 selection
- selected **round3** (seed 5) Δproxy +0.015 ΔmIoU +0.118

---

## 3-5 (t3) — paper nine / reject band

### Anchor (GT-blind)
- proxy 0.439 / reject; F1=0.124 fill=0.538 nan=0.227 residual=**56.6** unlocked
- real=0.0 fallback=1.0; retained=0.67; seed currently 1
- Severe centreline; detection collapsed.

### Round 1 CoT
- Observation: residual 56.6 cm is binding; seed 1 present. Probe seed 0 alone.
- Failure mode: f_centreline_residual (severe) + f_detection_fallback.
- Overlay: unfolding.random_seed=0. --full.

### 3-5 results
| Round | Proxy | Band | Residual | F1 | Note |
|---|---:|---|---:|---:|---|
| anchor | 0.439 | reject | 56.6 | 0.124 | seed 1 |
| R1 | **0.671** | refine | **2.6** | 0.407 | seed 0; crossed refine |
| R2 | 0.667 | refine | 2.6 | 0.394 | seed0+Hough |
| R3 | 0.591 | refine | 3.5 | 0.263 | seed5+Hough |
Selected **round1** Δproxy +0.232 ΔmIoU +0.282

---

## 4-4 (t4&5) — paper nine / reject band

### Anchor (GT-blind)
- proxy 0.453 / reject; F1=0.071 fill=0.722 nan=0.259 residual=**35.0** unlocked
- real=0.4 fallback=0.6; seed currently 0
- Complex irregular; centreline binding.

### Round 1 CoT
- Observation: residual 35 cm with seed 0. Probe seed 1 alone (legacy centreline fix on this family).
- Failure mode: f_centreline_residual.
- Overlay: unfolding.random_seed=1. --full.

### 4-4 results
| Round | Proxy | Band | Residual | F1 | Note |
|---|---:|---|---:|---:|---|
| anchor | 0.453 | reject | 35.0 | 0.071 | seed 0 |
| R1 | 0.514 | refine | 22.9 | 0.173 | seed 1 |
| R2 | 0.496 | reject | 22.9 | 0.135 | seed1+2–6 |
| R3 | **0.516** | refine | **2.3** | 0.164 | seed 5 |
Selected **round3** Δproxy +0.063 ΔmIoU +0.021

---

## Paper nine complete
All nine cases have fable selections. See `paper_nine_comparison.md`.

