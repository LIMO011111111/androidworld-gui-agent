"""Action space and grounding.

The model only ever produces text. This module is the program "outside" that
turns that text into something the device can execute (lecture Day 1):

1. `parse_action`  - tolerant JSON extraction plus strict validation. A reply
   that does not validate raises `ActionError`; the message is sent back to
   the model for a retry ("validate and retry").
2. `resolve_action` - grounding. In index mode the model names an element and
   WE look up its box and compute the tap point: grounding is a table lookup
   in our code, a bug we can find. In coordinate mode the model produces the
   numbers and we only rescale them.

No AndroidWorld import here; the output is a plain dict of `JSONAction`
keyword arguments.
"""

from __future__ import annotations

import ast
import dataclasses
import json
import re
from typing import Any, Optional, Sequence

from gui_agent import observation

CLICK = "click"
LONG_PRESS = "long_press"
INPUT_TEXT = "input_text"
SCROLL = "scroll"
OPEN_APP = "open_app"
NAVIGATE_BACK = "navigate_back"
NAVIGATE_HOME = "navigate_home"
KEYBOARD_ENTER = "keyboard_enter"
WAIT = "wait"
STATUS = "status"

ACTION_TYPES = (
    CLICK,
    LONG_PRESS,
    INPUT_TEXT,
    SCROLL,
    OPEN_APP,
    NAVIGATE_BACK,
    NAVIGATE_HOME,
    KEYBOARD_ENTER,
    WAIT,
    STATUS,
)
POINTING_ACTIONS = (CLICK, LONG_PRESS, INPUT_TEXT)
DIRECTIONS = ("up", "down", "left", "right")
COMPLETE = "complete"
INFEASIBLE = "infeasible"

_ACTION_ALIASES = {
    "tap": CLICK,
    "press": CLICK,
    "touch": CLICK,
    "longpress": LONG_PRESS,
    "long_click": LONG_PRESS,
    "type": INPUT_TEXT,
    "type_text": INPUT_TEXT,
    "input": INPUT_TEXT,
    "write": INPUT_TEXT,
    "open": OPEN_APP,
    "launch": OPEN_APP,
    "launch_app": OPEN_APP,
    "awake": OPEN_APP,
    "back": NAVIGATE_BACK,
    "home": NAVIGATE_HOME,
    "enter": KEYBOARD_ENTER,
    "done": STATUS,
    "complete": STATUS,
    "finish": STATUS,
    "finished": STATUS,
}
_STATUS_ALIASES = {
    "complete": COMPLETE,
    "completed": COMPLETE,
    "done": COMPLETE,
    "success": COMPLETE,
    "successful": COMPLETE,
    "task_complete": COMPLETE,
    "infeasible": INFEASIBLE,
    "impossible": INFEASIBLE,
    "failed": INFEASIBLE,
    "abort": INFEASIBLE,
}
_OPPOSITE = {"up": "down", "down": "up", "left": "right", "right": "left"}


class ActionError(ValueError):
  """The model's reply cannot be turned into a valid action.

  The message is written for the model: it is appended to the conversation
  and the model gets another try.
  """


@dataclasses.dataclass
class AgentAction:
  """A validated action in the agent's own vocabulary."""

  action_type: str
  index: Optional[int] = None
  x: Optional[int] = None
  y: Optional[int] = None
  text: Optional[str] = None
  direction: Optional[str] = None
  app_name: Optional[str] = None
  goal_status: Optional[str] = None
  thought: str = ""
  note: str = ""

  def as_dict(self) -> dict[str, Any]:
    return {k: v for k, v in dataclasses.asdict(self).items() if v not in (None, "")}

  def signature(self) -> str:
    """Identity of the action for loop detection (thought and note ignored)."""
    return json.dumps(
        [self.action_type, self.index, self.x, self.y, self.text,
         self.direction, self.app_name, self.goal_status]
    )


