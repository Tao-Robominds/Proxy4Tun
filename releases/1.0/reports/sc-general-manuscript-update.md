# SC-general manuscript update report

## Purpose and status

This document translates the SC-general Stage 2 calibration/holdout experiment
and Stage 3 self-refinement experiment into manuscript-ready structure,
wording, claims, and tables. It is a replacement guide only: no manuscript
`.tex`, figure, or bibliography file has been changed.

The revised evidence has two parts:

1. **SC-general proxy validation.** The K-row-dependent proxy is replaced by a
   four-feature Ridge model containing a layout-general line-to-label
   correspondence measurement.
2. **Deployment-honest refinement.** All anchor runs whose frozen proxy score
   lies in the refinement band \([0.5,0.7]\) are admitted to the campaign
   without using GT mIoU. This produces 22 cases rather than the manuscript's
   nine retrospectively GT-filtered cases.

The revised results support a more defensible mechanism claim than the current
manuscript, but not all current numerical claims survive:

- Cross-family transfer improves substantially: LOFO Spearman rises from the
  legacy value 0.678 to **0.828**.
- The paired holdout ranking remains perfect at **27/27**.
- Absolute holdout fidelity is weaker: Spearman **0.817**, MAE **0.109**,
  compared with the legacy manuscript values 0.827 and 0.086.
- At the old alarm threshold \(0.5\), all 27 degraded runs are detected but
  three anchor runs are also flagged. A threshold of \(0.43\) gives 27/27
  degraded detections and 0/27 anchor false positives on this stress test.
- The Fable-5 proxy-only 22-case refinement panel improves from **0.738 to
  0.768** mean mIoU; replacing those selections in all 27 holdout anchors
  changes the overall mean from **0.722 to 0.746**.
- A retrospective manuscript-style subgroup in which both initial proxy and
  GT mIoU lie in \([0.5,0.7]\) contains six cases and improves from **0.592 to
  0.689** under Fable-5 (deterministic comparison arm: 0.592 to 0.696). This
  remains the strongest observed response region, but GT is required to define
  it and it therefore cannot be the deployment case-selection rule.

### Critical Stage 3 provenance note

Stage 3 now has **two proposal arms** under the same SC-general proxy, GT-blind
context packet, three-round budget, and monotone-accept selection rule:

1. **`scgen-det`** — deterministic family recipes in
   `bo/sc_general/run_campaign.py` (outputs under
   `data/<S>-scgen-refinement/`). Kept as an internal comparison arm.
2. **`fable`** — live Fable-5 (Cursor agent) proposals logged in
   `data/sc-general/stage3/campaign_fable.md` (outputs under
   `data/<S>-scgen-fable-refinement/`). This is the arm that can support
   manuscript LLM self-refinement claims under the SC-general proxy.

**Protocol caveat:** during the loop the Fable proposer does not read
`offline_gt.json`, `performance.md`, or band CSVs. The same agent session had
previously seen aggregate GT for these cases, so the arm is **GT-blind by
protocol**, not by a hard information barrier. Manuscript wording must say so.

Headline Fable numbers (primary for LLM claims):

| Panel | Anchor mIoU | Fable selected | Δ | Det selected (comparison) |
|---|---:|---:|---:|---:|
| Dual mid-band (n=6) | 0.592 | **0.689** | +0.097 | 0.696 |
| Label-free proxy band (n=22) | 0.738 | **0.768** | +0.030 | 0.770 |
| Full 27 holdout anchors | 0.722 | **0.746** | +0.024 | 0.748 |

Sources: `report_fable.md`, `arm_comparison.md`, `region_comparison_fable.csv`.

---

## 1. Recommended claim hierarchy

### Primary claim

> A compact proxy combining preprocessing evidence with layout-general
> line-to-label correspondence can provide a GT-free ranking and bounded
> refinement signal across staggered, continuous, and complex tunnel-lining
> families.

Evidence:

- 120 calibration runs, 40 per family.
- LOFO Spearman 0.828.
- Within-family permutation control: real MAE 0.086 versus
  \(0.196\pm0.008\) after shuffling.
- Paired holdout ranking 27/27.
- Proxy-only Fable-5 refinement panel: 0.738 to 0.768 over 22 cases
  (15/22 rounds accepted).

### Secondary claim

> Refinement benefit is concentrated in outputs whose initial proxy and
> offline GT mIoU are both intermediate.

Evidence (Fable-5 arm):

- Dual mid-band, \(0.5\leq\hat y_0\leq0.7\) and
  \(0.5\leq y_0\leq0.7\): six cases, 0.592 to 0.689, mean change +0.097.
- Five improve, one is unchanged, none worsens.
- Deterministic comparison arm on the same six cases: 0.592 to 0.696
  (+0.104); legacy paper Fable on the same six: mean selected 0.678.
- The dual-band gain remains much larger than the +0.005 mean change among
  the 16 already-good (GT ≥ 0.7) cases in the Fable arm.

This statistical comparison is **exploratory and unadjusted**. The region was
inspected after seeing the experiment, \(n=6\) is small, and multiple possible
regions were compared. Use “strongest observed response region” rather than
“proven optimal region” or “statistically established operating region.”

### Boundary claim

> The proxy is better supported as an ordering/control signal than as an
> absolutely calibrated estimate of mIoU.

Evidence:

- Holdout Spearman 0.817 with subset-bootstrap 95% CI
  \([0.761,0.864]\).
- Holdout MAE 0.109.
- PairRank 27/27.
- At \(\tau=0.5\): 27 TP and 3 FP; at \(\tau\leq0.43\): 27 TP and 0 FP.
- Of 15 Fable cases where refinement was accepted, proxy and GT moved in the
  same direction in 10.

### Claims to avoid

Do not retain these current-manuscript claims for the SC-general model:

- “five-feature proxy” — the deployed model has **four** features.
- “Spearman 0.827 and MAE 0.086” — those belong to the legacy K-row proxy.
- “all degraded runs detected without false alarms at 0.5” — there are three
  anchor false positives at 0.5.
- “nine selected cases improve 0.569 to 0.675” — this belongs to the previous
  proxy/refinement campaign.
- “0.722 to 0.757 over 27 subsets” — the new result is 0.722 to 0.748.
- “family-reference statistics are required by the scoring features” — the
  frozen SC-general lean features are run-intrinsic.
- “K-row structure is the transferable SC mechanism” — it is inapplicable or
  identically zero for much of the staggered/complex data.
- “per-family recalibration is unnecessary” as a general conclusion. The
  per-family comparison is non-significant, but neither approach solves the
  absolute calibration miss.

---

## 2. Abstract

### Proposed replacement abstract

Tunnel-lining segmentation supports point-cloud inspection, but changing
tunnel conditions and scarce reference labels complicate deployment-time
quality assessment. Proxy4Tun estimates segmentation accuracy from
intermediate pipeline measurements using one labelled development subset and
one expert-tuned configuration per lining family. Across three Seg2Tunnel
families, bounded sampling and uncertainty-guided Bayesian exploration produce
120 calibration runs. Feature ablation yields a four-feature Ridge proxy that
combines depth-map completeness and ring-count evidence with segmentation fill
and layout-general correspondence between detected joint lines and predicted
label boundaries. The proxy achieves training Spearman correlation 0.904 and
leave-one-family-out correlation 0.828. On 54 paired runs from 27 held-out
subsets, it achieves Spearman correlation 0.817 (95% CI
\([0.761,0.864]\)), MAE 0.109, and ranks all 27 reference-sibling runs above
their deliberately degraded counterparts. In a deployment-style refinement
experiment, all 22 anchor runs with proxy scores in \([0.5,0.7]\) receive
three GT-blind refinement rounds; proxy-based monotone selection increases
their mean mIoU from 0.738 to 0.770, raising the 27-subset mean from 0.722 to
0.748. A retrospective six-case subgroup with both proxy and offline GT mIoU
in \([0.5,0.7]\) improves from 0.592 to 0.696, suggesting that benefit is
concentrated in genuinely intermediate-quality outputs. These results support
the proxy as a transferable ranking and bounded-refinement signal, while its
absolute calibration and operating thresholds require broader validation.

### Shorter conservative alternative

If the journal imposes a strict abstract word limit, remove the subgroup
sentence and report only the deployment-honest 22-case result. The subgroup
belongs naturally in Results/Discussion because it uses GT retrospectively.

---

## 3. Highlights

Suggested replacements:

1. Proxy4Tun estimates tunnel-lining segmentation quality without labels for
   new scans.
2. A layout-general line-to-label correspondence feature replaces
   family-specific K-row coherence.
3. The four-feature proxy reaches LOFO Spearman 0.828 and ranks all 27 paired
   holdout anchors above their degraded counterparts.
4. Proxy-only selection admits 22 refinement-band cases and raises their mean
   mIoU from 0.738 to 0.770.
5. Retrospective analysis identifies the dual proxy/GT mid-band as the
   strongest observed refinement-response region.

---

## 4. Introduction and contributions

### Conceptual wording

Retain the central research question, but define SC more concretely:

> Preprocessing quality (PQ) describes whether the projection supplies
> sufficiently complete and geometrically plausible evidence. Structure
> coherence (SC) describes whether physical joint evidence in the depth map
> agrees with the boundaries claimed by the produced segmentation. The key SC
> relation is therefore not the regularity of either artefact alone, but their
> correspondence.

### Revised contributions

1. A deployment-label-free quality-control framework that learns a compact
   accuracy proxy from limited offline annotations and run-observable
   intermediate artefacts.
2. A layout-general SC formulation based on typed correspondence between
   detected joint lines and predicted label boundaries, avoiding K-row
   assumptions that do not apply consistently across the three lining
   families.
3. A 120-run calibration and 54-run paired holdout study separating
   cross-family transfer, ranking fidelity, absolute error, and threshold
   behaviour.
4. A deployment-style 22-case self-refinement experiment selected by the
   proxy band alone, with retrospective analysis of where refinement benefit
   is concentrated.

Avoid saying that the new experiment validates unrestricted transfer to new
tunnel projects; all held-out subsets still come from represented families and
the same data collection.

---

## 5. Methodology: revised PQ and SC measurements

### Measurement principle

The current manuscript's family-reference/K-row paragraph should be replaced
with:

> For each completed run, we calculate ten candidate measurements without
> using that run's GT labels. PQ measurements describe projection
> completeness, point support, orientation, and ring-count plausibility. SC
> measurements describe agreement between detected joint evidence and the
> segmentation's label boundaries, together with segmentation coverage and
> cross-ring phase consistency. All measurements are computed from the run's
> own intermediate artefacts; the frozen lean model does not require
> family-reference feature statistics.

