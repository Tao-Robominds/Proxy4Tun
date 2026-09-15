#!/usr/bin/env python3
"""Resumable Gemini 3.8 Stage-3 campaign orchestrator (arm=gemini38).

Does not call an LLM itself. Emit sanitized packets, validate proposal JSON
against family BO spaces, log CoT, execute via refine_pilot.run_round, select,
and slim intermediates. Parent agent supplies proposals from a fresh
Gemini 3.8 subagent per case (`model=inherit`; resumed for rounds 2–3).

Usage:
  ./venv/bin/python bo/sc_general/run_gemini38_campaign.py --derive-panel
  ./venv/bin/python bo/sc_general/run_gemini38_campaign.py --emit 3-4
  ./venv/bin/python bo/sc_general/run_gemini38_campaign.py --apply 3-4 --round 1 \
      --proposal-json data/sc-general/stage3/packets-gemini38/3-4/round1_proposal.json
  ./venv/bin/python bo/sc_general/run_gemini38_campaign.py --finish 3-4
  ./venv/bin/python bo/sc_general/run_gemini38_campaign.py --status
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import shutil
import signal
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from bo.sc_general.refine_pilot import (  # noqa: E402
    ARM_PROPOSER,
    PNG_NAMES,
    build_context,
    out_root_for,
    packet_dir_for,
    run_round,
)
from bo.sc_general.overlay_validator import validate_overlay  # noqa: E402
from bo.sc_general.select_round import select, select_dir_for  # noqa: E402
from bo.sc_general.stage3_report import PANEL  # noqa: E402

ARM = "gemini38"
MODEL_ID = "inherit"
STAGE3 = _REPO / "data" / "sc-general" / "stage3"
CAMPAIGN = STAGE3 / "campaign_gemini38.md"
HOLDOUT = _REPO / "data" / "sc-general" / "stage2" / "holdout_scores.csv"
BASELINE_CSV = _REPO / "exports" / "sc-general-fable51-evaluation" / "27_baseline_four_feature.csv"
AGENT_STATE = STAGE3 / "gemini38_agent_state.json"
FREE_PAUSE_GB = 50.0
KEEP_ROUND_NAMES = {
    "reflection_record.json",
    "intrinsics.json",
    "offline_gt.json",
    "only_label.csv",
    "evaluation_offline.json",
    "sc_features.json",
    "proxy_score.json",
    "agent_feedback.json",
}
KEEP_ROUND_DIRS = {"evaluation"}
EXTRA_IMAGES = ["sam_depth_input.png", "depth_map.png"]


def _append(text: str) -> None:
    CAMPAIGN.parent.mkdir(parents=True, exist_ok=True)
    with CAMPAIGN.open("a", encoding="utf-8") as fh:
        fh.write(text if text.endswith("\n") else text + "\n")


def free_gb() -> float:
    return shutil.disk_usage(_REPO).free / 1024**3


def derive_panel() -> list[str]:
    """Label-free panel: proxy_scaled ∈ [0.5, 0.7) from frozen baseline CSV."""
    if BASELINE_CSV.exists():
        df = pd.read_csv(BASELINE_CSV)
        # Accept either proxy_scaled or proxy column names.
        col = "proxy_scaled" if "proxy_scaled" in df.columns else "proxy"
        if "config_kind" in df.columns:
            df = df[df["config_kind"] == "anchor"]
        band = df[(df[col] >= 0.5) & (df[col] < 0.7)].copy()
        got = sorted(band["subset"].astype(str).tolist())
    else:
        hs = pd.read_csv(HOLDOUT)
        a = hs[hs["config_kind"] == "anchor"]
        band = a[(a["proxy"] >= 0.5) & (a["proxy"] < 0.7)]
        got = sorted(band["subset"].astype(str).tolist())

    expected = sorted(PANEL)
    if got != expected:
        raise SystemExit(
            f"panel mismatch:\n  got={got}\n  expected={expected}\n"
            f"  missing={sorted(set(expected) - set(got))}\n"
            f"  extra={sorted(set(got) - set(expected))}"
        )
    assert len(got) == 22, f"expected 22 cases, got {len(got)}"
    # Preserve PANEL order for campaign sequencing.
    return list(PANEL)



def _load_agent_state() -> dict[str, Any]:
    if AGENT_STATE.exists():
        return json.loads(AGENT_STATE.read_text(encoding="utf-8"))
    return {"cases": {}}


def _save_agent_state(state: dict[str, Any]) -> None:
    AGENT_STATE.parent.mkdir(parents=True, exist_ok=True)
    AGENT_STATE.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")


def set_agent_id(subset: str, agent_id: str) -> None:
    state = _load_agent_state()
    state.setdefault("cases", {})[subset] = {
        "agent_id": agent_id,
        "model": MODEL_ID,
        "updated_at": datetime.now().isoformat(),
    }
    _save_agent_state(state)


def get_agent_id(subset: str) -> str | None:
    return (_load_agent_state().get("cases") or {}).get(subset, {}).get("agent_id")


def _copy_images(src_run: Path, img_dir: Path) -> list[str]:
    img_dir.mkdir(parents=True, exist_ok=True)
    attached: list[str] = []
    names = list(PNG_NAMES) + [n for n in EXTRA_IMAGES if n not in PNG_NAMES]
    for name in names:
        src = src_run / name
        if src.exists():
            dest = img_dir / name
            shutil.copy2(src, dest)
            attached.append(str(dest))
    return attached


def emit_packet(subset: str, *, write_overlay: bool = True) -> dict[str, Any]:
    """Build GT-blind context + AGENT_PROMPT + image attachments for the next round."""
    if subset not in PANEL:
        raise SystemExit(f"{subset} not in 22-case panel")
    ctx = build_context(subset, arm=ARM, write_overlay=write_overlay)
    packet_dir = packet_dir_for(subset, arm=ARM)
    packet_dir.mkdir(parents=True, exist_ok=True)

    # Prefer latest successful round images when history exists; else anchor.
    root = out_root_for(subset, arm=ARM)
    src_run = Path(ctx["anchor"]["run_dir"])
    for rd in sorted(root.glob("round*"), reverse=True):
        if (rd / "reflection_record.json").exists() and (rd / "depth_map_viridis.png").exists():
            src_run = rd
            break
    img_dir = packet_dir / "images"
    attached = _copy_images(src_run, img_dir)
    # Also keep correspondence overlay if present.
    ov = packet_dir / "sc_correspondence_overlay.png"
    if ov.exists():
        attached.append(str(ov))

    next_round = 1
    for r in (1, 2, 3):
        rec = root / f"round{r}" / "reflection_record.json"
        if rec.exists():
            data = json.loads(rec.read_text(encoding="utf-8"))
            if data.get("status") == "ok":
                next_round = r + 1
    next_round = min(next_round, 3)

    bounds_lines = []
    for b in ctx["parameter_bounds"]:
        bounds_lines.append(
            f"- `{b['stage']}.{b['key']}` ({b['kind']}): [{b['low']}, {b['high']}]"
        )

    hist = ctx.get("history") or []
    prompt = f"""# Gemini 3.8 reflection — subset {subset} (propose round {next_round})

