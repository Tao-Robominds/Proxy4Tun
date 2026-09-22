#!/usr/bin/env python3
"""Leave-one-family-out comparison and frozen four-feature proxy.

Feature sets are prespecified. Scaling and the Ridge penalty are chosen
inside each training split. Reported predictions are clipped to [0, 1].

Usage:
  ./venv/bin/python bo/release2/fit_proxy.py
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

from bo.paths import RELEASE2_DATA, REPO_ROOT  # noqa: E402
from bo.runtime.ridge import fit_ridge, predict  # noqa: E402

TABLE = RELEASE2_DATA / "calibration" / "records" / "training_table.csv"
OUT = RELEASE2_DATA / "proxy"
MODEL_PATH = REPO_ROOT / "configs" / "proxy" / "four_feature.json"

PQ = [
    "unfold_residual",
    "orient_agreement",
    "denoise_retained_ratio",
    "depth_nan_ratio",
]
SC = [
    "ring_count_error",
    "boundary_explained_edge@25",
    "correspondence_f1@15",
    "chamfer_sym_px",
    "sam_fill_rate",
    "phase_incoherence_deg",
]
TEN = PQ + SC
FOUR = [
    "correspondence_f1@15",
    "sam_fill_rate",
    "ring_count_error",
    "depth_nan_ratio",
]
SETS = {"PQ": PQ, "SC": SC, "ten": TEN, "four": FOUR}
PERM_REPEATS = 20
PERM_SEED = 0


def _clip(pred: np.ndarray) -> np.ndarray:
    return np.clip(np.asarray(pred, dtype=float), 0.0, 1.0)


def _spearman(y: np.ndarray, pred: np.ndarray) -> float:
    if len(y) < 3 or np.unique(y).size < 2 or np.unique(pred).size < 2:
        return float("nan")
    rho = stats.spearmanr(y, pred).correlation
    return float(rho) if rho is not None and np.isfinite(rho) else float("nan")


def lofo(df: pd.DataFrame, features: list[str]) -> tuple[pd.DataFrame, dict[str, float]]:
    """Per-fold and pooled LOFO. Predictions clipped to [0, 1]."""
    frames = []
    for fam in sorted(df["family"].unique()):
        train = df[df["family"] != fam]
        test = df[df["family"] == fam]
        model = fit_ridge(train, features)
        pred = _clip(predict(model, test))
        y = test["mIoU"].to_numpy(dtype=float)
        part = test[["family", "dev", "trial_id"]].copy()
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
    return pooled, summary


def permute(df: pd.DataFrame, features: list[str]) -> dict:
    rng = np.random.default_rng(PERM_SEED)
    real = lofo(df, features)[1]["pooled_spearman"]
    values = []
    for _ in range(PERM_REPEATS):
        shuffled = df.copy()
        for fam in shuffled["family"].unique():
            idx = shuffled.index[shuffled["family"] == fam]
            vals = shuffled.loc[idx, "mIoU"].to_numpy().copy()
            rng.shuffle(vals)
            shuffled.loc[idx, "mIoU"] = vals
        values.append(lofo(shuffled, features)[1]["pooled_spearman"])
    arr = np.asarray(values, dtype=float)
    return {
        "unpermuted_spearman": real,
        "n": PERM_REPEATS,
        "seed": PERM_SEED,
        "perm_spearman": [None if not np.isfinite(v) else float(v) for v in arr],
        "perm_mean": float(np.nanmean(arr)),
        "perm_std": float(np.nanstd(arr)),
        "perm_min": float(np.nanmin(arr)),
        "perm_max": float(np.nanmax(arr)),
    }


def _git_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=_REPO, text=True
        ).strip()
    except Exception:  # noqa: BLE001
        return "unknown"


def freeze(df: pd.DataFrame) -> dict:
    model = fit_ridge(df, FOUR)
    table_hash = hashlib.sha256(TABLE.read_bytes()).hexdigest()
    payload = {
        "features": FOUR,
        "mu": model["scaler_mean"],
        "sigma": model["scaler_scale"],
        "w": model["coef"],
        "intercept": model["intercept"],
        "alpha": model["alpha"],
        "n_train": model["n_train"],
        "training_table_sha256": table_hash,
        "git_commit": _git_commit(),
        "created_at": datetime.now().isoformat(timespec="seconds"),
    }
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, indent=2) + "\n"
    MODEL_PATH.write_text(text, encoding="utf-8")
    (OUT / "four_feature.json").write_text(text, encoding="utf-8")
    return payload


def main() -> int:
    if not TABLE.exists():
        raise SystemExit(f"missing {TABLE}")
    df = pd.read_csv(TABLE)
    if len(df) != 120:
        raise SystemExit(f"expected 120 training rows, found {len(df)}")
    df["mIoU"] = df["gt_miou"].astype(float)
    OUT.mkdir(parents=True, exist_ok=True)

    lofo_rows = []
    perm_rows = []
    lines = ["# Proxy comparison", "", f"Training rows: {len(df)}", ""]
    for name, feats in SETS.items():
        _pooled, summary = lofo(df, feats)
        row = {"set": name, "n_features": len(feats), **summary}
        lofo_rows.append(row)
        perm = permute(df, feats)
        perm_rows.append({"set": name, **{k: v for k, v in perm.items() if k != "perm_spearman"}, "perm_spearman": json.dumps(perm["perm_spearman"])})
        lines.append(
            f"- {name}: pooled Spearman {summary['pooled_spearman']:.3f}, "
            f"MAE {summary['pooled_mae']:.3f}; "
            f"permutation mean {perm['perm_mean']:.3f} "
            f"(std {perm['perm_std']:.3f}) vs unpermuted {perm['unpermuted_spearman']:.3f}"
        )
        for fam in sorted(df["family"].unique()):
            lines.append(
                f"  - {fam}: Spearman {summary[f'spearman_{fam}']:.3f}, "
                f"MAE {summary[f'mae_{fam}']:.3f}"
            )
    pd.DataFrame(lofo_rows).to_csv(OUT / "lofo.csv", index=False)
    pd.DataFrame(perm_rows).to_csv(OUT / "permutations.csv", index=False)
    (OUT / "comparison.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    frozen = freeze(df)
    lines.append("")
    lines.append(
        f"Frozen four-feature model: alpha={frozen['alpha']}, "
        f"intercept={frozen['intercept']:.6f}, n={frozen['n_train']}"
    )
    (OUT / "comparison.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {OUT / 'comparison.md'}")
    print(f"wrote {MODEL_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
