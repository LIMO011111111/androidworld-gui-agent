# One-time setup on Windows. Safe to run again: every step checks first.
# Windows counterpart of scripts/setup_mac.sh.
#
#   pwsh -ExecutionPolicy Bypass -File scripts\setup_windows.ps1
#
# What it does:
#   1. Python 3.11 environment in .venv (via uv)
#   2. AndroidWorld, pinned to the commit this agent was tested against
#   3. Android emulator image + the AVD "AndroidWorldAvd" (Pixel 6, API 33)
#   4. The local model in Ollama
#   5. The unit tests of this repo
$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

$AndroidWorldCommit = if ($env:ANDROID_WORLD_COMMIT) { $env:ANDROID_WORLD_COMMIT } else { "2dfc5ca3dc590efe9c72ce768f2b04182f2f75c7" }
$Model = if ($env:MODEL) { $env:MODEL } else { "qwen3-vl:4b-instruct" }
$AvdName = if ($env:AVD_NAME) { $env:AVD_NAME } else { "AndroidWorldAvd" }
$Sdk = if ($env:ANDROID_HOME) { $env:ANDROID_HOME } else { Join-Path $env:LOCALAPPDATA "Android\Sdk" }

function Say($msg)  { Write-Host "`n==> $msg" -ForegroundColor Cyan }
function Warn($msg) { Write-Host "    ! $msg" -ForegroundColor Yellow }
function Have($cmd) { [bool](Get-Command $cmd -ErrorAction SilentlyContinue) }
function Run {
  # Runs a native command and stops the script if it fails.
  $Exe, $Rest = $args
  & $Exe @Rest
  if ($LASTEXITCODE -ne 0) { throw "Command failed ($LASTEXITCODE): $Exe $Rest" }
}
$todo = New-Object System.Collections.Generic.List[string]

# --- 0. Disk space -----------------------------------------------------------
$freeGb = [int]((Get-PSDrive ($RepoRoot.Substring(0, 1))).Free / 1GB)
Say "Free disk space: $freeGb GB"
if ($freeGb -lt 20) {
  Warn "Emulator image, AVD data, AndroidWorld apps and the model need about 15-20 GB."
}

# --- 1. Tools ----------------------------------------------------------------
Say "Command-line tools"
foreach ($tool in @(
    @{ cmd = "git";    id = "Git.Git" },
    @{ cmd = "uv";     id = "astral-sh.uv" },
    @{ cmd = "ffmpeg"; id = "Gyan.FFmpeg" })) {
  if (Have $tool.cmd) {
    Write-Host "    $($tool.cmd): ok"
  } elseif (Have "winget") {
    winget install --id $tool.id -e --accept-source-agreements --accept-package-agreements
    $todo.Add("$($tool.cmd) was just installed: open a new terminal and run this script again.")
  } else {
    throw "$($tool.cmd) is missing and winget is not available. Install it by hand."
  }
}
if ($todo.Count -gt 0) { $todo | ForEach-Object { Write-Host "  - $_" }; exit 1 }

# --- 2. Python environment + AndroidWorld -----------------------------------
Say "Python 3.11 environment (.venv)"
$Py = Join-Path $RepoRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $Py)) {
  Run uv venv --seed --python 3.11 .venv
}

Say "AndroidWorld at commit $($AndroidWorldCommit.Substring(0, 7))"
$Aw = Join-Path $RepoRoot "third_party\android_world"
if (-not (Test-Path (Join-Path $Aw ".git"))) {
  New-Item -ItemType Directory -Force (Join-Path $RepoRoot "third_party") | Out-Null
  # AndroidWorld has paths longer than Windows' default limit of 260 characters.
  Run git -c core.longpaths=true clone https://github.com/google-research/android_world.git $Aw
}
Run git -C $Aw config core.longpaths true
git -C $Aw fetch --quiet origin
Run git -C $Aw checkout --quiet $AndroidWorldCommit
Run $Py -m pip install --quiet -r (Join-Path $Aw "requirements.txt")
Run $Py -m pip install --quiet setuptools
Push-Location $Aw
try { Run $Py setup.py install *> $null } finally { Pop-Location }
Run $Py -m pip install --quiet -r requirements.txt
Run $Py scripts\patch_android_env_windows.py

