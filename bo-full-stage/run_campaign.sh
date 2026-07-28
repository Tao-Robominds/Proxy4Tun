#!/usr/bin/env bash
# Launch new full-pipeline trials (gate trial already done for 3-1; smoke for 2-1).
# Targets: 2-1 26 ok, 3-1 10 ok (1 gate + 9), 5-1 19 ok
set -euo pipefail
cd "$(dirname "$0")/.."
PY=./venv/bin/python
LOG=data/bo-full-stage/campaign.log
mkdir -p data/bo-full-stage

count_ok() {
  local case="$1"
  $PY - <<PY
import json
from pathlib import Path
p=Path("data/bo-full-stage/${case}-trials/manifest.json")
if not p.exists():
    print(0)
else:
    m=json.loads(p.read_text())
    print(sum(1 for t in m.get("trials",[]) if t.get("status")=="ok" and t.get("mIoU") is not None))
PY
}

{
  need21=$((26 - $(count_ok 2-1)))
  echo "=== $(date -Is) start 2-1 need=$need21 ==="
  if [ "$need21" -gt 0 ]; then
    $PY bo-full-stage/run_trials_full.py --case 2-1 --n "$need21" --start-index 0 --seed 42
  fi

  need31=$((10 - $(count_ok 3-1)))
  echo "=== $(date -Is) start 3-1 need=$need31 ==="
  if [ "$need31" -gt 0 ]; then
    $PY bo-full-stage/run_trials_full.py --case 3-1 --n "$need31" --start-index 1 --seed 43
  fi

  need51=$((19 - $(count_ok 5-1)))
  echo "=== $(date -Is) start 5-1 need=$need51 ==="
  if [ "$need51" -gt 0 ]; then
    $PY bo-full-stage/run_trials_full.py --case 5-1 --n "$need51" --start-index 0 --seed 44
  fi
  echo "=== $(date -Is) campaign done ==="
  echo "ok counts: 2-1=$(count_ok 2-1) 3-1=$(count_ok 3-1) 5-1=$(count_ok 5-1)"
} 2>&1 | tee -a "$LOG"
