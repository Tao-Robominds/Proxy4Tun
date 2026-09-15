#!/usr/bin/env python3
"""Contingency: raise N0 (more Sobol), discard old GP tail, regenerate n_gp trials.

Default: N0=32, N_GP=8 (still 40 valid trials per family).
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))
from bo.bayes.run_bayes_trials import (  # noqa: E402
    TRAIN_CASES,
    _load_manifest,
    _ok_trials,
    _save_manifest,
    _study,
    run_campaign,
)


def archive_gp_trials(case: str) -> int:
    """Move existing gp_* trials to archived_gp so they no longer count."""
    man = _load_manifest(case)
    keep, archived = [], []
    for t in man.get("trials", []):
        if str(t.get("acquisition", "")).startswith("gp_"):
            archived.append(t)
        else:
            keep.append(t)
    man["trials"] = keep
    man.setdefault("archived_gp", [])
    man["archived_gp"].extend(archived)
    man["archived_gp_at"] = datetime.now().isoformat()
    _save_manifest(case, man)
    return len(archived)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--n0", type=int, default=32)
    p.add_argument("--n-gp", type=int, default=8)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--cases", nargs="+", default=list(TRAIN_CASES))
    args = p.parse_args()

    for case in args.cases:
        n_arch = archive_gp_trials(case)
        print(f"{case}: archived {n_arch} old GP trials; targeting N0={args.n0} N_GP={args.n_gp}")
        run_campaign(case, n0=args.n0, n_gp=args.n_gp, seed=args.seed, force=False)


if __name__ == "__main__":
    main()
