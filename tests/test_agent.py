"""The agent end to end, on a simulated phone with a scripted model.

Needs AndroidWorld installed (the agent subclasses its base class and emits
its JSONAction objects).
"""

import json

import pytest

pytest.importorskip("android_world")

from android_world import episode_runner  # noqa: E402
from android_world.env import json_action  # noqa: E402

from gui_agent import agent as agent_lib  # noqa: E402
from gui_agent import config as config_lib  # noqa: E402
from gui_agent import trajectory as trajectory_lib  # noqa: E402
from tests import fakes  # noqa: E402

GOAL = "Create a new contact for Nikola Fernandez. Their number is +11417776317."

HOME = [fakes.el("Phone", (100, 2000, 300, 2200), clickable=True, package="com.google.android.apps.nexuslauncher")]
LIST = [
    fakes.el("Contacts", (0, 100, 1080, 200), package="com.google.android.contacts"),
    fakes.el("", (860, 2100, 1020, 2260), desc="Create contact",
             cls="android.widget.ImageButton", clickable=True, package="com.google.android.contacts"),
]
FORM = [
    fakes.el("Create contact", (0, 100, 1080, 200), package="com.google.android.contacts"),
    fakes.el("Save", (860, 100, 1040, 200), cls="android.widget.Button",
             clickable=True, package="com.google.android.contacts"),
    fakes.el("", (100, 400, 980, 520), hint="First name",
             cls="android.widget.EditText", editable=True, package="com.google.android.contacts"),
    fakes.el("", (100, 700, 980, 820), hint="Phone",
             cls="android.widget.EditText", editable=True, package="com.google.android.contacts"),
]
FORM_FILLED = FORM[:2] + [
    fakes.el("Nikola Fernandez", (100, 400, 980, 520), hint="First name",
             cls="android.widget.EditText", editable=True, package="com.google.android.contacts"),
    fakes.el("+11417776317", (100, 700, 980, 820), hint="Phone",
             cls="android.widget.EditText", editable=True, package="com.google.android.contacts"),
]
SAVED = [
    fakes.el("Nikola Fernandez", (0, 300, 1080, 420), package="com.google.android.contacts"),
    fakes.el("+11417776317", (0, 600, 1080, 700), package="com.google.android.contacts"),
]
SCREENS = {"home": HOME, "list": LIST, "form": FORM, "filled": FORM_FILLED, "saved": SAVED}


def contacts_app(phone, action):
  """Transition rules of the simulated Contacts app."""
  kind = action.action_type
  if kind == "open_app" and action.app_name == "contacts":
    phone.current = "list"
  elif phone.current == "list" and kind == "click" and (action.x, action.y) == (940, 2180):
    phone.current = "form"
  elif phone.current == "form" and kind == "input_text" and "+1" in action.text:
    phone.current = "filled"
  elif phone.current == "filled" and kind == "click" and (action.x, action.y) == (950, 150):
    phone.current = "saved"


def reply(**fields):
  return json.dumps(fields)


def make_agent(replies, on_action=contacts_app, start="home", trajectory=None, **overrides):
  settings = dict(
      name="test", observation="tree", grounding="index",
      wait_for_stable=False, transition_pause_s=0.0,
      screen_change_hint=True, loop_guard=True, status_bar=True,
      verify_before_done=False,
  )
  settings.update(overrides)
  cfg = config_lib.AgentConfig(**settings)
  phone = fakes.FakePhone(SCREENS, start, on_action)
  model = fakes.ScriptedModel(replies)
  agent = agent_lib.GuiAgent(phone, cfg, model, trajectory)
  agent.reset(go_home=True)
  return agent, phone, model


HAPPY_PATH = [
    reply(thought="open contacts", action_type="open_app", app_name="contacts"),
    reply(thought="add", action_type="click", index=1),
    reply(thought="name", action_type="input_text", index=2, text="Nikola Fernandez"),
    reply(thought="number", action_type="input_text", index=3, text="+11417776317"),
    reply(thought="save", action_type="click", index=1),
    reply(thought="saved", action_type="status", goal_status="complete"),
]