You are a reflective parameter agent for the SAM4Tun tunnel-lining pipeline.
Propose ONE bounded multi-stage overlay to improve the GT-free SC-general proxy.

## Isolation (hard rules)

Read ONLY:
- this prompt and the attached diagnostic images
- `context.json` in this packet directory
- ontology files listed under context.ontology (generic priors only)

Do NOT read or search for:
- `evaluation/`, `offline_gt.json`, `performance.md`, any mIoU / GT labels
- GT-bearing CSVs, holdout score tables with mIoU columns used as targets
- `data/sc-general/stage3/selections/`, `selections-fable/`, `selections-gpt56/`,
  Fable/GPT/deterministic refinement trees, or other cases' Gemini proposals
- `data/bo/`, `data/anchors/`, `data/baseline`

## State

- subset: `{subset}`
- family: `{ctx['family']}`
- lining_mode: `{ctx['lining_mode']}`
- stage1_unlocked: `{ctx['stage1_unlocked']}` (residual gate 10 cm)
- arm: `{ARM}` / proposer: `{ARM_PROPOSER[ARM]}`
- model: `{MODEL_ID}`

### Anchor (GT-blind)
```json
{json.dumps(ctx['anchor'], indent=2)}
```

### Intrinsics (GT-blind)
```json
{json.dumps(ctx['intrinsics_gt_blind'], indent=2)}
```

