# Manuscript figures

PDF vector figures live here. High-resolution PNG exports (300 DPI) sit next to each PDF:

- `pipeline.pdf` → `pipeline.png`
- `motivation.pdf` → `motivation.png`
- etc.

## Generate PNGs locally

If `*.png` files are missing after `git pull`, render them from the PDFs:

```bash
pip install pymupdf
python manuscript/figs/render_pngs.py
```

Or from this directory:

```bash
cd manuscript/figs
pip install pymupdf
python render_pngs.py
ls *.png
```
