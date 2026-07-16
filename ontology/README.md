# SAM4Tun Functional Ontology

A functional ontology of the **SAM4Tun** tunnel-lining point-cloud segmentation
pipeline, designed to let **staged LLM agents** analyse the state of each pipeline
stage and suggest parameter changes.

- **Focus:** SAM4Tun (the pipeline implemented in `notebook/t1&2.ipynb`,
  `notebook/t3.ipynb`, `notebook/t4&5.ipynb`; paper `notebook/paper/sam4tun.pdf`).
- **Seg2Tunnel role:** prior knowledge only — the per-tunnel constants for
  T1–T5 live in `tunnel_priors.yaml`. Seg2Tunnel is *not* modelled as a pipeline.
- The former Algorithm 4 is modelled as **two independent stages/algorithms**:
  - `stage_4_detection` (**Algorithm 4**) — joint / segment **prompt-centre detection**
  - `stage_5_segmentation` (**Algorithm 5**) — **SAM template-prompt segmentation + reprojection**

## Files

| File | Content |
|------|---------|
| `sam4tun_functional_ontology.yaml` | The ontology: artifacts, stages, parameters, quality metrics, failure modes, diagnostic rules, remediation actions, inter-stage dependencies, and the agent interface. |
| `tunnel_priors.yaml` | Seg2Tunnel-derived per-tunnel priors (T1–T5): diameter, radius/theta gates, block geometry, Hough settings, up-sampling schedule, etc. |

## Pipeline stages

```
raw point cloud
  │
  ▼  Algorithm 1  ── stage_1_centreline   (axis → slices → ellipse centres → 3D curve → h,θ,r)
  ▼  Algorithm 2  ── stage_2_denoise      (radial gate + density/gradient filtering → pred=9 lining)
  ▼  Algorithm 3  ── stage_3_upsample     (surface + joint up-sampling → unrolled depth map + pixel↔point)
  ▼  Algorithm 4  ── stage_4_detection    (outlier map → Hough lines → distance pattern → prompt centres)
  ▼  Algorithm 5  ── stage_5_segmentation (SAM template prompts → masks → label/ring maps → reproject to 3D)
  │
  ▼ segmented point cloud (pred, pred_ring)
```

## How a staged agent uses the ontology

Each stage has one agent. The workflow per agent:

1. **Build a `State`** (see `agent_interface.state`): the current stage id,
   `tunnel_id` (selects the T1–T5 profile in `tunnel_priors.yaml`), which
   artifacts are present, current parameter values, and measured
   `quality_metrics`.
2. **Diagnose**: evaluate `diagnostic_rules` for the stage → matched
   `failure_modes`.
3. **Check upstream**: consult `inter_stage_dependencies`. If a matched failure
   is likely *caused* by an earlier stage (`likely_upstream`), defer to that
   stage's agent before changing local parameters.
4. **Propose**: emit ordered `remediation_actions` with concrete parameter
   deltas, honouring each action's `precondition` (e.g. "resolution unchanged"
   because pixel-domain priors derive from it).

### Key modelling choices

- **`tunnel_dependent: true`** parameters are resolved from `tunnel_priors.yaml`
  by `prior_ref`. Agents should always confirm the tunnel profile before
  suggesting a value.
- **Pixel-domain priors are derived, not hardcoded** (see `derivations` in
  `tunnel_priors.yaml`), so changing `resolution` rescales them consistently.
- **Causal chains** (`inter_stage_dependencies`) capture the most common
  cross-stage error propagation, e.g. a misplaced `n_segment` (stage 3) breaks
  the joint distance pattern (stage 4), which then offsets SAM crops (stage 5).

## Notes / open items

- Threshold values in the ontology are **symbolic**; numeric trigger points
  should be calibrated on real data per tunnel.
- `n_segment_hint` is **coverage-dependent** (half vs full station) and is the
  most frequently retuned parameter — flagged in both files.
- `generate_prompt_points` carries inner defaults (`segment_width=1200`,
  `K_height=1079.92`, `AB_height=3239.77`) that can shadow the tunnel-specific
  `process_row` values if not overridden — flagged in `tunnel_priors.yaml`
  (`defaults.prompt_inner_defaults`) for review.
- Some T3/T4/T5 detection tolerances are not explicit in the notebooks and are
  left `null` to be calibrated.