### Prior rounds (this arm only)
```json
{json.dumps(hist, indent=2)}
```

### Parameter bounds (ONLY these keys; reject anything else)
{chr(10).join(bounds_lines)}

## Required output

Write a single JSON object to:
`{packet_dir / f'round{next_round}_proposal.json'}`

Schema:
```json
{{
  "observation": "...",
  "rule": "...",
  "failure_mode": "...",
  "rationale": "...",
  "overlay": {{ "denoising": {{}}, "enhancing": {{}}, "detecting": {{}}, "sam": {{}} }},
  "full": false
}}
```

Use observation → rule → failure_mode → overlay. Stay inside bounds. If
stage1_unlocked is false, omit unfolding. Do not invent dead knobs.
"""
    prompt_path = packet_dir / "AGENT_PROMPT.md"
    prompt_path.write_text(prompt, encoding="utf-8")
    meta = {
        "subset": subset,
        "next_round": next_round,
        "stage1_unlocked": ctx["stage1_unlocked"],
        "context_path": ctx["context_path"],
        "prompt_path": str(prompt_path),
        "image_attachments": attached,
        "agent_id": get_agent_id(subset),
        "model": MODEL_ID,
        "emitted_at": datetime.now().isoformat(),
    }
    (packet_dir / "emit_meta.json").write_text(
        json.dumps(meta, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(meta, indent=2))
    return meta


def _extract_json_blob(text: str) -> dict[str, Any] | None:
    """Best-effort parse of a proposal JSON from agent prose."""
    text = text.strip()
    try:
        obj = json.loads(text)
        if isinstance(obj, dict) and "overlay" in obj:
            return obj
    except json.JSONDecodeError:
        pass
    # Fenced block
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, flags=re.DOTALL)
    if m:
        try:
            obj = json.loads(m.group(1))
            if isinstance(obj, dict) and "overlay" in obj:
                return obj
        except json.JSONDecodeError:
            pass
    # First balanced {...} containing "overlay"
    start = text.find("{")
    while start >= 0:
        depth = 0
        for i in range(start, len(text)):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    chunk = text[start : i + 1]
                    if '"overlay"' in chunk:
                        try:
                            obj = json.loads(chunk)
                            if isinstance(obj, dict) and "overlay" in obj:
                                return obj
                        except json.JSONDecodeError:
                            break
                    break
        start = text.find("{", start + 1)
    return None


def load_proposal(path: Path) -> dict[str, Any]:
    raw = path.read_text(encoding="utf-8")
    try:
        obj = json.loads(raw)
    except json.JSONDecodeError:
        obj = _extract_json_blob(raw)
        if obj is None:
            raise SystemExit(f"could not parse proposal JSON from {path}")
    if "overlay" not in obj:
        raise SystemExit(f"proposal missing overlay: {path}")
    return obj


def _clear_stale_gpu_pipeline() -> None:
    """Kill orphaned stage scripts that can leave the GPU OOM for the next run."""
    try:
        out = subprocess.check_output(
            ["nvidia-smi", "--query-compute-apps=pid,process_name", "--format=csv,noheader"],
            text=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        return
    markers = (
        "anchors/unified",
        "1_unfold",
        "2_denois",
        "3_enhanc",
        "4_detect",
        "5_sam",
        "6_reproj",
    )
    for line in out.splitlines():
        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 2:
            continue
        pid_s, name = parts[0], parts[1]
        if not any(m in name for m in markers):
            continue
        try:
            pid = int(pid_s)
            os.kill(pid, signal.SIGKILL)
            print(f"cleared stale GPU pid={pid} ({name})", file=sys.stderr)
        except (ValueError, ProcessLookupError, PermissionError):
            continue


def apply_proposal(
    subset: str,
    round_id: int,
    proposal: dict[str, Any],
    *,
    provenance: dict[str, Any] | None = None,
) -> dict[str, Any]:
    _clear_stale_gpu_pipeline()
    ctx = build_context(subset, arm=ARM, write_overlay=False)
    unlocked = bool(ctx["stage1_unlocked"])
    ok, errors, overlay = validate_overlay(
        subset, proposal["overlay"], stage1_unlocked=unlocked
    )
    if not ok:
        raise SystemExit(f"invalid overlay for {subset} R{round_id}: {errors}")

    observation = proposal.get("observation") or ""
    rule = proposal.get("rule") or proposal.get("ontology_rule") or ""
    failure_mode = proposal.get("failure_mode") or ""
    rationale = proposal.get("rationale") or ""
    full = bool(proposal.get("full")) or bool(overlay.get("unfolding"))

    packet_dir = packet_dir_for(subset, arm=ARM)
    packet_dir.mkdir(parents=True, exist_ok=True)
    prop_path = packet_dir / f"round{round_id}_proposal.json"
    cleaned = {
        "observation": observation,
        "rule": rule,
        "failure_mode": failure_mode,
        "rationale": rationale,
        "overlay": overlay,
        "full": full,
        "validated_at": datetime.now().isoformat(),
        "provenance": provenance or {},
    }
    prop_path.write_text(json.dumps(cleaned, indent=2) + "\n", encoding="utf-8")

    _append(
        f"\n## {subset} — round {round_id}\n\n"
        f"- Observation: {observation}\n"
        f"- Rule: {rule}\n"
        f"- Failure mode: {failure_mode}\n"
        f"- Rationale: {rationale}\n"
        f"- Overlay: `{json.dumps(overlay, separators=(',', ':'))}`\n"
        f"- full={full}\n"
        f"- provenance: `{json.dumps(provenance or {}, separators=(',', ':'))}`\n"
    )

    prov = {
        "model": MODEL_ID,
        "proposer": ARM_PROPOSER[ARM],
        "agent_id": (provenance or {}).get("agent_id") or get_agent_id(subset),
        "proposal_path": str(prop_path),
        **(provenance or {}),
    }
    rec = run_round(
        subset,
        round_id,
        overlay,
        arm=ARM,
        full=full,
        rationale=rationale,
        provenance=prov,
    )
    proxy = rec.get("proxy_scaled")
    finite = proxy is not None and math.isfinite(float(proxy))
    _append(
        f"### Result\n"
        f"- status={rec['status']} proxy={proxy} band={rec.get('band')} "
        f"residual={rec.get('recentre_residual_max_cm')} "
        f"elapsed={rec.get('elapsed_s')} finite_proxy={finite}\n"
        f"- output: `{rec.get('output_dir')}`\n"
    )
    if rec["status"] != "ok" or not finite:
        raise SystemExit(
            f"round failed gate: status={rec['status']} proxy={proxy} "
            f"out={rec.get('output_dir')}"
        )
    # Refresh packet for next round.
    emit_packet(subset, write_overlay=False)
    return rec


def slim_case(subset: str) -> dict[str, Any]:
    """Retain scoring essentials; remove bulky reproducible intermediates."""
    root = out_root_for(subset, arm=ARM)
    freed = 0
    removed = 0
    for rd in root.glob("round*"):
        if not rd.is_dir():
            continue
        for p in list(rd.iterdir()):
            if p.name in KEEP_ROUND_NAMES or p.name in KEEP_ROUND_DIRS:
                continue
            try:
                if p.is_dir():
                    size = sum(f.stat().st_size for f in p.rglob("*") if f.is_file())
                    shutil.rmtree(p)
                else:
                    size = p.stat().st_size
                    p.unlink()
                freed += size
                removed += 1
            except OSError as exc:
                print(f"WARN slim skip {p}: {exc}", file=sys.stderr)
    info = {
        "subset": subset,
        "removed": removed,
        "freed_gb": round(freed / 1024**3, 3),
        "free_gb_after": round(free_gb(), 2),
    }
    _append(
        f"### Slim\n- removed={removed} freed_gb={info['freed_gb']} "
        f"free_after={info['free_gb_after']} GB\n"
    )
    print(json.dumps(info, indent=2))
    if info["free_gb_after"] < FREE_PAUSE_GB:
        _append(
            f"**PAUSE**: free disk {info['free_gb_after']} GB < {FREE_PAUSE_GB} GB\n"
        )
        print(
            f"PAUSE: free disk {info['free_gb_after']} GB < {FREE_PAUSE_GB} GB",
            file=sys.stderr,
        )
    return info


def finish_case(subset: str) -> dict[str, Any]:
    sel = select(subset, arm=ARM)
    _append(
        f"\n### Selection ({subset})\n"
        f"- selected **{sel['selected']['round']}** "
        f"Δproxy={sel['delta_proxy_scaled']:+.3f} "
        f"ΔmIoU={sel.get('delta_mIoU_offline')}\n"
        f"- reason: {sel['selection_reason']}\n"
    )
    slim = slim_case(subset)
    out = {"selection": sel, "slim": slim}
    print(
        f"DONE {subset}: {sel['selected']['round']} "
        f"dproxy={sel['delta_proxy_scaled']:+.3f} "
        f"dmiou={sel.get('delta_mIoU_offline')}"
    )
    return out


def case_done(subset: str) -> bool:
    root = out_root_for(subset, arm=ARM)
    sel = select_dir_for(ARM) / f"{subset}.json"
    if not sel.exists():
        return False
    for r in (1, 2, 3):
        rec = root / f"round{r}" / "reflection_record.json"
        if not rec.exists():
            return False
        data = json.loads(rec.read_text(encoding="utf-8"))
        if data.get("status") != "ok" or data.get("proxy_scaled") is None:
            return False
    return True


def status() -> None:
    panel = derive_panel()
    rows = []
    for s in panel:
        root = out_root_for(s, arm=ARM)
        rounds_ok = 0
        for r in (1, 2, 3):
            rec = root / f"round{r}" / "reflection_record.json"
            if rec.exists():
                data = json.loads(rec.read_text(encoding="utf-8"))
                if data.get("status") == "ok":
                    rounds_ok += 1
        sel = select_dir_for(ARM) / f"{s}.json"
        rows.append(
            {
                "subset": s,
                "family": family_of_subset(s),
                "rounds_ok": rounds_ok,
                "selected": sel.exists(),
                "done": case_done(s),
                "agent_id": get_agent_id(s),
            }
        )
    df = pd.DataFrame(rows)
    print(df.to_string(index=False))
    print(
        f"\ndone={int(df['done'].sum())}/22  "
        f"selections={int(df['selected'].sum())}  "
        f"free_gb={free_gb():.1f}"
    )


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--derive-panel", action="store_true")
    p.add_argument("--emit", metavar="SUBSET")
    p.add_argument("--apply", metavar="SUBSET")
    p.add_argument("--round", type=int)
    p.add_argument("--proposal-json", type=Path)
    p.add_argument("--agent-id", default=None)
    p.add_argument("--set-agent", nargs=2, metavar=("SUBSET", "AGENT_ID"))
    p.add_argument("--finish", metavar="SUBSET")
    p.add_argument("--slim", metavar="SUBSET")
    p.add_argument("--status", action="store_true")
    args = p.parse_args()

    STAGE3.mkdir(parents=True, exist_ok=True)

    if args.derive_panel:
        panel = derive_panel()
        print(json.dumps({"n": len(panel), "panel": panel}, indent=2))
        return
    if args.set_agent:
        set_agent_id(args.set_agent[0], args.set_agent[1])
        print(json.dumps({"subset": args.set_agent[0], "agent_id": args.set_agent[1]}))
        return
    if args.emit:
        emit_packet(args.emit)
        return
    if args.apply:
        if args.round is None or args.proposal_json is None:
            p.error("--apply requires --round and --proposal-json")
        if args.agent_id:
            set_agent_id(args.apply, args.agent_id)
        prop = load_proposal(args.proposal_json)
        apply_proposal(
            args.apply,
            args.round,
            prop,
            provenance={"agent_id": args.agent_id or get_agent_id(args.apply)},
        )
        return
    if args.finish:
        finish_case(args.finish)
        return
    if args.slim:
        slim_case(args.slim)
        return
    if args.status:
        status()
        return
    p.print_help()


if __name__ == "__main__":
    main()
