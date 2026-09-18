#!/usr/bin/env python3
"""Training + holdout figures for bo-full-stage proxy.

Writes:
  paper/Proxy4Tun/figures/proxy_training_fullstage.{pdf,png,svg}
  paper/Proxy4Tun/figures/proxy_holdout_fullstage.{pdf,png,svg}
"""
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

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "bo-elegant"))
from features import CANDIDATE, COHERENCE, EVIDENCE  # noqa: E402

OUT = REPO / "paper" / "Proxy4Tun" / "figures"
TRAIN = REPO / "bo-full-stage" / "training_table.csv"
HOLDOUT = REPO / "bo-full-stage" / "holdout_scores.csv"
MODELS = REPO / "bo-full-stage" / "models.json"

FAMILY_COLORS = {
    "staggered": "#2C73D2",
    "continuous": "#44BBA4",
    "complex": "#E67E22",
}
FAMILY_ORDER = ("staggered", "continuous", "complex")

# Trend-line styles: lean solid/thin so dotted p(e+c) stays readable on top.
VARIANT_STYLE = {
    "p(e)": {"color": "#7F8C8D", "ls": ":", "lw": 1.8, "zorder": 2},
    "p(c)": {"color": "#8E44AD", "ls": ":", "lw": 1.8, "zorder": 2},
    "p(e+c)": {"color": "#2980B9", "ls": ":", "lw": 2.2, "zorder": 5},
    "lean p(e+c)": {"color": "#1A1A1A", "ls": "-", "lw": 1.0, "zorder": 4},
}


def _style() -> None:
    plt.rcParams.update(
        {
            "font.family": "serif",
            "font.size": 10,
            "axes.labelsize": 11,
            "axes.titlesize": 11,
            "legend.fontsize": 8,
            "xtick.labelsize": 9,
            "ytick.labelsize": 9,
            "axes.spines.top": False,
            "axes.spines.right": False,
        }
    )


