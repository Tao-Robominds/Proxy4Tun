#!/usr/bin/env python3
"""Rasterize every PDF in this directory to 300 DPI PNG (same folder).

Usage (from anywhere):
  python manuscript/figs/render_pngs.py

Requires: pip install pymupdf
"""

from __future__ import annotations

import sys
from pathlib import Path

try:
    import fitz
except ImportError:
    sys.exit("Missing dependency. Install with: pip install pymupdf")

DPI = 300
FIGS_DIR = Path(__file__).resolve().parent


def render_pdf(pdf: Path, dpi: int = DPI) -> list[Path]:
    zoom = dpi / 72.0
    matrix = fitz.Matrix(zoom, zoom)
    doc = fitz.open(pdf)
    outputs: list[Path] = []
    try:
        if doc.page_count == 1:
            out = pdf.with_suffix(".png")
            doc[0].get_pixmap(matrix=matrix, alpha=False).save(out)
            outputs.append(out)
        else:
            for i in range(doc.page_count):
                out = pdf.with_name(f"{pdf.stem}-{i + 1}.png")
                doc[i].get_pixmap(matrix=matrix, alpha=False).save(out)
                outputs.append(out)
    finally:
        doc.close()
    return outputs


def main() -> int:
    pdfs = sorted(FIGS_DIR.glob("*.pdf"))
    if not pdfs:
        print(f"No PDFs found in {FIGS_DIR}")
        return 1

    print(f"Rendering {len(pdfs)} PDF(s) at {DPI} DPI -> {FIGS_DIR}")
    for pdf in pdfs:
        outputs = render_pdf(pdf)
        for out in outputs:
            print(f"  {pdf.name} -> {out.name}")
    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
