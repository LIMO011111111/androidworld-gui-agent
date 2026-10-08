"""Test doubles: a scripted model and a tiny phone simulator.

They let the whole agent run without an emulator and without a model server,
so the harness rules can be tested deterministically.
"""

from __future__ import annotations

import dataclasses
import types
from typing import Any, Callable, Optional

import numpy as np

from gui_agent import model as model_lib

SCREEN = (1080, 2400)


def el(
    text: str = "",
    box: tuple[int, int, int, int] = (0, 0, 100, 100),
    *,
    desc: str = "",
    hint: str = "",
    cls: str = "android.widget.TextView",
    res: str = "",
    package: str = "net.gsantner.markor",
    clickable: bool = False,
    editable: bool = False,
    checkable: bool = False,
    checked: bool = False,
    scrollable: bool = False,
    focused: bool = False,
    visible: bool = True,
) -> Any:
  """A stand-in for android_world's UIElement (same attribute names)."""
  x0, y0, x1, y1 = box
  bbox = types.SimpleNamespace(x_min=x0, x_max=x1, y_min=y0, y_max=y1)
  return types.SimpleNamespace(
      text=text or None,
      content_description=desc or None,
      hint_text=hint or None,
      class_name=cls,
      resource_name=res or None,
      package_name=package,
      bbox_pixels=bbox,
      is_visible=visible,
      is_clickable=clickable,
      is_long_clickable=False,
      is_editable=editable,
      is_checkable=checkable,
      is_checked=checked,
      is_scrollable=scrollable,
      is_selected=False,
      is_focused=focused,
      is_enabled=True,
  )


class ScriptedModel:
  """Returns prepared replies in order and remembers what it was asked."""

  name = "scripted-model"

  def __init__(self, replies: list[str]):
    self._replies = list(replies)
    self.calls: list[dict[str, Any]] = []

  def chat(self, messages, schema=None) -> model_lib.ModelReply:
    self.calls.append({"messages": messages, "schema": schema})
    if not self._replies:
      raise AssertionError("ScriptedModel ran out of replies")
    return model_lib.ModelReply(
        text=self._replies.pop(0), latency_s=0.01,
        prompt_tokens=100, completion_tokens=10,
    )

  def describe(self) -> dict[str, Any]:
    return {"backend": "scripted", "model": self.name}

  @property
  def remaining(self) -> int:
    return len(self._replies)


@dataclasses.dataclass
class FakeState:
  pixels: np.ndarray
  forest: Any
  ui_elements: list[Any]
  auxiliaries: Optional[dict[str, Any]] = None


class FakePhone:
  """A phone that is a set of named screens plus a transition function.

  Duck-types the parts of android_world's AsyncEnv that the agent uses.
  `on_action(phone, action)` may change `phone.current`.
  """

  def __init__(
      self,
      screens: dict[str, list[Any]],
      start: str,
      on_action: Optional[Callable[["FakePhone", Any], None]] = None,
      size: tuple[int, int] = SCREEN,
      default_package: str = "net.gsantner.markor",
  ):
    self.default_package = default_package
    self.screens = screens
    self.current = start
    self._start = start
    self._on_action = on_action
    self._size = size
    self.executed: list[Any] = []
    self.interaction_cache = ""
    self.controller = object()

  # --- AsyncEnv surface used by the agent -----------------------------------
  def reset(self, go_home: bool = False) -> FakeState:
    self.current = self._start
    return self.get_state()

  def get_state(self, wait_to_stabilize: bool = False) -> FakeState:
    pixels = np.zeros((240, 108, 3), dtype=np.uint8)
    pixels.setflags(write=False)  # AndroidWorld hands out read-only arrays
    return FakeState(pixels, None, list(self.screens[self.current]))

  def execute_action(self, action: Any) -> None:
    self.executed.append(action)
    if self._on_action is not None:
      self._on_action(self, action)

  def hide_automation_ui(self) -> None:
    pass

  @property
  def logical_screen_size(self) -> tuple[int, int]:
    return self._size

  @property
  def device_screen_size(self) -> tuple[int, int]:
    return self._size

  @property
  def foreground_activity_name(self) -> str:
    """The resumed activity: the app that owns the current screen."""
    elements = self.screens[self.current]
    package = elements[0].package_name if elements else self.default_package
    return f"{package}/.Main"

  def close(self) -> None:
    pass


class FakeTask:
  """Minimal AndroidWorld task: succeeds when the phone shows a given screen."""

  complexity = 1.0

  def __init__(self, goal: str, success_screen: str):
    self.goal = goal
    self._success_screen = success_screen
    self.initialized = False
    self.torn_down = False

  def initialize_task(self, env: FakePhone) -> None:
    self.initialized = True

  def is_successful(self, env: FakePhone) -> float:
    return 1.0 if env.current == self._success_screen else 0.0

  def tear_down(self, env: FakePhone) -> None:
    self.torn_down = True