def _paper_style() -> None:
    """Lato + 50% larger text for paper figures."""
    plt.rcParams.update(
        {
            "font.family": "Lato",
            "font.sans-serif": ["Lato", "DejaVu Sans", "sans-serif"],
            "font.size": 15,
            "axes.labelsize": 16.5,
            "axes.titlesize": 16.5,
            "legend.fontsize": 12,
            "xtick.labelsize": 13.5,
            "ytick.labelsize": 13.5,
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


def _trend_line(ax, x: np.ndarray, y: np.ndarray, *, color: str, ls: str, lw: float, zorder: int) -> None:
    """Least-squares line of y vs x over the observed x-range."""
    mask = np.isfinite(x) & np.isfinite(y)
    x, y = x[mask], y[mask]
    if len(x) < 2:
        return
    slope, intercept = np.polyfit(x, y, 1)
    x_line = np.linspace(float(np.min(x)), float(np.max(x)), 100)
    ax.plot(x_line, slope * x_line + intercept, color=color, ls=ls, lw=lw, zorder=zorder)


def plot_training(lean_model: dict) -> None:
    _paper_style()
    df = pd.read_csv(TRAIN)
    all_feats = list(dict.fromkeys(list(CANDIDATE) + list(lean_model["features"])))
    for f in all_feats:
        if f in df.columns:
            df[f] = df[f].astype(float).fillna(0.0)

    variants: dict[str, dict[str, Any]] = {
        "p(e)": _fit_ridge(df, list(EVIDENCE)),
        "p(c)": _fit_ridge(df, list(COHERENCE)),
        "p(e+c)": _fit_ridge(df, list(CANDIDATE)),
        "lean p(e+c)": lean_model,
    }
    preds = {name: _predict(m, df) for name, m in variants.items()}
    df["proxy"] = preds["lean p(e+c)"]

    fig, ax = plt.subplots(figsize=(6.2, 6.0))
    lims = [-0.05, 1.05]

    for fam in FAMILY_ORDER:
        sub = df[df["family"] == fam]
        ax.scatter(
            sub["mIoU"],
            sub["proxy"],
            c=FAMILY_COLORS[fam],
            marker="o",
            s=34,
            alpha=0.9,
            edgecolors="white",
            linewidths=0.35,
            zorder=3,
        )

    x_gt = df["mIoU"].to_numpy(dtype=float)
    # Draw lean first (underneath), then dotted variants so p(e+c) stays visible.
    for name in ("lean p(e+c)", "p(e)", "p(c)", "p(e+c)"):
        style = VARIANT_STYLE[name]
        _trend_line(ax, x_gt, np.asarray(preds[name], dtype=float), **style)

    ax.set_xlim(lims)
    ax.set_ylim(lims)
    ax.set_xlabel("GT mIoU", labelpad=12)
    ax.set_ylabel(r"Proxy $\hat{y}$")
    ax.set_title("Training: 40 trials × 3 anchors")
    ax.set_aspect("equal", adjustable="box")

    fam_handles = [
        Line2D(
            [0],
            [0],
            marker="o",
            color="w",
            markerfacecolor=FAMILY_COLORS[f],
            markersize=6.4,
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
            label="Lean" if n == "lean p(e+c)" else n,
        )
        for n in ("lean p(e+c)", "p(e)", "p(c)", "p(e+c)")
    ]
    # Match holdout layout: families top-left, proxy lines bottom-right with a shared title.
    leg1 = ax.legend(handles=fam_handles, frameon=False, loc="upper left", fontsize=12)
    ax.add_artist(leg1)
    ax.legend(
        handles=line_handles,
        frameon=False,
        loc="lower right",
        fontsize=12,
        title="Proxy",
        title_fontsize=12,
    )

    mae = float(lean_model["train_mae"])
    sp = float(lean_model["train_spearman"])
    ax.text(
        0.98,
        0.98,
        f"MAE={mae:.3f}\nSpearman={sp:.3f}",
        transform=ax.transAxes,
        va="top",
        ha="right",
        fontsize=12,
    )
    fig.tight_layout()
    out = OUT / "proxy_training_fullstage.pdf"
    fig.savefig(out, bbox_inches="tight")
    fig.savefig(out.with_suffix(".png"), dpi=200, bbox_inches="tight")
    fig.savefig(out.with_suffix(".svg"), bbox_inches="tight")
    plt.close(fig)
    _style()
    print(f"Wrote {out}")


def plot_holdout(lean_model: dict) -> None:
    _paper_style()
    hs = pd.read_csv(HOLDOUT)
    hs = hs[hs["status"] == "ok"].copy()
    lean_feats = list(lean_model["features"])
    for f in lean_feats:
        if f in hs.columns:
            hs[f] = hs[f].astype(float).fillna(0.0)

    alarm = 0.5

    # Per-family lean refits on training rows, then predict holdout.
    train = pd.read_csv(TRAIN)
    for f in lean_feats:
        if f in train.columns:
            train[f] = train[f].astype(float).fillna(0.0)
    fam_preds: dict[str, np.ndarray] = {}
    for fam in FAMILY_ORDER:
        fam_model = _fit_ridge(train[train["family"] == fam], lean_feats)
        fam_preds[fam] = _predict(fam_model, hs)

    # Affine-scale all proxy scores into [0, 1] for display, centred so alarm=0.5
    # stays at 0.5 (Ridge can extrapolate outside [0, 1]).
    raw_proxy = hs["proxy"].to_numpy(dtype=float)
    all_raw = np.concatenate([raw_proxy, *[fam_preds[f] for f in FAMILY_ORDER]])
    half = float(max(alarm - float(np.min(all_raw)), float(np.max(all_raw)) - alarm))
    lo, hi = alarm - half, alarm + half

    def _scale01(y: np.ndarray) -> np.ndarray:
        return (np.asarray(y, dtype=float) - lo) / (hi - lo)

    hs["proxy"] = _scale01(raw_proxy)
    for fam in FAMILY_ORDER:
        fam_preds[fam] = _scale01(fam_preds[fam])

    anchors = hs[hs["config_kind"] == "anchor"]
    bads = hs[hs["config_kind"] == "bad"]

    fig, ax = plt.subplots(figsize=(6.2, 6.0))
    lims = [-0.05, 1.05]
    # Threshold segments: red alarm/reject L; yellow refine box [0.3,0.7]×[0.5,0.7].
    ax.hlines(alarm, lims[0], 0.3, color="#FF0000", ls="--", lw=0.9, zorder=7)
    ax.vlines(0.3, lims[0], 0.5, color="#FF0000", ls="--", lw=0.9, zorder=7)
    ax.hlines(0.5, 0.3, 0.7, color="#F1C40F", ls="--", lw=0.9, zorder=7)
    ax.hlines(0.7, 0.3, 0.7, color="#F1C40F", ls="--", lw=0.9, zorder=7)
    ax.vlines(0.3, 0.5, 0.7, color="#F1C40F", ls="--", lw=0.9, zorder=7)
    ax.vlines(0.7, 0.5, 0.7, color="#F1C40F", ls="--", lw=0.9, zorder=7)

    for fam in FAMILY_ORDER:
        a = anchors[anchors["family"] == fam]
        b = bads[bads["family"] == fam]
        ax.scatter(
            a["mIoU"],
            a["proxy"],
            c=FAMILY_COLORS[fam],
            marker="o",
            s=34,
            alpha=0.9,
            edgecolors="white",
            linewidths=0.35,
            zorder=3,
        )
        ax.scatter(
            b["mIoU"],
            b["proxy"],
            c=FAMILY_COLORS[fam],
            marker="X",
            s=34,
            alpha=0.9,
            linewidths=0.15,
            zorder=4,
        )

    x_gt = hs["mIoU"].to_numpy(dtype=float)
    # Unified lean p(e+c): solid, over all 54 points (existing pooled proxy column).
    _trend_line(
        ax,
        x_gt,
        hs["proxy"].to_numpy(dtype=float),
        color="#1A1A1A",
        ls="-",
        lw=1.0,
        zorder=5,
    )
    # Per-family lean refits: dotted, family-coloured.
    for fam in FAMILY_ORDER:
        mask = (hs["family"] == fam).to_numpy()
        _trend_line(
            ax,
            x_gt[mask],
            fam_preds[fam][mask],
            color=FAMILY_COLORS[fam],
            ls=":",
            lw=1.8,
            zorder=6,
        )

    ax.set_xlim(lims)
    ax.set_ylim(lims)
    ax.set_xlabel("GT mIoU", labelpad=12)
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
            markersize=6.4,
            label=f.capitalize(),
        )
        for f in FAMILY_ORDER
    ]
    line_handles = [
        Line2D([0], [0], color="#1A1A1A", ls="-", lw=1.0, label="Unified"),
    ] + [
        Line2D(
            [0],
            [0],
            color=FAMILY_COLORS[f],
            ls=":",
            lw=1.8,
            label=f.capitalize(),
        )
        for f in FAMILY_ORDER
    ]
    leg1 = ax.legend(handles=top_handles, frameon=False, loc="upper left", fontsize=12)
    ax.add_artist(leg1)
    ax.legend(
        handles=line_handles,
        frameon=False,
        loc="lower right",
        bbox_to_anchor=(1.03, 0.0),
        borderaxespad=0.0,
        fontsize=12,
        title="Lean p(e+c)",
        title_fontsize=12,
    )
    fig.tight_layout()
    out = OUT / "proxy_holdout_fullstage.pdf"
    fig.savefig(out, bbox_inches="tight")
    fig.savefig(out.with_suffix(".png"), dpi=200, bbox_inches="tight")
    fig.savefig(out.with_suffix(".svg"), bbox_inches="tight")
    plt.close(fig)
    _style()
    print(f"Wrote {out}")


def main() -> None:
    _style()
    OUT.mkdir(parents=True, exist_ok=True)
    model = json.loads(MODELS.read_text())["model"]
    plot_training(model)
    plot_holdout(model)


if __name__ == "__main__":
    main()
