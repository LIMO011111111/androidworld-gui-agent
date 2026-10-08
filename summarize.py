"""Builds the before-after summary from runs/log.csv.

    python summarize.py            # reads runs/log.csv, writes runs/summary.md

Counting rules (so the numbers cannot be dressed up):
  * every PASS and FAIL row counts, including repeated runs of the same task
    and run number;
  * ERROR rows (emulator or model server broke, the agent was not at fault)
    are listed separately and are not part of any rate.
"""

from __future__ import annotations

import argparse
import collections
import sys
from pathlib import Path
from typing import Optional

from gui_agent import evallog
from gui_agent import failure


def _num(value: str) -> float:
  try:
    return float(value)
  except (TypeError, ValueError):
    return 0.0


def _rate(passed: int, total: int) -> str:
  if total == 0:
    return "—"
  return f"{passed}/{total} ({100.0 * passed / total:.0f} %)"


def _mean(values: list[float]) -> str:
  return f"{sum(values) / len(values):.1f}" if values else "—"


def _table(header: list[str], rows: list[list[str]]) -> list[str]:
  lines = ["| " + " | ".join(header) + " |", "|" + "|".join(["---"] * len(header)) + "|"]
  lines += ["| " + " | ".join(str(c) for c in row) + " |" for row in rows]
  return lines + [""]


def build_summary(rows: list[dict[str, str]]) -> str:
  """Returns the summary as Markdown."""
  scored = [r for r in rows if r.get("verifier") in ("PASS", "FAIL")]
  errors = [r for r in rows if r.get("verifier") == "ERROR"]
  for r in rows:  # tolerate hand-edited logs with missing cells
    for key in ("agent", "task", "run", "steps", "verifier"):
      r[key] = r.get(key) or ""
  agents = list(dict.fromkeys(r["agent"] for r in rows))
  tasks = list(dict.fromkeys(r["task"] for r in rows))
  out = ["# Evaluation summary", ""]
  error_section = []
  if errors:
    error_section = ["## Runs excluded as ERROR", ""] + _table(
        ["agent", "task", "run", "note"],
        [[r["agent"], r["task"], r["run"], (r.get("note") or "").replace("|", "/")]
         for r in errors],
    )
  if not scored:
    return "\n".join(out + ["No scored runs in the log yet.", ""] + error_section)

  def select(agent: str, task: Optional[str] = None) -> list[dict[str, str]]:
    return [
        r for r in scored
        if r["agent"] == agent and (task is None or r["task"] == task)
    ]

  out += ["## Success rate (PASS / runs)", ""]
  body = []
  for task in tasks:
    body.append([task] + [
        _rate(sum(r["verifier"] == "PASS" for r in select(a, task)), len(select(a, task)))
        for a in agents
    ])
  body.append(["**all tasks**"] + [
      "**" + _rate(sum(r["verifier"] == "PASS" for r in select(a)), len(select(a))) + "**"
      for a in agents
  ])
  out += _table(["task"] + agents, body)

  out += ["## Same task instance, side by side", "",
          "Runs with the same seed have identical task parameters.", ""]
  by_instance: dict[tuple[str, str], dict[str, list[str]]] = collections.OrderedDict()
  for r in scored:
    key = (r["task"], r.get("seed", ""))
    by_instance.setdefault(key, collections.defaultdict(list))[r["agent"]].append(
        f'{r["verifier"]} in {r["steps"]} steps'
        + (f' [{r["failure_class"]}]' if r.get("failure_class") else "")
    )
  body = [
      [task, seed] + ["; ".join(cells.get(a, [])) or "—" for a in agents]
      for (task, seed), cells in by_instance.items()
  ]
  out += _table(["task", "seed"] + agents, body)

  out += ["## Cost", ""]
  body = []
  for a in agents:
    mine = select(a)
    calls = sum(_num(r.get("model_calls", "")) for r in mine)
    steps = sum(_num(r["steps"]) for r in mine)
    body.append([
        a,
        len(mine),
        _mean([_num(r["steps"]) for r in mine]),
        _mean([_num(r["steps"]) for r in mine if r["verifier"] == "PASS"]),
        _mean([_num(r.get("duration_s", "")) for r in mine]),
        f'{sum(_num(r.get("model_seconds", "")) for r in mine) / steps:.1f}' if steps else "—",
        f'{sum(_num(r.get("prompt_tokens", "")) for r in mine) / calls:.0f}' if calls else "—",
        f'{sum(_num(r.get("invalid_replies", "")) for r in mine):.0f}',
    ])
  out += _table(
      ["agent", "runs", "avg steps", "avg steps (PASS only)", "avg run time (s)",
       "model time per step (s)", "prompt tokens per model call", "invalid replies"],
      body,
  )

  out += ["## Failure classes (FAIL runs)", "",
          "A class followed by (?) in log.md is still an unreviewed suggestion.", ""]
  body = []
  for a in agents:
    fails = [r for r in select(a) if r["verifier"] == "FAIL"]
    counts = collections.Counter(r.get("failure_class", "") for r in fails)
    reviewed = sum(r.get("failure_reviewed", "").strip().lower() == "yes" for r in fails)
    body.append([a, len(fails)] + [counts.get(c, 0) for c in failure.FAILURE_CLASSES]
                + [f"{reviewed}/{len(fails)}"])
  out += _table(["agent", "FAIL runs"] + list(failure.FAILURE_CLASSES) + ["reviewed"], body)

  return "\n".join(out + error_section)


def main(argv: Optional[list[str]] = None) -> int:
  parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
  parser.add_argument("--log", default="runs/log.csv")
  parser.add_argument("--out", default="", help="default: summary.md next to the log")
  args = parser.parse_args(argv)
  rows = evallog.read_rows(args.log)
  if not rows:
    print(f"No rows found in {args.log}", file=sys.stderr)
    return 1
  text = build_summary(rows)
  out = Path(args.out) if args.out else Path(args.log).with_name("summary.md")
  out.write_text(text, encoding="utf-8")
  evallog.write_markdown(args.log, Path(args.log).with_name("log.md"))
  print(text)
  print(f"Written to {out}")
  return 0


if __name__ == "__main__":
  sys.exit(main())
