"""Runs the evaluation: N runs of each task with one agent configuration.

Example (emulator must already be running, see README):

    python run_eval.py --config configs/v1_baseline.json
    python run_eval.py --config configs/v2_index.json
    python summarize.py

For every run this script
  * creates the task instance from a seed (same seeds for every agent
    version, so V1 and V2 face identical task parameters),
  * records the screen,
  * writes the trajectory step by step,
  * asks AndroidWorld's own checker whether the task succeeded,
  * appends one row to runs/log.csv in the lecture's format.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import platform
import random
import sys
import time
import traceback
from pathlib import Path
from typing import Any, Optional

from gui_agent import config as config_lib
from gui_agent import evallog
from gui_agent import failure
from gui_agent import recorder as recorder_lib
from gui_agent import trajectory as trajectory_lib

REPO_ROOT = Path(__file__).resolve().parent
DEFAULT_TASKS = "ContactsAddContact,MarkorCreateNote,MarkorCreateNoteAndSms"

os.environ.setdefault("GRPC_VERBOSITY", "ERROR")
os.environ.setdefault("GRPC_TRACE", "none")


def instance_seed(base_seed: int, task_name: str, index: int) -> int:
  """Seed of the index-th (0-based) instance of a task.

  Same formula as android_world.suite_utils.create_suite, so run i here uses
  the same task parameters as the official harness with
  --task_random_seed=<base_seed> --n_task_combinations=<n>.
  """
  text = f"{base_seed}_{task_name}_{index}"
  return int(hashlib.sha256(text.encode()).hexdigest(), 16) % (2**32)


def run_episode(
    env: Any,
    agent: Any,
    task: Any,
    run_dir: Path,
    meta: dict[str, Any],
    recorder: Optional[recorder_lib.ScreenRecorder] = None,
    print_fn=print,
) -> dict[str, Any]:
  """Runs one task instance end to end and returns the result dict."""
  logger = trajectory_lib.TrajectoryLogger(run_dir, agent.config.image_max_side)
  started = time.time()
  error_text = None
  state_score: Optional[float] = None
  steps = 0
  initialized = False
  agent.clear_episode_state()
  try:
    task.initialize_task(env)
    initialized = True
    budget_from_task = int(task.complexity * 10)  # AndroidWorld's step budget
    agent.trajectory = logger
    agent.reset(go_home=True)
    agent.set_max_steps(budget_from_task)
    meta = dict(meta, goal=task.goal, budget=agent.budget)
    logger.write_meta(meta)
    print_fn(f"  goal: {task.goal}")
    if recorder is not None:
      recorder.start()

    for _ in range(agent.budget):
      step_started = time.time()
      result = agent.step(task.goal)
      print_fn(
          f"  step {agent.stats['steps']}/{agent.budget}"
          f"  {agent.last_history_line}"
          f"  ({time.time() - step_started:.1f}s)"
      )
      if result.done or agent.halted:
        break
    time.sleep(1.5)  # keep the final screen in the recording
  except KeyboardInterrupt:
    error_text = "interrupted by user"
    raise
  except Exception as error:  # pylint: disable=broad-exception-caught
    error_text = f"{type(error).__name__}: {error}"
    traceback.print_exc()
  finally:
    steps = agent.stats["steps"]  # also correct when a step raised
    recording_path = None
    recording_error = None
    if recorder is not None:
      try:
        recording_path = recorder.stop()
        recording_error = recorder.error
      except Exception as error:  # pylint: disable=broad-exception-caught
        recording_error = f"{type(error).__name__}: {error}"
    if initialized and error_text is None:
      try:
        state_score = float(task.is_successful(env))
      except Exception as error:  # pylint: disable=broad-exception-caught
        error_text = f"verifier error: {type(error).__name__}: {error}"
    if initialized:
      try:
        task.tear_down(env)
      except Exception as error:  # pylint: disable=broad-exception-caught
        print_fn(f"  warning: tear_down failed: {error}")

  stop_reason = agent.stop_reason or ("error" if error_text else "step_limit")
  declared_done = stop_reason == "model_done"
  if error_text is not None:
    verifier = "ERROR"
  elif declared_done and state_score is not None and state_score >= 0.999:
    verifier = "PASS"
  else:
    verifier = "FAIL"

  failure_class, evidence = "", ""
  if verifier == "FAIL":
    failure_class, evidence = failure.suggest_failure_class(
        False, declared_done, agent.stats, task.goal, stop_reason
    )
  notes = []
  if error_text:
    notes.append(error_text)
  if verifier == "FAIL" and state_score is not None and state_score >= 0.999:
    notes.append("device state was correct, but the agent never reported done")
  elif verifier == "FAIL" and state_score:
    notes.append(f"partial credit from the checker: {state_score:.2f}")
  if evidence:
    notes.append(evidence)
  if recording_error:
    notes.append(f"recording: {recording_error}")

  result = {
      "verifier": verifier,
      "state_score": state_score,
      "declared_done": declared_done,
      "stop_reason": stop_reason,
      "steps": steps,
      "budget": agent.budget,
      "failure_class": failure_class,
      "failure_evidence": evidence,
      "note": "; ".join(notes),
      "recording": str(recording_path) if recording_path else "",
      "duration_s": round(time.time() - started, 1),
      "stats": agent.stats,
  }
  logger.write_result(result)
  try:
    from gui_agent import report  # pylint: disable=import-outside-toplevel
    report.write_html(run_dir)
  except Exception as error:  # pylint: disable=broad-exception-caught
    print_fn(f"  warning: could not write trajectory.html: {error}")
  return result


def _relative(path: str | Path, root: Path) -> str:
  if not path:
    return ""
  try:
    return str(Path(path).resolve().relative_to(root.resolve()))
  except ValueError:
    return str(path)


def _parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
  parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
  parser.add_argument("--config", required=True, help="agent config JSON file")
  parser.add_argument("--tasks", default=DEFAULT_TASKS,
                      help="comma-separated AndroidWorld task names")
  parser.add_argument("--runs", type=int, default=3, help="runs per task")
  parser.add_argument("--run_indices", default="",
                      help='only these runs, e.g. "2" or "1,3" (for re-runs)')
  parser.add_argument("--seed", type=int, default=30,
                      help="base seed for task parameters")
  parser.add_argument("--out", default="runs", help="output directory")
  parser.add_argument("--model", default="", help="override the config's model")
  parser.add_argument("--max_steps", type=int, default=0,
                      help="override the config's hard step limit")
  parser.add_argument("--no_record", action="store_true",
                      help="do not record the screen")
  parser.add_argument("--adb_path", default="", help="path to adb")
  parser.add_argument("--console_port", type=int, default=5554)
  parser.add_argument("--perform_emulator_setup", action="store_true",
                      help="one-time app installation on a fresh emulator")
  return parser.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
  args = _parse_args(argv)
  cfg = config_lib.AgentConfig.from_file(args.config)
  try:
    if args.model:
      cfg = cfg.replace(model=args.model)
    if args.max_steps:
      cfg = cfg.replace(max_steps=args.max_steps)
  except ValueError as error:
    print(f"Invalid option: {error}", file=sys.stderr)
    return 2

  adb_path = recorder_lib.find_adb(args.adb_path or None)
  if not adb_path:
    print("adb not found. Install the Android SDK platform-tools or pass"
          " --adb_path.", file=sys.stderr)
    return 2

  # Imported late so that --help works without AndroidWorld installed.
  from android_world import registry  # pylint: disable=import-outside-toplevel
  from android_world.env import env_launcher  # pylint: disable=import-outside-toplevel
  from gui_agent import agent as agent_lib  # pylint: disable=import-outside-toplevel
  from gui_agent import model as model_lib  # pylint: disable=import-outside-toplevel
  import gui_agent  # pylint: disable=import-outside-toplevel

  task_registry = registry.TaskRegistry()
  all_tasks = task_registry.get_registry(task_registry.ANDROID_WORLD_FAMILY)
  task_names = [t.strip() for t in args.tasks.split(",") if t.strip()]
  unknown = [t for t in task_names if t not in all_tasks]
  if unknown:
    print(f"Unknown task(s): {unknown}", file=sys.stderr)
    return 2
  if args.run_indices:
    run_indices = [int(i) for i in args.run_indices.split(",")]
  else:
    run_indices = list(range(1, args.runs + 1))

  out_root = Path(args.out)
  out_root.mkdir(parents=True, exist_ok=True)
  csv_path = out_root / "log.csv"

  model = model_lib.make_client(cfg)
  model_info = model.describe()
  model_label = cfg.model
  if model_info.get("quantization"):
    model_label += f" ({model_info['quantization']}, {cfg.backend})"
  else:
    model_label += f" ({cfg.backend})"

  print(f"Connecting to emulator on console port {args.console_port} ...")
  env = env_launcher.load_and_setup_env(
      console_port=args.console_port,
      emulator_setup=args.perform_emulator_setup,
      adb_path=adb_path,
  )
  env.reset(go_home=True)
  agent = agent_lib.GuiAgent(env, cfg, model, skills_dir=REPO_ROOT / "skills")
  serial = f"emulator-{args.console_port}"

  print(f"Agent {cfg.name} | model {model_label} | observation"
        f" {cfg.observation} | grounding {cfg.grounding}")
  counts = {"PASS": 0, "FAIL": 0, "ERROR": 0}
  try:
    for task_name in task_names:
      task_type = all_tasks[task_name]
      for run_index in run_indices:
        seed = instance_seed(args.seed, task_name, run_index - 1)
        random.seed(seed)
        params = task_type.generate_random_params()
        params["seed"] = seed
        task = task_type(params)
        stamp = time.strftime("%Y%m%d-%H%M%S")
        run_dir = out_root / cfg.name / task_name / f"run{run_index}_{stamp}"
        run_dir.mkdir(parents=True, exist_ok=True)
        run_label = f"{run_index} of {max(args.runs, max(run_indices))}"
        print(f"\n[{cfg.name}] {task_name}, run {run_label} (seed {seed})")
        recorder = None
        if not args.no_record:
          recorder = recorder_lib.ScreenRecorder(
              adb_path, serial, run_dir / "recording.mp4"
          )
        meta = {
            "task": task_name,
            "run": run_index,
            "seed": seed,
            "base_seed": args.seed,
            "params": {k: v for k, v in params.items()},
            "complexity": task_type.complexity,
            "config": cfg.to_dict(),
            "model": model_info,
            "agent_version": gui_agent.__version__,
            "started": trajectory_lib.now_iso(),
            "host": f"{platform.system()} {platform.machine()},"
                    f" Python {platform.python_version()}",
        }
        result = run_episode(env, agent, task, run_dir, meta, recorder)
        counts[result["verifier"]] += 1
        stats = result["stats"]
        evallog.append_row(csv_path, {
            "timestamp": meta["started"],
            "agent": cfg.name,
            "task": task_name,
            "run": run_label,
            "model": model_label,
            "observation": cfg.observation,
            "grounding": cfg.grounding,
            "steps": result["steps"],
            "budget": result["budget"],
            "verifier": result["verifier"],
            "failure_class": result["failure_class"],
            "failure_reviewed": "",
            "recording": _relative(result["recording"], out_root),
            "note": result["note"],
            "stop_reason": result["stop_reason"],
            "state_score": result["state_score"],
            "seed": seed,
            "duration_s": result["duration_s"],
            "model_seconds": round(stats["model_seconds"], 1),
            "model_calls": stats["model_calls"],
            "prompt_tokens": stats["prompt_tokens"],
            "completion_tokens": stats["completion_tokens"],
            "invalid_replies": stats["invalid_replies"],
            "no_effect_actions": stats["no_effect_actions"],
            "blocked": ", ".join(f"{k}={v}" for k, v in stats["blocked"].items()),
            "goal": task.goal,
            "run_dir": _relative(run_dir, out_root),
        })
        evallog.write_markdown(csv_path, out_root / "log.md")
        print(f"  => {result['verifier']}  steps {result['steps']}"
              f" (budget {result['budget']})  {result['stop_reason']}"
              + (f"  [{result['failure_class']}?]" if result["failure_class"] else ""))
        if result["note"]:
          print(f"     {result['note']}")
  except KeyboardInterrupt:
    print("\nInterrupted. Finished runs are in the log.")
  finally:
    try:
      env.close()
    except Exception:  # pylint: disable=broad-exception-caught
      pass

  total = sum(counts.values())
  print(f"\nDone: {counts['PASS']} PASS, {counts['FAIL']} FAIL,"
        f" {counts['ERROR']} ERROR out of {total} run(s).")
  print(f"Log: {csv_path}   Table: {out_root / 'log.md'}")
  return 0


if __name__ == "__main__":
  sys.exit(main())
