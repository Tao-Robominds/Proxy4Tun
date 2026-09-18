# SC-general Stage-3 refinement campaign

GT-blind reflective loop. Proxy = pruned_lean. Panel = proxy ∈ [0.5, 0.7].


---

## 1-3 (staggered)


---

## 3-4 (continuous)

### Round 2 CoT (2026-09-12T21:03:31.121755)
- Observation: Residual unlocked; F1=0.170. Probe stage-1 seed.
- Failure mode: `f_centreline_residual`
- Rationale: Stage-1 seed probe (seed 0) with frozen later stages from overlay materialization of base+seed.
- Overlay: `{"unfolding":{"random_seed":0}}`
- full_pipeline: True
### Round 1 CoT (2026-09-12T21:03:34.016045)
- Observation: F1@15=0.187 fill=0.733 nan=0.109. Detection mostly real; SC bottleneck is line↔boundary agreement / SAM crop.
- Failure mode: `f_template_mismatch / weak correspondence`
- Rationale: 1-5-style multi-stage: tighten Hough + raise y_bounds lower + mask/curv retune.
- Overlay: `{"denoising":{"mask_r_low":2.4,"mask_r_high":2.85,"z_step":0.003,"grad_threshold":0.18},"enhancing":{"curvature_threshold":0.006,"inter_radius":0.055},"detecting":{"binary_threshold":120,"hough_threshold_oblique":75,"hough_threshold_horizontal":75,"hough_threshold_vertical":700,"maxLineGap_oblique":35},"sam":{"processing.y_bounds":[4200,13300]}}`
- full_pipeline: False
- Result: status=ok proxy_scaled=0.4963 band=reject F1=0.209 fill=0.556 elapsed=204.3s
### Round 3 CoT (2026-09-12T21:06:56.922732)
- Observation: Combine seed 5 with detection recipe; F1=0.209.
- Failure mode: `f_centreline_residual + weak correspondence`
- Rationale: Combined stage-1 seed 5 + R1 detection recipe.
- Overlay: `{"unfolding":{"random_seed":5},"denoising":{"mask_r_low":2.85,"mask_r_high":3.05,"mask_theta_low":1.5,"mask_theta_high":17.0},"enhancing":{"curvature_threshold":0.0008},"detecting":{"binary_threshold":120,"hough_threshold_oblique":35,"hough_threshold_horizontal":35,"hough_threshold_vertical":1600,"maxLineGap_oblique":40,"pattern_tolerance":12,"uniform_k_snap":true},"sam":{"segment_width":1200,"K_height":900,"angle":6.0}}`
- full_pipeline: True
- Result: status=ok proxy_scaled=0.4728 band=reject F1=0.160 fill=0.554 elapsed=195.3s

**Selected:** `anchor` (Δproxy=+0.0000, ΔmIoU_offline=0.0). Reason: monotone accept: no round beat anchor scaled proxy

---

## 1-3 (staggered)

### Round 1 CoT (2026-09-12T21:10:28.120697)
- Observation: F1@15=0.187 fill=0.733 nan=0.109. Detection mostly real; SC bottleneck is line↔boundary agreement / SAM crop.
- Failure mode: `f_template_mismatch / weak correspondence`
- Rationale: 1-5-style multi-stage: tighten Hough + raise y_bounds lower + mask/curv retune.
- Overlay: `{"denoising":{"mask_r_low":2.4,"mask_r_high":2.85,"z_step":0.003,"grad_threshold":0.18},"enhancing":{"curvature_threshold":0.006,"inter_radius":0.055},"detecting":{"binary_threshold":120,"hough_threshold_oblique":75,"hough_threshold_horizontal":75,"hough_threshold_vertical":700,"maxLineGap_oblique":35},"sam":{"processing.y_bounds":[4200,13300]}}`
- full_pipeline: False
- Result: status=ok proxy_scaled=0.6798 band=refine F1=0.416 fill=0.740 elapsed=279.3s
### Round 2 CoT (2026-09-12T21:15:10.211561)
- Observation: After R1: F1=0.416 fill=0.740. Probe milder Hough / wider gap.
- Failure mode: `over-suppressed joints or residual K-crop mismatch`
- Rationale: Relax Hough slightly; widen gap; nudge y_bounds toward K band.
- Overlay: `{"denoising":{"mask_r_low":2.3,"mask_r_high":2.8,"z_step":0.004,"grad_threshold":0.16},"enhancing":{"curvature_threshold":0.004,"inter_radius":0.045},"detecting":{"binary_threshold":110,"hough_threshold_oblique":60,"hough_threshold_horizontal":60,"hough_threshold_vertical":550,"maxLineGap_oblique":50},"sam":{"processing.y_bounds":[4000,13300]}}`
- full_pipeline: False
- Result: status=ok proxy_scaled=0.6525 band=refine F1=0.372 fill=0.739 elapsed=273.2s
### Round 3 CoT (2026-09-12T21:19:46.187120)
- Observation: R3 alternate: F1=0.372 fill=0.739.
- Failure mode: `incomplete correspondence; try denser retention + stronger vertical`
- Rationale: Third recipe: stronger vertical Hough + lower z_step for denser lining.
- Overlay: `{"denoising":{"mask_r_low":2.35,"mask_r_high":2.88,"z_step":0.002,"grad_threshold":0.2},"enhancing":{"curvature_threshold":0.005,"inter_radius":0.06},"detecting":{"binary_threshold":130,"hough_threshold_oblique":80,"hough_threshold_horizontal":70,"hough_threshold_vertical":750,"maxLineGap_oblique":40},"sam":{"processing.y_bounds":[4300,13300]}}`
- full_pipeline: False
- Result: status=ok proxy_scaled=0.6611 band=refine F1=0.390 fill=0.737 elapsed=279.0s

**Selected:** `round1` (Δproxy=+0.1296, ΔmIoU_offline=0.046). Reason: best proxy 0.6798; 1 within 0.01 margin; residual tiebreak -> round1

---

## 1-5 (staggered)

### Round 1 CoT (2026-09-12T21:24:51.783134)
- Observation: F1@15=0.201 fill=0.729 nan=0.118. Detection mostly real; SC bottleneck is line↔boundary agreement / SAM crop.
- Failure mode: `f_template_mismatch / weak correspondence`
- Rationale: 1-5-style multi-stage: tighten Hough + raise y_bounds lower + mask/curv retune.
- Overlay: `{"denoising":{"mask_r_low":2.4,"mask_r_high":2.85,"z_step":0.003,"grad_threshold":0.18},"enhancing":{"curvature_threshold":0.006,"inter_radius":0.055},"detecting":{"binary_threshold":120,"hough_threshold_oblique":75,"hough_threshold_horizontal":75,"hough_threshold_vertical":700,"maxLineGap_oblique":35},"sam":{"processing.y_bounds":[4200,13300]}}`
- full_pipeline: False
- Result: status=ok proxy_scaled=0.6343 band=refine F1=0.341 fill=0.737 elapsed=294.6s
### Round 2 CoT (2026-09-12T21:29:49.439149)
- Observation: After R1: F1=0.341 fill=0.737. Probe milder Hough / wider gap.
- Failure mode: `over-suppressed joints or residual K-crop mismatch`
- Rationale: Relax Hough slightly; widen gap; nudge y_bounds toward K band.
- Overlay: `{"denoising":{"mask_r_low":2.3,"mask_r_high":2.8,"z_step":0.004,"grad_threshold":0.16},"enhancing":{"curvature_threshold":0.004,"inter_radius":0.045},"detecting":{"binary_threshold":110,"hough_threshold_oblique":60,"hough_threshold_horizontal":60,"hough_threshold_vertical":550,"maxLineGap_oblique":50},"sam":{"processing.y_bounds":[4000,13300]}}`
- full_pipeline: False
- Result: status=ok proxy_scaled=0.5626 band=refine F1=0.206 fill=0.744 elapsed=287.3s
### Round 3 CoT (2026-09-12T21:34:39.673342)
- Observation: R3 alternate: F1=0.206 fill=0.744.
- Failure mode: `incomplete correspondence; try denser retention + stronger vertical`
- Rationale: Third recipe: stronger vertical Hough + lower z_step for denser lining.
- Overlay: `{"denoising":{"mask_r_low":2.35,"mask_r_high":2.88,"z_step":0.002,"grad_threshold":0.2},"enhancing":{"curvature_threshold":0.005,"inter_radius":0.06},"detecting":{"binary_threshold":130,"hough_threshold_oblique":80,"hough_threshold_horizontal":70,"hough_threshold_vertical":750,"maxLineGap_oblique":40},"sam":{"processing.y_bounds":[4300,13300]}}`
- full_pipeline: False
- Result: status=ok proxy_scaled=0.6575 band=refine F1=0.386 fill=0.733 elapsed=287.8s

