"""Prompts.

Layout follows the context-engineering rules from Day 2:

* The system prompt is a stable prefix: role, action space, rules. It does not
  change within a run, so it stays cache-friendly.
* Everything dynamic (goal, history, current screen, status bar) goes into one
  user message, with the most volatile part, the status bar, at the very end.
* The prompt is rebuilt every step instead of growing as a chat: old screens
  are never resent, only the one-line history. Context cost stays flat.
* Rules that must hold no matter what are NOT here. They are in guardrails.py.
"""

from __future__ import annotations

from typing import Any, Optional, Sequence

_ACTION_LINES_INDEX = """\
{"thought": "...", "action_type": "click", "index": 4}  -> tap element [4]
{"thought": "...", "action_type": "long_press", "index": 4}  -> press and hold element [4]
{"thought": "...", "action_type": "input_text", "index": 4, "text": "hello"}  -> tap text field [4], type the text, press Enter. Do not click the field first.
{"thought": "...", "action_type": "scroll", "direction": "down"}  -> show content further down ("up", "left", "right" work the same way)"""

_ACTION_LINES_COORDINATE = """\
{"thought": "...", "action_type": "click", "x": 500, "y": 300}  -> tap at this point
{"thought": "...", "action_type": "long_press", "x": 500, "y": 300}  -> press and hold at this point
{"thought": "...", "action_type": "input_text", "x": 500, "y": 300, "text": "hello"}  -> tap the text field at this point, type the text, press Enter. Do not click the field first.
{"thought": "...", "action_type": "scroll", "direction": "down"}  -> show content further down ("up", "left", "right" work the same way)"""

_ACTION_LINES_COMMON = """\
{"thought": "...", "action_type": "open_app", "app_name": "clock"}  -> open an app
{"thought": "...", "action_type": "navigate_back"}  -> Android back button
{"thought": "...", "action_type": "navigate_home"}  -> go to the home screen
{"thought": "...", "action_type": "keyboard_enter"}  -> press Enter
{"thought": "...", "action_type": "wait"}  -> wait for the screen to finish loading
{"thought": "...", "action_type": "status", "goal_status": "complete"}  -> the goal is fully achieved
{"thought": "...", "action_type": "status", "goal_status": "infeasible"}  -> the goal cannot be achieved"""

_SCREEN_INDEX = """\
CURRENT SCREEN lists the UI elements, one per line:
[index] Class "visible text" desc="description" hint="placeholder" (flags)
Point at an element with the number in [brackets]."""

_SCREEN_COORDINATE_REL = """\
CURRENT SCREEN is the attached screenshot. Point with "x" and "y", integers
from 0 to 1000 relative to the screenshot: x=0 is the left edge, x=1000 the
right edge, y=0 the top edge, y=1000 the bottom edge."""

_SCREEN_COORDINATE_PX = """\
CURRENT SCREEN is the attached screenshot. Point with "x" and "y" in pixels of
that screenshot (its size is stated each turn); 0,0 is the top-left corner."""


def system_prompt(
    grounding: str,
    allowed_apps: Sequence[str],
    coordinate_space: str = "relative_1000",
    with_notes: bool = False,
) -> str:
  """Stable prefix for the action-selection call."""
  if grounding == "index":
    screen, action_lines = _SCREEN_INDEX, _ACTION_LINES_INDEX
    pointing_rule = "Only use indices that appear in CURRENT SCREEN."
  else:
    screen = (
        _SCREEN_COORDINATE_REL
        if coordinate_space == "relative_1000"
        else _SCREEN_COORDINATE_PX
    )
    action_lines = _ACTION_LINES_COORDINATE
    pointing_rule = "Point at the centre of the element you mean."
  rules = [
      '"thought" comes first: one short sentence on what you see and why you'
      " choose this action.",
      "To open an app always use open_app with exactly one of these names: "
      + ", ".join(allowed_apps)
      + ". Never look for an app on the home screen or in a search bar.",
      "Copy names, numbers and texts from the GOAL exactly, character by"
      " character.",
      "If HISTORY says an action failed, was blocked or did not change the"
      " screen, do not repeat it. Try a different element or action.",
      pointing_rule,
      'Before you answer "complete", check on the CURRENT SCREEN that the'
      " result really exists (saved, sent, set). Stay in the app when you"
      " finish; do not go back or home afterwards.",
      "Never pay, buy, subscribe or enter payment details.",
  ]
  if with_notes:
    rules.append(
        "When you see a value you will need later (for example in another"
        ' app), add "note": "<the value>" to your reply. Your notes are shown'
        " to you again under STATUS."
    )
  numbered = "\n".join(f"{i}. {rule}" for i, rule in enumerate(rules, start=1))
  return (
      "You control an Android phone to complete a user's goal, one action at a"
      " time.\n\n"
      "Each turn you get the GOAL, the HISTORY of your previous actions and"
      " the CURRENT SCREEN. Reply with exactly one JSON object for the next"
      " action and nothing else.\n\n"
      f"{screen}\n\n"
      "Actions (pick one):\n"
      f"{action_lines}\n{_ACTION_LINES_COMMON}\n\n"
      f"Rules:\n{numbered}"
  )


def user_message(
    goal: str,
    history: str,
    tree_text: Optional[str],
    image_b64: Optional[str],
    image_size: Optional[tuple[int, int]] = None,
    state_size_hint: bool = False,
    status: Optional[str] = None,
    app_tips: Optional[str] = None,
    closing: str = "Reply with one JSON object for the next action.",
) -> dict[str, Any]:
  """The single dynamic message of a step. Volatile content goes last."""
  parts = [f"GOAL: {goal}", f"HISTORY:\n{history}"]
  if tree_text is not None:
    screen = f"CURRENT SCREEN:\n{tree_text}"
    if image_b64:
      screen += "\n(A screenshot of this screen is attached for visual context.)"
  else:
    screen = "CURRENT SCREEN: see the attached screenshot."
    if state_size_hint and image_size:
      screen += f" It is {image_size[0]}x{image_size[1]} pixels."
  parts.append(screen)
  if app_tips:
    parts.append(f"APP TIPS:\n{app_tips.strip()}")
  if status:
    parts.append(f"STATUS:\n{status}")
  parts.append(closing)
  message: dict[str, Any] = {"role": "user", "content": "\n\n".join(parts)}
  if image_b64:
    message["images"] = [image_b64]
  return message


VERIFIER_SYSTEM_PROMPT = (
    "You check the work of a phone agent. You get the GOAL, the HISTORY of the"
    " agent's actions and the CURRENT SCREEN. Decide whether the goal is fully"
    " achieved right now.\n\n"
    "Be strict. \"achieved\" is true only if the screen or the history shows"
    " clear evidence that every part of the goal was carried out, for example"
    " the item is saved, the message is sent, the value is set, with exactly"
    " the names, numbers and texts from the goal. If any part is missing,"
    " different, or you cannot see evidence for it, \"achieved\" is false.\n\n"
    "Reply with exactly one JSON object and nothing else:\n"
    '{"evidence": "<what you can see that proves or disproves it>",'
    ' "achieved": true or false,'
    ' "missing": "<what is still missing, empty if nothing>"}'
)

VERIFIER_CLOSING = "Is the goal fully achieved? Reply with the JSON object."

RETRY_TEMPLATE = (
    "Your reply could not be used: {error}\n"
    "Reply again with exactly one valid JSON object for the next action."
)
