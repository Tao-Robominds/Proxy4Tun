#!/usr/bin/env python3
"""Feature-set ablation for the bo-unified mIoU proxy.

Re-fits RidgeCV on stored features (no pipeline runs) and scores the 48
holdout runs. Produces:
  bo-unified/family/ablation_scores.csv
  bo-unified/ablation.md
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.metrics import mean_absolute_error

REPO_ROOT = Path(__file__).resolve().parent.parent
BO_DIR = Path(__file__).resolve().parent
FAMILY_DIR = BO_DIR / "family"
sys.path.insert(0, str(BO_DIR))

from blocks import FEATURE_SETS, features_for  # noqa: E402
from family_proxy import (  # noqa: E402
    FAMILY_ONEHOT,
    FAM_TO_OH,
    TRAINING_CSV,
    _add_family_onehot,
    _calibrate_alarm,
    _fit_ridge,
    _predict,
    load_training_table,
)
from pipeline import DATA_ROOT  # noqa: E402
from spaces import FAMILY_HOLDOUT_SUBSETS  # noqa: E402

ABLATION_SETS = ("B1", "B2lean", "B2", "B1+B2lean", "B1+B2")
ABLATION_CSV = FAMILY_DIR / "ablation_scores.csv"
ABLATION_MD = BO_DIR / "ablation.md"
PHASE_JSON = FAMILY_DIR / "phase_check.json"
N_PERM = 20
PERM_SEED = 0


def _load_holdout_frame(feature_cols: list[str]) -> pd.DataFrame:
    """Build a dataframe of all 48 holdout runs with Tier-1 features + mIoU."""
    rows: list[dict[str, Any]] = []
    for family, subsets in FAMILY_HOLDOUT_SUBSETS.items():
        for subset in subsets:
            man = DATA_ROOT / f"{subset}-family-proxy" / "manifest.json"
            if not man.exists():
                continue
            data = json.loads(man.read_text(encoding="utf-8"))
            for kind in ("anchor", "bad"):
                rec = next(
                    (r for r in data.get("runs", []) if r.get("run_id") == f"{subset}-{kind}"),
                    None,
                )
                if rec is None:
                    continue
                metrics = rec.get("metrics") or {}
                row: dict[str, Any] = {
                    "subset": subset,
                    "family": family,
                    "config_kind": kind,
                    "status": rec.get("status"),
                    "mIoU": rec.get("mIoU"),
                    "run_id": rec.get("run_id"),
                    "output_dir": rec.get("output_dir"),
                }
                for f in feature_cols:
                    row[f] = metrics.get(f)
                rows.append(row)
    df = pd.DataFrame(rows)
    return _add_family_onehot(df)


def _load_phase_alarms() -> dict[str, bool]:
    """Map run_id (basename of run dir) -> phase_alarm."""
    if not PHASE_JSON.exists():
        return {}
    data = json.loads(PHASE_JSON.read_text(encoding="utf-8"))
    out: dict[str, bool] = {}
    for rec in data:
        run_path = Path(rec["run"])
        out[run_path.name] = bool(rec.get("phase_alarm")) and bool(rec.get("applicable"))
    return out


def _ranking_accuracy(df: pd.DataFrame, proxy_col: str = "proxy") -> tuple[int, int]:
    n = n_ok = 0
    for subset, g in df.groupby("subset"):
        a = g[g["config_kind"] == "anchor"]
        b = g[g["config_kind"] == "bad"]
        if a.empty or b.empty:
            continue
        arow, brow = a.iloc[0], b.iloc[0]
        if not (
            math.isfinite(float(arow.get(proxy_col, np.nan)))
            and math.isfinite(float(brow.get(proxy_col, np.nan)))
        ):
            continue
        n += 1
        miou_order = float(arow["mIoU"]) >= float(brow["mIoU"])
        proxy_order = float(arow[proxy_col]) >= float(brow[proxy_col])
        if proxy_order == miou_order:
            n_ok += 1
    return n_ok, n


def _alarm_confusion(
    df: pd.DataFrame, alarm_col: str = "alarm", low_col: str = "is_low"
) -> dict[str, float]:
    tp = fp = tn = fn = 0
    for _, r in df.iterrows():
        alarm = bool(r[alarm_col])
        low = bool(r[low_col])
        if alarm and low:
            tp += 1
        elif alarm and not low:
            fp += 1
        elif (not alarm) and (not low):
            tn += 1
        else:
            fn += 1
    prec = tp / (tp + fp) if (tp + fp) else float("nan")
    rec = tp / (tp + fn) if (tp + fn) else float("nan")
    return {
        "tp": tp,
        "fp": fp,
        "tn": tn,
        "fn": fn,
        "precision": prec,
        "recall": rec,
    }


def _score_holdout(
    holdout: pd.DataFrame,
    *,
    features: list[str],
    mode: str,
    models: dict[str, dict[str, Any]],
    alarm_thr: dict[str, float],
    low_floor: dict[str, float],
    default_alarm_thr: float | None = None,
    default_low_floor: float | None = None,
) -> pd.DataFrame:
    """Attach proxy / alarm columns to a copy of holdout."""
    rows = []
    for _, r in holdout.iterrows():
        if r.get("status") != "ok" or r.get("mIoU") is None:
            continue
        if any(pd.isna(r.get(f)) for f in features if not f.startswith("fam_")):
            # Allow family one-hot NaN only if not used
            if any(pd.isna(r.get(f)) for f in features):
                continue
        fam = r["family"]
        if mode == "per_family":
            model = models[fam]
            thr = alarm_thr[fam]
            floor = low_floor[fam]
        else:
            model = models["pooled"]
            thr = float(default_alarm_thr) if default_alarm_thr is not None else alarm_thr[fam]
            floor = float(default_low_floor) if default_low_floor is not None else low_floor[fam]
        df1 = pd.DataFrame([{f: r[f] for f in model["features"]}])
        proxy = float(_predict(model, df1)[0])
        miou = float(r["mIoU"])
        rows.append(
            {
                "subset": r["subset"],
                "family": fam,
                "config_kind": r["config_kind"],
                "run_id": r["run_id"],
                "mIoU": miou,
                "proxy": proxy,
                "abs_err": abs(proxy - miou),
                "alarm": proxy <= thr,
                "is_low": miou <= floor,
                "alarm_threshold": thr,
                "low_miou_floor": floor,
            }
        )
    return pd.DataFrame(rows)


def _summarize(scored: pd.DataFrame, *, label: str, extra: dict[str, Any] | None = None) -> dict[str, Any]:
    if scored.empty:
        row = {
            "label": label,
            "n": 0,
            "mae": float("nan"),
            "mae_anchor": float("nan"),
            "mae_bad": float("nan"),
            "spearman": float("nan"),
            "rank_ok": 0,
            "rank_n": 0,
            "rank_acc": float("nan"),
            "alarm_precision": float("nan"),
            "alarm_recall": float("nan"),
            "tp": 0,
            "fp": 0,
            "tn": 0,
            "fn": 0,
        }
        if extra:
            row.update(extra)
        return row

    anc = scored[scored["config_kind"] == "anchor"]
    bad = scored[scored["config_kind"] == "bad"]
    sp = stats.spearmanr(scored["mIoU"], scored["proxy"]).correlation
    n_ok, n = _ranking_accuracy(scored)
    conf = _alarm_confusion(scored)
    row = {
        "label": label,
        "n": int(len(scored)),
        "mae": float(scored["abs_err"].mean()),
        "mae_anchor": float(anc["abs_err"].mean()) if len(anc) else float("nan"),
        "mae_bad": float(bad["abs_err"].mean()) if len(bad) else float("nan"),
        "spearman": float(sp) if sp is not None and math.isfinite(sp) else float("nan"),
        "rank_ok": int(n_ok),
        "rank_n": int(n),
        "rank_acc": (n_ok / n) if n else float("nan"),
        "alarm_precision": conf["precision"],
        "alarm_recall": conf["recall"],
        "tp": conf["tp"],
        "fp": conf["fp"],
        "tn": conf["tn"],
        "fn": conf["fn"],
    }
    if extra:
        row.update(extra)
    return row


def _fit_per_family(
    train: pd.DataFrame, features: list[str]
) -> tuple[dict[str, dict[str, Any]], dict[str, float], dict[str, float]]:
    models: dict[str, dict[str, Any]] = {}
    alarm: dict[str, float] = {}
    floor: dict[str, float] = {}
    for family in FAMILY_HOLDOUT_SUBSETS:
        sub = train[train["family"] == family].dropna(subset=features + ["mIoU"]).copy()
        # Drop family one-hot columns that are constant within family
        feats = [f for f in features if f not in FAMILY_ONEHOT]
        model = _fit_ridge(sub, feats)
        pred = _predict(model, sub)
        y = sub["mIoU"].to_numpy()
        models[family] = model
        alarm[family] = _calibrate_alarm(y, pred)
        floor[family] = float(np.quantile(y, 0.33))
    return models, alarm, floor


def _fit_pooled(
    train: pd.DataFrame, features: list[str]
) -> tuple[dict[str, Any], float, float]:
    sub = train.dropna(subset=features + ["mIoU"]).copy()
    model = _fit_ridge(sub, features)
    pred = _predict(model, sub)
    y = sub["mIoU"].to_numpy()
    return model, _calibrate_alarm(y, pred), float(np.quantile(y, 0.33))


def run_ablation_grid(train: pd.DataFrame, holdout: pd.DataFrame) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for set_name in ABLATION_SETS:
        feats = features_for(set_name)
        # --- per-family ---
        models, alarm, floor = _fit_per_family(train, feats)
        scored = _score_holdout(
            holdout, features=feats, mode="per_family", models=models, alarm_thr=alarm, low_floor=floor
        )
        rows.append(
            _summarize(
                scored,
                label=f"per_family/{set_name}",
                extra={"mode": "per_family", "feature_set": set_name, "onehot": False, "n_features": len(feats)},
            )
        )
        print(
            f"per_family/{set_name}: MAE={rows[-1]['mae']:.3f} "
            f"rank={rows[-1]['rank_ok']}/{rows[-1]['rank_n']} "
            f"P={rows[-1]['alarm_precision']:.2f} R={rows[-1]['alarm_recall']:.2f}"
        )

        # --- pooled without one-hot ---
        model, thr, fl = _fit_pooled(train, feats)
        scored = _score_holdout(
            holdout,
            features=feats,
            mode="pooled",
            models={"pooled": model},
            alarm_thr={},
            low_floor={},
            default_alarm_thr=thr,
            default_low_floor=fl,
        )
        rows.append(
            _summarize(
                scored,
                label=f"pooled/{set_name}",
                extra={"mode": "pooled", "feature_set": set_name, "onehot": False, "n_features": len(feats)},
            )
        )
        print(
            f"pooled/{set_name}: MAE={rows[-1]['mae']:.3f} "
            f"rank={rows[-1]['rank_ok']}/{rows[-1]['rank_n']}"
        )

        # --- pooled with family one-hot ---
        feats_oh = feats + list(FAMILY_ONEHOT)
        train_oh = _add_family_onehot(train)
        hold_oh = holdout  # already has one-hot
        model, thr, fl = _fit_pooled(train_oh, feats_oh)
        scored = _score_holdout(
            hold_oh,
            features=feats_oh,
            mode="pooled",
            models={"pooled": model},
            alarm_thr={},
            low_floor={},
            default_alarm_thr=thr,
            default_low_floor=fl,
        )
        rows.append(
            _summarize(
                scored,
                label=f"pooled+oh/{set_name}",
                extra={
                    "mode": "pooled",
                    "feature_set": set_name,
                    "onehot": True,
                    "n_features": len(feats_oh),
                },
            )
        )
        print(
            f"pooled+oh/{set_name}: MAE={rows[-1]['mae']:.3f} "
            f"rank={rows[-1]['rank_ok']}/{rows[-1]['rank_n']}"
        )
    return rows


def run_permutation_control(
    train: pd.DataFrame, holdout: pd.DataFrame, *, n_perm: int = N_PERM
) -> dict[str, Any]:
    """Shuffle mIoU within family, refit B1+B2lean per-family, average holdout metrics."""
    feats = features_for("B1+B2lean")
    rng = np.random.default_rng(PERM_SEED)
    maes: list[float] = []
    ranks: list[float] = []
    for i in range(n_perm):
        shuffled = train.copy()
        for family in FAMILY_HOLDOUT_SUBSETS:
            idx = shuffled.index[shuffled["family"] == family]
            vals = shuffled.loc[idx, "mIoU"].to_numpy()
            shuffled.loc[idx, "mIoU"] = rng.permutation(vals)
        models, alarm, floor = _fit_per_family(shuffled, feats)
        scored = _score_holdout(
            holdout, features=feats, mode="per_family", models=models, alarm_thr=alarm, low_floor=floor
        )
        if scored.empty:
            continue
        maes.append(float(scored["abs_err"].mean()))
        n_ok, n = _ranking_accuracy(scored)
        ranks.append((n_ok / n) if n else float("nan"))
        if (i + 1) % 5 == 0:
            print(f"  perm {i+1}/{n_perm}: mae={maes[-1]:.3f} rank={ranks[-1]:.2f}")
    return {
        "label": "perm_control/per_family/B1+B2lean",
        "mode": "permutation",
        "feature_set": "B1+B2lean",
        "onehot": False,
        "n_repeats": n_perm,
        "mae_mean": float(np.nanmean(maes)),
        "mae_std": float(np.nanstd(maes)),
        "rank_acc_mean": float(np.nanmean(ranks)),
        "rank_acc_std": float(np.nanstd(ranks)),
        "seed": PERM_SEED,
    }


def run_phase_augmentation(
    train: pd.DataFrame, holdout: pd.DataFrame
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Winning B1+B2lean per-family, with and without OR phase alarm."""
    feats = features_for("B1+B2lean")
    models, alarm, floor = _fit_per_family(train, feats)
    scored = _score_holdout(
        holdout, features=feats, mode="per_family", models=models, alarm_thr=alarm, low_floor=floor
    )
    base = _summarize(
        scored,
        label="phase_base/per_family/B1+B2lean",
        extra={"mode": "per_family", "feature_set": "B1+B2lean", "onehot": False, "phase_or": False},
    )

    phase = _load_phase_alarms()
    scored2 = scored.copy()
    scored2["alarm"] = [
        bool(a) or bool(phase.get(str(rid), False))
        for a, rid in zip(scored2["alarm"], scored2["run_id"])
    ]
    aug = _summarize(
        scored2,
        label="phase_or/per_family/B1+B2lean",
        extra={"mode": "per_family", "feature_set": "B1+B2lean", "onehot": False, "phase_or": True},
    )
    # Identify recovered FNs
    recovered = []
    for _, r in scored.iterrows():
        if (not bool(r["alarm"])) and bool(r["is_low"]):
            # was FN
            if phase.get(str(r["run_id"]), False):
                recovered.append(r["run_id"])
    aug["recovered_fns"] = ",".join(recovered)
    aug["n_recovered_fns"] = len(recovered)
    print(
        f"phase base: FP={base['fp']} FN={base['fn']}  "
        f"phase_or: FP={aug['fp']} FN={aug['fn']} recovered={recovered}"
    )
    return base, aug