**Selected:** `round3` (Δproxy=+0.1024, ΔmIoU_offline=0.144). Reason: best proxy 0.6575; 1 within 0.01 margin; residual tiebreak -> round3

---

## 1-1 (staggered)

### Round 1 CoT (2026-09-12T21:39:57.250182)
- Observation: F1@15=0.294 fill=0.723 nan=0.107. Detection mostly real; SC bottleneck is line↔boundary agreement / SAM crop.
- Failure mode: `f_template_mismatch / weak correspondence`
- Rationale: 1-5-style multi-stage: tighten Hough + raise y_bounds lower + mask/curv retune.
- Overlay: `{"denoising":{"mask_r_low":2.4,"mask_r_high":2.85,"z_step":0.003,"grad_threshold":0.18},"enhancing":{"curvature_threshold":0.006,"inter_radius":0.055},"detecting":{"binary_threshold":120,"hough_threshold_oblique":75,"hough_threshold_horizontal":75,"hough_threshold_vertical":700,"maxLineGap_oblique":35},"sam":{"processing.y_bounds":[4200,13300]}}`
- full_pipeline: False
- Result: status=ok proxy_scaled=0.6278 band=refine F1=0.328 fill=0.737 elapsed=283.5s
### Round 2 CoT (2026-09-12T21:44:44.655338)
- Observation: After R1: F1=0.328 fill=0.737. Probe milder Hough / wider gap.
- Failure mode: `over-suppressed joints or residual K-crop mismatch`
- Rationale: Relax Hough slightly; widen gap; nudge y_bounds toward K band.
- Overlay: `{"denoising":{"mask_r_low":2.3,"mask_r_high":2.8,"z_step":0.004,"grad_threshold":0.16},"enhancing":{"curvature_threshold":0.004,"inter_radius":0.045},"detecting":{"binary_threshold":110,"hough_threshold_oblique":60,"hough_threshold_horizontal":60,"hough_threshold_vertical":550,"maxLineGap_oblique":50},"sam":{"processing.y_bounds":[4000,13300]}}`
- full_pipeline: False
- Result: status=ok proxy_scaled=0.6122 band=refine F1=0.301 fill=0.736 elapsed=281.0s
### Round 3 CoT (2026-09-12T21:49:29.629277)
- Observation: R3 alternate: F1=0.301 fill=0.736.
- Failure mode: `incomplete correspondence; try denser retention + stronger vertical`
- Rationale: Third recipe: stronger vertical Hough + lower z_step for denser lining.
- Overlay: `{"denoising":{"mask_r_low":2.35,"mask_r_high":2.88,"z_step":0.002,"grad_threshold":0.2},"enhancing":{"curvature_threshold":0.005,"inter_radius":0.06},"detecting":{"binary_threshold":130,"hough_threshold_oblique":80,"hough_threshold_horizontal":70,"hough_threshold_vertical":750,"maxLineGap_oblique":40},"sam":{"processing.y_bounds":[4300,13300]}}`
- full_pipeline: False
- Result: status=ok proxy_scaled=0.6226 band=refine F1=0.320 fill=0.734 elapsed=280.7s

**Selected:** `round1` (Δproxy=+0.0211, ΔmIoU_offline=-0.003). Reason: best proxy 0.6278; 2 within 0.01 margin; residual tiebreak -> round1

---

## 1-4 (staggered)

### Round 1 CoT (2026-09-12T21:54:38.087848)
- Observation: F1@15=0.395 fill=0.699 nan=0.150. Detection mostly real; SC bottleneck is line↔boundary agreement / SAM crop.
- Failure mode: `f_template_mismatch / weak correspondence`
- Rationale: 1-5-style multi-stage: tighten Hough + raise y_bounds lower + mask/curv retune.
- Overlay: `{"denoising":{"mask_r_low":2.4,"mask_r_high":2.85,"z_step":0.003,"grad_threshold":0.18},"enhancing":{"curvature_threshold":0.006,"inter_radius":0.055},"detecting":{"binary_threshold":120,"hough_threshold_oblique":75,"hough_threshold_horizontal":75,"hough_threshold_vertical":700,"maxLineGap_oblique":35},"sam":{"processing.y_bounds":[4200,13300]}}`
- full_pipeline: False
- Result: status=ok proxy_scaled=0.7144 band=accept F1=0.494 fill=0.738 elapsed=275.6s
### Round 2 CoT (2026-09-12T21:59:16.558314)
- Observation: After R1: F1=0.494 fill=0.738. Probe milder Hough / wider gap.
- Failure mode: `over-suppressed joints or residual K-crop mismatch`
- Rationale: Relax Hough slightly; widen gap; nudge y_bounds toward K band.
- Overlay: `{"denoising":{"mask_r_low":2.3,"mask_r_high":2.8,"z_step":0.004,"grad_threshold":0.16},"enhancing":{"curvature_threshold":0.004,"inter_radius":0.045},"detecting":{"binary_threshold":110,"hough_threshold_oblique":60,"hough_threshold_horizontal":60,"hough_threshold_vertical":550,"maxLineGap_oblique":50},"sam":{"processing.y_bounds":[4000,13300]}}`
- full_pipeline: False
- Result: status=ok proxy_scaled=0.7095 band=accept F1=0.485 fill=0.742 elapsed=272.9s
### Round 3 CoT (2026-09-12T22:03:52.280594)
- Observation: R3 alternate: F1=0.485 fill=0.742.
- Failure mode: `incomplete correspondence; try denser retention + stronger vertical`
- Rationale: Third recipe: stronger vertical Hough + lower z_step for denser lining.
- Overlay: `{"denoising":{"mask_r_low":2.35,"mask_r_high":2.88,"z_step":0.002,"grad_threshold":0.2},"enhancing":{"curvature_threshold":0.005,"inter_radius":0.06},"detecting":{"binary_threshold":130,"hough_threshold_oblique":80,"hough_threshold_horizontal":70,"hough_threshold_vertical":750,"maxLineGap_oblique":40},"sam":{"processing.y_bounds":[4300,13300]}}`
- full_pipeline: False
- Result: status=ok proxy_scaled=0.7071 band=accept F1=0.481 fill=0.741 elapsed=274.0s

**Selected:** `round1` (Δproxy=+0.0681, ΔmIoU_offline=0.27). Reason: best proxy 0.7144; 3 within 0.01 margin; residual tiebreak -> round1

---

## 1-2 (staggered)

### Round 1 CoT (2026-09-12T22:09:00.839858)
- Observation: F1@15=0.368 fill=0.723 nan=0.102. Detection mostly real; SC bottleneck is line↔boundary agreement / SAM crop.
- Failure mode: `f_template_mismatch / weak correspondence`
- Rationale: 1-5-style multi-stage: tighten Hough + raise y_bounds lower + mask/curv retune.
- Overlay: `{"denoising":{"mask_r_low":2.4,"mask_r_high":2.85,"z_step":0.003,"grad_threshold":0.18},"enhancing":{"curvature_threshold":0.006,"inter_radius":0.055},"detecting":{"binary_threshold":120,"hough_threshold_oblique":75,"hough_threshold_horizontal":75,"hough_threshold_vertical":700,"maxLineGap_oblique":35},"sam":{"processing.y_bounds":[4200,13300]}}`
- full_pipeline: False
- Result: status=ok proxy_scaled=0.7010 band=accept F1=0.458 fill=0.732 elapsed=285.5s
### Round 2 CoT (2026-09-12T22:13:49.111454)
- Observation: After R1: F1=0.458 fill=0.732. Probe milder Hough / wider gap.
- Failure mode: `over-suppressed joints or residual K-crop mismatch`
- Rationale: Relax Hough slightly; widen gap; nudge y_bounds toward K band.
- Overlay: `{"denoising":{"mask_r_low":2.3,"mask_r_high":2.8,"z_step":0.004,"grad_threshold":0.16},"enhancing":{"curvature_threshold":0.004,"inter_radius":0.045},"detecting":{"binary_threshold":110,"hough_threshold_oblique":60,"hough_threshold_horizontal":60,"hough_threshold_vertical":550,"maxLineGap_oblique":50},"sam":{"processing.y_bounds":[4000,13300]}}`
- full_pipeline: False
- Result: status=ok proxy_scaled=0.6538 band=refine F1=0.377 fill=0.726 elapsed=280.3s
### Round 3 CoT (2026-09-12T22:18:32.198820)
- Observation: R3 alternate: F1=0.377 fill=0.726.
- Failure mode: `incomplete correspondence; try denser retention + stronger vertical`
- Rationale: Third recipe: stronger vertical Hough + lower z_step for denser lining.
- Overlay: `{"denoising":{"mask_r_low":2.35,"mask_r_high":2.88,"z_step":0.002,"grad_threshold":0.2},"enhancing":{"curvature_threshold":0.005,"inter_radius":0.06},"detecting":{"binary_threshold":130,"hough_threshold_oblique":80,"hough_threshold_horizontal":70,"hough_threshold_vertical":750,"maxLineGap_oblique":40},"sam":{"processing.y_bounds":[4300,13300]}}`
- full_pipeline: False
- Result: status=ok proxy_scaled=0.6884 band=refine F1=0.441 fill=0.728 elapsed=281.4s

