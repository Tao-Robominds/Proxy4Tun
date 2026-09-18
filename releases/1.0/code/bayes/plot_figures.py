#!/usr/bin/env python3
"""Regenerate training/holdout figures from bo/bayes tables into manuscript figs/.

Thin wrapper around scripts/drawing/plot_proxy_fullstage.py with path overrides.
"""

from __future__ import annotations

import runpy
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))
from bo.paths import BAYES_PKG, MANUSCRIPT_FIGS, REPO_ROOT

REPO = REPO_ROOT
SCRIPT = REPO / "scripts" / "drawing" / "plot_proxy_fullstage.py"
BAYES = BAYES_PKG
MS_FIGS = MANUSCRIPT_FIGS
PAPER_FIGS = REPO / "paper" / "Proxy4Tun" / "figures"


def main() -> None:
    out = MS_FIGS if MS_FIGS.exists() else PAPER_FIGS
    src = SCRIPT.read_text(encoding="utf-8")
    patched = src
    # Keep REPO pointing at the real repository root even though the temp
    # script lives under bo/bayes/.
    patched = patched.replace(
        'REPO = Path(__file__).resolve().parents[2]',
        f'REPO = Path(r"{REPO}")',
    )
    patched = patched.replace(
        'TRAIN = REPO / "bo" / "full_stage" / "training_table.csv"',
        f'TRAIN = Path(r"{BAYES / "training_table.csv"}")',
    )
    patched = patched.replace(
        'HOLDOUT = REPO / "bo" / "full_stage" / "holdout_scores.csv"',
        f'HOLDOUT = Path(r"{BAYES / "holdout_scores.csv"}")',
    )
    patched = patched.replace(
        'MODELS = REPO / "bo" / "full_stage" / "models.json"',
        f'MODELS = Path(r"{BAYES / "models.json"}")',
    )
    patched = patched.replace(
        'OUT = REPO / "paper" / "Proxy4Tun" / "figures"',
        f'OUT = Path(r"{out}")',
    )
    tmp = BAYES / "_plot_proxy_fullstage_bayes.py"
    tmp.write_text(patched, encoding="utf-8")
    print(f"Running patched plotter → {out}")
    runpy.run_path(str(tmp), run_name="__main__")
    for name in (
        "proxy_training_fullstage.pdf",
        "proxy_holdout_fullstage.pdf",
    ):
        src_p = out / name
        print(f"  {'present' if src_p.exists() else 'MISSING'}: {src_p}")


if __name__ == "__main__":
    main()