### Candidate-feature table

| Group | Measurement | Definition/interpretation | Stage |
|---|---|---|---|
| PQ | Depth-map missing-pixel fraction | Fraction of invalid or missing depth pixels | Enhancement |
| PQ | Denoising retained ratio | Fraction retained after denoising | Denoising |
| PQ | Unfolding residual | Residual of centreline/unfolding fit | Unfolding |
| PQ | Orientation agreement | Absolute agreement between inferred and expected orientation axis | Unfolding |
| PQ | Ring-count error | \(\lvert N_{\mathrm{ring}}-10\rvert\) | Unfolding/detection |
| SC | Correspondence F1@15 | Harmonic mean of detected-line support by label boundaries and boundary support by matching line evidence within 15 px | Detection + segmentation |
| SC | Boundary explained by edge@25 | Fraction of label-boundary evidence explained by the depth-edge map within 25 px | Enhancement + segmentation |
| SC | Symmetric line-boundary Chamfer distance | Symmetric distance between detected joint pixels and label-boundary pixels | Detection + segmentation |
| SC | Segmentation fill rate | Fraction assigned a non-background predicted label | Segmentation |
| SC | Phase incoherence | Cross-ring inconsistency of the produced label phase | Segmentation |

The complex-family segmentation route must be described accurately:
`results.pkl` is empty for the complex calibration runs, so the label map is
reconstructed from `only_label.csv` and `pixel_to_point.pkl`. Across all 174
Stage 2 runs, 116 label maps use `results.pkl` and 58 use the fallback route.
All 174 Hough replays match the stored prompt geometry within the one-pixel
audit tolerance, and all core features are finite. The observed maximum
differences are much smaller than that tolerance (approximately
\(2.93\times10^{-4}\) px in X and \(3.09\times10^{-5}\) px in Y), with
100% prompt-type agreement. Use “within tolerance,” not “bit-exact replay.”

### Model comparison table

| Model | Definition |
|---|---|
| \(P(e)\) | Five PQ features |
| \(P(c)\) | Five SC features |
| \(P(e+c)\) | All ten candidate features |
| Legacy lean | Previous five features, retained only as a reproducibility baseline |
| Pruned lean (deployed) | Four LOFO-selected features; one pooled model |
| Pruned per-family | Same four features; one model per family |

### Selection wording

> Candidate models are compared by training fit and leave-one-family-out
> (LOFO) validation. The compact model size is selected by LOFO Spearman
> correlation, with the additional requirement that both PQ and SC-general
> evidence remain represented. The final model is refitted on all 120
> calibration runs and frozen before the 54-run holdout evaluation.

This wording should replace any suggestion that the lean model was chosen
because it gives the best value on every metric.

---

## 6. Frozen proxy equation

With standardized features, the deployed model is:

\[
\hat y =
0.350
+0.082z_{\mathrm{corrF1@15}}
+0.080z_{\mathrm{fill}}
-0.045z_{\mathrm{ringerr}}
-0.064z_{\mathrm{nan}}.
\]

Feature order, training means, and scales:

| Feature | Mean \(\mu\) | Scale \(s\) | Standardized coefficient |
|---|---:|---:|---:|
| Correspondence F1@15 | 0.1683 | 0.1507 | +0.0823 |
| Segmentation fill rate | 0.4598 | 0.2944 | +0.0798 |
| Ring-count error | 0.5833 | 0.4930 | −0.0454 |
| Depth-map missing-pixel fraction | 0.4084 | 0.3105 | −0.0644 |

RidgeCV selects \(\alpha=10.0\).

Suggested interpretation:

> Positive correspondence and fill coefficients reward outputs whose predicted
> layout is both populated and supported by detected joint evidence. Negative
> ring-count and missing-depth coefficients penalise geometrically implausible
> or incomplete inputs. Coefficients are conditional associations in a
> correlated linear model, not independent causal effects or direct parameter
> instructions.

Do not rank feature “importance” from coefficient magnitude alone without
noting that all coefficients act on standardized variables.

---

## 7. Experimental setup

### Calibration and holdout

- Calibration: 120 `bo/bayes` runs; 40 each for subsets 2-1, 3-1, and 5-1.
- Holdout stress test: 54 runs; 27 anchor/degraded pairs; nine pairs per family.
- No model fitting or feature selection uses holdout labels.
- Spearman CI: 2,000 subset-level bootstrap replicates, preserving each
  anchor/degraded pair and stratifying by family.
- Per-family versus pooled comparison: two-sided Wilcoxon on 27
  subset-aggregated absolute errors.

### Refinement protocol

Replace the nine-case primary protocol with:

> The deployment-style refinement panel includes every anchor whose frozen
> SC-general proxy lies in the study refinement band:
>
> \[
> 0.5\leq\hat y_0\leq0.7.
> \]
>
> No GT condition is used to admit a case. This rule selects 22 of the 27
> held-out anchors. Each case receives three GT-blind refinement rounds without
> early stopping. A round is eligible only if its proxy exceeds the anchor
> score. Among candidates within 0.01 of the highest proxy, the candidate with
> the lowest centreline residual is retained; if no round beats the anchor, the
> anchor is kept. GT mIoU is revealed only after selection.

Configuration:

| Setting | Revised value |
|---|---|
| Proposal policy | Deterministic family-specific GT-blind recipes in `bo/sc_general/run_campaign.py` |
| Panel admission | Frozen proxy score in \([0.5,0.7]\), no GT bound |
| Cases | 22 |
| Budget | Three rounds per case (66 attempted rounds) |
| Early stopping | None |
| Agent context | GT-blind images, run intrinsics, SC-general features, proxy scores, engineering ontology |
| Selection | Monotone proxy improvement; 0.01 residual tiebreak; anchor retained if no eligible round |
| GT use | Offline evaluation only |
| Execution | Serial on one GPU after the single-instance gate |

The campaign initially exposed a practical GPU constraint: overlapping SAM
jobs exhausted the 8 GB GPU. The validated campaign was therefore executed
serially. This is an implementation detail suitable for reproducibility notes,
not a scientific result.

### Retrospective response-region analysis

Add a separate analysis explicitly labelled post hoc:

> After completing the proxy-only campaign, we stratify the 22 cases using
> offline initial GT mIoU to examine where benefit is concentrated. The
> manuscript-style dual mid-band is
> \(0.5\leq\hat y_0\leq0.7\) and
> \(0.5\leq y_0\leq0.7\). This analysis does not alter case admission or
> candidate selection.

---

## 8. Results: proxy calibration and ablation

### Calibration table

| Setting | MAE | Spearman |
|---|---:|---:|
| Training fit (\(n=120\)) | **0.086** | **0.904** |
| Permutation control (20 within-family shuffles) | \(0.196\pm0.008\) | \(0.202\pm0.089\) |
| LOFO CV | **0.112** | **0.828** |

Suggested results wording:

> The four-feature SC-general proxy achieves training MAE 0.086 and Spearman
> correlation 0.904. Under LOFO validation, MAE is 0.112 and Spearman
> correlation is 0.828, exceeding the legacy model's LOFO correlation of
> 0.678. Within-family permutation reduces mean Spearman correlation to
> \(0.202\pm0.089\) and increases MAE to \(0.196\pm0.008\), supporting an
> association between the run-observable measurements and segmentation
> accuracy beyond fixed between-family differences.

### Feature-set ablation table

| Condition | Features | Train Spearman | Train MAE | LOFO Spearman | LOFO MAE |
|---|---:|---:|---:|---:|---:|
| \(P(e)\), PQ only | 5 | 0.864 | 0.099 | 0.718 | 0.223 |
| \(P(c)\), SC only | 5 | 0.884 | 0.093 | 0.806 | 0.140 |
| \(P(e+c)\), combined | 10 | **0.915** | **0.081** | 0.794 | 0.197 |
| Legacy K-row lean | 5 | 0.877 | 0.098 | 0.678 | 0.143 |
| **SC-general pruned lean** | **4** | 0.904 | 0.086 | **0.828** | **0.112** |

Interpretation:

> SC alone remains the strongest complete feature group under LOFO
> (\(\rho=0.806\)). Combining all ten measurements improves in-sample fit but
> does not improve transfer. LOFO-guided pruning produces the best transfer
> result while retaining both PQ and layout-general SC. The legacy arm
> reproduces the current manuscript's calibration numbers, providing a
> pipeline sanity check.

### Distance sensitivity

| Correspondence F1 / boundary-edge setting | LOFO Spearman |
|---|---:|
| F1@8 / edge@8 | 0.789 |
| F1@15 / edge@25 (frozen candidate combination) | 0.794 |
| F1@25 / edge@25 | 0.803 |

The full ten-feature model is not highly sensitive to these candidate
combinations. The middle row must not be described as a symmetric “15 px”
setting: it uses correspondence F1@15 together with
boundary-explained-edge@25. Although the @25/@25 combination is slightly
higher in this analysis, the F1@15/edge@25 candidate remains frozen to avoid
post-holdout retuning.

---

## 9. Results: held-out proxy fidelity

### Holdout table

| Metric | SC-general proxy | Legacy manuscript proxy |
|---|---:|---:|
| Spearman \(\rho\) | **0.817** | 0.827 |
| Subset-bootstrap 95% CI | \([0.761,0.864]\) | \([0.749,0.887]\) |
| MAE overall | **0.109** | 0.086 |
| MAE staggered / continuous / complex | 0.126 / 0.122 / **0.078** | 0.117 / 0.046 / 0.095 |
| PairRank | **27/27** | 27/27 |
| Alarm at \(\tau=0.5\) | 27 TP / **3 FP** | 27 TP / 0 FP |
| Alarm at \(\tau=0.43\) | **27 TP / 0 FP** | not required |

Suggested wording:

> On the 54-run holdout stress test, the SC-general proxy achieves Spearman
> correlation 0.817 (subset-bootstrap 95% CI \([0.761,0.864]\)) and MAE
> 0.109. It ranks the reference-sibling output above its constructed degraded
> counterpart on all 27 subsets. At the prespecified threshold 0.5 it detects
> all 27 degraded runs but also flags three anchors (3-2, 3-5, and 4-4).
> A descriptive threshold sweep gives 27/27 detections and 0/27 anchor false
> positives for thresholds 0.40–0.43. Because this threshold is selected after
> observing the panel, 0.43 should be reported as a study operating point, not
> an independently validated deployment threshold.

This is not a “well-calibrated mIoU predictor” result. A safer phrase is
“useful rank-based quality signal with imperfect absolute calibration.”

