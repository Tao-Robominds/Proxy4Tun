#!/usr/bin/env python3
"""Merge Release-2 (15) + Release-2.1 (12) into a full 27-case analysis.

Reads frozen R2 panels and new R2.1 selections; writes under data/release2.1/analysis/.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from bo.paths import RELEASE2_DATA, RELEASE21_DATA, REPO_ROOT  # noqa: E402
from bo.release2_1.refine import EXTENSION_CASES, PANEL_ARMS, RECORDS  # noqa: E402
from bo.runtime.metadata import family_of  # noqa: E402

ANALYSIS = RELEASE21_DATA / "analysis"
N_BOOT = 100_000
BOOT_SEED = 0
LOW = ("3-5", "3-2")
HIGH = ("5-3", "4-5", "5-2", "1-4", "2-5", "5-4", "1-2", "2-4", "2-2", "2-3")
R2_15 = (
    "1-1", "1-3", "1-5",
    "3-3", "3-4", "3-6", "3-7", "3-8", "3-9", "3-10",
    "4-1", "4-2", "4-3", "4-4", "5-5",
)


def parent_tunnel(subset: str) -> str:
    return subset.split("-", 1)[0]


def _load_ext_panel() -> pd.DataFrame:
    rows = []
    for arm in PANEL_ARMS:
        for subset in EXTENSION_CASES:
            sel_path = RECORDS / "selections" / arm / f"{subset}.json"
            if not sel_path.exists():
                continue
            sel = json.loads(sel_path.read_text(encoding="utf-8"))
            start = sel["start"]
            chosen = sel["selected"]
            rows.append(
                {
                    "arm": arm,
                    "subset": subset,
                    "family": family_of(subset),
                    "parent": parent_tunnel(subset),
                    "start_score": float(start["score"]),
                    "start_miou": float(start.get("gt_miou") or float("nan")),
                    "selected_round": chosen.get("name"),
                    "selected_score": float(chosen["score"]),
                    "selected_miou": float(chosen.get("gt_miou") or float("nan")),
                    "delta_miou": float(chosen.get("gt_miou") or 0)
                    - float(start.get("gt_miou") or 0),
                    "delta_score": float(chosen["score"]) - float(start["score"]),
                    "source": "release2.1",
                    "stratum": (
                        "low" if subset in LOW else "high" if subset in HIGH else "mid"
                    ),
                }
            )
    return pd.DataFrame(rows)


def _load_r2_15() -> pd.DataFrame:
    base = pd.read_csv(RELEASE2_DATA / "refinement" / "records" / "panel.csv")
    base = base[base["arm"].isin(["random", "fable", "gemini38"])].copy()
    gpt = pd.read_csv(RELEASE2_DATA / "analysis" / "gpt56_medium_rerun" / "panel.csv")
    out = pd.concat([base, gpt], ignore_index=True)
    out["source"] = "release2"
    out["stratum"] = "mid"
    return out


def _boot_mean(deltas: np.ndarray, parents: list[str]) -> dict:
    rng = np.random.default_rng(BOOT_SEED)
    by = {}
    for d, p in zip(deltas, parents):
        by.setdefault(p, []).append(float(d))
    clusters = list(by.keys())
    if not clusters:
        return {"point": float("nan"), "ci95": [float("nan"), float("nan")]}
    point = float(np.mean([np.mean(by[c]) for c in clusters]))
    boots = []
    for _ in range(N_BOOT):
        picks = rng.choice(clusters, size=len(clusters), replace=True)
        boots.append(float(np.mean([np.mean(by[c]) for c in picks])))
    lo, hi = np.percentile(boots, [2.5, 97.5])
    return {
        "point": point,
        "ci95": [float(lo), float(hi)],
        "n_boot": N_BOOT,
        "n_clusters": len(clusters),
    }


def _arm_summary(df: pd.DataFrame, arm: str) -> dict:
    sub = df[df["arm"] == arm].copy()
    if sub.empty:
        return {}
    deltas = sub["delta_miou"].to_numpy(dtype=float)
    parents = sub["parent"].astype(str).tolist()
    return {
        "n": int(len(sub)),
        "mean_start": float(sub["start_miou"].mean()),
        "mean_selected": float(sub["selected_miou"].mean()),
        "mean_delta": float(deltas.mean()),
        "median_delta": float(np.median(deltas)),
        "bootstrap": _boot_mean(deltas, parents),
        "up": int((deltas > 1e-9).sum()),
        "same": int((np.abs(deltas) <= 1e-9).sum()),
        "down": int((deltas < -1e-9).sum()),
        "worst": float(deltas.min()) if len(deltas) else float("nan"),
    }


def main() -> int:
    ANALYSIS.mkdir(parents=True, exist_ok=True)
    ext = _load_ext_panel()
    r2 = _load_r2_15()
    merged = pd.concat([r2, ext], ignore_index=True)
    merged.to_csv(ANALYSIS / "panel_merged_27.csv", index=False)
    ext.to_csv(ANALYSIS / "panel_extension_12.csv", index=False)

    numbers: dict = {
        "n_extension": len(EXTENSION_CASES),
        "n_r2_15": len(R2_15),
        "n_merged": 27,
        "arms": list(PANEL_ARMS),
        "extension_low": list(LOW),
        "extension_high": list(HIGH),
    }

    lines = [
        "# Release 2.1 analysis",
        "",
        "Plans 1–3 skipped; frozen four-feature proxy and Release-2 starts reused.",
        "",
        "## Extension panel (12 cases)",
        "",
    ]
    for arm in PANEL_ARMS:
        s = _arm_summary(ext, arm)
        numbers[f"ext_{arm}"] = s
        if not s:
            lines.append(f"- {arm}: incomplete")
            continue
        ci = s["bootstrap"]["ci95"]
        lines.append(
            f"- **{arm}**: start {s['mean_start']:.3f} → selected {s['mean_selected']:.3f}; "
            f"Δ {s['mean_delta']:+.3f} (parent-tunnel 95% [{ci[0]:+.3f}, {ci[1]:+.3f}]); "
            f"up/same/down {s['up']}/{s['same']}/{s['down']}; worst {s['worst']:+.3f}"
        )

    lines += ["", "## Extension by proxy-start stratum", ""]
    for label, cases in (("low_<0.5", LOW), ("high_>0.7", HIGH)):
        lines.append(f"### {label}")
        for arm in PANEL_ARMS:
            sub = ext[(ext["arm"] == arm) & (ext["subset"].isin(cases))]
            s = _arm_summary(sub, arm) if not sub.empty else {}
            numbers[f"ext_{label}_{arm}"] = s
            if not s:
                lines.append(f"- {arm}: incomplete")
            else:
                lines.append(
                    f"- {arm}: n={s['n']} mean Δ {s['mean_delta']:+.3f} "
                    f"(up/same/down {s['up']}/{s['same']}/{s['down']})"
                )
        lines.append("")

    lines += ["## Merged 27-case panel (15 frozen + 12 extension)", ""]
    for arm in PANEL_ARMS:
        s = _arm_summary(merged, arm)
        numbers[f"merged27_{arm}"] = s
        if not s:
            lines.append(f"- {arm}: incomplete")
            continue
        ci = s["bootstrap"]["ci95"]
        lines.append(
            f"- **{arm}**: start {s['mean_start']:.3f} → selected {s['mean_selected']:.3f}; "
            f"Δ {s['mean_delta']:+.3f} (95% [{ci[0]:+.3f}, {ci[1]:+.3f}]); "
            f"up/same/down {s['up']}/{s['same']}/{s['down']}"
        )

    lines += ["", "## 15-case vs 27-case comparison", ""]
    for arm in PANEL_ARMS:
        a15 = _arm_summary(r2[r2["arm"] == arm], arm)
        a27 = numbers.get(f"merged27_{arm}") or {}
        if not a15 or not a27:
            lines.append(f"- {arm}: incomplete")
            continue
        lines.append(
            f"- {arm}: 15-case Δ {a15['mean_delta']:+.3f} → 27-case Δ {a27['mean_delta']:+.3f} "
            f"(change {a27['mean_delta'] - a15['mean_delta']:+.3f})"
        )
        numbers[f"compare15to27_{arm}"] = {
            "delta_15": a15["mean_delta"],
            "delta_27": a27["mean_delta"],
            "delta_change": a27["mean_delta"] - a15["mean_delta"],
        }

    (ANALYSIS / "numbers.json").write_text(json.dumps(numbers, indent=2) + "\n")
    (ANALYSIS / "benefit.md").write_text("\n".join(lines) + "\n")
    (ANALYSIS / "baseline_vs_release2.md").write_text(
        "\n".join(
            [
                "# 15-case Release 2 vs merged 27-case Release 2.1",
                "",
                "Extension covers the 12 reference starts outside inclusive [0.5, 0.7].",
                "",
                *lines[lines.index("## 15-case vs 27-case comparison") :],
            ]
        )
        + "\n"
    )
    print("wrote", ANALYSIS / "benefit.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
