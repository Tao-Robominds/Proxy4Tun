#!/usr/bin/env python3
"""SC-general refinement pilot: apply an overlay under data/<subset>-scgen[-…]-refinement/.

Default: copy frozen stage-1 from the unified holdout anchor and replay stages 2-6.
With --full (or an unfolding overlay): run stages 1-6.

Also supports --context: emit a GT-blind packet for the reflective agent
(no evaluation/, no perf_* fields).

Arms:
  scgen     -> data/<subset>-scgen-refinement/             (deterministic recipes)
  fable     -> data/<subset>-scgen-fable-refinement/       (Fable-5.1 live LLM)
  gpt56     -> data/<subset>-scgen-gpt56-refinement/       (GPT-5.6 fresh per-case)
  gemini38  -> data/<subset>-scgen-gemini38-refinement/    (Gemini 3.8 fresh per-case)

Usage:
  ./venv/bin/python bo/sc_general/refine_pilot.py --subset 3-4 --arm gemini38 --context
  ./venv/bin/python bo/sc_general/refine_pilot.py --subset 3-4 --arm gemini38 --round 1 \
      --overlay-json '{"detecting": {"hough_threshold_oblique": 30}}' \
      --rationale 'raise oblique Hough to cut fallback'
"""

from __future__ import annotations

import argparse
import json
import math
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from bo.paths import REPO_ROOT, UNIFIED_DATA  # noqa: E402
from bo.sc_general.overlay import render_overlay  # noqa: E402
from bo.sc_general.score_scaled import (  # noqa: E402
    ACCEPT_THR,
    REJECT_THR,
    extract_sc_features,
    score_run,
)
from bo.unified.intrinsics import extract_intrinsics, write_intrinsics  # noqa: E402
from bo.unified.param_io import (  # noqa: E402
    load_anchor_params,
    load_family_params,
    materialize_run_params,
)
from bo.unified.pipeline import copy_checkpoint, parse_performance, run_stages  # noqa: E402
from bo.unified.spaces import (  # noqa: E402
    FAMILY_MODE,
    FAMILY_SPACES,
    holdout_case_config,
)

STAGE3_ROOT = REPO_ROOT / "data" / "sc-general" / "stage3"
ONTOLOGY = REPO_ROOT / "agents" / "ontology"
VALID_ARMS = ("scgen", "fable", "fable_fresh", "gpt56", "gemini38", "random")
ARM_PROPOSER = {
    "scgen": "deterministic (run_campaign.propose)",
    "fable": "fable-5.1 (cursor agent, live)",
    "fable_fresh": "Fable-5.1 (fresh per-case agent)",
    "gpt56": "GPT-5.6 (fresh per-case agent)",
    "gemini38": "Gemini-3.8 (fresh per-case agent)",
    "random": "random-uniform-v1 (k-matched bounded overlay)",
}
# Legacy flat layout under data/<subset>-<suffix>/; preferred layout is
# data/refinement/<arm>/<subset>/ (see out_root_for).
ARM_OUT_SUFFIX = {
    "scgen": "scgen-refinement",
    "fable": "scgen-fable-refinement",
    "fable_fresh": "scgen-fable-fresh-refinement",
    "gpt56": "scgen-gpt56-refinement",
    "gemini38": "scgen-gemini38-refinement",
    "random": "scgen-random-refinement",
}
ARM_PACKET_DIR = {
    "scgen": "packets",
    "fable": "packets-fable",
    "fable_fresh": "packets-fable-fresh",
    "gpt56": "packets-gpt56",
    "gemini38": "packets-gemini38",
    "random": "packets-random",
}
PNG_NAMES = [
    "depth_map_viridis.png",
    "detected_lines.png",
    "initial_prompt_points.png",
    "segmentation_results.png",
]


def out_root_for(subset: str, arm: str = "scgen") -> Path:
    if arm not in VALID_ARMS:
        raise ValueError(f"unknown arm {arm!r}; expected one of {VALID_ARMS}")
    # Preferred consolidated layout (final package).
    preferred = REPO_ROOT / "data" / "refinement" / arm / subset
    if preferred.exists():
        return preferred
    # Legacy flat layout used by earlier campaigns.
    legacy = REPO_ROOT / "data" / f"{subset}-{ARM_OUT_SUFFIX[arm]}"
    if legacy.exists():
        return legacy
    # New runs land in the preferred layout.
    return preferred


