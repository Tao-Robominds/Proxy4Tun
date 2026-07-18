#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
PY=./venv/bin/python
OUT=data/cleanup-verify
mkdir -p logs

run_case() {
  local case="$1" profile="$2" params="$3"
  echo "========== $case =========="
  $PY -m sam4tun.pipeline \
    "data/subsets/${case}.txt" "${OUT}/${case}" \
    --profile "$profile" \
    --params-dir "$params" \
    --overwrite \
    2>&1 | tee "logs/cleanup-verify-${case}.log"
}

run_case 1-1 't1&2' 'anchors/t1&2/1-1'
run_case 2-1 't1&2' 'anchors/t1&2/2-1'
run_case 3-1-1 t3 anchors/t3/3-1-1
run_case 4-1 't4&5' 'anchors/t4&5/4-1'
run_case 5-1 't4&5' 'anchors/t4&5/5-1'

echo "========== mIoU summary =========="
for case in 1-1 2-1 3-1-1 4-1 5-1; do
  perf="${OUT}/${case}/evaluation/performance.md"
  miou=$(grep -m1 'Mean IoU' "$perf" | sed -E 's/.*: *//')
  echo "${case}: ${miou}"
done
