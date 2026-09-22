#!/usr/bin/env python3
"""Write immutable-input manifest for Release 2.1 (read-only R2 assets)."""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from bo.paths import RELEASE2_DATA, RELEASE21_DATA, REPO_ROOT  # noqa: E402
from bo.release2_1.refine import EXTENSION_CASES  # noqa: E402

PROXY = REPO_ROOT / "configs" / "proxy" / "four_feature.json"
PAIRS = RELEASE2_DATA / "degradation" / "records" / "pairs.csv"
RANDOM = REPO_ROOT / "configs" / "random_arm.json"
BANK = REPO_ROOT / "configs" / "example_bank.json"
R2_PANEL = RELEASE2_DATA / "refinement" / "records" / "panel.csv"
GPT_PANEL = RELEASE2_DATA / "analysis" / "gpt56_medium_rerun" / "panel.csv"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    RELEASE21_DATA.mkdir(parents=True, exist_ok=True)
    refs = {}
    for subset in EXTENSION_CASES:
        rec = RELEASE2_DATA / "references" / subset / "record.json"
        refs[subset] = {
            "record": str(rec.relative_to(REPO_ROOT)),
            "exists": rec.exists(),
            "sha256": sha256(rec) if rec.exists() else None,
        }
    manifest = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "extension_cases": list(EXTENSION_CASES),
        "skip_plans": [1, 2, 3],
        "protocol": "release2 plan4",
        "frozen_inputs": {
            "four_feature_proxy": {"path": str(PROXY.relative_to(REPO_ROOT)), "sha256": sha256(PROXY)},
            "pairs_csv": {"path": str(PAIRS.relative_to(REPO_ROOT)), "sha256": sha256(PAIRS)},
            "random_arm": {"path": str(RANDOM.relative_to(REPO_ROOT)), "sha256": sha256(RANDOM)},
            "example_bank": {"path": str(BANK.relative_to(REPO_ROOT)), "sha256": sha256(BANK)},
            "r2_panel_15": {"path": str(R2_PANEL.relative_to(REPO_ROOT)), "sha256": sha256(R2_PANEL)},
            "gpt56_medium_panel_15": {
                "path": str(GPT_PANEL.relative_to(REPO_ROOT)),
                "sha256": sha256(GPT_PANEL),
            },
        },
        "reference_starts": refs,
        "write_root": str((RELEASE21_DATA).relative_to(REPO_ROOT)),
        "never_write": ["data/release2/", "data/anchors/", "data/baseline", "data/bo/"],
    }
    out = RELEASE21_DATA / "INPUT_MANIFEST.json"
    out.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print("wrote", out)


if __name__ == "__main__":
    main()
