"""Agent configuration.

Every design decision the lecture asks us to justify is one field here, so a
run is fully described by its config file (reproducibility) and V1 / V2 / V3
differ only in flags (clean before-after comparison).
"""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path
from typing import Any

# The apps the agent may operate: AndroidWorld name -> Android package.
#
# This table is the agent's whole world. `open_app` only accepts these names
# and, while any other app is in the foreground, the agent can do nothing but
# leave (guardrails.AppScope). It deliberately contains no store, wallet,
# shopping, banking or browser app: every entry is an offline app without any
# payment function. That closed set, enforced in code, is the first layer of
# the payment ban and the fix for the `wrong_app` failure class.
# Names are the exact ones AndroidWorld's launch_app understands
# (android_world/env/adb_utils.py); a unit test checks the packages against it.
APP_PACKAGES = {
    "markor": "net.gsantner.markor",
    "simple sms messenger": "com.simplemobiletools.smsmessenger",
    "contacts": "com.google.android.contacts",
    "clock": "com.google.android.deskclock",
    "settings": "com.android.settings",
    "camera": "com.android.camera2",
    "files": "com.google.android.documentsui",
    "simple calendar pro": "com.simplemobiletools.calendar.pro",
    "simple gallery pro": "com.simplemobiletools.gallery.pro",
    "audio recorder": "com.dimowner.audiorecorder",
    "pro expense": "com.arduia.expense",
    "broccoli": "com.flauschcode.broccoli",
    "tasks": "org.tasks",
    "joplin": "net.cozic.joplin",
    "osmand": "net.osmand",
    "open tracks": "de.dennisguse.opentracks",
    "vlc": "org.videolan.vlc",
    "retro music": "code.name.monkey.retromusic",
}
DEFAULT_ALLOWED_APPS = tuple(APP_PACKAGES)

# Android's own surfaces that appear on top of or between apps: dialogs and
# the share sheet ("android"), status bar and notification shade, permission
# prompts, the system file picker. Always in scope.
SYSTEM_PACKAGES = (
    "android",
    "com.android.systemui",
    "com.android.intentresolver",
    "com.android.permissioncontroller",
    "com.google.android.permissioncontroller",
    "com.android.documentsui",
    "com.google.android.documentsui",
    "com.android.providers.media.module",
    "com.google.android.providers.media.module",
)

OBSERVATIONS = ("screenshot", "tree", "both")
GROUNDINGS = ("coordinate", "index")
COORDINATE_SPACES = ("relative_1000", "image_pixels")
BACKENDS = ("ollama", "openai")


