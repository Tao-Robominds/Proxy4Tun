#!/usr/bin/env python3
"""Drive the fable_fresh Stage-3 campaign via the Cursor `agent` CLI.

For each unfinished panel case:
  1. emit packet
  2. create a fresh chat; run agent --print with AGENT_PROMPT to write round1_proposal.json
  3. apply round 1
  4. resume same chat for rounds 2 and 3
  5. finish (select + slim)

Usage:
  ./venv/bin/python bo/sc_general/drive_fable_fresh_campaign.py
  ./venv/bin/python bo/sc_general/drive_fable_fresh_campaign.py --only 1-5,1-1
  ./venv/bin/python bo/sc_general/drive_fable_fresh_campaign.py --status
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from bo.sc_general.run_fable_fresh_campaign import (  # noqa: E402
    ARM,
    MODEL_ID,
    STAGE3,
    apply_proposal,
    case_done,
    emit_packet,
    finish_case,
    get_agent_id,
    load_proposal,
    set_agent_id,
)
from bo.sc_general.stage3_report import PANEL  # noqa: E402

AGENT_BIN = "agent"
VENV_PY = str(_REPO / "venv" / "bin" / "python")
CAMPAIGN_PY = str(_REPO / "bo" / "sc_general" / "run_fable_fresh_campaign.py")
DRIVER_LOG = STAGE3 / "drive_fable_fresh.log"


def _log(msg: str) -> None:
    line = f"[{time.strftime('%Y-%m-%dT%H:%M:%S')}] {msg}"
    print(line, flush=True)
    DRIVER_LOG.parent.mkdir(parents=True, exist_ok=True)
    with DRIVER_LOG.open("a", encoding="utf-8") as fh:
        fh.write(line + "\n")


def _create_chat() -> str:
    out = subprocess.check_output(
        [AGENT_BIN, "create-chat"],
        text=True,
        cwd=str(_REPO),
    ).strip()
    # create-chat returns the chat id on its own line
    chat_id = out.splitlines()[-1].strip()
    if not chat_id or " " in chat_id:
        raise RuntimeError(f"unexpected create-chat output: {out!r}")
    return chat_id


def _agent_propose(subset: str, round_id: int, chat_id: str, *, resume: bool) -> Path:
    packet = STAGE3 / "packets-fable-fresh" / subset
    prompt_path = packet / "AGENT_PROMPT.md"
    out_path = packet / f"round{round_id}_proposal.json"
    img_dir = packet / "images"
    imgs = sorted(img_dir.glob("*.png"))
    overlay = packet / "sc_correspondence_overlay.png"
    attachments = [str(p) for p in imgs]
    if overlay.exists():
        attachments.append(str(overlay))

    prompt = f"""You are the Fable 5.1 reflective parameter agent for arm `{ARM}`, subset `{subset}`, round {round_id}.

HARD ISOLATION: Read ONLY:
- this prompt
- `{prompt_path}`
- `{packet / 'context.json'}`
- ontology files listed under context.ontology
- the diagnostic PNGs under `{img_dir}` and `{overlay}` if present

Do NOT read evaluation/, offline_gt.json, performance.md, mIoU/GT labels, selections*, other cases' proposals, data/refinement/, data/bo/, data/anchors/, data/baseline.

Follow AGENT_PROMPT.md exactly. Write ONE JSON object to:
`{out_path}`

Schema: observation, rule, failure_mode, rationale, overlay, full.
Stay inside bounds. If stage1_unlocked is false, omit unfolding.
When finished, print only: path written, one-line strategy, full true/false.
"""
    cmd = [
        AGENT_BIN,
        "--print",
        "--trust",
        "--force",
        "--model",
        MODEL_ID,
        "--workspace",
        str(_REPO),
        "--output-format",
        "text",
    ]
    if resume:
        cmd.extend(["--resume", chat_id])
    else:
        # Seed the fresh chat by resuming the empty chat id created for this case.
        cmd.extend(["--resume", chat_id])
    cmd.append(prompt)

    _log(f"{subset} R{round_id}: launching agent chat={chat_id} resume={resume}")
    proc = subprocess.run(cmd, cwd=str(_REPO), text=True, capture_output=True)
    (packet / f"round{round_id}_agent_stdout.txt").write_text(proc.stdout or "", encoding="utf-8")
    (packet / f"round{round_id}_agent_stderr.txt").write_text(proc.stderr or "", encoding="utf-8")
    if proc.returncode != 0:
        raise RuntimeError(
            f"agent failed for {subset} R{round_id} rc={proc.returncode}\n"
            f"stderr={proc.stderr[-2000:]}"
        )
    if not out_path.exists():
        raise RuntimeError(
            f"agent did not write {out_path}; stdout tail:\n{(proc.stdout or '')[-2000:]}"
        )
    # Validate parse
    load_proposal(out_path)
    return out_path


def run_case(subset: str) -> None:
    if case_done(subset):
        _log(f"{subset}: already done, skip")
        return
    _log(f"==== START {subset} ====")
    emit_packet(subset)

    chat_id = get_agent_id(subset)
    if not chat_id:
        chat_id = _create_chat()
        set_agent_id(subset, chat_id)
        _log(f"{subset}: new chat {chat_id}")

    root = _REPO / "data" / "refinement" / "fable_fresh" / subset
    for r in (1, 2, 3):
        rec = root / f"round{r}" / "reflection_record.json"
        if rec.exists():
            data = json.loads(rec.read_text(encoding="utf-8"))
            if data.get("status") == "ok" and data.get("proxy_scaled") is not None:
                _log(f"{subset} R{r}: already ok, skip")
                emit_packet(subset, write_overlay=False)
                continue
        # Ensure packet is current for this round
        emit_packet(subset, write_overlay=False)
        prop_path = STAGE3 / "packets-fable-fresh" / subset / f"round{r}_proposal.json"
        if not prop_path.exists():
            _agent_propose(subset, r, chat_id, resume=(r > 1))
        else:
            _log(f"{subset} R{r}: proposal already on disk")
        prop = load_proposal(prop_path)
        apply_proposal(subset, r, prop, provenance={"agent_id": chat_id})
        _log(f"{subset} R{r}: applied")

    finish_case(subset)
    _log(f"==== DONE {subset} ====")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--only", default=None, help="comma-separated subsets")
    p.add_argument("--status", action="store_true")
    p.add_argument("--skip-done", action="store_true", default=True)
    args = p.parse_args()

    panel = list(PANEL)
    if args.only:
        panel = [s.strip() for s in args.only.split(",") if s.strip()]

    if args.status:
        for s in panel:
            print(f"{s}\tdone={case_done(s)}\tagent={get_agent_id(s)}")
        return

    for subset in panel:
        try:
            run_case(subset)
        except Exception as exc:
            _log(f"FATAL {subset}: {exc}")
            raise


if __name__ == "__main__":
    main()
