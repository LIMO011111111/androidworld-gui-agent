"""The run log: one row per run, in the format the lecture prescribes.

    task · run (x of 3) · model · observation · grounding · steps (budget) ·
    verifier PASS/FAIL · failure_class · recording · note

`log.csv` is the source of truth (it also keeps seed, timing and token counts
for the analysis). `log.md` is regenerated from it after every run and is the
table that goes on the slide.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

COLUMNS = [
    "timestamp", "agent", "task", "run", "model", "observation", "grounding",
    "steps", "budget", "verifier", "failure_class", "failure_reviewed",
    "recording", "note", "stop_reason", "state_score", "seed", "duration_s",
    "model_seconds", "model_calls", "prompt_tokens", "completion_tokens",
    "invalid_replies",
    "no_effect_actions", "blocked", "goal", "run_dir",
]


def read_rows(csv_path: str | Path) -> list[dict[str, str]]:
  path = Path(csv_path)
  if not path.exists():
    return []
  with open(path, "r", encoding="utf-8", newline="") as f:
    return list(csv.DictReader(f))


def append_row(csv_path: str | Path, row: dict[str, Any]) -> None:
  path = Path(csv_path)
  path.parent.mkdir(parents=True, exist_ok=True)
  is_new = not path.exists() or path.stat().st_size == 0
  with open(path, "a", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=COLUMNS, extrasaction="ignore")
    if is_new:
      writer.writeheader()
    writer.writerow({c: row.get(c, "") for c in COLUMNS})


def _cell(value: Any) -> str:
  text = "" if value is None else str(value)
  return text.replace("|", "\\|").replace("\n", " ").strip() or "—"


def write_markdown(csv_path: str | Path, md_path: str | Path) -> None:
  """Regenerates the slide-format table from the CSV."""
  rows = read_rows(csv_path)
  header = [
      "agent", "task", "run", "model", "observation", "grounding",
      "steps (budget)", "verifier", "failure_class", "recording", "note",
  ]
  lines = [
      "# Run log",
      "",
      "One row per run. `failure_class` is a suggestion until",
      "`failure_reviewed` is set to `yes` in log.csv after watching the recording.",
      "",
      "| " + " | ".join(header) + " |",
      "|" + "|".join(["---"] * len(header)) + "|",
  ]
  for r in rows:
    failure = r.get("failure_class", "")
    if failure and r.get("failure_reviewed", "").strip().lower() != "yes":
      failure += " (?)"
    lines.append(
        "| "
        + " | ".join(
            _cell(v)
            for v in [
                r.get("agent"), r.get("task"), r.get("run"), r.get("model"),
                r.get("observation"), r.get("grounding"),
                f'{r.get("steps")} ({r.get("budget")})', r.get("verifier"),
                failure, r.get("recording"), r.get("note"),
            ]
        )
        + " |"
    )
  Path(md_path).write_text("\n".join(lines) + "\n", encoding="utf-8")
