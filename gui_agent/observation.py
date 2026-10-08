"""Observation space: what the model gets to see.

Two renderings of the same screen (lecture Day 1, "Observation beyond texts"):

* the accessibility tree as one text line per element, with exact boxes kept
  on our side (cheap, precise, incomplete), and
* the screenshot, downscaled (sees everything, but the model must point).

Nothing in this module talks to the model or the device. It only turns an
AndroidWorld `State` into text, images and fingerprints, so it is unit-testable
without an emulator.
"""

from __future__ import annotations

import base64
import collections
import dataclasses
import hashlib
import io
from typing import Any, Iterable, Optional, Sequence

import numpy as np
from PIL import Image, ImageDraw

_SYSTEM_UI_PACKAGE = "com.android.systemui"
_MAX_LABEL_CHARS = 100


def is_keyboard_package(package: str) -> bool:
  """True for on-screen keyboards (Gboard, AOSP keyboard, ...)."""
  return "inputmethod" in (package or "").lower()


def is_launcher_package(package: str) -> bool:
  """True for home-screen apps (Pixel launcher, Launcher3, ...)."""
  return "launcher" in (package or "").lower()


@dataclasses.dataclass(frozen=True)
class ElementView:
  """One UI element as the agent uses it.

  `index` is the position in `state.ui_elements`, i.e. exactly the index
  AndroidWorld itself would accept. The bounding box is in logical screen
  pixels, the coordinate space of `adb input tap`.
  """

  index: int
  class_name: str
  text: str
  description: str
  hint: str
  resource: str
  package: str
  x_min: int
  y_min: int
  x_max: int
  y_max: int
  clickable: bool = False
  long_clickable: bool = False
  editable: bool = False
  checkable: bool = False
  checked: bool = False
  selected: bool = False
  focused: bool = False
  scrollable: bool = False
  enabled: bool = True

  @property
  def center(self) -> tuple[int, int]:
    return (self.x_min + self.x_max) // 2, (self.y_min + self.y_max) // 2

  @property
  def area(self) -> int:
    return max(0, self.x_max - self.x_min) * max(0, self.y_max - self.y_min)

  def contains(self, x: int, y: int) -> bool:
    return self.x_min <= x <= self.x_max and self.y_min <= y <= self.y_max

  def label(self) -> str:
    """The text line shown to the model, e.g. `[4] Button "Save" (clickable)`."""
    parts = [f"[{self.index}] {self.class_name or 'View'}"]
    # Android reports the hint of an EMPTY text field as its text. Showing it
    # as text would make the field look filled in.
    text = "" if self.editable and self.text == self.hint else self.text
    if text:
      parts.append(f'"{_clip(text)}"')
    if self.description and self.description != text:
      parts.append(f'desc="{_clip(self.description)}"')
    if self.hint:
      parts.append(f'hint="{_clip(self.hint)}"')
    elif self.editable and not text:
      parts.append("(empty)")
    if self.resource and not (self.text or self.description):
      parts.append(f"id={self.resource}")
    flags = []
    if self.editable:
      flags.append("editable")
    elif self.clickable:
      flags.append("clickable")
    if self.checkable:
      flags.append("checked" if self.checked else "unchecked")
    if self.selected:
      flags.append("selected")
    if self.focused:
      flags.append("focused")
    if self.scrollable:
      flags.append("scrollable")
    if not self.enabled:
      flags.append("disabled")
    if flags:
      parts.append("(" + ", ".join(flags) + ")")
    return " ".join(parts)

  def short(self) -> str:
    """Compact form for history lines and logs."""
    name = self.text or self.description or self.hint or self.resource
    return f'[{self.index}] {self.class_name or "View"} "{_clip(name, 40)}"'


def _clip(value: str, limit: int = _MAX_LABEL_CHARS) -> str:
  value = " ".join(str(value).split())  # collapse newlines and runs of spaces
  value = value.replace('"', "'")
  return value if len(value) <= limit else value[: limit - 1] + "…"


def _short_class(class_name: Optional[str]) -> str:
  return (class_name or "").rsplit(".", 1)[-1]