def packet_dir_for(subset: str, arm: str = "scgen") -> Path:
    if arm not in VALID_ARMS:
        raise ValueError(f"unknown arm {arm!r}; expected one of {VALID_ARMS}")
    return STAGE3_ROOT / ARM_PACKET_DIR[arm] / subset


def anchor_paths(subset: str) -> tuple[Path, Path]:
    """Return (anchor_run_dir, anchor_params_dir). Never writes into anchors/."""
    from bo.sc_general.score_scaled import anchor_run_dir

    run = anchor_run_dir(subset)
    # Prefer materialized family-proxy params when present.
    fam_params = UNIFIED_DATA / f"{subset}-family-proxy" / "params" / f"{subset}-anchor"
    if fam_params.is_dir() and (fam_params / "parameters_detecting.json").exists():
        return run, fam_params
    # Research-anchor / fallback: use find_params_dir (read-only).
    from bo.sc_general.replay import find_params_dir

    return run, find_params_dir(run)


def _bounds_for_family(family: str) -> list[dict[str, Any]]:
    dims = FAMILY_SPACES[family]()
    rows = []
    for d in dims:
        rows.append(
            {
                "name": f"{d.stage}.{d.name}",
                "stage": d.stage,
                "key": d.key,
                "kind": d.kind,
                "low": d.low,
                "high": d.high,
                "special": d.special,
            }
        )
    return rows


def _slim_score(scored: dict[str, Any]) -> dict[str, Any]:
    return {
        "proxy_raw": round(float(scored["proxy_raw"]), 6),
        "proxy_scaled": round(float(scored["proxy_scaled"]), 6),
        "band": scored["band"],
        "features": {k: round(float(v), 6) for k, v in scored["features"].items()},
        "recentre_residual_max_cm": scored.get("recentre_residual_max_cm"),
        "orient_axis_corr": scored.get("orient_axis_corr"),
        "ring_count": scored.get("ring_count"),
        "ring_count_error": scored["features"].get("ring_count_error"),
        "labelmap_source": scored.get("labelmap_source"),
        "run_dir": scored.get("run_dir"),
    }


