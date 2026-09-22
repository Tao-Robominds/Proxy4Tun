#!/usr/bin/env python3
"""Stage-2 feature gate: synthetic and natural rotation validation.

Writes data/release3/GATE_FEATURE.md and picks one scored candidate, or exits
non-zero if none pass.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from bo.paths import REFERENCES_DIR, RELEASE3_DATA  # noqa: E402
from bo.release2.measure import MEASUREMENT_KEYS as FOUR_BASE  # noqa: E402
from bo.release3.measure import measure_run  # noqa: E402
from bo.release3.synth_rotate import offline_gt_miou, write_shifted_run  # noqa: E402
from bo.runtime.metadata import DEV_SUBSETS, family_of  # noqa: E402

INPUTS = RELEASE3_DATA / "inputs"
SYNTH = RELEASE3_DATA / "rotation_synth"
GATE = RELEASE3_DATA / "GATE_FEATURE.md"
FOUR = (
    "correspondence_f1@15",
    "sam_fill_rate",
    "ring_count_error",
    "depth_nan_ratio",
)
CANDIDATES = ("rotation_advantage", "key_block_mismatch")


def _params(subset: str) -> Path:
    return REFERENCES_DIR / family_of(subset)


def _safe_rm(path: Path) -> None:
    if not path.exists():
        return
    for p in path.rglob("*"):
        try:
            p.chmod(p.stat().st_mode | 0o200)
        except OSError:
            pass
    try:
        path.chmod(path.stat().st_mode | 0o200)
    except OSError:
        pass
    import shutil

    shutil.rmtree(path)


def eval_pair(base_m: dict, shifted_m: dict) -> dict:
    four_delta = {k: abs(float(base_m[k]) - float(shifted_m[k])) for k in FOUR}
    return {
        "four_delta": four_delta,
        "four_ok": all(v < 1e-6 for v in four_delta.values()),
        "candidates": {
            name: {
                "base": float(base_m[name]),
                "shifted": float(shifted_m[name]),
                "delta": float(shifted_m[name]) - float(base_m[name]),
            }
            for name in CANDIDATES
        },
        "observability": {
            "base": float(base_m["key_observability"]),
            "shifted": float(shifted_m["key_observability"]),
        },
    }


def main() -> int:
    SYNTH.mkdir(parents=True, exist_ok=True)
    rows = []
    lines = [
        "# Release 3 feature gate",
        "",
        "Synthetic cyclic label shifts on development references under",
        "`data/release3/inputs/references/`. Boundaries and ring ids fixed.",
        "",
    ]

    for subset in DEV_SUBSETS:
        src = INPUTS / "references" / subset
        params = _params(subset)
        if not (src / "final.csv").exists():
            raise SystemExit(f"missing {src}")
        base = measure_run(src, subset, params)
        base_gt = offline_gt_miou(src, subset)
        rings = sorted({int(r) for r in __import__("pandas").read_csv(src / "final.csv", usecols=["pred_ring"])["pred_ring"].unique()})

        # All-ring shift k=1
        dst_all = SYNTH / f"{subset}_all_k1"
        _safe_rm(dst_all)
        write_shifted_run(src, dst_all, shift=1, params_dir=params, light=False)
        m_all = measure_run(dst_all, subset, dst_all)
        gt_all = offline_gt_miou(dst_all, subset)
        pair_all = eval_pair(base["measurements"], m_all["measurements"])
        rows.append(
            {
                "subset": subset,
                "family": family_of(subset),
                "mode": "all_rings_k1",
                "gt_base": base_gt,
                "gt_shifted": gt_all,
                **pair_all,
            }
        )

        # Single-ring shift on the median ring
        mid = rings[len(rings) // 2]
        dst_one = SYNTH / f"{subset}_ring{mid}_k1"
        _safe_rm(dst_one)
        write_shifted_run(src, dst_one, shift=1, ring_ids=[mid], params_dir=params, light=False)
        m_one = measure_run(dst_one, subset, dst_one)
        gt_one = offline_gt_miou(dst_one, subset)
        pair_one = eval_pair(base["measurements"], m_one["measurements"])
        rows.append(
            {
                "subset": subset,
                "family": family_of(subset),
                "mode": f"single_ring_{mid}_k1",
                "gt_base": base_gt,
                "gt_shifted": gt_one,
                **pair_one,
            }
        )

        lines.append(f"## {subset} ({family_of(subset)})")
        lines.append("")
        lines.append(f"- Base GT mIoU: {base_gt:.3f}")
        lines.append(
            f"- Base candidates: "
            + ", ".join(f"{c}={base['measurements'][c]:.4f}" for c in CANDIDATES)
            + f", observability={base['measurements']['key_observability']:.2f}"
        )
        for row in rows[-2:]:
            lines.append(
                f"- {row['mode']}: GT {row['gt_shifted']:.3f} "
                f"(Δ {row['gt_shifted'] - row['gt_base']:+.3f}); "
                f"four-invariant={row['four_ok']}; "
                + ", ".join(
                    f"{c} {row['candidates'][c]['base']:.4f}→{row['candidates'][c]['shifted']:.4f}"
                    for c in CANDIDATES
                )
            )
        lines.append("")

    # Natural: 1-5 start vs fable selection if available under release2 analysis numbers
    # Copied references only; use inputs/references/1-5 if present.
    natural_lines = ["## Natural checks", ""]
    nat_ok = True
    ref_15 = INPUTS / "references" / "1-5"
    if ref_15.exists():
        params = _params("1-5")
        m15 = measure_run(ref_15, "1-5", params)
        natural_lines.append(
            f"- 1-5 reference: GT {offline_gt_miou(ref_15, '1-5'):.3f}; "
            + ", ".join(f"{c}={m15['measurements'][c]:.4f}" for c in CANDIDATES)
        )
    else:
        natural_lines.append("- 1-5 reference missing from inputs")
        nat_ok = False

    # Decide winner
    lines.append("## Decision")
    lines.append("")
    decision = {"passed": False, "feature": None, "reason": ""}
    all_ring_rows = [r for r in rows if r["mode"] == "all_rings_k1"]
    single_rows = [r for r in rows if r["mode"].startswith("single_ring")]

    for cand in CANDIDATES:
        four_ok = all(r["four_ok"] for r in rows)
        # Separation: shifted > base + margin on all-ring for staggered+continuous
        sep_all = []
        for r in all_ring_rows:
            if r["family"] == "complex":
                continue
            d = r["candidates"][cand]["delta"]
            sep_all.append(d > 0.02 and r["gt_shifted"] < r["gt_base"] - 0.05)
        sep_single = []
        for r in single_rows:
            d = r["candidates"][cand]["delta"]
            sep_single.append(d > 0.005 and r["gt_shifted"] < r["gt_base"] - 0.01)
        # complex: either separates or observability marks uncertainty
        complex_rows = [r for r in all_ring_rows if r["family"] == "complex"]
        complex_ok = True
        for r in complex_rows:
            d = r["candidates"][cand]["delta"]
            obs = r["observability"]["base"]
            if d <= 0.02 and obs >= 0.5:
                complex_ok = False
            # if not separable, require low observability
            if d <= 0.02 and obs < 0.5:
                complex_ok = True
        gt_drop = all(r["gt_shifted"] < r["gt_base"] - 0.05 for r in all_ring_rows)

        all_ok = (
            four_ok
            and all(sep_all)
            and sum(sep_single) >= 2
            and complex_ok
            and gt_drop
        )
        lines.append(
            f"- Candidate `{cand}`: four_ok={four_ok}, "
            f"all-ring sep (non-complex)={sep_all}, "
            f"single-ring sep count={sum(sep_single)}/{len(sep_single)}, "
            f"complex_ok={complex_ok}, gt_drop={gt_drop} → "
            f"{'PASS' if all_ok else 'fail'}"
        )
        if all_ok and not decision["passed"]:
            decision = {
                "passed": True,
                "feature": cand,
                "reason": "first candidate meeting Stage-2 criteria",
            }

    lines.append("")
    if decision["passed"]:
        lines.append(f"**Selected scored feature: `{decision['feature']}`**")
        lines.append("")
        lines.append("Proceed to Stage 3 (five-feature proxy).")
    else:
        lines.append("**No candidate passed. Stop; do not rerun LLM/random arms.**")
        decision["reason"] = "no candidate met separation + invariance criteria"

    lines.extend([""] + natural_lines)

    (RELEASE3_DATA / "rotation_synth" / "gate_rows.json").write_text(
        json.dumps({"rows": rows, "decision": decision}, indent=2, default=float) + "\n",
        encoding="utf-8",
    )
    GATE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(GATE.read_text())
    return 0 if decision["passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
