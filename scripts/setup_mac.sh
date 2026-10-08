#!/usr/bin/env bash
# One-time setup on macOS. Safe to run again: every step checks first.
#
#   bash scripts/setup_mac.sh
#
# What it does:
#   1. Python 3.11 environment in .venv (via uv)
#   2. AndroidWorld, pinned to the commit this agent was tested against
#   3. Android emulator image + the AVD "AndroidWorldAvd" (Pixel 6, API 33)
#   4. The local model in Ollama
#   5. The unit tests of this repo
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

ANDROID_WORLD_COMMIT="${ANDROID_WORLD_COMMIT:-2dfc5ca3dc590efe9c72ce768f2b04182f2f75c7}"
MODEL="${MODEL:-qwen3-vl:4b-instruct}"
AVD_NAME="${AVD_NAME:-AndroidWorldAvd}"
SDK="${ANDROID_HOME:-$HOME/Library/Android/sdk}"

say()  { printf '\n\033[1m==> %s\033[0m\n' "$*"; }
warn() { printf '\033[33m    ! %s\033[0m\n' "$*"; }
todo=()

# --- 0. Disk space -----------------------------------------------------------
free_gb="$(df -g "$HOME" 2>/dev/null | awk 'NR==2 {print $4}' || true)"
free_gb="${free_gb:-0}"
say "Free disk space: ${free_gb} GB"
if [ "$free_gb" -lt 20 ]; then
  warn "Emulator image, AVD data, AndroidWorld apps and the model need about 15-20 GB."
fi

# --- 1. Tools ----------------------------------------------------------------
say "Command-line tools"
if ! command -v brew >/dev/null 2>&1 && [ -x /opt/homebrew/bin/brew ]; then
  eval "$(/opt/homebrew/bin/brew shellenv)"   # Homebrew installed, not on PATH
fi
if ! command -v brew >/dev/null 2>&1; then
  echo "Homebrew is required: https://brew.sh" >&2
  exit 1
fi
for tool in uv ffmpeg; do
  if ! command -v "$tool" >/dev/null 2>&1; then
    brew install "$tool"
  fi
done

# --- 2. Python environment + AndroidWorld -----------------------------------
say "Python 3.11 environment (.venv)"
if [ ! -x .venv/bin/python ]; then
  uv venv --seed --python 3.11 .venv
fi
PY="$REPO_ROOT/.venv/bin/python"

say "AndroidWorld at commit ${ANDROID_WORLD_COMMIT:0:7}"
if [ ! -d third_party/android_world/.git ]; then
  mkdir -p third_party
  git clone https://github.com/google-research/android_world.git third_party/android_world
fi
git -C third_party/android_world fetch --quiet origin || true
git -C third_party/android_world checkout --quiet "$ANDROID_WORLD_COMMIT"
"$PY" -m pip install --quiet -r third_party/android_world/requirements.txt
"$PY" -m pip install --quiet setuptools
(cd third_party/android_world && "$PY" setup.py install >/dev/null)
"$PY" -m pip install --quiet -r requirements.txt

# --- 3. Android SDK, emulator, AVD ------------------------------------------
say "Android SDK at $SDK"
# `uname -m` says x86_64 inside a Rosetta terminal, so ask the hardware.
if [ "$(uname -m)" = "arm64" ] || [ "$(sysctl -n hw.optional.arm64 2>/dev/null || echo 0)" = "1" ]; then
  ABI="arm64-v8a"
else
  ABI="x86_64"
fi
IMAGE="system-images;android-33;google_apis;${ABI}"
SDKMANAGER="$SDK/cmdline-tools/latest/bin/sdkmanager"
AVDMANAGER="$SDK/cmdline-tools/latest/bin/avdmanager"
# macOS ships a /usr/bin/java stub that exists but fails when no JDK is
# installed, so test that Java actually runs. Prefer Android Studio's own JDK.
have_java() { java -version >/dev/null 2>&1; }
STUDIO_JAVA="/Applications/Android Studio.app/Contents/jbr/Contents/Home"
if [ -x "$STUDIO_JAVA/bin/java" ]; then
  export JAVA_HOME="$STUDIO_JAVA"
  export PATH="$JAVA_HOME/bin:$PATH"
fi

avd_exists() {
  [ -x "$SDK/emulator/emulator" ] || return 1
  "$SDK/emulator/emulator" -list-avds 2>/dev/null | grep -x "$AVD_NAME" >/dev/null
}

if avd_exists; then
  echo "    AVD $AVD_NAME already exists."
elif [ -x "$SDKMANAGER" ] && have_java; then
  echo "    Accepting the Android SDK licences and installing the API 33 image."
  yes | "$SDKMANAGER" --licenses >/dev/null || true
  if "$SDKMANAGER" "platform-tools" "emulator" "platforms;android-33" "$IMAGE" \
      && echo "no" | "$AVDMANAGER" create avd -n "$AVD_NAME" -k "$IMAGE" -d pixel_6; then
    echo "    Created AVD $AVD_NAME."
  else
    warn "sdkmanager / avdmanager failed."
    todo+=("Create the AVD by hand in Android Studio: Virtual Device Manager > Create Device > Pixel 6 > Tiramisu (API 33, ${ABI}, target 'Google APIs', not 'Google Play') > name it ${AVD_NAME}.")
  fi
else
  warn "Could not create the AVD automatically (no SDK command-line tools or no working Java)."
  todo+=("If Android Studio is not installed: brew install --cask android-studio, then open it once so it installs the SDK.")
  todo+=("Either install 'Android SDK Command-line Tools (latest)' in Android Studio (SDK Manager > SDK Tools) and run this script again, or create the AVD by hand: Virtual Device Manager > Create Device > Pixel 6 > Tiramisu (API 33, ${ABI}, target 'Google APIs', not 'Google Play') > name it ${AVD_NAME}.")
fi
if [ ! -x "$SDK/platform-tools/adb" ]; then
  todo+=("adb is missing at $SDK/platform-tools/adb (it comes with the Android SDK).")
fi

# --- 4. Model ----------------------------------------------------------------
say "Model $MODEL"
if command -v ollama >/dev/null 2>&1; then
  ollama pull "$MODEL" || {
    warn "ollama pull failed. Open the Ollama app, and update it if it is older than 0.12.7."
    todo+=("ollama pull $MODEL")
  }
else
  todo+=("Install Ollama (https://ollama.com/download), open it once, then: ollama pull $MODEL")
fi

# --- 5. Tests ----------------------------------------------------------------
say "Unit tests"
"$PY" -m pytest -q tests || warn "Some unit tests failed (see above)."

say "Setup finished"
if [ "${#todo[@]}" -gt 0 ]; then
  echo "Still to do by hand:"
  for item in "${todo[@]}"; do echo "  - $item"; done
fi
cat <<'NEXT'

Next steps:
  1. Terminal A:  bash scripts/start_emulator.sh           (leave it running)
  2. Terminal B:  source .venv/bin/activate
                  python scripts/doctor.py
  3. First run only, installs the AndroidWorld apps on the emulator:
                  python run_eval.py --config configs/v2_index.json \
                      --tasks ContactsAddContact --runs 1 \
                      --perform_emulator_setup --out runs_setup
NEXT
