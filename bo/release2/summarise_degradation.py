#!/usr/bin/env python3
"""Paired-degradation summary: fidelity, ranking, alarms, intervals.

Reads record.json from the 27 reference and 27 degraded runs. Does not refit
the proxy.

Usage:
  ./venv/bin/python bo/release2/summarise_degradation.py
"""

from __future__ import annotations

import itertools
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.metrics import mean_absolute_error

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from bo.paths import RELEASE2_DATA  # noqa: E402
from bo.release2.run_pair import EVAL_SUBSETS  # noqa: E402
from bo.runtime.clustered_stats import subset_bootstrap_spearman  # noqa: E402

DEG = RELEASE2_DATA / "degradation"
REFS = RELEASE2_DATA / "references"
OUT = DEG / "records"
FOUR = (
    "correspondence_f1@15",
    "sam_fill_rate",
    "ring_count_error",
    "depth_nan_ratio",
)


def _spearman(y, pred) -> float:
    y = np.asarray(y, dtype=float)
    pred = np.asarray(pred, dtype=float)
    if len(y) < 3 or np.unique(y).size < 2 or np.unique(pred).size < 2:
        return float("nan")
    rho = stats.spearmanr(y, pred).correlation
    return float(rho) if rho is not None and np.isfinite(rho) else float("nan")


def _load_rows() -> pd.DataFrame:
    rows = []
    for subset in EVAL_SUBSETS:
        for arm, root in (("reference", REFS), ("degraded", DEG)):
            path = root / subset / "record.json"
            if not path.exists():
                continue
            rec = json.loads(path.read_text(encoding="utf-8"))
            if not rec.get("valid"):
                continue
            measurements = rec.get("measurements") or {}
            row = {
                "subset": subset,
                "family": rec["family"],
                "arm": arm,
                "parent": subset.split("-", 1)[0],
                "score": float(rec["score"]),
                "band": rec["band"],
                "gt_miou": float(rec["gt_miou"]),
            }
            for key in FOUR:
                row[key] = float(measurements[key])
            rows.append(row)
    return pd.DataFrame(rows)


def _alarm_rates(frame: pd.DataFrame) -> dict[str, float]:
    alarm = frame["score"] < 0.5
    degraded = frame["arm"] == "degraded"
    tp = int((alarm & degraded).sum())
    fp = int((alarm & ~degraded).sum())
    fn = int((~alarm & degraded).sum())
    precision = float(tp / (tp + fp)) if (tp + fp) else float("nan")
    recall = float(tp / (tp + fn)) if (tp + fn) else float("nan")
    return {
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "precision": precision,
        "recall": recall,
        "degraded_flagged": tp,
        "degraded_n": int(degraded.sum()),
        "reference_flagged": fp,
        "reference_n": int((~degraded).sum()),
    }


def _parent_interval(frame: pd.DataFrame) -> dict:
    tunnels = ["1", "2", "3", "4", "5"]
    groups = {tunnel: frame[frame["parent"] == tunnel] for tunnel in tunnels}
    rhos = []
    for combo in itertools.product(tunnels, repeat=5):
        boot = pd.concat([groups[tunnel] for tunnel in combo], ignore_index=True)
        rhos.append(_spearman(boot["gt_miou"], boot["score"]))
    arr = np.asarray(rhos, dtype=float)
    lo, hi = np.percentile(arr, [2.5, 97.5])
    return {
        "n": int(arr.size),
        "interval": [float(lo), float(hi)],
        "point": _spearman(frame["gt_miou"], frame["score"]),
    }


def _fmt(value: float, digits: int = 3) -> str:
    if value is None or not np.isfinite(value):
        return "n/a"
    return f"{value:.{digits}f}"