def _short_resource(resource_name: Optional[str]) -> str:
  if not resource_name:
    return ""
  return resource_name.rsplit("/", 1)[-1]


def build_views(
    ui_elements: Sequence[Any],
    screen_size: tuple[int, int],
    drop_status_bar: bool = True,
    drop_keyboard: bool = True,
) -> list[ElementView]:
  """Filters and converts AndroidWorld UIElements.

  Keeps an element when it is visible, has a real on-screen box and either
  says something (text / description / hint) or can be acted on. Indices are
  preserved, never renumbered.

  The keys of the on-screen keyboard are dropped: the agent types with
  `input_text`, and dozens of key elements would crowd out the real screen.
  """
  width, height = screen_size
  status_bar_bottom = int(height * 0.06)
  views = []
  for index, el in enumerate(ui_elements):
    if getattr(el, "is_visible", True) is False:
      continue
    box = getattr(el, "bbox_pixels", None)
    if box is None:
      continue
    x_min, x_max = int(box.x_min), int(box.x_max)
    y_min, y_max = int(box.y_min), int(box.y_max)
    if x_min >= x_max or y_min >= y_max:
      continue
    if x_min >= width or x_max <= 0 or y_min >= height or y_max <= 0:
      continue
    package = getattr(el, "package_name", None) or ""
    if drop_keyboard and is_keyboard_package(package):
      continue
    if (
        drop_status_bar
        and package == _SYSTEM_UI_PACKAGE
        and y_max <= status_bar_bottom
    ):
      continue
    text = getattr(el, "text", None) or ""
    description = getattr(el, "content_description", None) or ""
    hint = getattr(el, "hint_text", None) or ""
    clickable = bool(getattr(el, "is_clickable", False))
    long_clickable = bool(getattr(el, "is_long_clickable", False))
    editable = bool(getattr(el, "is_editable", False))
    checkable = bool(getattr(el, "is_checkable", False))
    scrollable = bool(getattr(el, "is_scrollable", False))
    says_something = bool(text or description or hint)
    actionable = clickable or long_clickable or editable or checkable or scrollable
    if not (says_something or actionable):
      continue
    views.append(
        ElementView(
            index=index,
            class_name=_short_class(getattr(el, "class_name", None)),
            text=text,
            description=description,
            hint=hint,
            resource=_short_resource(getattr(el, "resource_name", None)),
            package=package,
            x_min=max(0, x_min),
            y_min=max(0, y_min),
            x_max=min(width, x_max),
            y_max=min(height, y_max),
            clickable=clickable,
            long_clickable=long_clickable,
            editable=editable,
            checkable=checkable,
            checked=bool(getattr(el, "is_checked", False)),
            selected=bool(getattr(el, "is_selected", False)),
            focused=bool(getattr(el, "is_focused", False)),
            scrollable=scrollable,
            enabled=getattr(el, "is_enabled", True) is not False,
        )
    )
  return views


def keyboard_visible(ui_elements: Sequence[Any]) -> bool:
  """True if the on-screen keyboard is showing."""
  return any(
      is_keyboard_package(getattr(el, "package_name", None) or "")
      and getattr(el, "is_visible", True) is not False
      for el in ui_elements
  )


def render_tree(
    views: Sequence[ElementView], max_elements: int, keyboard: bool = False
) -> str:
  """Renders the element list for the prompt, capped at `max_elements`."""
  if not views:
    return "(no UI elements are exposed on this screen)"
  lines = [v.label() for v in views[:max_elements]]
  hidden = len(views) - max_elements
  if hidden > 0:
    lines.append(f"(+{hidden} more elements not shown; scroll to reach them)")
  if keyboard:
    lines.append("(the on-screen keyboard is open)")
  return "\n".join(lines)


def fingerprint(views: Iterable[ElementView], keyboard: bool = False) -> str:
  """A hash that changes when the visible screen changes.

  Used for three harness rules: "did my action do anything?", loop detection
  and the screen-changed check before continuing. Focus is ignored on purpose:
  a blinking cursor must not count as progress. The keyboard appearing or
  disappearing does count.
  """
  digest = hashlib.sha1()
  digest.update(b"keyboard" if keyboard else b"")
  for v in views:
    digest.update(
        repr((
            v.class_name, v.text, v.description, v.hint, v.resource,
            v.x_min, v.y_min, v.x_max, v.y_max, v.checked, v.selected,
        )).encode("utf-8")
    )
  return digest.hexdigest()[:16]


