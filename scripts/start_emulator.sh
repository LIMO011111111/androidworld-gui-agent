#!/usr/bin/env bash
# Starts the emulator the way AndroidWorld needs it: from the command line,
# without a snapshot, with the gRPC port for the accessibility forwarder.
#
#   bash scripts/start_emulator.sh            # with a window
#   HEADLESS=1 bash scripts/start_emulator.sh # no window (recording still works)
set -euo pipefail

AVD_NAME="${AVD_NAME:-AndroidWorldAvd}"
SDK="${ANDROID_HOME:-$HOME/Library/Android/sdk}"
if [ ! -x "$SDK/emulator/emulator" ] && [ -x "$HOME/Android/Sdk/emulator/emulator" ]; then
  SDK="$HOME/Android/Sdk"   # Linux default
fi
EMULATOR="$SDK/emulator/emulator"
if [ ! -x "$EMULATOR" ]; then
  echo "Emulator not found at $EMULATOR. Set ANDROID_HOME or install the Android SDK." >&2
  exit 1
fi

args=(-avd "$AVD_NAME" -no-snapshot -grpc 8554)
if [ "${HEADLESS:-0}" = "1" ]; then
  args+=(-no-window)
fi
echo "Starting: $EMULATOR ${args[*]}"
exec "$EMULATOR" "${args[@]}"
