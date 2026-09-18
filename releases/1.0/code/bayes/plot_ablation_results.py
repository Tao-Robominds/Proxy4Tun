#!/usr/bin/env python3
"""Native vector two-panel ablation_results.pdf from frozen bo-bayes snapshot."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from scipy import stats
from sklearn.linear_model import RidgeCV
from sklearn.metrics import mean_absolute_error
from sklearn.preprocessing import StandardScaler

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))
from bo.paths import BAYES_PKG, MANUSCRIPT_FIGS
from bo.elegant.features import CANDIDATE, COHERENCE, EVIDENCE  # noqa: E402

BAYES = BAYES_PKG
OUT = MANUSCRIPT_FIGS
TRAIN = BAYES / "training_table.csv"
HOLDOUT = BAYES / "holdout_scores.csv"
MODELS = BAYES / "models.json"

FAMILY_COLORS = {
    "staggered": "#2C73D2",
    "continuous": "#44BBA4",
    "complex": "#E67E22",
}
FAMILY_ORDER = ("staggered", "continuous", "complex")
VARIANT_STYLE = {
    "p(e)": {"color": "#7F8C8D", "ls": ":", "lw": 1.8, "zorder": 2},
    "p(c)": {"color": "#8E44AD", "ls": ":", "lw": 1.8, "zorder": 2},
    "p(e+c)": {"color": "#2980B9", "ls": ":", "lw": 2.2, "zorder": 5},
    "lean p(e+c)": {"color": "#1A1A1A", "ls": "-", "lw": 1.0, "zorder": 4},
}


def _paper_style() -> None:
    plt.rcParams.update(
        {
            "font.family": "Lato",
            "font.sans-serif": ["Lato", "DejaVu Sans", "sans-serif"],
            "font.size": 12,
            "axes.labelsize": 13,
            "axes.titlesize": 13,
            "legend.fontsize": 9,
            "xtick.labelsize": 11,
            "ytick.labelsize": 11,
            "axes.spines.top": False,
            "axes.spines.right": False,
        }
    )


def _safe_scale(scale: np.ndarray, eps: float = 1e-8) -> np.ndarray:
    out = np.asarray(scale, dtype=float).copy()
    out[~np.isfinite(out)] = 1.0
    out[np.abs(out) < eps] = 1.0
    return out


def _fit_ridge(df: pd.DataFrame, features: list[str]) -> dict[str, Any]:
    X = df[features].astype(float).to_numpy()
    y = df["mIoU"].astype(float).to_numpy()
    scaler = StandardScaler()
    scaler.fit(X)
    mean = np.asarray(scaler.mean_, dtype=float)
    scale = _safe_scale(scaler.scale_)
    Xs = (X - mean) / scale
    model = RidgeCV(alphas=np.logspace(-3, 3, 25))
    model.fit(Xs, y)
    pred = model.predict(Xs)
    return {
        "scaler_mean": mean.tolist(),
        "scaler_scale": scale.tolist(),
        "coef": model.coef_.tolist(),
        "intercept": float(model.intercept_),
        "features": list(features),
        "train_mae": float(mean_absolute_error(y, pred)),
        "train_spearman": float(stats.spearmanr(y, pred).correlation or 0.0),
    }


def _predict(model: dict, df: pd.DataFrame) -> np.ndarray:
    feats = model["features"]
    X = df[feats].astype(float).to_numpy()
    mean = np.asarray(model["scaler_mean"], dtype=float)
    scale = _safe_scale(np.asarray(model["scaler_scale"], dtype=float))
    return (X - mean) / scale @ np.asarray(model["coef"]) + float(model["intercept"])


def _trend_line(ax, x, y, *, color, ls, lw, zorder) -> None:
    mask = np.isfinite(x) & np.isfinite(y)
    x, y = x[mask], y[mask]
    if len(x) < 2:
        return
    slope, intercept = np.polyfit(x, y, 1)
    x_line = np.linspace(float(np.min(x)), float(np.max(x)), 100)
    ax.plot(x_line, slope * x_line + intercept, color=color, ls=ls, lw=lw, zorder=zorder)


def _draw_training(ax, lean_model: dict) -> tuple[float, float]:
    df = pd.read_csv(TRAIN)
    all_feats = list(dict.fromkeys(list(CANDIDATE) + list(lean_model["features"])))
    for f in all_feats:
        if f in df.columns:
            df[f] = df[f].astype(float).fillna(0.0)

    variants = {
        "p(e)": _fit_ridge(df, list(EVIDENCE)),
        "p(c)": _fit_ridge(df, list(COHERENCE)),
        "p(e+c)": _fit_ridge(df, list(CANDIDATE)),
        "lean p(e+c)": lean_model,
    }
    preds = {name: _predict(m, df) for name, m in variants.items()}
    df["proxy"] = preds["lean p(e+c)"]
    lims = [-0.05, 1.05]

    for fam in FAMILY_ORDER:
        sub = df[df["family"] == fam]
        ax.scatter(
            sub["mIoU"],
            sub["proxy"],
            c=FAMILY_COLORS[fam],
            marker="o",
            s=28,
            alpha=0.9,
            edgecolors="white",
            linewidths=0.3,
            zorder=3,
        )
    x_gt = df["mIoU"].to_numpy(dtype=float)
    for name in ("lean p(e+c)", "p(e)", "p(c)", "p(e+c)"):
        _trend_line(ax, x_gt, np.asarray(preds[name], dtype=float), **VARIANT_STYLE[name])

    ax.set_xlim(lims)
    ax.set_ylim(lims)
    ax.set_xlabel("GT mIoU")
    ax.set_ylabel(r"Proxy $\hat{y}$")
    ax.set_title("(a) Training: 40 trials × 3 anchors")
    ax.set_aspect("equal", adjustable="box")

    fam_handles = [
        Line2D(
            [0],
            [0],
            marker="o",
            color="w",
            markerfacecolor=FAMILY_COLORS[f],
            markersize=6,
            label=f.capitalize(),
        )
        for f in FAMILY_ORDER
    ]
    line_handles = [
        Line2D(
            [0],
            [0],
            color=VARIANT_STYLE[n]["color"],
            ls=VARIANT_STYLE[n]["ls"],
            lw=VARIANT_STYLE[n]["lw"],
            label="Lean p(e+c)" if n == "lean p(e+c)" else n,
        )
        for n in ("lean p(e+c)", "p(e)", "p(c)", "p(e+c)")
    ]
    leg1 = ax.legend(handles=fam_handles, frameon=False, loc="upper left", fontsize=9)
    ax.add_artist(leg1)
    ax.legend(handles=line_handles, frameon=False, loc="lower right", fontsize=9, title="Proxy")

    mae = float(lean_model["train_mae"])
    sp = float(lean_model["train_spearman"])
    ax.text(0.98, 0.98, f"MAE={mae:.3f}\nSpearman={sp:.3f}", transform=ax.transAxes, va="top", ha="right")
    return mae, sp


def _draw_holdout(ax, lean_model: dict) -> tuple[float, float]:
    hs = pd.read_csv(HOLDOUT)
    hs = hs[hs["status"] == "ok"].copy()
    lean_feats = list(lean_model["features"])
    for f in lean_feats:
        if f in hs.columns:
            hs[f] = hs[f].astype(float).fillna(0.0)

    alarm = 0.5
    train = pd.read_csv(TRAIN)
    for f in lean_feats:
        if f in train.columns:
            train[f] = train[f].astype(float).fillna(0.0)
    fam_preds: dict[str, np.ndarray] = {}
    for fam in FAMILY_ORDER:
        fam_model = _fit_ridge(train[train["family"] == fam], lean_feats)
        fam_preds[fam] = _predict(fam_model, hs)

    raw_proxy = hs["proxy"].to_numpy(dtype=float)
    holdout_mae = float(mean_absolute_error(hs["mIoU"], raw_proxy))
    holdout_sp = float(stats.spearmanr(hs["mIoU"], raw_proxy).correlation or 0.0)
    # Display scaling keeps alarm at 0.5; metrics use raw predictions.
    all_raw = np.concatenate([raw_proxy, *[fam_preds[f] for f in FAMILY_ORDER]])
    half = float(max(alarm - float(np.min(all_raw)), float(np.max(all_raw)) - alarm))
    lo, hi = alarm - half, alarm + half

    def _scale01(y: np.ndarray) -> np.ndarray:
        return (np.asarray(y, dtype=float) - lo) / (hi - lo)

    hs["proxy"] = _scale01(raw_proxy)
    for fam in FAMILY_ORDER:
        fam_preds[fam] = _scale01(fam_preds[fam])

    lims = [-0.05, 1.05]
    ax.hlines(alarm, lims[0], 0.3, color="#FF0000", ls="--", lw=0.9, zorder=7)
    ax.vlines(0.3, lims[0], 0.5, color="#FF0000", ls="--", lw=0.9, zorder=7)
    ax.hlines(0.5, 0.3, 0.7, color="#F1C40F", ls="--", lw=0.9, zorder=7)
    ax.hlines(0.7, 0.3, 0.7, color="#F1C40F", ls="--", lw=0.9, zorder=7)
    ax.vlines(0.3, 0.5, 0.7, color="#F1C40F", ls="--", lw=0.9, zorder=7)
    ax.vlines(0.7, 0.5, 0.7, color="#F1C40F", ls="--", lw=0.9, zorder=7)

    for fam in FAMILY_ORDER:
        sub = hs[hs["family"] == fam]
        ax.scatter(
            sub["mIoU"],
            sub["proxy"],
            c=FAMILY_COLORS[fam],
            marker="o",
            s=28,
            alpha=0.9,
            edgecolors="white",
            linewidths=0.3,
            zorder=3,
        )

    x_gt = hs["mIoU"].to_numpy(dtype=float)
    _trend_line(ax, x_gt, hs["proxy"].to_numpy(dtype=float), color="#1A1A1A", ls="-", lw=1.0, zorder=5)
    for fam in FAMILY_ORDER:
        mask = (hs["family"] == fam).to_numpy()
        _trend_line(ax, x_gt[mask], fam_preds[fam][mask], color=FAMILY_COLORS[fam], ls=":", lw=1.8, zorder=6)

    ax.set_xlim(lims)
    ax.set_ylim(lims)
    ax.set_xlabel("GT mIoU")
    ax.set_ylabel(r"Proxy $\hat{y}$")
    ax.set_title("Holdout: 9 subsets × 3 families")
    ax.set_aspect("equal", adjustable="box")

    top_handles = [
        Line2D(
            [0],
            [0],
            marker="o",
            color="w",
            markerfacecolor=FAMILY_COLORS[f],
            markersize=6,
            label=f.capitalize(),
        )
        for f in FAMILY_ORDER
    ]
    line_handles = [Line2D([0], [0], color="#1A1A1A", ls="-", lw=1.0, label="Unified")] + [
        Line2D([0], [0], color=FAMILY_COLORS[f], ls=":", lw=1.8, label=f.capitalize())
        for f in FAMILY_ORDER
    ]
    leg1 = ax.legend(handles=top_handles, frameon=False, loc="upper left", fontsize=9)
    ax.add_artist(leg1)
    ax.legend(handles=line_handles, frameon=False, loc="lower right", fontsize=9, title="Lean p(e+c)")
    ax.text(
        0.95,
        0.98,
        f"MAE={holdout_mae:.3f}\nSpearman={holdout_sp:.3f}",
        transform=ax.transAxes,
        va="top",
        ha="right",
    )
    # panel (b) label
    ax.set_title("(b) Holdout: 9 subsets × 3 families")
    return holdout_mae, holdout_sp


def main() -> None:
    _paper_style()
    OUT.mkdir(parents=True, exist_ok=True)
    lean = json.loads(MODELS.read_text(encoding="utf-8"))["model"]
    fig, axes = plt.subplots(1, 2, figsize=(12.4, 6.2))
    train_mae, train_sp = _draw_training(axes[0], lean)
    hold_mae, hold_sp = _draw_holdout(axes[1], lean)
    fig.tight_layout()
    out = OUT / "ablation_results.pdf"
    fig.savefig(out, bbox_inches="tight")
    fig.savefig(out.with_suffix(".png"), dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"Wrote {out}")
    print(f"train MAE={train_mae:.3f} Spearman={train_sp:.3f}")
    print(f"holdout MAE={hold_mae:.3f} Spearman={hold_sp:.3f}")
    assert abs(train_mae - 0.098) < 0.002 and abs(train_sp - 0.877) < 0.002
    assert abs(hold_mae - 0.086) < 0.002 and abs(hold_sp - 0.827) < 0.002


if __name__ == "__main__":
    main()