def write_ablation_md(grid: list[dict[str, Any]], perm: dict[str, Any], phase_base: dict, phase_aug: dict) -> Path:
    lines: list[str] = []
    lines.append("# Proxy feature-set ablation (bo-unified)")
    lines.append("")
    lines.append(f"_Generated {datetime.now().isoformat(timespec='seconds')}_")
    lines.append("")
    lines.append("## Goal")
    lines.append("")
    lines.append(
        "Justify each component of the final GT-free mIoU proxy with holdout "
        "numbers: B1 (coherence), B2lean (evidence), family one-hot, and the "
        "phase-check alarm. Zero new pipeline runs — all fits use "
        "`training_table.csv` (225 trials) and the 48 holdout manifests."
    )
    lines.append("")
    lines.append("## Feature sets")
    lines.append("")
    lines.append("| Set | Features |")
    lines.append("|---|---|")
    for name in ABLATION_SETS:
        feats = features_for(name)
        lines.append(f"| `{name}` | {len(feats)}: `{', '.join(feats)}` |")
    lines.append("")

    lines.append("## Holdout grid")
    lines.append("")
    lines.append(
        "Per-family = 3 RidgeCV models (one per family). "
        "Pooled = one RidgeCV on all training rows. "
        "`+oh` adds family one-hot."
    )
    lines.append("")
    lines.append(
        "| Label | n | MAE | MAE_anchor | MAE_bad | Spearman | Rank | Alarm P | Alarm R |"
    )
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|")
    for r in grid:
        sp = r["spearman"]
        sp_s = f"{sp:.3f}" if math.isfinite(sp) else "n/a"
        ra = r["rank_acc"]
        ra_s = f"{r['rank_ok']}/{r['rank_n']} ({ra:.2f})" if math.isfinite(ra) else "n/a"
        ap = r["alarm_precision"]
        ar = r["alarm_recall"]
        ap_s = f"{ap:.2f}" if math.isfinite(ap) else "—"
        ar_s = f"{ar:.2f}" if math.isfinite(ar) else "—"
        lines.append(
            f"| `{r['label']}` | {r['n']} | {r['mae']:.3f} | {r['mae_anchor']:.3f} | "
            f"{r['mae_bad']:.3f} | {sp_s} | {ra_s} | {ap_s} | {ar_s} |"
        )
    lines.append("")

    # Highlight winner among per-family
    per_fam = [r for r in grid if r.get("mode") == "per_family"]
    winner = min(per_fam, key=lambda r: (r["mae"], -r.get("rank_acc", 0)))
    lines.append(
        f"**Best per-family feature set by holdout MAE:** `{winner['feature_set']}` "
        f"(MAE={winner['mae']:.3f}, rank={winner['rank_ok']}/{winner['rank_n']})."
    )
    lines.append("")

    # One-hot contribution on B1+B2lean
    lean_pool = next((r for r in grid if r["label"] == "pooled/B1+B2lean"), None)
    lean_oh = next((r for r in grid if r["label"] == "pooled+oh/B1+B2lean"), None)
    lean_pf = next((r for r in grid if r["label"] == "per_family/B1+B2lean"), None)
    if lean_pool and lean_oh and lean_pf:
        lines.append("### Family one-hot vs per-family (B1+B2lean)")
        lines.append("")
        lines.append("| Variant | MAE | Rank |")
        lines.append("|---|---:|---:|")
        lines.append(
            f"| pooled (no one-hot) | {lean_pool['mae']:.3f} | "
            f"{lean_pool['rank_ok']}/{lean_pool['rank_n']} |"
        )
        lines.append(
            f"| pooled + family one-hot | {lean_oh['mae']:.3f} | "
            f"{lean_oh['rank_ok']}/{lean_oh['rank_n']} |"
        )
        lines.append(
            f"| **per-family** (separate models) | {lean_pf['mae']:.3f} | "
            f"{lean_pf['rank_ok']}/{lean_pf['rank_n']} |"
        )
        lines.append("")

    # B2 vs B2lean
    b2 = next((r for r in grid if r["label"] == "per_family/B2"), None)
    b2l = next((r for r in grid if r["label"] == "per_family/B2lean"), None)
    b1b2 = next((r for r in grid if r["label"] == "per_family/B1+B2"), None)
    b1b2l = next((r for r in grid if r["label"] == "per_family/B1+B2lean"), None)
    if b2 and b2l and b1b2 and b1b2l:
        lines.append("### B2 full vs B2lean (per-family)")
        lines.append("")
        lines.append("| Set | MAE | Rank |")
        lines.append("|---|---:|---:|")
        for r in (b2l, b2, b1b2l, b1b2):
            lines.append(
                f"| `{r['feature_set']}` | {r['mae']:.3f} | {r['rank_ok']}/{r['rank_n']} |"
            )
        lines.append("")
        lines.append(
            "B2lean drops `depth_outlier_ratio`, `det_midpoint_ratio`, and "
            "`det_n_points` (family-conditional / regime-constant). Prefer the "
            "lean set when MAE and ranking are comparable or better."
        )
        lines.append("")

    lines.append("## Permutation control")
    lines.append("")
    lines.append(
        f"Within-family mIoU shuffle, refit per-family `B1+B2lean`, "
        f"{perm['n_repeats']} repeats (seed={perm['seed']})."
    )
    lines.append("")
    lines.append("| | Real fit | Permutation mean ± std |")
    lines.append("|---|---:|---:|")
    real = next((r for r in grid if r["label"] == "per_family/B1+B2lean"), None)
    if real:
        lines.append(
            f"| Holdout MAE | **{real['mae']:.3f}** | "
            f"{perm['mae_mean']:.3f} ± {perm['mae_std']:.3f} |"
        )
        lines.append(
            f"| Ranking accuracy | **{real['rank_acc']:.2f}** "
            f"({real['rank_ok']}/{real['rank_n']}) | "
            f"{perm['rank_acc_mean']:.2f} ± {perm['rank_acc_std']:.2f} |"
        )
    lines.append("")
    lines.append(
        "A large gap (real ≪ perm MAE, real ≫ perm ranking) confirms the fit "
        "is not a capacity artifact."
    )
    lines.append("")

    lines.append("## Phase-alarm augmentation")
    lines.append("")
    lines.append(
        "For the winning per-family `B1+B2lean` proxy, final alarm = "
        "`proxy_alarm OR phase_alarm` (phase applicable on t1&2 / t3 only)."
    )
    lines.append("")
    lines.append("| Variant | FP | FN | Precision | Recall | Recovered FNs |")
    lines.append("|---|---:|---:|---:|---:|---|")
    lines.append(
        f"| proxy only | {phase_base['fp']} | {phase_base['fn']} | "
        f"{phase_base['alarm_precision']:.2f} | {phase_base['alarm_recall']:.2f} | — |"
    )
    recovered = phase_aug.get("recovered_fns") or "—"
    lines.append(
        f"| proxy OR phase | {phase_aug['fp']} | {phase_aug['fn']} | "
        f"{phase_aug['alarm_precision']:.2f} | {phase_aug['alarm_recall']:.2f} | "
        f"`{recovered}` |"
    )
    lines.append("")

    lines.append("## Conclusion")
    lines.append("")
    lines.append(
        f"- **Default proxy:** per-family RidgeCV on **`{winner['feature_set']}`** "
        f"(holdout MAE {winner['mae']:.3f}, ranking "
        f"{winner['rank_ok']}/{winner['rank_n']})."
    )
    if lean_pf and lean_oh and lean_pf["mae"] <= lean_oh["mae"] + 0.01:
        lines.append(
            "- Per-family models beat (or match) a single pooled model with "
            "family one-hot — keep separate family proxies for deployment."
        )
    if b1b2l and b1b2 and b1b2l["mae"] <= b1b2["mae"] + 0.01:
        lines.append(
            "- **B2lean** is preferred over full B2: equal or better holdout "
            "metrics with fewer, less family-conditional features."
        )
    if real and perm["mae_mean"] - real["mae"] > 0.05:
        lines.append(
            f"- Permutation control: real MAE {real['mae']:.3f} vs "
            f"shuffled {perm['mae_mean']:.3f} — signal is genuine."
        )
    lines.append(
        "- **Phase-check** is retained as an OR-ed second alarm on t1&2/t3 to "
        "catch circumferential label-rotation that B1+B2lean cannot see."
    )
    lines.append("")
    lines.append("## Artifacts")
    lines.append("")
    lines.append("- Scores: `bo-unified/family/ablation_scores.csv`")
    lines.append("- Script: `bo-unified/ablation.py`")
    lines.append("- Parent report: [`report.md`](report.md)")
    lines.append("")

    ABLATION_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {ABLATION_MD}")
    return ABLATION_MD


