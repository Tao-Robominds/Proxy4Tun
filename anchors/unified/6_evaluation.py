#!/usr/bin/env python3
# Evaluation for agents pipeline (faithful to sam4tun/6_evaluation.py)

import sys
import os
import matplotlib
matplotlib.use("Agg")

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

_PIPELINE_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(os.path.dirname(_PIPELINE_DIR))
_SAM4TUN_PKG = os.path.join(_REPO_ROOT, "sam4tun")
for _p in (_PIPELINE_DIR, _SAM4TUN_PKG):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from helpers.pipeline_io import ensure_dir

import family_io

tunnel_id = sys.argv[1]
family_mode = family_io.load_family_mode()
print(f"[unified] stage=evaluation family_mode={family_mode}")
paths = ensure_dir(tunnel_id)

test = pd.read_csv(paths["only_label"])
test
# =================  start evaluation  =================
gt_rings = test['gt_rings'].values.astype(int)
# global_gt_rings = test['global_gt_rings'].values.astype(int)
gt_labels = test['gt_labels'].values.astype(int)

pred_rings = test['pred_rings'].values.astype(int)
# global_pred_rings = test['global_pred_rings'].values.astype(int)
pred_labels = test['pred_labels'].values.astype(int)
def compute_iou(pred_points, gt_points):
    """Compute the IoU between predicted points and ground truth points."""
    intersection = len(np.intersect1d(pred_points, gt_points))
    union = len(np.union1d(pred_points, gt_points))
    if union == 0:
        return 0
    return intersection / union

def compute_iou_matrix(pred_rings, gt_rings, pred_labels, gt_labels, category):
    """Compute the IoU matrix between predicted and ground truth instances for a given category."""
    pred_instances = np.unique(pred_rings[pred_labels == category])
    gt_instances = np.unique(gt_rings[gt_labels == category])

    iou_matrix = np.zeros((len(pred_instances), len(gt_instances)))

    for i, pred_ring in enumerate(pred_instances):
        pred_points = np.where((pred_labels == category) & (pred_rings == pred_ring))[0]

        for j, gt_ring in enumerate(gt_instances):
            gt_points = np.where((gt_labels == category) & (gt_rings == gt_ring))[0]
            iou_matrix[i, j] = compute_iou(pred_points, gt_points)

    return iou_matrix, pred_instances, gt_instances
# For one station
import numpy as np
from tqdm import tqdm

iou_thresholds = np.round(np.arange(0.5, 1.0, 0.05), 2) 
categories = [1, 2, 3, 4, 5, 6]  # 0 is background
results = {cat: {'TP': [], 'FP': [], 'FN': []} for cat in categories}

for cat in tqdm(categories, desc='Processing categories', unit='category'):
    # calculate iou matrix
    # iou_matrix, pred_instances, gt_instances = compute_iou_matrix(global_pred_rings, global_gt_rings, pred_labels, gt_labels, cat)
    iou_matrix, pred_instances, gt_instances = compute_iou_matrix(pred_rings, gt_rings, pred_labels, gt_labels, cat)

    for iou_thresh in iou_thresholds:
        TP = 0
        FP = 0
        FN = 0

        # matching results
        matched_pred = set()
        matched_gt = set()

        for i in range(len(pred_instances)):
            for j in range(len(gt_instances)):
                if iou_matrix[i, j] >= iou_thresh:
                    TP += 1
                    matched_pred.add(i)
                    matched_gt.add(j)

        # FP
        FP = len(pred_instances) - len(matched_pred)

        # FN
        FN = len(gt_instances) - len(matched_gt)

        results[cat]['TP'].append(TP)
        results[cat]['FP'].append(FP)
        results[cat]['FN'].append(FN)
for cat in categories:
    print(f"Category: {cat}")
    for idx, iou_thresh in enumerate(iou_thresholds):
        print(f"IoU Threshold: {iou_thresh:.2f}, TP: {results[cat]['TP'][idx]}, "
              f"FP: {results[cat]['FP'][idx]}, FN: {results[cat]['FN'][idx]}")
# Initialize dictionaries to store the aggregated results across all categories
total_results = {'TP': [], 'FP': [], 'FN': []}

# Iterate over all IoU thresholds
for idx, iou_thresh in enumerate(iou_thresholds):
    total_TP, total_FP, total_FN = 0, 0, 0
    
    # Aggregate TP, FP, FN for all categories at this IoU threshold
    for cat in categories:
        total_TP += results[cat]['TP'][idx]
        total_FP += results[cat]['FP'][idx]
        total_FN += results[cat]['FN'][idx]
    
    # Store the aggregated results
    total_results['TP'].append(total_TP)
    total_results['FP'].append(total_FP)
    total_results['FN'].append(total_FN)

