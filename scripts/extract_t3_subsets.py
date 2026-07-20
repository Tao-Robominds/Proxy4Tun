#!/usr/bin/env python3
"""Extract T3 ring-window subsets from raw data/3-1.txt.

Pipeline (matches existing 3-1-*/_rings_meta.json schema):
1. Uniform-stride subsample the full raw file to ~target_points.
2. Filter consecutive 10-ring windows into data/subsets/<id>.txt.
3. Write <id>_rings_meta.json beside each subset.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# Non-overlapping, well-populated windows (avoid sparse rings 110+).
# Existing: 3-1 = 27-36, 3-2 = 46-55, 3-3 = 77-86 (renamed from 3-1-*).
DEFAULT_WINDOWS: dict[str, tuple[int, int]] = {
    "3-4": (57, 66),
    "3-5": (97, 106),
}


def count_lines(path: Path) -> int:
    n = 0
    with open(path, "rb") as f:
        for _ in f:
            n += 1
    return n


def extract_windows(
    src: Path,
    out_dir: Path,
    windows: dict[str, tuple[int, int]],
    *,
    target_points: int = 2_100_000,
) -> dict[str, dict]:
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"Counting lines in {src} ...")
    n_lines = count_lines(src)
    stride = max(1, n_lines // target_points)
    print(f"n_lines={n_lines} target={target_points} stride={stride}")

    ring_sets = {name: set(range(lo, hi + 1)) for name, (lo, hi) in windows.items()}
    writers = {name: open(out_dir / f"{name}.txt", "w", encoding="utf-8") for name in windows}
    n_in = 0
    n_out = {name: 0 for name in windows}
    unique_before: set[int] = set()

    try:
        with open(src, "r", encoding="utf-8", errors="replace") as f:
            for i, line in enumerate(f):
                if i % stride != 0:
                    continue
                parts = line.split()
                if len(parts) < 6:
                    continue
                try:
                    ring = int(float(parts[5]))
                except ValueError:
                    continue
                n_in += 1
                unique_before.add(ring)
                for name, rings in ring_sets.items():
                    if ring in rings:
                        writers[name].write(line if line.endswith("\n") else line + "\n")
                        n_out[name] += 1
    finally:
        for w in writers.values():
            w.close()

    metas: dict[str, dict] = {}
    for name, (lo, hi) in windows.items():
        kept = list(range(lo, hi + 1))
        meta = {
            "tunnel_id": name,
            "n_rings_requested": len(kept),
            "ring_ids_kept": kept,
            "n_rings_kept": len(kept),
            "n_points_in": n_in,
            "n_points_out": n_out[name],
            "unique_rings_before": sorted(unique_before),
            "source": str(src),
            "stride": stride,
        }
        meta_path = out_dir / f"{name}_rings_meta.json"
        meta_path.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
        metas[name] = meta
        print(f"{name}: rings {lo}-{hi} -> {n_out[name]} points ({meta_path.name})")
    return metas


def main() -> None:
    p = argparse.ArgumentParser(description="Extract T3 subsets from data/3-1.txt")
    p.add_argument("--src", type=Path, default=REPO / "data" / "3-1.txt")
    p.add_argument("--out-dir", type=Path, default=REPO / "data" / "subsets")
    p.add_argument("--target-points", type=int, default=2_100_000)
    p.add_argument(
        "--windows",
        nargs="*",
        default=None,
        help="Optional subset ids to extract (default: 3-4 3-5)",
    )
    args = p.parse_args()

    windows = DEFAULT_WINDOWS
    if args.windows:
        windows = {k: DEFAULT_WINDOWS[k] for k in args.windows}
    if not args.src.exists():
        raise SystemExit(f"Missing source {args.src}")
    extract_windows(args.src, args.out_dir, windows, target_points=args.target_points)


if __name__ == "__main__":
    main()
