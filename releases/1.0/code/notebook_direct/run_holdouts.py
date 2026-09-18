#!/usr/bin/env python3
"""Run notebook-faithful baseline on holdout subsets.

Never writes under data/anchors, data/baseline, or data/bo.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))
from bo.paths import NOTEBOOK_DATA, NOTEBOOK_PKG, REPO_ROOT, VENV_PY

OUT_ROOT = NOTEBOOK_DATA
PARAMS_ROOT = NOTEBOOK_PKG / "params"
LOG_DIR = NOTEBOOK_PKG / "logs"

# The 27-subset panel matching bo-full-stage/holdout_scores.csv anchors
# (excludes BO training cases 2-1, 3-1, 5-1; includes 1-1, 3-2, 4-1).
HOLDOUTS = [
    "1-1", "1-2", "1-3", "1-4", "1-5",
    "2-2", "2-3", "2-4", "2-5",
    "3-2", "3-3", "3-4", "3-5", "3-6", "3-7", "3-8", "3-9", "3-10",
    "4-1", "4-2", "4-3", "4-4", "4-5",
    "5-2", "5-3", "5-4", "5-5",
]

# Training-anchor cases used only for optional smoke (not in HOLDOUTS).
# Gate cases: one per family recipe.
GATE_CASES = ("1-2", "3-3", "4-2")


def sibling_params(subset: str) -> tuple[str, Path]:
    fam = subset.split("-")[0]
    if fam == "1":
        return "t1&2", PARAMS_ROOT / "1-1"
    if fam == "2":
        return "t1&2", PARAMS_ROOT / "2-1"
    if fam == "3":
        return "t3", PARAMS_ROOT / "3-1-1"
    if fam == "4":
        return "t4&5", PARAMS_ROOT / "4-1"
    if fam == "5":
        return "t4&5", PARAMS_ROOT / "5-1"
    raise ValueError(f"unknown family for {subset}")


def parse_miou(run_dir: Path) -> float | None:
    perf = run_dir / "evaluation" / "performance.md"
    if not perf.exists():
        return None
    text = perf.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"Mean IoU \(mIoU\):\s*([0-9.]+)", text)
    if not m:
        return None
    try:
        return float(m.group(1))
    except ValueError:
        return None


def run_one(subset: str, force: bool = False) -> dict:
    profile, params_dir = sibling_params(subset)
    input_txt = REPO_ROOT / "data" / "subsets" / f"{subset}.txt"
    out_dir = OUT_ROOT / subset
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_path = LOG_DIR / f"{subset}.log"
    meta_path = LOG_DIR / f"{subset}.json"

    if out_dir.exists() and any(out_dir.iterdir()) and not force:
        miou = parse_miou(out_dir)
        rec = {
            "subset": subset,
            "status": "skipped_existing" if miou is not None else "incomplete",
            "miou": miou,
            "profile": profile,
            "params_dir": str(params_dir.relative_to(REPO_ROOT)),
            "out_dir": str(out_dir.relative_to(REPO_ROOT)),
            "log": str(log_path.relative_to(REPO_ROOT)),
        }
        meta_path.write_text(json.dumps(rec, indent=2) + "\n")
        return rec

    if not input_txt.exists():
        rec = {
            "subset": subset,
            "status": "missing_input",
            "miou": None,
            "error": f"missing {input_txt}",
        }
        meta_path.write_text(json.dumps(rec, indent=2) + "\n")
        return rec

    cmd = [
        str(VENV_PY),
        "-m",
        "sam4tun.pipeline",
        str(input_txt),
        str(out_dir),
        "--profile",
        profile,
        "--params-dir",
        str(params_dir),
        "--overwrite",
    ]
    t0 = time.time()
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            check=False,
        )
        log_path.write_text(
            f"$ {' '.join(cmd)}\n\n"
            f"--- stdout ---\n{proc.stdout}\n"
            f"--- stderr ---\n{proc.stderr}\n"
            f"--- exit {proc.returncode} ---\n",
            encoding="utf-8",
        )
        elapsed = time.time() - t0
        miou = parse_miou(out_dir) if proc.returncode == 0 else None
        status = "ok" if proc.returncode == 0 and miou is not None else "fail"
        if proc.returncode == 0 and miou is None:
            status = "ok_no_miou"
        rec = {
            "subset": subset,
            "status": status,
            "miou": miou,
            "exit_code": proc.returncode,
            "elapsed_s": round(elapsed, 1),
            "profile": profile,
            "params_dir": str(params_dir.relative_to(REPO_ROOT)),
            "out_dir": str(out_dir.relative_to(REPO_ROOT)),
            "log": str(log_path.relative_to(REPO_ROOT)),
            "command": " ".join(cmd),
        }
        if status != "ok":
            # Keep a short error snippet for the report.
            tail = (proc.stderr or proc.stdout or "")[-800:]
            rec["error_tail"] = tail
    except Exception as exc:  # noqa: BLE001 — record and continue campaign
        elapsed = time.time() - t0
        rec = {
            "subset": subset,
            "status": "exception",
            "miou": None,
            "elapsed_s": round(elapsed, 1),
            "error": repr(exc),
            "command": " ".join(cmd),
        }
        log_path.write_text(f"$ {' '.join(cmd)}\n\nEXCEPTION: {exc!r}\n", encoding="utf-8")

    meta_path.write_text(json.dumps(rec, indent=2) + "\n")
    return rec


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--subset", help="Run a single subset id")
    ap.add_argument("--gate", action="store_true", help="Run GATE_CASES only")
    ap.add_argument("--all", action="store_true", help="Run all 27 holdouts")
    ap.add_argument("--force", action="store_true", help="Overwrite existing outputs")
    ap.add_argument(
        "--remaining",
        action="store_true",
        help="Run holdouts that do not yet have ok status in logs/",
    )
    args = ap.parse_args()

    if args.subset:
        targets = [args.subset]
    elif args.gate:
        targets = list(GATE_CASES)
    elif args.all or args.remaining:
        targets = list(HOLDOUTS)
    else:
        ap.error("specify --subset, --gate, --all, or --remaining")

    if args.remaining:
        filtered = []
        for s in targets:
            meta = LOG_DIR / f"{s}.json"
            if meta.exists():
                try:
                    prev = json.loads(meta.read_text())
                    if prev.get("status") == "ok" and prev.get("miou") is not None:
                        continue
                except json.JSONDecodeError:
                    pass
            filtered.append(s)
        targets = filtered

    print(f"Running {len(targets)} subset(s): {targets}")
    results = []
    for s in targets:
        print(f"\n=== {s} ===", flush=True)
        rec = run_one(s, force=args.force)
        results.append(rec)
        print(
            f"  status={rec.get('status')} miou={rec.get('miou')} "
            f"elapsed={rec.get('elapsed_s')}s",
            flush=True,
        )

    summary_path = LOG_DIR / "summary.json"
    summary_path.write_text(json.dumps(results, indent=2) + "\n")
    ok = sum(1 for r in results if r.get("status") == "ok")
    print(f"\nDone: {ok}/{len(results)} ok. Summary → {summary_path}")
    return 0 if ok == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
