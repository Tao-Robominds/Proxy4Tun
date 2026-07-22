#!/usr/bin/env python3
"""Anchor feature sanity-check + single-instance validation gate (subset 3-3)."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

from features import ANCHOR_PARAMS, CANDIDATE, TRAIN_ANCHORS, extract_lean, lean_vector, load_metrics_from_run
from train_proxy import predict

REPO_ROOT = Path(__file__).resolve().parent.parent
BO_DIR = Path(__file__).resolve().parent
MODELS_PATH = BO_DIR / "family" / "models.json"
GATE_PATH = BO_DIR / "validation_gate.md"
SANITY_PATH = BO_DIR / "family" / "anchor_sanity.json"


def check_anchors() -> dict:
    results = {}
    for case in TRAIN_ANCHORS:
        run_dir = REPO_ROOT / "data" / "anchors" / case
        params = ANCHOR_PARAMS[case]
        lean = extract_lean(run_dir, params_dir=params)
        results[case] = {
            "path": str(run_dir.relative_to(REPO_ROOT)),
            "complete": all(np.isfinite(lean.get(k, float("nan"))) for k in CANDIDATE),
            "orient_invariant_ok": lean.get("orient_invariant_ok"),
            "orient_h_ring_corr": lean.get("orient_h_ring_corr"),
            "features": {k: lean.get(k) for k in CANDIDATE},
        }
        print(
            f"{case}: complete={results[case]['complete']} "
            f"corr={results[case]['orient_h_ring_corr']:.3f} "
            f"ok={results[case]['orient_invariant_ok']}"
        )
        for k in CANDIDATE:
            print(f"  {k:28s} {lean.get(k)}")
    SANITY_PATH.parent.mkdir(parents=True, exist_ok=True)
    SANITY_PATH.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {SANITY_PATH}")
    return results


def validation_gate_3_3() -> dict:
    """Prove one representative holdout end-to-end before scoring all 27."""
    models = json.loads(MODELS_PATH.read_text(encoding="utf-8"))
    model = models["model"]
    features = list(models["features"])
    registry = json.loads((BO_DIR / "registry.json").read_text(encoding="utf-8"))

    rows = []
    for kind in ("anchor", "bad"):
        entry = next(
            e for e in registry["runs"] if e["subset"] == "3-3" and e["config_kind"] == kind
        )
        run_dir = REPO_ROOT / entry["path"]
        params = REPO_ROOT / entry["params_dir"]
        # Recompute lean features from artifacts
        recomputed = extract_lean(run_dir, params_dir=params)
        cached = load_metrics_from_run(run_dir) or {}
        # Compare overlapping keys
        deltas = {}
        for k in features:
            a = recomputed.get(k, float("nan"))
            b = cached.get(k, float("nan"))
            try:
                deltas[k] = abs(float(a) - float(b)) if np.isfinite(float(a)) and np.isfinite(float(b)) else None
            except (TypeError, ValueError):
                deltas[k] = None

        man = run_dir.parent.parent / "manifest.json"
        miou = None
        if man.exists():
            data = json.loads(man.read_text(encoding="utf-8"))
            for r in data.get("runs", []):
                if r.get("run_id") == f"3-3-{kind}":
                    miou = r.get("mIoU")
        df_one = pd.DataFrame([{f: recomputed[f] for f in features}])
        proxy = float(predict(model, df_one)[0])
        rows.append(
            {
                "kind": kind,
                "path": entry["path"],
                "mIoU": miou,
                "proxy": proxy,
                "features": {k: recomputed[k] for k in features},
                "max_delta_vs_intrinsics_json": max(
                    (d for d in deltas.values() if d is not None), default=None
                ),
                "deltas": deltas,
            }
        )

    a = next(r for r in rows if r["kind"] == "anchor")
    b = next(r for r in rows if r["kind"] == "bad")
    criteria = {
        "features_recomputable": all(
            np.isfinite(r["features"][f]) for r in rows for f in features
        ),
        "intrinsics_match": all(
            (r["max_delta_vs_intrinsics_json"] or 0) < 1e-6 for r in rows
        ),
        "anchor_gt_bad_proxy": a["proxy"] > b["proxy"],
        "proxy_gap_ge_0_1": (a["proxy"] - b["proxy"]) >= 0.1,
        "miou_anchor_ge_0_5": (a["mIoU"] or 0) >= 0.5,
        "miou_bad_le_0_2": (b["mIoU"] or 1) <= 0.2,
    }
    passed = all(criteria.values())

    lines = [
        "# Validation gate — subset 3-3",
        "",
        f"_Generated {datetime.now().isoformat(timespec='seconds')}_",
        "",
        "## Case",
        "",
        "- Subset: `3-3` (continuous family holdout)",
        f"- Lineage: reused `data/bo-unified/3-3-family-proxy/runs/3-3-{{anchor,bad}}`",
        f"- Proxy: frozen lean Ridge from `{MODELS_PATH.relative_to(REPO_ROOT)}`",
        f"- Features: `{features}`",
        "",
        "## Metrics",
        "",
        "| Kind | mIoU | proxy | path |",
        "|---|---:|---:|---|",
        f"| anchor | {a['mIoU']} | {a['proxy']:.4f} | `{a['path']}` |",
        f"| bad | {b['mIoU']} | {b['proxy']:.4f} | `{b['path']}` |",
        "",
        f"- Proxy gap (anchor − bad) = **{a['proxy'] - b['proxy']:.4f}**",
        "",
        "## Pass / fail criteria",
        "",
    ]
    for k, v in criteria.items():
        lines.append(f"- `{k}`: **{'PASS' if v else 'FAIL'}** ({v})")
    lines += [
        "",
        f"## Overall: **{'PASS' if passed else 'FAIL'}**",
        "",
        "### Feature values (recomputed)",
        "",
    ]
    for r in rows:
        lines.append(f"**{r['kind']}**")
        for k, v in r["features"].items():
            lines.append(f"- `{k}`: {v}")
        lines.append("")

    GATE_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {GATE_PATH}")
    print(f"GATE {'PASS' if passed else 'FAIL'}: criteria={criteria}")
    if not passed:
        raise SystemExit(1)
    return {"passed": passed, "criteria": criteria, "rows": rows}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--anchors", action="store_true")
    parser.add_argument("--gate", action="store_true")
    args = parser.parse_args()
    if args.anchors:
        check_anchors()
    if args.gate:
        validation_gate_3_3()
    if not args.anchors and not args.gate:
        check_anchors()
        validation_gate_3_3()


if __name__ == "__main__":
    main()
