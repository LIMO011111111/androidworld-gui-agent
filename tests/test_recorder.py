"""Screen recorder control flow, against a stand-in adb executable."""

import os
import shutil
import stat
import subprocess
import textwrap

import pytest

from gui_agent import recorder as recorder_lib

pytestmark = pytest.mark.skipif(
    os.name == "nt" or not shutil.which("ffmpeg"), reason="needs a POSIX shell and ffmpeg"
)


@pytest.fixture()
def fake_adb(tmp_path):
  """A script that behaves like `adb` for screenrecord / pkill / pull / rm."""
  device = tmp_path / "device"
  device.mkdir()
  clip = tmp_path / "clip.mp4"
  subprocess.run(
      ["ffmpeg", "-loglevel", "error", "-f", "lavfi", "-i",
       "testsrc=duration=1:size=72x160:rate=10", "-pix_fmt", "yuv420p", str(clip)],
      check=True,
  )
  script = tmp_path / "adb"
  script.write_text(textwrap.dedent(f"""\
      #!/usr/bin/env bash
      # usage: adb -s SERIAL <command...>
      shift 2
      device="{device}"
      case "$1 $2" in
        "shell screenrecord")
          remote="${{!#}}"
          limit="${{CHUNK_LIMIT:-1000}}"
          for ((i = 0; i < limit * 10; i++)); do
            [ -e "$device/stop" ] && break
            sleep 0.1
          done
          cp "{clip}" "$device/$(basename "$remote")"
          ;;
        "shell pkill") touch "$device/stop" ;;
        "shell rm") rm -f "$device/$(basename "${{!#}}")" ;;
        "pull "*) cp "$device/$(basename "$2")" "$3" ;;
      esac
      """))
  script.chmod(script.stat().st_mode | stat.S_IEXEC)
  return script, device


def test_single_chunk_is_pulled_and_named_recording(fake_adb, tmp_path):
  adb, device = fake_adb
  out = tmp_path / "run" / "recording.mp4"
  rec = recorder_lib.ScreenRecorder(str(adb), "emulator-5554", out)
  rec.start()
  path = rec.stop()
  assert path == out and out.stat().st_size > 1024
  assert rec.error is None
  assert [p.name for p in device.iterdir()] == ["stop"]  # device cleaned up
  assert [p.name for p in out.parent.iterdir()] == ["recording.mp4"]


def test_long_run_is_recorded_in_chunks_and_joined(fake_adb, tmp_path, monkeypatch):
  adb, _ = fake_adb
  monkeypatch.setenv("CHUNK_LIMIT", "3")  # the stand-in stops each chunk after 3 s
  out = tmp_path / "run" / "recording.mp4"
  rec = recorder_lib.ScreenRecorder(str(adb), "emulator-5554", out)
  rec.start()
  import time
  time.sleep(4.0)  # long enough for a second chunk to begin
  path = rec.stop()
  assert path == out and rec.error is None
  probe = subprocess.run(
      ["ffprobe", "-v", "error", "-show_entries", "format=duration",
       "-of", "csv=p=0", str(out)], capture_output=True, text=True, check=True)
  assert float(probe.stdout.strip()) > 1.5  # two one-second clips joined
  assert [p.name for p in out.parent.iterdir()] == ["recording.mp4"]


def test_recorder_reports_failure_instead_of_raising(tmp_path):
  rec = recorder_lib.ScreenRecorder("/no/such/adb", "emulator-5554", tmp_path / "r.mp4")
  rec.start()
  assert rec.stop() is None
  assert rec.error


def test_recorder_retries_when_the_device_is_briefly_offline(fake_adb, tmp_path):
  adb, device = fake_adb
  # The first two screenrecord calls fail at once ("device offline").
  original = adb.read_text()
  adb.write_text(original.replace(
      '"shell screenrecord")',
      '"shell screenrecord")\n          n=$(cat "$HOME_COUNT" 2>/dev/null || echo 0); echo $((n+1)) > "$HOME_COUNT"\n'
      '          if [ "$n" -lt 2 ]; then echo "adb: device offline"; exit 1; fi',
  ).replace("#!/usr/bin/env bash", f"#!/usr/bin/env bash\nHOME_COUNT={tmp_path}/count"))
  out = tmp_path / "run" / "recording.mp4"
  rec = recorder_lib.ScreenRecorder(str(adb), "emulator-5554", out)
  rec.start()
  import time
  time.sleep(6.0)
  path = rec.stop()
  assert rec.error is None and path == out and out.exists()
