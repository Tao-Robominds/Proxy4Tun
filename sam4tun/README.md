# SAM4Tun five-stage pipeline

The code in this package is extracted from:

- `notebook/t1&2.ipynb`
- `notebook/t3.ipynb`
- `notebook/t4&5.ipynb`

The notebooks, their figures, tables and cell outputs are not modified. The
Python pipeline persists the equivalent runtime artifacts in a form that can be
resumed and inspected by an LLM agent.

## Stages and state contract

| Stage | Module | Main persisted artifacts |
|---|---|---|
| 1 Centreline | `stages/stage1_centreline.py` | raw/unwrapped cloud, slices, ellipse fits, centre curve |
| 2 Denoise | `stages/stage2_denoise.py` | denoised cloud, lining candidates, density cutoffs |
| 3 Upsample | `stages/stage3_upsample.py` | enhanced surface/joints, depth map PNG/NPY, pixel-to-point map |
| 4 Detection | `stages/stage4_detection.py` | outlier map, dilated edges, Hough lines, `initial_points.csv` |
| 5 Segmentation | `stages/stage5_segmentation.py` | `results.pkl`, logit/label/ring maps, final point cloud and evaluation labels |

Every stage writes `manifest.json`, containing:

- the exact parameter values used;
- output artifact paths and media types;
- stage quality metrics;
- the preceding manifest path.

The next stage receives the preceding manifest, not notebook globals. Large
objects stay in CSV, NPY, PNG or PKL files; the manifest contains paths only.

## Reference profiles

Pipeline code does not branch on T1–T5. The three reference profiles describe
observable geometry and acquisition characteristics:

| Notebook reference | Feature profile | Main extracted values |
|---|---|---|
| T1/T2 | `compact_six_segment_railway` | 6 segments, 5.5 m diameter, 1.2 m pitch, bottom railway, K/AB 1079.92/3239.77 mm, taper 7.52°, radial band 2.7–2.8 m |
| T3 | `shallow_key_six_segment_sparse_joint` | 6 segments, 5.9 m diameter, shallow K=823.8 mm, sparse-joint Hough settings, theta gate 1.55–17.15 m |
| T4/T5 | `large_seven_segment_top_tube` | 7 segments, 7.5 m diameter, 1.8 m pitch, top service tube, K/AB 1226.97/3726.88 mm, taper 9.8°, radial band 3.65–3.9 m |

Implementation differences are represented by:

- `GeometryConfig`: layout and physical dimensions;
- `Stage1Config.obstruction`: railway, top tube or no obstruction;
- density/radial/angular settings in stages 2 and 3;
- `CoverageConfig`: left, centre or absolute reliable detection band;
- Hough sensitivity and taper-derived angle windows;
- geometry-derived prompt templates and sealing-band mode.

`NOTEBOOK_REFERENCE` in `config.py` records provenance only. No stage imports or
tests a tunnel id.

## Run

Install:

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pip install -e . --no-deps
```

Cursor Cloud performs these commands automatically through
`.cursor/environment.json`. No Docker environment is required.

Run stages 1–4 without requiring SAM:

```bash
python -m sam4tun.pipeline sample.txt output \
  --profile compact_six_segment_railway \
  --through-stage 4
```

Run all five stages after installing Meta Segment Anything and configuring the
checkpoint path:

```python
from dataclasses import replace
from sam4tun import get_reference_config, run_pipeline

config = get_reference_config("large_seven_segment_top_tube")
config = replace(
    config,
    stage5=replace(
        config.stage5,
        sam_checkpoint="/models/sam_vit_h_4b8939.pth",
        device="cuda",
    ),
)
manifest = run_pipeline("scan.txt", "run", config)
```

Each stage can also run independently:

```python
from sam4tun.stages import run_stage3

stage3_manifest = run_stage3(
    "run/stage2_denoise/manifest.json",
    "run/stage3_upsample",
    config.geometry,
    config.stage3,
    config.profile,
)
```

## Intentional corrections to notebook code

The extraction fixes notebook defects rather than encoding them as tunnel-id
branches:

- T3's upper theta gate compares `theta`, not `r`;
- `ring_count` and all geometry values are explicit parameters;
- the T3 projection uses the enhanced surface instead of accidentally
  overwriting it with the original candidate cloud;
- Stage 4 safely handles a missing Hough result and replaces hard-coded
  fallback pixel Y values with configurable geometric fallbacks;
- Stage 5 forwards real geometry to prompt generation instead of silently using
  T1/T2 defaults;
- boundary crops are clipped consistently during mask/logit merge;
- unassigned pixels retain ring `-1`, rather than becoming the last ring.

These choices are documented in manifests and can be changed through meaningful
configuration fields when reproducing a historical notebook run is necessary.
