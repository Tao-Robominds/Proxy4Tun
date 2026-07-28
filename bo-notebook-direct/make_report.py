#!/usr/bin/env python3
"""Assemble notebook-faithful vs unified vs refined comparison report."""
from __future__ import annotations

import csv
import json
import statistics
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
LOG_DIR = REPO / "bo-notebook-direct" / "logs"
OUT_CSV = REPO / "bo-notebook-direct" / "scores.csv"
OUT_MD = REPO / "bo-notebook-direct" / "report.md"

# 27-subset panel matching bo-full-stage holdout_scores.csv anchors
PANEL = [
    "1-1", "1-2", "1-3", "1-4", "1-5",
    "2-2", "2-3", "2-4", "2-5",
    "3-2", "3-3", "3-4", "3-5", "3-6", "3-7", "3-8", "3-9", "3-10",
    "4-1", "4-2", "4-3", "4-4", "4-5",
    "5-2", "5-3", "5-4", "5-5",
]

FAMILY = {
    "1": "staggered", "2": "staggered",
    "3": "continuous",
    "4": "complex", "5": "complex",
}


def load_unified() -> dict[str, float]:
    path = REPO / "bo-full-stage" / "holdout_scores.csv"
    out: dict[str, float] = {}
    with path.open() as f:
        for r in csv.DictReader(f):
            if r["config_kind"] == "anchor":
                out[r["subset"]] = float(r["mIoU"])
    return out


def load_refined() -> dict[str, float]:
    path = REPO / "bo-proxy-scale" / "refined_scores.csv"
    out: dict[str, float] = {}
    with path.open() as f:
        for r in csv.DictReader(f):
            out[r["subset"]] = float(r["selected_mIoU"])
    return out


def load_notebook() -> dict[str, dict]:
    out: dict[str, dict] = {}
    for s in PANEL:
        meta = LOG_DIR / f"{s}.json"
        if not meta.exists():
            out[s] = {"status": "missing", "miou": None}
            continue
        rec = json.loads(meta.read_text())
        out[s] = {
            "status": rec.get("status"),
            "miou": rec.get("miou"),
            "elapsed_s": rec.get("elapsed_s"),
            "error_tail": rec.get("error_tail") or rec.get("error"),
        }
    return out


def mean(xs: list[float]) -> float:
    return sum(xs) / len(xs) if xs else float("nan")