**Selected:** `round1` (Δproxy=+0.0531, ΔmIoU_offline=0.004). Reason: best proxy 0.7010; 1 within 0.01 margin; residual tiebreak -> round1

---

## 2-4 (staggered)

### Round 1 CoT (2026-09-12T22:23:44.040330)
- Observation: F1@15=0.412 fill=0.745 nan=0.109. Detection mostly real; SC bottleneck is line↔boundary agreement / SAM crop.
- Failure mode: `f_template_mismatch / weak correspondence`
- Rationale: 1-5-style multi-stage: tighten Hough + raise y_bounds lower + mask/curv retune.
- Overlay: `{"denoising":{"mask_r_low":2.4,"mask_r_high":2.85,"z_step":0.003,"grad_threshold":0.18},"enhancing":{"curvature_threshold":0.006,"inter_radius":0.055},"detecting":{"binary_threshold":120,"hough_threshold_oblique":75,"hough_threshold_horizontal":75,"hough_threshold_vertical":700,"maxLineGap_oblique":35},"sam":{"processing.y_bounds":[4200,13300]}}`
- full_pipeline: False
- Result: status=ok proxy_scaled=0.7089 band=accept F1=0.464 fill=0.757 elapsed=288.1s
### Round 2 CoT (2026-09-12T22:28:34.905890)
- Observation: After R1: F1=0.464 fill=0.757. Probe milder Hough / wider gap.
- Failure mode: `over-suppressed joints or residual K-crop mismatch`
- Rationale: Relax Hough slightly; widen gap; nudge y_bounds toward K band.
- Overlay: `{"denoising":{"mask_r_low":2.3,"mask_r_high":2.8,"z_step":0.004,"grad_threshold":0.16},"enhancing":{"curvature_threshold":0.004,"inter_radius":0.045},"detecting":{"binary_threshold":110,"hough_threshold_oblique":60,"hough_threshold_horizontal":60,"hough_threshold_vertical":550,"maxLineGap_oblique":50},"sam":{"processing.y_bounds":[4000,13300]}}`
- full_pipeline: False
- Result: status=ok proxy_scaled=0.6707 band=refine F1=0.403 fill=0.746 elapsed=281.8s
### Round 3 CoT (2026-09-12T22:33:19.436409)
- Observation: R3 alternate: F1=0.403 fill=0.746.
- Failure mode: `incomplete correspondence; try denser retention + stronger vertical`
- Rationale: Third recipe: stronger vertical Hough + lower z_step for denser lining.
- Overlay: `{"denoising":{"mask_r_low":2.35,"mask_r_high":2.88,"z_step":0.002,"grad_threshold":0.2},"enhancing":{"curvature_threshold":0.005,"inter_radius":0.06},"detecting":{"binary_threshold":130,"hough_threshold_oblique":80,"hough_threshold_horizontal":70,"hough_threshold_vertical":750,"maxLineGap_oblique":40},"sam":{"processing.y_bounds":[4300,13300]}}`
- full_pipeline: False
- Result: status=ok proxy_scaled=0.7083 band=accept F1=0.463 fill=0.754 elapsed=286.2s

**Selected:** `round1` (Δproxy=+0.0326, ΔmIoU_offline=-0.019). Reason: best proxy 0.7089; 2 within 0.01 margin; residual tiebreak -> round1

---

## 2-2 (staggered)

### Round 1 CoT (2026-09-12T22:38:47.266306)
- Observation: F1@15=0.455 fill=0.743 nan=0.111. Detection mostly real; SC bottleneck is line↔boundary agreement / SAM crop.
- Failure mode: `f_template_mismatch / weak correspondence`
- Rationale: 1-5-style multi-stage: tighten Hough + raise y_bounds lower + mask/curv retune.
- Overlay: `{"denoising":{"mask_r_low":2.4,"mask_r_high":2.85,"z_step":0.003,"grad_threshold":0.18},"enhancing":{"curvature_threshold":0.006,"inter_radius":0.055},"detecting":{"binary_threshold":120,"hough_threshold_oblique":75,"hough_threshold_horizontal":75,"hough_threshold_vertical":700,"maxLineGap_oblique":35},"sam":{"processing.y_bounds":[4200,13300]}}`
- full_pipeline: False
- Result: status=ok proxy_scaled=0.7573 band=accept F1=0.558 fill=0.747 elapsed=287.9s
### Round 2 CoT (2026-09-12T22:43:37.968846)
- Observation: After R1: F1=0.558 fill=0.747. Probe milder Hough / wider gap.
- Failure mode: `over-suppressed joints or residual K-crop mismatch`
- Rationale: Relax Hough slightly; widen gap; nudge y_bounds toward K band.
- Overlay: `{"denoising":{"mask_r_low":2.3,"mask_r_high":2.8,"z_step":0.004,"grad_threshold":0.16},"enhancing":{"curvature_threshold":0.004,"inter_radius":0.045},"detecting":{"binary_threshold":110,"hough_threshold_oblique":60,"hough_threshold_horizontal":60,"hough_threshold_vertical":550,"maxLineGap_oblique":50},"sam":{"processing.y_bounds":[4000,13300]}}`
- full_pipeline: False
- Result: status=ok proxy_scaled=0.6773 band=refine F1=0.409 fill=0.753 elapsed=283.8s
### Round 3 CoT (2026-09-12T22:48:24.619335)
- Observation: R3 alternate: F1=0.409 fill=0.753.
- Failure mode: `incomplete correspondence; try denser retention + stronger vertical`
- Rationale: Third recipe: stronger vertical Hough + lower z_step for denser lining.
- Overlay: `{"denoising":{"mask_r_low":2.35,"mask_r_high":2.88,"z_step":0.002,"grad_threshold":0.2},"enhancing":{"curvature_threshold":0.005,"inter_radius":0.06},"detecting":{"binary_threshold":130,"hough_threshold_oblique":80,"hough_threshold_horizontal":70,"hough_threshold_vertical":750,"maxLineGap_oblique":40},"sam":{"processing.y_bounds":[4300,13300]}}`
- full_pipeline: False
- Result: status=ok proxy_scaled=0.7225 band=accept F1=0.494 fill=0.746 elapsed=284.8s

**Selected:** `round1` (Δproxy=+0.0581, ΔmIoU_offline=0.17). Reason: best proxy 0.7573; 1 within 0.01 margin; residual tiebreak -> round1

---

## 3-3 (continuous)

