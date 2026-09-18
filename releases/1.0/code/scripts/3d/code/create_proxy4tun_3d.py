#!/usr/bin/env python3
"""3D point-cloud panels for Proxy4Tun: holdout anchor vs known-bad overlays.

Writes HTML under scripts/3d/ and static PNG/PDF under paper/Proxy4Tun/figures/.
Uses matplotlib for static export (no kaleido required).
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[3]
OUT_PNG = REPO / "paper" / "Proxy4Tun" / "figures" / "proxy4tun_3d_anchor_vs_bad.png"
OUT_PDF = REPO / "paper" / "Proxy4Tun" / "figures" / "proxy4tun_3d_anchor_vs_bad.pdf"
OUT_HTML = REPO / "scripts" / "3d" / "proxy4tun_anchor_vs_bad.html"

SEGMENT_COLORS = {
    0: "#B0C4DE",
    1: "#E67E22",
    2: "#58D68D",
    3: "#F5B7B1",
    4: "#AF7AC5",
    5: "#D4A373",
    6: "#F4D03F",
    7: "#85C1E9",
    8: "#ABB2B9",
    9: "#5D6D7E",
}

PAIRS = [
    ("1-2", "Staggered"),
    ("3-6", "Continuous"),
    ("5-2", "Complex"),
]


def _paths(subset: str) -> tuple[Path, Path]:
    root = REPO / "data" / "bo-unified" / f"{subset}-family-proxy" / "runs"
    return root / f"{subset}-anchor" / "final.csv", root / f"{subset}-bad" / "final.csv"


def _sample(df: pd.DataFrame, n: int = 7000, seed: int = 0) -> pd.DataFrame:
    if "pred" in df.columns:
        df = df[df["pred"].astype(int) != 0]
    if len(df) > n:
        df = df.sample(n=n, random_state=seed)
    return df


def main() -> None:
    fig = plt.figure(figsize=(11.5, 6.8))
    idx = 1
    for subset, fam in PAIRS:
        a_path, b_path = _paths(subset)
        for kind, path in [("anchor", a_path), ("known-bad", b_path)]:
            ax = fig.add_subplot(2, 3, idx, projection="3d")
            idx += 1
            if not path.exists():
                ax.set_title(f"{subset} {kind}\n(missing)", fontsize=9)
                ax.set_axis_off()
                continue
            df = _sample(pd.read_csv(path), seed=idx)
            pred = df["pred"].astype(int)
            colors = [SEGMENT_COLORS.get(int(p), "#888") for p in pred]
            ax.scatter(df["x"], df["y"], df["z"], c=colors, s=0.25, linewidths=0, alpha=0.9)
            ax.set_title(f"{subset} · {kind}\n({fam})", fontsize=9)
            ax.set_axis_off()
            ax.view_init(elev=18, azim=45)

    fig.suptitle(
        "Proxy4Tun holdout: sibling-anchor vs known-bad overlays (3D sample)",
        fontsize=12,
        y=0.98,
    )
    fig.tight_layout()
    OUT_PNG.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT_PNG, dpi=200, bbox_inches="tight")
    fig.savefig(OUT_PDF, bbox_inches="tight")
    plt.close(fig)
    print(f"Wrote {OUT_PNG}")
    print(f"Wrote {OUT_PDF}")

    # Optional interactive HTML if plotly is available
    try:
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots

        titles = []
        for subset, fam in PAIRS:
            titles += [f"{subset} anchor ({fam})", f"{subset} known-bad"]
        fig3 = make_subplots(
            rows=2,
            cols=3,
            subplot_titles=titles,
            specs=[[{"type": "scatter3d"}] * 3 for _ in range(2)],
            horizontal_spacing=0.02,
            vertical_spacing=0.04,
        )
        i = 0
        for subset, _fam in PAIRS:
            for path in _paths(subset):
                r, c = divmod(i, 3)
                r += 1
                c += 1
                i += 1
                if not path.exists():
                    continue
                df = _sample(pd.read_csv(path), n=10000, seed=i)
                pred = df["pred"].astype(int)
                for lab in sorted(pd.unique(pred)):
                    sub = df[pred == lab]
                    fig3.add_trace(
                        go.Scatter3d(
                            x=sub["x"],
                            y=sub["y"],
                            z=sub["z"],
                            mode="markers",
                            marker=dict(size=1.3, color=SEGMENT_COLORS.get(int(lab), "#888"), opacity=0.85),
                            showlegend=False,
                            hoverinfo="skip",
                        ),
                        row=r,
                        col=c,
                    )
        fig3.update_layout(height=640, width=1100, margin=dict(l=0, r=0, t=40, b=0))
        OUT_HTML.parent.mkdir(parents=True, exist_ok=True)
        fig3.write_html(str(OUT_HTML), include_plotlyjs="cdn")
        print(f"Wrote {OUT_HTML}")
    except Exception as e:
        print(f"HTML export skipped: {e}")


if __name__ == "__main__":
    main()
