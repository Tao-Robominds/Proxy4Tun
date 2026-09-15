#!/usr/bin/env python3
"""Compare Stage-3 arms: anchor / scgen-det / fable / legacy paper Fable.

Writes:
  data/sc-general/stage3/arm_comparison.md
  data/sc-general/stage3/region_comparison_fable.csv

Usage:
  ./venv/bin/python bo/sc_general/compare_arms.py
  ./venv/bin/python bo/sc_general/compare_arms.py --phase-a-only
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

from bo.sc_general.stage3_report import PANEL, build_tables  # noqa: E402

STAGE3 = _REPO / "data" / "sc-general" / "stage3"
LEGACY_CSV = _REPO / "bo" / "proxy_scale" / "refined_scores.csv"
HOLDOUT = _REPO / "data" / "sc-general" / "stage2" / "holdout_scores.csv"

DUAL_BAND = ["1-4", "1-5", "2-2", "3-4", "4-1", "4-3"]
PHASE_B = [s for s in PANEL if s not in DUAL_BAND]

# Region definitions keyed by subset lists (computed from holdout anchors).
PAPER_NINE = ["1-4", "1-5", "2-2", "3-2", "3-4", "3-5", "4-1", "4-3", "4-4"]

# Manuscript PoC table (legacy proxy). Selected mIoU only; Δ recomputed vs
# SC-general anchor mIoU. 4-4 baseline in some drafts was mistyped as 0.647;
# the true anchor is 0.347 (legacy Fable selected 0.700).
PAPER_NINE_LEGACY = {
    "4-4": {"fable5": 0.700, "gpt56": 0.422},
    "1-5": {"fable5": 0.782, "gpt56": 0.437},
    "1-4": {"fable5": 0.786, "gpt56": 0.556},
    "3-2": {"fable5": 0.719, "gpt56": 0.747},
    "4-3": {"fable5": 0.544, "gpt56": 0.516},
    "4-1": {"fable5": 0.659, "gpt56": 0.659},
    "3-4": {"fable5": 0.631, "gpt56": 0.622},
    "3-5": {"fable5": 0.588, "gpt56": 0.713},
    "2-2": {"fable5": 0.668, "gpt56": 0.586},
}


def _load_legacy() -> pd.DataFrame:
    df = pd.read_csv(LEGACY_CSV)
    df = df.rename(
        columns={
            "selected_mIoU": "legacy_mIoU",
            "delta_mIoU": "legacy_delta_mIoU",
            "selected_proxy_scaled": "legacy_proxy",
            "selected_round": "legacy_round",
            "arm": "legacy_arm",
            "anchor_mIoU": "legacy_anchor_mIoU",
            "anchor_proxy_scaled": "legacy_anchor_proxy",
        }
    )
    keep = [
        "subset",
        "legacy_arm",
        "legacy_round",
        "legacy_anchor_proxy",
        "legacy_anchor_mIoU",
        "legacy_proxy",
        "legacy_mIoU",
        "legacy_delta_mIoU",
    ]
    return df[keep]


def _arm_frame(arm: str) -> pd.DataFrame:
    df, _ = build_tables(arm)
    if arm == "scgen":
        prefix = "det"
    elif arm == "fable":
        prefix = "fable"
    elif arm == "fable_fresh":
        prefix = "fable_fresh"
    elif arm == "gpt56":
        prefix = "gpt56"
    elif arm == "gemini38":
        prefix = "gemini38"
    else:
        prefix = arm
    out = df[
        [
            "subset",
            "family",
            "in_panel",
            "anchor_proxy",
            "anchor_mIoU",
            "selected_round",
            "selected_proxy",
            "selected_mIoU",
            "delta_proxy",
            "delta_mIoU",
            "refined",
        ]
    ].copy()
    out = out.rename(
        columns={
            "selected_round": f"{prefix}_round",
            "selected_proxy": f"{prefix}_proxy",
            "selected_mIoU": f"{prefix}_mIoU",
            "delta_proxy": f"{prefix}_delta_proxy",
            "delta_mIoU": f"{prefix}_delta_mIoU",
            "refined": f"{prefix}_refined",
        }
    )
    return out


def build_comparison(
    *,
    with_gpt56: bool = False,
    with_gemini38: bool = False,
    with_random: bool = False,
) -> pd.DataFrame:
    det = _arm_frame("scgen")
    fable = _arm_frame("fable")
    # Prefer anchor columns from det (same anchors); drop fable duplicates.
    fable = fable.drop(columns=["family", "in_panel", "anchor_proxy", "anchor_mIoU"])
    merged = det.merge(fable, on="subset", how="outer")
    if with_gpt56 or with_gemini38 or with_random:
        gpt = _arm_frame("gpt56").drop(
            columns=["family", "in_panel", "anchor_proxy", "anchor_mIoU"]
        )
        merged = merged.merge(gpt, on="subset", how="outer")
    if with_gemini38 or with_random:
        gem = _arm_frame("gemini38").drop(
            columns=["family", "in_panel", "anchor_proxy", "anchor_mIoU"]
        )
        merged = merged.merge(gem, on="subset", how="outer")
    if with_random:
        rnd = _arm_frame("random").drop(
            columns=["family", "in_panel", "anchor_proxy", "anchor_mIoU"]
        )
        merged = merged.merge(rnd, on="subset", how="outer")
    legacy = _load_legacy()
    merged = merged.merge(legacy, on="subset", how="left")
    return merged.sort_values("subset")


def _region_stats(
    df: pd.DataFrame, cases: list[str], region: str, *, arm_prefix: str = "fable"
) -> dict[str, Any]:
    sub = df[df["subset"].isin(cases)].copy()
    n = len(sub)
    refined_col = f"{arm_prefix}_refined"
    delta_col = f"{arm_prefix}_delta_mIoU"
    miou_col = f"{arm_prefix}_mIoU"
    dproxy_col = f"{arm_prefix}_delta_proxy"
    if n == 0:
        return {
            "region": region,
            "n": 0,
            "cases": "",
            "n_refined": np.nan,
            "n_miou_up": np.nan,
            "n_miou_down": np.nan,
            "mean_a_miou": np.nan,
            "mean_s_miou": np.nan,
            "delta_mean": np.nan,
            "mean_delta": np.nan,
            "median_delta": np.nan,
            "mean_delta_proxy": np.nan,
            "frac_improved": np.nan,
            "delta_when_refined": np.nan,
        }
    refined = sub[sub[refined_col].fillna(False)]
    up = sub[sub[delta_col] > 1e-6]
    down = sub[sub[delta_col] < -1e-6]
    mean_a = float(sub["anchor_mIoU"].mean())
    mean_s = float(sub[miou_col].mean())
    deltas = sub[delta_col].astype(float)
    dproxy = sub[dproxy_col].astype(float)
    return {
        "region": region,
        "n": n,
        "cases": ", ".join(sorted(cases)),
        "n_refined": float(len(refined)),
        "n_miou_up": float(len(up)),
        "n_miou_down": float(len(down)),
        "mean_a_miou": mean_a,
        "mean_s_miou": mean_s,
        "delta_mean": mean_s - mean_a,
        "mean_delta": float(deltas.mean()),
        "median_delta": float(deltas.median()),
        "mean_delta_proxy": float(dproxy.mean()),
        "frac_improved": float(len(up) / n),
        "delta_when_refined": float(refined[delta_col].mean()) if len(refined) else np.nan,
    }


def build_regions(
    comp: pd.DataFrame, *, arm_prefix: str = "fable"
) -> pd.DataFrame:
    # Use SC-general anchor proxy / mIoU from the comparison frame.
    hs = pd.read_csv(HOLDOUT)
    anchors = hs[hs["config_kind"] == "anchor"].set_index("subset")

    def band_cases(proxy_lo=None, proxy_hi=None, gt_lo=None, gt_hi=None, gt_min=None, gt_max=None):
        cases = []
        for subset, row in anchors.iterrows():
            p = float(row["proxy"])
            g = float(row["mIoU"])
            if proxy_lo is not None and not (p >= proxy_lo):
                continue
            if proxy_hi is not None and not (p < proxy_hi):
                continue
            if gt_lo is not None and not (g >= gt_lo):
                continue
            if gt_hi is not None and not (g < gt_hi):
                continue
            if gt_min is not None and not (g >= gt_min):
                continue
            if gt_max is not None and not (g < gt_max):
                continue
            cases.append(str(subset))
        return cases

    # Match prior region_comparison.csv definitions.
    regions = [
        ("A: manuscript PoC (proxy∈[0.5,0.7] ∩ GT∈[0.5,0.7])",
         band_cases(0.5, 0.7, gt_lo=0.5, gt_hi=0.7)),
        ("B: proxy refine ∩ GT-good (proxy∈[0.5,0.7] ∩ GT≥0.7)",
         band_cases(0.5, 0.7, gt_min=0.7)),
        ("C: proxy refine ∩ GT-low (proxy∈[0.5,0.7] ∩ GT<0.5)",
         band_cases(0.5, 0.7, gt_max=0.5)),
        ("D: all label-free refine panel (proxy∈[0.5,0.7])",
         band_cases(0.5, 0.7)),
        ("E: mid-proxy / mid-GT tight (proxy∈[0.55,0.65] ∩ GT∈[0.5,0.7])",
         band_cases(0.55, 0.65, gt_lo=0.5, gt_hi=0.7)),
        ("F: high-proxy edge of band (proxy∈[0.65,0.7])",
         band_cases(0.65, 0.7)),
        ("G: low-proxy edge of band (proxy∈[0.5,0.55])",
         band_cases(0.5, 0.55)),
        ("H: reject band (proxy<0.5) — not refined",
         band_cases(proxy_hi=0.5)),
        ("I: accept band (proxy≥0.7) — not refined",
         [s for s, r in anchors.iterrows() if float(r["proxy"]) >= 0.7]),
        ("J: paper nine (legacy definition)", PAPER_NINE),
        ("K: paper nine ∩ in this run's panel",
         [s for s in PAPER_NINE if s in set(PANEL)]),
    ]
    rows = [_region_stats(comp, cases, name, arm_prefix=arm_prefix) for name, cases in regions]
    return pd.DataFrame(rows)


def write_markdown_gpt56(comp: pd.DataFrame, regions: pd.DataFrame) -> Path:
    """Full four-arm comparison including GPT-5.6."""
    sub = comp[comp["subset"].isin(PANEL)].copy()

    def _fmt(x: Any, nd: int = 3) -> str:
        if x is None or (isinstance(x, float) and (np.isnan(x) or np.isinf(x))):
            return "—"
        try:
            return f"{float(x):.{nd}f}"
        except (TypeError, ValueError):
            return str(x)

    lines = [
        "# Stage 3 arm comparison — SC-general (with GPT-5.6)",
        "",
        f"Generated: {datetime.now().isoformat()}",
        "",
        "## Arms",
        "",
        "- **anchor**: frozen SC-general holdout anchors (no refinement).",
        "- **scgen-det**: deterministic Stage-3 recipes (`run_campaign.propose`).",
        "- **fable**: Fable-5.1 (Cursor agent, live) GT-blind-by-protocol proposals.",
        "- **gpt56**: GPT-5.6 (fresh per-case agent) with sanitized packets and "
        "a stronger information barrier than the same-session Fable arm.",
        "",
        "## Per-case table (22-case proxy-only panel)",
        "",
        "| subset | family | a_proxy | a_mIoU | det | Δdet | fable | Δfable | gpt56 | Δgpt56 |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for _, r in sub.sort_values(["family", "anchor_proxy"]).iterrows():
        lines.append(
            f"| {r['subset']} | {r['family']} | {_fmt(r['anchor_proxy'])} | {_fmt(r['anchor_mIoU'])} | "
            f"{_fmt(r.get('det_mIoU'))} | {_fmt(r.get('det_delta_mIoU'), 3)} | "
            f"{_fmt(r.get('fable_mIoU'))} | {_fmt(r.get('fable_delta_mIoU'), 3)} | "
            f"{_fmt(r.get('gpt56_mIoU'))} | {_fmt(r.get('gpt56_delta_mIoU'), 3)} |"
        )

    def mean_delta(col: str) -> float:
        return float(sub[col].astype(float).mean()) if col in sub and len(sub) else float("nan")

    lines += [
        "",
        "### Panel means",
        "",
        "| arm | mean selected mIoU | mean ΔmIoU | n refined |",
        "|---|---:|---:|---:|",
        f"| anchor | {_fmt(sub['anchor_mIoU'].mean())} | 0.000 | 0 |",
        f"| scgen-det | {_fmt(sub['det_mIoU'].mean())} | {_fmt(mean_delta('det_delta_mIoU'))} | "
        f"{int(sub['det_refined'].fillna(False).sum())} |",
        f"| fable | {_fmt(sub['fable_mIoU'].mean())} | {_fmt(mean_delta('fable_delta_mIoU'))} | "
        f"{int(sub['fable_refined'].fillna(False).sum())} |",
        f"| gpt56 | {_fmt(sub['gpt56_mIoU'].mean())} | {_fmt(mean_delta('gpt56_delta_mIoU'))} | "
        f"{int(sub['gpt56_refined'].fillna(False).sum())} |",
        "",
        "### Dual mid-band (retrospective only)",
        "",
    ]
    dual = comp[comp["subset"].isin(DUAL_BAND)].copy()
    if len(dual):
        lines += [
            "| arm | mean mIoU | mean ΔmIoU |",
            "|---|---:|---:|",
            f"| anchor | {_fmt(dual['anchor_mIoU'].mean())} | 0.000 |",
            f"| scgen-det | {_fmt(dual['det_mIoU'].mean())} | {_fmt(float(dual['det_delta_mIoU'].mean()))} |",
            f"| fable | {_fmt(dual['fable_mIoU'].mean())} | {_fmt(float(dual['fable_delta_mIoU'].mean()))} |",
            f"| gpt56 | {_fmt(dual['gpt56_mIoU'].mean())} | {_fmt(float(dual['gpt56_delta_mIoU'].mean()))} |",
            "",
        ]

    # Family outcomes + harms
    lines += [
        "## Family outcomes (gpt56)",
        "",
        "| family | n | mean a_mIoU | mean gpt56 | Δmean | n refined |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for fam, g in sub.groupby("family"):
        lines.append(
            f"| {fam} | {len(g)} | {_fmt(g['anchor_mIoU'].mean())} | "
            f"{_fmt(g['gpt56_mIoU'].mean())} | {_fmt(float(g['gpt56_delta_mIoU'].mean()), 3)} | "
            f"{int(g['gpt56_refined'].fillna(False).sum())} |"
        )

    good = sub[sub["anchor_mIoU"] >= 0.7]
    harm = good[good["gpt56_delta_mIoU"] < -1e-6] if len(good) else good
    lines += [
        "",
        "## Harm on GT-good anchors (gpt56; anchor mIoU ≥ 0.7)",
        "",
        f"- GT-good in panel: {len(good)}",
        f"- GT drops among them: **{len(harm)}** "
        f"(mean Δ = {_fmt(float(harm['gpt56_delta_mIoU'].mean()) if len(harm) else 0.0, 3)})",
        "",
        "## Region comparison (gpt56 arm)",
        "",
        "| region | n | n_refined | n↑ | n↓ | mean a_mIoU | mean s_mIoU | Δmean | frac↑ |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for _, r in regions.iterrows():
        lines.append(
            f"| {r['region']} | {int(r['n'])} | {_fmt(r['n_refined'], 0)} | "
            f"{_fmt(r['n_miou_up'], 0)} | {_fmt(r['n_miou_down'], 0)} | "
            f"{_fmt(r['mean_a_miou'])} | {_fmt(r['mean_s_miou'])} | "
            f"{_fmt(r['delta_mean'])} | {_fmt(r['frac_improved'])} |"
        )

    lines += [
        "",
        "## Artefacts",
        "",
        f"- Det selections: `{STAGE3 / 'selections'}/`",
        f"- Fable selections: `{STAGE3 / 'selections-fable'}/`",
        f"- GPT-5.6 selections: `{STAGE3 / 'selections-gpt56'}/`",
        f"- GPT-5.6 report: `{STAGE3 / 'report_gpt56.md'}`",
        f"- Region CSV: `{STAGE3 / 'region_comparison_gpt56.csv'}`",
        f"- Campaign: `{STAGE3 / 'campaign_gpt56.md'}`",
        "",
    ]
    out = STAGE3 / "arm_comparison_gpt56.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out


def write_markdown_gemini38(comp: pd.DataFrame, regions: pd.DataFrame) -> Path:
    """Five-arm comparison including Gemini 3.8."""
    sub = comp[comp["subset"].isin(PANEL)].copy()

    def _fmt(x: Any, nd: int = 3) -> str:
        if x is None or (isinstance(x, float) and (np.isnan(x) or np.isinf(x))):
            return "—"
        try:
            return f"{float(x):.{nd}f}"
        except (TypeError, ValueError):
            return str(x)

    lines = [
        "# Stage 3 arm comparison — SC-general (with Gemini 3.8)",
        "",
        f"Generated: {datetime.now().isoformat()}",
        "",
        "## Arms",
        "",
        "- **anchor**: frozen SC-general holdout anchors (no refinement).",
        "- **scgen-det**: deterministic Stage-3 recipes (`run_campaign.propose`).",
        "- **fable**: Fable-5.1 (Cursor agent, live) GT-blind-by-protocol proposals.",
        "- **gpt56**: GPT-5.6 (fresh per-case agent) with sanitized packets.",
        "- **gemini38**: Gemini 3.8 (fresh per-case agent, `model=inherit`) with "
        "sanitized packets and the same information barrier as GPT-5.6.",
        "",
        "## Per-case table (22-case proxy-only panel)",
        "",
        "| subset | family | a_proxy | a_mIoU | det | Δdet | fable | Δfable | gpt56 | Δgpt56 | gemini38 | Δgemini |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for _, r in sub.sort_values(["family", "anchor_proxy"]).iterrows():
        lines.append(
            f"| {r['subset']} | {r['family']} | {_fmt(r['anchor_proxy'])} | {_fmt(r['anchor_mIoU'])} | "
            f"{_fmt(r.get('det_mIoU'))} | {_fmt(r.get('det_delta_mIoU'), 3)} | "
            f"{_fmt(r.get('fable_mIoU'))} | {_fmt(r.get('fable_delta_mIoU'), 3)} | "
            f"{_fmt(r.get('gpt56_mIoU'))} | {_fmt(r.get('gpt56_delta_mIoU'), 3)} | "
            f"{_fmt(r.get('gemini38_mIoU'))} | {_fmt(r.get('gemini38_delta_mIoU'), 3)} |"
        )

    def mean_delta(col: str) -> float:
        return float(sub[col].astype(float).mean()) if col in sub and len(sub) else float("nan")

    lines += [
        "",
        "### Panel means",
        "",
        "| arm | mean selected mIoU | mean ΔmIoU | n refined |",
        "|---|---:|---:|---:|",
        f"| anchor | {_fmt(sub['anchor_mIoU'].mean())} | 0.000 | 0 |",
        f"| scgen-det | {_fmt(sub['det_mIoU'].mean())} | {_fmt(mean_delta('det_delta_mIoU'))} | "
        f"{int(sub['det_refined'].fillna(False).sum())} |",
        f"| fable | {_fmt(sub['fable_mIoU'].mean())} | {_fmt(mean_delta('fable_delta_mIoU'))} | "
        f"{int(sub['fable_refined'].fillna(False).sum())} |",
        f"| gpt56 | {_fmt(sub['gpt56_mIoU'].mean())} | {_fmt(mean_delta('gpt56_delta_mIoU'))} | "
        f"{int(sub['gpt56_refined'].fillna(False).sum())} |",
        f"| gemini38 | {_fmt(sub['gemini38_mIoU'].mean())} | {_fmt(mean_delta('gemini38_delta_mIoU'))} | "
        f"{int(sub['gemini38_refined'].fillna(False).sum())} |",
        "",
        "### Dual mid-band (retrospective only)",
        "",
    ]
    dual = comp[comp["subset"].isin(DUAL_BAND)].copy()
    if len(dual):
        lines += [
            "| arm | mean mIoU | mean ΔmIoU |",
            "|---|---:|---:|",
            f"| anchor | {_fmt(dual['anchor_mIoU'].mean())} | 0.000 |",
            f"| scgen-det | {_fmt(dual['det_mIoU'].mean())} | {_fmt(float(dual['det_delta_mIoU'].mean()))} |",
            f"| fable | {_fmt(dual['fable_mIoU'].mean())} | {_fmt(float(dual['fable_delta_mIoU'].mean()))} |",
            f"| gpt56 | {_fmt(dual['gpt56_mIoU'].mean())} | {_fmt(float(dual['gpt56_delta_mIoU'].mean()))} |",
            f"| gemini38 | {_fmt(dual['gemini38_mIoU'].mean())} | {_fmt(float(dual['gemini38_delta_mIoU'].mean()))} |",
            "",
        ]

    lines += [
        "## Family outcomes (gemini38)",
        "",
        "| family | n | mean a_mIoU | mean gemini38 | Δmean | n refined |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for fam, g in sub.groupby("family"):
        lines.append(
            f"| {fam} | {len(g)} | {_fmt(g['anchor_mIoU'].mean())} | "
            f"{_fmt(g['gemini38_mIoU'].mean())} | {_fmt(float(g['gemini38_delta_mIoU'].mean()), 3)} | "
            f"{int(g['gemini38_refined'].fillna(False).sum())} |"
        )

    good = sub[sub["anchor_mIoU"] >= 0.7]
    harm = good[good["gemini38_delta_mIoU"] < -1e-6] if len(good) else good
    lines += [
        "",
        "## Harm on GT-good anchors (gemini38; anchor mIoU ≥ 0.7)",
        "",
        f"- GT-good in panel: {len(good)}",
        f"- GT drops among them: **{len(harm)}** "
        f"(mean Δ = {_fmt(float(harm['gemini38_delta_mIoU'].mean()) if len(harm) else 0.0, 3)})",
        "",
        "## Region comparison (gemini38 arm)",
        "",
        "| region | n | n_refined | n↑ | n↓ | mean a_mIoU | mean s_mIoU | Δmean | frac↑ |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for _, r in regions.iterrows():
        lines.append(
            f"| {r['region']} | {int(r['n'])} | {_fmt(r['n_refined'], 0)} | "
            f"{_fmt(r['n_miou_up'], 0)} | {_fmt(r['n_miou_down'], 0)} | "
            f"{_fmt(r['mean_a_miou'])} | {_fmt(r['mean_s_miou'])} | "
            f"{_fmt(r['delta_mean'])} | {_fmt(r['frac_improved'])} |"
        )

    lines += [
        "",
        "## Artefacts",
        "",
        f"- Det selections: `{STAGE3 / 'selections'}/`",
        f"- Fable selections: `{STAGE3 / 'selections-fable'}/`",
        f"- GPT-5.6 selections: `{STAGE3 / 'selections-gpt56'}/`",
        f"- Gemini 3.8 selections: `{STAGE3 / 'selections-gemini38'}/`",
        f"- Gemini 3.8 report: `{STAGE3 / 'report_gemini38.md'}`",
        f"- Region CSV: `{STAGE3 / 'region_comparison_gemini38.csv'}`",
        f"- Campaign: `{STAGE3 / 'campaign_gemini38.md'}`",
        "",
    ]
    out = STAGE3 / "arm_comparison_gemini38.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out


def write_markdown(comp: pd.DataFrame, regions: pd.DataFrame, *, phase_a_only: bool) -> Path:
    focus = DUAL_BAND if phase_a_only else PANEL
    sub = comp[comp["subset"].isin(focus)].copy()

    def _fmt(x: Any, nd: int = 3) -> str:
        if x is None or (isinstance(x, float) and (np.isnan(x) or np.isinf(x))):
            return "—"
        try:
            return f"{float(x):.{nd}f}"
        except (TypeError, ValueError):
            return str(x)

    lines = [
        "# Stage 3 arm comparison — SC-general",
        "",
        f"Generated: {datetime.now().isoformat()}",
        "",
        "## Arms",
        "",
        "- **anchor**: frozen SC-general holdout anchors (no refinement).",
        "- **scgen-det**: deterministic Stage-3 recipes (`run_campaign.propose`).",
        "- **fable**: Fable-5 (Cursor agent, live) GT-blind-by-protocol proposals.",
        "- **legacy**: paper reflection campaign (`bo/proxy_scale/refined_scores.csv`, "
        "older proxy).",
        "",
        "### Protocol caveat",
        "",
        "Fable-5 proposals never read `offline_gt.json` / `performance.md` / band CSVs "
        "during the loop. The proposer has seen aggregate GT for these cases earlier in "
        "the session, so this arm is **GT-blind by protocol**, not by information barrier.",
        "",
        f"## Per-case table ({'Phase A dual-band' if phase_a_only else 'full panel'})",
        "",
        "| subset | family | a_proxy | a_mIoU | det_round | det_mIoU | Δdet | "
        "fable_round | fable_mIoU | Δfable | legacy_arm | legacy_mIoU | Δlegacy |",
        "|---|---|---:|---:|---|---:|---:|---|---:|---:|---|---:|---:|",
    ]
    for _, r in sub.sort_values(["family", "anchor_proxy"]).iterrows():
        lines.append(
            f"| {r['subset']} | {r['family']} | {_fmt(r['anchor_proxy'])} | {_fmt(r['anchor_mIoU'])} | "
            f"{r.get('det_round') or '—'} | {_fmt(r.get('det_mIoU'))} | {_fmt(r.get('det_delta_mIoU'), 3)} | "
            f"{r.get('fable_round') or '—'} | {_fmt(r.get('fable_mIoU'))} | {_fmt(r.get('fable_delta_mIoU'), 3)} | "
            f"{r.get('legacy_arm') or '—'} | {_fmt(r.get('legacy_mIoU'))} | {_fmt(r.get('legacy_delta_mIoU'), 3)} |"
        )

    # Summary stats for focus set
    def mean_delta(col: str) -> float:
        return float(sub[col].astype(float).mean()) if col in sub and len(sub) else float("nan")

    lines += [
        "",
        "### Focus-set means",
        "",
        f"| arm | mean selected mIoU | mean ΔmIoU | n refined |",
        f"|---|---:|---:|---:|",
        f"| anchor | {_fmt(sub['anchor_mIoU'].mean())} | 0.000 | 0 |",
        f"| scgen-det | {_fmt(sub['det_mIoU'].mean())} | {_fmt(mean_delta('det_delta_mIoU'))} | "
        f"{int(sub['det_refined'].fillna(False).sum())} |",
        f"| fable | {_fmt(sub['fable_mIoU'].mean())} | {_fmt(mean_delta('fable_delta_mIoU'))} | "
        f"{int(sub['fable_refined'].fillna(False).sum())} |",
        f"| legacy (where present) | {_fmt(sub['legacy_mIoU'].mean())} | "
        f"{_fmt(mean_delta('legacy_delta_mIoU'))} | "
        f"{int(sub['legacy_mIoU'].notna().sum())} |",
        "",
        "## Region comparison (fable arm)",
        "",
        "| region | n | n_refined | n↑ | n↓ | mean a_mIoU | mean s_mIoU | Δmean | frac↑ |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for _, r in regions.iterrows():
        lines.append(
            f"| {r['region']} | {int(r['n'])} | {_fmt(r['n_refined'], 0)} | "
            f"{_fmt(r['n_miou_up'], 0)} | {_fmt(r['n_miou_down'], 0)} | "
            f"{_fmt(r['mean_a_miou'])} | {_fmt(r['mean_s_miou'])} | "
            f"{_fmt(r['delta_mean'])} | {_fmt(r['frac_improved'])} |"
        )

    lines += [
        "",
        "## Artefacts",
        "",
        f"- Det selections: `{STAGE3 / 'selections'}/`",
        f"- Fable selections: `{STAGE3 / 'selections-fable'}/`",
        f"- Det report: `{STAGE3 / 'report.md'}`",
        f"- Fable report: `{STAGE3 / 'report_fable.md'}`",
        f"- Region CSV: `{STAGE3 / 'region_comparison_fable.csv'}`",
        f"- Campaign: `{STAGE3 / 'campaign_fable.md'}`",
        "",
    ]
    out = STAGE3 / "arm_comparison.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out


def write_paper_nine(comp: pd.DataFrame) -> tuple[Path, Path]:
    """Nine-case feasibility table: SC-general Fable-5.1 vs legacy Fable/GPT."""
    from bo.sc_general.score_scaled import band as proxy_band
    from bo.sc_general.select_round import select_dir_for

    rows = []
    sel_dir = select_dir_for("fable")
    for subset in PAPER_NINE:
        r = comp[comp["subset"] == subset]
        if len(r) == 0:
            # May be out of 22-panel; load selection directly.
            sel_path = sel_dir / f"{subset}.json"
            if not sel_path.exists():
                continue
            sel = json.loads(sel_path.read_text(encoding="utf-8"))
            a_proxy = float(sel["anchor"]["proxy_scaled"])
            a_miou = float(sel["anchor"]["mIoU"])
            s = sel["selected"]
            f_round = s["round"]
            f_proxy = float(s["proxy_scaled"])
            f_miou = float(s["mIoU"])
            family = str(r["family"].iloc[0]) if len(r) else ""
        else:
            rr = r.iloc[0]
            a_proxy = float(rr["anchor_proxy"])
            a_miou = float(rr["anchor_mIoU"])
            f_round = rr.get("fable_round") or "anchor"
            f_proxy = float(rr["fable_proxy"]) if pd.notna(rr.get("fable_proxy")) else a_proxy
            f_miou = float(rr["fable_mIoU"]) if pd.notna(rr.get("fable_mIoU")) else a_miou
            family = str(rr["family"])

        # If selection missing from merge (out-of-panel before rebuild), reload.
        sel_path = sel_dir / f"{subset}.json"
        if sel_path.exists():
            sel = json.loads(sel_path.read_text(encoding="utf-8"))
            a_proxy = float(sel["anchor"]["proxy_scaled"])
            a_miou = float(sel["anchor"]["mIoU"])
            s = sel["selected"]
            f_round = s["round"]
            f_proxy = float(s["proxy_scaled"])
            f_miou = float(s["mIoU"])
            if not family:
                from bo.unified.spaces import FAMILY_MODE, family_of_subset

                family = FAMILY_MODE[family_of_subset(subset)]

        leg = PAPER_NINE_LEGACY[subset]
        leg_f = float(leg["fable5"])
        leg_g = float(leg["gpt56"])
        pband = proxy_band(a_proxy)
        rows.append(
            {
                "subset": subset,
                "family": family,
                "proxy_band": pband,
                "in_refine_band": pband == "refine",
                "anchor_proxy": round(a_proxy, 4),
                "anchor_mIoU": round(a_miou, 3),
                "fable51_round": f_round,
                "fable51_proxy": round(f_proxy, 4),
                "fable51_mIoU": round(f_miou, 3),
                "delta_fable51": round(f_miou - a_miou, 3),
                "legacy_fable5_mIoU": leg_f,
                "delta_legacy_fable5": round(leg_f - a_miou, 3),
                "legacy_gpt56_mIoU": leg_g,
                "delta_legacy_gpt56": round(leg_g - a_miou, 3),
            }
        )

    df = pd.DataFrame(rows)
    # Stable paper-nine order matching the manuscript table style.
    order = ["4-4", "1-5", "1-4", "3-2", "4-3", "4-1", "3-4", "3-5", "2-2"]
    df["__ord"] = df["subset"].map({s: i for i, s in enumerate(order)})
    df = df.sort_values("__ord").drop(columns="__ord")

    csv_path = STAGE3 / "paper_nine_comparison.csv"
    df.to_csv(csv_path, index=False)

    def _fmt(x: Any, nd: int = 3) -> str:
        if x is None or (isinstance(x, float) and (np.isnan(x) or np.isinf(x))):
            return "—"
        try:
            return f"{float(x):.{nd}f}"
        except (TypeError, ValueError):
            return str(x)

    n_reject = int((~df["in_refine_band"]).sum())
    lines = [
        "# Paper nine under the 4-feature SC-general proxy",
        "",
        f"Generated: {datetime.now().isoformat()}",
        "",
        "## Setup",
        "",
        "- Proxy: SC-general `pruned_lean` (4 features).",
        "- Proposer: **Fable-5.1** (Cursor agent, live); six dual-band cases "
        "reused from the earlier session arm; three reject-band cases "
        "(`3-2`, `3-5`, `4-4`) newly refined.",
        "- Selection: monotone accept on scaled proxy (GT offline only).",
        f"- Of the nine, **{n_reject}** sit in the proxy **reject** band "
        "(proxy < 0.5) and would be skipped by the label-free refine panel.",
        "- Legacy Fable-5 / GPT-5.6 columns are the manuscript PoC selected "
        "mIoU values (older K-row proxy). Δ is recomputed vs the SC-general "
        "anchor mIoU. Note: some drafts mistyped 4-4 baseline as 0.647; "
        "the true anchor is 0.347.",
        "",
        "## Per-case table",
        "",
        "| Subset | Band | Baseline | Fable-5.1 | ΔFable-5.1 | Legacy Fable-5 | ΔLegF5 | Legacy GPT-5.6 | ΔGPT |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for _, r in df.iterrows():
        lines.append(
            f"| {r['subset']} | {r['proxy_band']} | {_fmt(r['anchor_mIoU'])} | "
            f"{_fmt(r['fable51_mIoU'])} | {_fmt(r['delta_fable51'], 3)} | "
            f"{_fmt(r['legacy_fable5_mIoU'])} | {_fmt(r['delta_legacy_fable5'], 3)} | "
            f"{_fmt(r['legacy_gpt56_mIoU'])} | {_fmt(r['delta_legacy_gpt56'], 3)} |"
        )

    lines += [
        "",
        f"| **Mean** | — | **{_fmt(df['anchor_mIoU'].mean())}** | "
        f"**{_fmt(df['fable51_mIoU'].mean())}** | "
        f"**{_fmt(df['delta_fable51'].mean(), 3)}** | "
        f"**{_fmt(df['legacy_fable5_mIoU'].mean())}** | "
        f"**{_fmt(df['delta_legacy_fable5'].mean(), 3)}** | "
        f"**{_fmt(df['legacy_gpt56_mIoU'].mean())}** | "
        f"**{_fmt(df['delta_legacy_gpt56'].mean(), 3)}** |",
        "",
        "### Round / proxy detail (Fable-5.1)",
        "",
        "| Subset | Selected | a_proxy | s_proxy | Δproxy |",
        "|---|---|---:|---:|---:|",
    ]
    for _, r in df.iterrows():
        lines.append(
            f"| {r['subset']} | {r['fable51_round']} | {_fmt(r['anchor_proxy'], 3)} | "
            f"{_fmt(r['fable51_proxy'], 3)} | "
            f"{_fmt(r['fable51_proxy'] - r['anchor_proxy'], 3)} |"
        )

    lines += [
        "",
        "## Reading",
        "",
        "- Fable-5.1 under the 4-feature proxy is the new result of interest.",
        "- Legacy Fable-5 / GPT-5.6 used a different (K-row) proxy and proposal "
        "loop; treat them as historical PoC columns, not matched ablations.",
        "- Reject-band cases (`3-2`, `3-5`, `4-4`) were still refined here for "
        "parity with the manuscript nine; a strict label-free deployment gate "
        "would not admit them.",
        "",
        "## Artefacts",
        "",
        f"- CSV: `{csv_path}`",
        f"- Selections: `{sel_dir}/`",
        f"- Campaign: `{STAGE3 / 'campaign_fable.md'}`",
        "",
    ]
    md_path = STAGE3 / "paper_nine_comparison.md"
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return md_path, csv_path


def write_markdown_random(comp: pd.DataFrame, regions: pd.DataFrame) -> Path:
    """Four-proposal-arm comparison including the random-overlay control."""
    sub = comp[comp["subset"].isin(PANEL)].copy()

    def _fmt(x: Any, nd: int = 3) -> str:
        if x is None or (isinstance(x, float) and (np.isnan(x) or np.isinf(x))):
            return "—"
        try:
            return f"{float(x):.{nd}f}"
        except (TypeError, ValueError):
            return str(x)

    lines = [
        "# Stage 3 arm comparison — SC-general (with random-overlay control)",
        "",
        f"Generated: {datetime.now().isoformat()}",
        "",
        "Arms: fable / gpt56 / gemini38 / random (k-matched uniform bounded overlays).",
        "Selector and proxy are shared and GT-blind.",
        "",
        "## Per-case table (22-case proxy-only panel)",
        "",
        "| subset | family | a_mIoU | fable | Δf | gpt56 | Δg | gemini38 | Δm | random | Δr |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for _, r in sub.sort_values(["family", "anchor_proxy"]).iterrows():
        lines.append(
            f"| {r['subset']} | {r['family']} | {_fmt(r['anchor_mIoU'])} | "
            f"{_fmt(r.get('fable_mIoU'))} | {_fmt(r.get('fable_delta_mIoU'), 3)} | "
            f"{_fmt(r.get('gpt56_mIoU'))} | {_fmt(r.get('gpt56_delta_mIoU'), 3)} | "
            f"{_fmt(r.get('gemini38_mIoU'))} | {_fmt(r.get('gemini38_delta_mIoU'), 3)} | "
            f"{_fmt(r.get('random_mIoU'))} | {_fmt(r.get('random_delta_mIoU'), 3)} |"
        )

    def mean_delta(col: str) -> float:
        return float(sub[col].astype(float).mean()) if col in sub and len(sub) else float("nan")

    lines += [
        "",
        "### Panel means",
        "",
        "| arm | mean selected mIoU | mean ΔmIoU | n refined |",
        "|---|---:|---:|---:|",
        f"| anchor | {_fmt(sub['anchor_mIoU'].mean())} | 0.000 | 0 |",
        f"| fable | {_fmt(sub['fable_mIoU'].mean())} | {_fmt(mean_delta('fable_delta_mIoU'))} | "
        f"{int(sub['fable_refined'].fillna(False).sum())} |",
        f"| gpt56 | {_fmt(sub['gpt56_mIoU'].mean())} | {_fmt(mean_delta('gpt56_delta_mIoU'))} | "
        f"{int(sub['gpt56_refined'].fillna(False).sum())} |",
        f"| gemini38 | {_fmt(sub['gemini38_mIoU'].mean())} | {_fmt(mean_delta('gemini38_delta_mIoU'))} | "
        f"{int(sub['gemini38_refined'].fillna(False).sum())} |",
        f"| random | {_fmt(sub['random_mIoU'].mean())} | {_fmt(mean_delta('random_delta_mIoU'))} | "
        f"{int(sub['random_refined'].fillna(False).sum())} |",
        "",
        "## Region comparison (random arm)",
        "",
        "| region | n | n_refined | n↑ | n↓ | mean a_mIoU | mean s_mIoU | Δmean | frac↑ |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for _, r in regions.iterrows():
        lines.append(
            f"| {r['region']} | {int(r['n'])} | {_fmt(r['n_refined'], 0)} | "
            f"{_fmt(r['n_miou_up'], 0)} | {_fmt(r['n_miou_down'], 0)} | "
            f"{_fmt(r['mean_a_miou'])} | {_fmt(r['mean_s_miou'])} | "
            f"{_fmt(r['delta_mean'], 3)} | {_fmt(r['frac_improved'], 2)} |"
        )
    lines += [
        "",
        "## Artifacts",
        "",
        f"- Random selections: `{STAGE3 / 'selections-random'}/`",
        f"- Random report: `{STAGE3 / 'report_random.md'}`",
        f"- Region CSV: `{STAGE3 / 'region_comparison_random.csv'}`",
        f"- Campaign: `{STAGE3 / 'campaign_random.md'}`",
        "",
    ]
    out = STAGE3 / "arm_comparison_random.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument(
        "--phase-a-only",
        action="store_true",
        help="Restrict the markdown per-case table to the 6 dual-band cases",
    )
    p.add_argument(
        "--paper-nine",
        action="store_true",
        help="Also write paper_nine_comparison.md/csv for the manuscript nine",
    )
    p.add_argument(
        "--with-gpt56",
        action="store_true",
        help="Include GPT-5.6 arm; write arm_comparison_gpt56.md + region_comparison_gpt56.csv",
    )
    p.add_argument(
        "--with-gemini38",
        action="store_true",
        help="Include Gemini 3.8 (+ GPT-5.6) arm; write arm_comparison_gemini38.md + region CSV",
    )
    p.add_argument(
        "--with-random",
        action="store_true",
        help="Include random-overlay control (+ GPT/Gemini); write arm_comparison_random.md",
    )
    args = p.parse_args()
    STAGE3.mkdir(parents=True, exist_ok=True)

    if args.with_random:
        comp = build_comparison(with_gpt56=True, with_gemini38=True, with_random=True)
        regions = build_regions(comp, arm_prefix="random")
        regions.to_csv(STAGE3 / "region_comparison_random.csv", index=False)
        md = write_markdown_random(comp, regions)
        print(f"wrote {STAGE3 / 'region_comparison_random.csv'} ({len(regions)} regions)")
        print(f"wrote {md}")
        panel = comp[comp["subset"].isin(PANEL)]
        print(
            "Panel mean mIoU: "
            f"anchor={panel['anchor_mIoU'].mean():.3f} "
            f"fable={panel['fable_mIoU'].mean():.3f} "
            f"gpt56={panel['gpt56_mIoU'].mean():.3f} "
            f"gemini38={panel['gemini38_mIoU'].mean():.3f} "
            f"random={panel['random_mIoU'].mean():.3f}"
        )
        return

    if args.with_gemini38:
        comp = build_comparison(with_gpt56=True, with_gemini38=True)
        regions = build_regions(comp, arm_prefix="gemini38")
        regions.to_csv(STAGE3 / "region_comparison_gemini38.csv", index=False)
        md = write_markdown_gemini38(comp, regions)
        print(f"wrote {STAGE3 / 'region_comparison_gemini38.csv'} ({len(regions)} regions)")
        print(f"wrote {md}")
        panel = comp[comp["subset"].isin(PANEL)]
        print(
            "Panel mean mIoU: "
            f"anchor={panel['anchor_mIoU'].mean():.3f} "
            f"det={panel['det_mIoU'].mean():.3f} "
            f"fable={panel['fable_mIoU'].mean():.3f} "
            f"gpt56={panel['gpt56_mIoU'].mean():.3f} "
            f"gemini38={panel['gemini38_mIoU'].mean():.3f}"
        )
        return

    if args.with_gpt56:
        comp = build_comparison(with_gpt56=True)
        regions = build_regions(comp, arm_prefix="gpt56")
        regions.to_csv(STAGE3 / "region_comparison_gpt56.csv", index=False)
        md = write_markdown_gpt56(comp, regions)
        print(f"wrote {STAGE3 / 'region_comparison_gpt56.csv'} ({len(regions)} regions)")
        print(f"wrote {md}")
        panel = comp[comp["subset"].isin(PANEL)]
        print(
            "Panel mean mIoU: "
            f"anchor={panel['anchor_mIoU'].mean():.3f} "
            f"det={panel['det_mIoU'].mean():.3f} "
            f"fable={panel['fable_mIoU'].mean():.3f} "
            f"gpt56={panel['gpt56_mIoU'].mean():.3f}"
        )
        return

    comp = build_comparison()
    regions = build_regions(comp)
    regions.to_csv(STAGE3 / "region_comparison_fable.csv", index=False)
    md = write_markdown(comp, regions, phase_a_only=args.phase_a_only)
    print(f"wrote {STAGE3 / 'region_comparison_fable.csv'} ({len(regions)} regions)")
    print(f"wrote {md}")
    dual = comp[comp["subset"].isin(DUAL_BAND)]
    if len(dual):
        print(
            "Phase A dual-band mean mIoU: "
            f"anchor={dual['anchor_mIoU'].mean():.3f} "
            f"det={dual['det_mIoU'].mean():.3f} "
            f"fable={dual['fable_mIoU'].mean():.3f} "
            f"legacy={dual['legacy_mIoU'].mean():.3f}"
        )

    if args.paper_nine:
        sel_dir = STAGE3 / "selections-fable"
        missing = [s for s in PAPER_NINE if not (sel_dir / f"{s}.json").exists()]
        if missing:
            raise SystemExit(f"paper-nine selections missing: {missing}")
        md9, csv9 = write_paper_nine(comp)
        print(f"wrote {csv9}")
        print(f"wrote {md9}")
        df9 = pd.read_csv(csv9)
        print(
            "Paper nine mean mIoU: "
            f"anchor={df9['anchor_mIoU'].mean():.3f} "
            f"fable51={df9['fable51_mIoU'].mean():.3f} "
            f"legacy_f5={df9['legacy_fable5_mIoU'].mean():.3f} "
            f"legacy_gpt={df9['legacy_gpt56_mIoU'].mean():.3f}"
        )


if __name__ == "__main__":
    main()