def main() -> None:
    unified = load_unified()
    refined = load_refined()
    notebook = load_notebook()

    rows = []
    for s in PANEL:
        nb = notebook[s]
        rows.append({
            "subset": s,
            "family": FAMILY[s.split("-")[0]],
            "notebook_status": nb["status"],
            "notebook_mIoU": nb["miou"],
            "unified_mIoU": unified.get(s),
            "refined_mIoU": refined.get(s),
            "delta_nb_vs_unified": (
                None if nb["miou"] is None or s not in unified
                else round(nb["miou"] - unified[s], 3)
            ),
            "elapsed_s": nb.get("elapsed_s"),
        })

    with OUT_CSV.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    nb_ok = [r for r in rows if r["notebook_mIoU"] is not None]
    nb_fail = [r for r in rows if r["notebook_mIoU"] is None]
    nb_vals = [float(r["notebook_mIoU"]) for r in nb_ok]
    un_vals = [float(r["unified_mIoU"]) for r in rows if r["unified_mIoU"] is not None]
    rf_vals = [float(r["refined_mIoU"]) for r in rows if r["refined_mIoU"] is not None]
    # Paired means on subsets where notebook succeeded
    paired_u = [float(r["unified_mIoU"]) for r in nb_ok]
    paired_r = [float(r["refined_mIoU"]) for r in nb_ok if r["refined_mIoU"] is not None]

    by_fam = {}
    for fam in ("staggered", "continuous", "complex"):
        fam_rows = [r for r in nb_ok if r["family"] == fam]
        by_fam[fam] = {
            "n": len(fam_rows),
            "notebook": mean([float(r["notebook_mIoU"]) for r in fam_rows]),
            "unified": mean([float(r["unified_mIoU"]) for r in fam_rows]),
        }

    lines = []
    lines.append("# Notebook-faithful baseline — report")
    lines.append("")
    lines.append("Date: 2026-07-28.")
    lines.append("")
    lines.append("Notebook-mode parameter overlays from")
    lines.append("`bo-notebook-direct/params/` run through the original per-family")
    lines.append("anchor stage scripts on the 27-subset panel that yields the")
    lines.append("unified mean **0.722**. See `README.md` for caveats")
    lines.append("(geometric SAM fallback, T3 mask-column fix, etc. remain).")
    lines.append("")
    lines.append("## 1. Headline numbers")
    lines.append("")
    lines.append("| Scope | n | Mean mIoU |")
    lines.append("|---|---:|---:|")
    lines.append(f"| Notebook-faithful (ok runs) | {len(nb_ok)} | **{mean(nb_vals):.3f}** |")
    lines.append(f"| Unified sibling-anchor (full panel) | {len(un_vals)} | **{mean(un_vals):.3f}** |")
    lines.append(f"| After proxy-selected refinement | {len(rf_vals)} | **{mean(rf_vals):.3f}** |")
    if paired_u:
        lines.append(
            f"| Unified on same subsets as notebook-ok | {len(paired_u)} | {mean(paired_u):.3f} |"
        )
        lines.append(
            f"| Δ (notebook − unified), paired | {len(paired_u)} | "
            f"**{mean(nb_vals) - mean(paired_u):+.3f}** |"
        )
    lines.append("")
    lines.append(f"Failures / missing: **{len(nb_fail)}** "
                 f"({', '.join(r['subset'] for r in nb_fail) or 'none'}).")
    lines.append("")
    lines.append("## 2. Per-family means (notebook-ok only)")
    lines.append("")
    lines.append("| Family | n | Notebook | Unified | Δ |")
    lines.append("|---|---:|---:|---:|---:|")
    for fam, d in by_fam.items():
        if d["n"] == 0:
            continue
        lines.append(
            f"| {fam} | {d['n']} | {d['notebook']:.3f} | {d['unified']:.3f} | "
            f"{d['notebook'] - d['unified']:+.3f} |"
        )
    lines.append("")
    lines.append("## 3. Per-subset results")
    lines.append("")
    lines.append("| Subset | Family | Notebook | Unified | Refined | Δ nb−un | Status |")
    lines.append("|---|---|---:|---:|---:|---:|---|")
    for r in rows:
        nb = "—" if r["notebook_mIoU"] is None else f"{r['notebook_mIoU']:.3f}"
        un = "—" if r["unified_mIoU"] is None else f"{r['unified_mIoU']:.3f}"
        rf = "—" if r["refined_mIoU"] is None else f"{r['refined_mIoU']:.3f}"
        dlt = "—" if r["delta_nb_vs_unified"] is None else f"{r['delta_nb_vs_unified']:+.3f}"
        lines.append(
            f"| {r['subset']} | {r['family']} | {nb} | {un} | {rf} | {dlt} | "
            f"{r['notebook_status']} |"
        )
    lines.append("")
    if nb_fail:
        lines.append("## 4. Failure inventory")
        lines.append("")
        for r in nb_fail:
            nb = notebook[r["subset"]]
            lines.append(f"### {r['subset']} (`{nb['status']}`)")
            lines.append("")
            lines.append("```")
            lines.append(str(nb.get("error_tail") or "see logs/")[:600])
            lines.append("```")
            lines.append("")
    lines.append("## Manuscript-ready sentence")
    lines.append("")
    if nb_vals:
        lines.append(
            f"Applying the notebook-faithful expert configuration (parametric "
            f"adaptations disabled) to the same {len(PANEL)}-subset panel yields "
            f"mean mIoU **{mean(nb_vals):.3f}**"
            + (f" on {len(nb_ok)} completed runs" if len(nb_ok) < len(PANEL) else "")
            + f", versus **{mean(un_vals):.3f}** under the unified sibling-anchor "
            f"pipeline and **{mean(rf_vals):.3f}** after proxy-selected self-refinement"
            + (
                f" (paired Δ notebook−unified "
                f"**{mean(nb_vals) - mean(paired_u):+.3f}**)."
                if paired_u else "."
            )
        )
    lines.append("")
    lines.append("## Caveats")
    lines.append("")
    lines.append("- Geometric SAM fallback on tunnels 4/5 remains (hardcoded).")
    lines.append("- T3 theta-column fix and T1/T2 oblique sign fix remain.")
    lines.append("- T3 `n_segment` kept at subset-scale `[2,8]` (not notebook `[11,11]`).")
    lines.append("")

    OUT_MD.write_text("\n".join(lines))
    print(f"Wrote {OUT_CSV}")
    print(f"Wrote {OUT_MD}")
    print(f"notebook mean={mean(nb_vals):.3f} n={len(nb_ok)}; "
          f"unified={mean(un_vals):.3f}; refined={mean(rf_vals):.3f}; "
          f"fail={len(nb_fail)}")


if __name__ == "__main__":
    main()
