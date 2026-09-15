#!/usr/bin/env python3
"""Execute one GPT-5.6 overlay round into data/<subset>-gpt56-refinement/.

Does not call any LLM. Scores with the frozen scaled pooled proxy and writes
GT-blind agent_feedback.json plus offline evaluation.json (mIoU held out).
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from bo.unified.intrinsics import extract_intrinsics, write_intrinsics  # noqa: E402
from bo.unified.param_io import load_anchor_params, load_family_params, materialize_run_params  # noqa: E402
from bo.unified.pipeline import copy_checkpoint, parse_performance, run_stages  # noqa: E402
from bo.unified.spaces import holdout_case_config  # noqa: E402
from bo.full_stage.score_run import _anchor_run_dir  # noqa: E402
from bo.proxy_scale.score_scaled import score_scaled  # noqa: E402


from constants import AGENT_IMAGES, GT_KEYS, LOGS_DIR, out_root  # noqa: E402
from validate_overlay import validate_overlay  # noqa: E402


def _sanitize(d: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in d.items() if k not in GT_KEYS and not k.startswith("perf_")}


def run_round(
    subset: str,
    round_id: int,
    overlay: dict[str, Any],
    *,
    proposal: dict[str, Any] | None = None,
) -> dict[str, Any]:
    ok, errors, overlay = validate_overlay(subset, overlay)
    if not ok:
        raise ValueError(f"invalid overlay: {errors}")

    cfg = holdout_case_config(subset)
    input_txt = REPO_ROOT / cfg["input_txt"]
    anchor_run = Path(_anchor_run_dir(subset))
    # Anchor params live beside the family-proxy run tree when present.
    anchor_params = anchor_run.parent.parent / "params" / f"{subset}-anchor"
    if not anchor_params.is_dir():
        # Fallback: params_dir from case config (unified anchors).
        anchor_params = REPO_ROOT / cfg["params_dir"]

    full = bool(overlay.get("unfolding"))
    root = out_root(subset)
    run_id = f"round{round_id}"
    run_dir = root / run_id
    params_root = root / "params"
    logs_root = root / "logs"
    for d in (root, params_root, logs_root, LOGS_DIR):
        d.mkdir(parents=True, exist_ok=True)

    base = load_anchor_params(anchor_params)
    family_params = load_family_params(anchor_params)
    params_dir = materialize_run_params(
        params_root / run_id, base, overlay, family_params=family_params
    )

    if run_dir.exists():
        shutil.rmtree(run_dir)
    run_dir.mkdir(parents=True)

    start_stage = 1 if full else 2
    if not full:
        if not (anchor_run / "state.pkl").exists():
            raise FileNotFoundError(f"missing anchor checkpoint {anchor_run}")
        copy_checkpoint(anchor_run, run_dir)

    log_path = logs_root / f"{run_id}.log"
    status = "ok"
    log_text = ""
    elapsed = 0.0
    try:
        log_text, elapsed = run_stages(
            run_id=run_id,
            params_dir=params_dir,
            input_txt=input_txt,
            out_root=root,
            log_path=log_path,
            start_stage=start_stage,
            end_stage=6,
        )
    except RuntimeError as exc:
        status = "failed"
        print(f"FAILED: {exc}", file=sys.stderr)
        if log_path.exists():
            log_text = log_path.read_text(encoding="utf-8")

    perf = parse_performance(run_dir / "evaluation" / "performance.md")
    metrics = extract_intrinsics(
        run_dir,
        params_dir=params_dir,
        log_text=log_text,
        expected_rings=int(cfg["expected_rings"]),
    )
    metrics.update({f"perf_{k}": v for k, v in perf.items()})
    write_intrinsics(run_dir, metrics)

    scored = score_scaled(run_dir, subset)
    # Own residual (full 1-6 re-measures it)
    residual = metrics.get("recentre_residual_max_cm")
    if residual is not None:
        scored["recentre_residual_max_cm"] = float(residual)

    # Offline GT (never shown to the agent during the loop)
    offline = {
        "subset": subset,
        "round": round_id,
        "mIoU": perf.get("mIoU"),
        "perf": perf,
        "status": status,
    }
    (run_dir / "evaluation_offline.json").write_text(
        json.dumps(offline, indent=2) + "\n", encoding="utf-8"
    )

    # Anchor proxy for delta
    anchor_scored = score_scaled(anchor_run, subset)

    feedback = {
        "subset": subset,
        "round": round_id,
        "status": status,
        "full_pipeline": full,
        "overlay": overlay,
        "proxy_scaled": scored["proxy_scaled"],
        "proxy_raw": scored["proxy_raw"],
        "band": scored["band"],
        "delta_proxy_scaled": round(
            scored["proxy_scaled"] - anchor_scored["proxy_scaled"], 4
        ),
        "recentre_residual_max_cm": scored.get("recentre_residual_max_cm"),
        "intrinsics_gt_blind": _sanitize(metrics),
        "lean_features": scored.get("features"),
        "images": [n for n in AGENT_IMAGES if (run_dir / n).exists()],
        "elapsed_s": elapsed,
        "run_dir": str(run_dir),
        "finished_at": datetime.now().isoformat(),
    }
    # Explicitly never include mIoU in feedback
    assert "mIoU" not in feedback
    (run_dir / "agent_feedback.json").write_text(
        json.dumps(feedback, indent=2) + "\n", encoding="utf-8"
    )

    record = {
        "proposal": proposal,
        "overlay": overlay,
        "feedback_path": str(run_dir / "agent_feedback.json"),
        "offline_path": str(run_dir / "evaluation_offline.json"),
        "status": status,
        "proxy_scaled": scored["proxy_scaled"],
        "mIoU_offline": perf.get("mIoU"),
        "elapsed_s": elapsed,
    }
    (run_dir / "round_record.json").write_text(
        json.dumps(record, indent=2) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "subset": subset,
                "round": round_id,
                "status": status,
                "full_pipeline": full,
                "proxy_scaled": scored["proxy_scaled"],
                "delta_proxy_scaled": feedback["delta_proxy_scaled"],
                "mIoU_offline": perf.get("mIoU"),
                "elapsed_s": elapsed,
                "run_dir": str(run_dir),
            },
            indent=2,
        )
    )
    return record


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--subset", required=True)
    p.add_argument("--round", type=int, required=True)
    p.add_argument("--overlay-json", default=None)
    p.add_argument("--proposal-json", default=None, help="Path to full proposal JSON")
    args = p.parse_args()

    proposal = None
    if args.proposal_json:
        proposal = json.loads(Path(args.proposal_json).read_text(encoding="utf-8"))
        overlay = proposal["overlay"]
    elif args.overlay_json:
        overlay = json.loads(args.overlay_json)
    else:
        p.error("provide --overlay-json or --proposal-json")
    run_round(args.subset, args.round, overlay, proposal=proposal)


if __name__ == "__main__":
    main()
