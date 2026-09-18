# Per-family mIoU proxy — held-out evaluation

_Generated 2026-07-20T15:59:04_

## Design

- Feature set: **B1+B2lean** (GT-free).
- Train within family; test on held-out sub-tunnels.
- Per held-out subset: sibling **anchor** config + one frozen **known-bad** config.
- Training cases: t1&2=`1-1+2-1`, t3=`3-1+3-2`, t4&5=`4-1+5-1`.
- T3 subsets are ring windows of one scan (`data/3-1.txt`); holdouts are other sections, not other tunnels.

## Training (within-family)

| Family | n | train MAE | pooled MAE | pooled Spearman | alarm thr | low-mIoU floor |
|---|---:|---:|---:|---:|---:|---:|
| t1&2 | 80 | 0.046 | 0.075 | 0.814 | 0.694 | 0.665 |
| t3 | 72 | 0.125 | 0.188 | 0.560 | 0.231 | 0.147 |
| t4&5 | 73 | 0.017 | 0.086 | 0.932 | 0.564 | 0.596 |

### Leave-one-tunnel-out

- **t1&2** hold `1-1`: MAE=0.076, Spearman=0.705 (n_test=40)
- **t1&2** hold `2-1`: MAE=0.074, Spearman=0.721 (n_test=40)
- **t3** hold `3-1`: MAE=0.281, Spearman=0.513 (n_test=35)
- **t3** hold `3-2`: MAE=0.099, Spearman=0.886 (n_test=37)
- **t4&5** hold `4-1`: MAE=0.059, Spearman=0.800 (n_test=40)
- **t4&5** hold `5-1`: MAE=0.119, Spearman=0.928 (n_test=33)

## Known-bad configs

| Family | Source trial | Training mIoU | Δ vs min sibling anchor |
|---|---|---:|---:|
| t1&2 | `2-1/2-1-t002` | 0.032 | 0.755 |
| t3 | `3-2/3-2-t029` | 0.027 | 0.604 |
| t4&5 | `4-1/4-1-t009` | 0.036 | 0.599 |

## Held-out calibration

| Family | config | n | MAE | Spearman | mean mIoU | mean proxy |
|---|---|---:|---:|---:|---:|---:|
| t1&2 | anchor | 8 | 0.076 | 0.167 | 0.781 | 0.804 |
| t1&2 | bad | 8 | 0.049 | -0.843 | 0.035 | 0.017 |
| t3 | anchor | 3 | 0.275 | 1.000 | 0.733 | 0.458 |
| t3 | bad | 3 | 0.044 | 1.000 | 0.038 | 0.082 |
| t4&5 | anchor | 15 | 0.094 | 0.717 | 0.577 | 0.625 |
| t4&5 | bad | 15 | 0.117 | 0.289 | 0.090 | -0.007 |

Overall MAE (ok runs): **0.099** (n=52).

## Alarm confusion (split by config)

| Family | config | TP | FP | TN | FN | precision | recall |
|---|---|---:|---:|---:|---:|---:|---:|
| t1&2 | anchor | 0 | 0 | 7 | 1 | — | 0.00 |
| t1&2 | bad | 8 | 0 | 0 | 0 | 1.00 | 1.00 |
| t3 | anchor | 0 | 0 | 3 | 0 | — | — |
| t3 | bad | 3 | 0 | 0 | 0 | 1.00 | 1.00 |
| t4&5 | anchor | 5 | 1 | 9 | 0 | 0.83 | 1.00 |
| t4&5 | bad | 15 | 0 | 0 | 0 | 1.00 | 1.00 |

Notable misclassifications:
- **FN** `1-5`/anchor: mIoU=0.490 below floor but proxy=0.784 (no alarm).
- **FP** `4-6`/anchor: mIoU=0.611 above floor but proxy=0.479 (alarm).

## Per-tunnel ranking (anchor vs bad)

Proxy preserves mIoU order on **26/26** pairs (accuracy=1.00).

