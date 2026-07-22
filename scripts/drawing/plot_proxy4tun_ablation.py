#!/usr/bin/env python3
"""Bar charts for Proxy4Tun proxy feature-set ablation (bo-unified).

Reads bo-unified/family/ablation_scores.csv and holdout_scores.csv.
Writes PDF/PNG into paper/Proxy4Tun/figures/.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
ABLATION = REPO / "bo-unified" / "family" / "ablation_scores.csv"
HOLDOUT = REPO / "bo-unified" / "family" / "holdout_scores.csv"
OUT = REPO / "paper" / "Proxy4Tun" / "figures"

FEATURE_ORDER = ["B1", "B2lean", "B2", "B1+B2lean", "B1+B2"]
COLORS = {
    "per_family": "#2C73D2",
    "pooled": "#FF6B6B",
    "pooled+oh": "#44BBA4",
}


def _style():
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


def plot_mae_bars(df: pd.DataFrame) -> Path:
    """Grouped bars: holdout MAE by feature set × model structure."""
    rows = df[df["phase_or"].isna() | (df["phase_or"] == False)]  # noqa: E712
    rows = rows[rows["feature_set"].isin(FEATURE_ORDER)].copy()
    # Exclude permutation control rows
    rows = rows[rows["n_repeats"].isna() | (rows["n_repeats"] == 0) | (rows["n_repeats"].isna())]
    # Keep only single-fit ablation rows (no mae_std from perm)
    rows = rows[rows["label"].str.contains("per_family|pooled", regex=True)]
    rows = rows[~rows["label"].str.contains("perm", case=False, na=False)]

    fig, ax = plt.subplots(figsize=(8.2, 3.8))
    x = np.arange(len(FEATURE_ORDER))
    width = 0.26
    modes = ["per_family", "pooled", "pooled+oh"]
    labels = ["Per-family", "Pooled", "Pooled + one-hot"]

    for i, (mode, lab) in enumerate(zip(modes, labels)):
        vals = []
        for fs in FEATURE_ORDER:
            sub = rows[(rows["mode"] == mode) & (rows["feature_set"] == fs) & (rows["onehot"] == (mode == "pooled+oh"))]
            # pooled+oh has mode pooled and onehot True in some exports — also match label
            if sub.empty:
                sub = rows[rows["label"] == f"{mode}/{fs}"]
            if sub.empty and mode == "pooled+oh":
                sub = rows[rows["label"] == f"pooled+oh/{fs}"]
            vals.append(float(sub["mae"].iloc[0]) if len(sub) else np.nan)
        ax.bar(
            x + (i - 1) * width,
            vals,
            width,
            label=lab,
            color=COLORS["per_family" if mode == "per_family" else ("pooled" if mode == "pooled" else "pooled+oh")],
            edgecolor="white",
            linewidth=0.4,
        )

    ax.set_xticks(x)
    ax.set_xticklabels(FEATURE_ORDER)
    ax.set_ylabel("Holdout MAE")
    ax.set_ylim(0, 0.18)
    ax.axhline(0.110, color="#333333", ls="--", lw=0.9, alpha=0.7, label="Deploy default (B1+B2lean)")
    ax.legend(loc="upper right", frameon=False, ncol=2)
    ax.set_title("Proxy feature-set ablation (48 holdout runs)")
    fig.tight_layout()
    out = OUT / "proxy_ablation_mae.pdf"
    fig.savefig(out, bbox_inches="tight")
    fig.savefig(out.with_suffix(".png"), dpi=200, bbox_inches="tight")
    plt.close(fig)
    return out


def plot_alarm_bars(df: pd.DataFrame) -> Path:
    """Alarm precision/recall for key per-family sets + phase OR."""
    keys = [
        ("per_family/B2lean", "B2lean"),
        ("per_family/B1+B2lean", "B1+B2lean"),
        ("per_family/B1+B2", "B1+B2"),
    ]
    prec, rec = [], []
    labels = []
    for lab, short in keys:
        row = df[df["label"] == lab]
        if row.empty:
            continue
        labels.append(short)
        prec.append(float(row["alarm_precision"].iloc[0]))
        rec.append(float(row["alarm_recall"].iloc[0]))

    phase = df[df["label"] == "phase_or/per_family/B1+B2lean"]
    if len(phase):
        labels.append("B1+B2lean+phase")
        prec.append(float(phase["alarm_precision"].iloc[0]))
        rec.append(float(phase["alarm_recall"].iloc[0]))

    fig, ax = plt.subplots(figsize=(7.2, 3.6))
    x = np.arange(len(labels))
    w = 0.36
    ax.bar(x - w / 2, prec, w, label="Alarm precision", color="#2C73D2")
    ax.bar(x + w / 2, rec, w, label="Alarm recall", color="#44BBA4")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=15, ha="right")
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Score")
    ax.legend(frameon=False, loc="lower right")
    ax.set_title("Deployment alarm quality (per-family proxies)")
    for i, (p, r) in enumerate(zip(prec, rec)):
        ax.text(i - w / 2, p + 0.02, f"{p:.2f}", ha="center", fontsize=8)
        ax.text(i + w / 2, r + 0.02, f"{r:.2f}", ha="center", fontsize=8)
    fig.tight_layout()
    out = OUT / "proxy_ablation_alarm.pdf"
    fig.savefig(out, bbox_inches="tight")
    fig.savefig(out.with_suffix(".png"), dpi=200, bbox_inches="tight")
    plt.close(fig)
    return out


def plot_proxy_scatter(hs: pd.DataFrame) -> Path:
    """Proxy vs GT mIoU on holdout (per-family), coloured by config kind."""
    fig, ax = plt.subplots(figsize=(5.2, 4.6))
    for kind, color, marker in [("anchor", "#2C73D2", "o"), ("bad", "#E74C3C", "X")]:
        sub = hs[hs["config_kind"] == kind]
        ax.scatter(
            sub["mIoU"],
            sub["proxy_family"],
            c=color,
            marker=marker,
            s=42,
            alpha=0.85,
            label=kind,
            edgecolors="white",
            linewidths=0.4,
        )
    lims = [-0.15, 1.0]
    ax.plot(lims, lims, ls="--", color="gray", lw=0.9, alpha=0.7)
    ax.set_xlim(lims)
    ax.set_ylim(lims)
    ax.set_xlabel("GT mIoU")
    ax.set_ylabel("Per-family proxy $\\hat{y}$")
    ax.set_title("Holdout calibration (24 subsets × 2 configs)")
    ax.legend(frameon=False)
    ax.set_aspect("equal", adjustable="box")
    fig.tight_layout()
    out = OUT / "proxy_holdout_scatter.pdf"
    fig.savefig(out, bbox_inches="tight")
    fig.savefig(out.with_suffix(".png"), dpi=200, bbox_inches="tight")
    plt.close(fig)
    return out


def plot_family_miou_bars(hs: pd.DataFrame) -> Path:
    """Mean GT mIoU for anchor vs bad by family."""
    fam_order = ["t1&2", "t3", "t4&5"]
    fam_labels = ["Staggered\n(T1/T2)", "Continuous\n(T3)", "Complex\n(T4/T5)"]
    fig, ax = plt.subplots(figsize=(6.4, 3.8))
    x = np.arange(len(fam_order))
    w = 0.34
    for i, (kind, color) in enumerate([("anchor", "#2C73D2"), ("bad", "#E74C3C")]):
        means = [float(hs[(hs["family"] == f) & (hs["config_kind"] == kind)]["mIoU"].mean()) for f in fam_order]
        ax.bar(x + (i - 0.5) * w, means, w, label=kind, color=color)
        for j, m in enumerate(means):
            ax.text(j + (i - 0.5) * w, m + 0.02, f"{m:.2f}", ha="center", fontsize=8)
    ax.set_xticks(x)
    ax.set_xticklabels(fam_labels)
    ax.set_ylabel("Mean GT mIoU")
    ax.set_ylim(0, 1.0)
    ax.legend(frameon=False)
    ax.set_title("Holdout panel: sibling-anchor vs known-bad overlays")
    fig.tight_layout()
    out = OUT / "proxy_family_miou_bars.pdf"
    fig.savefig(out, bbox_inches="tight")
    fig.savefig(out.with_suffix(".png"), dpi=200, bbox_inches="tight")
    plt.close(fig)
    return out


def main() -> None:
    _style()
    OUT.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(ABLATION)
    hs = pd.read_csv(HOLDOUT)
    paths = [
        plot_mae_bars(df),
        plot_alarm_bars(df),
        plot_proxy_scatter(hs),
        plot_family_miou_bars(hs),
    ]
    for p in paths:
        print(f"Wrote {p}")


if __name__ == "__main__":
    main()
