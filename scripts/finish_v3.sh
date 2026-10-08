#!/usr/bin/env bash
# Runs the missing V3 runs unattended. Before every single run the emulator is
# restarted fresh (it tends to crash after ~20-30 min on a 16 GB MacBook Air).
# A run that ends as ERROR (emulator crash) is retried once. Finally the
# summary is rebuilt.
#
#   bash scripts/finish_v3.sh
set -u
cd "$(dirname "$0")/.."
# shellcheck disable=SC1091
source .venv/bin/activate

SDK="${ANDROID_HOME:-$HOME/Library/Android/sdk}"
ADB="$SDK/platform-tools/adb"
CONFIG="configs/v3_full.json"
EMU_LOG="runs/emulator_finish_v3.log"

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
  "$ADB" wait-for-device
  for _ in $(seq 1 80); do
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
    caffeinate -i python run_eval.py --config "$CONFIG" --tasks "$1" --run_indices "$2" \
      2>>runs/finish_v3_errors.log
    verdict="$(last_verdict)"
    echo "  -> $verdict"
    if [ "$verdict" != "ERROR" ]; then
      return 0
    fi
  done
  echo "  giving up on $1 run $2 (stays ERROR)"
}

run_one ContactsAddContact 2
run_one ContactsAddContact 3
run_one MarkorCreateNoteAndSms 1
run_one MarkorCreateNoteAndSms 2
run_one MarkorCreateNoteAndSms 3

stop_emulator
echo
python summarize.py
echo
echo "Done. Send the summary above to Claude."