# --- 3. Android SDK, emulator, AVD ------------------------------------------
Say "Android SDK at $Sdk"
$Image = "system-images;android-33;google_apis;x86_64"
$SdkManager = Join-Path $Sdk "cmdline-tools\latest\bin\sdkmanager.bat"
$AvdManager = Join-Path $Sdk "cmdline-tools\latest\bin\avdmanager.bat"
$Emulator = Join-Path $Sdk "emulator\emulator.exe"
# Prefer Android Studio's own JDK; sdkmanager needs Java.
$StudioJava = "C:\Program Files\Android\Android Studio\jbr"
if (Test-Path (Join-Path $StudioJava "bin\java.exe")) {
  $env:JAVA_HOME = $StudioJava
  $env:Path = "$StudioJava\bin;$env:Path"
}

function AvdExists {
  if (-not (Test-Path $Emulator)) { return $false }
  return [bool]((& $Emulator -list-avds 2>$null) -contains $AvdName)
}

if (AvdExists) {
  Write-Host "    AVD $AvdName already exists."
} elseif ((Test-Path $SdkManager) -and (Have "java")) {
  Write-Host "    Accepting the Android SDK licences and installing the API 33 image."
  ("y`n" * 30) | & $SdkManager --licenses *> $null
  # sdkmanager/avdmanager are .bat files: cmd.exe splits unquoted arguments at
  # ";", so the package names have to reach cmd.exe inside quotes.
  cmd /c "`"$SdkManager`" platform-tools emulator `"platforms;android-33`" `"$Image`""
  $ok = $LASTEXITCODE -eq 0
  if ($ok) {
    "no" | cmd /c "`"$AvdManager`" create avd -n $AvdName -k `"$Image`" -d pixel_6"
    $ok = $LASTEXITCODE -eq 0
  }
  if ($ok) {
    Write-Host "    Created AVD $AvdName."
  } else {
    Warn "sdkmanager / avdmanager failed."
    $todo.Add("Create the AVD by hand in Android Studio: Device Manager > Create Device > Pixel 6 > Tiramisu (API 33, x86_64, target 'Google APIs', not 'Google Play') > name it $AvdName.")
  }
} else {
  Warn "Could not create the AVD automatically (no SDK command-line tools or no working Java)."
  if (-not (Test-Path "C:\Program Files\Android\Android Studio")) {
    $todo.Add("Install Android Studio (winget install Google.AndroidStudio), open it once and finish the setup wizard so it installs the SDK.")
  }
  $todo.Add("Then either install 'Android SDK Command-line Tools (latest)' in Android Studio (Settings > Languages & Frameworks > Android SDK > SDK Tools) and run this script again, or create the AVD by hand: Device Manager > Create Device > Pixel 6 > Tiramisu (API 33, x86_64, target 'Google APIs', not 'Google Play') > name it $AvdName.")
}
if (-not (Test-Path (Join-Path $Sdk "platform-tools\adb.exe"))) {
  $todo.Add("adb is missing at $Sdk\platform-tools\adb.exe (it comes with the Android SDK).")
}

# --- 4. Model ----------------------------------------------------------------
Say "Model $Model"
if (Have "ollama") {
  ollama pull $Model
  if ($LASTEXITCODE -ne 0) {
    Warn "ollama pull failed. Open the Ollama app, and update it if it is older than 0.12.7."
    $todo.Add("ollama pull $Model")
  }
} else {
  $todo.Add("Install Ollama (https://ollama.com/download), open it once, then: ollama pull $Model")
}

# --- 5. Tests ----------------------------------------------------------------
Say "Unit tests"
& $Py -m pytest -q tests
if ($LASTEXITCODE -ne 0) { Warn "Some unit tests failed (see above)." }

Say "Setup finished"
if ($todo.Count -gt 0) {
  Write-Host "Still to do by hand:"
  $todo | ForEach-Object { Write-Host "  - $_" }
}
Write-Host @"

Next steps:
  1. Terminal A:  pwsh -File scripts\start_emulator.ps1          (leave it running)
  2. Terminal B:  .venv\Scripts\Activate.ps1
                  python scripts\doctor.py
  3. First run only, installs the AndroidWorld apps on the emulator:
                  python run_eval.py --config configs\v2_index.json ``
                      --tasks ContactsAddContact --runs 1 ``
                      --perform_emulator_setup --out runs_setup
"@