def link_from_report() -> None:
    report = BO_DIR / "report.md"
    if not report.exists():
        return
    text = report.read_text(encoding="utf-8")
    link = (
        "- Feature-set ablation (B1 / B2lean / one-hot / phase): "
        "[`ablation.md`](ablation.md)."
    )
    if "ablation.md" in text:
        print("report.md already links ablation.md")
        return
    # Insert under Design bullets
    needle = "- Orientation / seed knobs frozen in unified params; BO overlays touch stages 2–6 only."
    if needle in text:
        text = text.replace(needle, needle + "\n" + link)
    else:
        text = text.replace("## Design\n", "## Design\n\n" + link + "\n", 1)
    report.write_text(text, encoding="utf-8")
    print(f"Linked ablation from {report}")


def main() -> None:
    p = argparse.ArgumentParser(description="bo-unified proxy feature-set ablation")
    p.add_argument("--skip-perm", action="store_true", help="Skip permutation control")
    p.add_argument("--n-perm", type=int, default=N_PERM)
    args = p.parse_args()

    FAMILY_DIR.mkdir(parents=True, exist_ok=True)
    train = load_training_table()
    # Collect all Tier-1 columns needed across sets
    all_feats = sorted({f for name in ABLATION_SETS for f in features_for(name)})
    holdout = _load_holdout_frame(all_feats)
    ok = holdout[holdout["status"] == "ok"]
    print(f"Training rows={len(train)}  Holdout ok={len(ok)}")

    grid = run_ablation_grid(train, holdout)

    n_perm = int(args.n_perm)
    if args.skip_perm:
        perm = {
            "label": "perm_control/skipped",
            "mode": "permutation",
            "feature_set": "B1+B2lean",
            "onehot": False,
            "n_repeats": 0,
            "mae_mean": float("nan"),
            "mae_std": float("nan"),
            "rank_acc_mean": float("nan"),
            "rank_acc_std": float("nan"),
            "seed": PERM_SEED,
        }
    else:
        print(f"Permutation control ({n_perm} repeats)...")
        perm = run_permutation_control(train, holdout, n_perm=n_perm)
        print(
            f"perm MAE={perm['mae_mean']:.3f}±{perm['mae_std']:.3f} "
            f"rank={perm['rank_acc_mean']:.2f}±{perm['rank_acc_std']:.2f}"
        )

    phase_base, phase_aug = run_phase_augmentation(train, holdout)

    # Flatten all rows into CSV
    csv_rows = list(grid)
    csv_rows.append(
        {
            "label": perm["label"],
            "mode": "permutation",
            "feature_set": perm["feature_set"],
            "onehot": False,
            "n": n_perm,
            "mae": perm["mae_mean"],
            "mae_std": perm["mae_std"],
            "rank_acc": perm["rank_acc_mean"],
            "rank_acc_std": perm["rank_acc_std"],
            "n_repeats": perm["n_repeats"],
            "seed": perm["seed"],
        }
    )
    for r in (phase_base, phase_aug):
        csv_rows.append(r)

    pd.DataFrame(csv_rows).to_csv(ABLATION_CSV, index=False)
    print(f"Wrote {ABLATION_CSV} ({len(csv_rows)} rows)")

    write_ablation_md(grid, perm, phase_base, phase_aug)
    link_from_report()


if __name__ == "__main__":
    main()
