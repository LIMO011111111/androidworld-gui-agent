# Starts the emulator the way AndroidWorld needs it: from the command line,
# without a snapshot, with the gRPC port for the accessibility forwarder.
# Windows counterpart of scripts/start_emulator.sh.
#
#   pwsh -File scripts\start_emulator.ps1             # with a window
#   $env:HEADLESS = "1"; pwsh -File scripts\start_emulator.ps1   # no window
$ErrorActionPreference = "Stop"

$AvdName = if ($env:AVD_NAME) { $env:AVD_NAME } else { "AndroidWorldAvd" }
$Sdk = if ($env:ANDROID_HOME) { $env:ANDROID_HOME } else { Join-Path $env:LOCALAPPDATA "Android\Sdk" }
$Emulator = Join-Path $Sdk "emulator\emulator.exe"
if (-not (Test-Path $Emulator)) {
  Write-Error "Emulator not found at $Emulator. Set ANDROID_HOME or install the Android SDK."
  exit 1
}

$emuArgs = @("-avd", $AvdName, "-no-snapshot", "-grpc", "8554")
if ($env:HEADLESS -eq "1") { $emuArgs += "-no-window" }
Write-Host "Starting: $Emulator $($emuArgs -join ' ')"
& $Emulator @emuArgs
