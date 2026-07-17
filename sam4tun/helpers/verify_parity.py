#!/usr/bin/env python3
"""Verify modular pipeline matches monolith SAM4Tun.py outputs."""

import argparse
import os
import sys

import numpy as np
import pandas as pd

from helpers.pipeline_io import SAM4TUN_ROOT, _out_root, pipeline_dir


def miou7(path: str) -> tuple[float, float]:
    df = pd.read_csv(path)
    gt = df["gt_labels"].values
    pred = df["pred_labels"].values
    ious = []
    for c in sorted(set(gt) | set(pred)):
        inter = ((gt == c) & (pred == c)).sum()
        union = ((gt == c) | (pred == c)).sum()
        ious.append(inter / union if union else 0.0)
    return float((gt == pred).mean()), float(np.mean(ious))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tunnel_id", help="e.g. sample")
    parser.add_argument(
        "--out-root",
        default=None,
        help="Modular artifact root (default: PROXY4TUN_OUT_ROOT or sam4tun/data)",
    )
    parser.add_argument(
        "--monolith-dir",
        default=os.path.join(SAM4TUN_ROOT, "data", "monolith"),
        help="Directory with monolith outputs (only_label.csv, etc.)",
    )
    args = parser.parse_args()

    if args.out_root:
        os.environ["PROXY4TUN_OUT_ROOT"] = os.path.abspath(args.out_root)

    mod_only = os.path.join(pipeline_dir(args.tunnel_id), "only_label.csv")
    mono_only = os.path.join(args.monolith_dir, "only_label.csv")

    print(f"Modular root: {_out_root()}")
    if not os.path.exists(mod_only):
        print(f"Missing modular output: {mod_only}", file=sys.stderr)
        sys.exit(1)
    if not os.path.exists(mono_only):
        print(f"Missing monolith output: {mono_only}", file=sys.stderr)
        sys.exit(1)

    m = pd.read_csv(mono_only)
    d = pd.read_csv(mod_only)
    pred_match = (m["pred_labels"].values == d["pred_labels"].values).all()
    ring_match = (m["pred_rings"].values == d["pred_rings"].values).all()
    mono_oa, mono_miou = miou7(mono_only)
    mod_oa, mod_miou = miou7(mod_only)

    print(f"Monolith: OA={mono_oa:.6f}  7-class mIoU={mono_miou:.6f}")
    print(f"Modular:  OA={mod_oa:.6f}  7-class mIoU={mod_miou:.6f}")
    print(f"pred_labels identical: {pred_match}")
    print(f"pred_rings identical:  {ring_match}")

    if not pred_match:
        n = int((m["pred_labels"].values != d["pred_labels"].values).sum())
        print(f"pred_labels diffs: {n} / {len(m)} ({100 * n / len(m):.4f}%)")

    sys.exit(0 if pred_match and ring_match else 1)


if __name__ == "__main__":
    main()
