# Project report (template)

Fill every `<...>` from your own runs. Numbers come from `runs/summary.md`
and `runs/log.csv`; do not write a number that is not in the log.

## 1. Use case and tasks

* Tasks: `ContactsAddContact` (warm-up), `MarkorCreateNote` (real work),
  `MarkorCreateNoteAndSms` (multi-app and memory).
* Why these: `<one sentence each>`

## 2. Agent design

Summarise from `docs/DESIGN.md`: observation space, grounding, action space,
context handling, harness. Name the model exactly as logged:
`<model name, parameter size, quantisation, runtime>`.

## 3. Evaluation setup

* `<n>` runs per task and version, seeds `<base seed>`, temperature 0.
* Machine: `<model of laptop, RAM>`; emulator: Pixel 6, API 33.
* PASS = agent reported complete and AndroidWorld's checker returned 1.0.

## 4. Results

Paste the tables "Success rate", "Same task instance, side by side" and
"Cost" from `runs/summary.md`.

## 5. Failure analysis (at least one run, in depth)

* Run: `<agent / task / run, link to recording and trajectory.html>`
* What the task asked: `<goal>`
* What happened, step by step: `<the two or three decisive steps, with the
  screenshot from screens/step_NN.jpg>`
* Failure class: `<one of the five>`, reviewed against the recording.
* Evidence: `<what in the trajectory shows it: tap point, target element,
  screen changed or not, typed text>`
* Root cause in one sentence: `<...>`

## 6. One documented improvement

* Change: `<v1_baseline -> v2_index: observation and grounding>`
* Why this change for this failure class: `<...>`
* Why the fix belongs in code and not in the prompt: `<...>`
* Before and after, same task instances:

| | before (`<version>`) | after (`<version>`) |
|---|---|---|
| success rate | `<x/9>` | `<y/9>` |
| avg steps | `<...>` | `<...>` |
| prompt tokens per model call | `<...>` | `<...>` |
| failure classes | `<...>` | `<...>` |

* What did not improve, or got worse: `<...>`

## 7. A failed attempt

`<Something you tried that did not work, with the run that shows it. For
example: the check step before done, a prompt rule, a different model.>`

## 8. Lessons

`<Three sentences at most.>`

## 9. How to reproduce

`README.md`, section "Quick start". Commit: `<git commit hash>`.
