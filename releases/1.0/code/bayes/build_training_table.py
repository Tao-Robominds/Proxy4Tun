#!/usr/bin/env python3
"""Build bo-bayes/training_table.csv from data/bo/bayes/<case>-trials manifests.

Selects exactly 40 ok+complete trials per train anchor (2-1, 3-1, 5-1):
prefer first 24 sobol_* then first 16 gp_* by trial_id order.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))
from bo.paths import BAYES_DATA, BAYES_PKG
from bo.elegant.features import CANDIDATE, family_of_subset  # noqa: E402

DATA_ROOT = BAYES_DATA
OUT = BAYES_PKG / "training_table.csv"
TRAIN_CASES = ("2-1", "3-1", "5-1")
# Defaults match contingency N0=32 / N_GP=8 after hard-constraint failure;
# override via --n0 / --n-gp for the original 24/16 split.
N0 = 32
N_GP = 8


def _pick(trials: list[dict[str, Any]], prefix: str, n: int) -> list[dict[str, Any]]:
    ok = [
        t
        for t in trials
        if t.get("status") == "ok"
        and t.get("mIoU") is not None
        and t.get("lean_complete")
        and str(t.get("acquisition", "")).startswith(prefix)
    ]
    ok = sorted(ok, key=lambda t: str(t.get("trial_id")))
    return ok[:n]


def main() -> None:
    import argparse

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--n0", type=int, default=N0)
    ap.add_argument("--n-gp", type=int, default=N_GP)
    args = ap.parse_args()
    n0, n_gp = args.n0, args.n_gp

    rows: list[dict[str, Any]] = []
    for case in TRAIN_CASES:
        man_path = DATA_ROOT / f"{case}-trials" / "manifest.json"
        if not man_path.exists():
            raise SystemExit(f"Missing {man_path}")
        man = json.loads(man_path.read_text(encoding="utf-8"))
        trials = man.get("trials", [])
        sobol = _pick(trials, "sobol", n0)
        gp = _pick(trials, "gp_", n_gp)
        if len(sobol) < n0 or len(gp) < n_gp:
            raise SystemExit(
                f"{case}: need {n0} sobol + {n_gp} gp, got {len(sobol)}/{len(gp)}"
            )
        print(f"{case}: using {len(sobol)} sobol + {len(gp)} gp")
        for t in sobol + gp:
            metrics = t.get("metrics") or {}
            row: dict[str, Any] = {
                "source": "bo-bayes",
                "case": case,
                "family": family_of_subset(case),
                "trial_id": t["trial_id"],
                "mIoU": float(t["mIoU"]),
                "stage1_varied": bool(t.get("stage1_varied", True)),
                "acquisition": t.get("acquisition"),
                "path": t.get("path", ""),
            }
            for k in CANDIDATE:
                v = metrics.get(k, 0.0)
                try:
                    fv = float(v)
                    row[k] = fv if fv == fv else 0.0
                except (TypeError, ValueError):
                    row[k] = 0.0
            rows.append(row)

    df = pd.DataFrame(rows)
    assert len(df) == 120, len(df)
    df.to_csv(OUT, index=False)
    print(f"Wrote {OUT} n={len(df)}")
    print(df.groupby(["case", "family"]).size())


if __name__ == "__main__":
    main()
