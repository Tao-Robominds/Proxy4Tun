#!/usr/bin/env python3
"""Score a completed pipeline run with the frozen SC-general pruned_lean proxy.

Features (from bo/sc_general/models.json):
  correspondence_f1@15, sam_fill_rate, ring_count_error, depth_nan_ratio

Clip raw proxy to [0, 1]. Bands:
  reject  : < 0.5
  refine  : [0.5, 0.7)
  accept  : >= 0.7

GT mIoU is revealed only when reveal_gt=True (selection/report).

Usage:
  ./venv/bin/python bo/sc_general/score_scaled.py --subset 3-4 --anchor
  ./venv/bin/python bo/sc_general/score_scaled.py data/3-4-scgen-refinement/round1 --subset 3-4
  ./venv/bin/python bo/sc_general/score_scaled.py --subset 3-4 --anchor --reveal-gt
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path
from typing import Any

import pandas as pd

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from bo.runtime.ridge import predict  # noqa: E402
from bo.paths import UNIFIED_DATA  # noqa: E402
from bo.sc_general.features import all_features  # noqa: E402
from bo.sc_general.label_map import build_label_map  # noqa: E402
from bo.sc_general.replay import (  # noqa: E402
    find_params_dir,
    find_ring_count,
    replay_run,
)
from bo.runtime.intrinsics import extract_intrinsics  # noqa: E402
from bo.runtime.spaces import holdout_case_config  # noqa: E402

PKG = Path(__file__).resolve().parent
MODELS = PKG / "models.json"
STAGE1 = _REPO / "bo" / "full_stage" / "stage1_features.json"
SHADOW = _REPO / "data" / "sc-general" / "replay" / "stage3"
EXPECTED_PROXY = {"3-4": 0.5196911758815168}

REJECT_THR = 0.5
ACCEPT_THR = 0.7
DEFAULT_RING = 10


def scale(proxy_raw: float) -> float:
    return min(max(float(proxy_raw), 0.0), 1.0)


def band(proxy_scaled: float) -> str:
    if proxy_scaled < REJECT_THR:
        return "reject"
    if proxy_scaled < ACCEPT_THR:
        return "refine"
    return "accept"


def anchor_run_dir(subset: str) -> Path:
    """Resolve the holdout/reference sibling used in Stage-2 scoring.

    Prefer the unified family-proxy run; fall back to frozen research anchors
    for train cases that appear in the bayes holdout panel (1-1, and 4-1 if
    the family-proxy tree is missing).
    """
    candidates = [
        UNIFIED_DATA / f"{subset}-family-proxy" / "runs" / f"{subset}-anchor",
        _REPO / "data" / "anchors" / subset,
    ]
    for cand in candidates:
        if (cand / "final.csv").exists() or (cand / "state.pkl").exists():
            return cand
    raise FileNotFoundError(f"No holdout anchor for {subset}; tried {candidates}")


def _load_models() -> dict[str, Any]:
    return json.loads(MODELS.read_text(encoding="utf-8"))


def _parse_miou(run_dir: Path) -> float | None:
    perf = run_dir / "evaluation" / "performance.md"
    if perf.exists():
        m = re.search(r"Mean IoU \(mIoU\):\s*([\d.]+)", perf.read_text(encoding="utf-8"))
        if m:
            return float(m.group(1))
    intr = run_dir / "intrinsics.json"
    if intr.exists():
        d = json.loads(intr.read_text(encoding="utf-8"))
        v = d.get("perf_mIoU")
        if v is not None and math.isfinite(float(v)):
            return float(v)
    return None


def _read_log(run_dir: Path) -> str:
    from bo.sc_general.replay import find_log

    log = find_log(run_dir)
    if log is None:
        return ""
    return log.read_text(encoding="utf-8", errors="ignore")


def _residual_backfill(run_dir: Path, subset: str, metrics: dict[str, Any]) -> None:
    """Prefer run-own residual; else existing intrinsics; else stage1_features."""
    r = metrics.get("recentre_residual_max_cm")
    if r is not None and math.isfinite(float(r)):
        return
    intr_path = run_dir / "intrinsics.json"
    if intr_path.exists():
        intr = json.loads(intr_path.read_text(encoding="utf-8"))
        rr = intr.get("recentre_residual_max_cm")
        if rr is not None and math.isfinite(float(rr)):
            metrics["recentre_residual_max_cm"] = float(rr)
            if "unfold_residual" in intr:
                metrics["unfold_residual"] = float(intr["unfold_residual"])
            return
    if STAGE1.exists():
        s1 = json.loads(STAGE1.read_text(encoding="utf-8")).get(subset, {})
        if s1.get("status") == "ok":
            rr = s1.get("recentre_residual_max_cm")
            if rr is not None and math.isfinite(float(rr)):
                metrics["recentre_residual_max_cm"] = float(rr)
                metrics["unfold_residual"] = float(s1.get("unfold_residual", 0.0))


def _gt_blind_intrinsics(metrics: dict[str, Any]) -> dict[str, Any]:
    out = {}
    for k, v in metrics.items():
        if k.startswith("perf_") or k.startswith("tier"):
            continue
        if isinstance(v, (int, float)) and math.isfinite(float(v)):
            out[k] = float(v)
        elif isinstance(v, (str, bool)) or v is None:
            out[k] = v
    return out


def extract_sc_features(
    run_dir: Path,
    subset: str,
    *,
    write_shadow: bool = True,
    log_text: str | None = None,
) -> dict[str, Any]:
    """Compute SC-general lean features + diagnostic intrinsics (GT-blind)."""
    run_dir = Path(run_dir)
    cfg = holdout_case_config(subset)
    params_dir = find_params_dir(run_dir)
    if log_text is None:
        log_text = _read_log(run_dir)

    metrics = extract_intrinsics(
        run_dir,
        params_dir=params_dir,
        log_text=log_text,
        expected_rings=int(cfg["expected_rings"]),
    )
    _residual_backfill(run_dir, subset, metrics)

    rc, rc_src = find_ring_count(run_dir)
    ls = replay_run(
        run_dir,
        params_dir=params_dir,
        ring_count=rc,
        write_shadow=write_shadow,
        shadow_root=SHADOW,
    )
    lm = build_label_map(run_dir, params_dir=params_dir)
    sc = all_features(ls, lm, ring_count=rc)

    feat = {
        "correspondence_f1@15": float(sc["correspondence_f1@15"]),
        "sam_fill_rate": float(metrics["sam_fill_rate"]),
        "ring_count_error": float(abs(rc - DEFAULT_RING)),
        "depth_nan_ratio": float(metrics["depth_nan_ratio"]),
    }
    for k, v in list(feat.items()):
        if not math.isfinite(v):
            raise ValueError(f"non-finite feature {k}={v} for {run_dir}")

    resid = metrics.get("recentre_residual_max_cm")
    corr = metrics.get("orient_axis_corr")
    return {
        "features": feat,
        "intrinsics_gt_blind": _gt_blind_intrinsics(metrics),
        "ring_count": int(rc),
        "ring_count_source": rc_src,
        "labelmap_source": lm.source,
        "recentre_residual_max_cm": float(resid) if resid is not None and math.isfinite(float(resid)) else None,
        "orient_axis_corr": float(corr) if corr is not None and math.isfinite(float(corr)) else None,
        "params_dir": str(params_dir),
        "ls": ls,
        "lm": lm,
    }


def score_run(
    run_dir: Path,
    subset: str,
    *,
    reveal_gt: bool = False,
    write_shadow: bool = True,
    log_text: str | None = None,
    model: dict[str, Any] | None = None,
) -> dict[str, Any]:
    models = _load_models()
    model = model or models["model"]
    alarm_thr = float(models.get("alarm_threshold", 0.5))

    extracted = extract_sc_features(
        run_dir, subset, write_shadow=write_shadow, log_text=log_text
    )
    feat = extracted["features"]
    proxy_raw = float(predict(model, pd.DataFrame([feat]))[0])
    proxy_scaled = scale(proxy_raw)

    out: dict[str, Any] = {
        "subset": subset,
        "run_dir": str(run_dir),
        "proxy_raw": proxy_raw,
        "proxy_scaled": proxy_scaled,
        "proxy": proxy_raw,
        "band": band(proxy_scaled),
        "alarm": proxy_scaled < alarm_thr,
        "alarm_threshold": alarm_thr,
        "features": feat,
        "intrinsics_gt_blind": extracted["intrinsics_gt_blind"],
        "ring_count": extracted["ring_count"],
        "ring_count_source": extracted["ring_count_source"],
        "labelmap_source": extracted["labelmap_source"],
        "recentre_residual_max_cm": extracted["recentre_residual_max_cm"],
        "orient_axis_corr": extracted["orient_axis_corr"],
        "mIoU": None,
    }
    if reveal_gt:
        out["mIoU"] = _parse_miou(run_dir)
    return out


def main() -> None:
    p = argparse.ArgumentParser(description="SC-general scaled proxy scorer")
    p.add_argument("run_dir", nargs="?", type=Path, default=None)
    p.add_argument("--subset", required=True)
    p.add_argument("--anchor", action="store_true")
    p.add_argument("--reveal-gt", action="store_true")
    p.add_argument("--no-shadow", action="store_true")
    args = p.parse_args()

    if args.anchor:
        run_dir = anchor_run_dir(args.subset)
    elif args.run_dir is not None:
        run_dir = args.run_dir
    else:
        p.error("Provide run_dir or --anchor")

    out = score_run(
        run_dir,
        args.subset,
        reveal_gt=args.reveal_gt,
        write_shadow=not args.no_shadow,
    )
    # Drop bulky nested keys for CLI readability when present
    print(json.dumps({k: v for k, v in out.items() if k != "intrinsics_gt_blind"}, indent=2))
    if args.subset in EXPECTED_PROXY and args.anchor:
        exp = EXPECTED_PROXY[args.subset]
        delta = abs(out["proxy_raw"] - exp)
        print(f"# gate-check vs stage2 {args.subset}: expected={exp:.12f} delta={delta:.2e}", file=sys.stderr)


if __name__ == "__main__":
    main()