### Unified versus per-family wording

> Per-family refits reduce mean subset-aggregated MAE from 0.109 to 0.100, but
> the difference is not significant (Wilcoxon \(W=128\), two-sided
> \(p=0.148\)). The data do not establish that family-specific refitting is
> superior; nor do they establish that the unified proxy is equally calibrated
> in every family.

---

## 10. Results: deployment-style self-refinement

Primary numbers below are the **Fable-5** arm. The deterministic arm is cited
only as a comparison (nearly identical aggregate lift).

### Primary 22-case table (Fable-5)

| Metric | Fable-5 | Det (comparison) |
|---|---:|---:|
| Proxy-band cases | 22/27 | 22/27 |
| Cases selecting a round over the anchor | **15/22** | 14/22 |
| Anchor proxy mean | 0.606 | 0.606 |
| Selected proxy mean | 0.652 | 0.647 |
| Anchor mIoU mean | **0.738** | 0.738 |
| Selected mIoU mean | **0.768** | 0.770 |
| Mean mIoU change | **+0.030** | +0.032 |
| Improved / unchanged / worsened | 10 / 7 / 5 | 9 / 8 / 5 |
| Proxy/GT direction agreement among accepted rounds | 10/15 | 9/14 |

Suggested wording:

> Under live Fable-5 proposals, the proxy-only rule admits 22 of the 27
> anchors. Fifteen cases retain a proposed round; seven retain the anchor.
> Mean mIoU increases from 0.738 to 0.768 (mean change +0.030). Ten cases
> improve, seven are unchanged because the anchor is retained, and five
> decline slightly. A deterministic recipe arm on the same panel reaches
> 0.770 (+0.032), showing that the lift is not unique to the LLM proposer,
> while the Fable arm is the one that supports the paper's LLM claim under
> the SC-general proxy. The dual mid-band (n=6) still concentrates the gain:
> 0.592 → 0.689 under Fable-5 versus 0.592 → 0.696 under the deterministic arm.

### Family-level outcomes (Fable-5)

| Family | Cases | Round selected | Improved / worsened | Anchor mIoU | Selected mIoU | Change |
|---|---:|---:|---:|---:|---:|---:|
| Staggered | 7 | 7 | 5 / 2 | 0.714 | 0.795 | **+0.080** |
| Continuous | 7 | 2 | 0 / 2 | 0.787 | 0.786 | **−0.001** |
| Complex | 8 | 6 | 5 / 1 | 0.716 | 0.728 | **+0.012** |

Suggested interpretation:

> The aggregate gain is driven primarily by the staggered family (especially
> 1-5 and 2-2). Continuous-family proposals are rarely accepted or else move
> GT slightly down; complex cases show a modest positive mean. The same
> staggered-heavy pattern appears in the deterministic comparison arm.

### Overall 27-subset operating points

| Operating point | Mean mIoU |
|---|---:|
| Bayesian/family-reference anchors | 0.722 |
| + SC-general Fable-5 refinement | **0.746** |
| + SC-general det refinement (comparison) | 0.748 |

> 0.456 (notebook expert configuration) → 0.722 (Bayesian/family-reference
> anchors) → **0.746** (SC-general Fable-5 proxy-guided refinement).

---

## 11. Results: where does refinement help most?

### Region comparison (Fable-5 arm)

| Region defined by initial values | n | Anchor mIoU | Selected mIoU | Mean change | Improved / worsened |
|---|---:|---:|---:|---:|---:|
| **Proxy and GT both [0.5, 0.7]** | **6** | **0.592** | **0.689** | **+0.097** | **5 / 0** |
| Proxy [0.5, 0.7], GT ≥ 0.7 | 16 | 0.793 | 0.797 | +0.005 | 5 / 5 |
| All proxy [0.5, 0.7] | 22 | 0.738 | 0.768 | +0.030 | 10 / 5 |
| Proxy [0.50, 0.55) | 5 | 0.705 | 0.718 | +0.013 | 2 / 0 |
| Proxy [0.65, 0.70] | 6 | 0.776 | 0.799 | +0.023 | 1 / 3 |

Main result:

> The strongest observed response still occurs when both the proxy and actual
> starting accuracy are intermediate. Under Fable-5 the six-case dual mid-band
> gains +0.097 mIoU on average (0.592 → 0.689), versus +0.005 among the 16
> cases already above 0.7 GT mIoU. The deterministic comparison arm reaches
> 0.696 (+0.104) on the same six cases; legacy paper Fable averaged 0.678.
> Use the dual mid-band as retrospective response evidence, not as the
> deployable admission rule.

### Six dual-mid-band cases (Fable-5)

| Subset | Family | Anchor proxy | Anchor mIoU | Selected | Selected proxy | Selected mIoU | mIoU change |
|---|---|---:|---:|---|---:|---:|---:|
| 1-5 | Staggered | 0.555 | 0.549 | Round 3 | 0.684 | 0.892 | **+0.343** |
| 2-2 | Staggered | 0.699 | 0.673 | Round 2 | 0.757 | 0.843 | **+0.170** |
| 4-3 | Complex | 0.520 | 0.516 | Round 2 | 0.573 | 0.544 | +0.028 |
| 1-4 | Staggered | 0.646 | 0.556 | Round 2 | 0.722 | 0.578 | +0.022 |
| 4-1 | Complex | 0.552 | 0.635 | Round 1 | 0.621 | 0.653 | +0.018 |
| 3-4 | Continuous | 0.520 | 0.622 | Anchor | 0.520 | 0.622 | 0.000 |
| **Mean** | — | **0.582** | **0.592** | — | **0.646** | **0.689** | **+0.097** |