| Subset | Family | rank_ok | anchor mIoU | bad mIoU | anchor proxy | bad proxy |
|---|---|---|---:|---:|---:|---:|
| 1-2 | t1&2 | True | 0.817 | 0.037 | 0.766 | -0.079 |
| 1-3 | t1&2 | True | 0.745 | 0.037 | 0.823 | -0.059 |
| 1-4 | t1&2 | True | 0.828 | 0.035 | 0.789 | 0.015 |
| 1-5 | t1&2 | True | 0.490 | 0.038 | 0.784 | 0.012 |
| 2-2 | t1&2 | True | 0.845 | 0.032 | 0.808 | 0.086 |
| 2-3 | t1&2 | True | 0.796 | 0.034 | 0.823 | 0.074 |
| 2-4 | t1&2 | True | 0.833 | 0.034 | 0.827 | 0.063 |
| 2-5 | t1&2 | True | 0.892 | 0.033 | 0.815 | 0.025 |
| 3-3 | t3 | True | 0.806 | 0.031 | 0.571 | 0.069 |
| 3-4 | t3 | True | 0.596 | 0.045 | 0.364 | 0.089 |
| 3-5 | t3 | True | 0.798 | 0.037 | 0.438 | 0.086 |
| 4-10 | t4&5 | True | 0.247 | 0.094 | 0.486 | 0.080 |
| 4-2 | t4&5 | True | 0.725 | 0.150 | 0.756 | -0.001 |
| 4-3 | t4&5 | True | 0.279 | 0.120 | 0.503 | 0.023 |
| 4-4 | t4&5 | True | 0.671 | 0.136 | 0.789 | -0.056 |
| 4-5 | t4&5 | True | 0.786 | 0.042 | 0.698 | -0.039 |
| 4-6 | t4&5 | True | 0.611 | 0.114 | 0.479 | 0.095 |
| 4-7 | t4&5 | True | 0.815 | 0.075 | 0.781 | -0.079 |
| 4-8 | t4&5 | True | 0.256 | 0.220 | 0.368 | 0.150 |
| 4-9 | t4&5 | True | 0.078 | 0.088 | 0.192 | 0.213 |
| 5-2 | t4&5 | True | 0.789 | 0.039 | 0.722 | 0.066 |
| 5-3 | t4&5 | True | 0.759 | 0.058 | 0.776 | 0.023 |
| 5-4 | t4&5 | True | 0.760 | 0.048 | 0.803 | -0.063 |
| 5-5 | t4&5 | True | 0.781 | 0.040 | 0.762 | 0.003 |
| 5-6 | t4&5 | True | 0.671 | 0.074 | 0.733 | 0.004 |
| 5-7 | t4&5 | True | 0.423 | 0.049 | 0.531 | -0.530 |

## Per-subset scores

