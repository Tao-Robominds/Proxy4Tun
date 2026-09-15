#!/usr/bin/env bash
set -euo pipefail
cd /home/boringtao/Projects/Proxy4Tun
STAGE3=data/sc-general/stage3
mkdir -p "$STAGE3/logs"
PANEL=(1-5 1-1 1-4 1-2 2-4 2-2 3-3 3-7 3-8 3-10 3-9 3-6 4-3 4-2 4-1 4-5 5-5 5-3 5-2 5-4)
MAX=2

is_done() { [[ -f "$STAGE3/selections/${1}.json" ]]; }

workers() {
  ps -eo pid=,args= | awk '/\.\/venv\/bin\/python bo\/sc_general\/run_campaign\.py --subset/ {print $1, $0}'
}

running_count() { workers | wc -l; }

is_running() {
  workers | grep -E -- "--subset ${1}( |$)" >/dev/null
}

launch() {
  local s="$1" from="${2:-1}"
  echo "[$(date -Iseconds)] launch $s from-round=$from"
  PYTHONUNBUFFERED=1 nohup ./venv/bin/python bo/sc_general/run_campaign.py --subset "$s" --from-round "$from" \
    > "$STAGE3/logs/run_${s}.log" 2>&1 &
}

ALL=(1-3 3-4 "${PANEL[@]}")
while true; do
  for s in "${ALL[@]}"; do
    if is_done "$s"; then continue; fi
    if is_running "$s"; then continue; fi
    # resume from next missing round
    fr=1
    [[ -f "data/${s}-scgen-refinement/round1/reflection_record.json" ]] && fr=2
    [[ -f "data/${s}-scgen-refinement/round2/reflection_record.json" ]] && fr=3
    if [[ -f "data/${s}-scgen-refinement/round3/reflection_record.json" ]]; then
      echo "[$(date -Iseconds)] select only $s"
      PYTHONUNBUFFERED=1 ./venv/bin/python bo/sc_general/select_round.py --subset "$s" \
        > "$STAGE3/logs/select_${s}.log" 2>&1 || true
      continue
    fi
    while [[ "$(running_count)" -ge "$MAX" ]]; do
      echo "[$(date -Iseconds)] waiting slots (running=$(running_count))"
      sleep 30
    done
    launch "$s" "$fr"
    sleep 2
  done

  all_done=1
  for s in "${ALL[@]}"; do
    if ! is_done "$s"; then all_done=0; break; fi
  done
  if [[ "$all_done" -eq 1 ]] && [[ "$(running_count)" -eq 0 ]]; then
    echo "[$(date -Iseconds)] ALL DONE"
    break
  fi
  echo "[$(date -Iseconds)] progress: selections=$(ls "$STAGE3/selections" 2>/dev/null | wc -l)/22 running=$(running_count)"
  sleep 45
done
