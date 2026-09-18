#!/usr/bin/env python3
"""BO training scatter: GT mIoU vs proxy on the 120-trial corpus.

Writes:
  paper/Proxy4Tun/figures/proxy_training.{pdf,png,svg}
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
TRAINING = REPO / "bo-elegant" / "family" / "training_table.csv"
MODELS = REPO / "bo-elegant" / "family" / "models.json"
OUT = REPO / "paper" / "Proxy4Tun" / "figures"

FAMILY_COLORS = {"t1&2": "#2C73D2", "t3": "#44BBA4", "t4&5": "#E67E22"}
FAMILY_LABELS = {"t1&2": "Staggered", "t3": "Continuous", "t4&5": "Complex"}
FAMILY_ORDER = ("t1&2", "t3", "t4&5")


def _style() -> None:
    plt.rcParams.update(
        {
            "font.family": "serif",
            "font.size": 10,
            "axes.labelsize": 11,
            "axes.titlesize": 11,
            "legend.fontsize": 9,
            "xtick.labelsize": 9,
            "ytick.labelsize": 9,
            "axes.spines.top": False,
            "axes.spines.right": False,
        }
    )


def _safe_scale(scale: np.ndarray, eps: float = 1e-8) -> np.ndarray:
    out = np.asarray(scale, dtype=float).copy()
    out[~np.isfinite(out)] = 1.0
    out[np.abs(out) < eps] = 1.0
    return out


def _predict(model: dict, df: pd.DataFrame) -> np.ndarray:
    feats = model["features"]
    X = df[feats].astype(float).to_numpy()
    mean = np.asarray(model["scaler_mean"], dtype=float)
    scale = _safe_scale(np.asarray(model["scaler_scale"], dtype=float))
    return (X - mean) / scale @ np.asarray(model["coef"], dtype=float) + float(model["intercept"])


def main() -> None:
    _style()
    df = pd.read_csv(TRAINING)
    models = json.loads(MODELS.read_text(encoding="utf-8"))
    pred = _predict(models["model"], df)
    y = df["mIoU"].astype(float).to_numpy()
    mae = float(np.mean(np.abs(y - pred)))

    fig, ax = plt.subplots(figsize=(5.2, 4.8))
    for fam in FAMILY_ORDER:
        idx = (df["family"] == fam).to_numpy()
        ax.scatter(
            y[idx],
            pred[idx],
            c=FAMILY_COLORS[fam],
            s=36,
            alpha=0.75,
            edgecolors="white",
            linewidths=0.35,
            label=FAMILY_LABELS[fam],
        )
    lims = [-0.15, 1.05]
    ax.plot(lims, lims, ls="--", color="gray", lw=0.9, alpha=0.75)
    ax.set_xlim(lims)
    ax.set_ylim(lims)
    ax.set_xlabel("GT mIoU")
    ax.set_ylabel(r"Proxy $\hat{y}$")
    ax.set_title("BO-driven proxy training")
    ax.set_aspect("equal", adjustable="box")
    ax.legend(frameon=False, loc="lower right")
    ax.text(
        0.04,
        0.96,
        f"MAE = {mae:.3f}\n$n$ = {len(df)}",
        transform=ax.transAxes,
        va="top",
        ha="left",
        fontsize=9,
        bbox=dict(boxstyle="round,pad=0.25", facecolor="white", edgecolor="#cccccc", alpha=0.9),
    )
    OUT.mkdir(parents=True, exist_ok=True)
    out = OUT / "proxy_training.pdf"
    fig.savefig(out, bbox_inches="tight")
    fig.savefig(out.with_suffix(".png"), dpi=200, bbox_inches="tight")
    fig.savefig(out.with_suffix(".svg"), bbox_inches="tight")
    plt.close(fig)
    print(f"Wrote {out} (+ png/svg)")


if __name__ == "__main__":
    main()