| Subset | Family | config | status | mIoU | proxy | |err| | alarm | low? |
|---|---|---|---|---:|---:|---:|---|---|
| 1-2 | t1&2 | anchor | ok | 0.817 | 0.766 | 0.051 | False | False |
| 1-2 | t1&2 | bad | ok | 0.037 | -0.079 | 0.116 | True | True |
| 1-3 | t1&2 | anchor | ok | 0.745 | 0.823 | 0.078 | False | False |
| 1-3 | t1&2 | bad | ok | 0.037 | -0.059 | 0.096 | True | True |
| 1-4 | t1&2 | anchor | ok | 0.828 | 0.789 | 0.039 | False | False |
| 1-4 | t1&2 | bad | ok | 0.035 | 0.015 | 0.020 | True | True |
| 1-5 | t1&2 | anchor | ok | 0.490 | 0.784 | 0.294 | False | True |
| 1-5 | t1&2 | bad | ok | 0.038 | 0.012 | 0.026 | True | True |
| 2-2 | t1&2 | anchor | ok | 0.845 | 0.808 | 0.037 | False | False |
| 2-2 | t1&2 | bad | ok | 0.032 | 0.086 | 0.054 | True | True |
| 2-3 | t1&2 | anchor | ok | 0.796 | 0.823 | 0.027 | False | False |
| 2-3 | t1&2 | bad | ok | 0.034 | 0.074 | 0.040 | True | True |
| 2-4 | t1&2 | anchor | ok | 0.833 | 0.827 | 0.006 | False | False |
| 2-4 | t1&2 | bad | ok | 0.034 | 0.063 | 0.029 | True | True |
| 2-5 | t1&2 | anchor | ok | 0.892 | 0.815 | 0.077 | False | False |
| 2-5 | t1&2 | bad | ok | 0.033 | 0.025 | 0.008 | True | True |
| 3-3 | t3 | anchor | ok | 0.806 | 0.571 | 0.235 | False | False |
| 3-3 | t3 | bad | ok | 0.031 | 0.069 | 0.038 | True | True |
| 3-4 | t3 | anchor | ok | 0.596 | 0.364 | 0.232 | False | False |
| 3-4 | t3 | bad | ok | 0.045 | 0.089 | 0.044 | True | True |
| 3-5 | t3 | anchor | ok | 0.798 | 0.438 | 0.360 | False | False |
| 3-5 | t3 | bad | ok | 0.037 | 0.086 | 0.049 | True | True |
| 4-10 | t4&5 | anchor | ok | 0.247 | 0.486 | 0.239 | True | True |
| 4-10 | t4&5 | bad | ok | 0.094 | 0.080 | 0.014 | True | True |
| 4-2 | t4&5 | anchor | ok | 0.725 | 0.756 | 0.031 | False | False |
| 4-2 | t4&5 | bad | ok | 0.150 | -0.001 | 0.151 | True | True |
| 4-3 | t4&5 | anchor | ok | 0.279 | 0.503 | 0.224 | True | True |
| 4-3 | t4&5 | bad | ok | 0.120 | 0.023 | 0.097 | True | True |
| 4-4 | t4&5 | anchor | ok | 0.671 | 0.789 | 0.118 | False | False |
| 4-4 | t4&5 | bad | ok | 0.136 | -0.056 | 0.192 | True | True |
| 4-5 | t4&5 | anchor | ok | 0.786 | 0.698 | 0.088 | False | False |
| 4-5 | t4&5 | bad | ok | 0.042 | -0.039 | 0.081 | True | True |
| 4-6 | t4&5 | anchor | ok | 0.611 | 0.479 | 0.132 | True | False |
| 4-6 | t4&5 | bad | ok | 0.114 | 0.095 | 0.019 | True | True |
| 4-7 | t4&5 | anchor | ok | 0.815 | 0.781 | 0.034 | False | False |
| 4-7 | t4&5 | bad | ok | 0.075 | -0.079 | 0.154 | True | True |
| 4-8 | t4&5 | anchor | ok | 0.256 | 0.368 | 0.112 | True | True |
| 4-8 | t4&5 | bad | ok | 0.220 | 0.150 | 0.070 | True | True |
| 4-9 | t4&5 | anchor | ok | 0.078 | 0.192 | 0.114 | True | True |
| 4-9 | t4&5 | bad | ok | 0.088 | 0.213 | 0.125 | True | True |
| 5-2 | t4&5 | anchor | ok | 0.789 | 0.722 | 0.067 | False | False |
| 5-2 | t4&5 | bad | ok | 0.039 | 0.066 | 0.027 | True | True |
| 5-3 | t4&5 | anchor | ok | 0.759 | 0.776 | 0.017 | False | False |
| 5-3 | t4&5 | bad | ok | 0.058 | 0.023 | 0.035 | True | True |
| 5-4 | t4&5 | anchor | ok | 0.760 | 0.803 | 0.043 | False | False |
| 5-4 | t4&5 | bad | ok | 0.048 | -0.063 | 0.111 | True | True |
| 5-5 | t4&5 | anchor | ok | 0.781 | 0.762 | 0.019 | False | False |
| 5-5 | t4&5 | bad | ok | 0.040 | 0.003 | 0.037 | True | True |
| 5-6 | t4&5 | anchor | ok | 0.671 | 0.733 | 0.062 | False | False |
| 5-6 | t4&5 | bad | ok | 0.074 | 0.004 | 0.070 | True | True |
| 5-7 | t4&5 | anchor | ok | 0.423 | 0.531 | 0.108 | True | True |
| 5-7 | t4&5 | bad | ok | 0.049 | -0.530 | 0.579 | True | True |