### Round 1 CoT (2026-09-12T22:53:47.334704)
- Observation: F1@15=0.113 fill=0.780 nan=0.114 fallback=1.00. Uniform-K continuous; correspondence weak when Hough falls back.
- Failure mode: `f_detection_fallback / low line↔boundary F1`
- Rationale: Moderate Hough (not ultra-low) to recover real joints without flooding spurious lines that tank F1; keep uniform_k_snap.
- Overlay: `{"denoising":{"mask_r_low":2.85,"mask_r_high":3.05,"mask_theta_low":1.5,"mask_theta_high":17.0},"enhancing":{"curvature_threshold":0.0008},"detecting":{"binary_threshold":120,"hough_threshold_oblique":35,"hough_threshold_horizontal":35,"hough_threshold_vertical":1600,"maxLineGap_oblique":40,"pattern_tolerance":12,"uniform_k_snap":true},"sam":{"segment_width":1200,"K_height":900,"angle":6.0}}`
- full_pipeline: False
- Result: status=ok proxy_scaled=0.5009 band=refine F1=0.071 fill=0.780 elapsed=194.7s
### Round 2 CoT (2026-09-12T22:57:03.407349)
- Observation: F1=0.071 fill=0.780. Try wider mask + lower binary.
- Failure mode: `f_depth_incomplete or weak edges`
- Rationale: Widen retention + slightly lower Hough to catch more joint evidence.
- Overlay: `{"denoising":{"mask_r_low":2.75,"mask_r_high":3.12,"mask_theta_low":1.2,"mask_theta_high":18.0},"enhancing":{"curvature_threshold":0.0012},"detecting":{"binary_threshold":105,"hough_threshold_oblique":28,"hough_threshold_horizontal":28,"hough_threshold_vertical":2000,"maxLineGap_oblique":55,"pattern_tolerance":15,"uniform_k_snap":true},"sam":{"segment_width":1150,"K_height":850,"angle":7.0}}`
- full_pipeline: False
- Result: status=ok proxy_scaled=0.5116 band=refine F1=0.091 fill=0.781 elapsed=198.0s
### Round 3 CoT (2026-09-12T23:00:22.813917)
- Observation: R3 alternate SAM/Hough; F1=0.091 fill=0.781.
- Failure mode: `f_sam_crop_mismatch`
- Rationale: Cleaner edges (higher binary) + larger SAM window.
- Overlay: `{"denoising":{"mask_r_low":2.9,"mask_r_high":3.1,"mask_theta_low":1.8,"mask_theta_high":16.5},"enhancing":{"curvature_threshold":0.0005},"detecting":{"binary_threshold":140,"hough_threshold_oblique":45,"hough_threshold_horizontal":40,"hough_threshold_vertical":1800,"maxLineGap_oblique":30,"pattern_tolerance":10,"uniform_k_snap":true},"sam":{"segment_width":1300,"K_height":950,"angle":5.0}}`
- full_pipeline: False
- Result: status=ok proxy_scaled=0.4697 band=reject F1=0.039 fill=0.737 elapsed=174.2s

**Selected:** `anchor` (Δproxy=+0.0000, ΔmIoU_offline=0.0). Reason: monotone accept: no round beat anchor scaled proxy

---

## 3-7 (continuous)

### Round 1 CoT (2026-09-12T23:03:29.563943)
- Observation: F1@15=0.172 fill=0.767 nan=0.165 fallback=1.00. Uniform-K continuous; correspondence weak when Hough falls back.
- Failure mode: `f_detection_fallback / low line↔boundary F1`
- Rationale: Moderate Hough (not ultra-low) to recover real joints without flooding spurious lines that tank F1; keep uniform_k_snap.
- Overlay: `{"denoising":{"mask_r_low":2.85,"mask_r_high":3.05,"mask_theta_low":1.5,"mask_theta_high":17.0},"enhancing":{"curvature_threshold":0.0008},"detecting":{"binary_threshold":120,"hough_threshold_oblique":35,"hough_threshold_horizontal":35,"hough_threshold_vertical":1600,"maxLineGap_oblique":40,"pattern_tolerance":12,"uniform_k_snap":true},"sam":{"segment_width":1200,"K_height":900,"angle":6.0}}`
- full_pipeline: False
- Result: status=ok proxy_scaled=0.5289 band=refine F1=0.148 fill=0.767 elapsed=187.1s
### Round 2 CoT (2026-09-12T23:06:37.848517)
- Observation: F1=0.148 fill=0.767. Try wider mask + lower binary.
- Failure mode: `f_depth_incomplete or weak edges`
- Rationale: Widen retention + slightly lower Hough to catch more joint evidence.
- Overlay: `{"denoising":{"mask_r_low":2.75,"mask_r_high":3.12,"mask_theta_low":1.2,"mask_theta_high":18.0},"enhancing":{"curvature_threshold":0.0012},"detecting":{"binary_threshold":105,"hough_threshold_oblique":28,"hough_threshold_horizontal":28,"hough_threshold_vertical":2000,"maxLineGap_oblique":55,"pattern_tolerance":15,"uniform_k_snap":true},"sam":{"segment_width":1150,"K_height":850,"angle":7.0}}`
- full_pipeline: False
- Result: status=ok proxy_scaled=0.5252 band=refine F1=0.140 fill=0.770 elapsed=190.1s
### Round 3 CoT (2026-09-12T23:09:49.139041)
- Observation: R3 alternate SAM/Hough; F1=0.140 fill=0.770.
- Failure mode: `f_sam_crop_mismatch`
- Rationale: Cleaner edges (higher binary) + larger SAM window.
- Overlay: `{"denoising":{"mask_r_low":2.9,"mask_r_high":3.1,"mask_theta_low":1.8,"mask_theta_high":16.5},"enhancing":{"curvature_threshold":0.0005},"detecting":{"binary_threshold":140,"hough_threshold_oblique":45,"hough_threshold_horizontal":40,"hough_threshold_vertical":1800,"maxLineGap_oblique":30,"pattern_tolerance":10,"uniform_k_snap":true},"sam":{"segment_width":1300,"K_height":950,"angle":5.0}}`
- full_pipeline: False
- Result: status=ok proxy_scaled=0.4806 band=reject F1=0.084 fill=0.723 elapsed=168.0s

**Selected:** `anchor` (Δproxy=+0.0000, ΔmIoU_offline=0.0). Reason: monotone accept: no round beat anchor scaled proxy

---

## 3-8 (continuous)

### Round 1 CoT (2026-09-12T23:12:52.854785)
- Observation: F1@15=0.302 fill=0.597 nan=0.182 fallback=1.00. Uniform-K continuous; correspondence weak when Hough falls back.
- Failure mode: `f_detection_fallback / low line↔boundary F1`
- Rationale: Moderate Hough (not ultra-low) to recover real joints without flooding spurious lines that tank F1; keep uniform_k_snap.
- Overlay: `{"denoising":{"mask_r_low":2.85,"mask_r_high":3.05,"mask_theta_low":1.5,"mask_theta_high":17.0},"enhancing":{"curvature_threshold":0.0008},"detecting":{"binary_threshold":120,"hough_threshold_oblique":35,"hough_threshold_horizontal":35,"hough_threshold_vertical":1600,"maxLineGap_oblique":40,"pattern_tolerance":12,"uniform_k_snap":true},"sam":{"segment_width":1200,"K_height":900,"angle":6.0}}`
- full_pipeline: False
- Result: status=ok proxy_scaled=0.5421 band=refine F1=0.257 fill=0.603 elapsed=190.0s
### Round 2 CoT (2026-09-12T23:16:04.265156)
- Observation: Residual unlocked; F1=0.257. Probe stage-1 seed.
- Failure mode: `f_centreline_residual`
- Rationale: Stage-1 seed probe (seed 0) with frozen later stages from overlay materialization of base+seed.
- Overlay: `{"unfolding":{"random_seed":0}}`
- full_pipeline: True
- Result: status=ok proxy_scaled=0.4061 band=reject F1=0.120 fill=0.471 elapsed=194.1s
### Round 3 CoT (2026-09-12T23:19:19.764424)
- Observation: Combine seed 5 with detection recipe; F1=0.120.
- Failure mode: `f_centreline_residual + weak correspondence`
- Rationale: Combined stage-1 seed 5 + R1 detection recipe.
- Overlay: `{"unfolding":{"random_seed":5},"denoising":{"mask_r_low":2.85,"mask_r_high":3.05,"mask_theta_low":1.5,"mask_theta_high":17.0},"enhancing":{"curvature_threshold":0.0008},"detecting":{"binary_threshold":120,"hough_threshold_oblique":35,"hough_threshold_horizontal":35,"hough_threshold_vertical":1600,"maxLineGap_oblique":40,"pattern_tolerance":12,"uniform_k_snap":true},"sam":{"segment_width":1200,"K_height":900,"angle":6.0}}`
- full_pipeline: True
- Result: status=ok proxy_scaled=0.5312 band=refine F1=0.194 fill=0.665 elapsed=198.5s

