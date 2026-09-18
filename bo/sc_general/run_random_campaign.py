#!/usr/bin/env python3
"""Random-overlay control arm for the SC-general refinement panel.

Draws k-matched uniform bounded overlays (k from the empirical LLM
changed-knob distribution), validates them with the shared validator,
executes via refine_pilot.run_round, and selects with the same monotone
proxy rule. Non-adaptive by construction: all three rounds are drawn
up front.

Usage:
  ./venv/bin/python bo/sc_general/run_random_campaign.py --design
  ./venv/bin/python bo/sc_general/run_random_campaign.py --emit 1-5
  ./venv/bin/python bo/sc_general/run_random_campaign.py --apply 1-5 --round 1
  ./venv/bin/python bo/sc_general/run_random_campaign.py --finish 1-5
  ./venv/bin/python bo/sc_general/run_random_campaign.py --all
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from bo.sc_general.overlay_validator import validate_overlay  # noqa: E402
from bo.sc_general.refine_pilot import (  # noqa: E402
    ARM_PROPOSER,
    anchor_paths,
    build_context,
    out_root_for,
    packet_dir_for,
    run_round,
)
from bo.sc_general.select_round import select, select_dir_for  # noqa: E402
from bo.sc_general.stage3_report import PANEL  # noqa: E402
from bo.runtime.param_io import get_nested, load_anchor_params  # noqa: E402
from bo.runtime.spaces import FAMILY_SPACES, Dim, family_of_subset  # noqa: E402

ARM = "random"
SEED_BASE = 20260915
STAGE3 = _REPO / "data" / "sc-general" / "stage3"
DESIGN_PATH = STAGE3 / "random_arm_design.json"
CAMPAIGN = STAGE3 / "campaign_random.md"
LOG_DIR = STAGE3 / "logs"
UNLOCKED = {"3-4", "3-8", "3-10", "4-3"}
LLM_ARMS = ("fable", "gpt56", "gemini38")


def _append(text: str) -> None:
    CAMPAIGN.parent.mkdir(parents=True, exist_ok=True)
    with CAMPAIGN.open("a", encoding="utf-8") as fh:
        fh.write(text if text.endswith("\n") else text + "\n")


def _flat_base(base: dict[str, dict[str, Any]], dim: Dim) -> Any:
    stage = base.get(dim.stage) or {}
    if dim.special == "y_bounds_lower":
        yb = get_nested(stage, "processing.y_bounds")
        return float(yb[0]) if yb is not None else None
    try:
        return get_nested(stage, dim.key)
    except (KeyError, TypeError):
        return stage.get(dim.key)


def _values_equal(a: Any, b: Any) -> bool:
    if a is None or b is None:
        return False
    if isinstance(a, bool) or isinstance(b, bool):
        return bool(a) == bool(b)
    if isinstance(a, (list, tuple)) or isinstance(b, (list, tuple)):
        try:
            return list(a) == list(b)
        except Exception:
            return False
    try:
        return abs(float(a) - float(b)) < 1e-9
    except (TypeError, ValueError):
        return a == b


def _overlay_changed_count(
    overlay: dict[str, Any], base: dict[str, dict[str, Any]], dims: list[Dim]
) -> int:
    n = 0
    for d in dims:
        stage_ov = overlay.get(d.stage) or {}
        if d.special == "y_bounds_lower":
            if "processing.y_bounds" not in stage_ov and d.key not in stage_ov:
                continue
            val = stage_ov.get("processing.y_bounds", stage_ov.get(d.key))
            if isinstance(val, (list, tuple)):
                val = val[0]
            bv = _flat_base(base, d)
            if not _values_equal(val, bv):
                n += 1
            continue
        if d.key not in stage_ov:
            continue
        if not _values_equal(stage_ov[d.key], _flat_base(base, d)):
            n += 1
    return n


def _step_sizes(
    overlay: dict[str, Any], base: dict[str, dict[str, Any]], dims: list[Dim]
) -> list[float]:
    sizes: list[float] = []
    for d in dims:
        if d.kind == "bool" or d.high == d.low:
            continue
        stage_ov = overlay.get(d.stage) or {}
        if d.special == "y_bounds_lower":
            if "processing.y_bounds" not in stage_ov and d.key not in stage_ov:
                continue
            val = stage_ov.get("processing.y_bounds", stage_ov.get(d.key))
            if isinstance(val, (list, tuple)):
                val = val[0]
        elif d.key not in stage_ov:
            continue
        else:
            val = stage_ov[d.key]
        bv = _flat_base(base, d)
        if bv is None:
            continue
        try:
            sizes.append(abs(float(val) - float(bv)) / (d.high - d.low))
        except (TypeError, ValueError):
            continue
    return sizes


def _load_base(subset: str) -> dict[str, dict[str, Any]]:
    _, params_dir = anchor_paths(subset)
    return load_anchor_params(params_dir)


def build_design() -> dict[str, Any]:
    """Compute pooled changed-knob distribution from the three LLM arms."""
    k_counts: Counter[int] = Counter()
    step_sizes: list[float] = []
    n_records = 0
    per_arm: dict[str, Any] = {}
    for arm in LLM_ARMS:
        arm_k: Counter[int] = Counter()
        arm_n = 0
        root = _REPO / "data" / "refinement" / arm
        for rec_path in sorted(root.glob("*/round*/reflection_record.json")):
            rec = json.loads(rec_path.read_text(encoding="utf-8"))
            subset = str(rec.get("subset") or rec_path.parents[1].name)
            if subset not in PANEL:
                continue
            overlay = rec.get("overlay") or {}
            dims = FAMILY_SPACES[family_of_subset(subset)]()
            # Drop unfolding knobs from the comparison when locked, matching
            # what the random sampler is allowed to touch for that case.
            if subset not in UNLOCKED:
                dims = [d for d in dims if d.stage != "unfolding"]
            try:
                base = _load_base(subset)
            except Exception:
                continue
            k = _overlay_changed_count(overlay, base, dims)
            k_counts[k] += 1
            arm_k[k] += 1
            step_sizes.extend(_step_sizes(overlay, base, dims))
            arm_n += 1
            n_records += 1
        per_arm[arm] = {
            "n_panel_records": arm_n,
            "k_histogram": {str(k): v for k, v in sorted(arm_k.items())},
        }

    # Open knobs per family (with and without unfolding).
    open_knobs: dict[str, Any] = {}
    for fam, factory in FAMILY_SPACES.items():
        dims = factory()
        open_knobs[fam] = {
            "all": [f"{d.stage}.{d.name}" for d in dims],
            "locked_no_unfolding": [
                f"{d.stage}.{d.name}" for d in dims if d.stage != "unfolding"
            ],
            "n_all": len(dims),
            "n_locked": sum(1 for d in dims if d.stage != "unfolding"),
        }

    hist = {str(k): int(v) for k, v in sorted(k_counts.items())}
    # Empirical PMF over observed k (exclude k=0 so we always change something).
    usable = {k: v for k, v in k_counts.items() if k > 0}
    if not usable:
        usable = {8: 1}
    total = sum(usable.values())
    k_values = sorted(usable)
    k_probs = [usable[k] / total for k in k_values]

    design = {
        "arm": ARM,
        "proposer": ARM_PROPOSER[ARM],
        "seed_base": SEED_BASE,
        "panel": list(PANEL),
        "unlocked_cases": sorted(UNLOCKED),
        "n_llm_panel_records": n_records,
        "k_histogram": hist,
        "k_values": k_values,
        "k_probs": k_probs,
        "step_size_abs_over_range": {
            "n": len(step_sizes),
            "mean": float(np.mean(step_sizes)) if step_sizes else None,
            "median": float(np.median(step_sizes)) if step_sizes else None,
            "p90": float(np.percentile(step_sizes, 90)) if step_sizes else None,
        },
        "per_arm": per_arm,
        "open_knobs": open_knobs,
        "notes": [
            "Overlays are drawn non-adaptively (all three rounds up front).",
            "k is sampled from the pooled LLM changed-knob distribution (k>0).",
            "Chosen knobs get values ~ Uniform(low, high); ints rounded; bools thresholded.",
            "Radial-gate midpoint repair applied when both mask_r_* are drawn inverted.",
            "Unfolding knobs only when stage-1 residual unlocks the case.",
            "Step-size distribution is descriptive only; values are not step-matched.",
        ],
        "created_at": datetime.now().isoformat(),
    }
    DESIGN_PATH.parent.mkdir(parents=True, exist_ok=True)
    DESIGN_PATH.write_text(json.dumps(design, indent=2) + "\n", encoding="utf-8")
    _append(f"## Design written {design['created_at']}\n")
    _append(f"- n LLM panel records: {n_records}\n")
    _append(f"- k histogram: {hist}\n")
    _append(f"- usable k PMF: {dict(zip(k_values, [round(p, 3) for p in k_probs]))}\n")
    return design


def _load_design() -> dict[str, Any]:
    if not DESIGN_PATH.exists():
        return build_design()
    return json.loads(DESIGN_PATH.read_text(encoding="utf-8"))


def _sample_value(rng: np.random.Generator, dim: Dim) -> Any:
    u = float(rng.random())
    if dim.kind == "bool":
        return bool(u >= 0.5)
    if dim.kind == "int":
        # Inclusive integer range via continuous then round+clip.
        raw = dim.low + u * (dim.high - dim.low)
        return int(max(dim.low, min(dim.high, round(raw))))
    return float(dim.low + u * (dim.high - dim.low))


def sample_overlay(
    subset: str,
    rng: np.random.Generator,
    design: dict[str, Any],
) -> dict[str, Any]:
    """Draw one k-matched random overlay for subset; validate and return normalized."""
    dims_all = FAMILY_SPACES[family_of_subset(subset)]()
    unlocked = subset in UNLOCKED
    dims = dims_all if unlocked else [d for d in dims_all if d.stage != "unfolding"]
    if not dims:
        raise RuntimeError(f"no open knobs for {subset}")

    k_values = design["k_values"]
    k_probs = design["k_probs"]
    k = int(rng.choice(k_values, p=k_probs))
    k = min(k, len(dims))
    chosen_idx = rng.choice(len(dims), size=k, replace=False)
    chosen = [dims[i] for i in chosen_idx]

    raw: dict[str, dict[str, Any]] = {}
    for d in chosen:
        raw.setdefault(d.stage, {})[d.key if d.special != "y_bounds_lower" else "processing.y_bounds"] = (
            _sample_value(rng, d)
            if d.special != "y_bounds_lower"
            else _sample_value(rng, d)
        )

    # Radial-gate midpoint repair when both gates were drawn.
    den = raw.get("denoising") or {}
    if "mask_r_low" in den and "mask_r_high" in den:
        lo, hi = float(den["mask_r_low"]), float(den["mask_r_high"])
        if lo >= hi:
            mid = 0.5 * (lo + hi)
            den["mask_r_low"] = mid - 0.02
            den["mask_r_high"] = mid + 0.02

    # Expand y_bounds scalar to [lo, inherited_hi] via validator using base upper.
    base = _load_base(subset)
    if "sam" in raw and "processing.y_bounds" in raw["sam"]:
        lo = raw["sam"]["processing.y_bounds"]
        if not isinstance(lo, (list, tuple)):
            yb = list(get_nested(base["sam"], "processing.y_bounds"))
            yb[0] = int(lo)
            raw["sam"]["processing.y_bounds"] = yb

    ok, errors, normalized = validate_overlay(
        subset, raw, stage1_unlocked=unlocked
    )
    if not ok:
        raise RuntimeError(f"sampled overlay invalid for {subset}: {errors}")
    return {
        "overlay": normalized,
        "k": k,
        "chosen": [f"{d.stage}.{d.name}" for d in chosen],
        "stage1_unlocked": unlocked,
    }


def emit_case(subset: str, design: dict[str, Any] | None = None) -> list[Path]:
    if subset not in PANEL:
        raise SystemExit(f"{subset} not in PANEL")
    design = design or _load_design()
    idx = PANEL.index(subset)
    rng = np.random.default_rng(SEED_BASE + idx)
    pkt = packet_dir_for(subset, arm=ARM)
    pkt.mkdir(parents=True, exist_ok=True)
    # Also emit a context packet for provenance parity with LLM arms.
    build_context(subset, arm=ARM)
    paths: list[Path] = []
    for round_id in (1, 2, 3):
        drawn = sample_overlay(subset, rng, design)
        proposal = {
            "observation": "random-uniform-v1 control proposal (non-adaptive)",
            "rule": "k-matched uniform draw within family search space",
            "failure_mode": "n/a (control)",
            "rationale": "random bounded overlay",
            "overlay": drawn["overlay"],
            "full": bool(drawn["overlay"].get("unfolding")),
            "provenance": {
                "arm": ARM,
                "proposer": ARM_PROPOSER[ARM],
                "seed_base": SEED_BASE,
                "panel_index": idx,
                "round": round_id,
                "k": drawn["k"],
                "chosen": drawn["chosen"],
                "stage1_unlocked": drawn["stage1_unlocked"],
            },
        }
        path = pkt / f"round{round_id}_proposal.json"
        path.write_text(json.dumps(proposal, indent=2) + "\n", encoding="utf-8")
        paths.append(path)
        _append(f"- emit {subset} R{round_id}: k={drawn['k']} keys={drawn['chosen']}\n")
    return paths


def apply_round(subset: str, round_id: int) -> dict[str, Any]:
    prop_path = packet_dir_for(subset, arm=ARM) / f"round{round_id}_proposal.json"
    if not prop_path.exists():
        raise SystemExit(f"missing proposal: {prop_path}; run --emit {subset} first")
    prop = json.loads(prop_path.read_text(encoding="utf-8"))
    overlay = prop["overlay"]
    full = bool(prop.get("full") or overlay.get("unfolding"))
    out_root = out_root_for(subset, arm=ARM)
    run_dir = out_root / f"round{round_id}"
    # Skip if already completed successfully.
    rec = run_dir / "reflection_record.json"
    gt = run_dir / "offline_gt.json"
    if rec.exists() and gt.exists():
        existing = json.loads(rec.read_text(encoding="utf-8"))
        if existing.get("status") == "ok":
            _append(f"- skip {subset} R{round_id} (already ok)\n")
            return existing

    result = run_round(
        subset,
        round_id,
        overlay,
        arm=ARM,
        full=full,
        rationale=prop.get("rationale") or "random bounded overlay",
        provenance=prop.get("provenance"),
    )
    _append(
        f"- apply {subset} R{round_id}: status={result.get('status')} "
        f"proxy={result.get('proxy_scaled')} "
        f"dir={result.get('output_dir')}\n"
    )
    return result


def finish_case(subset: str) -> dict[str, Any]:
    sel = select(subset, arm=ARM)
    out = select_dir_for(ARM) / f"{subset}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(sel, indent=2) + "\n", encoding="utf-8")
    _append(
        f"- finish {subset}: selected={sel['selected']['round']} "
        f"ΔmIoU={sel.get('delta_mIoU_offline')}\n"
    )
    return sel


def run_all(*, gate_only: bool = False) -> None:
    design = _load_design()
    cases = ["1-5"] if gate_only else list(PANEL)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_path = LOG_DIR / ("random_gate.log" if gate_only else "random_all.log")
    _append(f"\n## run_all start {datetime.now().isoformat()} gate_only={gate_only}\n")
    with log_path.open("a", encoding="utf-8") as log:
        for subset in cases:
            log.write(f"=== {subset} {datetime.now().isoformat()} ===\n")
            log.flush()
            emit_case(subset, design=design)
            for r in (1, 2, 3):
                if gate_only and not (subset == "1-5" and r == 1):
                    continue
                try:
                    result = apply_round(subset, r)
                    log.write(
                        f"R{r} status={result.get('status')} "
                        f"proxy={result.get('proxy_scaled')}\n"
                    )
                except Exception as exc:
                    log.write(f"R{r} ERROR {exc}\n")
                    _append(f"- ERROR {subset} R{r}: {exc}\n")
                    raise
                log.flush()
                if gate_only:
                    return
            finish_case(subset)
            log.write(f"finished {subset}\n")
            log.flush()
    _append(f"## run_all done {datetime.now().isoformat()}\n")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--design", action="store_true", help="Write random_arm_design.json")
    p.add_argument("--emit", metavar="SUBSET", help="Emit 3 proposal JSONs for a case")
    p.add_argument("--apply", metavar="SUBSET", help="Execute one round")
    p.add_argument("--round", type=int, choices=(1, 2, 3), help="Round for --apply")
    p.add_argument("--finish", metavar="SUBSET", help="Select and write selection JSON")
    p.add_argument("--all", action="store_true", help="Emit+apply+finish all 22 cases")
    p.add_argument(
        "--gate",
        action="store_true",
        help="Single-instance gate: emit 1-5 and apply round 1 only",
    )
    args = p.parse_args()

    if args.design:
        d = build_design()
        print(json.dumps({k: d[k] for k in ("n_llm_panel_records", "k_histogram", "k_values", "k_probs")}, indent=2))
        print(f"wrote {DESIGN_PATH}")
        return
    if args.emit:
        paths = emit_case(args.emit)
        for path in paths:
            print(path)
        return
    if args.apply:
        if args.round is None:
            raise SystemExit("--apply requires --round")
        result = apply_round(args.apply, args.round)
        print(json.dumps({k: result.get(k) for k in (
            "status", "proxy_scaled", "band", "output_dir", "elapsed_s"
        )}, indent=2))
        return
    if args.finish:
        sel = finish_case(args.finish)
        print(json.dumps({
            "subset": sel["subset"],
            "selected": sel["selected"]["round"],
            "delta_mIoU": sel.get("delta_mIoU_offline"),
        }, indent=2))
        return
    if args.gate:
        run_all(gate_only=True)
        return
    if args.all:
        run_all(gate_only=False)
        return
    p.print_help()


if __name__ == "__main__":
    main()
