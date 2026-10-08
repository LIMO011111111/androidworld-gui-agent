"""The evaluation runner, the run log and the failure-class suggestion."""

import json

import pytest

pytest.importorskip("android_world")

import run_eval  # noqa: E402
from gui_agent import agent as agent_lib  # noqa: E402
from gui_agent import config as config_lib  # noqa: E402
from gui_agent import evallog  # noqa: E402
from gui_agent import failure  # noqa: E402
from tests import fakes  # noqa: E402
from tests import test_agent  # noqa: E402


def _run(tmp_path, replies, **overrides):
  settings = dict(
      name="test", wait_for_stable=False, transition_pause_s=0.0,
      verify_before_done=False,
  )
  settings.update(overrides)
  cfg = config_lib.AgentConfig(**settings)
  phone = fakes.FakePhone(test_agent.SCREENS, "home", test_agent.contacts_app)
  agent = agent_lib.GuiAgent(phone, cfg, fakes.ScriptedModel(replies))
  task = fakes.FakeTask(test_agent.GOAL, success_screen="saved")
  meta = {"task": "ContactsAddContact", "run": 1, "seed": 7, "config": cfg.to_dict(),
          "model": {"model": "scripted"}}
  result = run_eval.run_episode(phone, agent, task, tmp_path, meta, None, lambda _: None)
  return result, task, phone


def test_passing_run_writes_all_artifacts(tmp_path):
  result, task, _ = _run(tmp_path, test_agent.HAPPY_PATH)
  assert result["verifier"] == "PASS"
  assert result["steps"] == 6 and result["budget"] == 10  # complexity 1.0 * 10
  assert result["failure_class"] == ""
  assert task.initialized and task.torn_down
  assert json.loads((tmp_path / "meta.json").read_text())["goal"] == test_agent.GOAL
  assert json.loads((tmp_path / "result.json").read_text())["verifier"] == "PASS"
  assert len((tmp_path / "trajectory.jsonl").read_text().strip().splitlines()) == 6
  page = (tmp_path / "trajectory.html").read_text()
  assert "Step 6 of 10" in page and "screens/step_01.jpg" in page


def test_false_done_is_a_fail_even_though_the_agent_said_complete(tmp_path):
  replies = [
      test_agent.reply(thought="open", action_type="open_app", app_name="contacts"),
      test_agent.reply(thought="looks done", action_type="status", goal_status="complete"),
  ]
  result, _, _ = _run(tmp_path, replies)
  assert result["verifier"] == "FAIL"
  assert result["declared_done"] is True
  assert result["failure_class"] == failure.FALSE_DONE
  assert "verifier says fail" in result["failure_evidence"]


def test_running_out_of_steps_is_a_fail_and_is_never_reported_as_done(tmp_path):
  waits = [test_agent.reply(thought="w", action_type="wait")] * 10
  result, _, phone = _run(tmp_path, waits, loop_guard=False)
  assert result["verifier"] == "FAIL"
  assert result["stop_reason"] == "step_limit"
  assert result["steps"] == 10 and len(phone.executed) == 10


def test_correct_state_without_done_is_still_a_fail_and_says_so(tmp_path):
  replies = test_agent.HAPPY_PATH[:5] + [test_agent.reply(thought="w", action_type="wait")] * 5
  result, _, _ = _run(tmp_path, replies, loop_guard=False)
  assert result["state_score"] == 1.0
  assert result["verifier"] == "FAIL"
  assert "never reported done" in result["note"]


def test_crash_inside_a_run_becomes_an_error_row_not_a_fail(tmp_path):
  result, task, _ = _run(tmp_path, [])  # the scripted model has nothing to say
  assert result["verifier"] == "ERROR"
  assert "ran out of replies" in result["note"]
  assert task.torn_down


def test_seeds_match_androidworlds_own_formula():
  from android_world import suite_utils
  suite = suite_utils.create_suite(
      {"ContactsAddContact": __import__(
          "android_world.registry", fromlist=["x"]
      ).TaskRegistry().get_registry("android_world")["ContactsAddContact"]},
      n_task_combinations=3, seed=30,
  )
  official = [t.params["seed"] for t in suite["ContactsAddContact"]]
  ours = [run_eval.instance_seed(30, "ContactsAddContact", i) for i in range(3)]
  assert ours == official


def test_log_csv_and_markdown_table(tmp_path):
  csv_path = tmp_path / "log.csv"
  for run, verdict, cls in (("1 of 3", "PASS", ""), ("2 of 3", "FAIL", "grounding")):
    evallog.append_row(csv_path, {
        "agent": "v1_baseline", "task": "MarkorCreateNote", "run": run,
        "model": "qwen3-vl:4b-instruct (Q4_K_M, ollama)", "observation": "screenshot",
        "grounding": "coordinate", "steps": 9, "budget": 16, "verifier": verdict,
        "failure_class": cls, "recording": "v1/run.mp4", "note": "a | b",
    })
  rows = evallog.read_rows(csv_path)
  assert [r["verifier"] for r in rows] == ["PASS", "FAIL"]
  evallog.write_markdown(csv_path, tmp_path / "log.md")
  table = (tmp_path / "log.md").read_text()
  assert "| steps (budget) |" in table and "| 9 (16) |" in table
  assert "grounding (?)" in table  # unreviewed suggestions are marked
  assert "a \\| b" in table