**Selected:** `anchor` (Δproxy=+0.0000, ΔmIoU_offline=0.0). Reason: monotone accept: no round beat anchor scaled proxy

---

## 3-10 (continuous)

### Round 1 CoT (2026-09-12T23:22:55.581495)
- Observation: F1@15=0.287 fill=0.698 nan=0.142 fallback=1.00. Uniform-K continuous; correspondence weak when Hough falls back.
- Failure mode: `f_detection_fallback / low line↔boundary F1`
- Rationale: Moderate Hough (not ultra-low) to recover real joints without flooding spurious lines that tank F1; keep uniform_k_snap.
- Overlay: `{"denoising":{"mask_r_low":2.85,"mask_r_high":3.05,"mask_theta_low":1.5,"mask_theta_high":17.0},"enhancing":{"curvature_threshold":0.0008},"detecting":{"binary_threshold":120,"hough_threshold_oblique":35,"hough_threshold_horizontal":35,"hough_threshold_vertical":1600,"maxLineGap_oblique":40,"pattern_tolerance":12,"uniform_k_snap":true},"sam":{"segment_width":1200,"K_height":900,"angle":6.0}}`
- full_pipeline: False
- Result: status=ok proxy_scaled=0.5633 band=refine F1=0.234 fill=0.701 elapsed=190.2s
### Round 2 CoT (2026-09-12T23:26:07.171798)
- Observation: Residual unlocked; F1=0.234. Probe stage-1 seed.
- Failure mode: `f_centreline_residual`
- Rationale: Stage-1 seed probe (seed 0) with frozen later stages from overlay materialization of base+seed.
- Overlay: `{"unfolding":{"random_seed":0}}`
- full_pipeline: True
- Result: status=ok proxy_scaled=0.5580 band=refine F1=0.230 fill=0.698 elapsed=198.5s
### Round 3 CoT (2026-09-12T23:29:27.009412)
- Observation: Combine seed 5 with detection recipe; F1=0.230.
- Failure mode: `f_centreline_residual + weak correspondence`
- Rationale: Combined stage-1 seed 5 + R1 detection recipe.
- Overlay: `{"unfolding":{"random_seed":5},"denoising":{"mask_r_low":2.85,"mask_r_high":3.05,"mask_theta_low":1.5,"mask_theta_high":17.0},"enhancing":{"curvature_threshold":0.0008},"detecting":{"binary_threshold":120,"hough_threshold_oblique":35,"hough_threshold_horizontal":35,"hough_threshold_vertical":1600,"maxLineGap_oblique":40,"pattern_tolerance":12,"uniform_k_snap":true},"sam":{"segment_width":1200,"K_height":900,"angle":6.0}}`
- full_pipeline: True
- Result: status=ok proxy_scaled=0.5744 band=refine F1=0.252 fill=0.704 elapsed=200.6s

**Selected:** `anchor` (Δproxy=+0.0000, ΔmIoU_offline=0.0). Reason: monotone accept: no round beat anchor scaled proxy

---

## 3-9 (continuous)

### Round 1 CoT (2026-09-12T23:32:58.561270)
- Observation: F1@15=0.364 fill=0.729 nan=0.131 fallback=1.00. Uniform-K continuous; correspondence weak when Hough falls back.
- Failure mode: `f_detection_fallback / low line↔boundary F1`
- Rationale: Moderate Hough (not ultra-low) to recover real joints without flooding spurious lines that tank F1; keep uniform_k_snap.
- Overlay: `{"denoising":{"mask_r_low":2.85,"mask_r_high":3.05,"mask_theta_low":1.5,"mask_theta_high":17.0},"enhancing":{"curvature_threshold":0.0008},"detecting":{"binary_threshold":120,"hough_threshold_oblique":35,"hough_threshold_horizontal":35,"hough_threshold_vertical":1600,"maxLineGap_oblique":40,"pattern_tolerance":12,"uniform_k_snap":true},"sam":{"segment_width":1200,"K_height":900,"angle":6.0}}`
- full_pipeline: False
- Result: status=ok proxy_scaled=0.6334 band=refine F1=0.345 fill=0.731 elapsed=191.6s
### Round 2 CoT (2026-09-12T23:36:11.575892)
- Observation: F1=0.345 fill=0.731. Try wider mask + lower binary.
- Failure mode: `f_depth_incomplete or weak edges`
- Rationale: Widen retention + slightly lower Hough to catch more joint evidence.
- Overlay: `{"denoising":{"mask_r_low":2.75,"mask_r_high":3.12,"mask_theta_low":1.2,"mask_theta_high":18.0},"enhancing":{"curvature_threshold":0.0012},"detecting":{"binary_threshold":105,"hough_threshold_oblique":28,"hough_threshold_horizontal":28,"hough_threshold_vertical":2000,"maxLineGap_oblique":55,"pattern_tolerance":15,"uniform_k_snap":true},"sam":{"segment_width":1150,"K_height":850,"angle":7.0}}`
- full_pipeline: False
- Result: status=ok proxy_scaled=0.5679 band=refine F1=0.228 fill=0.725 elapsed=192.8s
### Round 3 CoT (2026-09-12T23:39:25.718018)
- Observation: R3 alternate SAM/Hough; F1=0.228 fill=0.725.
- Failure mode: `f_sam_crop_mismatch`
- Rationale: Cleaner edges (higher binary) + larger SAM window.
- Overlay: `{"denoising":{"mask_r_low":2.9,"mask_r_high":3.1,"mask_theta_low":1.8,"mask_theta_high":16.5},"enhancing":{"curvature_threshold":0.0005},"detecting":{"binary_threshold":140,"hough_threshold_oblique":45,"hough_threshold_horizontal":40,"hough_threshold_vertical":1800,"maxLineGap_oblique":30,"pattern_tolerance":10,"uniform_k_snap":true},"sam":{"segment_width":1300,"K_height":950,"angle":5.0}}`
- full_pipeline: False
- Result: status=ok proxy_scaled=0.5483 band=refine F1=0.205 fill=0.696 elapsed=172.8s

**Selected:** `anchor` (Δproxy=+0.0000, ΔmIoU_offline=0.0). Reason: monotone accept: no round beat anchor scaled proxy

---

## 3-6 (continuous)

### Round 1 CoT (2026-09-12T23:42:41.445108)
- Observation: F1@15=0.467 fill=0.649 nan=0.105 fallback=1.00. Uniform-K continuous; correspondence weak when Hough falls back.
- Failure mode: `f_detection_fallback / low line↔boundary F1`
- Rationale: Moderate Hough (not ultra-low) to recover real joints without flooding spurious lines that tank F1; keep uniform_k_snap.
- Overlay: `{"denoising":{"mask_r_low":2.85,"mask_r_high":3.05,"mask_theta_low":1.5,"mask_theta_high":17.0},"enhancing":{"curvature_threshold":0.0008},"detecting":{"binary_threshold":120,"hough_threshold_oblique":35,"hough_threshold_horizontal":35,"hough_threshold_vertical":1600,"maxLineGap_oblique":40,"pattern_tolerance":12,"uniform_k_snap":true},"sam":{"segment_width":1200,"K_height":900,"angle":6.0}}`
- full_pipeline: False
- Result: status=ok proxy_scaled=0.6637 band=refine F1=0.427 fill=0.654 elapsed=192.4s
### Round 2 CoT (2026-09-12T23:45:55.284932)
- Observation: F1=0.427 fill=0.654. Try wider mask + lower binary.
- Failure mode: `f_depth_incomplete or weak edges`
- Rationale: Widen retention + slightly lower Hough to catch more joint evidence.
- Overlay: `{"denoising":{"mask_r_low":2.75,"mask_r_high":3.12,"mask_theta_low":1.2,"mask_theta_high":18.0},"enhancing":{"curvature_threshold":0.0012},"detecting":{"binary_threshold":105,"hough_threshold_oblique":28,"hough_threshold_horizontal":28,"hough_threshold_vertical":2000,"maxLineGap_oblique":55,"pattern_tolerance":15,"uniform_k_snap":true},"sam":{"segment_width":1150,"K_height":850,"angle":7.0}}`
- full_pipeline: False
- Result: status=ok proxy_scaled=0.7254 band=accept F1=0.536 fill=0.663 elapsed=194.3s
### Round 3 CoT (2026-09-12T23:49:11.094795)
- Observation: R3 alternate SAM/Hough; F1=0.536 fill=0.663.
- Failure mode: `f_sam_crop_mismatch`
- Rationale: Cleaner edges (higher binary) + larger SAM window.
- Overlay: `{"denoising":{"mask_r_low":2.9,"mask_r_high":3.1,"mask_theta_low":1.8,"mask_theta_high":16.5},"enhancing":{"curvature_threshold":0.0005},"detecting":{"binary_threshold":140,"hough_threshold_oblique":45,"hough_threshold_horizontal":40,"hough_threshold_vertical":1800,"maxLineGap_oblique":30,"pattern_tolerance":10,"uniform_k_snap":true},"sam":{"segment_width":1300,"K_height":950,"angle":5.0}}`
- full_pipeline: False
- Result: status=ok proxy_scaled=0.5779 band=refine F1=0.289 fill=0.616 elapsed=172.7s