def test_happy_path_emits_grounded_androidworld_actions():
  agent, phone, model = make_agent(HAPPY_PATH)
  results = [agent.step(GOAL) for _ in range(6)]
  assert [r.done for r in results] == [False] * 5 + [True]
  assert agent.stop_reason == agent_lib.STOP_MODEL_DONE
  assert phone.current == "saved"
  assert all(isinstance(a, json_action.JSONAction) for a in phone.executed)
  kinds = [a.action_type for a in phone.executed]
  assert kinds == ["open_app", "click", "input_text", "input_text", "click"]
  # Index 1 on the list screen was resolved by OUR code to the button centre.
  assert (phone.executed[1].x, phone.executed[1].y) == (940, 2180)
  assert phone.executed[1].index is None
  assert phone.executed[3].text == "+11417776317"
  assert model.remaining == 0


def test_context_stays_flat_only_latest_screen_and_one_line_history():
  agent, _, model = make_agent(HAPPY_PATH)
  for _ in range(6):
    agent.step(GOAL)
  last_user = model.calls[-1]["messages"][1]["content"]
  # History is one code-written line per step, with the observed effect.
  assert "1. open_app contacts -> screen changed, now in com.google.android.contacts" in last_user
  assert '5. click [1] Button "Save" -> screen changed' in last_user
  # Old screens are gone: the form's element lines are not in the last prompt.
  assert 'hint="First name"' not in last_user
  assert 'hint="First name"' in model.calls[2]["messages"][1]["content"]
  # The status bar is the last block before the closing instruction.
  assert last_user.index("STATUS:") > last_user.index("CURRENT SCREEN:")
  assert "step: 6 of 20" in last_user
  # Every call has exactly system + user: the conversation never grows.
  assert all(len(c["messages"]) == 2 for c in model.calls)
  assert all("images" not in c["messages"][1] for c in model.calls)


def test_step_limit_is_enforced_in_code():
  waits = [reply(thought="wait", action_type="wait")] * 10
  agent, phone, model = make_agent(waits, max_steps=3, loop_guard=False)
  results = [agent.step(GOAL) for _ in range(8)]
  assert len(phone.executed) == 3  # nothing reaches the device after step 3
  assert len(model.calls) == 3  # and the model is not even asked
  assert not any(r.done for r in results)  # out of steps is never "done"
  assert agent.stop_reason == agent_lib.STOP_STEP_LIMIT
  assert agent.halted


def test_task_budget_lowers_the_limit():
  waits = [reply(thought="wait", action_type="wait")] * 10
  agent, phone, _ = make_agent(waits, max_steps=20, loop_guard=False)
  agent.set_max_steps(2)
  for _ in range(5):
    agent.step(GOAL)
  assert len(phone.executed) == 2


def test_payment_action_never_reaches_the_device():
  shop = {"shop": [
      fakes.el("Buy now", (100, 1000, 980, 1120), cls="android.widget.Button", clickable=True),
      fakes.el("Details", (100, 1300, 980, 1420), cls="android.widget.Button", clickable=True),
      fakes.el("Price: 9.99", (100, 600, 980, 700)),
  ]}
  phone = fakes.FakePhone(shop, "shop")
  model = fakes.ScriptedModel([
      reply(thought="buy it", action_type="click", index=0),
      reply(thought="ok, details", action_type="click", index=1),
  ])
  cfg = config_lib.AgentConfig(wait_for_stable=False, transition_pause_s=0.0, verify_before_done=False)
  agent = agent_lib.GuiAgent(phone, cfg, model)
  agent.reset()
  first = agent.step("Order the headphones.")
  assert phone.executed == []  # blocked before execution
  assert first.data["outcome"] == "blocked"
  assert agent.stats["blocked"] == {"payment_ban": 1}
  agent.step("Order the headphones.")
  assert len(phone.executed) == 1 and phone.executed[0].y == 1360
  # The model was told why, in the history of the next prompt.
  assert "BLOCKED by the payment guardrail" in model.calls[1]["messages"][1]["content"]


