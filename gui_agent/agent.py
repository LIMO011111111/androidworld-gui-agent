"""The agent: one class, one `step()` method.

`step(goal)` reads the screen and the task, chooses one action, and says
whether the agent is done. That is the whole contract of the project and of
AndroidWorld's `EnvironmentInteractingAgent`.

The method is a fixed pipeline (process-driven, not a pile of rules), so a
failed run can be pinned to a stage:

    0  budget     step limit, checked before anything else            [code]
    1  observe    screen -> element list / screenshot / fingerprint   [code]
    2  decide     prompt -> model -> one JSON action                  [model]
    3  validate   parse, retry on malformed output                    [code]
    4  ground     index -> exact pixel (or rescale coordinates)       [code]
    5  check      done-verification, payment ban, app allow-list,
                  loop detection                                      [code]
    6  act        execute on the device                               [code]
    7  feedback   did the screen change? write one history line       [code]

Only stage 2 is the model. Everything that has to hold is in the stages
around it.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Optional

from android_world.agents import base_agent
from android_world.env import interface
from android_world.env import json_action

from gui_agent import actions
from gui_agent import config as config_lib
from gui_agent import goal_values
from gui_agent import guardrails
from gui_agent import memory as memory_lib
from gui_agent import model as model_lib
from gui_agent import observation as obs_lib
from gui_agent import prompts
from gui_agent import trajectory as trajectory_lib

# Why an episode ended. Only the first two mean "the agent says it is done".
STOP_MODEL_DONE = "model_done"
STOP_MODEL_INFEASIBLE = "model_infeasible"
STOP_STEP_LIMIT = "step_limit"
STOP_LOOP_ABORT = "loop_abort"

# Leaving, opening an allowed app or waiting is safe on any screen.
_ALWAYS_SAFE = (
    actions.NAVIGATE_BACK,
    actions.NAVIGATE_HOME,
    actions.OPEN_APP,
    actions.WAIT,
)

# Button names that commit the work of a form or editor.
_COMMIT_BUTTONS = frozenset({"save", "send", "sms", "ok", "done", "create", "add"})

# Actions that should visibly change the screen. If they do not, we look twice.
_EXPECT_CHANGE = (
    actions.CLICK,
    actions.LONG_PRESS,
    actions.INPUT_TEXT,
    actions.OPEN_APP,
    actions.NAVIGATE_BACK,
    actions.NAVIGATE_HOME,
)


class _Observation:
  """Everything derived from one device state."""

  def __init__(self, state: interface.State, screen_size: tuple[int, int],
               cfg: config_lib.AgentConfig, resumed_package: str = ""):
    self.state = state
    self.screen_size = screen_size
    self.views = obs_lib.build_views(
        state.ui_elements, screen_size, cfg.drop_status_bar
    )
    self.resumed_package = resumed_package
    self.keyboard = obs_lib.keyboard_visible(state.ui_elements)
    self.fingerprint = obs_lib.fingerprint(self.views, self.keyboard)
    # The resumed activity reported by the device is the ground truth for
    # "which app is in front". The element majority is only the fallback.
    self.package = resumed_package or obs_lib.foreground_package(self.views)
    self.tree_text = obs_lib.render_tree(
        self.views, cfg.max_elements, self.keyboard
    )


class GuiAgent(base_agent.EnvironmentInteractingAgent):
  """Vision-language GUI agent for AndroidWorld with a code-level harness."""

  def __init__(
      self,
      env: interface.AsyncEnv,
      config: Optional[config_lib.AgentConfig] = None,
      model: Optional[model_lib.ModelClient] = None,
      trajectory: Optional[trajectory_lib.TrajectoryLogger] = None,
      skills_dir: Optional[str | Path] = None,
  ):
    self.config = config or config_lib.AgentConfig()
    super().__init__(
        env,
        name=self.config.name,
        # None = AndroidWorld's "auto" mode: poll until the UI stops changing.
        transition_pause=(
            None if self.config.wait_for_stable else self.config.transition_pause_s
        ),
    )
    self.model = model or model_lib.make_client(self.config)
    self.trajectory = trajectory
    self._skills_dir = Path(skills_dir) if skills_dir else None

    # Guardrails. Step limit, payment ban, app scope and app allow-list have
    # no off switch.
    self._budget = guardrails.StepBudget(self.config.max_steps)
    self._payment_guard = guardrails.PaymentGuard()
    self._app_scope = guardrails.AppScope(self.config.scope_packages())
    self._app_allow_list = guardrails.AppAllowList(self.config.allowed_apps)
    self._loop_detector = guardrails.LoopDetector()

    self._memory = memory_lib.EpisodeMemory()
    self.clear_episode_state()

  # --- episode lifecycle ------------------------------------------------------

  def clear_episode_state(self) -> None:
    """Forgets everything about the previous episode."""
    self._memory.reset()
    self._loop_detector.reset()
    self._budget = guardrails.StepBudget(self.config.max_steps)
    self._pending: Optional[_Observation] = None  # screen after the last action
    self._last_effect: Optional[str] = None
    self._done_rejections = 0
    self._goal_rejections = 0
    self._goal_tracker: Optional[goal_values.GoalTracker] = None
    self.stop_reason: Optional[str] = None
    self.stats: dict[str, Any] = {
        "steps": 0,
        "model_calls": 0,
        "model_seconds": 0.0,
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "invalid_replies": 0,
        "no_effect_actions": 0,
        "late_changes": 0,
        "taps_on_nothing": 0,
        "pixel_fallback_steps": 0,
        "blocked": {},
        "done_rejections": 0,
        "goal_value_rejections": 0,
        "prefilled_replaced": 0,
        "done_hints": 0,
        "action_errors": 0,
        "apps_opened": [],
        "packages_seen": [],
        "launcher_steps": 0,
        "stale_screens": 0,
        "typed_texts": [],
    }

  def reset(self, go_home: bool = False) -> None:
    """Starts a new episode."""
    super().reset(go_home)
    try:
      self.env.hide_automation_ui()
    except Exception:  # pylint: disable=broad-exception-caught
      pass
    self.clear_episode_state()

  def set_max_steps(self, max_steps: int) -> None:
    """The task budget can lower the step limit, never raise it."""
    super().set_max_steps(max_steps)
    self._budget.set_task_budget(max_steps)

  @property
  def halted(self) -> bool:
    """True once the episode is over, for whatever reason."""
    return self.stop_reason is not None

  @property
  def budget(self) -> int:
    return self._budget.budget

  @property
  def last_history_line(self) -> str:
    return self._memory.history[-1] if self._memory.history else ""

  # --- the one method ---------------------------------------------------------

  def step(self, goal: str) -> base_agent.AgentInteractionResult:
    """Reads the screen and the goal, performs one action, reports done.

    Returns `done=True` only when the model itself declares the task finished
    (and, if enabled, the check step agrees). Running out of steps is never
    reported as done.
    """
    # Stage 0 - step limit. No model call and no device action beyond it.
    if self.halted:
      return self._result(done=self._declared_done(), record={"halted": True})
    if self._budget.exhausted():
      self.stop_reason = STOP_STEP_LIMIT
      return self._result(done=False, record={"halted": True})

    cfg = self.config
    step_no = self._budget.consume()
    self.stats["steps"] = step_no
    record: dict[str, Any] = {
        "step": step_no,
        "budget": self._budget.budget,
        "time": trajectory_lib.now_iso(),
        "goal": goal,
    }

    # Stage 1 - observe.
    obs = self._pending or self._observe()
    self._pending = None
    if obs.package and obs.package not in self.stats["packages_seen"]:
      self.stats["packages_seen"].append(obs.package)
    if step_no > 1 and obs_lib.is_launcher_package(obs.package):
      self.stats["launcher_steps"] += 1

    grounding = cfg.grounding
    show_tree = cfg.observation in ("tree", "both")
    show_image = cfg.observation in ("screenshot", "both")
    if grounding == "index" and len(obs.views) < cfg.pixel_fallback_min_elements:
      # "Take the index route unless the tree is empty."
      grounding, show_tree, show_image = "coordinate", False, True
      record["pixel_fallback"] = True
      self.stats["pixel_fallback_steps"] += 1

    image_b64, image_size = None, None
    if show_image:
      image_b64, image_size = obs_lib.encode_screenshot(
          obs.state.pixels, cfg.image_max_side
      )
    status_text = None
    if cfg.status_bar:
      status_text = self._memory.render_status(
          step_no, self._budget.budget, obs.package, self._last_effect
      )
    if cfg.goal_tracker:
      tracker_text = self._tracker(goal).render(self.stats["typed_texts"])
      if tracker_text:
        status_text = f"{status_text}\n{tracker_text}" if status_text else tracker_text
    record["observation"] = {
        "mode": cfg.observation if not record.get("pixel_fallback") else "screenshot",
        "grounding": grounding,
        "package": obs.package,
        "screen_size": list(obs.screen_size),
        "elements": len(obs.views),
        "fingerprint": obs.fingerprint,
        "tree": obs.tree_text,
        "image_size": list(image_size) if image_size else None,
    }

    # Stage 2 + 3 - decide, validate, retry.
    with_notes = cfg.status_bar
    messages = [
        {
            "role": "system",
            "content": prompts.system_prompt(
                grounding, cfg.allowed_apps, cfg.coordinate_space, with_notes
            ),
        },
        prompts.user_message(
            goal=goal,
            history=self._memory.render_history(cfg.history_lines),
            tree_text=obs.tree_text if show_tree else None,
            image_b64=image_b64,
            image_size=image_size,
            state_size_hint=cfg.coordinate_space == "image_pixels",
            status=status_text,
            app_tips=self._app_tips(obs.package),
        ),
    ]
    schema = actions.action_schema(grounding, cfg.allowed_apps, with_notes)
    record["prompt"] = model_lib.redact_messages(messages)
    record["model"] = {"name": self.model.name, "attempts": []}

    resolved: Optional[actions.ResolvedAction] = None
    for _ in range(cfg.parse_retries + 1):
      try:
        reply = self.model.chat(messages, schema)
      except Exception as error:
        record["model"]["error"] = f"{type(error).__name__}: {error}"
        self._log(record, obs)
        raise
      self._count_model_call(reply)
      attempt = {
          "raw": reply.text,
          "latency_s": round(reply.latency_s, 2),
          "prompt_tokens": reply.prompt_tokens,
          "completion_tokens": reply.completion_tokens,
      }
      record["model"]["attempts"].append(attempt)
      try:
        action = actions.parse_action(reply.text, grounding)
        resolved = actions.resolve_action(
            action, obs.views, obs.screen_size, grounding,
            cfg.coordinate_space, image_size,
        )
        break
      except actions.ActionError as error:
        attempt["error"] = str(error)
        self.stats["invalid_replies"] += 1
        messages = messages + [
            {"role": "assistant", "content": reply.text or "(empty reply)"},
            {"role": "user", "content": prompts.RETRY_TEMPLATE.format(error=error)},
        ]

    if resolved is None:
      # The step is spent, nothing reaches the device.
      self._memory.add_step("(invalid reply)", "no action was executed")
      self._last_effect = "your reply was not a valid action; nothing happened"
      record["outcome"] = "invalid_reply"
      self._log(record, obs)
      return self._result(done=False, record=record)

    action = resolved.action
    record["thought"] = action.thought
    record["action"] = action.as_dict()
    record["resolved"] = {
        "description": resolved.description,
        "grounding": resolved.grounding,
        "tap_xy": list(resolved.tap_xy) if resolved.tap_xy else None,
        "target": resolved.target.label() if resolved.target else None,
    }
    if cfg.status_bar and action.note:
      self._memory.add_note(action.note)
    record["notes"] = list(self._memory.notes)

    # Stage 5a - the model says it is finished.
    if action.action_type == actions.STATUS:
      return self._handle_status(goal, obs, resolved, record)

    # Stage 5b - guardrails. Order: payment ban, app allow-list, app scope,
    # loop guard. The first block wins and names its rule in the log.
    verdict = self._payment_guard.check(
        resolved, obs.views, obs.package, self.stats["typed_texts"][-4:]
    )
    if verdict.allowed:
      verdict = self._app_allow_list.check(resolved)
    if verdict.allowed:
      verdict = self._app_scope.check(resolved, obs.package)
    if verdict.allowed and cfg.loop_guard:
      verdict = self._loop_detector.check(action.signature(), obs.fingerprint)
    if not verdict.allowed:
      self.stats["blocked"][verdict.rule] = self.stats["blocked"].get(verdict.rule, 0) + 1
      self._memory.add_step(resolved.description, verdict.message)
      self._last_effect = verdict.message
      record["guardrail"] = {"rule": verdict.rule, "message": verdict.message}
      record["outcome"] = "blocked"
      if (
          verdict.rule == guardrails.LoopDetector.RULE
          and self._loop_detector.blocks >= cfg.max_loop_blocks
      ):
        self.stop_reason = STOP_LOOP_ABORT
        record["stop_reason"] = self.stop_reason
      self._log(record, obs, resolved)
      return self._result(done=False, record=record)

    if (
        cfg.replace_prefilled_text
        and action.action_type == actions.INPUT_TEXT
        and resolved.target is not None
        and resolved.target.editable
        and resolved.target.text
        and resolved.target.text != resolved.target.hint
        # Not when the model is continuing its own text in that field.
        and not action.text.startswith(resolved.target.text)
        and resolved.target.text not in "".join(self.stats["typed_texts"])
    ):
      # The field already shows a value: replace it instead of appending.
      resolved.env_action["clear_text"] = True
      record["resolved"]["cleared_prefilled"] = resolved.target.text
      self.stats["prefilled_replaced"] += 1
    record["resolved"]["env_action"] = dict(resolved.env_action)

    # The guardrails judged the screen from before the model call, which can
    # be many seconds old. If a different app has come to the front in the
    # meantime, do not act on a stale picture: look again next step.
    if action.action_type not in _ALWAYS_SAFE and obs.resumed_package:
      now_in_front = self._resumed_package()
      if now_in_front and now_in_front != obs.resumed_package:
        message = (
            f"not executed: {now_in_front} came to the front while deciding."
            " Look at the new screen."
        )
        self._memory.add_step(resolved.description, message)
        self._last_effect = message
        self.stats["stale_screens"] += 1
        record["outcome"] = "stale_screen"
        self._log(record, obs, resolved)
        return self._result(done=False, record=record)

    # Stage 6 - act.
    if resolved.grounding == "coordinate" and resolved.target is None and obs.views:
      self.stats["taps_on_nothing"] += 1
    if action.action_type == actions.OPEN_APP:
      self.stats["apps_opened"].append(resolved.env_action.get("app_name"))
    if action.action_type == actions.INPUT_TEXT:
      self.stats["typed_texts"].append(action.text)
    error_text = None
    try:
      self.env.execute_action(json_action.JSONAction(**resolved.env_action))
    except Exception as error:  # pylint: disable=broad-exception-caught
      # A failed device call must not kill the episode; the model is told.
      error_text = f"{type(error).__name__}: {error}"
      self.stats["action_errors"] += 1

    # Stage 7 - feedback: wait, look again, compare.
    # Tapping a text field only moves the focus, and going home while already
    # home changes nothing. Neither is a failed action.
    focus_only = (
        action.action_type == actions.CLICK
        and resolved.target is not None
        and resolved.target.editable
    )
    already_home = action.action_type == actions.NAVIGATE_HOME and (
        obs_lib.is_launcher_package(obs.package)
    )
    expect_change = (
        action.action_type in _EXPECT_CHANGE and not focus_only and not already_home
    )
    after = self._observe()
    changed = after.fingerprint != obs.fingerprint
    late_change = False
    if (
        not changed
        and error_text is None
        and cfg.wait_for_stable
        and expect_change
    ):
      # The screen may simply not have finished loading (`too_early`). Look a
      # second time before telling the model that nothing happened.
      time.sleep(1.0)
      after = self._observe()
      changed = after.fingerprint != obs.fingerprint
      late_change = changed
      if late_change:
        self.stats["late_changes"] += 1
    self._pending = after
    if not changed and expect_change:
      self.stats["no_effect_actions"] += 1

    if error_text is not None:
      outcome = f"FAILED ({error_text})"
    elif not cfg.screen_change_hint:
      outcome = "executed"
    elif changed:
      outcome = "screen changed"
      if after.package and after.package != obs.package:
        outcome += f", now in {after.package}"
    elif action.action_type == actions.WAIT:
      outcome = "waited, screen is the same"
    elif focus_only:
      outcome = "text field selected"
    elif already_home:
      outcome = "already on the home screen"
    else:
      outcome = "screen did NOT change"
    if (
        cfg.done_hint
        and error_text is None
        and changed
        and self._is_commit_action(resolved)
    ):
      tracker = self._tracker(goal)
      typed = self.stats["typed_texts"]
      if tracker.values and typed and not tracker.missing_parts(typed):
        outcome += (
            ". All values from the goal are typed and you pressed a"
            " save/send button: if the goal is fully done, reply"
            ' status "complete" now instead of pressing it again'
        )
        self.stats["done_hints"] += 1
    self._memory.add_step(resolved.description, outcome)
    self._last_effect = f"{resolved.description} -> {outcome}"

    record["outcome"] = "executed" if error_text is None else "action_error"
    record["effect"] = {
        "screen_changed": changed,
        "late_change": late_change,
        "package_after": after.package,
        "fingerprint_after": after.fingerprint,
        "error": error_text,
    }
    record["history_line"] = self._memory.history[-1]
    self._log(record, obs, resolved)
    return self._result(done=False, record=record)

  # --- stages -----------------------------------------------------------------

  def _observe(self) -> _Observation:
    state = self.get_post_transition_state()
    try:
      width, height = self.env.logical_screen_size
    except Exception:  # pylint: disable=broad-exception-caught
      height, width = state.pixels.shape[:2]
    return _Observation(
        state, (int(width), int(height)), self.config, self._resumed_package()
    )

  def _resumed_package(self) -> str:
    """Package of the activity the device reports as resumed ("" if unknown)."""
    try:
      activity = self.env.foreground_activity_name
      return str(activity or "").split("/")[0].strip()
    except Exception:  # pylint: disable=broad-exception-caught
      return ""

  def _handle_status(
      self,
      goal: str,
      obs: _Observation,
      resolved: actions.ResolvedAction,
      record: dict[str, Any],
  ) -> base_agent.AgentInteractionResult:
    cfg = self.config
    action = resolved.action
    if (
        action.goal_status == actions.COMPLETE
        and cfg.goal_tracker
        and self._goal_rejections < cfg.max_done_rejections
    ):
      # Code-side check before `done` (V4): every literal value from the goal
      # must have been typed at least once. No model call, so it cannot be
      # fooled the way a same-size verifier model is.
      missing = self._tracker(goal).missing_parts(self.stats["typed_texts"])
      record["goal_values_missing"] = missing
      if missing:
        self._goal_rejections += 1
        self.stats["done_rejections"] += 1
        self.stats["goal_value_rejections"] += 1
        listed = ", ".join(f'"{m}"' for m in missing)
        message = (
            f"REJECTED by code, not finished yet: you never typed {listed}"
            " from the goal. Type it into the right field (and save) first."
        )
        self._memory.add_step("status complete", message)
        self._last_effect = message
        self._pending = obs  # nothing was executed, the screen is the same
        record["outcome"] = "done_rejected"
        self._log(record, obs)
        return self._result(done=False, record=record)
    if (
        action.goal_status == actions.COMPLETE
        and cfg.verify_before_done
        and self._done_rejections < cfg.max_done_rejections
    ):
      # A check step before `done` (fix for `false_done`): a second, separate
      # look at the final screen. At most `max_done_rejections` vetoes, so the
      # checker cannot keep the agent running forever.
      check = self._verify(goal, obs)
      record["done_check"] = check
      if check is not None and not check["achieved"]:
        self._done_rejections += 1
        self.stats["done_rejections"] += 1
        reason = check.get("missing") or check.get("evidence") or "no evidence"
        message = f"REJECTED by the check step, not finished yet: {reason}"
        self._memory.add_step("status complete", message)
        self._last_effect = message
        self._pending = obs  # nothing was executed, the screen is the same
        record["outcome"] = "done_rejected"
        self._log(record, obs)
        return self._result(done=False, record=record)

    self.stop_reason = (
        STOP_MODEL_DONE
        if action.goal_status == actions.COMPLETE
        else STOP_MODEL_INFEASIBLE
    )
    self._memory.add_step(resolved.description, "episode ended by the agent")
    record["outcome"] = "done"
    record["stop_reason"] = self.stop_reason
    self._log(record, obs)
    return self._result(done=True, record=record)

  @staticmethod
  def _is_commit_action(resolved: actions.ResolvedAction) -> bool:
    """A tap on a button that commits the work: Save, Send, SMS, OK, Done."""
    if resolved.action.action_type != actions.CLICK or resolved.target is None:
      return False
    name = (resolved.target.text or resolved.target.description or "").strip().lower()
    return name in _COMMIT_BUTTONS

  def _tracker(self, goal: str) -> goal_values.GoalTracker:
    if self._goal_tracker is None or self._goal_tracker.goal != goal:
      self._goal_tracker = goal_values.GoalTracker(goal)
    return self._goal_tracker

  def _verify(self, goal: str, obs: _Observation) -> Optional[dict[str, Any]]:
    """Asks for a strict yes/no on the current screen. None if it cannot tell."""
    cfg = self.config
    use_tree = cfg.observation in ("tree", "both") and bool(obs.views)
    image_b64 = None
    if not use_tree or cfg.observation == "both":
      image_b64, _ = obs_lib.encode_screenshot(obs.state.pixels, cfg.image_max_side)
    messages = [
        {"role": "system", "content": prompts.VERIFIER_SYSTEM_PROMPT},
        prompts.user_message(
            goal=goal,
            history=self._memory.render_history(cfg.history_lines),
            tree_text=obs.tree_text if use_tree else None,
            image_b64=image_b64,
            closing=prompts.VERIFIER_CLOSING,
        ),
    ]
    try:
      reply = self.model.chat(messages, actions.VERIFIER_SCHEMA)
      self._count_model_call(reply)
      data = actions.extract_json_object(reply.text)
    except Exception as error:  # pylint: disable=broad-exception-caught
      return {"achieved": True, "evidence": "", "missing": "",
              "error": f"check step failed, accepting done: {error}"}
    achieved = data.get("achieved")
    if isinstance(achieved, str):
      achieved = achieved.strip().lower() in ("true", "yes", "1")
    return {
        "achieved": bool(achieved),
        "evidence": str(data.get("evidence", "") or "")[:300],
        "missing": str(data.get("missing", "") or "")[:300],
        "latency_s": round(reply.latency_s, 2),
    }

  def _app_tips(self, package: str) -> Optional[str]:
    """Skill-style tips, loaded only while the matching app is in front.

    A file `skills/<key>.md` applies when <key> occurs in the foreground
    package name (e.g. `markor.md` for net.gsantner.markor). Progressive
    disclosure: the tips cost tokens only when they are relevant.
    """
    if not (self.config.use_skills and self._skills_dir and package):
      return None
    if not self._skills_dir.is_dir():
      return None
    tips = []
    for path in sorted(self._skills_dir.glob("*.md")):
      key = path.stem.lower()
      if key != "readme" and key in package.lower():
        tips.append(path.read_text(encoding="utf-8").strip())
    return "\n".join(t for t in tips if t) or None

  # --- bookkeeping ------------------------------------------------------------

  def _count_model_call(self, reply: model_lib.ModelReply) -> None:
    self.stats["model_calls"] += 1
    self.stats["model_seconds"] += reply.latency_s
    self.stats["prompt_tokens"] += reply.prompt_tokens or 0
    self.stats["completion_tokens"] += reply.completion_tokens or 0

  def _declared_done(self) -> bool:
    return self.stop_reason in (STOP_MODEL_DONE, STOP_MODEL_INFEASIBLE)

  def _log(
      self,
      record: dict[str, Any],
      obs: _Observation,
      resolved: Optional[actions.ResolvedAction] = None,
  ) -> None:
    if self.trajectory is None:
      return
    box = None
    tap_xy = None
    if resolved is not None:
      tap_xy = resolved.tap_xy
      if resolved.target is not None and tap_xy is not None:
        t = resolved.target
        box = (t.x_min, t.y_min, t.x_max, t.y_max)
    self.trajectory.log_step(
        record, obs.state.pixels, obs.screen_size, tap_xy, box
    )

  def _result(
      self, done: bool, record: dict[str, Any]
  ) -> base_agent.AgentInteractionResult:
    # Note: AndroidWorld reserves the key 'step_number' in this dict.
    data = {
        "agent_step": record.get("step"),
        "action": record.get("action"),
        "thought": record.get("thought"),
        "outcome": record.get("outcome"),
        "stop_reason": self.stop_reason,
        "halted": self.halted,
    }
    return base_agent.AgentInteractionResult(done=done, data=data)