**Selected:** `round2` (Δproxy=+0.0441, ΔmIoU_offline=-0.001). Reason: best proxy 0.7254; 1 within 0.01 margin; residual tiebreak -> round2

---

## 4-3 (complex)

### Round 1 CoT (2026-09-12T23:52:38.158665)
- Observation: F1@15=0.191 fill=0.717 nan=0.245 fallback=0.40. Complex irregular K; widen mask and raise vertical Hough hard.
- Failure mode: `f_detection_sparse / complex layout mismatch`
- Rationale: 4-4 cursor2 coordinated recipe: widen mask, hard vertical, live SAM sizes.
- Overlay: `{"denoising":{"mask_r_low":3.55,"mask_r_high":3.95},"enhancing":{"curvature_threshold":0.001},"detecting":{"binary_threshold":120,"hough_threshold_oblique":40,"hough_threshold_horizontal":30,"hough_threshold_vertical":3500,"maxLineGap_oblique":70,"maxLineGap_horizontal":20,"pattern_tolerance":12},"sam":{"segment_width":1700,"K_height":1150,"angle":9.0}}`
- full_pipeline: False
- Result: status=ok proxy_scaled=0.5614 band=refine F1=0.261 fill=0.722 elapsed=254.9s
### Round 2 CoT (2026-09-12T23:57:00.696304)
- Observation: Residual unlocked (True); F1=0.261. Stage-1 seed probe.
- Failure mode: `f_centreline_residual`
- Rationale: Stage-1 unlock seed 1 (sibling of healthy complex anchors).
- Overlay: `{"unfolding":{"random_seed":1}}`
- full_pipeline: True
- Result: status=ok proxy_scaled=0.5710 band=refine F1=0.278 fill=0.719 elapsed=264.9s
### Round 3 CoT (2026-09-13T00:01:33.116366)
- Observation: Combine seed 3 with R1 recipe; F1=0.278.
- Failure mode: `f_centreline_residual + sparse detection`
- Rationale: Seed 3 + R1 detection/SAM recipe.
- Overlay: `{"unfolding":{"random_seed":3},"denoising":{"mask_r_low":3.55,"mask_r_high":3.95},"enhancing":{"curvature_threshold":0.001},"detecting":{"binary_threshold":120,"hough_threshold_oblique":40,"hough_threshold_horizontal":30,"hough_threshold_vertical":3500,"maxLineGap_oblique":70,"maxLineGap_horizontal":20,"pattern_tolerance":12},"sam":{"segment_width":1700,"K_height":1150,"angle":9.0}}`
- full_pipeline: True
- Result: status=ok proxy_scaled=0.5915 band=refine F1=0.308 fill=0.726 elapsed=273.4s

**Selected:** `round3` (Δproxy=+0.0713, ΔmIoU_offline=0.024). Reason: best proxy 0.5915; 1 within 0.01 margin; residual tiebreak -> round3

---

## 4-2 (complex)

### Round 1 CoT (2026-09-13T00:07:01.038196)
- Observation: F1@15=0.213 fill=0.732 nan=0.209 fallback=0.40. Complex irregular K; widen mask and raise vertical Hough hard.
- Failure mode: `f_detection_sparse / complex layout mismatch`
- Rationale: 4-4 cursor2 coordinated recipe: widen mask, hard vertical, live SAM sizes.
- Overlay: `{"denoising":{"mask_r_low":3.55,"mask_r_high":3.95},"enhancing":{"curvature_threshold":0.001},"detecting":{"binary_threshold":120,"hough_threshold_oblique":40,"hough_threshold_horizontal":30,"hough_threshold_vertical":3500,"maxLineGap_oblique":70,"maxLineGap_horizontal":20,"pattern_tolerance":12},"sam":{"segment_width":1700,"K_height":1150,"angle":9.0}}`
- full_pipeline: False
- Result: status=ok proxy_scaled=0.6431 band=refine F1=0.392 fill=0.735 elapsed=255.7s
### Round 2 CoT (2026-09-13T00:11:24.237310)
- Observation: F1=0.392 fill=0.735. Alternate: looser oblique, taller K.
- Failure mode: `f_k_height_mismatch`
- Rationale: Widen SAM K_height/width; slightly looser oblique Hough.
- Overlay: `{"denoising":{"mask_r_low":3.6,"mask_r_high":4.0},"enhancing":{"curvature_threshold":0.0006},"detecting":{"binary_threshold":110,"hough_threshold_oblique":32,"hough_threshold_horizontal":28,"hough_threshold_vertical":2800,"maxLineGap_oblique":75,"maxLineGap_horizontal":15,"pattern_tolerance":15},"sam":{"segment_width":1900,"K_height":1300,"angle":10.0}}`
- full_pipeline: False
- Result: status=ok proxy_scaled=0.6870 band=refine F1=0.474 fill=0.734 elapsed=246.6s
### Round 3 CoT (2026-09-13T00:15:38.242357)
- Observation: R3: tighter Hough + smaller SAM; F1=0.474.
- Failure mode: `f_spurious_lines`
- Rationale: Suppress spurious joints; keep SAM near family centre.
- Overlay: `{"denoising":{"mask_r_low":3.65,"mask_r_high":3.9},"enhancing":{"curvature_threshold":0.0015},"detecting":{"binary_threshold":135,"hough_threshold_oblique":55,"hough_threshold_horizontal":45,"hough_threshold_vertical":4000,"maxLineGap_oblique":50,"maxLineGap_horizontal":10,"pattern_tolerance":8},"sam":{"segment_width":1600,"K_height":1100,"angle":8.0}}`
- full_pipeline: False
- Result: status=ok proxy_scaled=0.6462 band=refine F1=0.400 fill=0.730 elapsed=257.4s

**Selected:** `round2` (Δproxy=+0.1435, ΔmIoU_offline=0.039). Reason: best proxy 0.6870; 1 within 0.01 margin; residual tiebreak -> round2

---

## 4-1 (complex)

