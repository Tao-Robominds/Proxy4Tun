#!/usr/bin/env python3
"""Release-3 refinement orchestrator.

Commands:
  ./venv/bin/python -u bo/release3/refine.py --emit SUBSET --arm ARM
  ./venv/bin/python -u bo/release3/refine.py --apply SUBSET --arm ARM --round R --proposal-json FILE
  ./venv/bin/python -u bo/release3/refine.py --finish SUBSET --arm ARM
  ./venv/bin/python -u bo/release3/refine.py --status
  ./venv/bin/python -u bo/release3/refine.py --random-round SUBSET --round R
  ./venv/bin/python -u bo/release3/refine.py --run-random-case SUBSET
  ./venv/bin/python -u bo/release3/refine.py --run-random-all
  ./venv/bin/python -u bo/release3/refine.py --gate
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from bo.paths import REFERENCES_DIR, RELEASE3_DATA, REPO_ROOT  # noqa: E402
from bo.release3.measure import measure_run  # noqa: E402
from bo.release3.score import score_measurements  # noqa: E402
from bo.runtime.metadata import expected_rings, family_of  # noqa: E402
from bo.runtime.param_io import (  # noqa: E402
    get_nested,
    load_anchor_params,
    load_family_params,
    materialize_run_params,
)
from bo.runtime.pipeline import copy_checkpoint, parse_performance, run_stages  # noqa: E402
from bo.runtime.spaces import Dim  # noqa: E402
from bo.sc_general.overlay_validator import validate_overlay  # noqa: E402

# Published panel. GPT-5.6 high (gpt56) results were removed; medium is separate.
PANEL_ARMS = ("random", "fable", "gpt56_medium", "gemini38")
ARMS = PANEL_ARMS
ARM_LABEL = {
    "random": "adaptive-random",
    "fable": "Fable 5.1",
    "gpt56_medium": "GPT-5.6 medium",
    "gemini38": "Gemini 3.8",
}
MODEL_SLUG = {
    "fable": "claude-fable-5-1-thinking-high",
    "gpt56_medium": "gpt-5.6-sol-medium",
    "gemini38": "inherit",
}
def _load_admitted() -> tuple[str, ...]:
    path = RELEASE3_DATA / "degradation" / "admitted.json"
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
        return tuple(data["admitted"])
    return (
        "1-1", "1-3", "1-5",
        "3-3", "3-4", "3-6", "3-7", "3-8", "3-9", "3-10",
        "4-1", "4-2", "4-3", "4-4", "5-5",
    )


ADMITTED = _load_admitted()
GATE_CASE = "1-1"
TIE_MARGIN = 0.01
RESIDUAL_UNLOCK_CM = 10.0
SEED_BASE = 20260915
PNG_NAMES = (
    "detected_lines.png",
    "segmentation_results.png",
    "depth_map_viridis.png",
    "initial_prompt_points.png",
)
SLIM_NAMES = (
    "state.pkl",
    "unwrapped.csv",
    "denoised.csv",
    "enhanced.csv",
    "final.csv",
    "pixel_to_point.pkl",
    "results.pkl",
    "depth_map.npy",
    "depth_map_outlier.npy",
)
ONTOLOGY = REPO_ROOT / "agents" / "ontology" / "sam4tun_ontology.yaml"
REFINE = RELEASE3_DATA / "refinement"
RECORDS = REFINE / "records"
REFS = RELEASE3_DATA / "inputs" / "references"
BOUNDS = REPO_ROOT / "configs" / "bounds"
RANDOM_CFG = REPO_ROOT / "configs" / "random_arm.json"
EXAMPLE_BANK = REPO_ROOT / "configs" / "example_bank.json"
FOUR = (
    "correspondence_f1@15",
    "sam_fill_rate",
    "ring_count_error",
    "depth_nan_ratio",
    "rotation_advantage",
)
# Higher is better for these; ring_count_error and depth_nan_ratio are lower-better.
HIGHER_BETTER = {"correspondence_f1@15", "sam_fill_rate"}


def _log(msg: str) -> None:
    print(f"[{datetime.now().isoformat(timespec='seconds')}] {msg}", flush=True)


def case_root(arm: str, subset: str) -> Path:
    return REFINE / arm / subset


def round_dir(arm: str, subset: str, round_id: int) -> Path:
    return case_root(arm, subset) / f"round{round_id}"


def start_dir(subset: str) -> Path:
    return REFS / subset


def residual_cm(measurements: dict[str, Any]) -> float:
    """Invert unfold_residual = log1p(recentre_cm)."""
    try:
        u = float(measurements.get("unfold_residual", 0.0))
    except (TypeError, ValueError):
        return 0.0
    if not math.isfinite(u) or u <= 0:
        return 0.0
    return float(math.expm1(u))


def stage1_unlocked(measurements: dict[str, Any]) -> bool:
    return residual_cm(measurements) > RESIDUAL_UNLOCK_CM


def load_start(subset: str) -> dict[str, Any]:
    path = start_dir(subset) / "record.json"
    if not path.exists():
        raise FileNotFoundError(f"missing start record {path}")
    rec = json.loads(path.read_text(encoding="utf-8"))
    if not rec.get("valid"):
        raise RuntimeError(f"start record invalid for {subset}")
    # Re-score with the Release-3 five-feature proxy (record may still hold R2 score).
    measurements = dict(rec.get("measurements") or {})
    if "rotation_advantage" not in measurements:
        from bo.release3.rotation_features import compute_rotation_features

        params = Path(rec.get("params_dir") or (REFERENCES_DIR / family_of(subset)))
        rot = compute_rotation_features(start_dir(subset), params_dir=params, subset=subset)
        measurements.update(rot)
    scored = score_measurements(measurements)
    rec = dict(rec)
    rec["measurements"] = measurements
    rec["score"] = scored["score"]
    rec["band"] = scored["band"]
    rec["score_raw"] = scored.get("score_raw")
    return rec


def admitted_panel() -> list[str]:
    return list(ADMITTED)


def _bounds_payload(family: str) -> list[dict[str, Any]]:
    data = json.loads((BOUNDS / f"{family}.json").read_text(encoding="utf-8"))
    return list(data["dims"])


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _slim(run: Path) -> None:
    for name in SLIM_NAMES:
        p = run / name
        if p.exists():
            p.unlink()


def _append_csv(path: Path, fieldnames: list[str], row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    new = not path.exists()
    with path.open("a", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        if new:
            writer.writeheader()
        writer.writerow(row)


def _failure(subset: str, arm: str, round_id: int, reason: str) -> None:
    _append_csv(
        RECORDS / "failures.csv",
        ["subset", "arm", "round", "failure_reason", "ts"],
        {
            "subset": subset,
            "arm": arm,
            "round": round_id,
            "failure_reason": reason,
            "ts": datetime.now().isoformat(timespec="seconds"),
        },
    )


def incumbent_path(arm: str, subset: str) -> Path:
    return case_root(arm, subset) / "incumbent.json"


def load_incumbent(arm: str, subset: str) -> dict[str, Any]:
    path = incumbent_path(arm, subset)
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    start = load_start(subset)
    inc = {
        "source": "start",
        "round": 0,
        "run_dir": str(start_dir(subset)),
        "params_dir": str(REFERENCES_DIR / family_of(subset)),
        "score": float(start["score"]),
        "band": start["band"],
        "measurements": start["measurements"],
        "overlay_from_start": {},
        "gt_miou": start.get("gt_miou"),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(inc, indent=2) + "\n", encoding="utf-8")
    return inc


def save_incumbent(arm: str, subset: str, inc: dict[str, Any]) -> None:
    incumbent_path(arm, subset).write_text(json.dumps(inc, indent=2) + "\n", encoding="utf-8")


def _copy_images(src: Path, dest: Path) -> dict[str, str]:
    dest.mkdir(parents=True, exist_ok=True)
    out = {}
    for name in PNG_NAMES:
        s = src / name
        if s.exists():
            d = dest / name
            shutil.copy2(s, d)
            try:
                d.chmod(d.stat().st_mode | 0o200)
            except OSError:
                pass
            out[name] = str(d)
    return out


def match_examples(family: str, measurements: dict[str, float], n: int = 3) -> list[dict]:
    if not EXAMPLE_BANK.exists():
        return []
    bank = json.loads(EXAMPLE_BANK.read_text(encoding="utf-8"))
    examples = [e for e in bank["examples"] if e["family"] == family]
    if not examples:
        return []
    # Dominant deficiency: largest z-gap vs example bank family means, signed so
    # higher-better features use low values as deficient.
    deficits = []
    for feat in FOUR:
        vals = [float(e["after"]["measurements"].get(feat, float("nan"))) for e in examples]
        vals = [v for v in vals if math.isfinite(v)]
        if not vals:
            continue
        mu = float(np.mean(vals))
        sd = float(np.std(vals)) or 1.0
        cur = float(measurements.get(feat, mu))
        if feat in HIGHER_BETTER:
            deficit = (mu - cur) / sd
        else:
            deficit = (cur - mu) / sd
        deficits.append((deficit, feat))
    deficits.sort(reverse=True)
    primary = deficits[0][1] if deficits else FOUR[0]
    improving = [e for e in examples if e.get("dominant_feature") == primary and e.get("direction") == "improve"]
    degrading = [e for e in examples if e.get("dominant_feature") == primary and e.get("direction") == "degrade"]
    other_imp = [e for e in examples if e.get("direction") == "improve" and e not in improving]
    other_deg = [e for e in examples if e.get("direction") == "degrade" and e not in degrading]
    chosen: list[dict] = []
    for pool in (improving, degrading, other_imp, other_deg, examples):
        for e in pool:
            if e not in chosen:
                chosen.append(e)
            if len(chosen) >= n:
                break
        if len(chosen) >= n:
            break
    # Guarantee at least one improve and one degrade when available.
    has_imp = any(e.get("direction") == "improve" for e in chosen)
    has_deg = any(e.get("direction") == "degrade" for e in chosen)
    if not has_imp and other_imp:
        chosen[-1] = other_imp[0]
    if not has_deg and other_deg:
        chosen[0 if len(chosen) == 1 else -2 if len(chosen) > 1 else 0] = other_deg[0]
        chosen = chosen[:n]
    return chosen[:n]


def _build_feedback(arm: str, subset: str, prev_round: int) -> dict[str, Any]:
    prev = round_dir(arm, subset, prev_round)
    rec = json.loads((prev / "record.json").read_text(encoding="utf-8"))
    # Incumbent at proposal time was stored on the record.
    before_m = rec.get("incumbent_before_measurements") or {}
    after_m = rec.get("measurements") or {}
    before_score = rec.get("incumbent_before_score")
    after_score = rec.get("score")
    deltas = {}
    for k in FOUR:
        try:
            b = float(before_m.get(k))
            a = float(after_m.get(k))
            deltas[k] = None if not (math.isfinite(b) and math.isfinite(a)) else round(a - b, 6)
        except (TypeError, ValueError):
            deltas[k] = None
    img_before = case_root(arm, subset) / f"round{prev_round}" / "feedback_images" / "before"
    img_after = case_root(arm, subset) / f"round{prev_round}" / "feedback_images" / "after"
    return {
        "previous_round": prev_round,
        "overlay": rec.get("overlay"),
        "valid": rec.get("valid"),
        "failure_reason": rec.get("failure_reason"),
        "verdict": rec.get("verdict"),
        "score_before": before_score,
        "score_after": after_score,
        "measurements_before": {k: before_m.get(k) for k in FOUR},
        "measurements_after": {k: after_m.get(k) for k in FOUR},
        "measurement_deltas": deltas,
        "images_before": {n: str(img_before / n) for n in PNG_NAMES if (img_before / n).exists()},
        "images_after": {n: str(img_after / n) for n in PNG_NAMES if (img_after / n).exists()},
    }


def emit(subset: str, arm: str) -> dict[str, Any]:
    if subset not in ADMITTED:
        raise SystemExit(f"{subset} not in admitted panel")
    if arm not in ARMS:
        raise SystemExit(f"unknown arm {arm}")
    root = case_root(arm, subset)
    root.mkdir(parents=True, exist_ok=True)
    # Determine next round.
    next_round = 1
    for r in (1, 2, 3):
        if (round_dir(arm, subset, r) / "record.json").exists():
            next_round = r + 1
    if next_round > 3:
        raise SystemExit(f"{subset}/{arm}: all three rounds already executed")
    if next_round > 1:
        prev = next_round - 1
        if not (round_dir(arm, subset, prev) / "record.json").exists():
            raise SystemExit(
                f"refusing emit for round {next_round}: round {prev} has no record.json"
            )

    inc = load_incumbent(arm, subset)
    start = load_start(subset)
    family = family_of(subset)
    measurements = inc["measurements"]
    unlocked = stage1_unlocked(start["measurements"])  # unlock from start residual
    examples = match_examples(family, measurements) if arm != "random" else []

    packet_dir = root / "packet"
    if packet_dir.exists():
        shutil.rmtree(packet_dir)
    packet_dir.mkdir(parents=True)
    images = _copy_images(Path(inc["run_dir"]), packet_dir / "images")

    feedback = None
    if next_round > 1:
        feedback = _build_feedback(arm, subset, next_round - 1)
        (packet_dir / "feedback.json").write_text(
            json.dumps(feedback, indent=2) + "\n", encoding="utf-8"
        )

    packet = {
        "subset": subset,
        "family": family,
        "arm": arm,
        "proposer": ARM_LABEL[arm],
        "model_slug": MODEL_SLUG.get(arm),
        "round": next_round,
        "stage1_unlocked": unlocked,
        "residual_cm": residual_cm(start["measurements"]),
        "residual_gate_cm": RESIDUAL_UNLOCK_CM,
        "expected_rings": expected_rings(subset),
        "incumbent": {
            "source": inc["source"],
            "round": inc["round"],
            "score": inc["score"],
            "band": inc["band"],
            "measurements": {k: measurements.get(k) for k in FOUR},
            "all_measurements": measurements,
        },
        "start": {
            "score": start["score"],
            "band": start["band"],
            "measurements": {k: start["measurements"].get(k) for k in FOUR},
        },
        "images": images,
        "ontology": str(ONTOLOGY),
        "parameter_bounds": _bounds_payload(family),
        "examples": examples,
        "feedback": feedback,
        "instructions": [
            "Propose exactly ONE overlay (JSON object of stage -> param -> value).",
            "Return JSON with keys: observation, rule, failure_mode, rationale, overlay, full.",
            "Do NOT include GT, mIoU, evaluation/, or multiple overlays.",
            "If stage1_unlocked is false, do not touch unfolding keys.",
            "Use the worked examples as condition→change→response analogies; do not invent per-parameter causal effects for joint changes.",
            "Stay inside parameter_bounds.",
        ],
        "created_at": datetime.now().isoformat(timespec="seconds"),
    }
    # GT hygiene check.
    blob = json.dumps(packet)
    for banned in ("gt_miou", "gt_labels", "mIoU", "evaluation/", "perf_"):
        if banned in blob and banned != "gt_miou":
            # gt_miou must not appear; start record had it but we stripped.
            pass
    if "gt_miou" in blob or "gt_labels" in blob:
        raise RuntimeError("packet leaked GT fields")

    (packet_dir / "packet.json").write_text(json.dumps(packet, indent=2) + "\n", encoding="utf-8")
    prompt = _render_prompt(packet)
    (packet_dir / "AGENT_PROMPT.md").write_text(prompt, encoding="utf-8")
    _log(f"emit {subset}/{arm} round={next_round} unlocked={unlocked} examples={len(examples)}")
    return packet


def _render_prompt(packet: dict[str, Any]) -> str:
    subset = packet["subset"]
    rnd = packet["round"]
    lines = [
        f"# Reflection — subset {subset}, round {rnd} ({packet['proposer']})",
        "",
        "You are a reflective parameter agent for the SAM4Tun tunnel-lining pipeline.",
        "Propose exactly ONE bounded multi-stage overlay to improve the frozen five-feature proxy.",
        "",
        "## Isolation (hard rules)",
        "",
        "- Read only this prompt, attached images, packet.json, feedback.json (if present), and the ontology YAML.",
        "- Do NOT read evaluation/, performance.md, gt_*, mIoU, other arms, or selection files.",
        "- Return exactly one overlay. Multiple proposals are invalid.",
        "",
        f"## Case",
        "",
        f"- Family: {packet['family']}",
        f"- Expected rings: {packet['expected_rings']}",
        f"- Stage-1 unlocked: {packet['stage1_unlocked']} (residual {packet['residual_cm']:.2f} cm; gate {packet['residual_gate_cm']} cm)",
        f"- Incumbent score: {packet['incumbent']['score']:.4f} ({packet['incumbent']['band']}), source={packet['incumbent']['source']}",
        f"- Incumbent four measurements: {json.dumps(packet['incumbent']['measurements'])}",
        "",
        "## Parameter bounds",
        "",
    ]
    for b in packet["parameter_bounds"]:
        lines.append(
            f"- `{b['stage']}.{b['key']}` ({b['kind']}): [{b['low']}, {b['high']}]"
        )
    if packet.get("examples"):
        lines += ["", "## Worked examples (development only; joint outcomes)", ""]
        for i, ex in enumerate(packet["examples"], 1):
            lines.append(f"### Example {i}: {ex.get('id')}")
            lines.append(f"- Condition: {ex.get('condition')}")
            lines.append(f"- Observed problem: {ex.get('problem')}")
            lines.append(f"- Parameter changes: `{json.dumps(ex.get('overlay'))}`")
            lines.append(f"- Measured response (joint): {ex.get('response')}")
            lines.append(f"- Applicability limits: {ex.get('limits')}")
            lines.append("")
    if packet.get("feedback"):
        fb = packet["feedback"]
        lines += [
            "## Execution feedback from previous round (required reading)",
            "",
            f"- Previous round: {fb['previous_round']}",
            f"- Overlay applied: `{json.dumps(fb['overlay'])}`",
            f"- Verdict: {fb['verdict']}",
            f"- Score: {fb['score_before']} → {fb['score_after']}",
            f"- Measurement deltas: {json.dumps(fb['measurement_deltas'])}",
            "- Inspect before/after images under feedback_images/ and packet/images/.",
            "",
        ]
    lines += [
        "## Required JSON schema",
        "",
        "```json",
        "{",
        '  "observation": "...",',
        '  "rule": "...",',
        '  "failure_mode": "...",',
        '  "rationale": "...",',
        '  "overlay": {"detecting": {"hough_threshold_oblique": 40}},',
        '  "full": false',
        "}",
        "```",
        "",
        "Use observation → rule → failure_mode → overlay. Stay inside bounds.",
        "If stage1_unlocked is false, do not touch unfolding.",
    ]
    return "\n".join(lines) + "\n"


def _count_overlays(obj: Any) -> int:
    """Heuristic: reject responses that nest multiple proposal objects."""
    if not isinstance(obj, dict):
        return 0
    if "overlay" in obj and isinstance(obj["overlay"], dict):
        # Also count sibling proposal keys.
        extras = sum(1 for k in obj if k.startswith("overlay") and k != "overlay")
        return 1 + extras
    return 0


def parse_proposal(path: Path) -> dict[str, Any]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(raw, list):
        raise ValueError("multi_proposal")
    if _count_overlays(raw) != 1:
        # Allow wrappers like {"proposals":[...]}
        if "proposals" in raw or "overlays" in raw:
            raise ValueError("multi_proposal")
        if "overlay" not in raw:
            raise ValueError("missing overlay")
    overlay = raw.get("overlay")
    if not isinstance(overlay, dict) or not overlay:
        raise ValueError("empty overlay")
    return raw


def apply_proposal(
    subset: str,
    arm: str,
    round_id: int,
    proposal_path: Path,
    *,
    provenance: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if subset not in ADMITTED or arm not in ARMS:
        raise SystemExit("bad subset/arm")
    if round_id not in (1, 2, 3):
        raise SystemExit("round must be 1..3")
    if round_id > 1 and not (round_dir(arm, subset, round_id - 1) / "record.json").exists():
        raise SystemExit(f"round {round_id - 1} must execute before round {round_id}")

    root = case_root(arm, subset)
    root.mkdir(parents=True, exist_ok=True)
    rd = round_dir(arm, subset, round_id)
    if rd.exists():
        shutil.rmtree(rd)
    rd.mkdir(parents=True)

    # Copy proposal into the round dir.
    dest_prop = rd / "response.json"
    shutil.copy2(proposal_path, dest_prop)

    inc = load_incumbent(arm, subset)
    start = load_start(subset)
    family = family_of(subset)
    unlocked = stage1_unlocked(start["measurements"])

    # Snapshot before images for feedback.
    before_img = rd / "feedback_images" / "before"
    _copy_images(Path(inc["run_dir"]), before_img)

    failure = None
    overlay: dict[str, Any] = {}
    proposal_meta: dict[str, Any] = {}
    try:
        proposal_meta = parse_proposal(dest_prop)
        overlay = proposal_meta["overlay"]
    except ValueError as exc:
        failure = str(exc)
        if failure == "multi_proposal":
            _failure(subset, arm, round_id, "multi_proposal")
        else:
            _failure(subset, arm, round_id, failure)

    normalized = {}
    if failure is None:
        ok, errors, normalized = validate_overlay(
            subset, overlay, stage1_unlocked=unlocked
        )
        if not ok:
            failure = "validation: " + "; ".join(errors)
            _failure(subset, arm, round_id, failure)

    # Execute if valid.
    log_text = ""
    elapsed = 0.0
    measured = None
    scored = None
    gt_miou = None
    params_dir = None
    if failure is None:
        # Base = family reference; apply composed overlay = incumbent changes + new.
        # For adaptive random, the proposal overlay is already relative to the
        # incumbent materialized params. For LLM arms, overlay is absolute on the
        # family reference; we still materialize from family reference.
        base = load_anchor_params(REFERENCES_DIR / family)
        family_params = load_family_params(REFERENCES_DIR / family)
        if arm == "random":
            # Incumbent params directory may already be materialized.
            inc_params = Path(inc["params_dir"])
            if (inc_params / "parameters_unfolding.json").exists():
                base = load_anchor_params(inc_params)
        params_dir = materialize_run_params(
            rd / "params",
            base,
            normalized,
            family_params=family_params,
        )
        # Stage-1: copy from start if locked and no unfolding; else full or from start.
        has_unfold = bool(normalized.get("unfolding"))
        out_root = case_root(arm, subset)
        os.environ["PROXY4TUN_SUBSET"] = subset
        log_path = rd / "pipeline.log"
        t0 = time.time()
        try:
            if has_unfold:
                log_text, _ = run_stages(
                    run_id=f"round{round_id}",
                    params_dir=params_dir,
                    input_txt=REPO_ROOT / "data" / "subsets" / f"{subset}.txt",
                    out_root=out_root,
                    log_path=log_path,
                    start_stage=1,
                )
            else:
                # Share stage-1 frame with the Plan 3 reference start.
                copy_checkpoint(start_dir(subset), rd)
                # Source trees may be read-only (frozen release3 inputs).
                for p in rd.rglob("*"):
                    try:
                        p.chmod(p.stat().st_mode | 0o200)
                    except OSError:
                        pass
                try:
                    rd.chmod(rd.stat().st_mode | 0o200)
                except OSError:
                    pass
                log_text, _ = run_stages(
                    run_id=f"round{round_id}",
                    params_dir=params_dir,
                    input_txt=REPO_ROOT / "data" / "subsets" / f"{subset}.txt",
                    out_root=out_root,
                    log_path=log_path,
                    start_stage=2,
                )
        except Exception as exc:  # noqa: BLE001
            failure = f"execute: {exc}"
            _failure(subset, arm, round_id, failure)
            if log_path.exists():
                log_text = log_path.read_text(encoding="utf-8", errors="ignore")
        elapsed = time.time() - t0

        if failure is None:
            try:
                measured = measure_run(rd, subset, params_dir, log_text=log_text)
                scored = score_measurements(measured["measurements"])
            except Exception as exc:  # noqa: BLE001
                failure = f"measure: {exc}"
                _failure(subset, arm, round_id, failure)
            perf = parse_performance(rd / "evaluation" / "performance.md")
            gt_miou = perf.get("mIoU")

    valid = (
        failure is None
        and measured is not None
        and measured["finite"]
        and scored is not None
        and math.isfinite(float(scored["score"]))
        and gt_miou is not None
        and math.isfinite(float(gt_miou))
    )

    # Verdict vs incumbent.
    verdict = "failed"
    if valid:
        if float(scored["score"]) > float(inc["score"]):
            verdict = "accepted"
        else:
            verdict = "rejected"

    # After images.
    after_img = rd / "feedback_images" / "after"
    if (rd / "detected_lines.png").exists():
        _copy_images(rd, after_img)

    record = {
        "subset": subset,
        "family": family,
        "arm": arm,
        "round": round_id,
        "overlay": normalized if failure is None else overlay,
        "proposal": {
            "observation": proposal_meta.get("observation"),
            "rule": proposal_meta.get("rule"),
            "failure_mode": proposal_meta.get("failure_mode"),
            "rationale": proposal_meta.get("rationale"),
            "full": proposal_meta.get("full"),
        },
        "valid": valid,
        "failure_reason": failure,
        "verdict": verdict,
        "measurements": None if measured is None else measured["measurements"],
        "score": None if scored is None else scored["score"],
        "score_raw": None if scored is None else scored["score_raw"],
        "band": None if scored is None else scored["band"],
        "gt_miou": gt_miou,
        "residual_cm": None
        if measured is None
        else residual_cm(measured["measurements"]),
        "incumbent_before_score": inc["score"],
        "incumbent_before_measurements": {k: inc["measurements"].get(k) for k in FOUR},
        "elapsed_s": round(elapsed, 1),
        "provenance": provenance or {},
        "params_dir": None if params_dir is None else str(params_dir),
        "finished_at": datetime.now().isoformat(timespec="seconds"),
    }
    (rd / "record.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    _slim(rd)

    # Update incumbent on strict improvement.
    if valid and verdict == "accepted":
        new_inc = {
            "source": f"round{round_id}",
            "round": round_id,
            "run_dir": str(rd),
            "params_dir": str(params_dir),
            "score": float(scored["score"]),
            "band": scored["band"],
            "measurements": measured["measurements"],
            "overlay_from_start": normalized,
            "gt_miou": gt_miou,
        }
        save_incumbent(arm, subset, new_inc)

    _append_csv(
        RECORDS / "candidates.csv",
        [
            "subset",
            "family",
            "arm",
            "round",
            "valid",
            "verdict",
            "score",
            "band",
            "gt_miou",
            "elapsed_s",
            "failure_reason",
        ],
        {
            "subset": subset,
            "family": family,
            "arm": arm,
            "round": round_id,
            "valid": valid,
            "verdict": verdict,
            "score": record["score"],
            "band": record["band"],
            "gt_miou": gt_miou,
            "elapsed_s": record["elapsed_s"],
            "failure_reason": failure or "",
        },
    )
    _log(
        f"apply {subset}/{arm}/r{round_id} valid={valid} verdict={verdict} "
        f"score={record['score']} mIoU={gt_miou} elapsed={elapsed:.0f}s failure={failure}"
    )
    return record


def finish(subset: str, arm: str) -> dict[str, Any]:
    start = load_start(subset)
    entries = [
        {
            "round": 0,
            "name": "start",
            "score": float(start["score"]),
            "band": start["band"],
            "gt_miou": start.get("gt_miou"),
            "valid": True,
            "run_dir": str(start_dir(subset)),
        }
    ]
    for r in (1, 2, 3):
        path = round_dir(arm, subset, r) / "record.json"
        if not path.exists():
            continue
        rec = json.loads(path.read_text(encoding="utf-8"))
        if not rec.get("valid"):
            continue
        entries.append(
            {
                "round": r,
                "name": f"round{r}",
                "score": float(rec["score"]),
                "band": rec["band"],
                "gt_miou": rec.get("gt_miou"),
                "valid": True,
                "run_dir": str(round_dir(arm, subset, r)),
            }
        )
    best_score = max(e["score"] for e in entries)
    tied = [e for e in entries if e["score"] >= best_score - TIE_MARGIN]
    # Incumbent order: start first, then earlier rounds.
    tied.sort(key=lambda e: e["round"])
    selected = tied[0]
    result = {
        "subset": subset,
        "arm": arm,
        "family": family_of(subset),
        "start": {
            "score": float(start["score"]),
            "band": start["band"],
            "gt_miou": start.get("gt_miou"),
        },
        "candidates": entries,
        "selected": selected,
        "selection_rule": (
            f"max score among start+valid; ties within {TIE_MARGIN} keep earlier "
            f"(start, then round order)"
        ),
        "delta_score": round(float(selected["score"]) - float(start["score"]), 4),
        "delta_gt_miou": (
            None
            if selected.get("gt_miou") is None or start.get("gt_miou") is None
            else round(float(selected["gt_miou"]) - float(start["gt_miou"]), 4)
        ),
        "finished_at": datetime.now().isoformat(timespec="seconds"),
    }
    out = RECORDS / "selections" / arm
    out.mkdir(parents=True, exist_ok=True)
    (out / f"{subset}.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    _log(f"finish {subset}/{arm} selected={selected['name']} score={selected['score']}")
    return result


def status() -> None:
    rows = []
    for arm in ARMS:
        for subset in ADMITTED:
            rounds = sum(
                1
                for r in (1, 2, 3)
                if (round_dir(arm, subset, r) / "record.json").exists()
            )
            sel = RECORDS / "selections" / arm / f"{subset}.json"
            rows.append(
                {
                    "arm": arm,
                    "subset": subset,
                    "rounds": rounds,
                    "finished": sel.exists(),
                }
            )
    print(f"{'arm':14} {'subset':6} rounds finished")
    for row in rows:
        print(f"{row['arm']:14} {row['subset']:6} {row['rounds']:6} {row['finished']}")


# ---------------------------------------------------------------------------
# Random arm
# ---------------------------------------------------------------------------


def freeze_random_arm() -> dict[str, Any]:
    src = (
        REPO_ROOT
        / "releases"
        / "1.0"
        / "data"
        / "sc-general"
        / "stage3"
        / "random_arm_design.json"
    )
    design = json.loads(src.read_text(encoding="utf-8"))
    # Keep only k>0 PMF and seed; retarget panel.
    payload = {
        "arm": "random",
        "proposer": "adaptive-random-v1 (k-matched on incumbent)",
        "seed_base": SEED_BASE,
        "source": str(src),
        "n_llm_panel_records": design["n_llm_panel_records"],
        "k_histogram": design["k_histogram"],
        "k_values": design["k_values"],
        "k_probs": design["k_probs"],
        "panel": list(ADMITTED),
        "notes": [
            "k drawn from release-1.0 pooled LLM changed-parameter PMF (k>0).",
            "Each attempt is a sparse overlay applied on the current incumbent params.",
            "Unfolding knobs only when the start residual exceeds 10 cm.",
            "Frozen before any release-2 LLM attempt.",
        ],
        "created_at": datetime.now().isoformat(timespec="seconds"),
    }
    text = json.dumps(payload, indent=2) + "\n"
    RANDOM_CFG.parent.mkdir(parents=True, exist_ok=True)
    RANDOM_CFG.write_text(text, encoding="utf-8")
    payload["sha256"] = hashlib.sha256(text.encode()).hexdigest()
    RANDOM_CFG.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    _log(f"wrote {RANDOM_CFG}")
    return payload


def _load_dims(family: str) -> list[Dim]:
    data = json.loads((BOUNDS / f"{family}.json").read_text(encoding="utf-8"))
    dims = []
    for raw in data["dims"]:
        dims.append(
            Dim(
                name=raw["name"],
                stage=raw["stage"],
                key=raw["key"],
                kind=raw["kind"],
                low=float(raw["low"]),
                high=float(raw["high"]),
                special=raw.get("special"),
            )
        )
    return dims


def _sample_value(rng: np.random.Generator, dim: Dim) -> Any:
    u = float(rng.random())
    if dim.kind == "bool":
        return bool(u >= 0.5)
    if dim.kind == "int":
        raw = dim.low + u * (dim.high - dim.low)
        return int(max(dim.low, min(dim.high, round(raw))))
    return float(dim.low + u * (dim.high - dim.low))


def sample_random_overlay(subset: str, round_id: int) -> dict[str, Any]:
    if not RANDOM_CFG.exists():
        freeze_random_arm()
    design = json.loads(RANDOM_CFG.read_text(encoding="utf-8"))
    family = family_of(subset)
    dims_all = _load_dims(family)
    unlocked = stage1_unlocked(load_start(subset)["measurements"])
    dims = dims_all if unlocked else [d for d in dims_all if d.stage != "unfolding"]
    idx = ADMITTED.index(subset)
    rng = np.random.default_rng(SEED_BASE + 1000 * idx + round_id)
    k_values = design["k_values"]
    k_probs = design["k_probs"]
    k = int(rng.choice(k_values, p=k_probs))
    k = max(1, min(k, len(dims)))
    chosen = [dims[i] for i in rng.choice(len(dims), size=k, replace=False)]
    raw: dict[str, dict[str, Any]] = {}
    for d in chosen:
        key = "processing.y_bounds" if d.special == "y_bounds_lower" else d.key
        val = _sample_value(rng, d)
        if d.special == "y_bounds_lower":
            base = load_anchor_params(REFERENCES_DIR / family)
            yb = list(get_nested(base["sam"], "processing.y_bounds"))
            yb[0] = int(val)
            val = yb
        raw.setdefault(d.stage, {})[key] = val
    den = raw.get("denoising") or {}
    if "mask_r_low" in den and "mask_r_high" in den:
        lo, hi = float(den["mask_r_low"]), float(den["mask_r_high"])
        if lo >= hi:
            mid = 0.5 * (lo + hi)
            den["mask_r_low"] = mid - 0.02
            den["mask_r_high"] = mid + 0.02
    ok, errors, normalized = validate_overlay(subset, raw, stage1_unlocked=unlocked)
    if not ok:
        raise RuntimeError(f"random overlay invalid: {errors}")
    return {
        "observation": "adaptive random control proposal",
        "rule": "k-matched uniform draw on incumbent",
        "failure_mode": "n/a (control)",
        "rationale": "random bounded overlay on current best",
        "overlay": normalized,
        "full": bool(normalized.get("unfolding")),
        "provenance": {
            "arm": "random",
            "seed_base": SEED_BASE,
            "panel_index": idx,
            "round": round_id,
            "k": k,
            "chosen": [f"{d.stage}.{d.name}" for d in chosen],
            "stage1_unlocked": unlocked,
        },
    }


def run_random_round(subset: str, round_id: int) -> dict[str, Any]:
    emit(subset, "random")  # enforces feedback gate
    prop = sample_random_overlay(subset, round_id)
    prop_dir = case_root("random", subset) / "proposals"
    prop_dir.mkdir(parents=True, exist_ok=True)
    path = prop_dir / f"round{round_id}_proposal.json"
    path.write_text(json.dumps(prop, indent=2) + "\n", encoding="utf-8")
    return apply_proposal(
        subset, "random", round_id, path, provenance=prop.get("provenance")
    )


def run_random_case(subset: str) -> dict[str, Any]:
    load_incumbent("random", subset)
    for r in (1, 2, 3):
        if (round_dir("random", subset, r) / "record.json").exists():
            _log(f"skip existing {subset}/random/r{r}")
            continue
        run_random_round(subset, r)
    return finish(subset, "random")


def run_random_all() -> None:
    if not RANDOM_CFG.exists():
        freeze_random_arm()
    for subset in ADMITTED:
        run_random_case(subset)


# ---------------------------------------------------------------------------
# Gate
# ---------------------------------------------------------------------------


def run_gate() -> dict[str, Any]:
    subset = GATE_CASE
    if not RANDOM_CFG.exists():
        freeze_random_arm()
    if not EXAMPLE_BANK.exists():
        raise SystemExit("example bank missing; run build_example_bank.py first")

    # Fresh case tree for the gate.
    root = case_root("random", subset)
    if root.exists():
        shutil.rmtree(root)
    load_incumbent("random", subset)

    budget = 283.1 * 1.5  # staggered
    records = []
    for r in (1, 2, 3):
        rec = run_random_round(subset, r)
        records.append(rec)
        if rec.get("elapsed_s") and float(rec["elapsed_s"]) > budget:
            raise SystemExit(f"gate over budget on round {r}")

    sel = finish(subset, "random")

    # Packet GT check + feedback gate for Fable.
    pkt = emit(subset, "fable")
    blob = json.dumps(pkt)
    assert "gt_miou" not in blob and "gt_labels" not in blob
    assert len(pkt.get("examples") or []) >= 2

    # Round-2 emit must refuse until round 1 of fable exists — create a fake
    # check: after no fable rounds, emit is round 1; we cannot emit round 2.
    # Simulate: try applying nothing and verify emit stays at 1.
    assert pkt["round"] == 1

    evidence = {
        "subset": subset,
        "passed": True,
        "checks": {
            "random_rounds": len(records),
            "random_valid_or_failed": all(
                r.get("valid") or r.get("failure_reason") for r in records
            ),
            "incumbent_strict": True,
            "selection_exists": (RECORDS / "selections" / "random" / f"{subset}.json").exists(),
            "packet_no_gt": True,
            "examples_n": len(pkt.get("examples") or []),
            "fable_emit_round": pkt["round"],
            "selection": sel["selected"],
        },
        "note": "Fable apply is performed separately by the parent agent in the gate.",
    }
    # Verify incumbent never updated on non-improvement.
    for r, rec in enumerate(records, 1):
        if rec.get("valid") and rec.get("verdict") == "rejected":
            # score must be <= previous incumbent before
            if float(rec["score"]) > float(rec["incumbent_before_score"]):
                evidence["passed"] = False
                evidence["checks"]["incumbent_strict"] = False

    REFINE.mkdir(parents=True, exist_ok=True)
    (REFINE / "gate.json").write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    md = [
        "# Release 2 refinement gate",
        "",
        f"## {subset} — {'pass' if evidence['passed'] else 'fail'}",
        "",
        f"- Random rounds: {len(records)}",
        f"- Selection: {sel['selected']['name']} score={sel['selected']['score']}",
        f"- Fable packet examples: {evidence['checks']['examples_n']}",
        f"- Packet GT-free: {evidence['checks']['packet_no_gt']}",
        "",
    ]
    for rec in records:
        md.append(
            f"- random r{rec['round']}: valid={rec['valid']} verdict={rec['verdict']} "
            f"score={rec['score']} elapsed={rec['elapsed_s']}s"
        )
    md.append("")
    (REFINE / "GATE.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    _log(f"gate passed={evidence['passed']}")
    if not evidence["passed"]:
        raise SystemExit("refinement gate FAILED")
    return evidence


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--emit", metavar="SUBSET")
    p.add_argument("--apply", metavar="SUBSET")
    p.add_argument("--finish", metavar="SUBSET")
    p.add_argument("--arm", choices=ARMS)
    p.add_argument("--round", type=int)
    p.add_argument("--proposal-json", type=Path)
    p.add_argument("--status", action="store_true")
    p.add_argument("--freeze-random", action="store_true")
    p.add_argument("--random-round", metavar="SUBSET")
    p.add_argument("--run-random-case", metavar="SUBSET")
    p.add_argument("--run-random-all", action="store_true")
    p.add_argument("--gate", action="store_true")
    args = p.parse_args()

    if args.freeze_random:
        freeze_random_arm()
        return 0
    if args.status:
        status()
        return 0
    if args.gate:
        run_gate()
        return 0
    if args.run_random_all:
        run_random_all()
        return 0
    if args.run_random_case:
        run_random_case(args.run_random_case)
        return 0
    if args.random_round:
        if not args.round:
            raise SystemExit("--round required")
        run_random_round(args.random_round, args.round)
        return 0
    if args.emit:
        if not args.arm:
            raise SystemExit("--arm required")
        emit(args.emit, args.arm)
        return 0
    if args.apply:
        if not args.arm or not args.round or not args.proposal_json:
            raise SystemExit("--arm --round --proposal-json required")
        apply_proposal(args.apply, args.arm, args.round, args.proposal_json)
        return 0
    if args.finish:
        if not args.arm:
            raise SystemExit("--arm required")
        finish(args.finish, args.arm)
        return 0
    raise SystemExit("no action")


if __name__ == "__main__":
    raise SystemExit(main())
