"""Patches android_env's APK install for Windows. Safe to run again.

android_env writes the APK to a NamedTemporaryFile and calls `adb install`
while the file is still open. On Windows an open temporary file cannot be
opened by another process, so adb fails with "failed to open ...apk: No such
file or directory". The patch closes the file first and deletes it afterwards.

  .venv\\Scripts\\python scripts\\patch_android_env_windows.py
"""

import pathlib
import sys

from android_env.components import adb_call_parser

OLD = """        with tempfile.NamedTemporaryFile(**kwargs) as f:
          fpath = f.name
          f.write(install_apk.blob.contents)

          response, _ = self._execute_command(
              ['install', '-r', '-t', '-g', fpath], timeout=timeout
          )
"""
NEW = """        # Patched for Windows (scripts/patch_android_env_windows.py).
        with tempfile.NamedTemporaryFile(suffix='.apk', delete=False) as f:
          fpath = f.name
          f.write(install_apk.blob.contents)
        try:
          response, _ = self._execute_command(
              ['install', '-r', '-t', '-g', fpath], timeout=timeout
          )
        finally:
          os.remove(fpath)
"""

path = pathlib.Path(adb_call_parser.__file__)
source = path.read_text(encoding="utf-8")
if NEW in source:
  print(f"already patched: {path}")
elif OLD in source:
  path.write_text(source.replace(OLD, NEW), encoding="utf-8")
  print(f"patched: {path}")
else:
  print(f"code not found, android_env version changed? {path}", file=sys.stderr)
  sys.exit(1)
