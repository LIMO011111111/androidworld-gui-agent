"""Episode memory: history lines, scratch notes and the status bar.

The model is stateless; whatever it should know about earlier steps has to be
put back into the window by us (Day 1). We do NOT resend old screenshots or
old tree dumps. Each finished step is replaced by one line written by code:

    3. click [5] Button "Save" -> screen changed

and the hidden state of a long trajectory (step count, last effect, warnings,
values to carry between apps) is made explicit in a status bar that is
maintained by code and appended at the END of the prompt (Day 2).
"""

from __future__ import annotations

from typing import Optional

_MAX_NOTES = 6
_MAX_NOTE_CHARS = 200


class EpisodeMemory:
  """Everything the agent remembers within one episode."""

  def __init__(self) -> None:
    self.history: list[str] = []
    self.notes: list[str] = []
    self.warnings: list[str] = []

  def reset(self) -> None:
    self.history.clear()
    self.notes.clear()
    self.warnings.clear()

  # -- history ---------------------------------------------------------------
  def add_step(self, description: str, outcome: str) -> None:
    """Records one finished step as a single code-written line."""
    self.history.append(f"{description} -> {outcome}")

  def render_history(self, max_lines: int) -> str:
    if not self.history:
      return "No actions yet."
    first = max(0, len(self.history) - max_lines)
    lines = []
    if first > 0:
      lines.append(f"(steps 1-{first} omitted)")
    for number, line in enumerate(self.history[first:], start=first + 1):
      lines.append(f"{number}. {line}")
    return "\n".join(lines)

  # -- scratch notes (fix for `lost_value`) ---------------------------------
  def add_note(self, note: str) -> None:
    """Stores a value the model wants to carry forward, e.g. into another app.

    The model decides WHAT is worth noting; keeping it and putting it back in
    front of the model every step is done by code, so it cannot be forgotten.
    """
    note = " ".join((note or "").split())[:_MAX_NOTE_CHARS]
    if not note or note in self.notes:
      return
    self.notes.append(note)
    del self.notes[:-_MAX_NOTES]

  # -- status bar ------------------------------------------------------------
  def render_status(
      self,
      step: int,
      budget: int,
      package: str,
      last_effect: Optional[str],
  ) -> str:
    lines = [f"step: {step} of {budget}"]
    if package:
      lines.append(f"app in foreground: {package}")
    if last_effect:
      lines.append(f"last action: {last_effect}")
    if budget - step <= 2:
      lines.append("warning: almost out of steps, finish now")
    for warning in self.warnings:
      lines.append(f"warning: {warning}")
    if self.notes:
      lines.append("notes: " + " | ".join(self.notes))
    return "\n".join(lines)