def test_payment_ban_also_covers_coordinate_taps():
  shop = {"shop": [
      fakes.el("Buy now", (100, 1000, 980, 1120), cls="android.widget.Button", clickable=True),
      fakes.el("Details", (100, 1300, 980, 1420), cls="android.widget.Button", clickable=True),
      fakes.el("Price", (100, 600, 980, 700)),
  ]}
  phone = fakes.FakePhone(shop, "shop")
  model = fakes.ScriptedModel([reply(thought="buy", action_type="click", x=500, y=440)])
  cfg = config_lib.AgentConfig(
      observation="screenshot", grounding="coordinate", wait_for_stable=False,
      transition_pause_s=0.0, verify_before_done=False,
  )
  agent = agent_lib.GuiAgent(phone, cfg, model)
  agent.reset()
  agent.step("Order the headphones.")
  assert phone.executed == []
  # In pixel mode the model gets the image, not the tree.
  user = model.calls[0]["messages"][1]
  assert "images" in user and "Buy now" not in user["content"]


def test_app_not_on_the_allow_list_is_blocked():
  agent, phone, model = make_agent([
      reply(thought="sms", action_type="open_app", app_name="Messages"),
      reply(thought="ok", action_type="open_app", app_name="contacts"),
  ])
  agent.step(GOAL)
  assert phone.executed == []
  assert agent.stats["blocked"] == {"app_allow_list": 1}
  agent.step(GOAL)
  assert phone.executed[0].app_name == "contacts"


def test_loop_guard_blocks_then_aborts():
  taps = [reply(thought="tap", action_type="click", index=0)] * 10
  dead = {"dead": [
      fakes.el("Label", (0, 0, 500, 100)),
      fakes.el("Other", (0, 200, 500, 300), clickable=True),
      fakes.el("More", (0, 400, 500, 500), clickable=True),
  ]}
  phone = fakes.FakePhone(dead, "dead")
  cfg = config_lib.AgentConfig(wait_for_stable=False, transition_pause_s=0.0,
                               verify_before_done=False, max_loop_blocks=2)
  agent = agent_lib.GuiAgent(phone, cfg, fakes.ScriptedModel(taps))
  agent.reset()
  outcomes = [agent.step("x").data["outcome"] for _ in range(4)]
  assert outcomes == ["executed", "executed", "blocked", "blocked"]
  assert len(phone.executed) == 2
  assert agent.stop_reason == agent_lib.STOP_LOOP_ABORT
  assert agent.stats["no_effect_actions"] == 2


def test_invalid_reply_is_retried_with_the_error_message():
  agent, phone, model = make_agent([
      "I think I should open the contacts app.",
      reply(thought="open", action_type="open_app", app_name="contacts"),
  ])
  result = agent.step(GOAL)
  assert result.data["outcome"] == "executed"
  assert len(phone.executed) == 1
  retry = model.calls[1]["messages"]
  assert len(retry) == 4 and retry[2]["role"] == "assistant"
  assert "could not be used" in retry[3]["content"]
  assert agent.stats["invalid_replies"] == 1


def test_step_is_spent_without_action_when_every_retry_is_invalid():
  agent, phone, _ = make_agent(["nope", "still nope", "nope again"], parse_retries=2)
  result = agent.step(GOAL)
  assert result.done is False and result.data["outcome"] == "invalid_reply"
  assert phone.executed == []
  assert agent.stats["steps"] == 1


def test_check_step_can_veto_a_premature_done():
  agent, _, model = make_agent(
      [
          reply(thought="done already", action_type="status", goal_status="complete"),
          reply(evidence="home screen, no contact", achieved=False, missing="contact was not created"),
          reply(thought="open", action_type="open_app", app_name="contacts"),
      ],
      verify_before_done=True,
  )
  first = agent.step(GOAL)
  assert first.done is False and first.data["outcome"] == "done_rejected"
  assert not agent.halted
  agent.step(GOAL)
  assert "REJECTED by the check step" in model.calls[2]["messages"][1]["content"]
  assert "contact was not created" in model.calls[2]["messages"][1]["content"]


def test_check_step_accepts_a_real_done_and_cannot_veto_forever():
  done = reply(thought="done", action_type="status", goal_status="complete")
  no = reply(evidence="nothing", achieved=False, missing="everything")
  agent, _, _ = make_agent(
      [done, no, done, no, done], verify_before_done=True, max_done_rejections=2
  )
  assert agent.step(GOAL).done is False
  assert agent.step(GOAL).done is False
  # Third claim: the veto budget is used up, the agent's decision stands.
  assert agent.step(GOAL).done is True

  yes = reply(evidence="contact visible", achieved=True, missing="")
  agent, _, _ = make_agent([done, yes], verify_before_done=True, start="saved")
  assert agent.step(GOAL).done is True


