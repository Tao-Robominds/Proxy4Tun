#!/usr/bin/env python3
"""Summarise the GPT-5.6 medium arm.

Writes only under data/release2/analysis/gpt56_medium_rerun/. Does not rewrite
the panel analysis files.
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

from bo.paths import RELEASE2_DATA  # noqa: E402
from bo.release2.analyse_benefit import (  # noqa: E402
    _cluster_bootstrap,
    _load_selection,
    _policy_selected,
    parent_tunnel,
    point_error_fractions,
)
from bo.release2.refine import ADMITTED, MODEL_SLUG, round_dir, start_dir  # noqa: E402
from bo.release2.run_pair import EVAL_SUBSETS  # noqa: E402
from bo.runtime.metadata import family_of  # noqa: E402

ARMS = ("gpt56_medium",)
OUT = RELEASE2_DATA / "analysis" / "gpt56_medium_rerun"
RECORDS = RELEASE2_DATA / "refinement" / "records"


def _rows() -> pd.DataFrame:
    rows = []
    for arm in ARMS:
        for subset in ADMITTED:
            sel = _load_selection(arm, subset)
            if sel is None:
                raise SystemExit(f"missing selection {arm}/{subset}")
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


def _proposal_rows() -> pd.DataFrame:
    rows = []
    for arm in ARMS:
        for subset in ADMITTED:
            start = json.loads((start_dir(subset) / "record.json").read_text())
            for r in (1, 2, 3):
                path = round_dir(arm, subset, r) / "record.json"
                if not path.exists():
                    raise SystemExit(f"missing record {arm}/{subset}/r{r}")
                rec = json.loads(path.read_text())
                rows.append(
                    {
                        "arm": arm,
                        "subset": subset,
                        "round": r,
                        "valid": bool(rec.get("valid")),
                        "verdict": rec.get("verdict"),
                        "score": rec.get("score"),
                        "gt_miou": rec.get("gt_miou"),
                        "start_miou": float(start["gt_miou"]),
                        "model": (rec.get("provenance") or {}).get("model"),
                        "failure_reason": rec.get("failure_reason") or "",
                    }
                )
    return pd.DataFrame(rows)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    panel = _rows()
    props = _proposal_rows()
    panel.to_csv(OUT / "panel.csv", index=False)
    props.to_csv(OUT / "proposals.csv", index=False)

    numbers: dict = {
        "arms": list(ARMS),
        "model": {arm: MODEL_SLUG[arm] for arm in ARMS},
        "note": (
            "0.770 is the Release 1 deterministic 22-case selected mean, "
            "not a GPT-5.6 medium baseline. The GPT-5.6 high arm results were removed."
        ),
    }
    lines = [
        "# GPT-5.6 medium",
        "",
        "Same 15 admitted starts, frozen four-feature proxy, and selection rule.",
        "0.770 is not a reproduced GPT-5.6 medium baseline; Release 1 attributes that",
        "value to the deterministic arm on a 22-case panel.",
        "",
    ]
    for arm, part in panel.groupby("arm"):
        by_parent = part.groupby("parent")["delta_miou"].mean().to_dict()
        boot = _cluster_bootstrap(by_parent)
        up = int((part["delta_miou"] > 5e-4).sum())
        same = int((part["delta_miou"].abs() <= 5e-4).sum())
        down = int((part["delta_miou"] < -5e-4).sum())
        numbers[arm] = {
            "mean_start": float(part["start_miou"].mean()),
            "mean_selected": float(part["selected_miou"].mean()),
            "mean_delta": float(part["delta_miou"].mean()),
            "bootstrap": boot,
            "up": up,
            "same": same,
            "down": down,
            "worst": float(part["delta_miou"].min()),
        }
        lines += [
            f"## {arm} ({MODEL_SLUG[arm]})",
            "",
            f"- Start mean GT mIoU: {part['start_miou'].mean():.3f}",
            f"- Selected mean GT mIoU: {part['selected_miou'].mean():.3f}",
            f"- Mean paired Δ: {part['delta_miou'].mean():.3f} "
            f"(parent-tunnel 95% [{boot['ci95'][0]:.3f}, {boot['ci95'][1]:.3f}])",
            f"- Improved/unchanged/harmed: {up}/{same}/{down}; worst {part['delta_miou'].min():.3f}",
            "",
        ]

    lines += ["## Selection policies", ""]
    policies = ("start", "round1", "uniform_round", "max_proxy", "monotone", "oracle")
    policy_rows = []
    for arm in ARMS:
        means = {}
        for policy in policies:
            vals = []
            for subset in ADMITTED:
                sel = _load_selection(arm, subset)
                chosen = _policy_selected(sel, policy)
                vals.append(float(chosen["gt_miou"]))
                policy_rows.append(
                    {"arm": arm, "subset": subset, "policy": policy, "gt_miou": vals[-1]}
                )
            means[policy] = float(np.mean(vals))
        recovery = means["monotone"] / means["oracle"] if means["oracle"] else float("nan")
        regret = means["oracle"] - means["monotone"]
        numbers[arm]["policies"] = {**means, "oracle_recovery": recovery, "regret": regret}
        lines.append(f"### {arm}")
        lines.append("")
        for policy, value in means.items():
            lines.append(f"- {policy}: {value:.3f}")
        lines.append(f"- Oracle recovery: {recovery:.3f}; regret: {regret:.3f}")
        lines.append("")
    pd.DataFrame(policy_rows).to_csv(OUT / "policies.csv", index=False)

    lines += ["## Proposal stability", ""]
    for arm, g in props.groupby("arm"):
        delta = g["gt_miou"].astype(float) - g["start_miou"].astype(float)
        numbers[arm]["stability"] = {
            "n": int(len(g)),
            "n_valid": int(g["valid"].sum()),
            "mean_proposal_miou": float(g["gt_miou"].mean()),
            "std_delta": float(delta.std()),
            "frac_drop_gt_0.05": float((delta < -0.05).mean()),
            "models": sorted(set(g["model"].dropna().astype(str))),
        }
        lines += [
            f"- {arm}: valid {int(g['valid'].sum())}/{len(g)}; "
            f"mean proposal mIoU {g['gt_miou'].mean():.3f}; "
            f"std Δ {delta.std():.3f}; "
            f"share dropped >0.05 {(delta < -0.05).mean():.3f}",
        ]
    lines.append("")

    lines += ["## Retrospective initial-GT strata", ""]
    for arm, part in panel.groupby("arm"):
        for lo, hi, label in ((0.0, 0.5, "<0.5"), (0.5, 0.7, "[0.5,0.7]"), (0.7, 1.01, ">0.7")):
            g = part[(part["start_miou"] >= lo) & (part["start_miou"] < hi)]
            lines.append(
                f"- {arm} {label}: n={len(g)}"
                + ("" if g.empty else f", mean Δ {g['delta_miou'].mean():.3f}")
            )
    lines.append("")

    # Point-error fractions for selected outputs.
    lines += ["## Point-error fractions", ""]
    for arm in ARMS:
        start_err = []
        sel_err = []
        for subset in ADMITTED:
            start_err.append(point_error_fractions(subset, start_dir(subset)))
            sel = _load_selection(arm, subset)
            name = sel["selected"]["name"]
            if name == "start":
                sel_err.append(start_err[-1])
            else:
                sel_err.append(
                    point_error_fractions(subset, round_dir(arm, subset, sel["selected"]["round"]))
                )

        def mean_frac(rows, key):
            vals = [r[key] for r in rows if np.isfinite(r[key])]
            return float(np.mean(vals)) if vals else float("nan")

        numbers[arm]["point_error"] = {
            "start": {k: mean_frac(start_err, k) for k in ("correct", "FN", "FP", "swap")},
            "selected": {k: mean_frac(sel_err, k) for k in ("correct", "FN", "FP", "swap")},
        }
        lines.append(
            f"- {arm} selected: "
            + ", ".join(f"{k}={mean_frac(sel_err, k):.3f}" for k in ("correct", "FN", "FP", "swap"))
        )
    lines.append("")

    # All-27 carry-start means.
    lines += ["## All 27 subsets (non-admitted carry start)", ""]
    for arm in ARMS:
        deltas = []
        for subset in EVAL_SUBSETS:
            start = json.loads((start_dir(subset) / "record.json").read_text())
            start_m = float(start["gt_miou"])
            if subset in ADMITTED:
                sel = _load_selection(arm, subset)
                deltas.append(float(sel["selected"]["gt_miou"]) - start_m)
            else:
                deltas.append(0.0)
        numbers[arm]["all27_delta"] = float(np.mean(deltas))
        lines.append(f"- {arm}: {float(np.mean(deltas)):.3f}")

    (OUT / "comparison.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (OUT / "numbers.json").write_text(json.dumps(numbers, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
