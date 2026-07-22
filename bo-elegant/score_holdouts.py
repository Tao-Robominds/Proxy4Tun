#!/usr/bin/env python3
"""Score all registered holdout runs with the frozen lean unified proxy."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.metrics import mean_absolute_error

from features import (
    ANCHOR_PARAMS,
    CANDIDATE,
    extract_lean,
    features_complete,
    lean_vector,
    load_metrics_from_run,
)
from train_proxy import predict

REPO_ROOT = Path(__file__).resolve().parent.parent
BO_DIR = Path(__file__).resolve().parent
FAMILY_DIR = BO_DIR / "family"
MODELS_PATH = FAMILY_DIR / "models.json"
REGISTRY_PATH = BO_DIR / "registry.json"
SCORES_PATH = FAMILY_DIR / "holdout_scores.csv"
REPORT_PATH = BO_DIR / "report.md"
MIoU_RE = re.compile(r"Mean IoU \(mIoU\):\s*([\d.]+)")


def _read_miou(run_dir: Path, registry_hint: dict | None = None) -> float | None:
    # Prefer evaluation/performance.md; fall back to bo-unified manifest.
    perf = run_dir / "evaluation" / "performance.md"
    if perf.exists():
        m = MIoU_RE.search(perf.read_text(encoding="utf-8"))
        if m:
            return float(m.group(1))
    # Parent family-proxy manifest
    man = run_dir.parent.parent / "manifest.json"
    if man.exists():
        data = json.loads(man.read_text(encoding="utf-8"))
        for r in data.get("runs", []):
            if r.get("run_id") == run_dir.name and r.get("mIoU") is not None:
                return float(r["mIoU"])
    return None


def _load_features(entry: dict[str, Any], features: list[str]) -> dict[str, Any]:
    run_dir = REPO_ROOT / entry["path"]
    params = REPO_ROOT / entry["params_dir"]
    metrics = load_metrics_from_run(run_dir)
    if metrics is None or not features_complete(metrics, features):
        metrics = extract_lean(run_dir, params_dir=params if params.exists() else None)
    return lean_vector(metrics, features)


def score_all() -> pd.DataFrame:
    models = json.loads(MODELS_PATH.read_text(encoding="utf-8"))
    model = models["model"]
    features = list(models["features"])
    alarm = float(models["alarm_threshold"])
    floor = float(models["low_miou_floor"])
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))

    rows = []
    for entry in registry["runs"]:
        run_dir = REPO_ROOT / entry["path"]
        base = {
            "subset": entry["subset"],
            "family": entry["family"],
            "config_kind": entry["config_kind"],
            "run_id": entry["run_id"],
            "source": entry["source"],
            "path": entry["path"],
        }
        if not run_dir.exists():
            rows.append({**base, "status": "missing", "mIoU": np.nan, "proxy": np.nan})
            continue
        miou = _read_miou(run_dir)
        try:
            feats = _load_features(entry, features)
        except Exception as exc:  # noqa: BLE001
            rows.append(
                {
                    **base,
                    "status": "feature_fail",
                    "mIoU": miou if miou is not None else np.nan,
                    "proxy": np.nan,
                    "note": str(exc),
                }
            )
            continue
        if miou is None or not features_complete(feats, features):
            rows.append(
                {
                    **base,
                    "status": "incomplete",
                    "mIoU": miou if miou is not None else np.nan,
                    "proxy": np.nan,
                    **{f: feats.get(f) for f in features},
                }
            )
            continue
        df_one = pd.DataFrame([{f: feats[f] for f in features}])
        proxy = float(predict(model, df_one)[0])
        rows.append(
            {
                **base,
                "status": "ok",
                "mIoU": float(miou),
                "proxy": proxy,
                "abs_err": abs(proxy - float(miou)),
                "alarm": proxy <= alarm,
                "is_low_miou": float(miou) <= floor,
                "alarm_threshold": alarm,
                "low_miou_floor": floor,
                **{f: feats[f] for f in features},
            }
        )
    out = pd.DataFrame(rows)
    FAMILY_DIR.mkdir(parents=True, exist_ok=True)
    out.to_csv(SCORES_PATH, index=False)
    print(f"Wrote {SCORES_PATH} ({len(out)} rows, ok={int((out.status=='ok').sum())})")
    return out


def ranking_accuracy(df: pd.DataFrame) -> dict[str, Any]:
    ok = 0
    total = 0
    misses = []
    for subset, g in df.groupby("subset"):
        a = g[g["config_kind"] == "anchor"]
        b = g[g["config_kind"] == "bad"]
        if a.empty or b.empty:
            continue
        if a.iloc[0]["status"] != "ok" or b.iloc[0]["status"] != "ok":
            continue
        total += 1
        if float(a.iloc[0]["proxy"]) > float(b.iloc[0]["proxy"]):
            ok += 1
        else:
            misses.append(
                {
                    "subset": subset,
                    "proxy_anchor": float(a.iloc[0]["proxy"]),
                    "proxy_bad": float(b.iloc[0]["proxy"]),
                    "miou_anchor": float(a.iloc[0]["mIoU"]),
                    "miou_bad": float(b.iloc[0]["mIoU"]),
                }
            )
    return {"ok": ok, "total": total, "accuracy": ok / total if total else 0.0, "misses": misses}


def write_report(df: pd.DataFrame) -> None:
    models = json.loads(MODELS_PATH.read_text(encoding="utf-8"))
    ablation = json.loads((FAMILY_DIR / "ablation.json").read_text(encoding="utf-8"))
    ok = df[df["status"] == "ok"].copy()
    rank = ranking_accuracy(ok)

    lines = [
        "# bo-elegant report — 3-anchor unified lean proxy",
        "",
        f"_Generated {datetime.now().isoformat(timespec='seconds')}_",
        "",
        "## Design",
        "",
        f"- Train anchors: `{', '.join(models['train_anchors'])}` ({models['n_train_rows']} archived trials).",
        f"- Selected feature set: **{models['selected_set']}** → `{models['features']}`.",
        "- Taxonomy: Evidence = artifact/depth quality; Coherence = detection+segmentation form.",
        "- One pooled RidgeCV (no family one-hot).",
        "",
        "### Dropped up front (prior lessons)",
        "",
    ]
    for k, reason in models["dropped_upfront"].items():
        lines.append(f"- `{k}`: {reason}")

    lines += [
        "",
        "### Frozen coefficients (standardized)",
        "",
        "| Feature | Coef | Block |",
        "|---|---:|---|",
    ]
    ev = set(models["candidate_features"]["Evidence"])
    for f, c in sorted(
        zip(models["features"], models["model"]["coef"]), key=lambda t: -abs(t[1])
    ):
        block = "Evidence" if f in ev else "Coherence"
        lines.append(f"| `{f}` | {c:+.4f} | {block} |")

    lines += [
        "",
        f"- Train MAE={models['model']['train_mae']:.3f}, "
        f"Spearman={models['model']['train_spearman']:.3f}, "
        f"α={models['model']['alpha']:.4g}",
        f"- Alarm threshold={models['alarm_threshold']:.3f}, "
        f"low-mIoU floor={models['low_miou_floor']:.3f}",
        "",
        "### Mini-ablation (training / LOLO)",
        "",
        "| Set | n | train MAE | train Sp | LOLO MAE | LOLO Sp |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for r in ablation["variants"]:
        if r["set"].startswith("loo_") and r["set"] not in (
            f"loo_{f}" for f in ("sam_ring_completeness", "sam_ontology_divergence")
        ):
            # keep table readable: show named sets + the two backstop LOOs
            continue
        sel = models["selected_set"].replace("+pruned", "")
        mark = " ← selected" if r["set"] == sel or r["set"] == models["selected_set"] else ""
        lines.append(
            f"| `{r['set']}`{mark} | {r['n_features']} | {r['train_mae']:.3f} | "
            f"{r['train_spearman']:.3f} | {r['lolo_mae']:.3f} | {r['lolo_spearman']:.3f} |"
        )

    perm = models["permutation"]
    lines += [
        "",
        "### Permutation control",
        "",
        f"- Real train MAE **{perm['real_mae']:.3f}** vs shuffled "
        f"{perm['perm_mae_mean']:.3f} ± {perm['perm_mae_std']:.3f} "
        f"(n={perm['n_repeats']}, pass={perm['pass']}).",
        "",
        "## Holdout evaluation",
        "",
        f"- Scored runs: {len(df)} (ok={int((df.status=='ok').sum())}).",
    ]

    if len(ok) >= 2:
        sp = float(stats.spearmanr(ok["mIoU"], ok["proxy"]).correlation or 0.0)
        pe = float(stats.pearsonr(ok["mIoU"], ok["proxy"]).statistic)
        mae = float(mean_absolute_error(ok["mIoU"], ok["proxy"]))
        lines += [
            f"- Pooled MAE={mae:.3f}, Spearman={sp:.3f}, Pearson={pe:.3f}",
            f"- Anchor>bad ranking: **{rank['ok']}/{rank['total']}** "
            f"(acc={rank['accuracy']:.2f})",
            "",
            "### Per-family",
            "",
            "| Family | n | MAE | Spearman | MAE_anchor | MAE_bad |",
            "|---|---:|---:|---:|---:|---:|",
        ]
        for fam, g in ok.groupby("family"):
            spf = float(stats.spearmanr(g["mIoU"], g["proxy"]).correlation or 0.0)
            maef = float(mean_absolute_error(g["mIoU"], g["proxy"]))
            a = g[g["config_kind"] == "anchor"]
            b = g[g["config_kind"] == "bad"]
            lines.append(
                f"| {fam} | {len(g)} | {maef:.3f} | {spf:.3f} | "
                f"{mean_absolute_error(a['mIoU'], a['proxy']) if len(a) else float('nan'):.3f} | "
                f"{mean_absolute_error(b['mIoU'], b['proxy']) if len(b) else float('nan'):.3f} |"
            )

        # Alarm metrics
        tp = int(((ok["alarm"]) & (ok["is_low_miou"])).sum())
        fp = int(((ok["alarm"]) & (~ok["is_low_miou"])).sum())
        fn = int(((~ok["alarm"]) & (ok["is_low_miou"])).sum())
        prec = tp / (tp + fp) if (tp + fp) else 0.0
        rec = tp / (tp + fn) if (tp + fn) else 0.0
        lines += [
            "",
            "### Bad-flagging alarm",
            "",
            f"- Precision={prec:.2f}, Recall={rec:.2f} (TP={tp}, FP={fp}, FN={fn})",
            f"- Threshold={models['alarm_threshold']:.3f} "
            f"(low-mIoU floor on train={models['low_miou_floor']:.3f})",
        ]
        if rank["misses"]:
            lines += ["", "### Ranking misses", ""]
            for m in rank["misses"]:
                lines.append(
                    f"- `{m['subset']}`: proxy_anchor={m['proxy_anchor']:.3f} "
                    f"≤ proxy_bad={m['proxy_bad']:.3f} "
                    f"(mIoU {m['miou_anchor']:.3f} vs {m['miou_bad']:.3f})"
                )

    lines += [
        "",
        "## Artifacts",
        "",
        "- `bo-elegant/family/models.json`",
        "- `bo-elegant/family/ablation.json`",
        "- `bo-elegant/family/holdout_scores.csv`",
        "- `bo-elegant/registry.json`",
        "",
    ]
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {REPORT_PATH}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--score", action="store_true")
    parser.add_argument("--report", action="store_true")
    args = parser.parse_args()
    if args.score or args.report or True:
        df = score_all()
        write_report(df)


if __name__ == "__main__":
    main()