@pytest.mark.parametrize(
    "stats, declared, expected",
    [
        ({"blocked": {"app_allow_list": 1}}, True, failure.WRONG_APP),
        ({"typed_texts": ["Nikola Fernandes"]}, True, failure.LOST_VALUE),
        ({"typed_texts": ["Nikola Fernandez"], "taps_on_nothing": 2}, False, failure.GROUNDING),
        ({"no_effect_actions": 3}, True, failure.GROUNDING),
        ({"late_changes": 1}, False, failure.TOO_EARLY),
        ({}, True, failure.FALSE_DONE),
    ],
)
def test_failure_class_suggestion(stats, declared, expected):
  chosen, evidence = failure.suggest_failure_class(
      False, declared, stats, test_agent.GOAL, "step_limit"
  )
  assert chosen == expected and evidence


def test_no_failure_class_for_a_pass():
  assert failure.suggest_failure_class(True, True, {}, "goal") == ("", "")


class _RegisteredTask(fakes.FakeTask):
  """A task type as the registry would hand it out."""

  complexity = 1.2

  def __init__(self, params):
    super().__init__(test_agent.GOAL, success_screen="saved")
    self.params = params

  @classmethod
  def generate_random_params(cls):
    return {"name": "Nikola Fernandez"}


def test_main_runs_tasks_times_runs_and_fills_the_log(tmp_path, monkeypatch):
  from android_world import registry
  from android_world.env import env_launcher
  from gui_agent import model as model_lib
  from gui_agent import recorder as recorder_lib

  phone = fakes.FakePhone(test_agent.SCREENS, "home", test_agent.contacts_app)
  monkeypatch.setattr(recorder_lib, "find_adb", lambda explicit=None: "/fake/adb")
  monkeypatch.setattr(env_launcher, "load_and_setup_env", lambda **kwargs: phone)
  monkeypatch.setattr(
      registry.TaskRegistry, "get_registry",
      lambda self, family=None: {"ContactsAddContact": _RegisteredTask},
  )
  monkeypatch.setattr(
      model_lib, "make_client",
      lambda cfg: fakes.ScriptedModel(test_agent.HAPPY_PATH * 2),
  )
  config_path = tmp_path / "cfg.json"
  config_path.write_text(json.dumps({
      "_comment": "ignored", "name": "v_test", "wait_for_stable": False,
      "transition_pause_s": 0.0, "verify_before_done": False,
  }))
  out = tmp_path / "runs"
  code = run_eval.main([
      "--config", str(config_path), "--tasks", "ContactsAddContact",
      "--runs", "2", "--out", str(out), "--no_record",
  ])
  assert code == 0
  rows = evallog.read_rows(out / "log.csv")
  assert [r["run"] for r in rows] == ["1 of 2", "2 of 2"]
  assert [r["verifier"] for r in rows] == ["PASS", "PASS"]
  assert rows[0]["agent"] == "v_test" and rows[0]["budget"] == "12"
  assert rows[0]["seed"] != rows[1]["seed"]
  assert (out / rows[0]["run_dir"] / "trajectory.html").exists()
  assert (out / "log.md").exists()


def test_summary_counts_pass_and_fail_and_sets_errors_aside():
  import summarize

  def row(agent, task, seed, verdict, steps, cls=""):
    return {"agent": agent, "task": task, "run": "1 of 3", "seed": seed,
            "verifier": verdict, "steps": str(steps), "failure_class": cls,
            "duration_s": "60", "model_seconds": "40", "model_calls": str(steps),
            "prompt_tokens": str(steps * 1000), "invalid_replies": "0", "note": "boom"}

  rows = [
      row("v1", "A", "1", "FAIL", 10, "grounding"),
      row("v1", "A", "2", "PASS", 6),
      row("v1", "B", "3", "ERROR", 0),
      row("v2", "A", "1", "PASS", 5),
      row("v2", "A", "2", "PASS", 7),
  ]
  text = summarize.build_summary(rows)
  assert "| A | 1/2 (50 %) | 2/2 (100 %) |" in text
  assert "| **all tasks** | **1/2 (50 %)** | **2/2 (100 %)** |" in text
  assert "| A | 1 | FAIL in 10 steps [grounding] | PASS in 5 steps |" in text
  assert "| v1 | 1 | 1 | 0 | 0 | 0 | 0 | 0/1 |" in text
  assert "## Runs excluded as ERROR" in text and "| v1 | B |" in text


def test_a_blocked_home_screen_tap_followed_by_open_app_is_not_wrong_app():
  # The first real run on the device: one blocked tap on the home screen,
  # then open_app contacts, only the first name typed, then "complete".
  stats = {"blocked": {"home_screen": 1}, "apps_opened": ["contacts"],
           "typed_texts": ["Hugo", "+13920741751"], "no_effect_actions": 3}
  goal = "Create a new contact for Hugo Pereira. Their number is +13920741751."
  chosen, evidence = failure.suggest_failure_class(False, True, stats, goal, "model_done")
  assert chosen != failure.WRONG_APP
  assert "home screen" in evidence
  stats["apps_opened"] = []
  assert failure.suggest_failure_class(False, False, stats, goal, "step_limit")[0] == failure.WRONG_APP


def test_an_omitted_goal_value_with_done_is_lost_value():
  goal = "Create a new contact for Isla Martin. Their number is +15256606183."
  stats = {"typed_texts": ["Isla", "+15256606183"]}
  chosen, evidence = failure.suggest_failure_class(False, True, stats, goal, "model_done")
  assert chosen == failure.LOST_VALUE
  assert "never typed: 'Martin'" in evidence
  # Without "complete" it is only evidence, not the root cause.
  assert failure.suggest_failure_class(False, False, stats, goal, "step_limit")[0] != failure.LOST_VALUE