Det comparison arm mean on the same six: 0.696 (+0.104). Legacy paper Fable mean selected mIoU: 0.678.

Recommended manuscript wording:

> A retrospective response analysis recovers a six-case subgroup matching the
> manuscript's dual proxy×GT mid-band. Under live Fable-5 proposals the mean
> rises from 0.592 to 0.689 (+0.097), with five improvements and no declines.
> The deterministic comparison arm reaches 0.696 on the same cases. Because
> this subgroup is small, retrospectively defined using GT, and identified
> after region comparison, these values are exploratory rather than
> confirmatory. The deployable selection result remains the 22-case proxy-only
> Fable-5 analysis (0.738 → 0.768).

### Optional narrower region

The tight region proxy \([0.55,0.65]\) and GT \([0.5,0.7]\) contains only
three cases (1-4, 1-5, 4-1). Under Fable-5 it shows +0.128 mean mIoU with all
three improving (0.580 → 0.708). Do **not** promote it as the preferred
region: \(n=3\) is too small and more post hoc.

---

## 12. Discussion

### Proposed key-findings wording

> Three findings emerge. First, layout-general line-to-label correspondence is
> a transferable SC signal. The four-feature pruned proxy improves LOFO
> Spearman from the legacy model's 0.678 to 0.828 and avoids K-row assumptions
> that do not apply consistently to staggered and complex layouts. Second, the
> proxy preserves perfect paired ranking but is imperfectly calibrated:
> holdout Spearman is 0.817, MAE is 0.109, and the old threshold 0.5 produces
> three anchor false alarms. The model should therefore be interpreted as an
> auditable ordering/control signal rather than a precise mIoU replacement.
> Third, proxy-only admission with live Fable-5 proposals demonstrates a
> positive refinement effect over a substantially broader 22-case panel
> (0.738 → 0.768), but the gain is heterogeneous. The strongest response
> occurs in the retrospective six-case dual mid-band (0.592 → 0.689);
> already-good cases show little net benefit and occasional small declines.

### Mechanistic interpretation

> Correspondence F1 links two independently imperfect artefacts: Hough-derived
> physical joint evidence and the segmentation's claimed boundaries. A high
> value therefore requires the detected geometry and produced label map to
> explain each other. This relation is meaningful across layouts, unlike
> fixed K-row position residuals. The feature is not sufficient alone: fill,
> ring-count plausibility, and depth completeness prevent a sparse or
> internally coherent failure from appearing healthy.

### Why the dual mid-band responds most

> Genuinely mid-quality outputs retain enough structural evidence for bounded
> parameter changes to repair them, while still leaving room for improvement.
> Already-good outputs have less headroom, and proxy calibration error can
> cause them to enter the refinement band despite high GT accuracy. Very poor
> outputs fall below the proxy band and were not tested in this campaign, so
> the experiment cannot determine whether they are irrecoverable or merely
> excluded by the gate.

This explanation is plausible and evidence-consistent, but should be framed as
an interpretation rather than a demonstrated causal mechanism.

---

## 13. Limitations

Suggested replacement limitations:

1. **Single development subset per family.** Calibration covers represented
   families and acquisition conditions, not unrestricted transfer to new
   projects or geometries.
2. **Absolute calibration miss.** The proxy's holdout MAE is 0.109 and the old
   0.5 alarm threshold gives three anchor false positives. Threshold 0.43 is
   descriptive and must be validated on independent natural failures.
3. **Constructed degradation stress test.** PairRank and alarm results concern
   controlled degraded siblings, not prevalence-weighted operational failures.
4. **Retrospective response subgroup.** The six-case dual mid-band uses GT,
   is post hoc, and is too small for a confirmatory “optimal region” claim.
5. **Proposal-policy comparison.** Fable-5 and the deterministic recipe arm
   produce nearly identical aggregate lifts on the 22-case panel
   (+0.030 vs +0.032). The LLM claim is supported by the Fable arm; the
   nearly matching det arm shows the proxy+selection loop, not only the
   proposer, drives much of the mean gain.
6. **GT-blind-by-protocol caveat.** Fable proposals did not read offline GT
   files during the loop, but the proposing agent had seen aggregate GT for
   these cases earlier in the same research session.
7. **Family heterogeneity.** Staggered cases contribute most of the gain;
   continuous cases are essentially unchanged.
8. **Linear estimator.** Ridge is transparent but cannot express uncertainty
   or nonlinear interactions; broader calibration would be required before
   testing more expressive alternatives.
9. **Selection errors remain.** Five already-good cases decline after a round
   is accepted under Fable-5 (mean decline among those five ≈ −0.008).

The current manuscript limitation claiming that no proxy-only deployment panel
was run should be removed: Stage 3 now performs exactly that experiment with
both Fable-5 and deterministic proposers.

---

## 14. Conclusions

### Proposed replacement conclusion