@dataclasses.dataclass
class ResolvedAction:
  """An action after grounding, ready for the guardrails and the device."""

  action: AgentAction
  env_action: dict[str, Any]  # kwargs for android_world JSONAction
  description: str  # code-written line that goes into the history
  grounding: str  # "index" | "coordinate" | "none"
  target: Optional[observation.ElementView] = None  # what the tap lands on
  tap_xy: Optional[tuple[int, int]] = None  # logical screen pixels


# --- Parsing -----------------------------------------------------------------


def extract_json_object(raw: str) -> dict[str, Any]:
  """Finds the first complete JSON object in the model output.

  Handles the format drift from the lecture: prose before the JSON, markdown
  fences, <think> blocks, nested braces and braces inside strings.
  """
  if not raw or not raw.strip():
    raise ActionError("Your reply was empty. Reply with one JSON object.")
  text = re.sub(r"<think>.*?</think>", " ", raw, flags=re.DOTALL | re.IGNORECASE)
  # Reasoning that was cut off before </think> must not be mined for actions.
  text = re.split(r"<think>", text, flags=re.IGNORECASE)[0]
  start = text.find("{")
  while start != -1:
    depth = 0
    in_string = False
    quote = ""
    escaped = False
    for pos in range(start, len(text)):
      ch = text[pos]
      if in_string:
        if escaped:
          escaped = False
        elif ch == "\\":
          escaped = True
        elif ch == quote:
          in_string = False
        continue
      if ch in "\"'":
        in_string, quote = True, ch
      elif ch == "{":
        depth += 1
      elif ch == "}":
        depth -= 1
        if depth == 0:
          candidate = text[start : pos + 1]
          parsed = _loads_lenient(candidate)
          if isinstance(parsed, dict):
            return parsed
          break
    start = text.find("{", start + 1)
  raise ActionError(
      "Your reply did not contain a valid JSON object. Reply with exactly one"
      ' JSON object such as {"thought": "...", "action_type": "wait"}.'
  )


def _loads_lenient(candidate: str) -> Any:
  # Whatever the model wrote, a parse problem must surface as "invalid
  # reply" (and be retried), never as an exception that kills the episode.
  try:
    return json.loads(candidate)
  except Exception:  # pylint: disable=broad-exception-caught
    pass
  try:
    return ast.literal_eval(candidate)  # single quotes, True/False/None
  except Exception:  # pylint: disable=broad-exception-caught
    return None


def _as_int(value: Any, name: str) -> int:
  if isinstance(value, bool):
    raise ActionError(f'"{name}" must be an integer.')
  try:
    number = float(str(value).strip())
  except (TypeError, ValueError):
    raise ActionError(f'"{name}" must be an integer, got {value!r}.') from None
  if number != number or number in (float("inf"), float("-inf")):
    raise ActionError(f'"{name}" must be an integer, got {value!r}.')
  return int(round(number))


def _present(value: Any) -> bool:
  return value is not None and not (isinstance(value, str) and not value.strip())