### Round 1 CoT (2026-09-13T00:21:07.150264)
- Observation: F1@15=0.225 fill=0.749 nan=0.223 fallback=0.60. Complex irregular K; widen mask and raise vertical Hough hard.
- Failure mode: `f_detection_sparse / complex layout mismatch`
- Rationale: 4-4 cursor2 coordinated recipe: widen mask, hard vertical, live SAM sizes.
- Overlay: `{"denoising":{"mask_r_low":3.55,"mask_r_high":3.95},"enhancing":{"curvature_threshold":0.001},"detecting":{"binary_threshold":120,"hough_threshold_oblique":40,"hough_threshold_horizontal":30,"hough_threshold_vertical":3500,"maxLineGap_oblique":70,"maxLineGap_horizontal":20,"pattern_tolerance":12},"sam":{"segment_width":1700,"K_height":1150,"angle":9.0}}`
- full_pipeline: False
- Result: status=ok proxy_scaled=0.6208 band=refine F1=0.347 fill=0.754 elapsed=252.3s
### Round 2 CoT (2026-09-13T00:25:28.396364)
- Observation: F1=0.347 fill=0.754. Alternate: looser oblique, taller K.
- Failure mode: `f_k_height_mismatch`
- Rationale: Widen SAM K_height/width; slightly looser oblique Hough.
- Overlay: `{"denoising":{"mask_r_low":3.6,"mask_r_high":4.0},"enhancing":{"curvature_threshold":0.0006},"detecting":{"binary_threshold":110,"hough_threshold_oblique":32,"hough_threshold_horizontal":28,"hough_threshold_vertical":2800,"maxLineGap_oblique":75,"maxLineGap_horizontal":15,"pattern_tolerance":15},"sam":{"segment_width":1900,"K_height":1300,"angle":10.0}}`
- full_pipeline: False
- Result: status=ok proxy_scaled=0.5967 band=refine F1=0.305 fill=0.752 elapsed=244.9s
### Round 3 CoT (2026-09-13T00:29:42.089626)
- Observation: R3: tighter Hough + smaller SAM; F1=0.305.
- Failure mode: `f_spurious_lines`
- Rationale: Suppress spurious joints; keep SAM near family centre.
- Overlay: `{"denoising":{"mask_r_low":3.65,"mask_r_high":3.9},"enhancing":{"curvature_threshold":0.0015},"detecting":{"binary_threshold":135,"hough_threshold_oblique":55,"hough_threshold_horizontal":45,"hough_threshold_vertical":4000,"maxLineGap_oblique":50,"maxLineGap_horizontal":10,"pattern_tolerance":8},"sam":{"segment_width":1600,"K_height":1100,"angle":8.0}}`
- full_pipeline: False
- Result: status=ok proxy_scaled=0.5876 band=refine F1=0.289 fill=0.747 elapsed=253.2s

**Selected:** `round1` (Δproxy=+0.0690, ΔmIoU_offline=0.018). Reason: best proxy 0.6208; 1 within 0.01 margin; residual tiebreak -> round1

---

## 4-5 (complex)

### Round 1 CoT (2026-09-13T00:35:07.319439)
- Observation: F1@15=0.334 fill=0.735 nan=0.216 fallback=0.40. Complex irregular K; widen mask and raise vertical Hough hard.
- Failure mode: `f_detection_sparse / complex layout mismatch`
- Rationale: 4-4 cursor2 coordinated recipe: widen mask, hard vertical, live SAM sizes.
- Overlay: `{"denoising":{"mask_r_low":3.55,"mask_r_high":3.95},"enhancing":{"curvature_threshold":0.001},"detecting":{"binary_threshold":120,"hough_threshold_oblique":40,"hough_threshold_horizontal":30,"hough_threshold_vertical":3500,"maxLineGap_oblique":70,"maxLineGap_horizontal":20,"pattern_tolerance":12},"sam":{"segment_width":1700,"K_height":1150,"angle":9.0}}`
- full_pipeline: False
- Result: status=ok proxy_scaled=0.6389 band=refine F1=0.384 fill=0.739 elapsed=257.3s
### Round 2 CoT (2026-09-13T00:39:32.157478)
- Observation: F1=0.384 fill=0.739. Alternate: looser oblique, taller K.
- Failure mode: `f_k_height_mismatch`
- Rationale: Widen SAM K_height/width; slightly looser oblique Hough.
- Overlay: `{"denoising":{"mask_r_low":3.6,"mask_r_high":4.0},"enhancing":{"curvature_threshold":0.0006},"detecting":{"binary_threshold":110,"hough_threshold_oblique":32,"hough_threshold_horizontal":28,"hough_threshold_vertical":2800,"maxLineGap_oblique":75,"maxLineGap_horizontal":15,"pattern_tolerance":15},"sam":{"segment_width":1900,"K_height":1300,"angle":10.0}}`
- full_pipeline: False
- Result: status=ok proxy_scaled=0.5990 band=refine F1=0.311 fill=0.740 elapsed=247.4s
### Round 3 CoT (2026-09-13T00:43:47.047565)
- Observation: R3: tighter Hough + smaller SAM; F1=0.311.
- Failure mode: `f_spurious_lines`
- Rationale: Suppress spurious joints; keep SAM near family centre.
- Overlay: `{"denoising":{"mask_r_low":3.65,"mask_r_high":3.9},"enhancing":{"curvature_threshold":0.0015},"detecting":{"binary_threshold":135,"hough_threshold_oblique":55,"hough_threshold_horizontal":45,"hough_threshold_vertical":4000,"maxLineGap_oblique":50,"maxLineGap_horizontal":10,"pattern_tolerance":8},"sam":{"segment_width":1600,"K_height":1100,"angle":8.0}}`
- full_pipeline: False
- Result: status=ok proxy_scaled=0.5871 band=refine F1=0.293 fill=0.732 elapsed=257.4s

**Selected:** `round1` (Δproxy=+0.0295, ΔmIoU_offline=0.025). Reason: best proxy 0.6389; 1 within 0.01 margin; residual tiebreak -> round1

---

## 5-5 (complex)

### Round 1 CoT (2026-09-13T00:49:10.738191)
- Observation: F1@15=0.316 fill=0.756 nan=0.193 fallback=0.20. Complex irregular K; widen mask and raise vertical Hough hard.
- Failure mode: `f_detection_sparse / complex layout mismatch`
- Rationale: 4-4 cursor2 coordinated recipe: widen mask, hard vertical, live SAM sizes.
- Overlay: `{"denoising":{"mask_r_low":3.55,"mask_r_high":3.95},"enhancing":{"curvature_threshold":0.001},"detecting":{"binary_threshold":120,"hough_threshold_oblique":40,"hough_threshold_horizontal":30,"hough_threshold_vertical":3500,"maxLineGap_oblique":70,"maxLineGap_horizontal":20,"pattern_tolerance":12},"sam":{"segment_width":1700,"K_height":1150,"angle":9.0}}`
- full_pipeline: False
- Result: status=ok proxy_scaled=0.6422 band=refine F1=0.372 fill=0.759 elapsed=260.7s
### Round 2 CoT (2026-09-13T00:53:39.222428)
- Observation: F1=0.372 fill=0.759. Alternate: looser oblique, taller K.
- Failure mode: `f_k_height_mismatch`
- Rationale: Widen SAM K_height/width; slightly looser oblique Hough.
- Overlay: `{"denoising":{"mask_r_low":3.6,"mask_r_high":4.0},"enhancing":{"curvature_threshold":0.0006},"detecting":{"binary_threshold":110,"hough_threshold_oblique":32,"hough_threshold_horizontal":28,"hough_threshold_vertical":2800,"maxLineGap_oblique":75,"maxLineGap_horizontal":15,"pattern_tolerance":15},"sam":{"segment_width":1900,"K_height":1300,"angle":10.0}}`
- full_pipeline: False
- Result: status=ok proxy_scaled=0.6677 band=refine F1=0.422 fill=0.756 elapsed=251.4s
### Round 3 CoT (2026-09-13T00:57:58.495993)
- Observation: R3: tighter Hough + smaller SAM; F1=0.422.
- Failure mode: `f_spurious_lines`
- Rationale: Suppress spurious joints; keep SAM near family centre.
- Overlay: `{"denoising":{"mask_r_low":3.65,"mask_r_high":3.9},"enhancing":{"curvature_threshold":0.0015},"detecting":{"binary_threshold":135,"hough_threshold_oblique":55,"hough_threshold_horizontal":45,"hough_threshold_vertical":4000,"maxLineGap_oblique":50,"maxLineGap_horizontal":10,"pattern_tolerance":8},"sam":{"segment_width":1600,"K_height":1100,"angle":8.0}}`
- full_pipeline: False
- Result: status=ok proxy_scaled=0.6657 band=refine F1=0.418 fill=0.753 elapsed=263.9s

**Selected:** `round2` (Δproxy=+0.0579, ΔmIoU_offline=-0.005). Reason: best proxy 0.6677; 2 within 0.01 margin; residual tiebreak -> round2

---

## 5-3 (complex)