Proxy4Tun calibrates a GT-free quality signal for segmental tunnel-lining
segmentation from 120 design-time exploration runs. Replacing family-specific
K-row features with layout-general line-to-label correspondence yields a
four-feature Ridge proxy with LOFO Spearman 0.828. On 54 paired holdout runs,
the proxy achieves Spearman 0.817 and MAE 0.109, while ranking all 27
reference-sibling outputs above their constructed degraded counterparts.
These results support cross-family ranking, but also show that absolute mIoU
calibration and fixed alarm thresholds remain imperfect.

Using only the frozen proxy band to admit cases, the expanded 22-case
Fable-5 self-refinement campaign raises mean mIoU from 0.738 to 0.768 and
raises the 27-subset mean from 0.722 to 0.746. A deterministic comparison arm
reaches 0.770 / 0.748. Retrospective analysis identifies a six-case dual
proxy/GT mid-band with a larger 0.592-to-0.689 Fable gain, whereas
already-good cases show little net benefit. The deployable result is therefore
the broader proxy-only panel; the dual mid-band is evidence for a promising
response region that requires prospective identification without GT.

Overall, observable correspondence between physical joint evidence and
predicted segmentation boundaries provides a more layout-general control
signal than K-row regularity. Future work should calibrate uncertainty,
prospectively identify improvable mid-quality outputs without GT, validate
thresholds on natural failures and external tunnels, and reduce the small
selection harms observed on already-good outputs.

### Conclusion bullets

- Four-feature SC-general proxy: train 0.086/0.904 MAE/Spearman; LOFO
  0.112/0.828.
- Holdout: 0.109 MAE, 0.817 Spearman, PairRank 27/27; 27 TP/3 FP at 0.5 and
  27 TP/0 FP at 0.43.
- Proxy-only 22-case Fable-5 refinement: 0.738 to 0.768; full 27-subset mean
  0.722 to 0.746 (det comparison: 0.770 / 0.748).
- Retrospective dual mid-band: six cases, 0.592 to 0.689 (Fable); det 0.696;
  promising but not a deployable GT-free gate.

---

## 15. Tables and figures to replace or regenerate

| Current manuscript item | Required revision |
|---|---|
| Abstract and highlights | Replace five-feature, 0.827/0.086, nine-case 0.569→0.675 claims |
| Candidate-feature table | Remove K-row trio/reference-relative rows; insert correspondence, edge support, Chamfer, ring-count error |
| Model-comparison table | PQ 5, SC 5, full 10, legacy 5, deployed 4 |
| Algorithm: proxy calibration | Remove stored family statistics \(S_f\); features depend on run \(r\) and expected ring count |
| Lean-proxy equation | Replace legacy five-feature coefficients with four-feature SC-general equation |
| Proxy calibration table | Replace with 0.086/0.904 train and 0.112/0.828 LOFO |
| Holdout-fidelity table | Replace with 0.817, CI [0.761,0.864], MAE 0.109, per-family MAEs, threshold results |
| Ablation table | Replace all PQ/SC/combined/lean values with Stage 2 results |
| Unified/per-family table | Rebuild from the four-feature models; include Wilcoxon 0.109 vs 0.100, \(p=0.148\) |
| Refinement workflow figure | Show proxy-only admission of 22 cases; GT revealed after selection |
| Refinement results figure | Plot 22-case anchor/selected values, family breakdown, and dual-mid-band retrospective highlight |
| PoC model table | Replace/update with Fable-5 SC-general arm; keep legacy Fable/GPT and `scgen-det` as separate comparison columns |
| Panel mIoU table | Replace 0.757 with 0.746 (Fable) and note det 0.748 |
| PoC appendix | Replace nine-case per-round evidence with 22-case Fable selections (`campaign_fable.md`) or move full table to supplementary data |
| Discussion/conclusion | Reframe proxy as strong ranking/control signal with imperfect calibration and heterogeneous refinement benefit; state GT-blind-by-protocol caveat |

Recommended figure panels:

1. **Proxy validation:** calibration scatter and 54-run holdout scatter, with
   the \([0.5,0.7]\) proxy band.
2. **Region-response plot:** initial proxy versus initial GT mIoU, marker
   colour/arrow showing selected mIoU change; outline the retrospective dual
   mid-band.
3. **Family refinement bars:** staggered +0.080, continuous ≈0, complex +0.012
   (Fable-5).
4. **Operating-point progression:** 0.456 → 0.722 → 0.746 (Fable).
5. **Arm comparison:** dual-band and 22-case means for Fable vs det vs legacy.

---

## 16. Traceability

| Result | Canonical source |
|---|---|
| Feature replay and 120+54 tables | `data/sc-general/stage2/gate.md`; `training_table.csv`; `holdout_table.csv`; `replay_audit.csv` |
| Frozen model/scaler/equation | `bo/sc_general/models.json` |
| Arms, LOFO, delta sensitivity | `bo/sc_general/ablation.json` |
| Holdout fidelity, CI, alarms, Wilcoxon | `data/sc-general/stage2/holdout_metrics.json`; `holdout_scores.csv`; `validation_gate.md` |
| Stage 3 protocol/gate (det) | `data/sc-general/stage3/gate.md`; `campaign.md`; `validation_gate.md` |
| Stage 3 Fable-5 protocol/gate | `data/sc-general/stage3/gate_fable.md`; `campaign_fable.md` |
| Per-case selection (det) | `data/sc-general/stage3/selections/*.json` |
| Per-case selection (Fable) | `data/sc-general/stage3/selections-fable/*.json` |
| 22/27 outcomes (det) | `data/sc-general/stage3/refined_scores.csv`; `report.md` |
| 22/27 outcomes (Fable) | `data/sc-general/stage3/refined_scores_fable.csv`; `report_fable.md` |
| Region analysis (det) | `data/sc-general/stage3/region_comparison.csv`; `poc_band_cases.csv` |
| Region + arm comparison (Fable) | `data/sc-general/stage3/region_comparison_fable.csv`; `arm_comparison.md` |
| Paper nine (Fable-5.1 vs legacy) | `data/sc-general/stage3/paper_nine_comparison.md`; `paper_nine_comparison.csv` |