@dataclasses.dataclass
class AgentConfig:
  """All knobs of the agent. Defaults are the full V3 harness."""

  name: str = "v3_full"

  # --- Model -----------------------------------------------------------------
  backend: str = "ollama"  # "ollama" (native API) or "openai" (compatible API)
  model: str = "qwen3-vl:4b-instruct"
  base_url: str = "http://localhost:11434"
  api_key_env: str = ""  # name of the env var holding the key (openai backend)
  temperature: float = 0.0  # 0 + fixed seed: runs are repeatable (Day 1)
  seed: int = 42
  num_ctx: int = 8192  # Ollama defaults to 4096, too small for tree + image
  max_output_tokens: int = 400
  request_timeout_s: float = 300.0
  constrain_output: bool = True  # JSON-schema constrained decoding
  think: bool | None = None  # only sent to Ollama when not None

  # --- Observation space (first design decision of the project) -------------
  observation: str = "tree"  # "screenshot" | "tree" | "both"
  image_max_side: int = 1024  # screenshots are downscaled before sending
  max_elements: int = 70  # cap on tree lines, keeps context cost bounded
  drop_status_bar: bool = True  # hide clock/battery icons from the tree

  # --- Grounding --------------------------------------------------------------
  grounding: str = "index"  # "index" (table lookup in our code) | "coordinate"
  coordinate_space: str = "relative_1000"  # Qwen3-VL / GELab-Zero convention
  # Lecture rule: "take the index route unless the tree is empty". With fewer
  # usable elements than this, an index-mode step falls back to pixels.
  # 1 = fall back only when the tree exposes nothing at all.
  pixel_fallback_min_elements: int = 1

  # --- Harness (rules that live in code, not in the prompt) -----------------
  max_steps: int = 20  # hard step limit; the per-task budget can only lower it
  parse_retries: int = 2  # validate-and-retry on malformed model output
  history_lines: int = 8  # older steps are dropped from the prompt
  wait_for_stable: bool = True  # wait until the UI stops changing (too_early)
  transition_pause_s: float = 2.0  # fixed pause when wait_for_stable is False
  screen_change_hint: bool = True  # tell the model when an action had no effect
  loop_guard: bool = True  # block identical actions that change nothing
  max_loop_blocks: int = 3  # abort the episode after this many blocks
  status_bar: bool = True  # code-maintained status + scratch notes (lost_value)
  verify_before_done: bool = True  # check step before `status: complete`
  max_done_rejections: int = 2
  use_skills: bool = False  # load skills/<app>.md tips for the foreground app
  # V4: code tracks which literal values from the goal (names, numbers, file
  # names, note text) were typed, shows the gaps every step and vetoes
  # "complete" while a value was never typed (fix for `lost_value`, without a
  # second model call). At most `max_done_rejections` vetoes.
  goal_tracker: bool = False

  # --- Safety -----------------------------------------------------------------
  # Which of the apps in APP_PACKAGES this agent may operate. To add an app,
  # add it to APP_PACKAGES in code first; a config file cannot introduce one.
  allowed_apps: tuple[str, ...] = DEFAULT_ALLOWED_APPS
  # Extra packages that count as "in scope", for system surfaces of a device
  # that are not in SYSTEM_PACKAGES (a different launcher is recognised
  # automatically). Payment and store packages are rejected at load time.
  extra_scope_packages: tuple[str, ...] = ()

  def __post_init__(self) -> None:
    for field in dataclasses.fields(self):
      value = getattr(self, field.name)
      if field.type in ("bool", bool) and not isinstance(value, bool):
        raise ValueError(f"{field.name} must be true or false, got {value!r}")
    for name in ("allowed_apps", "extra_scope_packages"):
      value = getattr(self, name)
      if isinstance(value, str) or not all(isinstance(v, str) for v in value):
        raise ValueError(f"{name} must be a list of strings")
    self.allowed_apps = tuple(a.strip().lower() for a in self.allowed_apps)
    self.extra_scope_packages = tuple(p.strip() for p in self.extra_scope_packages)
    unknown_apps = [a for a in self.allowed_apps if a not in APP_PACKAGES]
    if unknown_apps:
      raise ValueError(
          f"allowed_apps contains apps that are not in APP_PACKAGES:"
          f" {unknown_apps}. Known apps: {sorted(APP_PACKAGES)}"
      )
    if self.observation not in OBSERVATIONS:
      raise ValueError(f"observation must be one of {OBSERVATIONS}")
    if self.grounding not in GROUNDINGS:
      raise ValueError(f"grounding must be one of {GROUNDINGS}")
    if self.coordinate_space not in COORDINATE_SPACES:
      raise ValueError(f"coordinate_space must be one of {COORDINATE_SPACES}")
    if self.backend not in BACKENDS:
      raise ValueError(f"backend must be one of {BACKENDS}")
    if self.grounding == "index" and self.observation == "screenshot":
      raise ValueError(
          "index grounding needs the accessibility tree in the observation"
          " (observation must be 'tree' or 'both')"
      )
    if self.grounding == "coordinate" and self.observation != "screenshot":
      raise ValueError(
          "coordinate grounding is the pixels-only setting: observation must"
          " be 'screenshot' (with a tree in the prompt, use index grounding)"
      )
    if self.max_steps < 1:
      raise ValueError("max_steps must be at least 1")
    if self.parse_retries < 0 or self.max_done_rejections < 0:
      raise ValueError("parse_retries and max_done_rejections must be >= 0")
    if self.transition_pause_s < 0:
      raise ValueError("transition_pause_s must be >= 0")
    if self.history_lines < 1 or self.max_elements < 1:
      raise ValueError("history_lines and max_elements must be at least 1")
    if not self.allowed_apps:
      raise ValueError("allowed_apps must not be empty")

  def scope_packages(self) -> tuple[str, ...]:
    """Packages the agent may act in: allowed apps, system surfaces, extras."""
    apps = tuple(APP_PACKAGES[a] for a in self.allowed_apps)
    return apps + SYSTEM_PACKAGES + self.extra_scope_packages

  def replace(self, **changes: Any) -> "AgentConfig":
    """A validated copy with some fields changed (for CLI overrides)."""
    return dataclasses.replace(self, **changes)

  # -- (de)serialisation -------------------------------------------------------
  def to_dict(self) -> dict[str, Any]:
    data = dataclasses.asdict(self)
    data["allowed_apps"] = list(self.allowed_apps)
    data["extra_scope_packages"] = list(self.extra_scope_packages)
    return data

  @classmethod
  def from_dict(cls, data: dict[str, Any]) -> "AgentConfig":
    known = {f.name for f in dataclasses.fields(cls)}
    unknown = sorted(k for k in data if k not in known and not k.startswith("_"))
    if unknown:
      raise ValueError(f"Unknown config keys: {unknown}")
    clean = {k: v for k, v in data.items() if k in known}
    for name in ("allowed_apps", "extra_scope_packages"):
      if name in clean and isinstance(clean[name], list):
        clean[name] = tuple(clean[name])
    return cls(**clean)

  @classmethod
  def from_file(cls, path: str | Path) -> "AgentConfig":
    with open(path, "r", encoding="utf-8") as f:
      return cls.from_dict(json.load(f))