# Output the total results
for idx, iou_thresh in enumerate(iou_thresholds):
    print(f"IoU Threshold: {iou_thresh:.2f}, Total TP: {total_results['TP'][idx]}, "
          f"Total FP: {total_results['FP'][idx]}, Total FN: {total_results['FN'][idx]}")
from collections import defaultdict

def average_precision(recalls, precisions, mode='area'):
    """Calculate average precision (for single or multiple scales). this part is from coco"""
    if recalls.ndim == 1:
        recalls = recalls[np.newaxis, :]
        precisions = precisions[np.newaxis, :]
    assert recalls.shape == precisions.shape
    assert recalls.ndim == 2
    num_scales = recalls.shape[0]
    ap = np.zeros(num_scales, dtype=np.float32)
    if mode == 'area':
        zeros = np.zeros((num_scales, 1), dtype=recalls.dtype)
        ones = np.ones((num_scales, 1), dtype=recalls.dtype)
        mrec = np.hstack((zeros, recalls, ones))
        mpre = np.hstack((zeros, precisions, zeros))
        for i in range(mpre.shape[1] - 1, 0, -1):
            mpre[:, i - 1] = np.maximum(mpre[:, i - 1], mpre[:, i])
        for i in range(num_scales):
            ind = np.where(mrec[i, 1:] != mrec[i, :-1])[0]
            ap[i] = np.sum(
                (mrec[i, ind + 1] - mrec[i, ind]) * mpre[i, ind + 1])
    elif mode == '11points':
        for i in range(num_scales):
            for thr in np.arange(0, 1 + 1e-3, 0.1):
                precs = precisions[i, recalls[i, :] >= thr]
                prec = precs.max() if precs.size > 0 else 0
                ap[i] += prec
            ap /= 11
    else:
        raise ValueError(
            'Unrecognized mode, only "area" and "11points" are supported')
    return ap

def calculate_metrics(results):
    class_aps = defaultdict(list)
    ap_per_class_iou = defaultdict(list)
    iou_thresholds = iou_thresholds = np.round(np.arange(0.5, 1.0, 0.05), 2)  # List of IoU thresholds

    # Iterate over all IoU thresholds
    for idx, iou_thresh in enumerate(iou_thresholds):
        for cat in results.keys():
            tp = results[cat]['TP'][idx]
            fp = results[cat]['FP'][idx]
            fn = results[cat]['FN'][idx]

            precision = tp / (tp + fp) if tp + fp > 0 else 0
            recall = tp / (tp + fn) if tp + fn > 0 else 0
            class_aps[cat].append((recall, precision))

            # Calculate AP for this specific class and IoU threshold
            ap = average_precision(np.array([[recall]]), np.array([[precision]]))
            ap_per_class_iou[cat].append((iou_thresh, ap[0]))
    
    # Calculate mAP, mAP50, mAP75, mAP90, and class_mAP
    all_aps = [ap for aps in ap_per_class_iou.values() for _, ap in aps]
    mAP = np.mean(all_aps)
    
    mAP50 = np.mean([ap for cat in ap_per_class_iou.values() for iou, ap in cat if iou == 0.5])
    mAP75 = np.mean([ap for cat in ap_per_class_iou.values() for iou, ap in cat if iou == 0.75])
    mAP90 = np.mean([ap for cat in ap_per_class_iou.values() for iou, ap in cat if iou == 0.9])
    
    class_mAP = {cat: np.mean([ap for _, ap in aps]) for cat, aps in ap_per_class_iou.items()}
    
    return class_aps, ap_per_class_iou, mAP, mAP50, mAP75, mAP90, class_mAP
class_aps, ap_per_class_iou, mAP, mAP50, mAP75, mAP90, class_mAP = calculate_metrics(results)

print(f"mAP: {mAP:.4f}")
print(f"mAP@50: {mAP50:.4f}")
print(f"mAP@75: {mAP75:.4f}")
print(f"mAP@90: {mAP90:.4f}")
print("\nClass-wise mAP:")
for class_id, ap in class_mAP.items():
    print(f"Class {class_id}: {ap:.4f}")
