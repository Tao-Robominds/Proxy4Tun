#!/usr/bin/env python3
"""Build a GT-blind sanitized input packet for one subset.

Writes gpt56-refinement/packets/<subset>/ with:
  - packet.json (sanitized intrinsics, proxy, bounds, unlock flag, hashes)
  - images/ (symlink or copy of allowed PNGs from the anchor)
  - allowlist.md / denylist.md copies
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from bo.unified.spaces import family_of_subset, sibling_anchor_case, space_for_case  # noqa: E402
from bo.proxy_scale.score_scaled import score_scaled  # noqa: E402
from bo.full_stage.score_run import _anchor_run_dir  # noqa: E402


from constants import (  # noqa: E402
    AGENT_IMAGES,
    CAMPAIGN_DIR,
    GT_KEYS,
    KNOWLEDGE_DIR,
    MODEL_LABEL,
    PACKETS_DIR,
    STAGE1_UNLOCK,
)


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _sanitize_intrinsics(raw: dict[str, Any]) -> dict[str, Any]:
    out = {}
    for k, v in raw.items():
        if k in GT_KEYS or k.startswith("perf_"):
            continue
        if k.startswith("tier"):
            continue
        out[k] = v
    return out


def _bounds_table(subset: str) -> list[dict[str, Any]]:
    sibling = sibling_anchor_case(subset)
    dims = space_for_case(sibling)
    unlock = subset in STAGE1_UNLOCK
    rows = []
    for d in dims:
        if d.stage == "unfolding" and not unlock:
            continue
        rows.append(
            {
                "name": d.name,
                "stage": d.stage,
                "key": d.key,
                "kind": d.kind,
                "low": d.low,
                "high": d.high,
                "special": d.special,
            }
        )
    return rows


def build_packet(subset: str) -> Path:
    family = family_of_subset(subset)
    anchor_run = _anchor_run_dir(subset)
    scored = score_scaled(anchor_run, subset)
    intr_path = Path(anchor_run) / "intrinsics.json"
    raw_intr = json.loads(intr_path.read_text(encoding="utf-8")) if intr_path.exists() else {}
    sanitized = _sanitize_intrinsics(raw_intr)

    pkt_dir = PACKETS_DIR / subset
    img_dir = pkt_dir / "images"
    if pkt_dir.exists():
        shutil.rmtree(pkt_dir)
    img_dir.mkdir(parents=True)

    image_hashes = {}
    for name in AGENT_IMAGES:
        src = Path(anchor_run) / name
        if not src.exists():
            continue
        dst = img_dir / name
        shutil.copy2(src, dst)
        image_hashes[name] = _sha256(dst)

    # Knowledge hashes
    knowledge_hashes = json.loads((KNOWLEDGE_DIR / "hashes.json").read_text())["files"]

    allow = (CAMPAIGN_DIR / "allowlist.md").read_text(encoding="utf-8")
    deny = (CAMPAIGN_DIR / "denylist.md").read_text(encoding="utf-8")
    (pkt_dir / "allowlist.md").write_text(allow)
    (pkt_dir / "denylist.md").write_text(deny)

    packet = {
        "subset": subset,
        "family": family,
        "model": MODEL_LABEL,
        "built_at": datetime.now().isoformat(),
        "anchor_run": str(anchor_run),
        "stage1_unlocked": subset in STAGE1_UNLOCK,
        "recentre_residual_max_cm": scored.get("recentre_residual_max_cm"),
        "anchor_proxy_scaled": scored["proxy_scaled"],
        "anchor_proxy_raw": scored["proxy_raw"],
        "band": scored["band"],
        "intrinsics_gt_blind": sanitized,
        "lean_features": scored.get("features"),
        "parameter_bounds": _bounds_table(subset),
        "images": image_hashes,
        "knowledge_hashes": knowledge_hashes,
        "knowledge_dir": str(KNOWLEDGE_DIR.resolve()),
        "protocol": {
            "rounds": 3,
            "selection": (
                "monotone accept on scaled proxy vs anchor; "
                "among candidates within 0.01 of best proxy, "
                "prefer lowest recentre_residual_max_cm then higher proxy"
            ),
            "output_schema": {
                "observation": "str",
                "failure_mode": "str",
                "rationale": "str",
                "overlay": "dict[stage -> {param: value}]",
            },
            "rules": [
                "Propose ONE bounded overlay per round.",
                "Only use keys listed in parameter_bounds.",
                "Unfolding changes are allowed only when stage1_unlocked is true.",
                "Never request or use GT mIoU / evaluation metrics.",
                "Do not read data/reflect, bo-proxy-scale selections, or prior campaign reports.",
                "Prefer coordinated multi-stage changes when upstream defects are visible.",
            ],
        },
        "hashes": {
            "allowlist.md": hashlib.sha256(allow.encode()).hexdigest(),
            "denylist.md": hashlib.sha256(deny.encode()).hexdigest(),
            "packet_images": image_hashes,
        },
    }
    out = pkt_dir / "packet.json"
    out.write_text(json.dumps(packet, indent=2) + "\n", encoding="utf-8")
    # Prompt stub the agent reads
    prompt = _render_prompt(packet)
    (pkt_dir / "AGENT_PROMPT.md").write_text(prompt, encoding="utf-8")
    print(json.dumps({"subset": subset, "packet": str(out), "stage1_unlocked": packet["stage1_unlocked"], "proxy_scaled": packet["anchor_proxy_scaled"]}, indent=2))
    return pkt_dir


def _render_prompt(packet: dict[str, Any]) -> str:
    bounds_lines = [
        f"- `{r['stage']}.{r['key']}` ({r['kind']}): [{r['low']}, {r['high']}]"
        for r in packet["parameter_bounds"]
    ]
    img_lines = [f"- images/{n}" for n in packet["images"]]
    return f"""# GPT-5.6 Sol reflection — subset {packet['subset']} (round proposal)

