"""Checks that everything needed for an evaluation run is in place.

    python scripts/doctor.py                       # all checks
    python scripts/doctor.py --config configs/v1_baseline.json
    python scripts/doctor.py --skip_model          # no model calls

The model check sends one tree prompt and one screenshot prompt through the
same code the agent uses and reports validity, latency and, for the
screenshot, whether the tap coordinates land inside the target button. Run it
whenever you change the model, the quantisation or the Ollama version.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from gui_agent import actions  # noqa: E402
from gui_agent import config as config_lib  # noqa: E402
from gui_agent import model as model_lib  # noqa: E402
from gui_agent import observation  # noqa: E402
from gui_agent import prompts  # noqa: E402
from gui_agent import recorder  # noqa: E402

OK, WARN, FAIL = "ok  ", "WARN", "FAIL"
_problems = 0
_needs_app_setup = False


def report(status: str, what: str, detail: str = "") -> None:
  global _problems
  if status == FAIL:
    _problems += 1
  print(f"[{status}] {what}" + (f": {detail}" if detail else ""))


def run(command: list[str], timeout: int = 30) -> tuple[int, str]:
  try:
    done = subprocess.run(command, capture_output=True, timeout=timeout, check=False)
    return done.returncode, (done.stdout + done.stderr).decode("utf-8", "replace").strip()
  except (OSError, subprocess.SubprocessError) as error:
    return 1, str(error)


def check_python() -> None:
  version = sys.version_info
  text = f"{version.major}.{version.minor}.{version.micro}"
  if (version.major, version.minor) in ((3, 11), (3, 12)):
    report(OK, "Python", text)
  else:
    report(WARN, "Python", f"{text}; AndroidWorld's pinned packages expect 3.11")


def check_android_world() -> None:
  try:
    from android_world import registry  # pylint: disable=import-outside-toplevel
    from android_world.agents import base_agent  # noqa: F401 pylint: disable=import-outside-toplevel,unused-import
    names = registry.TaskRegistry().get_registry("android_world")
    report(OK, "AndroidWorld import", f"{len(names)} tasks in the registry")
  except Exception as error:  # pylint: disable=broad-exception-caught
    report(FAIL, "AndroidWorld import", f"{type(error).__name__}: {error}")


def check_device(adb_path: str, console_port: int) -> None:
  adb = recorder.find_adb(adb_path or None)
  if not adb:
    report(FAIL, "adb", "not found; install Android SDK platform-tools")
    return
  report(OK, "adb", adb)
  serial = f"emulator-{console_port}"
  _, devices = run([adb, "devices"])
  if f"{serial}\tdevice" not in devices:
    report(FAIL, "emulator", f"{serial} is not online. Start it with"
           " scripts/start_emulator.sh (adb devices says: "
           + " / ".join(devices.splitlines()[1:]) + ")")
    return
  report(OK, "emulator", f"{serial} is online")
  _, booted = run([adb, "-s", serial, "shell", "getprop", "sys.boot_completed"])
  if booted.strip() != "1":
    report(FAIL, "emulator boot", "Android is still booting. Wait for the"
           " home screen and run this check again")
    return
  _, sdk = run([adb, "-s", serial, "shell", "getprop", "ro.build.version.sdk"])
  report(OK if sdk.strip() == "33" else WARN, "Android API level",
         f"{sdk.strip()} (AndroidWorld is built for 33)")
  _, size = run([adb, "-s", serial, "shell", "wm", "size"])
  good = "1080x2400" in size
  report(OK if good else WARN, "screen size",
         size.replace("\n", " ") + ("" if good else " (expected 1080x2400, Pixel 6)"))
  code, _ = run([adb, "-s", serial, "shell", "pm", "path", "net.gsantner.markor"])
  if code == 0:
    report(OK, "AndroidWorld apps", "Markor is installed")
  else:
    global _needs_app_setup
    _needs_app_setup = True
    report(WARN, "AndroidWorld apps", "Markor is not installed: run the first"
           " evaluation once with --perform_emulator_setup")


def check_tools() -> None:
  ffmpeg = shutil.which("ffmpeg")
  report(OK if ffmpeg else WARN, "ffmpeg",
         ffmpeg or "not found; recordings longer than ~3 min stay in parts")


def _sample_screen():
  """A synthetic 'new contact' screen as tree and as picture."""
  import types  # pylint: disable=import-outside-toplevel
  from PIL import Image, ImageDraw, ImageFont  # pylint: disable=import-outside-toplevel

  def element(text, box, cls, **flags):
    return types.SimpleNamespace(
        text=text or None, content_description=None, hint_text=flags.pop("hint", None),
        class_name=cls, resource_name=None, package_name="com.example.contacts",
        bbox_pixels=types.SimpleNamespace(x_min=box[0], y_min=box[1], x_max=box[2], y_max=box[3]),
        is_visible=True, is_clickable=flags.get("clickable", False),
        is_long_clickable=False, is_editable=flags.get("editable", False),
        is_checkable=False, is_checked=False, is_scrollable=False,
        is_selected=False, is_focused=False, is_enabled=True,
    )

  save_box = (290, 1500, 790, 1660)
  elements = [
      element("New contact", (60, 180, 1020, 300), "android.widget.TextView"),
      element("Anna Schmidt", (60, 480, 1020, 620), "android.widget.EditText",
              editable=True, hint="Name"),
      element("+4915112345678", (60, 760, 1020, 900), "android.widget.EditText",
              editable=True, hint="Phone"),
      element("SAVE", save_box, "android.widget.Button", clickable=True),
      element("CANCEL", (290, 1800, 790, 1960), "android.widget.Button", clickable=True),
  ]
  image = Image.new("RGB", (1080, 2400), (250, 250, 250))
  draw = ImageDraw.Draw(image)
  try:
    font = ImageFont.load_default(size=72)
  except TypeError:  # older Pillow
    font = ImageFont.load_default()
  draw.text((60, 200), "New contact", fill=(20, 20, 20), font=font)
  for label, (x0, y0, x1, y1) in (("Anna Schmidt", (60, 480, 1020, 620)),
                                 ("+4915112345678", (60, 760, 1020, 900))):
    draw.rectangle([x0, y0, x1, y1], outline=(120, 120, 120), width=4)
    draw.text((x0 + 30, y0 + 30), label, fill=(20, 20, 20), font=font)
  draw.rectangle(list(save_box), fill=(26, 115, 232))
  draw.text((save_box[0] + 150, save_box[1] + 40), "SAVE", fill=(255, 255, 255), font=font)
  draw.rectangle([290, 1800, 790, 1960], fill=(200, 200, 200))
  draw.text((290 + 110, 1800 + 40), "CANCEL", fill=(20, 20, 20), font=font)
  import numpy as np  # pylint: disable=import-outside-toplevel
  return elements, np.asarray(image), save_box


def check_model(cfg: config_lib.AgentConfig) -> None:
  import requests  # pylint: disable=import-outside-toplevel

  if cfg.backend == "ollama":
    base = cfg.base_url.rstrip("/")
    try:
      version = requests.get(f"{base}/api/version", timeout=10).json().get("version", "?")
      report(OK, "Ollama server", f"version {version} at {base}")
      tags = requests.get(f"{base}/api/tags", timeout=10).json().get("models", [])
      names = [m.get("name") for m in tags]
      if cfg.model in names:
        report(OK, "model", f"{cfg.model} is pulled")
      else:
        report(FAIL, "model", f"{cfg.model} is not pulled. Run: ollama pull"
               f" {cfg.model}  (available: {', '.join(names) or 'none'})")
        return
    except Exception as error:  # pylint: disable=broad-exception-caught
      report(FAIL, "Ollama server", f"not reachable at {base} ({error})."
             " Start it with: ollama serve")
      return
    if cfg.model.startswith("qwen3-vl") and "instruct" not in cfg.model:
      report(WARN, "model variant", "qwen3-vl tags without '-instruct' are the"
             " thinking build: slower, and thinking cannot be switched off."
             " Prefer qwen3-vl:4b-instruct")

  try:
    client = model_lib.make_client(cfg)
  except Exception as error:  # pylint: disable=broad-exception-caught
    report(FAIL, "model client", str(error))
    return
  info = client.describe()
  if info.get("quantization"):
    report(OK, "model identity",
           f"{info.get('parameter_size')} {info.get('quantization')}"
           f" digest {info.get('digest', '?')}")

  elements, pixels, save_box = _sample_screen()
  screen = (1080, 2400)
  views = observation.build_views(elements, screen)
  goal = "Save the new contact."

  def ask(grounding, tree_text, image_b64, image_size):
    messages = [
        {"role": "system", "content": prompts.system_prompt(
            grounding, cfg.allowed_apps, cfg.coordinate_space, False)},
        prompts.user_message(
            goal, "No actions yet.", tree_text, image_b64, image_size,
            state_size_hint=cfg.coordinate_space == "image_pixels"),
    ]
    reply = client.chat(messages, actions.action_schema(grounding, cfg.allowed_apps, False))
    action = actions.parse_action(reply.text, grounding)
    resolved = actions.resolve_action(
        action, views, screen, grounding, cfg.coordinate_space, image_size)
    return reply, resolved

  # 1. Tree + index: is the output valid, and does it pick the right element?
  try:
    reply, resolved = ask("index", observation.render_tree(views, cfg.max_elements), None, None)
    right = resolved.target is not None and resolved.target.text == "SAVE"
    report(OK if right else WARN, "tree prompt",
           f"{resolved.description} in {reply.latency_s:.1f}s,"
           f" {reply.prompt_tokens} prompt tokens"
           + ("" if right else "  (expected a click on SAVE)"))
  except actions.ActionError as error:
    report(FAIL, "tree prompt", f"invalid reply: {error}")
  except Exception as error:  # pylint: disable=broad-exception-caught
    report(FAIL, "tree prompt", f"{type(error).__name__}: {error}")

  # 2. Screenshot + coordinates: does the tap land inside the button?
  try:
    image_b64, image_size = observation.encode_screenshot(pixels, cfg.image_max_side)
    reply, resolved = ask("coordinate", None, image_b64, image_size)
    if resolved.tap_xy is None:
      report(WARN, "screenshot prompt",
             f"{resolved.description} (expected a click) in {reply.latency_s:.1f}s")
    else:
      x, y = resolved.tap_xy
      inside = save_box[0] <= x <= save_box[2] and save_box[1] <= y <= save_box[3]
      report(OK if inside else WARN, "screenshot prompt",
             f"tap at ({x}, {y}) is {'inside' if inside else 'OUTSIDE'} the SAVE"
             f" button {save_box} in {reply.latency_s:.1f}s,"
             f" {reply.prompt_tokens} prompt tokens")
      if not inside:
        print("       Pointing by coordinates is unreliable with this model"
              " build. That is the `grounding` failure class; index mode"
              " avoids it.")
  except actions.ActionError as error:
    report(FAIL, "screenshot prompt", f"invalid reply: {error}")
  except Exception as error:  # pylint: disable=broad-exception-caught
    report(FAIL, "screenshot prompt", f"{type(error).__name__}: {error}")


def main() -> int:
  parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
  parser.add_argument("--config", default=str(REPO_ROOT / "configs" / "v3_full.json"))
  parser.add_argument("--model", default="")
  parser.add_argument("--adb_path", default="")
  parser.add_argument("--console_port", type=int, default=5554)
  parser.add_argument("--skip_model", action="store_true")
  parser.add_argument("--skip_device", action="store_true")
  args = parser.parse_args()
  cfg = config_lib.AgentConfig.from_file(args.config)
  if args.model:
    cfg.model = args.model

  check_python()
  check_android_world()
  check_tools()
  if not args.skip_device:
    check_device(args.adb_path, args.console_port)
  if not args.skip_model:
    check_model(cfg)
  print()
  if _problems:
    print(f"{_problems} problem(s) must be fixed before running the evaluation.")
    return 1
  if _needs_app_setup:
    print("Almost ready. Install the AndroidWorld apps once:\n"
          "  python run_eval.py --config configs/v2_index.json --tasks"
          " ContactsAddContact --runs 1 --perform_emulator_setup --out runs_setup")
  else:
    print("Ready. Next: python run_eval.py --config configs/v1_baseline.json")
  return 0


if __name__ == "__main__":
  sys.exit(main())
