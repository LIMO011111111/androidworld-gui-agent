"""Goal-value tracker (V4): which values from the goal have been typed yet.

The most frequent failure of V2 and V3 was `lost_value`: the agent typed the
first name and saved, the surname never reached the device ("Isla" instead of
"Isla Martin"). V3's check step could not catch it because it is the same
small model looking at the screen.

This module is the code-side answer. It pulls the literal values out of the
goal text with plain rules (no model call), compares them with what the agent
has actually typed, and

* shows the result every step ("NOT typed yet: Martin"), and
* lets the agent veto a "complete" while a value was never typed.

The rules are generic, not tied to one app:

* quoted strings ("..." or '...');
* the free text after "with the following text:" / "with the text:";
* phone numbers (a "+" or 7+ digits);
* file names with an extension: only the name part must be typed (apps
  often preset the extension in a separate field); the status line shows
  name and extension separately as a hint;
* runs of two or more capitalised words (names like "Isla Martin"), each word
  tracked on its own, minus app names and words that start the goal.

A value counts as typed when it appears inside any typed text, compared
case-insensitively and ignoring spaces, dashes and a trailing full stop.
"""

from __future__ import annotations

import dataclasses
import re
from typing import Iterable, Sequence

from gui_agent import config as config_lib

_QUOTED = re.compile(r"\"([^\"]{2,})\"|'([^']{2,})'")
_FREE_TEXT = re.compile(r"with (?:the )?(?:following )?text:\s*(.+)", re.IGNORECASE)
_PHONE = re.compile(r"(?<![\w.])\+?\d[\d \-]{5,}\d(?![\w])")
_FILENAME = re.compile(r"\b([\w-]+)(\.[A-Za-z0-9]{1,5})\b")
_NAME_RUN = re.compile(r"\b([A-Z][a-z]+(?:[ -][A-Z][a-z]+)+)\b")
_FILE_EXTENSIONS = {".md", ".txt", ".csv", ".json", ".pdf", ".jpg", ".png", ".mp3", ".mp4"}

# Words that are capitalised for grammar, not because they are a value.
_STOP_WORDS = {
    "create", "add", "share", "send", "open", "delete", "edit", "make", "set",
    "their", "the", "a", "an", "in", "with", "using", "via", "and", "then",
    "new", "note", "contact", "message", "sms", "save", "call", "find",
    "update", "remove", "write", "enter", "type", "please", "text", "name",
    "rename",
}


def _norm(text: str) -> str:
  text = text.lower().strip()
  text = re.sub(r"[\s\-]+", "", text)
  return text.rstrip(".")


def _digits(text: str) -> str:
  return re.sub(r"\D", "", text)


@dataclasses.dataclass
class GoalValue:
  """One value the goal asks for, split into the parts that must be typed."""

  label: str  # how it is shown to the model
  parts: tuple[str, ...]  # each part must appear in some typed text
  kind: str  # "quoted" | "text" | "phone" | "file" | "name"

  def missing(self, typed: Sequence[str]) -> list[str]:
    typed = [t for t in typed if t]
    # Also accept a value typed in several chunks (all typing joined up).
    haystacks = [_norm(t) for t in typed] + [_norm("".join(typed))]
    if self.kind == "phone":
      digits = [_digits(t) for t in typed] + [_digits("".join(typed))]
      return [
          p for p in self.parts
          if not any(_digits(p)[-7:] in d for d in digits if d)
      ]
    return [p for p in self.parts if not any(_norm(p) in h for h in haystacks)]


def _app_words() -> set[str]:
  words = set()
  for name in config_lib.APP_PACKAGES:
    words.update(name.lower().split())
  return words


def extract(goal: str) -> list[GoalValue]:
  """Literal values in the goal text, in order of appearance, no duplicates."""
  values: list[GoalValue] = []
  covered: list[str] = []  # normalised strings already tracked

  def add(label: str, parts: Iterable[str], kind: str) -> None:
    parts = tuple(p.strip() for p in parts if p and p.strip())
    if not parts:
      return
    key = _norm(label)
    if not key or any(key in c or c in key for c in covered):
      return
    covered.append(key)
    values.append(GoalValue(label=label.strip(), parts=parts, kind=kind))

  remaining = goal

  # 1. Free text after "with the following text:". It ends where the next
  #    instruction starts ("... words.. Share the ...") or at the end.
  match = _FREE_TEXT.search(remaining)
  if match:
    body = match.group(1)
    split = re.split(
        r"(?<=\.)\.\s+|\.\s+(?=(?:Share|Send|Then|Open|Copy|Forward|Text|Save)\b)",
        body, maxsplit=1,
    )
    text = split[0].strip()
    if text:
      add(text, [text], "text")
      remaining = remaining.replace(text, " ")

  # 2. Quoted strings.
  for m in _QUOTED.finditer(remaining):
    quoted = m.group(1) or m.group(2)
    add(quoted, [quoted], "quoted")

  # 3. File names: name and extension are separate parts.
  for m in _FILENAME.finditer(remaining):
    stem, ext = m.group(1), m.group(2)
    if ext.lower() in _FILE_EXTENSIONS:
      add(stem + ext, [stem], "file")

  # 4. Phone numbers.
  for m in _PHONE.finditer(remaining):
    add(m.group(0), [m.group(0)], "phone")

  # 5. Names: runs of capitalised words, each word its own part.
  app_words = _app_words()
  for m in _NAME_RUN.finditer(remaining):
    words = [
        w for w in re.split(r"[ -]", m.group(1))
        if w.lower() not in _STOP_WORDS and w.lower() not in app_words
    ]
    if len(words) >= 2:
      add(" ".join(words), words, "name")

  # Show them in the order the goal mentions them.
  values.sort(key=lambda v: goal.find(v.parts[0]) if v.parts[0] in goal else len(goal))
  return values


class GoalTracker:
  """Holds the goal's values for one episode and reports what is missing."""

  def __init__(self, goal: str):
    self.goal = goal
    self.values = extract(goal)

  def missing(self, typed: Sequence[str]) -> list[tuple[GoalValue, list[str]]]:
    out = []
    for value in self.values:
      gap = value.missing(typed)
      if gap:
        out.append((value, gap))
    return out

  def missing_parts(self, typed: Sequence[str]) -> list[str]:
    return [p for _, gap in self.missing(typed) for p in gap]

  def render(self, typed: Sequence[str]) -> str:
    """The STATUS block shown to the model every step."""
    if not self.values:
      return ""
    lines = ["VALUES FROM THE GOAL (tracked by code from what you typed):"]
    for value in self.values:
      gap = value.missing(typed)
      if value.kind == "file":
        stem = value.parts[0]
        ext = value.label[len(stem):]
        shape = (
            f'file "{value.label}" = name "{stem}" + extension "{ext}"'
            " (if there is a separate extension field, the extension goes"
            " there, not into the name)"
        )
      else:
        shape = f'"{value.label}"'
      if not gap:
        lines.append(f"- {shape}: typed")
      elif len(gap) == len(value.parts):
        lines.append(f"- {shape}: NOT typed yet")
      else:
        missing = ", ".join(f'"{p}"' for p in gap)
        lines.append(f"- {shape}: still missing {missing}")
    return "\n".join(lines)
