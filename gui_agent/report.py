"""Turns a run directory into a single HTML page for reviewing a trajectory.

One card per step: the screen the agent saw (tap point marked), what it
thought, what it did, what the harness decided and what happened. Open
`trajectory.html` next to the recording when classifying a failure.
"""

from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any

from gui_agent import trajectory as trajectory_lib

_CSS = """
:root { --bg:#f6f7f9; --card:#fff; --ink:#1c1f24; --muted:#5d6672; --line:#dfe3e8;
        --ok:#1a7f4b; --bad:#b3261e; --warn:#9a6700; --code:#f0f2f5; }
@media (prefers-color-scheme: dark) {
  :root { --bg:#14171b; --card:#1d2126; --ink:#e7eaee; --muted:#9aa4b0; --line:#2e343b;
          --ok:#5cc98d; --bad:#ff8a80; --warn:#e3b341; --code:#262b31; } }
* { box-sizing: border-box; }
body { margin:0; padding:24px 16px 64px; background:var(--bg); color:var(--ink);
       font:15px/1.5 system-ui,-apple-system,"Segoe UI",sans-serif; }
main { max-width:1000px; margin:0 auto; }
h1 { font-size:22px; margin:0 0 4px; }
.goal { color:var(--muted); margin:0 0 16px; }
.facts { display:flex; flex-wrap:wrap; gap:8px; margin:0 0 24px; padding:0; list-style:none; }
.facts li { background:var(--card); border:1px solid var(--line); border-radius:8px; padding:6px 10px; }
.facts b { font-weight:600; }
.pass { color:var(--ok); } .fail { color:var(--bad); } .warn { color:var(--warn); }
.step { display:grid; grid-template-columns:220px 1fr; gap:16px; background:var(--card);
        border:1px solid var(--line); border-radius:12px; padding:14px; margin:0 0 14px; }
.step img { width:100%; border-radius:8px; border:1px solid var(--line); display:block; }
.step h2 { font-size:16px; margin:0 0 6px; }
.thought { color:var(--muted); margin:0 0 8px; }
.row { margin:0 0 6px; overflow-wrap:anywhere; }
.label { color:var(--muted); font-size:12px; text-transform:uppercase; letter-spacing:.04em; }
code, pre { background:var(--code); border-radius:6px; font:13px/1.45 ui-monospace,Menlo,Consolas,monospace; }
code { padding:1px 5px; } pre { padding:10px; overflow:auto; max-height:320px; white-space:pre-wrap; }
details { margin-top:8px; } summary { cursor:pointer; color:var(--muted); }
@media (max-width:640px) { .step { grid-template-columns:1fr; } .step img { max-width:260px; } }
"""


def _esc(value: Any) -> str:
  return html.escape("" if value is None else str(value))


def _load(path: Path) -> dict[str, Any]:
  if not path.exists():
    return {}
  with open(path, "r", encoding="utf-8") as f:
    return json.load(f)


