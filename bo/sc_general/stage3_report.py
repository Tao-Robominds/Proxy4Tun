#!/usr/bin/env python3
"""Aggregate SC-general Stage-3 refinement results into report + CSV.

Usage:
  ./venv/bin/python bo/sc_general/stage3_report.py
  ./venv/bin/python bo/sc_general/stage3_report.py --arm fable
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from bo.sc_general.refine_pilot import VALID_ARMS  # noqa: E402
from bo.sc_general.score_scaled import band  # noqa: E402
from bo.sc_general.select_round import select_dir_for  # noqa: E402
from bo.runtime.spaces import FAMILY_MODE, family_of_subset  # noqa: E402

STAGE3 = _REPO / "data" / "sc-general" / "stage3"
HOLDOUT = _REPO / "data" / "sc-general" / "stage2" / "holdout_scores.csv"

# Label-free refine band (proxy only); order: family then ascending proxy.
PANEL = [
    "1-3", "1-5", "1-1", "1-4", "1-2", "2-4", "2-2",
    "3-4", "3-3", "3-7", "3-8", "3-10", "3-9", "3-6",
    "4-3", "4-2", "4-1", "4-5", "5-5", "5-3", "5-2", "5-4",
]
PAPER_NINE = ["1-4", "1-5", "2-2", "3-2", "3-4", "3-5", "4-1", "4-3", "4-4"]
PAPER_REFINE_START = 0.569
PAPER_REFINE_END = 0.675
PAPER_PANEL27_ANCHOR = 0.722
PAPER_PANEL27_REFINED = 0.757


def _paths_for_arm(arm: str) -> tuple[Path, Path, Path]:
    select_dir = select_dir_for(arm)
    if arm == "fable":
        return select_dir, STAGE3 / "refined_scores_fable.csv", STAGE3 / "report_fable.md"
    if arm == "fable_fresh":
        return (
            select_dir,
            STAGE3 / "refined_scores_fable_fresh.csv",
            STAGE3 / "report_fable_fresh.md",
        )
    if arm == "gpt56":
        return select_dir, STAGE3 / "refined_scores_gpt56.csv", STAGE3 / "report_gpt56.md"
    if arm == "gemini38":
        return (
            select_dir,
            STAGE3 / "refined_scores_gemini38.csv",
            STAGE3 / "report_gemini38.md",
        )
    if arm == "random":
        return (
            select_dir,
            STAGE3 / "refined_scores_random.csv",
            STAGE3 / "report_random.md",
        )
    return select_dir, STAGE3 / "refined_scores.csv", STAGE3 / "report.md"


def _load_selection(subset: str, select_dir: Path) -> dict[str, Any] | None:
    path = select_dir / f"{subset}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def build_tables(arm: str = "scgen") -> tuple[pd.DataFrame, pd.DataFrame]:
    select_dir, _, _ = _paths_for_arm(arm)
    hs = pd.read_csv(HOLDOUT)
    anchors = hs[hs["config_kind"] == "anchor"].copy()
    rows = []
    for _, a in anchors.iterrows():
        subset = str(a["subset"])
        fam = family_of_subset(subset)
        mode = FAMILY_MODE[fam]
        sel = _load_selection(subset, select_dir)
        in_panel = subset in PANEL
        if sel is None:
            # Non-panel / unfinished: keep anchor as selected.
            proxy_a = float(a["proxy"])
            miou_a = float(a["mIoU"])
            rows.append(
                {
                    "subset": subset,
                    "family": mode,
                    "arm": arm,
                    "in_panel": in_panel,
                    "anchor_proxy": proxy_a,
                    "anchor_band": band(proxy_a),
                    "anchor_mIoU": miou_a,
                    "selected_round": "anchor",
                    "selected_proxy": proxy_a,
                    "selected_mIoU": miou_a,
                    "delta_proxy": 0.0,
                    "delta_mIoU": 0.0,
                    "refined": False,
                    "gt_good": miou_a >= 0.7,
                    "selection_reason": "not refined (out of band or missing selection)",
                }
            )
            continue
        a_proxy = float(sel["anchor"]["proxy_scaled"])
        a_miou = float(sel["anchor"]["mIoU"])
        s = sel["selected"]
        s_proxy = float(s["proxy_scaled"])
        s_miou = float(s["mIoU"]) if s.get("mIoU") is not None else float("nan")
        refined = s["round"] != "anchor"
        rows.append(
            {
                "subset": subset,
                "family": mode,
                "arm": arm,
                "in_panel": in_panel,
                "anchor_proxy": a_proxy,
                "anchor_band": sel["anchor"]["band"],
                "anchor_mIoU": a_miou,
                "selected_round": s["round"],
                "selected_proxy": s_proxy,
                "selected_mIoU": s_miou,
                "delta_proxy": float(sel["delta_proxy_scaled"]),
                "delta_mIoU": float(sel["delta_mIoU_offline"])
                if sel.get("delta_mIoU_offline") is not None
                else float("nan"),
                "refined": refined,
                "gt_good": a_miou >= 0.7,
                "selection_reason": sel["selection_reason"],
            }
        )
    df = pd.DataFrame(rows).sort_values("subset")
    panel = df[df["in_panel"]].copy()
    return df, panel


def write_report(
    df: pd.DataFrame, panel: pd.DataFrame, *, arm: str, out_md: Path, out_csv: Path
) -> None:
    select_dir, _, _ = _paths_for_arm(arm)
    n_panel = len(panel)
    n_sel = int(panel["refined"].sum()) if n_panel else 0
    mean_a_proxy = float(panel["anchor_proxy"].mean()) if n_panel else float("nan")
    mean_s_proxy = float(panel["selected_proxy"].mean()) if n_panel else float("nan")
    mean_a_miou = float(panel["anchor_mIoU"].mean()) if n_panel else float("nan")
    mean_s_miou = float(panel["selected_mIoU"].mean()) if n_panel else float("nan")

    good = panel[panel["gt_good"]] if n_panel else panel
    harm = good[good["delta_mIoU"] < -1e-6] if len(good) else good
    improve = panel[panel["delta_mIoU"] > 1e-6] if n_panel else panel
    worsen = panel[panel["delta_mIoU"] < -1e-6] if n_panel else panel

    changed = panel[panel["refined"]] if n_panel else panel
    same_dir = 0
    for _, r in changed.iterrows():
        if np.sign(r["delta_proxy"]) == np.sign(r["delta_mIoU"]) and abs(r["delta_mIoU"]) > 1e-9:
            same_dir += 1

    mean27_anchor = float(df["anchor_mIoU"].mean()) if len(df) else float("nan")
    mean27_refined = float(df["selected_mIoU"].mean()) if len(df) else float("nan")

    paper_in = [s for s in PAPER_NINE if s in set(panel["subset"])] if n_panel else []
    paper_df = panel[panel["subset"].isin(paper_in)] if paper_in else panel.iloc[0:0]

    if arm == "gemini38":
        arm_label = "Gemini-3.8 (fresh per-case agent)"
        out_root_pat = "`data/<subset>-scgen-gemini38-refinement/`"
        campaign_log = "campaign_gemini38.md"
        gate_log = "gate_gemini38.md"
    elif arm == "gpt56":
        arm_label = "GPT-5.6 (fresh per-case agent)"
        out_root_pat = "`data/<subset>-scgen-gpt56-refinement/`"
        campaign_log = "campaign_gpt56.md"
        gate_log = "gate_gpt56.md"
    elif arm == "fable_fresh":
        arm_label = "Fable-5.1 (fresh per-case agent)"
        out_root_pat = "`data/refinement/fable_fresh/<subset>/`"
        campaign_log = "campaign_fable_fresh.md"
        gate_log = "gate_fable_fresh.md"
    elif arm == "fable":
        arm_label = "Fable-5 live LLM"
        out_root_pat = "`data/<subset>-scgen-fable-refinement/`"
        campaign_log = "campaign_fable.md"
        gate_log = "gate_fable.md"
    else:
        arm_label = "deterministic recipes"
        out_root_pat = "`data/<subset>-scgen-refinement/`"
        campaign_log = "campaign.md"
        gate_log = "gate.md"

    lines = [
        f"# Stage 3 report — SC-general label-free self-refinement (arm `{arm}`)",
        "",
        f"Generated: {datetime.now().isoformat()}",
        "",
        "## Setup",
        "",
        "- Proxy: `bo/sc_general/models.json` pruned_lean "
        "(`correspondence_f1@15`, `sam_fill_rate`, `ring_count_error`, `depth_nan_ratio`).",
        f"- Proposer: **{arm_label}**.",
        "- Panel: all 27 holdout anchors with **proxy ∈ [0.5, 0.7]** (no GT bound).",
        f"- Panel size: **{n_panel}** cases; 3 rounds each; monotone-accept selection.",
        f"- Outputs under {out_root_pat}; summaries in `data/sc-general/stage3/`.",
        "",
        "## Panel outcomes",
        "",
        f"| metric | value |",
        f"|---|---:|",
        f"| cases refined (selected ≠ anchor) | {n_sel}/{n_panel} |",
        f"| mean anchor proxy | {mean_a_proxy:.3f} |",
        f"| mean selected proxy | {mean_s_proxy:.3f} |",
        f"| mean anchor mIoU (offline) | {mean_a_miou:.3f} |",
        f"| mean selected mIoU (offline) | {mean_s_miou:.3f} |",
        f"| Δ mean mIoU | {mean_s_miou - mean_a_miou:+.3f} |",
        f"| cases with mIoU↑ | {len(improve)} |",
        f"| cases with mIoU↓ | {len(worsen)} |",
        "",
        "### Harm on GT-good anchors (anchor mIoU ≥ 0.7)",
        "",
        f"- GT-good in panel: {len(good)}",
        f"- GT drops among them: **{len(harm)}** "
        f"(mean Δ mIoU = {float(harm['delta_mIoU'].mean()) if len(harm) else 0.0:+.3f})",
        "",
        "### 27-subset means (replace refined selections into full holdout anchors)",
        "",
        f"- Anchor-only mean mIoU: **{mean27_anchor:.3f}** (paper reported {PAPER_PANEL27_ANCHOR})",
        f"- After refinement mean mIoU: **{mean27_refined:.3f}** (paper reported {PAPER_PANEL27_REFINED})",
        "",
        "### vs paper nine-case PoC",
        "",
        f"- Paper: {PAPER_REFINE_START:.3f} → {PAPER_REFINE_END:.3f} on 9 GT-filtered cases.",
        f"- Overlap still in this label-free band: {paper_in}",
        (
            f"- Overlap mean mIoU: {float(paper_df['anchor_mIoU'].mean()):.3f} → "
            f"{float(paper_df['selected_mIoU'].mean()):.3f}"
            if len(paper_df)
            else "- Overlap: none"
        ),
        "",
        "## Per-case table (panel)",
        "",
        "| subset | family | anchor proxy | anchor mIoU | selected | sel proxy | sel mIoU | Δproxy | ΔmIoU |",
        "|---|---|---:|---:|---|---:|---:|---:|---:|",
    ]
    if n_panel:
        for _, r in panel.sort_values(["family", "anchor_proxy"]).iterrows():
            lines.append(
                f"| {r['subset']} | {r['family']} | {r['anchor_proxy']:.3f} | {r['anchor_mIoU']:.3f} | "
                f"{r['selected_round']} | {r['selected_proxy']:.3f} | {r['selected_mIoU']:.3f} | "
                f"{r['delta_proxy']:+.3f} | {r['delta_mIoU']:+.3f} |"
            )

    lines += [
        "",
        "## Direction agreement (refined cases)",
        "",
        f"- Refined cases: {len(changed)}",
        f"- Proxy and GT move same direction: {same_dir}/{len(changed) if len(changed) else 1}",
        "",
        "## Artefacts",
        "",
        f"- Selections: `{select_dir}/`",
        f"- CSV: `{out_csv}`",
        f"- Campaign log: `{STAGE3 / campaign_log}`",
        f"- Gate: `{STAGE3 / gate_log}`",
        "",
    ]
    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--arm", default="scgen", choices=VALID_ARMS)
    args = p.parse_args()
    STAGE3.mkdir(parents=True, exist_ok=True)
    select_dir, out_csv, out_md = _paths_for_arm(args.arm)
    df, panel = build_tables(args.arm)
    df.to_csv(out_csv, index=False)
    write_report(df, panel, arm=args.arm, out_md=out_md, out_csv=out_csv)
    print(f"wrote {out_csv} ({len(df)} rows; panel={len(panel)}; arm={args.arm})")
    print(f"wrote {out_md}")
    if len(panel):
        print(
            f"panel mean mIoU {panel['anchor_mIoU'].mean():.3f} -> {panel['selected_mIoU'].mean():.3f} "
            f"(refined {int(panel['refined'].sum())}/{len(panel)})"
        )


if __name__ == "__main__":
    main()