import numpy as np
gt_binary = np.where(gt_labels == 0, 0, 1)
pred_binary = np.where(pred_labels == 0, 0, 1)
# sematic segmentation
def calculate_semantic_metrics(gt_labels, pred_labels):
    num_classes = int(max(max(gt_labels), max(pred_labels)) + 1)
    class_counts = np.zeros(num_classes)
    class_correct = np.zeros(num_classes)
    ious = np.zeros(num_classes)

    for gt, pred in zip(gt_labels.astype(int), pred_labels):
        class_counts[gt] += 1
        if gt == pred:
            class_correct[gt] += 1

    for cls in range(num_classes):
        tp = class_correct[cls]
        fp = np.sum(pred_labels == cls) - tp
        fn = class_counts[cls] - tp
        ious[cls] = tp / (tp + fp + fn) if (tp + fp + fn) > 0 else 0

    overall_accuracy = np.sum(class_correct) / np.sum(class_counts)
    mean_iou = np.mean(ious)
    class_accuracy = class_correct / class_counts
    mean_class_acc = class_accuracy.mean()
    per_class_f1_scores = 2 * (class_accuracy * ious) / (class_accuracy + ious)
    f1_scores = per_class_f1_scores.mean()

    return overall_accuracy, mean_iou, class_accuracy, mean_class_acc, ious, per_class_f1_scores, f1_scores
overall_accuracy, mean_iou, class_accuracy, mean_class_acc, ious, per_class_f1_scores, f1_scores = calculate_semantic_metrics(gt_labels, pred_labels)
overall_accuracy, mean_iou, class_accuracy, mean_class_acc, ious, per_class_f1_scores, f1_scores = calculate_semantic_metrics(gt_binary, pred_binary)
# print(f"overall_accuracy: {overall_accuracy:.4f}")
# print(f"mean_class_accuracy: {mean_class_acc:.4f}")
# print(f"mean_iou: {mean_iou:.4f}")
# print(f"f1_score: {f1_scores:.4f}")

# print("\nclass_accuracy:")
# for idx, acc in enumerate(class_accuracy):
#     print(f"Class {idx}: {acc:.4f}")

# print("\niou_per_class:")
# for idx, iou in enumerate(ious):
#     print(f"Class {idx}: {iou:.4f}")

# print("\nper_class_f1_scores:")
# for idx, f1_score in enumerate(per_class_f1_scores):
#     print(f"Class {idx}: {f1_score:.4f}")

print(f"{overall_accuracy:.4f}")
print(f"{mean_class_acc:.4f}")
print(f"{mean_iou:.4f}")
print(f"{f1_scores:.4f}")

for idx, acc in enumerate(class_accuracy):
    print(f"{acc:.4f}")

for idx, iou in enumerate(ious):
    print(f"{iou:.4f}")

for idx, f1_score in enumerate(per_class_f1_scores):
    print(f"{f1_score:.4f}")

# ================= write evaluation/ artifacts =================
import seaborn as sns
from sklearn.metrics import accuracy_score, f1_score as sklearn_f1_score, jaccard_score

SEGMENT_SCHEMAS = {
    6: {
        "max_class_id": 6,
        "label": "6-class (B2 at index 6)",
        "class_names": {
            0: "Background",
            1: "K-block",
            2: "B1-block",
            3: "A1-block",
            4: "A2-block",
            5: "A3-block",
            6: "B2-block",
        },
    },
    7: {
        "max_class_id": 7,
        "label": "7-class (A4 at 6, B2 at 7)",
        "class_names": {
            0: "Background",
            1: "K-block",
            2: "B1-block",
            3: "A1-block",
            4: "A2-block",
            5: "A3-block",
            6: "A4-block",
            7: "B2-block",
        },
    },
}


def _infer_segment_schema(gt):
    mx_gt = float(np.nanmax(np.asarray(gt, dtype=np.float64))) if len(gt) else 0.0
    return 7 if mx_gt > 6 else 6


def _semantic_metrics_sklearn(gt, pred, class_names):
    gt = np.asarray(gt)
    pred = np.asarray(pred)
    classes = np.sort(np.unique(np.concatenate((np.unique(gt), np.unique(pred)))))
    oa = accuracy_score(gt, pred)
    f1 = sklearn_f1_score(gt, pred, average="macro", labels=classes, zero_division=0)
    iou_per_class = jaccard_score(gt, pred, average=None, labels=classes, zero_division=0)
    miou = float(np.mean(iou_per_class))
    return {
        "OA": oa,
        "F1": f1,
        "mIoU": miou,
        "IoU_per_class": iou_per_class,
        "classes": classes,
        "class_names": class_names,
    }