You are a reflective parameter agent for the SAM4Tun tunnel-lining pipeline.
Propose ONE bounded parameter overlay to improve the GT-free scaled proxy.

## Isolation (hard rules)

Read ONLY:
- this packet (`packet.json`)
- `images/` under this packet directory
- knowledge files under `{packet['knowledge_dir']}` (sanitized experiences, ontology, priors)
- allowlist.md / denylist.md in this packet

Do NOT read or search for: data/bo/reflect/, bo/proxy_scale/selections/, campaign logs,
prior Fable/Cursor results, evaluation/, or any mIoU / ground-truth labels.

## State

- subset: `{packet['subset']}`
- family: `{packet['family']}`
- stage1_unlocked: `{packet['stage1_unlocked']}` (residual={packet['recentre_residual_max_cm']} cm)
- anchor_proxy_scaled: `{packet['anchor_proxy_scaled']:.4f}` (band={packet['band']})

### GT-blind intrinsics
```json
{json.dumps(packet['intrinsics_gt_blind'], indent=2)}
```

### Lean proxy features
```json
{json.dumps(packet['lean_features'], indent=2)}
```

### Allowed images
{chr(10).join(img_lines)}

### Parameter bounds (only these keys)
{chr(10).join(bounds_lines)}

## Task

1. Inspect the images and intrinsics.
2. Diagnose a failure mode using the ontology / sanitized experiences.
3. Propose a coordinated overlay within bounds.
4. Return **only** a single JSON object (no markdown fences) with keys:
   `observation`, `failure_mode`, `rationale`, `overlay`

`overlay` shape example:
{{"detecting": {{"hough_threshold_oblique": 40}}, "denoising": {{"mask_r_low": 2.8}}}}

If stage1_unlocked is true and centreline residual is large, you may include
`unfolding` keys (e.g. random_seed). Otherwise do not touch unfolding.
"""


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--subset", required=True)
    args = p.parse_args()
    # Ensure allow/deny docs exist
    if not (CAMPAIGN_DIR / "allowlist.md").exists():
        raise SystemExit("missing allowlist.md — create campaign docs first")
    build_packet(args.subset)


if __name__ == "__main__":
    main()
