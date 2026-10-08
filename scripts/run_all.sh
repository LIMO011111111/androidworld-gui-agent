#!/usr/bin/env bash
# Runs all 9 evaluation runs (3 tasks x 3 runs) of one config unattended.
# The emulator is restarted fresh before every run (it tends to crash after
# ~20-30 min on a 16 GB MacBook Air); a run that ends as ERROR is retried once.
#
#   bash scripts/run_all.sh                         # V4 (default)
#   bash scripts/run_all.sh configs/v2_index.json   # any other version
set -u
cd "$(dirname "$0")/.."
mkdir -p runs
set +u
# shellcheck disable=SC1091
source .venv/bin/activate
set -u

SDK="${ANDROID_HOME:-$HOME/Library/Android/sdk}"
ADB="$SDK/platform-tools/adb"
CONFIG="${1:-configs/v4_tracker.json}"
EMU_LOG="runs/emulator_run_all.log"

stop_emulator() {
  "$ADB" emu kill >/dev/null 2>&1 || true
  sleep 3
  pkill -f "qemu-system.*AndroidWorldAvd" >/dev/null 2>&1 || true
  pkill -f "emulator.*AndroidWorldAvd" >/dev/null 2>&1 || true
  sleep 3
}

start_emulator() {
  stop_emulator
  echo "  starting emulator ..."
  HEADLESS=1 nohup bash scripts/start_emulator.sh >>"$EMU_LOG" 2>&1 &
  for _ in $(seq 1 100); do
    if [ "$("$ADB" shell getprop sys.boot_completed 2>/dev/null | tr -d '\r')" = "1" ]; then
      sleep 15  # let the launcher and services settle
      echo "  emulator ready"
      return 0
    fi
    sleep 3
  done
  echo "  emulator did not finish booting"
  return 1
}

row_count() {
  python -c "from gui_agent import evallog; print(len(evallog.read_rows('runs/log.csv')))"
}

last_verdict() {
  python -c "from gui_agent import evallog; r = evallog.read_rows('runs/log.csv'); print(r[-1]['verifier'] if r else '')"
}

run_one() {  # $1 = task, $2 = run index
  for attempt in 1 2; do
    echo
    echo "=== $1, run $2 (attempt $attempt of 2) ==="
    if ! start_emulator; then
      continue
    fi
    rows_before="$(row_count)"
    caffeinate -i python run_eval.py --config "$CONFIG" --tasks "$1" --run_indices "$2" \
      2>>runs/run_all_errors.log
    verdict="$(last_verdict)"
    if [ "$(row_count)" = "$rows_before" ]; then
      verdict="ERROR"  # run_eval.py died before writing a row
    fi
    echo "  -> $verdict"
    if [ "$verdict" != "ERROR" ]; then
      return 0
    fi
  done
  echo "  giving up on $1 run $2 (stays ERROR)"
}

for task in ContactsAddContact MarkorCreateNote MarkorCreateNoteAndSms; do
  for i in 1 2 3; do
    run_one "$task" "$i"
  done
done

stop_emulator
echo
python summarize.py
echo
echo "Done. Send the summary above to Claude."
