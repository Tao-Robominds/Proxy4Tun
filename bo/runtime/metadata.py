"""Engineering metadata for release-2 runs.

Expected ring counts come from data/subsets/<id>_rings_meta.json.
Travel direction comes from data/subsets/tunnel_meta.json (one vector per
parent tunnel). Neither helper reads point-level labels or ring indices.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
SUBSETS = _REPO / "data" / "subsets"
TUNNEL_META_PATH = SUBSETS / "tunnel_meta.json"

_FAMILY = {
    "1": "staggered",
    "2": "staggered",
    "3": "continuous",
    "4": "complex",
    "5": "complex",
}

DEV_SUBSETS: tuple[str, ...] = ("2-1", "3-1", "5-1")


def family_of(subset: str) -> str:
    """Return staggered, continuous, or complex."""
    tunnel = subset.split("-", 1)[0]
    try:
        return _FAMILY[tunnel]
    except KeyError as exc:
        raise ValueError(f"unknown tunnel in subset {subset!r}") from exc


def expected_rings(subset: str) -> int:
    """Design/acquisition ring count from the subset's engineering metadata."""
    path = SUBSETS / f"{subset}_rings_meta.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("tunnel_id") not in (None, subset):
        raise ValueError(f"{path} tunnel_id {data.get('tunnel_id')!r} != {subset}")
    return int(data["n_rings_kept"])


@lru_cache(maxsize=1)
def load_tunnel_meta() -> dict:
    return json.loads(TUNNEL_META_PATH.read_text(encoding="utf-8"))


def tunnel_meta(subset: str) -> dict:
    """Drive-direction record for ``subset``.

    ``h_axis_direction_xy`` is the subset vector when headings differ inside
    the parent tunnel, otherwise the shared tunnel vector.
    """
    tunnel = subset.split("-", 1)[0]
    data = load_tunnel_meta()
    if tunnel not in data:
        raise KeyError(f"no tunnel_meta entry for tunnel {tunnel} (subset {subset})")
    raw = data[tunnel]
    out = dict(raw)
    per_subset = (raw.get("subsets") or {}).get(subset)
    if per_subset is not None:
        out["h_axis_direction_xy"] = list(per_subset)
    if out.get("h_axis_direction_xy") is None:
        raise KeyError(f"no drive direction for subset {subset}")
    return out


def drive_direction_xy(subset: str) -> tuple[float, float]:
    vec = tunnel_meta(subset)["h_axis_direction_xy"]
    return float(vec[0]), float(vec[1])