### Round 1 CoT (2026-09-13T01:03:33.689454)
- Observation: F1@15=0.459 fill=0.737 nan=0.201 fallback=0.30. Complex irregular K; widen mask and raise vertical Hough hard.
- Failure mode: `f_detection_sparse / complex layout mismatch`
- Rationale: 4-4 cursor2 coordinated recipe: widen mask, hard vertical, live SAM sizes.
- Overlay: `{"denoising":{"mask_r_low":3.55,"mask_r_high":3.95},"enhancing":{"curvature_threshold":0.001},"detecting":{"binary_threshold":120,"hough_threshold_oblique":40,"hough_threshold_horizontal":30,"hough_threshold_vertical":3500,"maxLineGap_oblique":70,"maxLineGap_horizontal":20,"pattern_tolerance":12},"sam":{"segment_width":1700,"K_height":1150,"angle":9.0}}`
- full_pipeline: False
- Result: status=ok proxy_scaled=0.6675 band=refine F1=0.426 fill=0.747 elapsed=260.3s
### Round 2 CoT (2026-09-13T01:08:01.771853)
- Observation: F1=0.426 fill=0.747. Alternate: looser oblique, taller K.
- Failure mode: `f_k_height_mismatch`
- Rationale: Widen SAM K_height/width; slightly looser oblique Hough.
- Overlay: `{"denoising":{"mask_r_low":3.6,"mask_r_high":4.0},"enhancing":{"curvature_threshold":0.0006},"detecting":{"binary_threshold":110,"hough_threshold_oblique":32,"hough_threshold_horizontal":28,"hough_threshold_vertical":2800,"maxLineGap_oblique":75,"maxLineGap_horizontal":15,"pattern_tolerance":15},"sam":{"segment_width":1900,"K_height":1300,"angle":10.0}}`
- full_pipeline: False
- Result: status=ok proxy_scaled=0.6619 band=refine F1=0.416 fill=0.747 elapsed=252.4s
### Round 3 CoT (2026-09-13T01:12:22.037355)
- Observation: R3: tighter Hough + smaller SAM; F1=0.416.
- Failure mode: `f_spurious_lines`
- Rationale: Suppress spurious joints; keep SAM near family centre.
- Overlay: `{"denoising":{"mask_r_low":3.65,"mask_r_high":3.9},"enhancing":{"curvature_threshold":0.0015},"detecting":{"binary_threshold":135,"hough_threshold_oblique":55,"hough_threshold_horizontal":45,"hough_threshold_vertical":4000,"maxLineGap_oblique":50,"maxLineGap_horizontal":10,"pattern_tolerance":8},"sam":{"segment_width":1600,"K_height":1100,"angle":8.0}}`
- full_pipeline: False
- Result: status=ok proxy_scaled=0.6417 band=refine F1=0.387 fill=0.733 elapsed=260.6s

**Selected:** `anchor` (Δproxy=+0.0000, ΔmIoU_offline=0.0). Reason: monotone accept: no round beat anchor scaled proxy

---

## 5-2 (complex)

### Round 1 CoT (2026-09-13T01:17:56.805257)
- Observation: F1@15=0.453 fill=0.751 nan=0.194 fallback=0.40. Complex irregular K; widen mask and raise vertical Hough hard.
- Failure mode: `f_detection_sparse / complex layout mismatch`
- Rationale: 4-4 cursor2 coordinated recipe: widen mask, hard vertical, live SAM sizes.
- Overlay: `{"denoising":{"mask_r_low":3.55,"mask_r_high":3.95},"enhancing":{"curvature_threshold":0.001},"detecting":{"binary_threshold":120,"hough_threshold_oblique":40,"hough_threshold_horizontal":30,"hough_threshold_vertical":3500,"maxLineGap_oblique":70,"maxLineGap_horizontal":20,"pattern_tolerance":12},"sam":{"segment_width":1700,"K_height":1150,"angle":9.0}}`
- full_pipeline: False
- Result: status=ok proxy_scaled=0.6243 band=refine F1=0.340 fill=0.757 elapsed=261.7s
### Round 2 CoT (2026-09-13T01:22:26.215195)
- Observation: F1=0.340 fill=0.757. Alternate: looser oblique, taller K.
- Failure mode: `f_k_height_mismatch`
- Rationale: Widen SAM K_height/width; slightly looser oblique Hough.
- Overlay: `{"denoising":{"mask_r_low":3.6,"mask_r_high":4.0},"enhancing":{"curvature_threshold":0.0006},"detecting":{"binary_threshold":110,"hough_threshold_oblique":32,"hough_threshold_horizontal":28,"hough_threshold_vertical":2800,"maxLineGap_oblique":75,"maxLineGap_horizontal":15,"pattern_tolerance":15},"sam":{"segment_width":1900,"K_height":1300,"angle":10.0}}`
- full_pipeline: False
- Result: status=ok proxy_scaled=0.7031 band=accept F1=0.489 fill=0.752 elapsed=252.2s
### Round 3 CoT (2026-09-13T01:26:46.358272)
- Observation: R3: tighter Hough + smaller SAM; F1=0.489.
- Failure mode: `f_spurious_lines`
- Rationale: Suppress spurious joints; keep SAM near family centre.
- Overlay: `{"denoising":{"mask_r_low":3.65,"mask_r_high":3.9},"enhancing":{"curvature_threshold":0.0015},"detecting":{"binary_threshold":135,"hough_threshold_oblique":55,"hough_threshold_horizontal":45,"hough_threshold_vertical":4000,"maxLineGap_oblique":50,"maxLineGap_horizontal":10,"pattern_tolerance":8},"sam":{"segment_width":1600,"K_height":1100,"angle":8.0}}`
- full_pipeline: False
- Result: status=ok proxy_scaled=0.6647 band=refine F1=0.418 fill=0.749 elapsed=262.9s

**Selected:** `round2` (Δproxy=+0.0202, ΔmIoU_offline=-0.012). Reason: best proxy 0.7031; 1 within 0.01 margin; residual tiebreak -> round2

---

## 5-4 (complex)

### Round 1 CoT (2026-09-13T01:32:19.652651)
- Observation: F1@15=0.467 fill=0.760 nan=0.198 fallback=0.30. Complex irregular K; widen mask and raise vertical Hough hard.
- Failure mode: `f_detection_sparse / complex layout mismatch`
- Rationale: 4-4 cursor2 coordinated recipe: widen mask, hard vertical, live SAM sizes.
- Overlay: `{"denoising":{"mask_r_low":3.55,"mask_r_high":3.95},"enhancing":{"curvature_threshold":0.001},"detecting":{"binary_threshold":120,"hough_threshold_oblique":40,"hough_threshold_horizontal":30,"hough_threshold_vertical":3500,"maxLineGap_oblique":70,"maxLineGap_horizontal":20,"pattern_tolerance":12},"sam":{"segment_width":1700,"K_height":1150,"angle":9.0}}`
- full_pipeline: False
- Result: status=ok proxy_scaled=0.6869 band=refine F1=0.454 fill=0.763 elapsed=264.2s
### Round 2 CoT (2026-09-13T01:36:51.489882)
- Observation: F1=0.454 fill=0.763. Alternate: looser oblique, taller K.
- Failure mode: `f_k_height_mismatch`
- Rationale: Widen SAM K_height/width; slightly looser oblique Hough.
- Overlay: `{"denoising":{"mask_r_low":3.6,"mask_r_high":4.0},"enhancing":{"curvature_threshold":0.0006},"detecting":{"binary_threshold":110,"hough_threshold_oblique":32,"hough_threshold_horizontal":28,"hough_threshold_vertical":2800,"maxLineGap_oblique":75,"maxLineGap_horizontal":15,"pattern_tolerance":15},"sam":{"segment_width":1900,"K_height":1300,"angle":10.0}}`
- full_pipeline: False
- Result: status=ok proxy_scaled=0.6364 band=refine F1=0.364 fill=0.761 elapsed=254.9s
### Round 3 CoT (2026-09-13T01:41:14.228681)
- Observation: R3: tighter Hough + smaller SAM; F1=0.364.
- Failure mode: `f_spurious_lines`
- Rationale: Suppress spurious joints; keep SAM near family centre.
- Overlay: `{"denoising":{"mask_r_low":3.65,"mask_r_high":3.9},"enhancing":{"curvature_threshold":0.0015},"detecting":{"binary_threshold":135,"hough_threshold_oblique":55,"hough_threshold_horizontal":45,"hough_threshold_vertical":4000,"maxLineGap_oblique":50,"maxLineGap_horizontal":10,"pattern_tolerance":8},"sam":{"segment_width":1600,"K_height":1100,"angle":8.0}}`
- full_pipeline: False
- Result: status=ok proxy_scaled=0.6582 band=refine F1=0.404 fill=0.757 elapsed=266.0s

**Selected:** `anchor` (Δproxy=+0.0000, ΔmIoU_offline=0.0). Reason: monotone accept: no round beat anchor scaled proxy
