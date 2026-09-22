# Release 2 refinement gate

## 1-1 — pass

- Command: `./venv/bin/python -u bo/release2/refine.py --run-random-case 1-1` then Fable emit/apply round 1
- Random r1: valid=True verdict=accepted score=0.619 elapsed=256 s
- Random r2: valid=True verdict=rejected score=0.227 elapsed=192 s
- Random r3: valid=True verdict=rejected score=0.091 elapsed=187 s
- Selection: start (score 0.614) under 0.01 tie vs r1 0.619; incumbent during loop = r1
- Packet GT-free: True; examples in Fable packet: 3
- Fable r1: valid=True verdict=rejected score=0.6034802098852765 mIoU=0.784 elapsed=287.9 s
- Emit round 2 after r1 succeeds with feedback (score 0.614 → 0.603, verdict=rejected)

