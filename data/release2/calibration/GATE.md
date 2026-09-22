# Release 2 calibration gate

## 2-1 — pass

- Command: `./venv/bin/python -u bo/release2/calibrate.py --dev 2-1 --gate --seed 2`
- Sobol: valid=True, mIoU=0.476, in_bounds=True, elapsed=314.2 s (budget 425 s)
- GP: valid=True, mIoU=0.438, in_bounds=True, sigma=0.1509, elapsed=301.7 s
- Sobol record: `/home/boringtao/Projects/Proxy4Tun/data/release2/calibration/2-1/runs/s000/record.json`
- GP record: `/home/boringtao/Projects/Proxy4Tun/data/release2/calibration/2-1/runs/g000/record.json`

