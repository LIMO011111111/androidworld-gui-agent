# AndroidWorld GUI agent with a code-level harness

Group project, *Agentic AI in Business* (MGTHN0211), TUM Campus Heilbronn.

A vision-language GUI agent for the [AndroidWorld](https://github.com/google-research/android_world)
benchmark. The agent is one class with a single `step()` method
(`gui_agent/agent.py`): it reads the screen and the task, chooses one action
and says whether it is done. Everything that has to hold regardless of what
the model outputs (step limit, payment ban, app scope, loop detection, the
check before "done") is enforced in code around the model call.

The repo contains the agent, three switchable versions of it for a clean
before-after comparison, the evaluation runner (3 tasks x 3 runs, screen
recording, trajectory logs, one log row per run in the lecture's format) and
unit tests for the guardrails, including the bypass attempts of an
adversarial review.

## Quick start (macOS)

Open the Ollama app first (`ollama --version` must work), then:

```bash
bash scripts/setup_mac.sh            # Python env, AndroidWorld, AVD, model, tests
bash scripts/start_emulator.sh       # terminal A, leave it running
```

Wait until the emulator shows the Android home screen (a cold boot takes one
to two minutes), then:

```bash
source .venv/bin/activate            # terminal B
python scripts/doctor.py             # checks emulator, model, grounding sanity

# First run only: installs the AndroidWorld apps on the fresh emulator.
python run_eval.py --config configs/v2_index.json \
    --tasks ContactsAddContact --runs 1 --perform_emulator_setup --out runs_setup

# The evaluation: 3 tasks x 3 runs per agent version.
python run_eval.py --config configs/v1_baseline.json
python run_eval.py --config configs/v2_index.json
python run_eval.py --config configs/v3_full.json      # optional third level
python summarize.py                                    # before-after tables
```

An evaluation with a local model runs for a long time. Prefix the commands
with `caffeinate -i` (for example `caffeinate -i python run_eval.py ...`) so
the laptop does not go to sleep in the middle of a run.

Requirements: macOS with Homebrew, about 15 to 20 GB of free disk space,
[Ollama](https://ollama.com/download) (0.12.7 or newer for Qwen3-VL), and the
Android SDK with an emulator. `setup_mac.sh` creates the AVD itself when the
SDK command-line tools are installed (Android Studio: SDK Manager, tab "SDK
Tools", "Android SDK Command-line Tools"). Otherwise it prints what to click
in Android Studio: device Pixel 6, system image Tiramisu / API 33 with the
target **"Google APIs"** (not "Google Play": AndroidWorld needs `adb root`,
which Play images refuse), name `AndroidWorldAvd`.

The default tasks are one per difficulty row of the project brief:

| Difficulty | Task | Step budget |
|---|---|---|
| Warm-up | `ContactsAddContact` | 12 |
| Real work | `MarkorCreateNote` | 16 |
| Multi-app and memory | `MarkorCreateNoteAndSms` | 18 |

The step budget is AndroidWorld's own (`complexity x 10`), capped by the
agent's hard limit `max_steps`. Other tasks: `--tasks ClockTimerEntry,SimpleSmsSend`.

## What a run produces

```
runs/
  log.csv        one row per run, the source of truth
  log.md         the same as a table in the lecture's format
  summary.md     before-after tables (python summarize.py)
  v2_index/MarkorCreateNote/run1_20261008-141502/
    meta.json          task, goal, seed, full config, model name + quantisation
    trajectory.jsonl   one record per step, written during the run
    screens/step_NN.jpg  the screen before each action, tap point marked
    recording.mp4      screen recording of the run
    result.json        verifier result, stop reason, statistics
    trajectory.html    step-by-step replay for failure analysis
```

Log row, as prescribed:
`task · run (x of 3) · model · observation · grounding · steps (budget) ·
verifier PASS/FAIL · failure_class · recording · note`

* **verifier** is AndroidWorld's own checker (`task.is_successful`). A run is
  PASS only if the agent itself reported "complete" *and* the checker returns
  1.0. Running out of steps is never counted as done.
* **failure_class** is one of `grounding`, `too_early`, `lost_value`,
  `wrong_app`, `false_done`. The runner suggests one and writes the evidence
  into `note`. Watch the recording, correct the class if needed and set
  `failure_reviewed` to `yes` in `log.csv`. Unreviewed classes show as `(?)`.
* **ERROR** rows (emulator or model server broke) are kept in the log but
  excluded from all rates.

## The agent

`step()` is a fixed pipeline. Only stage 2 is the model.

| # | Stage | What happens | Where |
|---|---|---|---|
| 0 | budget | step limit checked before anything else | `guardrails.StepBudget` |
| 1 | observe | screen to element list / screenshot / fingerprint | `observation.py` |
| 2 | decide | prompt, model, one JSON action | `prompts.py`, `model.py` |
| 3 | validate | tolerant parsing, strict validation, retry with the error | `actions.parse_action` |
| 4 | ground | index to exact pixel, or rescale 0-1000 coordinates | `actions.resolve_action` |
| 5 | check | check before done, payment ban, app allow-list, loop guard | `guardrails.py`, `agent._verify` |
| 6 | act | execute on the device through AndroidWorld | `agent.py` |
| 7 | feedback | did the screen change? one code-written history line | `agent.py`, `memory.py` |

Design decisions and the reasons for them are in [docs/DESIGN.md](docs/DESIGN.md).

## Three versions, one switch each

All versions share the same code, model, prompts structure, tasks and seeds.
They differ only in config flags, so a difference in results can be attributed.

| | `v1_baseline` | `v2_index` | `v3_full` |
|---|---|---|---|
| observation | screenshot | accessibility tree | accessibility tree |
| grounding | coordinates from the model | index, resolved in code | index, resolved in code |
| wait until the screen is stable | no (fixed 2 s) | no (fixed 2 s) | yes |
| "your action changed nothing" feedback | no | no | yes |
| loop guard | no | no | yes |
| status bar and scratch notes | no | no | yes |
| check step before done | no | no | yes |
| step limit, payment ban, app scope, app allow-list | **always on** | **always on** | **always on** |

V1 to V2 is exactly one change (observation and grounding) and is the
documented improvement. V3 stacks the remaining harness fixes on top.

## Guardrails

Enforced in code after the model has decided and before anything reaches the
device. The step limit, the payment ban, the app scope and the `open_app`
allow-list have no off switch.

* **Step limit.** `max_steps` is a hard cap; a task budget can lower it, never
  raise it. Beyond the limit the model is not called and nothing is executed.
* **Payment ban, layer 1: app scope.** The agent can only act inside a closed
  set of apps, listed with their packages in `config.APP_PACKAGES` (offline
  apps such as Markor, Contacts, Clock; no store, wallet, shop, bank or
  browser), plus Android's own dialogs. A config file can narrow the app set
  but cannot add an app to it. `extra_scope_packages` exists only for system
  surfaces of a particular device image; it is recorded in every run's
  `meta.json`, and payment apps and browsers are refused there. Whenever any other app is in the foreground (judged by the
  resumed activity the device reports), every action except going back, going
  home, waiting or `open_app` is blocked. On the home screen the agent cannot
  tap or type at all; apps are opened by exact name only. A payment is
  therefore not something the agent can reach, whatever a screen says.
* **Payment ban, layer 2: deny rules.** On top of the scope: no action while
  an element of a payment app (Play Store billing sheet, wallet, ...) is
  visible; no action on a payment form (any card / IBAN / CVC field on
  screen); no tap or typing on, or next to, a control labelled pay, buy,
  subscribe, donate, a price, and so on (matched after normalising case,
  camelCase, underscores, zero-width characters and look-alike letters; every
  element under the tap point and the row around the label are checked); no
  Enter and no untargeted typing while such a control is on screen; and no
  typing of a valid card number or IBAN, checked on the text the device will
  actually receive, also when it is split over several inputs.
* **App allow-list.** `open_app` only works for the names in `allowed_apps`.
  With Ollama the list is also part of the JSON schema, so other names cannot
  even be generated.
* **Loop guard** (V3). The same action on an unchanged screen is allowed twice
  and blocked the third time; after three blocks the episode is aborted.

`tests/test_guardrails.py` and `tests/test_agent.py` are the evidence. For
example a scripted model that fills in a checkout form, presses Enter and taps
"Pay" produces zero device actions. What the rules do not cover is listed
under "Known limits".

## Reproducibility

* One command per agent version; the config file is the complete description
  of the agent and is copied into every run's `meta.json`.
* Task parameters come from a seed. Run *i* of a task uses the same seed
  formula as AndroidWorld's `run.py --task_random_seed=30`, and the same seed
  for every agent version.
* Temperature 0 and, with the Ollama backend, a fixed model seed. The model
  name, parameter size, quantisation, digest and Ollama version are recorded
  per run. If any of them changes, re-run the evaluation: it is a different
  model.
* AndroidWorld is pinned to the commit the agent was tested against
  (`scripts/setup_mac.sh`).

## Using a different model

The model is a config value. Any Ollama model:

```bash
python run_eval.py --config configs/v2_index.json --model qwen3-vl:8b-instruct
```

Any OpenAI-compatible endpoint: copy a config and set

```json
{"backend": "openai", "base_url": "https://.../v1", "model": "...", "api_key_env": "MY_API_KEY"}
```

For models that return pixel coordinates of the image instead of 0 to 1000,
set `"coordinate_space": "image_pixels"`.

Note on Qwen3-VL in Ollama: the plain tags (`qwen3-vl:4b`) are the *thinking*
build. Use the `-instruct` tags for an agent loop; `scripts/doctor.py` warns
about this and measures latency and pointing accuracy on a sample screen.

## Tests

```bash
python -m pytest
```

The tests run without an emulator and without a model server: a scripted model
drives a simulated phone through the real AndroidWorld classes
(`JSONAction`, `EnvironmentInteractingAgent`, `episode_runner.run_episode`).

## Known limits

* The payment ban rests on the app scope. Which app is in front is taken from
  the resumed activity reported by the device, with the accessibility tree as
  fallback. Content shown *inside* an allowed app (for example a web page in
  an embedded WebView) is judged only by the deny rules.
* The deny rules are word lists (English and German) and cannot be complete;
  a generic label such as "Continue" is not blocked inside an allowed app.
  Some allowed apps contain "donate" or "upgrade" links; these are blocked by
  label, and where they lead (Play Store, browser) is out of scope anyway.
* The guards judge the screen that was observed before the model call. Right
  before acting, the agent checks again which app is in front and does not
  act if it changed. A change inside the same app (a dialog that appears
  while the model is thinking) is only seen one step later.
* The check step before "done" asks the same small model a second question.
  It can be wrong in both directions, which is why it has a veto budget.
* AndroidWorld's `input_text` always presses Enter after typing and drops
  non-ASCII characters.
* `adb screenrecord` is capped at 180 s per file on Android 13. Longer runs
  are recorded in chunks and joined with ffmpeg; there is a gap of about one
  second between chunks. If recording fails on a machine, the run continues
  and the log row says so; record the emulator window with the OS instead.
* `too_early` can only be suggested automatically for V3 (it needs the second
  look at the screen). For V1 and V2 it has to come from the recording.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `emulator-5554 is not online` | Start the emulator with `scripts/start_emulator.sh`, not from the Android Studio UI (the `-grpc 8554` flag is required). |
| App not found, Markor missing | Run once with `--perform_emulator_setup`. |
| Setup fails downloading apps | It needs internet access to `storage.googleapis.com`. |
| Model replies are slow or empty | Check `python scripts/doctor.py`; use an `-instruct` tag; keep `num_ctx` at 8192 or higher. |
| A run ended as ERROR | Re-run only that one: `--tasks <Task> --run_indices <n>`. |
| History says `BLOCKED: this screen belongs to <package>` for a harmless system screen | Add that package to `"extra_scope_packages"` in the config (payment packages are refused) and re-run. |
| Emulator online but `doctor.py` says it is still booting | Wait for the home screen, then run it again. |
| No `recording.mp4` | See `note` in the log row; use `--no_record` and record the window with the OS screen recorder. |
