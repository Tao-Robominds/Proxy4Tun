"""Synthetic cyclic label rotations and offline GT mIoU for Release 3 gates."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import jaccard_score

from bo.paths import REPO_ROOT
from bo.release3.rotation_features import shift_labels_cyclic
from bo.runtime.metadata import family_of
from bo.sc_general.label_map import block_to_label_from_config, load_sam_config

SUBSETS = REPO_ROOT / "data" / "subsets"


def offline_gt_miou(run_dir: Path, subset: str) -> float:
    """Mean per-class IoU including background, matching stage-6 semantics."""
    only = pd.read_csv(run_dir / "only_label.csv")
    pred = only["pred_labels"].to_numpy(dtype=int)
    gt = np.loadtxt(SUBSETS / f"{subset}.txt", usecols=(4,))
    if len(gt) != len(pred):
        raise ValueError(f"GT rows {len(gt)} != pred rows {len(pred)} for {subset}")
    gt = gt.astype(int)
    classes = np.sort(np.unique(np.concatenate((np.unique(gt), np.unique(pred)))))
    ious = jaccard_score(gt, pred, average=None, labels=classes, zero_division=0)
    return float(np.mean(ious))


def write_shifted_run(
    src: Path,
    dst: Path,
    *,
    shift: int,
    ring_ids: list[int] | None = None,
    params_dir: Path | None = None,
    light: bool = True,
) -> dict[str, Any]:
    """Create a label-rotated run.

    ``light=True`` (default) copies only final.csv, only_label.csv and SAM
    params — enough for rotation features and offline GT. Full trees are only
    used for the Stage-2 gate when ``light=False``.
    """
    src = Path(src)
    dst = Path(dst)
    if dst.exists():
        for p in dst.rglob("*"):
            try:
                p.chmod(p.stat().st_mode | 0o200)
            except OSError:
                pass
        try:
            dst.chmod(dst.stat().st_mode | 0o200)
        except OSError:
            pass
        shutil.rmtree(dst)
    dst.mkdir(parents=True)

    if light:
        for name in ("final.csv", "only_label.csv", "record.json"):
            if (src / name).exists():
                shutil.copy2(src / name, dst / name)
                (dst / name).chmod((dst / name).stat().st_mode | 0o200)
    else:
        shutil.copytree(
            src,
            dst,
            dirs_exist_ok=True,
            ignore=shutil.ignore_patterns("evaluation", "*.png", "pipeline.log"),
        )
        for p in dst.rglob("*"):
            try:
                p.chmod(p.stat().st_mode | 0o200)
            except OSError:
                pass
        dst.chmod(dst.stat().st_mode | 0o200)

    cfg = load_sam_config(src, params_dir=params_dir)
    _b2l, order = block_to_label_from_config(cfg)
    n = len(order)

    final = pd.read_csv(dst / "final.csv")
    only = pd.read_csv(dst / "only_label.csv")
    if len(final) != len(only):
        raise ValueError(f"final/only_label length mismatch in {src}")

    pred = final["pred"].to_numpy(dtype=int)
    rings = final["pred_ring"].to_numpy(dtype=int)
    if ring_ids is None:
        mask = pred > 0
        pred[mask] = shift_labels_cyclic(pred[mask], shift=shift, n_classes=n)
    else:
        for rid in ring_ids:
            mask = (rings == int(rid)) & (pred > 0)
            pred[mask] = shift_labels_cyclic(pred[mask], shift=shift, n_classes=n)
    final["pred"] = pred
    only["pred_labels"] = pred
    final.to_csv(dst / "final.csv", index=False)
    only.to_csv(dst / "only_label.csv", index=False)

    if params_dir is not None:
        for fname in (
            "parameters_sam.json",
            "parameters_detecting.json",
            "parameters_denoising.json",
            "parameters_enhancing.json",
            "parameters_unfolding.json",
            "parameters_family.json",
        ):
            src_p = Path(params_dir) / fname
            if src_p.exists():
                shutil.copy2(src_p, dst / fname)

    meta = {
        "source": str(src),
        "shift": int(shift),
        "ring_ids": None if ring_ids is None else [int(r) for r in ring_ids],
        "n_classes": n,
        "light": bool(light),
        "family": family_of(Path(src).name) if "-" in Path(src).name else None,
    }
    (dst / "synth_meta.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    return meta