def build_context(
    subset: str, *, arm: str = "scgen", write_overlay: bool = True
) -> dict[str, Any]:
    if arm not in VALID_ARMS:
        raise ValueError(f"unknown arm {arm!r}; expected one of {VALID_ARMS}")
    cfg = holdout_case_config(subset)
    family = cfg["family"]
    mode = FAMILY_MODE[family]
    anchor_run, _ = anchor_paths(subset)
    out_root = out_root_for(subset, arm=arm)
    STAGE3_ROOT.mkdir(parents=True, exist_ok=True)

    scored = score_run(anchor_run, subset, reveal_gt=False, write_shadow=True)
    residual = scored.get("recentre_residual_max_cm")
    stage1_unlocked = (
        residual is not None
        and math.isfinite(float(residual))
        and float(residual) > 10.0
    )

    history = []
    if out_root.exists():
        for rd in sorted(out_root.glob("round*")):
            rec_path = rd / "reflection_record.json"
            if not rec_path.exists():
                continue
            rec = json.loads(rec_path.read_text(encoding="utf-8"))
            history.append(
                {
                    "round": rec.get("round"),
                    "status": rec.get("status"),
                    "overlay": rec.get("overlay"),
                    "proxy_scaled": rec.get("proxy_scaled"),
                    "band": rec.get("band"),
                    "features": rec.get("features"),
                    "recentre_residual_max_cm": rec.get("recentre_residual_max_cm"),
                    "full_pipeline": rec.get("full_pipeline"),
                    "rationale": rec.get("rationale"),
                    "proposer": rec.get("proposer"),
                }
            )

    images = {}
    for name in PNG_NAMES:
        p = anchor_run / name
        if p.exists():
            images[name] = str(p)

    packet_dir = packet_dir_for(subset, arm=arm)
    packet_dir.mkdir(parents=True, exist_ok=True)
    if write_overlay:
        extracted = extract_sc_features(anchor_run, subset, write_shadow=True)
        overlay_png = packet_dir / "sc_correspondence_overlay.png"
        render_overlay(
            anchor_run,
            extracted["ls"],
            extracted["lm"],
            overlay_png,
            delta=15,
            title=f"{subset} anchor SC correspondence @15",
        )
        images["sc_correspondence_overlay.png"] = str(overlay_png)

    packet = {
        "subset": subset,
        "arm": arm,
        "proposer": ARM_PROPOSER[arm],
        "family": family,
        "lining_mode": mode,
        "stage1_unlocked": stage1_unlocked,
        "residual_gate_cm": 10.0,
        "bands": {
            "reject": f"<{REJECT_THR}",
            "refine": f"[{REJECT_THR}, {ACCEPT_THR})",
            "accept": f">={ACCEPT_THR}",
        },
        "anchor": _slim_score(scored),
        "intrinsics_gt_blind": {
            k: scored["intrinsics_gt_blind"].get(k)
            for k in (
                "orient_axis_corr",
                "orient_invariant_ok",
                "recentre_residual_max_cm",
                "denoise_retained_ratio",
                "depth_nan_ratio",
                "depth_outlier_ratio",
                "det_real_detection_ratio",
                "det_fallback_ratio",
                "det_n_points",
                "sam_fill_rate",
                "sam_ring_completeness",
                "sam_segment_size_cv",
                "sam_ontology_divergence",
            )
            if k in scored["intrinsics_gt_blind"]
        },
        "history": history,
        "images": images,
        "ontology": {
            "experiences": str(ONTOLOGY / "experiences.md"),
            "sam4tun_ontology": str(ONTOLOGY / "sam4tun_ontology.yaml"),
            "tunnel_priors": str(ONTOLOGY / "tunnel_priors.yaml"),
        },
        "parameter_bounds": _bounds_for_family(family),
        "instructions": [
            "Propose ONE coordinated multi-stage overlay within parameter_bounds.",
            "Use observation -> ontology rule -> failure_mode -> overlay.",
            "Do NOT read evaluation/, offline_gt.json, performance.md, perf_*, mIoU, "
            "or any ground-truth labels / GT-bearing CSVs.",
            "Do NOT read existing Fable/deterministic selections, campaign logs, "
            "or other arms' refinement trees.",
            "Use the SC-general proxy (proxy_scaled / band / lean features) as the between-round signal.",
            "If stage1_unlocked is false, do not touch unfolding keys.",
            "If stage1_unlocked is true and residual remains high, you may include unfolding (e.g. random_seed) and the pilot will auto --full.",
            "Return JSON with keys: observation, failure_mode, rationale, overlay.",
        ],
        "created_at": datetime.now().isoformat(),
    }

    pkt_path = packet_dir / "context.json"
    pkt_path.write_text(json.dumps(packet, indent=2) + "\n", encoding="utf-8")
    packet["context_path"] = str(pkt_path)
    return packet


