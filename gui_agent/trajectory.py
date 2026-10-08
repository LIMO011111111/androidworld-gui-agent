"""Trajectory logging: what the agent saw and did, step by step.

Written while the run is happening, one JSON line per step, flushed
immediately. If a run crashes at step 9, steps 1-8 are already on disk.

Layout of one run directory:
    meta.json          task, goal, seed, full agent config, model identity
    trajectory.jsonl   one record per step (observation, prompt, raw model
                       output, parsed action, grounding, guardrail verdict,
                       effect on the screen, latency, tokens)
    screens/step_NN.jpg  the screen BEFORE the action, tap point marked
    result.json        verifier outcome and episode statistics
    recording.mp4      screen recording (written by recorder.py)
"""

from __future__ import annotations

import datetime
import json
from pathlib import Path
from typing import Any, Optional

import numpy as np

from gui_agent import observation


def _json_default(value: Any) -> Any:
  if isinstance(value, (np.integer,)):
    return int(value)
  if isinstance(value, (np.floating,)):
    return float(value)
  if isinstance(value, np.ndarray):
    return f"<array {value.shape}>"
  if isinstance(value, (datetime.datetime, datetime.date)):
    return value.isoformat()
  if isinstance(value, Path):
    return str(value)
  return repr(value)


def now_iso() -> str:
  return datetime.datetime.now().astimezone().isoformat(timespec="seconds")


class TrajectoryLogger:
  """Writes the trajectory of one episode to a run directory."""

  def __init__(self, run_dir: str | Path, image_max_side: int = 1024):
    self.run_dir = Path(run_dir)
    self.screens_dir = self.run_dir / "screens"
    self.screens_dir.mkdir(parents=True, exist_ok=True)
    self._image_max_side = image_max_side
    self._jsonl = self.run_dir / "trajectory.jsonl"

  def write_meta(self, meta: dict[str, Any]) -> None:
    self._write_json("meta.json", meta)

  def write_result(self, result: dict[str, Any]) -> None:
    self._write_json("result.json", result)

  def log_step(
      self,
      record: dict[str, Any],
      pixels: Optional[np.ndarray] = None,
      logical_size: Optional[tuple[int, int]] = None,
      tap_xy: Optional[tuple[int, int]] = None,
      box: Optional[tuple[int, int, int, int]] = None,
  ) -> None:
    """Appends one step. Never raises: logging must not break a run."""
    try:
      if pixels is not None and logical_size is not None:
        name = f"step_{int(record.get('step', 0)):02d}.jpg"
        image = observation.annotated_screenshot(
            pixels, logical_size, tap_xy, box, self._image_max_side
        )
        image.save(self.screens_dir / name, format="JPEG", quality=80)
        record["screenshot"] = f"screens/{name}"
      with open(self._jsonl, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False, default=_json_default))
        f.write("\n")
        f.flush()
    except Exception as error:  # pylint: disable=broad-exception-caught
      print(f"[trajectory] could not log step: {error}")

  def _write_json(self, name: str, data: dict[str, Any]) -> None:
    with open(self.run_dir / name, "w", encoding="utf-8") as f:
      json.dump(data, f, ensure_ascii=False, indent=2, default=_json_default)


def read_trajectory(run_dir: str | Path) -> list[dict[str, Any]]:
  path = Path(run_dir) / "trajectory.jsonl"
  if not path.exists():
    return []
  records = []
  with open(path, "r", encoding="utf-8") as f:
    for line in f:
      line = line.strip()
      if line:
        records.append(json.loads(line))
  return records
