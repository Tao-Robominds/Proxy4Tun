#!/usr/bin/env python3
"""Benefit, selection policies, and error analysis for release-2 Plan 4.

Usage:
  ./venv/bin/python bo/release2_1/analyse_benefit.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from bo.paths import RELEASE21_DATA, REPO_ROOT  # noqa: E402
from bo.release2_1.refine import ADMITTED, PANEL_ARMS, round_dir, start_dir  # noqa: E402
from bo.release2.run_pair import EVAL_SUBSETS  # noqa: E402
from bo.runtime.metadata import family_of  # noqa: E402

RECORDS = RELEASE21_DATA / "refinement" / "records"
ANALYSIS = RELEASE21_DATA / "analysis"
N_BOOT = 100_000
BOOT_SEED = 0
TIE_MARGIN = 0.01


def parent_tunnel(subset: str) -> str:
    return subset.split("-", 1)[0]


def _load_selection(arm: str, subset: str) -> dict | None:
    path = RECORDS / "selections" / arm / f"{subset}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _panel_rows() -> pd.DataFrame:
    rows = []
    for arm in PANEL_ARMS:
        for subset in ADMITTED:
            sel = _load_selection(arm, subset)
            if sel is None:
                continue
            start = sel["start"]
            selected = sel["selected"]
            rows.append(
                {
                    "arm": arm,
                    "subset": subset,
                    "family": family_of(subset),
                    "parent": parent_tunnel(subset),
                    "start_score": float(start["score"]),
                    "start_miou": float(start["gt_miou"]),
                    "selected_round": selected["name"],
                    "selected_score": float(selected["score"]),
                    "selected_miou": float(selected["gt_miou"]),
                    "delta_miou": float(selected["gt_miou"]) - float(start["gt_miou"]),
                    "delta_score": float(selected["score"]) - float(start["score"]),
                }
            )
    return pd.DataFrame(rows)


def _cluster_bootstrap(deltas_by_parent: dict[str, float], n: int = N_BOOT, seed: int = BOOT_SEED) -> dict:
    parents = sorted(deltas_by_parent)
    vals = np.asarray([deltas_by_parent[p] for p in parents], dtype=float)
    rng = np.random.default_rng(seed)
    means = []
    for _ in range(n):
        draw = rng.choice(vals, size=len(vals), replace=True)
        means.append(float(np.mean(draw)))
    arr = np.asarray(means)
    lo, hi = np.percentile(arr, [2.5, 97.5])
    return {
        "point": float(np.mean(vals)),
        "ci95": [float(lo), float(hi)],
        "n_boot": n,
        "n_clusters": len(parents),
    }


def _policy_selected(sel: dict, policy: str) -> dict:
    cands = {c["name"]: c for c in sel["candidates"]}
    start = cands["start"]
    if policy == "start":
        return start
    if policy == "round1":
        return cands.get("round1", start)
    if policy == "uniform_round":
        # Mean over available rounds; failed/missing count as start.
        mious = []
        for r in ("round1", "round2", "round3"):
            mious.append(float(cands[r]["gt_miou"]) if r in cands else float(start["gt_miou"]))
        return {
            "name": "uniform_round",
            "gt_miou": float(np.mean(mious)),
            "score": float("nan"),
        }
    if policy == "max_proxy":
        return max(cands.values(), key=lambda c: float(c["score"]))
    if policy == "oracle":
        return max(cands.values(), key=lambda c: float(c["gt_miou"]))
    if policy == "monotone":
        return sel["selected"]
    raise ValueError(policy)


def point_error_fractions(subset: str, run_dir: Path) -> dict[str, float]:
    """Join GT labels from the subset txt with pred_labels from only_label.csv."""
    only = run_dir / "only_label.csv"
    txt = REPO_ROOT / "data" / "subsets" / f"{subset}.txt"
    if not only.exists() or not txt.exists():
        return {"correct": float("nan"), "FN": float("nan"), "FP": float("nan"), "swap": float("nan")}
    pred = pd.read_csv(only)
    # Input columns: x,y,z,intensity,gt_label,gt_ring (0-indexed 4,5) — stage 6 convention.
    gt = np.loadtxt(txt, usecols=(4,)).astype(int)
    n = min(len(pred), len(gt))
    g = gt[:n]
    q = pred["pred_labels"].to_numpy()[:n].astype(int)
    return {
        "correct": float((g == q).mean()),
        "FN": float(((g > 0) & (q == 0)).mean()),
        "FP": float(((g == 0) & (q > 0)).mean()),
        "swap": float(((g > 0) & (q > 0) & (g != q)).mean()),
    }


def main() -> int:
    ANALYSIS.mkdir(parents=True, exist_ok=True)
    RECORDS.mkdir(parents=True, exist_ok=True)
    panel = _panel_rows()
    if panel.empty:
        raise SystemExit("no selections yet")
    missing = []
    for arm in PANEL_ARMS:
        for subset in ADMITTED:
            if _load_selection(arm, subset) is None:
                missing.append(f"{arm}/{subset}")
    if missing:
        raise SystemExit(f"incomplete selections ({len(missing)}): {', '.join(missing[:8])}...")

    panel.to_csv(RECORDS / "panel.csv", index=False)
    numbers: dict = {"n_admitted": len(ADMITTED), "arms": list(PANEL_ARMS)}

    # ---- Benefit ----
    benefit_lines = ["# Benefit", "", f"Admitted panel: {len(ADMITTED)} subsets × {len(PANEL_ARMS)} arms.", ""]
    for arm, part in panel.groupby("arm"):
        mean_start = float(part["start_miou"].mean())
        mean_sel = float(part["selected_miou"].mean())
        mean_d = float(part["delta_miou"].mean())
        by_parent = part.groupby("parent")["delta_miou"].mean().to_dict()
        boot = _cluster_bootstrap(by_parent)
        med = float(part["delta_miou"].median())
        up = int((part["delta_miou"] > 5e-4).sum())
        same = int((part["delta_miou"].abs() <= 5e-4).sum())
        down = int((part["delta_miou"] < -5e-4).sum())
        worst = float(part["delta_miou"].min())
        numbers[f"benefit_{arm}"] = {
            "mean_start": mean_start,
            "mean_selected": mean_sel,
            "mean_delta": mean_d,
            "median_delta": med,
            "bootstrap": boot,
            "up": up,
            "same": same,
            "down": down,
            "worst": worst,
        }
        benefit_lines += [
            f"## {arm}",
            "",
            f"- Start mean GT mIoU: {mean_start:.3f}",
            f"- Selected mean GT mIoU: {mean_sel:.3f}",
            f"- Mean paired Δ: {mean_d:.3f} (parent-tunnel bootstrap 95% [{boot['ci95'][0]:.3f}, {boot['ci95'][1]:.3f}])",
            f"- Median Δ: {med:.3f}; improved/unchanged/harmed: {up}/{same}/{down}; worst {worst:.3f}",
            "",
        ]
        for fam, g in part.groupby("family"):
            benefit_lines.append(f"- {fam}: mean Δ {g['delta_miou'].mean():.3f} (n={len(g)})")
        benefit_lines.append("")

    # All-27: non-admitted carry start.
    all27_lines = ["## All 27 subsets (non-admitted carry start)", ""]
    for arm in PANEL_ARMS:
        deltas = []
        for subset in EVAL_SUBSETS:
            start = json.loads((start_dir(subset) / "record.json").read_text())
            start_m = float(start["gt_miou"])
            if subset in ADMITTED:
                sel = _load_selection(arm, subset)
                deltas.append(float(sel["selected"]["gt_miou"]) - start_m)
            else:
                deltas.append(0.0)
        all27_lines.append(f"- {arm}: mean Δ over 27 = {float(np.mean(deltas)):.3f}")
        numbers[f"all27_delta_{arm}"] = float(np.mean(deltas))
    benefit_lines += all27_lines + [""]

    # Retrospective strata by start GT.
    benefit_lines.append("## Retrospective initial-GT strata (admitted only)")
    benefit_lines.append("")
    for arm, part in panel.groupby("arm"):
        for lo, hi, label in ((0.0, 0.5, "<0.5"), (0.5, 0.7, "[0.5,0.7]"), (0.7, 1.01, ">0.7")):
            g = part[(part["start_miou"] >= lo) & (part["start_miou"] < hi)]
            if g.empty:
                benefit_lines.append(f"- {arm} {label}: n=0")
            else:
                benefit_lines.append(
                    f"- {arm} {label}: n={len(g)}, mean Δ {g['delta_miou'].mean():.3f}"
                )
    (ANALYSIS / "benefit.md").write_text("\n".join(benefit_lines) + "\n", encoding="utf-8")

    # ---- Selection policies ----
    policy_rows = []
    sel_lines = ["# Selection policies", ""]
    policies = ("start", "round1", "uniform_round", "max_proxy", "monotone", "oracle")
    for arm in PANEL_ARMS:
        sel_lines.append(f"## {arm}")
        sel_lines.append("")
        means = {}
        for policy in policies:
            vals = []
            for subset in ADMITTED:
                sel = _load_selection(arm, subset)
                chosen = _policy_selected(sel, policy)
                vals.append(float(chosen["gt_miou"]))
                policy_rows.append(
                    {
                        "arm": arm,
                        "subset": subset,
                        "policy": policy,
                        "gt_miou": float(chosen["gt_miou"]),
                        "name": chosen.get("name"),
                    }
                )
            means[policy] = float(np.mean(vals))
            sel_lines.append(f"- {policy}: mean GT mIoU {means[policy]:.3f}")
        oracle = means["oracle"]
        mono = means["monotone"]
        recovery = mono / oracle if oracle else float("nan")
        regret = oracle - mono
        sel_lines.append(f"- Oracle recovery (monotone/oracle): {recovery:.3f}")
        sel_lines.append(f"- Regret (oracle − monotone): {regret:.3f}")
        sel_lines.append("")
        numbers[f"policies_{arm}"] = {**means, "oracle_recovery": recovery, "regret": regret}
        # Failed rounds
        fails = []
        for subset in ADMITTED:
            for r in (1, 2, 3):
                path = round_dir(arm, subset, r) / "record.json"
                if not path.exists():
                    fails.append(f"{subset}/r{r}:missing")
                    continue
                rec = json.loads(path.read_text())
                if not rec.get("valid"):
                    fails.append(f"{subset}/r{r}:{rec.get('failure_reason')}")
        sel_lines.append(f"Failed/invalid rounds ({len(fails)}): " + (", ".join(fails) if fails else "none"))
        sel_lines.append("")
    pd.DataFrame(policy_rows).to_csv(RECORDS / "policies.csv", index=False)
    (ANALYSIS / "selection.md").write_text("\n".join(sel_lines) + "\n", encoding="utf-8")

    # ---- Errors ----
    err_lines = ["# Error analysis", ""]
    yield_rows = []
    for arm in PANEL_ARMS:
        above = 0
        above_and_gt = 0
        total_valid = 0
        transitions = {"flag→refine": 0, "flag→accept": 0, "refine→accept": 0, "refine→flag": 0, "accept→refine": 0, "accept→flag": 0, "same": 0}
        start_err = []
        sel_err = []
        for subset in ADMITTED:
            start = json.loads((start_dir(subset) / "record.json").read_text())
            start_score = float(start["score"])
            start_miou = float(start["gt_miou"])
            start_band = start["band"]
            sel = _load_selection(arm, subset)
            sel_band = None
            # Find selected band from candidate
            for c in sel["candidates"]:
                if c["name"] == sel["selected"]["name"]:
                    # band may be missing on start — use start
                    if c["name"] == "start":
                        sel_band = start_band
                    else:
                        rec = json.loads((round_dir(arm, subset, c["round"]) / "record.json").read_text())
                        sel_band = rec["band"]
            key = f"{start_band}→{sel_band}" if start_band != sel_band else "same"
            if key in transitions:
                transitions[key] += 1
            else:
                transitions["same"] += 1

            for r in (1, 2, 3):
                path = round_dir(arm, subset, r) / "record.json"
                if not path.exists():
                    continue
                rec = json.loads(path.read_text())
                if not rec.get("valid"):
                    continue
                total_valid += 1
                if float(rec["score"]) > start_score:
                    above += 1
                    if float(rec["gt_miou"]) > start_miou:
                        above_and_gt += 1

            start_err.append(point_error_fractions(subset, start_dir(subset)))
            sel_name = sel["selected"]["name"]
            if sel_name == "start":
                sel_err.append(start_err[-1])
            else:
                sel_err.append(point_error_fractions(subset, round_dir(arm, subset, sel["selected"]["round"])))

        prec = above_and_gt / above if above else float("nan")
        yield_rows.append(
            {
                "arm": arm,
                "proxy_above_start": above,
                "also_gt_improve": above_and_gt,
                "accepted_precision": prec,
                "valid_proposals": total_valid,
            }
        )
        err_lines += [
            f"## {arm}",
            "",
            f"- Valid proposals: {total_valid}; proxy above start: {above}; of those also GT↑: {above_and_gt} (precision {prec:.3f})",
            f"- Band transitions: {transitions}",
            "",
        ]
        def _finite(x) -> bool:
            try:
                return bool(np.isfinite(x))
            except Exception:
                return False

        def mean_frac(rows, key):
            vals = [r[key] for r in rows if _finite(r[key])]
            return float(np.mean(vals)) if vals else float("nan")

        err_lines.append(
            "- Start point-error fractions: "
            + ", ".join(f"{k}={mean_frac(start_err, k):.3f}" for k in ("correct", "FN", "FP", "swap"))
        )
        err_lines.append(
            "- Selected point-error fractions: "
            + ", ".join(f"{k}={mean_frac(sel_err, k):.3f}" for k in ("correct", "FN", "FP", "swap"))
        )
        err_lines.append("")
        numbers[f"errors_{arm}"] = {
            "yield": yield_rows[-1],
            "transitions": transitions,
            "start_fractions": {k: mean_frac(start_err, k) for k in ("correct", "FN", "FP", "swap")},
            "selected_fractions": {k: mean_frac(sel_err, k) for k in ("correct", "FN", "FP", "swap")},
        }

    (ANALYSIS / "errors.md").write_text("\n".join(err_lines) + "\n", encoding="utf-8")
    (ANALYSIS / "numbers.json").write_text(json.dumps(numbers, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {ANALYSIS}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
