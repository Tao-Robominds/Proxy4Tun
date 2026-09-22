"""Canonical paths for the consolidated BO package.

Artifact trees live under ``data/bo/<phase>/`` (frozen; do not overwrite).
Override the root with ``PROXY4TUN_BO_DATA_ROOT`` only for *new* campaigns
written elsewhere (e.g. ``data/<experiment-id>/``).
"""

from __future__ import annotations

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PACKAGE_ROOT = Path(__file__).resolve().parent
VENV_PY = REPO_ROOT / "venv" / "bin" / "python"


def _bo_data_root() -> Path:
    override = (os.environ.get("PROXY4TUN_BO_DATA_ROOT") or "").strip()
    if override:
        return Path(override).resolve()
    return REPO_ROOT / "data" / "bo"


DATA_ROOT = _bo_data_root()
UNIFIED_DATA = DATA_ROOT / "unified"
ELEGANT_DATA = DATA_ROOT / "elegant"
FULL_STAGE_DATA = DATA_ROOT / "full_stage"
BAYES_DATA = DATA_ROOT / "bayes"
REFLECT_ROOT = DATA_ROOT / "reflect"
NOTEBOOK_DATA = DATA_ROOT / "notebook_direct"
ARCHIVE_V0_DATA = DATA_ROOT / "archive_v0"

# Sub-package roots (code)
UNIFIED_PKG = PACKAGE_ROOT / "unified"
ELEGANT_PKG = PACKAGE_ROOT / "elegant"
FULL_STAGE_PKG = PACKAGE_ROOT / "full_stage"
BAYES_PKG = PACKAGE_ROOT / "bayes"
PROXY_SCALE_PKG = PACKAGE_ROOT / "proxy_scale"
NOTEBOOK_PKG = PACKAGE_ROOT / "notebook_direct"
ARCHIVE_V0_PKG = PACKAGE_ROOT / "archive_v0"

# Manuscript figure output (read by bayes plotters)
MANUSCRIPT_FIGS = REPO_ROOT / "paper" / "Proxy4Tun" / "figs"

# Release 2 manuscript snapshot. Frozen: do not modify or delete.
RELEASE2_DATA = REPO_ROOT / "data" / "release2"
# Release 2.1 extension (12 out-of-band cases). Writes only under data/release2.1/.
RELEASE21_DATA = REPO_ROOT / "data" / "release2.1"
# Release 3 campaign (self-contained under data/release3/; never write into release2).
RELEASE3_DATA = REPO_ROOT / "data" / "release3"
PIPELINE_DIR = REPO_ROOT / "pipeline"
REFERENCES_DIR = REPO_ROOT / "configs" / "references"
