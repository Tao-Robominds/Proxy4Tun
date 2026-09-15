# Single-instance validation gate — GPT-5.6 isolated refinement

Date: 2026-07-29. Representative case: **subset 3-4** (continuous / t3),
GT-low (anchor mIoU 0.622), refine-band scaled proxy 0.574, stage-1 unlocked
(residual 20.8 cm).

## Isolation proof

| Check | Evidence |
|---|---|
| Model | GPT-5.6 Sol (`gpt-5.6-sol-medium`), fresh context agent `58d485de-4d09-4ae5-8d81-655c14f7cf69` |
| Allowed inputs | `gpt56-refinement/packets/3-4/*`, `gpt56-refinement/knowledge/*` |
| Denied inputs | `data/bo/reflect/**`, Fable recipes, selections, raw `experiences.md`, `evaluation/` during proposals |
| Knowledge snapshot | `experiences_sanitized.md` (no §8 / §11–12 / Fable refs); hashes in `knowledge/hashes.json` |
| Output tree | `data/3-4-gpt56-refinement/` (not anchors/baseline/bo/reflect) |

## Commands / lineage

```bash
./venv/bin/python gpt56-refinement/build_packet.py --subset 3-4
# GPT-5.6 Sol proposes → packets/3-4/round{N}_proposal.json
./venv/bin/python gpt56-refinement/run_round.py --subset 3-4 --round N --proposal-json ...
./venv/bin/python gpt56-refinement/select_round.py --subset 3-4
```

## Round outcomes (proxy-selected; mIoU offline)

| Round | Overlay summary | Proxy scaled | Δproxy | Residual cm | mIoU offline |
|---|---|---:|---:|---:|---:|
| anchor | — | 0.574 | — | 20.8 | 0.622 |
| round1 | poly3 + tighter RANSAC + denoise priors | 0.135 | −0.439 | 32.9 | 0.517 |
| round2 | rollback poly2 / RANSAC 1.0 | 0.574 | 0.000 | 20.8 | 0.622 |
| round3 | uniform_k_snap + T3 SAM geometry | 0.574 | 0.000 | 20.8 | 0.622 |

Selected: **anchor** (monotone accept: no round beat anchor scaled proxy).
ΔmIoU offline = 0.000.

## Pass criteria

| Check | Criterion | Result |
|---|---|---|
| 3/3 rounds complete | status=ok | yes |
| Overlay validation | within family bounds | yes |
| Scaled proxy finite | frozen pooled scorer | yes |
| GT-blind selection | no mIoU in agent_feedback | yes |
| Isolation | denylist not used in proposals | yes (prompt-enforced + packet-only) |
| Output path | `data/3-4-gpt56-refinement/` | yes |

## Verdict

**GATE: PASS — proceed to the remaining 8 subsets.**

Note: GPT-5.6 did not improve this gate case; that is an acceptable PoC outcome
and does not block scaling. The harness, isolation, and selection rules are verified.
