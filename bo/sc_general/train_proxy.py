#!/usr/bin/env python3
"""Stage 2: train / ablate / freeze the SC-general proxy.

Arms: P(e), P(c), P(e+c), legacy_lean, leave-one-feature-out, pruned_lean
(size chosen by LOFO Spearman). Delta sensitivity on the correspondence pair.

Writes bo/sc_general/models.json, bo/sc_general/ablation.json,
data/sc-general/stage2/train_summary.json.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from bo.full_stage.train_proxy import (  # noqa: E402
    COEF_PRUNE_FRAC,
    fit_ridge,
    leave_one_family_out_cv,
    permutation_control,
    predict,
)
from bo.sc_general.build_tables import LEAN10, LEGACY_LEAN  # noqa: E402

OUT_DIR = _REPO / "bo" / "sc_general"
STAGE2 = _REPO / "data" / "sc-general" / "stage2"
TRAIN_TABLE = STAGE2 / "training_table.csv"
MODELS = OUT_DIR / "models.json"
ABLATION = OUT_DIR / "ablation.json"
TRAIN_SUMMARY = STAGE2 / "train_summary.json"

PQ5 = [
    "depth_nan_ratio",
    "denoise_retained_ratio",
    "unfold_residual",
    "orient_agreement",
    "ring_count_error",
]
SC5 = [
    "correspondence_f1@15",
    "boundary_explained_edge@25",
    "chamfer_sym_px",
    "sam_fill_rate",
    "phase_incoherence_deg",
]
assert PQ5 + SC5 == LEAN10

DELTA_VARIANTS = {
    "delta@8": ("correspondence_f1@8", "boundary_explained_edge@8"),
    "delta@15": ("correspondence_f1@15", "boundary_explained_edge@25"),
    "delta@25": ("correspondence_f1@25", "boundary_explained_edge@25"),
}
SC_STEMS = {"correspondence_f1", "boundary_explained_edge", "chamfer_sym_px"}


def _public(arm: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in arm.items() if k != "model"}


def arm_metrics(df: pd.DataFrame, features: list[str]) -> dict[str, Any]:
    model = fit_ridge(df, features)
    lofo = leave_one_family_out_cv(df, features)
    fam_mae = {
        str(fam): float(mean_absolute_error(g["mIoU"], predict(model, g)))
        for fam, g in df.groupby("family")
    }
    return {
        "features": list(features),
        "n_features": len(features),
        "train_mae": model["train_mae"],
        "train_spearman": model["train_spearman"],
        "lolo_mae": lofo["lolo_mae"],
        "lolo_spearman": lofo["lolo_spearman"],
        "family_mae": fam_mae,
        "alpha": model["alpha"],
        "coef": {f: float(c) for f, c in zip(model["features"], model["coef"])},
        "intercept": model["intercept"],
        "model": model,
    }


def _ensure_groups(
    feats: list[str],
    ranked: list[tuple[str, float]],
    coef_map: dict[str, float],
) -> list[str]:
    out = list(feats)
    if not any(f in PQ5 for f in out):
        out.append(max(PQ5, key=lambda f: abs(coef_map.get(f, 0.0))))
    if not any(f in SC5 for f in out):
        out.append(max(SC5, key=lambda f: abs(coef_map.get(f, 0.0))))
    seen: set[str] = set()
    ordered: list[str] = []
    for f, _ in ranked:
        if f in out and f not in seen:
            ordered.append(f)
            seen.add(f)
    for f in out:
        if f not in seen:
            ordered.append(f)
    return ordered


def prune_by_lofo(
    df: pd.DataFrame, features: list[str], frac: float = COEF_PRUNE_FRAC
) -> dict[str, Any]:
    full = fit_ridge(df, features)
    coefs = np.asarray(full["coef"], dtype=float)
    coef_map = {f: float(c) for f, c in zip(features, coefs)}
    max_abs = float(np.max(np.abs(coefs))) if len(coefs) else 0.0
    ranked = sorted(zip(features, np.abs(coefs)), key=lambda t: t[1], reverse=True)
    keep_tiny = [
        f for f, c in zip(features, coefs) if max_abs > 0 and abs(c) >= frac * max_abs
    ]

    candidates: list[list[str]] = []
    if keep_tiny:
        candidates.append(keep_tiny)
    for k in range(3, len(features) + 1):
        candidates.append([f for f, _ in ranked[:k]])

    best: dict[str, Any] | None = None
    trials: list[dict[str, Any]] = []
    seen: set[tuple[str, ...]] = set()
    for raw in candidates:
        feats = _ensure_groups(raw, ranked, coef_map)
        key = tuple(feats)
        if key in seen:
            continue
        seen.add(key)
        m = arm_metrics(df, feats)
        trials.append(_public(m))
        if best is None or m["lolo_spearman"] > best["lolo_spearman"] + 1e-12:
            best = m
        elif (
            abs(m["lolo_spearman"] - best["lolo_spearman"]) <= 1e-12
            and m["n_features"] < best["n_features"]
        ):
            best = m
    assert best is not None
    return {"selected": best, "trials": trials}


def delta_feature_set(tag: str) -> list[str]:
    f1, edge = DELTA_VARIANTS[tag]
    out = []
    for f in LEAN10:
        if f.startswith("correspondence_f1@"):
            out.append(f1)
        elif f.startswith("boundary_explained_edge@"):
            out.append(edge)
        else:
            out.append(f)
    return out


def has_sc_general(feats: list[str]) -> bool:
    return any(f.split("@")[0] in SC_STEMS for f in feats)


def main() -> None:
    if not TRAIN_TABLE.exists():
        raise SystemExit(f"missing {TRAIN_TABLE}; run build_tables.py first")
    df = pd.read_csv(TRAIN_TABLE)
    needed = set(LEAN10 + LEGACY_LEAN)
    for pair in DELTA_VARIANTS.values():
        needed.update(pair)
    for k in needed:
        if k not in df.columns:
            raise SystemExit(f"missing feature column {k}")
        df[k] = df[k].astype(float)

    arms: dict[str, dict[str, Any]] = {}
    for name, feats in {
        "P(e)": PQ5,
        "P(c)": SC5,
        "P(e+c)": LEAN10,
        "legacy_lean": LEGACY_LEAN,
    }.items():
        print(f"arm {name} ...", flush=True)
        arms[name] = arm_metrics(df, feats)
        a = arms[name]
        print(
            f"  train mae={a['train_mae']:.4f} sp={a['train_spearman']:.3f} "
            f"lolo mae={a['lolo_mae']:.4f} sp={a['lolo_spearman']:.3f}"
        )

    for drop in LEAN10:
        name = f"lofo_drop:{drop}"
        print(f"arm {name} ...", flush=True)
        arms[name] = arm_metrics(df, [f for f in LEAN10 if f != drop])

    print("pruned_lean ...", flush=True)
    pruned = prune_by_lofo(df, LEAN10)
    arms["pruned_lean"] = pruned["selected"]
    pr = arms["pruned_lean"]
    print(
        f"  features={pr['features']}\n"
        f"  train mae={pr['train_mae']:.4f} sp={pr['train_spearman']:.3f} "
        f"lolo mae={pr['lolo_mae']:.4f} sp={pr['lolo_spearman']:.3f}"
    )

    delta_rows = []
    for tag in DELTA_VARIANTS:
        m = arm_metrics(df, delta_feature_set(tag))
        delta_rows.append(
            {
                "delta": tag,
                "features": m["features"],
                "train_mae": m["train_mae"],
                "train_spearman": m["train_spearman"],
                "lolo_mae": m["lolo_mae"],
                "lolo_spearman": m["lolo_spearman"],
            }
        )
        print(f"delta {tag}: lolo sp={m['lolo_spearman']:.3f}")

    pec = arms["P(e+c)"]
    if pr["lolo_spearman"] + 1e-12 >= pec["lolo_spearman"] and has_sc_general(pr["features"]):
        deploy_name = "pruned_lean"
    else:
        deploy_name = "P(e+c)"
    deploy = arms[deploy_name]

    perm = permutation_control(df, deploy["features"])
    print(
        f"permutation pass={perm['pass']} "
        f"real_mae={perm['real_mae']:.4f} perm_mae={perm['perm_mae_mean']:.4f}"
    )

    per_family = {
        str(fam): fit_ridge(g, deploy["features"]) for fam, g in df.groupby("family")
    }

    payload = {
        "created_at": datetime.now().isoformat(),
        "n_train": int(len(df)),
        "n_per_case": df.groupby("case").size().astype(int).to_dict()
        if "case" in df.columns
        else {},
        "lean10": LEAN10,
        "pq5": PQ5,
        "sc5": SC5,
        "legacy_lean": LEGACY_LEAN,
        "deployment_arm": deploy_name,
        "lean_features": deploy["features"],
        "delta": 15,
        "ring_count_convention": "|ring_count - 10|",
        "model": deploy["model"],
        "per_family_models": per_family,
        "permutation": perm,
        "lolo_cv": {
            "lolo_mae": deploy["lolo_mae"],
            "lolo_spearman": deploy["lolo_spearman"],
        },
        "family_mae": deploy["family_mae"],
        "alarm_threshold": 0.5,
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    MODELS.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    ABLATION.write_text(
        json.dumps(
            {
                "created_at": datetime.now().isoformat(),
                "arms": {k: _public(v) for k, v in arms.items()},
                "pruned_trials": pruned["trials"],
                "delta_sensitivity": delta_rows,
                "deployment_arm": deploy_name,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    TRAIN_SUMMARY.write_text(
        json.dumps(
            {
                "deployment_arm": deploy_name,
                "lean_features": deploy["features"],
                "train_mae": deploy["train_mae"],
                "train_spearman": deploy["train_spearman"],
                "lolo_mae": deploy["lolo_mae"],
                "lolo_spearman": deploy["lolo_spearman"],
                "family_mae": deploy["family_mae"],
                "permutation": perm,
                "delta_sensitivity": delta_rows,
                "legacy_lolo_spearman": arms["legacy_lean"]["lolo_spearman"],
                "legacy_train_spearman": arms["legacy_lean"]["train_spearman"],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"wrote {MODELS}")
    print(f"wrote {ABLATION}")
    print(f"deployment={deploy_name} features={deploy['features']}")


if __name__ == "__main__":
    main()