def run_round(
    subset: str,
    round_id: int,
    overlay: dict[str, dict[str, Any]],
    *,
    arm: str = "scgen",
    full: bool = False,
    rationale: str | None = None,
    provenance: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if arm not in VALID_ARMS:
        raise ValueError(f"unknown arm {arm!r}; expected one of {VALID_ARMS}")
    cfg = holdout_case_config(subset)
    input_txt = REPO_ROOT / cfg["input_txt"]
    anchor_run, anchor_params = anchor_paths(subset)
    if not full and not (anchor_run / "state.pkl").exists():
        raise FileNotFoundError(f"Missing anchor stage-1 checkpoint at {anchor_run}")

    if overlay.get("unfolding") and not full:
        full = True

    out_root = out_root_for(subset, arm=arm)
    run_id = f"round{round_id}"
    run_dir = out_root / run_id
    params_root = out_root / "params"
    logs_root = out_root / "logs"
    for d in (out_root, params_root, logs_root):
        d.mkdir(parents=True, exist_ok=True)

    base = load_anchor_params(anchor_params)
    family_params = load_family_params(anchor_params)
    params_dir = materialize_run_params(
        params_root / run_id, base, overlay, family_params=family_params
    )

    if run_dir.exists():
        shutil.rmtree(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)

    start_stage = 1 if full else 2
    if not full:
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
            out_root=out_root,
            log_path=log_path,
            start_stage=start_stage,
            end_stage=6,
        )
    except RuntimeError as exc:
        status = "failed"
        print(f"FAILED: {exc}", file=sys.stderr)
        if log_path.exists():
            log_text = log_path.read_text(encoding="utf-8")

    # Write GT-blind intrinsics (strip perf before write for agent safety)
    metrics: dict[str, Any] = {}
    try:
        metrics = extract_intrinsics(
            run_dir,
            params_dir=params_dir,
            log_text=log_text,
            expected_rings=int(cfg["expected_rings"]),
        )
        write_intrinsics(run_dir, metrics)
    except Exception as exc:  # noqa: BLE001
        print(f"WARN: intrinsics failed: {exc}", file=sys.stderr)

    perf = parse_performance(run_dir / "evaluation" / "performance.md")
    offline = {f"perf_{k}": v for k, v in perf.items()}
    (run_dir / "offline_gt.json").write_text(
        json.dumps(offline, indent=2) + "\n", encoding="utf-8"
    )

    scored: dict[str, Any] | None = None
    if status == "ok" and (run_dir / "only_label.csv").exists():
        try:
            scored = score_run(
                run_dir,
                subset,
                reveal_gt=False,
                write_shadow=True,
                log_text=log_text,
            )
        except Exception as exc:  # noqa: BLE001
            status = "score_failed"
            print(f"WARN: score_run failed: {exc}", file=sys.stderr)

    rec = {
        "subset": subset,
        "arm": arm,
        "proposer": ARM_PROPOSER[arm],
        "rationale": rationale,
        "round": round_id,
        "status": status,
        "full_pipeline": full,
        "start_stage": start_stage,
        "overlay": overlay,
        "proxy_raw": None if scored is None else scored["proxy_raw"],
        "proxy_scaled": None if scored is None else scored["proxy_scaled"],
        "band": None if scored is None else scored["band"],
        "features": None if scored is None else scored["features"],
        "recentre_residual_max_cm": None if scored is None else scored.get("recentre_residual_max_cm"),
        "orient_axis_corr": None if scored is None else scored.get("orient_axis_corr"),
        "ring_count": None if scored is None else scored.get("ring_count"),
        "labelmap_source": None if scored is None else scored.get("labelmap_source"),
        "elapsed_s": elapsed,
        "output_dir": str(run_dir),
        "log_path": str(log_path),
        "finished_at": datetime.now().isoformat(),
    }
    if provenance:
        rec["provenance"] = provenance
    (run_dir / "reflection_record.json").write_text(
        json.dumps(rec, indent=2) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                k: rec[k]
                for k in (
                    "subset",
                    "arm",
                    "proposer",
                    "round",
                    "status",
                    "full_pipeline",
                    "proxy_scaled",
                    "band",
                    "features",
                    "recentre_residual_max_cm",
                    "elapsed_s",
                    "output_dir",
                )
            },
            indent=2,
        )
    )
    return rec


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--subset", required=True)
    p.add_argument("--arm", default="scgen", choices=VALID_ARMS)
    p.add_argument("--round", type=int, default=None)
    p.add_argument("--overlay-json", default=None)
    p.add_argument("--rationale", default=None, help="Proposer rationale (logged in record)")
    p.add_argument("--full", action="store_true")
    p.add_argument("--context", action="store_true", help="Emit GT-blind context packet")
    p.add_argument("--no-overlay-png", action="store_true")
    args = p.parse_args()

    if args.context:
        packet = build_context(
            args.subset, arm=args.arm, write_overlay=not args.no_overlay_png
        )
        print(json.dumps(packet, indent=2))
        return

    if args.round is None or args.overlay_json is None:
        p.error("--round and --overlay-json required unless --context")
    overlay = json.loads(args.overlay_json)
    run_round(
        args.subset,
        args.round,
        overlay,
        arm=args.arm,
        full=args.full,
        rationale=args.rationale,
    )


if __name__ == "__main__":
    main()