def parse_action(raw: str, grounding: str) -> AgentAction:
  """Turns raw model text into a validated `AgentAction` for this grounding mode."""
  data = extract_json_object(raw)
  data = {str(k).strip().lower(): v for k, v in data.items()}

  action_type = data.get("action_type", data.get("action"))
  if not isinstance(action_type, str) or not action_type.strip():
    raise ActionError(
        f'Missing "action_type". Choose one of: {", ".join(ACTION_TYPES)}.'
    )
  action_type = action_type.strip().lower().replace("-", "_").replace(" ", "_")
  flip_direction = action_type in ("swipe", "slide")  # finger direction
  if flip_direction:
    action_type = SCROLL
  goal_status = data.get("goal_status")
  if action_type in _STATUS_ALIASES and action_type not in ACTION_TYPES:
    goal_status = goal_status or _STATUS_ALIASES[action_type]
  action_type = _ACTION_ALIASES.get(action_type, action_type)
  if action_type in (INFEASIBLE, "impossible", "abort"):
    action_type, goal_status = STATUS, INFEASIBLE
  if action_type not in ACTION_TYPES:
    raise ActionError(
        f'Unknown action_type "{action_type}". Choose one of:'
        f' {", ".join(ACTION_TYPES)}.'
    )

  # Accept common alternative spellings of a point.
  point = data.get("point", data.get("coordinate", data.get("position")))
  if isinstance(point, (list, tuple)) and len(point) == 2:
    data.setdefault("x", point[0])
    data.setdefault("y", point[1])

  action = AgentAction(
      action_type=action_type,
      thought=str(data.get("thought", data.get("reason", "")) or "").strip(),
      note=str(data.get("note", "") or "").strip(),
  )

  if action_type in POINTING_ACTIONS:
    has_index = _present(data.get("index"))
    has_xy = _present(data.get("x")) and _present(data.get("y"))
    if grounding == "index":
      if has_index:
        action.index = _as_int(data["index"], "index")
      elif action_type != INPUT_TEXT:
        raise ActionError(
            f'"{action_type}" needs "index": the number in [brackets] of the'
            " element you want. Coordinates are not accepted."
        )
    else:
      if has_xy:
        action.x = _as_int(data["x"], "x")
        action.y = _as_int(data["y"], "y")
      elif action_type != INPUT_TEXT:
        raise ActionError(
            f'"{action_type}" needs integer "x" and "y" coordinates.'
        )

  if action_type == INPUT_TEXT:
    text = data.get("text", data.get("value"))
    if not _present(text):
      raise ActionError('"input_text" needs a non-empty "text".')
    action.text = str(text)

  elif action_type == SCROLL:
    direction = str(data.get("direction", "") or "").strip().lower()
    if direction not in DIRECTIONS:
      raise ActionError(
          '"scroll" needs "direction": one of up, down, left, right.'
      )
    action.direction = _OPPOSITE[direction] if flip_direction else direction
    if grounding == "index" and _present(data.get("index")):
      action.index = _as_int(data["index"], "index")

  elif action_type == OPEN_APP:
    app_name = data.get("app_name", data.get("app", data.get("value")))
    if not _present(app_name):
      raise ActionError('"open_app" needs "app_name".')
    action.app_name = str(app_name).strip()

  elif action_type == STATUS:
    status = str(goal_status or COMPLETE).strip().lower().replace(" ", "_")
    status = _STATUS_ALIASES.get(status)
    if status is None:
      raise ActionError(
          '"status" needs "goal_status": "complete" or "infeasible".'
      )
    action.goal_status = status

  return action


# --- Grounding ---------------------------------------------------------------


def scale_point(
    x: int,
    y: int,
    screen_size: tuple[int, int],
    coordinate_space: str,
    image_size: Optional[tuple[int, int]] = None,
) -> tuple[int, int]:
  """Model coordinates -> logical screen pixels (what `adb input tap` wants)."""
  width, height = screen_size
  if coordinate_space == "relative_1000":
    if not (0 <= x <= 1000 and 0 <= y <= 1000):
      raise ActionError(
          f"Coordinates ({x}, {y}) are out of range. x and y must be between"
          " 0 and 1000 (0,0 is the top-left corner, 1000,1000 bottom-right)."
      )
    px, py = x / 1000.0 * width, y / 1000.0 * height
  else:  # image_pixels: coordinates on the (downscaled) image we sent
    if not image_size:
      raise ActionError("No screenshot was sent, so coordinates cannot be used.")
    img_w, img_h = image_size
    if not (0 <= x <= img_w and 0 <= y <= img_h):
      raise ActionError(
          f"Coordinates ({x}, {y}) are outside the {img_w}x{img_h} screenshot."
      )
    px, py = x / float(img_w) * width, y / float(img_h) * height
  return (
      min(width - 1, max(0, int(round(px)))),
      min(height - 1, max(0, int(round(py)))),
  )