def test_notes_are_kept_by_code_and_shown_again():
  agent, _, model = make_agent([
      reply(thought="remember the number", action_type="wait", note="number is +11417776317"),
      reply(thought="again", action_type="open_app", app_name="contacts"),
  ])
  agent.step(GOAL)
  agent.step(GOAL)
  assert "notes: number is +11417776317" in model.calls[1]["messages"][1]["content"]


def test_pixel_fallback_when_the_tree_is_empty():
  canvas = {"canvas": []}  # a game or WebView: nothing in the accessibility tree
  phone = fakes.FakePhone(canvas, "canvas")
  model = fakes.ScriptedModel([reply(thought="tap", action_type="click", x=500, y=500)])
  cfg = config_lib.AgentConfig(wait_for_stable=False, transition_pause_s=0.0, verify_before_done=False)
  agent = agent_lib.GuiAgent(phone, cfg, model)
  agent.reset()
  agent.step("Tap the middle.")
  assert (phone.executed[0].x, phone.executed[0].y) == (540, 1200)
  assert "images" in model.calls[0]["messages"][1]
  assert "x" in model.calls[0]["schema"]["properties"]
  assert agent.stats["pixel_fallback_steps"] == 1


def test_device_error_is_reported_to_the_model_not_raised():
  def broken(phone, action):
    raise ValueError("Invalid element index")
  agent, _, model = make_agent(
      [reply(thought="a", action_type="wait"), reply(thought="b", action_type="wait")],
      on_action=broken, loop_guard=False,
  )
  result = agent.step(GOAL)
  assert result.data["outcome"] == "action_error"
  agent.step(GOAL)
  assert "FAILED (ValueError: Invalid element index)" in model.calls[1]["messages"][1]["content"]


def test_runs_inside_androidworlds_own_episode_runner():
  agent, phone, _ = make_agent(HAPPY_PATH)
  result = episode_runner.run_episode(
      goal=GOAL, agent=agent, max_n_steps=12, start_on_home_screen=True,
      print_fn=lambda _: None,
  )
  assert result.done is True
  assert phone.current == "saved"
  assert len(result.step_data["step_number"]) == 6


def test_trajectory_is_written_step_by_step(tmp_path):
  logger = trajectory_lib.TrajectoryLogger(tmp_path)
  agent, _, _ = make_agent(HAPPY_PATH[:2], trajectory=logger)
  agent.reset()
  agent.trajectory = logger
  agent.step(GOAL)
  records = trajectory_lib.read_trajectory(tmp_path)
  assert len(records) == 1  # on disk after the first step, not at the end
  agent.step(GOAL)
  records = trajectory_lib.read_trajectory(tmp_path)
  assert len(records) == 2
  second = records[1]
  assert second["resolved"]["tap_xy"] == [940, 2180]
  assert second["resolved"]["target"].startswith("[1] ImageButton")
  assert second["effect"]["screen_changed"] is True
  assert second["observation"]["tree"].startswith("[0] TextView")
  assert second["model"]["attempts"][0]["raw"]
  assert (tmp_path / second["screenshot"]).exists()


def test_real_androidworld_ui_elements_are_read_correctly():
  from android_world.env import representation_utils as ru
  from gui_agent import observation

  elements = [
      # BoundingBox argument order is (x_min, x_max, y_min, y_max).
      ru.UIElement(text="Save", class_name="android.widget.Button",
                   bbox_pixels=ru.BoundingBox(800, 1000, 300, 400),
                   is_visible=True, is_clickable=True, package_name="com.x"),
      ru.UIElement(text="hidden", bbox_pixels=ru.BoundingBox(0, 10, 0, 10), is_visible=False),
      ru.UIElement(text="off screen", bbox_pixels=ru.BoundingBox(2000, 2100, 0, 10), is_visible=True),
      ru.UIElement(hint_text="Name", class_name="android.widget.EditText",
                   resource_name="com.x:id/name_field",
                   bbox_pixels=ru.BoundingBox(0, 1080, 500, 600),
                   is_visible=True, is_editable=True, package_name="com.x"),
  ]
  views = observation.build_views(elements, fakes.SCREEN)
  assert [v.index for v in views] == [0, 3]  # original indices are kept
  assert views[0].center == (900, 350)
  assert views[0].label() == '[0] Button "Save" (clickable)'
  assert views[1].label() == '[3] EditText hint="Name" id=name_field (editable)'
  assert observation.foreground_package(views) == "com.x"


