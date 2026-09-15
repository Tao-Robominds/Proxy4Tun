#!/usr/bin/env python3
"""Reliable Stage-3 campaign queue (max 2 concurrent python workers)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
STAGE3 = _REPO / "data" / "sc-general" / "stage3"
LOGS = STAGE3 / "logs"
SELECTIONS = STAGE3 / "selections"
VENV_PY = str(_REPO / "venv" / "bin" / "python")
SCRIPT = str(_REPO / "bo" / "sc_general" / "run_campaign.py")

PANEL = [
    "1-3", "1-5", "1-1", "1-4", "1-2", "2-4", "2-2",
    "3-4", "3-3", "3-7", "3-8", "3-10", "3-9", "3-6",
    "4-3", "4-2", "4-1", "4-5", "5-5", "5-3", "5-2", "5-4",
]
# One at a time: stage-5 SAM OOMs the 8GB GPU when two pipelines overlap.
MAX = 1


def log(msg: str) -> None:
    print(f"[{time.strftime('%Y-%m-%dT%H:%M:%S')}] {msg}", flush=True)


def is_done(subset: str) -> bool:
    return (SELECTIONS / f"{subset}.json").exists()


def from_round(subset: str) -> int | None:
    """Next round to run, or None if all 3 successful rounds exist."""
    root = _REPO / "data" / f"{subset}-scgen-refinement"
    have = []
    for r in (1, 2, 3):
        rec = root / f"round{r}" / "reflection_record.json"
        if not rec.exists():
            continue
        try:
            data = json.loads(rec.read_text(encoding="utf-8"))
        except Exception:
            continue
        if data.get("status") == "ok" and data.get("proxy_scaled") is not None:
            have.append(r)
    if len(have) >= 3:
        return None
    # next missing successful round index
    for r in (1, 2, 3):
        if r not in have:
            return r
    return None


def list_worker_subsets() -> dict[str, int]:
    """Map subset -> pid for live run_campaign workers."""
    out: dict[str, int] = {}
    try:
        import psutil  # type: ignore
    except ImportError:
        psutil = None
    if psutil is not None:
        for proc in psutil.process_iter(["pid", "cmdline"]):
            try:
                cmd = proc.info["cmdline"] or []
            except Exception:
                continue
            if len(cmd) >= 4 and cmd[0].endswith("venv/bin/python") and "run_campaign.py" in " ".join(cmd):
                if "--subset" in cmd:
                    i = cmd.index("--subset")
                    if i + 1 < len(cmd):
                        out[cmd[i + 1]] = int(proc.info["pid"])
        return out

    # Fallback without psutil: parse /proc
    for pid_dir in Path("/proc").iterdir():
        if not pid_dir.name.isdigit():
            continue
        try:
            raw = (pid_dir / "cmdline").read_bytes()
        except Exception:
            continue
        parts = [p.decode("utf-8", "ignore") for p in raw.split(b"\0") if p]
        if not parts:
            continue
        joined = " ".join(parts)
        if "run_campaign.py" not in joined:
            continue
        if not parts[0].endswith("venv/bin/python"):
            continue
        if "--subset" in parts:
            i = parts.index("--subset")
            if i + 1 < len(parts):
                out[parts[i + 1]] = int(pid_dir.name)
    return out


def select_only(subset: str) -> None:
    log(f"select only {subset}")
    LOGS.mkdir(parents=True, exist_ok=True)
    with (LOGS / f"select_{subset}.log").open("w") as fh:
        subprocess.run(
            [VENV_PY, str(_REPO / "bo/sc_general/select_round.py"), "--subset", subset],
            cwd=_REPO,
            stdout=fh,
            stderr=subprocess.STDOUT,
            check=False,
        )


def launch(subset: str, fr: int) -> None:
    LOGS.mkdir(parents=True, exist_ok=True)
    log_path = LOGS / f"run_{subset}.log"
    log(f"launch {subset} from-round={fr} -> {log_path}")
    fh = log_path.open("a")
    fh.write(f"\n===== launch from-round={fr} at {time.strftime('%Y-%m-%dT%H:%M:%S')} =====\n")
    fh.flush()
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    subprocess.Popen(
        [VENV_PY, SCRIPT, "--subset", subset, "--from-round", str(fr)],
        cwd=_REPO,
        stdout=fh,
        stderr=subprocess.STDOUT,
        env=env,
        start_new_session=True,
    )


def main() -> None:
    STAGE3.mkdir(parents=True, exist_ok=True)
    SELECTIONS.mkdir(parents=True, exist_ok=True)
    LOGS.mkdir(parents=True, exist_ok=True)
    while True:
        workers = list_worker_subsets()
        for subset in PANEL:
            if is_done(subset):
                continue
            if subset in workers:
                continue
            fr = from_round(subset)
            if fr is None:
                select_only(subset)
                continue
            while len(list_worker_subsets()) >= MAX:
                log(f"waiting slots (running={len(list_worker_subsets())}: {sorted(list_worker_subsets())})")
                time.sleep(20)
            # re-check after wait
            if is_done(subset) or subset in list_worker_subsets():
                continue
            launch(subset, fr)
            time.sleep(2)

        workers = list_worker_subsets()
        n_done = sum(1 for s in PANEL if is_done(s))
        log(f"progress: selections={n_done}/22 running={len(workers)} {sorted(workers)}")
        if n_done == len(PANEL) and not workers:
            log("ALL DONE")
            return
        time.sleep(30)


if __name__ == "__main__":
    main()
