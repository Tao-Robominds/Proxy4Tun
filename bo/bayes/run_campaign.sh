#!/usr/bin/env bash
# Full Bayesian-exploration campaign: 24 Sobol + 16 GP per train anchor.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
PY="$ROOT/venv/bin/python"
LOGDIR="$ROOT/bo/bayes/logs"
mkdir -p "$LOGDIR" "$ROOT/data/bo/bayes"

N0="${N0:-24}"
NGP="${NGP:-16}"
SEED="${SEED:-0}"

for case in 2-1 3-1 5-1; do
  echo "===== $(date -Is) START $case N0=$N0 N_GP=$NGP =====" | tee -a "$LOGDIR/campaign.log"
  "$PY" "$ROOT/bo/bayes/run_bayes_trials.py" \
    --case "$case" --n0 "$N0" --n-gp "$NGP" --seed "$SEED" \
    2>&1 | tee -a "$LOGDIR/${case}.log"
  echo "===== $(date -Is) DONE $case =====" | tee -a "$LOGDIR/campaign.log"
done

echo "===== $(date -Is) ALL CASES DONE =====" | tee -a "$LOGDIR/campaign.log"