## Failure analysis: the `1-5` false negative (GT autopsy)

Per-ring comparison against GT (`only_label.csv`) shows the miss is a
**within-ring block-label rotation**, not a segmentation-quality problem:

- Ring geometry is correct: every GT ring maps to exactly one predicted ring
  (purity 0.95–0.99, correct order).
- Rings 266–269 and 272–273 score 0.93–0.95 label accuracy; rings **270**
  (29% of points) and **271** (21%) score 0.35/0.55.
- Inside those two rings the confusion matrix is a clean cyclic shift: ring
  270 has every block label rotated **+1 position** (GT 1→pred 2, 2→3, 4→5,
  5→6, 6→1), ring 271 rotated **−1**. Two rotated rings holding ~50% of the
  points drag mIoU from ~0.85-level to 0.490.

B1+B2lean cannot see this: fill, completeness, and detection provenance are
genuinely healthy; only the block *identities* are rotated. This is the label
blind spot the ablation predicted (H2), observed here on t1&2 rather than T3.

### GT-free mitigation: cross-ring phase-coherence check (`bo/phase_check.py`)

Rings in these linings reuse a small set of build orientations, so every
ring's "clock face" (circular mean θ per block label) should match some
sibling ring. Score = point-weighted mean of each ring's nearest-peer face
distance. Uses only `final.csv` (pred labels + unwrapped θ,h) — no GT.

Results on all held-out runs (`bo/family/phase_check.json`, threshold
12°, applicable to t1&2/t3 whose stagger is regular):

- Healthy t1&2/t3 anchors score **1.4–3.6°**; the rotated `1-5` anchor scores
  **14.4°** → **phase alarm fires, recovering the false negative**.
- One new borderline alarm: `1-4` anchor (14.2°, mIoU 0.828). GT confirms it
  **does** contain one genuinely rotated ring (GT ring 204, block acc 0.00,
  shift +4) — the ring is just small (1.5% of points) so mIoU survived. The
  alarm is factually right about rotation; cost is one re-check.
- All t3 anchors score ≤2.8° (the `uniform_k_snap` + K-row clamp already
  suppress this failure mode there).
- **Not applicable to t4&5**: irregular stagger sequences put healthy anchors
  at 10–37°, indistinguishable from rotation. (GT truth table
  `bo/family/ring_rotation_truth.csv` shows t4&5 anchors contain many
  genuinely rotated rings — but the B1+B2lean proxy already alarms correctly
  on the low-mIoU ones there.)

Combined verdict (proxy alarm OR phase alarm): the dangerous miss (`1-5`
false negative, bad delivery) is converted into a cheap false positive
(`1-4`, re-check). Overall correctness stays 50/52 but the error mass moves
to the safe side.

## Limitations

- Only two quality levels per held-out tunnel (anchor + one known-bad); not a full ranking study.
- T3 train/holdout sections are windows of the **same** physical scan (`3-1`…`3-5`); transfer is cross-section, not cross-tunnel. Sibling params come from `anchors/t3/3-1-1` (`segment_order`, `h_ring_sign`).
- Known-bad configs are frozen from training-tunnel BO archives; transfer of *that specific failure mode* is assumed.
- Sibling-anchor params are the honest deployment baseline, not per-tunnel retuning.
- t3 holdout anchor calibration remains biased low (proxy under-predicts good sections).
- Phase-coherence check is family-scoped: reliable for t1&2/t3 (regular stagger), not usable for t4&5 (irregular stagger); its threshold (12°) is set from this panel, not an independent set.

## Confidence

**Moderate** based on holdout MAE=0.099, ranking accuracy=1.0, and the T3 same-scan caveat.