def resolve_action(
    action: AgentAction,
    views: Sequence[observation.ElementView],
    screen_size: tuple[int, int],
    grounding: str,
    coordinate_space: str = "relative_1000",
    image_size: Optional[tuple[int, int]] = None,
) -> ResolvedAction:
  """Grounds an action: decides the exact pixel the device will be told to tap."""
  kind = action.action_type
  by_index = {v.index: v for v in views}
  env: dict[str, Any] = {"action_type": kind}
  target = None
  tap_xy = None
  used = "none"

  if kind in POINTING_ACTIONS:
    if action.index is not None:
      target = by_index.get(action.index)
      if target is None:
        raise ActionError(
            f"There is no element [{action.index}] on the current screen."
            " Use an index from the CURRENT SCREEN list."
        )
      tap_xy = target.center
      used = "index"
    elif action.x is not None and action.y is not None:
      tap_xy = scale_point(
          action.x, action.y, screen_size, coordinate_space, image_size
      )
      target = observation.hit_test(views, *tap_xy)  # for logs and guardrails
      used = "coordinate"
    if tap_xy is not None:
      # We always hand AndroidWorld explicit pixels. Passing the index through
      # would make it re-resolve against a fresh UI dump, which can silently
      # point at a different element if the screen shifted in between.
      env["x"], env["y"] = tap_xy

  if kind == INPUT_TEXT:
    env["text"] = action.text
    if used == "index":
      where = f" into {target.short()}"
    elif used == "coordinate":
      where = f" at x={action.x} y={action.y}"
    else:
      where = " into the focused field"
    description = f'input_text "{action.text}"{where}'
  elif kind in (CLICK, LONG_PRESS):
    if used == "index":
      description = f"{kind} {target.short()}"
    else:
      description = f"{kind} at x={action.x} y={action.y}"
  elif kind == SCROLL:
    env["direction"] = action.direction
    description = f"scroll {action.direction}"
    scroll_target = by_index.get(action.index) if action.index is not None else None
    # Only scroll inside an element that is actually scrollable; otherwise
    # scroll the whole screen (a swipe inside a small button does nothing).
    # This is the one case where the index is handed to AndroidWorld: it has
    # no other way to scroll inside an element. Index 0 is excluded because
    # AndroidWorld treats it as "no index".
    if scroll_target is not None and scroll_target.scrollable and action.index:
      env["index"] = action.index
      target = scroll_target
      description += f" inside {target.short()}"
  elif kind == OPEN_APP:
    env["app_name"] = action.app_name
    description = f"open_app {action.app_name}"
  elif kind == STATUS:
    env["goal_status"] = action.goal_status
    description = f"status {action.goal_status}"
  else:
    description = kind

  return ResolvedAction(
      action=action,
      env_action=env,
      description=description,
      grounding=used,
      target=target,
      tap_xy=tap_xy,
  )


# --- Constrained decoding ----------------------------------------------------


def action_schema(
    grounding: str, allowed_apps: Sequence[str], with_note: bool
) -> dict[str, Any]:
  """JSON schema handed to the model server for constrained decoding.

  Invalid action types and app names that are not on the allow-list cannot be
  generated at all (Day 1: "constrain the decoding so invalid tokens cannot be
  produced"). Validation in `parse_action` still runs afterwards, because not
  every backend enforces a schema.
  """
  properties: dict[str, Any] = {
      "thought": {"type": "string"},
      "action_type": {"type": "string", "enum": list(ACTION_TYPES)},
  }
  if grounding == "index":
    properties["index"] = {"type": "integer"}
  else:
    properties["x"] = {"type": "integer"}
    properties["y"] = {"type": "integer"}
  properties["text"] = {"type": "string"}
  properties["direction"] = {"type": "string", "enum": list(DIRECTIONS)}
  properties["app_name"] = {"type": "string", "enum": list(allowed_apps)}
  properties["goal_status"] = {"type": "string", "enum": [COMPLETE, INFEASIBLE]}
  if with_note:
    properties["note"] = {"type": "string"}
  return {
      "type": "object",
      "properties": properties,
      "required": ["thought", "action_type"],
  }


VERIFIER_SCHEMA = {
    "type": "object",
    "properties": {
        "evidence": {"type": "string"},
        "achieved": {"type": "boolean"},
        "missing": {"type": "string"},
    },
    "required": ["evidence", "achieved"],
}
