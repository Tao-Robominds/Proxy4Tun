# Release 2 GPT-5.6 medium gate

## 1-1 — pass

- Case: `1-1`
- Model: `gpt-5.6-sol-medium` (arm `gpt56_medium`, agent `fbce82ce-26d2-4164-b6ae-f400f21d4c95`)
- Lineage: emit packet, one proposal, then execute, then the next round. Commands:
  - `./venv/bin/python -u bo/release2/drive_llm_arm.py --prepare 1-1 --arm gpt56_medium`
  - `./venv/bin/python -u bo/release2/drive_llm_arm.py --apply-file 1-1 --arm gpt56_medium --round R --proposal data/release2/refinement/gpt56_medium/1-1/proposals/roundR_proposal.json`
  - `./venv/bin/python -u bo/release2/drive_llm_arm.py --finish 1-1 --arm gpt56_medium`
- Criteria: packet has no `gt_miou` or `gt_labels`; provenance is `gpt-5.6-sol-medium`; three records are valid or explicitly failed; selection uses max score with a 0.01 tie kept by earlier order; next proposal only after the previous record exists.

| round | valid | verdict | score | gt_miou | elapsed_s | model |
| --- | --- | --- | --- | ---: | ---: | ---: | --- |
| 1 | True | rejected | 0.6115 | 0.784 | 258 | gpt-5.6-sol-medium |
| 2 | True | accepted | 0.6150 | 0.784 | 256 | gpt-5.6-sol-medium |
| 3 | True | rejected | 0.6150 | 0.784 | 257 | gpt-5.6-sol-medium |

- Start score 0.6140. Round 2 is a strict proxy improvement, but it is within 0.01 of the start, so the frozen tie rule keeps `start`.
- Packet GT-free: True. Feedback GT-free: True. Stage-1 locked: True.
- Evidence: `data/release2/refinement/gpt56_medium/1-1/round{1,2,3}/record.json` and `data/release2/refinement/records/selections/gpt56_medium/1-1.json`.