The FAIL recorded in `data/sc-general/stage2/report.md` is the historical
Stage-2 holdout-fidelity gate outcome. Stage 3 subsequently proceeded by an
explicit user decision and passed its own execution/completeness gate. The two
statuses answer different questions and should not be collapsed into one
unqualified “gate” result.

---

## 17. Editorial recommendation

Use the **22-case proxy-only experiment as the primary refinement result**.
It directly answers the deployment question and removes the current
manuscript's most important selection-bias limitation.

Use the **six-case dual mid-band as a secondary retrospective response
analysis**, not as the deployed gate. Under Fable-5 it gives the clearest
improvement \((0.592\rightarrow0.689)\), but calling it the deployment panel
would recreate the GT-selection problem that Stage 3 was designed to remove.

The revised paper is scientifically stronger if it accepts the trade-off
honestly:

- the new proxy is more layout-general and transfers better across families;
- it preserves perfect pairwise discrimination;
- it is less accurate in absolute holdout calibration than the legacy proxy;
- live Fable-5 self-refinement on the broader proxy-only panel still produces
  a positive mean gain (0.738 → 0.768), nearly matching the deterministic arm;
- the largest gains occur in a small, retrospectively identified mid-quality
  subgroup that now motivates prospective uncertainty/response gating.

For manuscript positioning:

1. **Use the Fable-5.1 arm as the primary LLM self-refinement result** under the
   SC-general proxy (22-case + dual-band retrospective + paper-nine table),
   with the explicit GT-blind-by-protocol caveat.
2. **Keep `scgen-det` and legacy paper Fable/GPT as comparison columns** in
   `arm_comparison.md` / `paper_nine_comparison.md`, not as replacements for
   the LLM claim.

---

## 18. Paper nine under the 4-feature SC-general proxy

The manuscript's nine-case feasibility set was re-run with Fable-5.1 proposals
guided by the frozen 4-feature SC-general proxy (monotone-accept selection).
Six cases already existed from the dual-band campaign; the three reject-band
cases (`3-2`, `3-5`, `4-4`) were newly refined.

| Subset | Band | Baseline | Fable-5.1 | ΔFable-5.1 | Legacy Fable-5 | ΔLegF5 | Legacy GPT-5.6 | ΔGPT |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| 4-4 | reject | 0.347 | 0.368 | +0.021 | 0.700 | +0.353 | 0.422 | +0.075 |
| 1-5 | refine | 0.549 | 0.892 | +0.343 | 0.782 | +0.233 | 0.437 | −0.112 |
| 1-4 | refine | 0.556 | 0.578 | +0.022 | 0.786 | +0.230 | 0.556 | 0.000 |
| 3-2 | reject | 0.631 | 0.749 | +0.118 | 0.719 | +0.088 | 0.747 | +0.116 |
| 4-3 | refine | 0.516 | 0.544 | +0.028 | 0.544 | +0.028 | 0.516 | 0.000 |
| 4-1 | refine | 0.635 | 0.653 | +0.018 | 0.659 | +0.024 | 0.659 | +0.024 |
| 3-4 | refine | 0.622 | 0.622 | 0.000 | 0.631 | +0.009 | 0.622 | 0.000 |
| 3-5 | reject | 0.588 | 0.870 | +0.282 | 0.588 | 0.000 | 0.713 | +0.125 |
| 2-2 | refine | 0.673 | 0.843 | +0.170 | 0.668 | −0.005 | 0.586 | −0.087 |
| **Mean** | — | **0.569** | **0.680** | **+0.111** | **0.675** | **+0.107** | **0.584** | **+0.016** |

Suggested wording:

> On the original nine-case feasibility set, Fable-5.1 proposals under the
> 4-feature SC-general proxy raise mean mIoU from 0.569 to 0.680
> (+0.111), matching the magnitude of the legacy Fable-5 PoC (+0.107 to
> 0.675) and exceeding legacy GPT-5.6 (+0.016 to 0.584). Three of the nine
> (`3-2`, `3-5`, `4-4`) fall in the SC-general reject band (proxy < 0.5) and
> would be skipped by a strict label-free refine gate; they were still refined
> here for parity with the manuscript panel. The largest new lifts are 1-5
> (+0.343), 3-5 (+0.282, unlocked by a stage-1 seed change that dropped
> residual from 56.6 cm to 2.6 cm), and 2-2 (+0.170). Case 4-4 remains hard
> under the SC-general signal (+0.021) relative to the legacy Fable-5 jump
> (+0.353), which used a different proxy and proposal history.

Canonical sources: `data/sc-general/stage3/paper_nine_comparison.md`,
`paper_nine_comparison.csv`, `campaign_fable.md`,
`selections-fable/{3-2,3-5,4-4}.json`.
