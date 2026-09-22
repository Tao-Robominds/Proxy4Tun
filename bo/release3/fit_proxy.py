#!/usr/bin/env python3
"""Fit and freeze the Release-3 five-feature proxy.

Compares four-feature vs five-feature (adds rotation_advantage) under LOFO and
permutations, on the original 120 rows and on the augmented table.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.metrics import mean_absolute_error

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from bo.paths import RELEASE3_DATA, REPO_ROOT  # noqa: E402
from bo.runtime.ridge import fit_ridge, predict  # noqa: E402

TABLE = RELEASE3_DATA / "calibration" / "records" / "training_table.csv"
OUT = RELEASE3_DATA / "proxy"
MODEL_PATH = REPO_ROOT / "configs" / "proxy" / "five_feature.json"

FOUR = [
    "correspondence_f1@15",
    "sam_fill_rate",
    "ring_count_error",
    "depth_nan_ratio",
]
FIVE = FOUR + ["rotation_advantage"]
SETS = {"four": FOUR, "five": FIVE}
PERM_REPEATS = 20
PERM_SEED = 0


def _clip(pred: np.ndarray) -> np.ndarray:
    return np.clip(np.asarray(pred, dtype=float), 0.0, 1.0)


def _spearman(y: np.ndarray, pred: np.ndarray) -> float:
    if len(y) < 3 or np.unique(y).size < 2 or np.unique(pred).size < 2:
        return float("nan")
    rho = stats.spearmanr(y, pred).correlation
    return float(rho) if rho is not None and np.isfinite(rho) else float("nan")


def lofo(df: pd.DataFrame, features: list[str]) -> dict[str, float]:
    frames = []
    for fam in sorted(df["family"].unique()):
        train = df[df["family"] != fam]
        test = df[df["family"] == fam]
        model = fit_ridge(train, features)
        pred = _clip(predict(model, test))
        y = test["mIoU"].to_numpy(dtype=float)
        part = test[["family"]].copy()
        part["y"] = y
        part["pred"] = pred
        part["fold"] = fam
        frames.append(part)
    pooled = pd.concat(frames, ignore_index=True)
    summary = {
        "pooled_spearman": _spearman(pooled["y"].to_numpy(), pooled["pred"].to_numpy()),
        "pooled_mae": float(mean_absolute_error(pooled["y"], pooled["pred"])),
    }
    for fam, g in pooled.groupby("fold"):
        summary[f"spearman_{fam}"] = _spearman(g["y"].to_numpy(), g["pred"].to_numpy())
        summary[f"mae_{fam}"] = float(mean_absolute_error(g["y"], g["pred"]))
    return summary


def permute(df: pd.DataFrame, features: list[str]) -> dict:
    rng = np.random.default_rng(PERM_SEED)
    real = lofo(df, features)["pooled_spearman"]
    values = []
    for _ in range(PERM_REPEATS):
        shuffled = df.copy()
        for fam in shuffled["family"].unique():
            idx = shuffled.index[shuffled["family"] == fam]
            vals = shuffled.loc[idx, "mIoU"].to_numpy().copy()
            rng.shuffle(vals)
            shuffled.loc[idx, "mIoU"] = vals
        values.append(lofo(shuffled, features)["pooled_spearman"])
    arr = np.asarray(values, dtype=float)
    return {
        "unpermuted_spearman": real,
        "perm_mean": float(np.nanmean(arr)),
        "perm_std": float(np.nanstd(arr)),
    }


def _git_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=_REPO, text=True).strip()
    except Exception:  # noqa: BLE001
        return "unknown"


def freeze(df: pd.DataFrame) -> dict:
    model = fit_ridge(df, FIVE)
    table_hash = hashlib.sha256(TABLE.read_bytes()).hexdigest()
    payload = {
        "features": FIVE,
        "mu": model["scaler_mean"],
        "sigma": model["scaler_scale"],
        "w": model["coef"],
        "intercept": model["intercept"],
        "alpha": model["alpha"],
        "n_train": model["n_train"],
        "training_table_sha256": table_hash,
        "git_commit": _git_commit(),
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "note": "five-feature Release-3 proxy; rotation_advantage from template-free width mismatch",
    }
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, indent=2) + "\n"
    MODEL_PATH.write_text(text, encoding="utf-8")
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "five_feature.json").write_text(text, encoding="utf-8")
    return payload


def main() -> int:
    df = pd.read_csv(TABLE)
    df["mIoU"] = df["gt_miou"].astype(float)
    df["synthetic"] = df["synthetic"].astype(str).str.lower().eq("true")
    # Drop rows missing the fifth feature.
    df = df[np.isfinite(df["rotation_advantage"].astype(float))].copy()
    orig = df[~df["synthetic"]].copy()
    if len(orig) < 100:
        raise SystemExit(f"expected many original rows, found {len(orig)}")

    OUT.mkdir(parents=True, exist_ok=True)
    lines = ["# Release 3 proxy comparison", "", f"Rows: original {len(orig)}, augmented {len(df)}", ""]
    summaries = {}
    for label, part in (("original120", orig), ("augmented", df)):
        lines.append(f"## {label}")
        lines.append("")
        summaries[label] = {}
        for name, feats in SETS.items():
            summary = lofo(part, feats)
            perm = permute(part, feats)
            summaries[label][name] = {**summary, **perm}
            lines.append(
                f"- {name}: Spearman {summary['pooled_spearman']:.3f}, "
                f"MAE {summary['pooled_mae']:.3f}; "
                f"perm mean {perm['perm_mean']:.3f} vs unpermuted {perm['unpermuted_spearman']:.3f}"
            )
        lines.append("")

    # Freeze on augmented table (user decision).
    payload = freeze(df)
    lines.append("## Frozen model")
    lines.append("")
    lines.append(f"- Path: `{MODEL_PATH}`")
    lines.append(f"- Features: {payload['features']}")
    lines.append(f"- n_train: {payload['n_train']}, alpha: {payload['alpha']:.4g}")
    lines.append(f"- weights: {list(zip(payload['features'], payload['w']))}")

    (OUT / "comparison.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (OUT / "comparison.json").write_text(json.dumps(summaries, indent=2) + "\n", encoding="utf-8")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