def foreground_package(views: Iterable[ElementView]) -> str:
  """Package that owns most of the visible elements (no extra adb call)."""
  counts = collections.Counter(
      v.package for v in views
      if v.package
      and v.package != _SYSTEM_UI_PACKAGE
      and not is_keyboard_package(v.package)
  )
  if not counts:
    return ""
  return counts.most_common(1)[0][0]


def hit_test(
    views: Sequence[ElementView], x: int, y: int
) -> Optional[ElementView]:
  """The smallest element containing the point, or None if the tap hits nothing.

  In coordinate mode the model never sees the tree, but the harness still has
  it. This lets us (a) log what a pixel tap actually landed on, which is the
  evidence for the `grounding` failure class, and (b) apply the payment ban to
  coordinate taps too.
  """
  hits = hits_at(views, x, y)
  if not hits:
    return None
  return min(hits, key=lambda v: v.area)


def hits_at(views: Sequence[ElementView], x: int, y: int) -> list[ElementView]:
  """Every element whose box contains the point."""
  return [v for v in views if v.contains(x, y)]


# --- Images ------------------------------------------------------------------


def to_pil(pixels: np.ndarray) -> Image.Image:
  # AndroidWorld hands out a read-only view; copy before touching it.
  return Image.fromarray(np.ascontiguousarray(pixels, dtype=np.uint8)).convert("RGB")


def encode_screenshot(
    pixels: np.ndarray, max_side: int
) -> tuple[str, tuple[int, int]]:
  """Downscales and JPEG-encodes a screenshot.

  Returns the base64 string and the (width, height) the model actually sees.
  Screenshots are the expensive part of the context, so we shrink them and we
  only ever send the latest one.
  """
  image = to_pil(pixels)
  width, height = image.size
  scale = min(1.0, max_side / float(max(width, height)))
  if scale < 1.0:
    image = image.resize(
        (max(1, round(width * scale)), max(1, round(height * scale))),
        Image.LANCZOS,
    )
  buffer = io.BytesIO()
  image.save(buffer, format="JPEG", quality=85)
  return base64.b64encode(buffer.getvalue()).decode("ascii"), image.size


def annotated_screenshot(
    pixels: np.ndarray,
    logical_size: tuple[int, int],
    tap_xy: Optional[tuple[int, int]] = None,
    box: Optional[tuple[int, int, int, int]] = None,
    max_side: int = 1024,
) -> Image.Image:
  """Screenshot for the trajectory log with the tap point drawn on it.

  Makes pointing errors visible at a glance when reviewing a failed run.
  """
  image = to_pil(pixels)
  sx = image.width / float(logical_size[0])
  sy = image.height / float(logical_size[1])
  draw = ImageDraw.Draw(image)
  stroke = max(3, image.width // 180)
  if box is not None:
    x0, y0, x1, y1 = box
    draw.rectangle(
        [x0 * sx, y0 * sy, x1 * sx, y1 * sy], outline=(0, 200, 0), width=stroke
    )
  if tap_xy is not None:
    cx, cy = tap_xy[0] * sx, tap_xy[1] * sy
    radius = max(14, image.width // 40)
    draw.ellipse(
        [cx - radius, cy - radius, cx + radius, cy + radius],
        outline=(255, 0, 0),
        width=stroke,
    )
    draw.line([cx - 2 * radius, cy, cx + 2 * radius, cy], fill=(255, 0, 0), width=stroke)
    draw.line([cx, cy - 2 * radius, cx, cy + 2 * radius], fill=(255, 0, 0), width=stroke)
  scale = min(1.0, max_side / float(max(image.size)))
  if scale < 1.0:
    image = image.resize(
        (max(1, round(image.width * scale)), max(1, round(image.height * scale))),
        Image.LANCZOS,
    )
  return image