def _step_card(record: dict[str, Any]) -> str:
  resolved = record.get("resolved") or {}
  effect = record.get("effect") or {}
  model = record.get("model") or {}
  attempts = model.get("attempts") or []
  outcome = record.get("outcome", "")
  rows = []

  if record.get("thought"):
    rows.append(f'<p class="thought">“{_esc(record["thought"])}”</p>')
  if record.get("action"):
    rows.append(
        '<p class="row"><span class="label">Action</span><br>'
        f'<code>{_esc(json.dumps(record["action"], ensure_ascii=False))}</code></p>'
    )
  if resolved.get("target") or resolved.get("tap_xy"):
    target = resolved.get("target") or "no UI element at this point"
    rows.append(
        f'<p class="row"><span class="label">Grounding ({_esc(resolved.get("grounding"))})</span><br>'
        f'{_esc(target)} → tap at {_esc(resolved.get("tap_xy"))}</p>'
    )
  if record.get("guardrail"):
    g = record["guardrail"]
    rows.append(
        f'<p class="row fail"><span class="label">Guardrail: {_esc(g.get("rule"))}</span><br>'
        f'{_esc(g.get("message"))}</p>'
    )
  if record.get("done_check"):
    c = record["done_check"]
    verdict = "accepted" if c.get("achieved") else "rejected"
    css = "pass" if c.get("achieved") else "warn"
    rows.append(
        f'<p class="row {css}"><span class="label">Check before done: {verdict}</span><br>'
        f'{_esc(c.get("missing") or c.get("evidence") or c.get("error"))}</p>'
    )
  if effect:
    if effect.get("error"):
      text, css = f'action failed: {effect["error"]}', "fail"
    elif effect.get("screen_changed"):
      text, css = "screen changed", "pass"
      if effect.get("late_change"):
        text += " (only after an extra wait)"
    else:
      text, css = "screen did not change", "warn"
    rows.append(
        f'<p class="row {css}"><span class="label">Effect</span><br>{_esc(text)}'
        f' · now in <code>{_esc(effect.get("package_after"))}</code></p>'
    )
  if outcome == "invalid_reply":
    rows.append('<p class="row fail">No valid action after all retries.</p>')
  if record.get("notes"):
    rows.append(
        '<p class="row"><span class="label">Notes</span><br>'
        f'{_esc(" | ".join(record["notes"]))}</p>'
    )
  timing = ", ".join(
      f'{a.get("latency_s")}s / {a.get("prompt_tokens")}+{a.get("completion_tokens")} tok'
      for a in attempts
  )
  if timing:
    rows.append(
        f'<p class="row"><span class="label">Model ({len(attempts)} call(s))</span><br>{_esc(timing)}</p>'
    )

  prompt_text = "\n\n".join(
      f'[{m.get("role")}]\n{m.get("content")}' for m in record.get("prompt") or []
  )
  raw_text = "\n---\n".join(str(a.get("raw", "")) for a in attempts)
  details = (
      "<details><summary>Prompt and raw model output</summary>"
      f"<pre>{_esc(prompt_text)}</pre><pre>{_esc(raw_text)}</pre></details>"
  )
  image = ""
  if record.get("screenshot"):
    image = (
        f'<img src="{_esc(record["screenshot"])}" loading="lazy"'
        f' alt="Screen before step {_esc(record.get("step"))}">'
    )
  title = resolved.get("description") or outcome or "step"
  return (
      '<section class="step">'
      f"<div>{image}</div>"
      f'<div><h2>Step {_esc(record.get("step"))} of {_esc(record.get("budget"))}:'
      f" {_esc(title)}</h2>{''.join(rows)}{details}</div>"
      "</section>"
  )


def write_html(run_dir: str | Path) -> Path:
  """Writes `<run_dir>/trajectory.html` and returns its path."""
  run_dir = Path(run_dir)
  meta = _load(run_dir / "meta.json")
  result = _load(run_dir / "result.json")
  records = trajectory_lib.read_trajectory(run_dir)
  verdict = result.get("verifier", "?")
  css = "pass" if verdict == "PASS" else "fail"
  config = meta.get("config") or {}
  facts = [
      ("Verifier", f'<span class="{css}">{_esc(verdict)}</span>'),
      ("Agent", _esc(config.get("name"))),
      ("Model", _esc((meta.get("model") or {}).get("model"))),
      ("Observation", _esc(config.get("observation"))),
      ("Grounding", _esc(config.get("grounding"))),
      ("Steps", f'{_esc(result.get("steps"))} (budget {_esc(result.get("budget"))})'),
      ("Stop reason", _esc(result.get("stop_reason"))),
      ("Failure class", _esc(result.get("failure_class") or "—")),
      ("Seed", _esc(meta.get("seed"))),
  ]
  facts_html = "".join(f"<li><b>{k}:</b> {v}</li>" for k, v in facts)
  recording = ""
  if result.get("recording"):
    name = Path(str(result["recording"])).name
    recording = f'<p><a href="{_esc(name)}">Screen recording ({_esc(name)})</a></p>'
  evidence = ""
  if result.get("failure_evidence"):
    evidence = f'<p class="goal">Evidence: {_esc(result["failure_evidence"])}</p>'
  page = (
      "<!doctype html><html lang='en'><head><meta charset='utf-8'>"
      "<meta name='viewport' content='width=device-width, initial-scale=1'>"
      f"<title>{_esc(meta.get('task'))} run {_esc(meta.get('run'))}</title>"
      f"<style>{_CSS}</style></head><body><main>"
      f"<h1>{_esc(meta.get('task'))}, run {_esc(meta.get('run'))}</h1>"
      f"<p class='goal'>{_esc(meta.get('goal'))}</p>"
      f"<ul class='facts'>{facts_html}</ul>{evidence}{recording}"
      f"{''.join(_step_card(r) for r in records)}"
      "</main></body></html>"
  )
  out = run_dir / "trajectory.html"
  out.write_text(page, encoding="utf-8")
  return out
