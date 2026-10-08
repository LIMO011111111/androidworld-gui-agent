"""Screen recording of an evaluation run.

Uses `adb shell screenrecord`, which runs on the device itself and therefore
records exactly what the emulator shows, with or without a visible window.

Android 13 caps one recording at 180 seconds. A run with a local model can
take longer, so we record back-to-back chunks and join them with ffmpeg at the
end (there is a gap of about a second between chunks).

The recorder is deliberately fail-safe: if recording does not work on a
machine, the run continues and the log row says so. In that case record the
emulator window with the OS screen recorder instead.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import threading
import time
from pathlib import Path
from typing import Optional

_REMOTE_DIR = "/sdcard"
_CHUNK_SECONDS = 170  # below the 180 s cap of Android 13
_MAX_QUICK_FAILURES = 5  # retries when screenrecord exits right away


def find_adb(explicit: Optional[str] = None) -> Optional[str]:
  """Locates adb: explicit path, ANDROID_HOME, the usual SDK folders, PATH."""
  candidates = []
  if explicit:
    candidates.append(os.path.expanduser(explicit))
  for var in ("ANDROID_HOME", "ANDROID_SDK_ROOT"):
    if os.environ.get(var):
      candidates.append(os.path.join(os.environ[var], "platform-tools", "adb"))
  candidates += [
      os.path.expanduser("~/Library/Android/sdk/platform-tools/adb"),  # macOS
      os.path.expanduser("~/Android/Sdk/platform-tools/adb"),  # Linux
      os.path.expanduser("~/AppData/Local/Android/Sdk/platform-tools/adb.exe"),
  ]
  for path in candidates:
    if os.path.isfile(path):
      return path
  return shutil.which("adb")


class ScreenRecorder:
  """Records the device screen to an mp4 file while an episode runs."""

  def __init__(
      self,
      adb_path: str,
      serial: str,
      out_path: str | Path,
      size: str = "720x1600",
      bit_rate: int = 4_000_000,
  ):
    self._adb = [adb_path, "-s", serial]
    self._out = Path(out_path)
    self._size = size
    self._bit_rate = bit_rate
    self._tag = f"awrec_{os.getpid()}_{int(time.time())}"
    self._stop = threading.Event()
    self._thread: Optional[threading.Thread] = None
    self._process: Optional[subprocess.Popen] = None
    self._chunks: list[str] = []
    self.error: Optional[str] = None

  def start(self) -> None:
    self._out.parent.mkdir(parents=True, exist_ok=True)
    self._thread = threading.Thread(target=self._loop, daemon=True)
    self._thread.start()
    time.sleep(1.0)  # give screenrecord a moment before the first action

  def _loop(self) -> None:
    index = 0
    quick_failures = 0
    while not self._stop.is_set():
      remote = f"{_REMOTE_DIR}/{self._tag}_{index:02d}.mp4"
      command = self._adb + [
          "shell", "screenrecord",
          "--time-limit", str(_CHUNK_SECONDS),
          "--bit-rate", str(self._bit_rate),
      ]
      if self._size:
        command += ["--size", self._size]
      command.append(remote)
      started = time.time()
      try:
        self._process = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
        )
        self._chunks.append(remote)
        output, _ = self._process.communicate()
      except OSError as error:
        self.error = f"could not start screenrecord: {error}"
        return
      if time.time() - started < 2.0 and not self._stop.is_set():
        # screenrecord exited immediately. Usually adb or the device was
        # briefly unavailable (adb server restart, device offline right after
        # a task reset), so try again a few times before giving up.
        quick_failures += 1
        text = (output or b"").decode("utf-8", "replace").strip()
        if quick_failures >= _MAX_QUICK_FAILURES:
          self.error = f"screenrecord exited at once: {text[:200]}"
          return
        self._adb_quiet(["wait-for-device"])
        time.sleep(2.0)
        continue
      quick_failures = 0
      index += 1

  def stop(self) -> Optional[Path]:
    """Stops recording and returns the local video path (None on failure)."""
    if self._thread is None:
      return None
    self._stop.set()
    # SIGINT on the device makes screenrecord finalise the mp4 properly.
    # Killing the local adb process instead can leave a broken file.
    if not self._adb_quiet(["shell", "pkill", "-2", "screenrecord"]):
      self._adb_quiet(["shell", "killall", "-2", "screenrecord"])
    self._thread.join(timeout=15)
    if self._thread.is_alive() and self._process is not None:
      self._adb_quiet(["shell", "pkill", "-9", "screenrecord"])
      self._process.kill()
      self._thread.join(timeout=5)
    time.sleep(1.0)  # let the device flush the file

    local_parts = []
    for i, remote in enumerate(self._chunks):
      local = self._out.with_name(f"{self._out.stem}.part{i:02d}.mp4")
      pulled = self._adb_quiet(["pull", remote, str(local)])
      self._adb_quiet(["shell", "rm", "-f", remote])
      if pulled and local.exists() and local.stat().st_size > 1024:
        local_parts.append(local)
      elif local.exists():
        local.unlink()
    if not local_parts:
      self.error = self.error or "no recording could be pulled from the device"
      return None
    if len(local_parts) == 1:
      local_parts[0].replace(self._out)
      return self._out
    return self._concat(local_parts)

  def _concat(self, parts: list[Path]) -> Path:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
      self.error = "ffmpeg not found: recording left as separate part files"
      return parts[0]
    listing = self._out.with_suffix(".parts.txt")
    listing.write_text(
        "".join(f"file '{p.resolve().as_posix()}'\n" for p in parts),
        encoding="utf-8",
    )
    done = subprocess.run(
        [ffmpeg, "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
         "-i", str(listing), "-c", "copy", str(self._out)],
        capture_output=True, check=False,
    )
    listing.unlink(missing_ok=True)
    if done.returncode != 0 or not self._out.exists():
      self.error = "ffmpeg could not join the parts: " + done.stderr.decode(
          "utf-8", "replace")[:200]
      return parts[0]
    for part in parts:
      part.unlink(missing_ok=True)
    return self._out

  def _adb_quiet(self, args: list[str]) -> bool:
    try:
      done = subprocess.run(
          self._adb + args, capture_output=True, timeout=60, check=False
      )
      return done.returncode == 0
    except (OSError, subprocess.SubprocessError):
      return False
