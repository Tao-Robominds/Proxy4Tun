#!/usr/bin/env python3
"""Build registry.json mapping every holdout run to an existing (or new) path.

Reuse by reference — no large copies. New missing runs land under data/bo-elegant/.
"""

from __future__ import annotations

import json
from pathlib import Path

from features import FAMILY_ANCHOR, HOLDOUT_SUBSETS, family_of_subset

REPO_ROOT = Path(__file__).resolve().parent.parent
BO_UNIFIED = REPO_ROOT / "data" / "bo-unified"
ANCHORS = REPO_ROOT / "data" / "anchors"
ELEGANT = REPO_ROOT / "data" / "bo-elegant"
OUT = Path(__file__).resolve().parent / "registry.json"

# Sibling params used by existing bo-unified holdouts (tunnel-local).
# For new runs we keep the same convention so anchor/bad pairs are comparable.
SIBLING_PARAMS: dict[str, str] = {
    "1": "anchors/unified/params/1-1",
    "2": "anchors/unified/params/2-1",
    "3": "anchors/unified/params/3-1-1",
    "4": "anchors/unified/params/4-1",
    "5": "anchors/unified/params/5-1",
}


def _existing_family_proxy(subset: str, kind: str) -> Path | None:
    run = BO_UNIFIED / f"{subset}-family-proxy" / "runs" / f"{subset}-{kind}"
    if (run / "only_label.csv").exists() or (run / "intrinsics.json").exists():
        return run
    return None


def _anchor_tree(subset: str) -> Path | None:
    """Frozen data/anchors/<subset> for ex-anchor 'good' runs (1-1, 4-1)."""
    run = ANCHORS / subset
    if (run / "only_label.csv").exists() and (run / "evaluation" / "performance.md").exists():
        return run
    return None


def _elegant_path(subset: str, kind: str) -> Path:
    return ELEGANT / f"{subset}-holdout" / "runs" / f"{subset}-{kind}"


def build() -> dict:
    entries = []
    for family, subsets in HOLDOUT_SUBSETS.items():
        for subset in subsets:
            tunnel = subset.split("-")[0]
            params_dir = SIBLING_PARAMS[tunnel]
            fam_anchor = FAMILY_ANCHOR[family]
            for kind in ("anchor", "bad"):
                source = None
                path = None
                status = "missing"

                if kind == "anchor":
                    # Prefer existing family-proxy good run; else frozen anchors for 1-1/4-1.
                    path = _existing_family_proxy(subset, "anchor")
                    if path is not None:
                        source = "bo-unified"
                        status = "reuse"
                    else:
                        path = _anchor_tree(subset)
                        if path is not None:
                            source = "data/anchors"
                            status = "reuse"
                else:
                    path = _existing_family_proxy(subset, "bad")
                    if path is not None:
                        source = "bo-unified"
                        status = "reuse"

                if path is None:
                    path = _elegant_path(subset, kind)
                    source = "bo-elegant"
                    if (path / "only_label.csv").exists() or (path / "intrinsics.json").exists():
                        status = "reuse"
                    else:
                        status = "to_run"

                entries.append(
                    {
                        "subset": subset,
                        "family": family,
                        "family_anchor": fam_anchor,
                        "config_kind": kind,
                        "run_id": f"{subset}-{kind}",
                        "path": str(path.relative_to(REPO_ROOT)),
                        "params_dir": params_dir,
                        "source": source,
                        "status": status,
                    }
                )
    payload = {
        "train_anchors": ["2-1", "3-1", "5-1"],
        "n_holdout_subsets": sum(len(v) for v in HOLDOUT_SUBSETS.values()),
        "n_runs": len(entries),
        "n_reuse": sum(1 for e in entries if e["status"] == "reuse"),
        "n_to_run": sum(1 for e in entries if e["status"] == "to_run"),
        "runs": entries,
    }
    OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(
        f"Wrote {OUT}: {payload['n_runs']} runs "
        f"({payload['n_reuse']} reuse, {payload['n_to_run']} to_run)"
    )
    for e in entries:
        if e["status"] == "to_run":
            print(f"  TO_RUN {e['run_id']} -> {e['path']}")
    return payload


if __name__ == "__main__":
    build()
