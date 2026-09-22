# Release 2 degradation gate

## 1-2 — pass

- Command: `./venv/bin/python -u bo/release2/run_pair.py --gate`
- Reference: valid=True, score=0.7201063837582617, mIoU=0.809, elapsed=274.4 s (budget 425 s)
- Degraded: valid=True, score=0.16564085763663905, mIoU=0.032, elapsed=188.5 s
- Overlay matches frozen selection: True
- Stage-1 unwrapped.csv hash equal: True
- Reference record: `/home/boringtao/Projects/Proxy4Tun/data/release2/references/1-2/record.json`
- Degraded record: `/home/boringtao/Projects/Proxy4Tun/data/release2/degradation/1-2/record.json`