def main() -> int:
    frame = _load_rows()
    OUT.mkdir(parents=True, exist_ok=True)
    cols = ["subset", "family", "arm", *FOUR, "score", "band", "gt_miou"]
    frame.to_csv(OUT / "pairs.csv", index=False, columns=cols if len(frame) else cols)

    expected = 54
    lines = [
        "# Degradation summary",
        "",
        f"Completed runs: {len(frame)} / {expected}.",
        "",
    ]
    if len(frame) < 3:
        lines.append("Too few completed runs to summarise fidelity.")
        (OUT / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"wrote {OUT / 'summary.md'}")
        return 0

    rho = _spearman(frame["gt_miou"], frame["score"])
    mae = float(mean_absolute_error(frame["gt_miou"], frame["score"]))
    lines.append(f"- Spearman rho: {_fmt(rho)}")
    lines.append(f"- MAE: {_fmt(mae)}")

    boot_frame = frame.rename(columns={"gt_miou": "mIoU", "score": "proxy"})
    boot = subset_bootstrap_spearman(boot_frame, n_boot=2000, seed=0)
    parent = _parent_interval(frame)
    lines.append(
        f"- Subset bootstrap 95% interval (2000, pairs kept, stratified by family): "
        f"[{_fmt(boot['ci95'][0])}, {_fmt(boot['ci95'][1])}]"
    )
    lines.append(
        f"- Parent-tunnel enumeration ({parent['n']} = 5^5 ordered resamples): "
        f"[{_fmt(parent['interval'][0])}, {_fmt(parent['interval'][1])}]"
    )
    lines.append("")
    lines.append("## By family and arm")
    lines.append("")
    for family, part in frame.groupby("family"):
        lines.append(
            f"- {family}: rho {_fmt(_spearman(part['gt_miou'], part['score']))}, "
            f"MAE {_fmt(float(mean_absolute_error(part['gt_miou'], part['score'])))} "
            f"(n={len(part)})"
        )
    for arm, part in frame.groupby("arm"):
        lines.append(
            f"- {arm}: rho {_fmt(_spearman(part['gt_miou'], part['score']))}, "
            f"MAE {_fmt(float(mean_absolute_error(part['gt_miou'], part['score'])))} "
            f"(n={len(part)})"
        )

    both = set(frame.loc[frame["arm"] == "reference", "subset"]) & set(
        frame.loc[frame["arm"] == "degraded", "subset"]
    )
    ranked = 0
    for subset in sorted(both):
        ref = float(frame[(frame["subset"] == subset) & (frame["arm"] == "reference")]["score"].iloc[0])
        deg = float(frame[(frame["subset"] == subset) & (frame["arm"] == "degraded")]["score"].iloc[0])
        if ref > deg:
            ranked += 1
    lines.append("")
    lines.append(
        f"Strict pair ranking: {ranked}/{len(both)} pairs with reference score > degraded score."
    )
    missing = [s for s in EVAL_SUBSETS if s not in both]
    if missing:
        lines.append(f"Incomplete pairs: {', '.join(missing)}.")

    lines.append("")
    lines.append("## Alarms at 0.5")
    lines.append("")
    overall = _alarm_rates(frame)
    lines.append(
        f"- Overall precision {_fmt(overall['precision'])}, recall {_fmt(overall['recall'])} "
        f"(degraded flagged {overall['degraded_flagged']}/{overall['degraded_n']}, "
        f"reference flagged {overall['reference_flagged']}/{overall['reference_n']})."
    )
    for family, part in frame.groupby("family"):
        rates = _alarm_rates(part)
        lines.append(
            f"- {family}: precision {_fmt(rates['precision'])}, recall {_fmt(rates['recall'])} "
            f"(degraded {rates['degraded_flagged']}/{rates['degraded_n']}, "
            f"reference {rates['reference_flagged']}/{rates['reference_n']})."
        )

    lines.append("")
    lines.append("## Plan 4 starting bands")
    lines.append("")
    lines.append("Admitted starts are reference runs with score in [0.5, 0.7] inclusive.")
    lines.append("")
    lines.append("| subset | family | score | band | gt_miou |")
    lines.append("| --- | --- | ---: | --- | ---: |")
    admitted = []
    refs = frame[frame["arm"] == "reference"].sort_values("subset")
    for _, row in refs.iterrows():
        lines.append(
            f"| {row['subset']} | {row['family']} | {_fmt(row['score'])} | {row['band']} | {_fmt(row['gt_miou'])} |"
        )
        if 0.5 <= float(row["score"]) <= 0.7:
            admitted.append(str(row["subset"]))
    lines.append("")
    lines.append(f"Admitted ({len(admitted)}): {', '.join(admitted) if admitted else '(none)'}.")
    (OUT / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {OUT / 'summary.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
