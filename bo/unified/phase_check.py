"""GT-free cross-ring phase-coherence check.

Detects per-ring block-label rotation (block identities assigned with the
wrong circumferential phase) using only pipeline outputs: predicted block
labels, predicted ring ids, and the unwrapped coordinates (theta, h) from
``final.csv``. No ground truth is used.

Motivation: the 1-5 anchor false negative. Two rings had all block labels
rotated by one position around the circumference; every B1/B2 feature looked
healthy, so the proxy scored the run 0.78 while actual mIoU was 0.49.

Method
------
Segmental linings reuse a small set of build orientations, so every ring's
"clock face" (circular mean theta of each block label) should closely match
at least one sibling ring in the same tunnel. For each ring we compute the
distance to its nearest sibling face (median absolute circular difference
over shared labels). The run-level score is the point-weighted mean of these
nearest-peer distances:

- healthy runs: every ring has a near-twin, score is a few degrees;
- a ring with rotated labels has no twin (its face sits one block width away
  from every legitimate orientation), inflating the score.

Applicability: validated for t1&2 and t3 (regular two-orientation stagger;
healthy anchors score 1-4 deg, the rotated 1-5 anchor scores 17 deg). For
t4&5 the stagger sequence is irregular and block widths vary, so healthy runs
already score 10-35 deg and the check is NOT reliable there - results for
t4&5 are reported but flagged as out-of-scope.

Usage
-----
./venv/bin/python bo/phase_check.py data/bo/1-5-family-proxy/runs/1-5-anchor -v
./venv/bin/python bo/phase_check.py --all data/bo --json-out bo/family/phase_check.json
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

# Run-level alarm threshold (degrees) for families with a regular stagger.
DEFAULT_THRESHOLD_DEG = 12.0
APPLICABLE_FAMILIES = {"t1&2", "t3"}


def family_of(subset: str) -> str:
    head = subset.split("-", 1)[0]
    return {"1": "t1&2", "2": "t1&2", "3": "t3"}.get(head, "t4&5")


def circular_mean(angles_rad: np.ndarray) -> float:
    return math.atan2(np.sin(angles_rad).mean(), np.cos(angles_rad).mean())


def circular_diff_deg(a_rad: float, b_rad: float) -> float:
    """Signed smallest difference a-b in degrees, in (-180, 180]."""
    d = math.degrees(a_rad - b_rad)
    return (d + 180.0) % 360.0 - 180.0


def face_distance(face_a: dict[int, float], face_b: dict[int, float]) -> float | None:
    """Median absolute circular offset between two clock faces over shared labels."""
    common = set(face_a) & set(face_b)
    if len(common) < 3:
        return None
    return float(np.median([abs(circular_diff_deg(face_a[k], face_b[k])) for k in common]))


def phase_coherence(run_dir: Path, min_pts: int = 50) -> dict:
    df = pd.read_csv(run_dir / "final.csv", usecols=["theta", "h", "pred", "pred_ring"])
    blocks = df[df["pred"] > 0]

    faces: dict[int, dict[int, float]] = {}
    sizes: dict[int, int] = {}
    for ring, ring_df in blocks.groupby("pred_ring"):
        face = {}
        for label, lab_df in ring_df.groupby("pred"):
            if len(lab_df) >= min_pts:
                face[int(label)] = circular_mean(lab_df["theta"].to_numpy())
        if len(face) >= 3:
            faces[int(ring)] = face
            sizes[int(ring)] = len(ring_df)

    order = [
        int(r)
        for r in blocks.groupby("pred_ring")["h"].median().sort_values().index
        if int(r) in faces
    ]

    rings_out = []
    total_pts = sum(sizes[r] for r in order)
    weighted_sum = 0.0
    for ring in order:
        dists = [face_distance(faces[ring], faces[other]) for other in order if other != ring]
        dists = [d for d in dists if d is not None]
        if not dists:
            continue
        nearest = min(dists)
        weighted_sum += nearest * sizes[ring] / total_pts
        rings_out.append(
            {
                "ring": ring,
                "points": sizes[ring],
                "nearest_peer_dist_deg": round(nearest, 1),
            }
        )

    score = round(weighted_sum, 1) if rings_out else None
    return {
        "run": str(run_dir),
        "n_rings_scored": len(rings_out),
        "phase_incoherence_deg": score,
        "rings": rings_out,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("target", help="run directory containing final.csv, or a data root with --all")
    ap.add_argument("--all", action="store_true", help="scan all */runs/* under target")
    ap.add_argument("--threshold-deg", type=float, default=DEFAULT_THRESHOLD_DEG)
    ap.add_argument("--json-out", type=Path, default=None)
    ap.add_argument("-v", "--verbose", action="store_true", help="print per-ring distances")
    args = ap.parse_args()

    target = Path(args.target)
    if args.all:
        run_dirs = sorted(p for p in target.glob("*-family-proxy/runs/*") if (p / "final.csv").exists())
    else:
        run_dirs = [target]

    results = []
    for run_dir in run_dirs:
        subset = run_dir.name.rsplit("-", 1)[0]
        family = family_of(subset)
        try:
            res = phase_coherence(run_dir)
        except Exception as exc:  # noqa: BLE001
            print(f"{run_dir}: ERROR {exc}", file=sys.stderr)
            continue
        res["family"] = family
        applicable = family in APPLICABLE_FAMILIES
        score = res["phase_incoherence_deg"]
        res["applicable"] = applicable
        res["phase_alarm"] = bool(applicable and score is not None and score > args.threshold_deg)
        results.append(res)

        if not applicable:
            status = "n/a (irregular stagger family)"
        elif res["phase_alarm"]:
            status = "PHASE ALARM"
        else:
            status = "ok"
        score_txt = f"{score:6.1f}" if score is not None else "   n/a"
        print(f"{run_dir.name:20s} family={family:5s} phase_incoherence={score_txt} deg  [{status}]")
        if args.verbose:
            for r in res["rings"]:
                print(
                    f"    ring {r['ring']:3d}: nearest-peer dist {r['nearest_peer_dist_deg']:6.1f} deg "
                    f"({r['points']} pts)"
                )

    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(results, indent=2))
        print(f"\nWrote {args.json_out}")


if __name__ == "__main__":
    main()