def test_works_with_androidworlds_own_fake_environment():
  from android_world.utils import test_utils

  env = test_utils.FakeAsyncEnv()
  model = fakes.ScriptedModel([
      reply(thought="tap", action_type="click", x=500, y=500),
      reply(thought="done", action_type="status", goal_status="complete"),
  ])
  cfg = config_lib.AgentConfig(wait_for_stable=False, transition_pause_s=0.0,
                               verify_before_done=False,
                               extra_scope_packages=("MockActivity",))
  agent = agent_lib.GuiAgent(env, cfg, model)
  result = episode_runner.run_episode(
      goal="Tap the middle.", agent=agent, max_n_steps=5, print_fn=lambda _: None)
  assert result.done is True
  assert agent.stats["pixel_fallback_steps"] == 2  # this fake exposes no tree


def _fresh_agent(screens, start, replies, **overrides):
  settings = dict(wait_for_stable=False, transition_pause_s=0.0, verify_before_done=False)
  settings.update(overrides)
  phone = fakes.FakePhone(screens, start)
  model = fakes.ScriptedModel(replies)
  agent = agent_lib.GuiAgent(phone, config_lib.AgentConfig(**settings), model)
  agent.reset()
  return agent, phone, model


def test_outside_its_apps_the_agent_can_only_leave():
  browser = {"web": [
      fakes.el("Sign in", (100, 1000, 980, 1120), cls="android.widget.Button",
               clickable=True, package="com.android.chrome"),
      fakes.el("", (100, 400, 980, 520), hint="Search or type URL",
               cls="android.widget.EditText", editable=True, package="com.android.chrome"),
  ]}
  agent, phone, model = _fresh_agent(browser, "web", [
      reply(thought="sign in", action_type="click", index=0),
      reply(thought="type", action_type="input_text", index=1, text="shop.example"),
      reply(thought="enter", action_type="keyboard_enter"),
      reply(thought="leave", action_type="navigate_back"),
  ])
  for _ in range(4):
    agent.step("Look something up.")
  assert [a.action_type for a in phone.executed] == ["navigate_back"]
  assert agent.stats["blocked"] == {"app_scope": 3}
  assert "outside the apps you may operate" in model.calls[1]["messages"][1]["content"]


def test_home_screen_icons_are_never_tapped():
  agent, phone, _ = make_agent([
      reply(thought="tap the phone icon", action_type="click", index=0),
      reply(thought="ok, by name", action_type="open_app", app_name="contacts"),
  ])
  agent.step(GOAL)
  assert phone.executed == [] and agent.stats["blocked"] == {"home_screen": 1}
  agent.step(GOAL)
  assert phone.executed[0].action_type == "open_app"


def test_a_checkout_form_receives_no_input_at_all():
  checkout = {"pay": [
      fakes.el("", (100, 400, 980, 520), hint="Card no.", cls="android.widget.EditText",
               editable=True, focused=True),
      fakes.el("", (100, 600, 500, 720), hint="MM/YY", cls="android.widget.EditText", editable=True),
      fakes.el("", (580, 600, 980, 720), res="com.shop:id/security_code",
               cls="android.widget.EditText", editable=True),
      fakes.el("Pay €10", (100, 1000, 980, 1120), cls="android.widget.Button", clickable=True),
  ]}
  agent, phone, _ = _fresh_agent(checkout, "pay", [
      reply(thought="card", action_type="input_text", index=0, text="4111–1111–1111–1111"),
      reply(thought="focused field", action_type="input_text", text="12/29"),
      reply(thought="cvc", action_type="input_text", index=2, text="123"),
      reply(thought="submit", action_type="keyboard_enter"),
      reply(thought="pay", action_type="click", index=3),
      reply(thought="pay by pixel", action_type="long_press", index=3),
  ], loop_guard=False)
  for _ in range(6):
    agent.step("Pay for the order.")
  assert phone.executed == []
  assert agent.stats["blocked"] == {"payment_ban": 6}


