"""Suggests a failure class for a failed run.

The five classes are the fixed list from the lecture. The suggestion is a
starting point computed from the trajectory; a human confirms it against the
recording (the log has a `failure_reviewed` column for that). The evidence
string says which signals fired, so the suggestion can be checked, not just
believed.
"""

from __future__ import annotations

from typing import Any, Optional

from gui_agent import goal_values

GROUNDING = "grounding"  # the tap lands on nothing, or in the wrong place
TOO_EARLY = "too_early"  # acted on a screen that had not finished loading
LOST_VALUE = "lost_value"  # a value was lost or invented on the way
WRONG_APP = "wrong_app"  # ended up in / tried to open a different app
FALSE_DONE = "false_done"  # said "complete", the verifier says fail
FAILURE_CLASSES = (GROUNDING, TOO_EARLY, LOST_VALUE, WRONG_APP, FALSE_DONE)


def _normalise(text: str) -> str:
  return " ".join(str(text).lower().split())


def suggest_failure_class(
    passed: bool,
    declared_done: bool,
    stats: dict[str, Any],
    goal: str,
    stop_reason: Optional[str] = None,
) -> tuple[str, str]:
  """Returns (failure_class, evidence). Both empty for a passed run.

  Signals are checked root cause first: a run that typed an invented value
  and then announced success is `lost_value`, not `false_done`.
  """
  if passed:
    return "", ""
  blocked = stats.get("blocked") or {}
  evidence = []

  # wrong_app: tried to open something off the list, acted in an app outside
  # the allowed set, or tried to find an app on the home screen.
  off_list = blocked.get("app_allow_list", 0)
  out_of_scope = blocked.get("app_scope", 0)
  home_taps = blocked.get("home_screen", 0)
  if home_taps:
    evidence.append(
        f"{home_taps} tap(s) on the home screen blocked (apps must be opened"
        " by name)"
    )
  if off_list:
    evidence.append(f"{off_list} open_app call(s) for an app not on the list")
  if out_of_scope:
    evidence.append(
        f"{out_of_scope} action(s) blocked outside the allowed apps"
    )
  if stats.get("launcher_steps") and not stats.get("apps_opened"):
    evidence.append("stayed on the home screen and never used open_app")
  # A blocked home-screen tap that was followed by open_app is a detour, not
  # a wrong app. It only counts if the agent never got into an app at all.
  never_opened = not stats.get("apps_opened")
  wrong_app = bool(off_list or out_of_scope or (home_taps and never_opened))

  # lost_value: typed something that is not in the goal.
  goal_norm = _normalise(goal)
  invented = [
      t for t in stats.get("typed_texts", [])
      if t and _normalise(t) not in goal_norm
  ]
  if invented:
    shown = "; ".join(repr(t[:40]) for t in invented[:3])
    evidence.append(f"typed text that is not in the goal: {shown}")
  # lost_value, the other half: a value from the goal was never typed at all
  # ("Isla" typed, "Martin" never). Only a root cause if the agent then said
  # "complete"; a run that simply ran out of steps may not have got there.
  # Counted only when some goal values were typed and others not: an agent
  # that typed nothing at all and said "complete" is plain `false_done`.
  tracker = goal_values.GoalTracker(goal)
  omitted = tracker.missing_parts(stats.get("typed_texts", []))
  all_parts = [p for v in tracker.values for p in v.parts]
  partly_typed = bool(omitted) and len(omitted) < len(all_parts)
  if omitted and partly_typed:
    shown = "; ".join(repr(t[:40]) for t in omitted[:3])
    evidence.append(f"goal value(s) never typed: {shown}")
  lost = bool(invented) or (partly_typed and declared_done)

  # grounding: taps that hit nothing or changed nothing.
  on_nothing = stats.get("taps_on_nothing", 0)
  no_effect = stats.get("no_effect_actions", 0)
  loop_blocks = blocked.get("loop_guard", 0)
  if on_nothing:
    evidence.append(f"{on_nothing} tap(s) landed on no UI element")
  if no_effect:
    evidence.append(f"{no_effect} action(s) did not change the screen")
  if loop_blocks:
    evidence.append(f"{loop_blocks} repeated action(s) blocked by the loop guard")
  # One tap on blank space is not enough: the tree lists only leaf elements,
  # so a correct tap on a row's padding also "hits nothing".
  grounding = (
      no_effect >= 2 or loop_blocks >= 1 or (on_nothing >= 1 and no_effect >= 1)
  )

  # too_early: the screen only changed on the second look. This is measured
  # only when `wait_for_stable` is on (V3); V1 and V2 never take the second
  # look, so for them this class has to come from watching the recording.
  late = stats.get("late_changes", 0)
  if late:
    evidence.append(f"{late} action(s) only showed an effect after an extra wait")

  if declared_done:
    evidence.append("agent reported complete, verifier says fail")
  elif stop_reason:
    evidence.append(f"ended by {stop_reason}")
  if stats.get("invalid_replies"):
    evidence.append(f"{stats['invalid_replies']} invalid model repl(ies)")
  if stats.get("done_rejections"):
    evidence.append(f"{stats['done_rejections']} done claim(s) rejected by the check step")

  if wrong_app:
    chosen = WRONG_APP
  elif lost:
    chosen = LOST_VALUE
  elif grounding:
    chosen = GROUNDING
  elif late:
    chosen = TOO_EARLY
  elif declared_done:
    chosen = FALSE_DONE
  else:
    chosen = GROUNDING  # ran out of steps without a clearer signal
    evidence.append("no clear signal: check the recording")
  return chosen, "; ".join(evidence)
