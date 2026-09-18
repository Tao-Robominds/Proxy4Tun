#!/usr/bin/env python3
"""Candidate proxies tried during training vs the final frozen one.

X-axis: the 27x2 holdout runs ranked by GT mIoU. Each candidate proxy's
predictions are drawn as a thin dotted line; the final frozen v2 lean proxy
is the solid line. GT mIoU is the grey reference.

Reuses the ablation harness (bo-elegant/ablation_study.py) so every variant
is fitted exactly as in the reported ablation table.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "bo-elegant"))
sys.path.insert(0, str(REPO / "bo-unified"))

from ablation_study import (  # noqa: E402
    build_holdout_matrix,
    build_train_matrix,
)
from train_proxy_v2 import fit_ridge, predict  # noqa: E402
from features import CANDIDATE, COHERENCE, EVIDENCE  # noqa: E402

OUT = REPO / "paper" / "Proxy4Tun" / "figures"
MODELS_V2 = REPO / "bo-elegant" / "family" / "models_v2.json"

V1_FEATURES = [
    "depth_nan_ratio",
    "denoise_retained_ratio",
    "det_real_detection_ratio",
    "sam_fill_rate",
    "sam_ontology_divergence",
]

VARIANTS: list[tuple[str, list[str]]] = [
    ("Evidence only (2)", list(EVIDENCE)),
    ("Coherence only (6)", list(COHERENCE)),
    ("Full candidate (8)", list(CANDIDATE)),
    ("v1 features (regime-confounded)", V1_FEATURES),
]


def main() -> None:
    train = build_train_matrix()
    hold = build_holdout_matrix()

    frozen = json.loads(MODELS_V2.read_text())["model"]
    feats5 = frozen["features"]

    # Order holdout runs by GT mIoU
    ok = hold.dropna(subset=feats5).copy()
    ok = ok.sort_values("mIoU").reset_index(drop=True)
    x = np.arange(len(ok))

    fig, ax = plt.subplots(figsize=(9.2, 5.4))

    # GT reference
    ax.plot(
        x, ok["mIoU"], color="0.25", lw=2.2, label="GT mIoU (reference)", zorder=3
    )

    palette = ["#5DADE2", "#F5B041", "#58D68D", "#CD6155"]
    for (label, feats), color in zip(VARIANTS, palette):
        tr = train.dropna(subset=list(feats) + ["mIoU"])
        model = fit_ridge(tr, list(feats))
        sub = ok.dropna(subset=list(feats))
        preds = predict(model, sub)
        ax.plot(
            sub.index.to_numpy(),
            preds,
            ls=":",
            lw=1.4,
            color=color,
            label=f"candidate: {label}",
            zorder=2,
            alpha=0.95,
        )

    # Final frozen proxy — solid
    final_pred = predict(frozen, ok)
    ax.plot(
        x,
        final_pred,
        color="#1A5276",
        lw=2.6,
        label="final: lean 5-term proxy (frozen v2)",
        zorder=4,
    )

    ax.set_xlabel("27 held-out subsets x {anchor, known-bad}, ranked by GT mIoU")
    ax.set_ylabel(r"predicted quality $\hat{y}$")
    ax.set_title(
        "Candidate proxies explored during training vs the final frozen proxy\n"
        "(all fitted on the same anchor-trial table; evaluated on unseen holdouts)"
    )
    ax.legend(fontsize=8.5, loc="upper left", frameon=False)
    ax.spines[["top", "right"]].set_visible(False)
    ax.set_xticks([])
    fig.tight_layout()

    for ext in ("png", "pdf", "svg"):
        out = OUT / f"proxy_variants.{ext}"
        fig.savefig(out, dpi=200 if ext == "png" else None, bbox_inches="tight")
        print(f"Wrote {out}")
    plt.close(fig)


if __name__ == "__main__":
    main()