def test_keyboard_keys_are_hidden_but_the_keyboard_counts_as_a_change():
  from gui_agent import observation

  field = fakes.el("", (100, 400, 980, 520), hint="Name", cls="android.widget.EditText", editable=True)
  keys = [fakes.el(k, (100 * i, 1800, 100 * i + 90, 1900), clickable=True,
                   package="com.google.android.inputmethod.latin") for i, k in enumerate("qwertyuiop")]
  closed = observation.build_views([field], fakes.SCREEN)
  opened = observation.build_views([field] + keys, fakes.SCREEN)
  assert [v.index for v in opened] == [0]  # keys are not shown to the model
  assert observation.keyboard_visible([field] + keys)
  assert observation.fingerprint(closed, False) != observation.fingerprint(opened, True)
  assert "keyboard is open" in observation.render_tree(opened, 70, True)
  assert observation.foreground_package(opened) == "net.gsantner.markor"


def test_an_empty_field_is_not_shown_as_filled_with_its_hint():
  from gui_agent import observation

  empty = fakes.el("First name", (100, 400, 980, 520), hint="First name",
                   cls="android.widget.EditText", editable=True)
  filled = fakes.el("Anna", (100, 600, 980, 720), hint="First name",
                    cls="android.widget.EditText", editable=True)
  views = observation.build_views([empty, filled], fakes.SCREEN)
  assert views[0].label() == '[0] EditText hint="First name" (editable)'
  assert views[1].label() == '[1] EditText "Anna" hint="First name" (editable)'


def test_malformed_json_is_an_invalid_reply_not_a_crash():
  agent, phone, _ = make_agent([
      '{{"action_type": "click", "index": 0}}',  # double braces
      "[" * 5000 + "{" * 5000,  # absurd nesting
      '<think>maybe {"action_type": "navigate_home"} or',  # truncated reasoning
      "{'action_type': }",
  ], parse_retries=2)
  result = agent.step(GOAL)
  # The first reply still contains one well-formed object and is used
  # (and then blocked, because it is a tap on the home screen).
  assert result.data["outcome"] == "blocked"
  result = agent.step(GOAL)
  assert result.data["outcome"] == "invalid_reply"
  assert agent.stats["invalid_replies"] == 3
  assert phone.executed == []


def test_no_action_on_a_stale_screen_if_another_app_came_to_the_front():
  screens = {
      "note": [fakes.el("OK", (100, 1000, 980, 1120), cls="android.widget.Button", clickable=True)],
      "store": [fakes.el("Install", (100, 1000, 980, 1120), cls="android.widget.Button",
                         clickable=True, package="com.android.vending")],
  }
  phone = fakes.FakePhone(screens, "note")

  class SlowModel(fakes.ScriptedModel):
    def chat(self, messages, schema=None):
      phone.current = "store"  # a store page opens while the model is thinking
      return super().chat(messages, schema)

  model = SlowModel([
      reply(thought="tap OK", action_type="click", index=0),
      reply(thought="leave", action_type="navigate_home"),
  ])
  cfg = config_lib.AgentConfig(wait_for_stable=False, transition_pause_s=0.0, verify_before_done=False)
  agent = agent_lib.GuiAgent(phone, cfg, model)
  agent.reset()
  phone.current = "note"
  result = agent.step("Confirm the dialog.")
  assert result.data["outcome"] == "stale_screen"
  assert phone.executed == []  # the tap would have hit "Install"
  agent.step("Confirm the dialog.")
  assert [a.action_type for a in phone.executed] == ["navigate_home"]


def test_tapping_a_text_field_or_going_home_twice_is_not_a_failed_action():
  agent, phone, model = make_agent([
      reply(thought="home", action_type="navigate_home"),
      reply(thought="open", action_type="open_app", app_name="contacts"),
      reply(thought="add", action_type="click", index=1),
      reply(thought="focus", action_type="click", index=2),
  ], loop_guard=False)
  for _ in range(4):
    agent.step(GOAL)
  assert agent.stats["no_effect_actions"] == 0
  history = model.calls[-1]["messages"][1]["content"]
  assert "navigate_home -> already on the home screen" in history
  assert agent.last_history_line.endswith("text field selected")