def _plot_iou_bars(iou_per_class, classes, class_names, output_file):
    class_labels = [class_names.get(c, f"Class {c}") for c in classes]
    plt.figure(figsize=(12, 6))
    colors = plt.cm.viridis(np.linspace(0, 1, len(classes)))
    bars = plt.bar(class_labels, iou_per_class, color=colors)
    plt.axhline(y=np.mean(iou_per_class), color="r", linestyle="-",
                label=f"Mean IoU: {np.mean(iou_per_class):.3f}")
    for bar, iou in zip(bars, iou_per_class):
        plt.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.01,
                 f"{iou:.3f}", ha="center", va="bottom")
    plt.xlabel("Class")
    plt.ylabel("IoU Score")
    plt.title("IoU Scores by Class")
    plt.ylim(0, 1.0)
    plt.legend()
    plt.grid(axis="y", linestyle="--", alpha=0.7)
    plt.tight_layout()
    plt.savefig(output_file)
    plt.close()


def _plot_class_distribution(gt, pred, class_names, output_file):
    classes = sorted(set(np.unique(gt)) | set(np.unique(pred)))
    gt_counts = np.array([np.sum(gt == c) for c in classes])
    pred_counts = np.array([np.sum(pred == c) for c in classes])
    class_labels = [class_names.get(c, f"Class {c}") for c in classes]
    plt.figure(figsize=(10, 8))
    x = np.arange(len(classes))
    width = 0.35
    plt.bar(x - width / 2, gt_counts, width, label="Ground Truth")
    plt.bar(x + width / 2, pred_counts, width, label="Prediction")
    plt.xlabel("Class")
    plt.ylabel("Count")
    plt.title("Class Distribution (Counts)")
    plt.xticks(x, class_labels)
    plt.legend()
    plt.grid(axis="y", linestyle="--", alpha=0.7)
    plt.tight_layout()
    plt.savefig(output_file)
    plt.close()


_eval_dir = paths["evaluation_dir"]
os.makedirs(_eval_dir, exist_ok=True)

_gt_sem = test["gt_labels"].values
_pred_sem = test["pred_labels"].values
_segment_schema = _infer_segment_schema(_gt_sem)
_cfg = SEGMENT_SCHEMAS[_segment_schema]
_max_id = _cfg["max_class_id"]
_class_names = _cfg["class_names"]
_valid = (
    np.isfinite(_gt_sem)
    & np.isfinite(_pred_sem)
    & (_gt_sem <= _max_id)
    & (_pred_sem <= _max_id)
)
_gt_sem = _gt_sem[_valid].astype(int)
_pred_sem = _pred_sem[_valid].astype(int)

_sem = _semantic_metrics_sklearn(_gt_sem, _pred_sem, _class_names)
_plot_iou_bars(
    _sem["IoU_per_class"], _sem["classes"], _class_names,
    os.path.join(_eval_dir, "iou_by_class.png"),
)
_plot_class_distribution(
    _gt_sem, _pred_sem, _class_names,
    os.path.join(_eval_dir, "class_distribution.png"),
)

_markdown_path = os.path.join(_eval_dir, "performance.md")
with open(_markdown_path, "w") as _f:
    _f.write(f"# Performance Metrics for Tunnel {tunnel_id}\n\n")
    _f.write(f"- Segment schema: **{_segment_schema}-class** ({_cfg['label']})\n\n")
    _f.write("## Overall Metrics\n")
    _f.write(f"- Overall Accuracy (OA): {_sem['OA']:.3f}\n")
    _f.write(f"- F1 Score: {_sem['F1']:.3f}\n")
    _f.write(f"- Mean IoU (mIoU): {_sem['mIoU']:.3f}\n\n")
    _f.write("## Per-class IoU\n")
    for _i, _class_idx in enumerate(_sem["classes"]):
        _name = _class_names.get(_class_idx, f"Class {_class_idx}")
        _f.write(f"- {_name}: {_sem['IoU_per_class'][_i]:.3f}\n")
    _f.write("\n## Instance Metrics\n")
    _f.write(f"- mAP: {mAP:.4f}\n")
    _f.write(f"- mAP@50: {mAP50:.4f}\n")
    _f.write(f"- mAP@75: {mAP75:.4f}\n")
    _f.write(f"- mAP@90: {mAP90:.4f}\n")
    _f.write("\n### Class-wise mAP\n")
    for _class_id, _ap in class_mAP.items():
        _f.write(f"- Class {_class_id}: {_ap:.4f}\n")

print(f"Performance metrics saved to {_markdown_path}")
print(f"Evaluation complete -> {_eval_dir}")

