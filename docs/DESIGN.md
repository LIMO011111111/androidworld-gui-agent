# Design decisions

Each decision below names the lecture point it answers and the place in the
code where it lives. Nothing here is a result; results come from
`runs/summary.md` after the evaluation.

## 1. Observation space: accessibility tree first, screenshot as fallback

*Day 1, "Which one you put in the window is the first real design decision."*

| | Screenshot | Accessibility tree |
|---|---|---|
| Sees | everything, including canvases and WebViews | only what apps expose |
| Precision | the model must locate the element itself | exact strings and exact boxes |
| Cost | one image per step | one short text line per element |

Decision: V2 and V3 send the tree as text, one line per element:

```
[4] Button "Save" (clickable)
[7] EditText "Anna" hint="First name" (editable, focused)
```

Elements that say nothing and cannot be acted on are dropped, long texts are
clipped, the status bar icons are hidden and the list is capped
(`max_elements`). If the tree exposes nothing at all, that single step falls
back to screenshot plus coordinates ("take the index route unless the tree is
empty"). Code: `observation.build_views`, `observation.render_tree`,
`agent.step` (pixel fallback).

V1 is the opposite corner on purpose: screenshot only, as in GELab-Zero, so
the comparison isolates this decision.

## 2. Grounding: by index, resolved in our code

*Day 1, "Most GUI-agent failures are pointing failures, not reasoning
failures." "Where grounding happens decides who you can blame."*

In index mode the model answers `{"action_type": "click", "index": 4}`. Our
code looks up element 4 in the list the model was shown, takes the centre of
its box and sends explicit pixel coordinates to the device. Grounding is a
table lookup, so a wrong tap is a bug we can find in the trajectory log, where
every step records the target element and the tap point.

For taps and typing we do not pass the index through to AndroidWorld. Its
`execute_action` takes a fresh UI dump and resolves the index against that; if
the screen shifted in between, the same number can mean a different element.
The one exception is scrolling inside a scrollable element, where AndroidWorld
offers no coordinate form.

In coordinate mode (V1) the model produces `x` and `y` on a 0 to 1000 grid
(the Qwen3-VL and GELab-Zero convention) and the code only rescales them to
screen pixels. Even then the harness hit-tests the point against the tree,
which the model does not see, to log what the tap landed on and to apply the
payment ban. Code: `actions.resolve_action`, `observation.hit_test`.

## 3. Context cost: one screen, one line per past step

*Day 1, "Keep the state, not every image." Day 2, status bar.*

The prompt is rebuilt every step and never grows as a chat:

* only the current screen is included; old screens are never resent;
* each past step is one line written by code, with the observed effect:
  `3. click [5] Button "Save" -> screen changed`;
* only the last `history_lines` lines are kept;
* there is no second model call to summarise a step (AndroidWorld's reference
  agents T3A and M3A make one per step); the summary line is produced by code.

Prompt tokens per model call are logged for every step, so the cost of the
two observation spaces can be compared with numbers from our own runs.
Code: `memory.EpisodeMemory`, `prompts.user_message`.

## 4. Prompt layout: stable prefix, volatile content last

*Day 2, cache-friendly design.*

The system prompt (role, action space, rules) is identical for every step of a
run. Goal, history and screen follow in one user message, and the status bar,
which changes every step, is the last block. Roles are sent as standard chat
messages, not flattened into one string.

## 5. Action space: small, AndroidWorld-native, constrained

*Day 3, tools are the action space.*

Ten actions: `click`, `long_press`, `input_text`, `scroll`, `open_app`,
`navigate_back`, `navigate_home`, `keyboard_enter`, `wait`, `status`. They map
one to one onto AndroidWorld's `JSONAction`, so no translation layer can
introduce errors.

Output is constrained twice (*Day 1, format drift*):

1. With Ollama the JSON schema is passed as `format`, so invalid action types
   and app names that are not on the allow-list cannot be generated.
2. The reply is still parsed tolerantly (prose around the JSON, code fences,
   `<think>` blocks, single quotes) and validated strictly. An invalid reply
   is sent back with the error message for up to `parse_retries` retries.

The `thought` field comes first in the schema and in every example, which
steers the model to write its reason before it commits to an action.
Code: `actions.py`.

## 6. Harness instead of prompt

*Day 4, layered constraints. Day 5, "A rule that must never be bypassed ->
Programs."*

| Rule | Why it is in code | Code |
|---|---|---|
| Step limit | "Limit the number of iterations": the loop lives in our code | `guardrails.StepBudget` |
| App scope | the agent can only act inside a closed set of payment-free apps; elsewhere it can only leave. Holds for screens nobody anticipated | `guardrails.AppScope`, `config.APP_PACKAGES` |
| Payment deny rules | payment apps, forms, buttons, fields, card numbers, IBANs | `guardrails.PaymentGuard` |
| App allow-list | `wrong_app`: `open_app` by name only; no tapping on the home screen (enforced by the scope rule); a few near-miss spellings are corrected in code | `guardrails.AppAllowList` |
| Loop detection | the harness counts repeats; the model is not asked to notice | `guardrails.LoopDetector` |
| Check before done | `false_done` is silent; a separate look at the final screen | `agent._verify` |
| Screen-changed check | `too_early`: wait for a stable UI, look twice before saying "nothing happened" | `agent.step`, stage 7 |
| Scratch notes | `lost_value`: the model chooses what to note, code keeps it in front of it | `memory.EpisodeMemory` |

The prompt also says "never pay". That line is guidance, not the guardrail.

Why two layers for the payment ban: a list of payment words can never be
complete, so a list alone is not a ban. The scope rule does not try to
recognise payments. It restricts where the agent can act at all, to apps that
cannot charge anything, and treats every other app as "leave only". The word
lists then catch the donate and upgrade links inside those apps one step
before they would lead out of scope.

## 7. The five failure classes and where each one is fixed

| Class | What it looks like in the trajectory | Fix in this agent | Flag |
|---|---|---|---|
| `grounding` | tap lands on no element, or the screen does not change | index grounding in code | `grounding: index` |
| `too_early` | effect only visible after an extra wait | wait until stable, second look | `wait_for_stable` |
| `lost_value` | typed text that is not in the goal | notes in the status bar | `status_bar` |
| `wrong_app` | `open_app` for a name off the list, actions blocked outside the allowed apps or on the home screen | allow-list for `open_app`, app scope | always on |
| `false_done` | agent says complete, verifier says fail | check step before done | `verify_before_done` |

The runner computes these signals for every failed run and suggests a class
(`failure.py`). A person confirms it against the recording.

## 8. Evaluation design

* 3 tasks x 3 runs per agent version, one task per difficulty row.
* Identical task parameters for every version (same seeds), so each V1 run has
  a V2 twin on the same task instance.
* Temperature 0 with a fixed seed. Variation between the three runs of a task
  comes from different task parameters, not from sampling noise.
* PASS requires both the agent's own "complete" and AndroidWorld's checker.
  A correct device state without "complete" is a FAIL and is flagged as such
  in the note.
* Infrastructure failures are ERROR rows and never enter a rate.

## 9. Where a future fix should go

*Day 5, "Put the fix in".*

| The failure is... | Put the fix in | In this repo |
|---|---|---|
| a rule that must never be bypassed | Programs | `guardrails.py` |
| a judgement you can state in one sentence | Instructions | a rule in `prompts.py`, or an app tip in `skills/` |
| a fact about one app | Knowledge | `skills/<app>.md`, loaded only while that app is in front |
| perception or pointing ability | Parameters | a different model (config value) |
