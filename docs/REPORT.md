# GUI agent for AndroidWorld: project report

> All 27 scored runs (3 versions × 3 tasks × 3 runs) are complete; numbers
> are from `runs/summary.md`. Every place marked **[check video]** is a
> reading of the trajectory log that a team member still has to confirm
> against the recording before submission.

## 1. Use case and tasks

| level | task | why this task |
|---|---|---|
| Warm-up | `ContactsAddContact` | One app and three fields: it isolates basic grounding (find the right field, type the right value). |
| Real work | `MarkorCreateNote` | A dialog with a separate extension field, a type spinner and an editor that saves on its own: realistic UI friction. |
| Multi-app and memory | `MarkorCreateNoteAndSms` | Two apps; the note text has to be carried from Markor into Simple SMS Messenger, so a value must survive an app switch. |

## 2. Agent design

One class, `gui_agent.agent.GuiAgent`, subclasses AndroidWorld's
`EnvironmentInteractingAgent` and implements a single `step(goal)`. Each step:
observe, build the prompt, call the model once, parse, resolve the action to
pixels, run the guardrails, execute, record the effect.

* **Model:** `qwen3-vl:4b-instruct`, 4.4B parameters, Q4_K_M, digest
  `ee4b975b58c1`, served locally by Ollama 0.35.1; temperature 0,
  JSON-schema constrained output.
* **Observation:** V1 sends the screenshot only. V2 and V3 send the
  accessibility tree as one text line per element, with the screenshot only as
  a fallback when the tree is empty.
* **Grounding:** V1 lets the model output coordinates on a 0–1000 grid.
  V2 and V3 let the model name an element index, and our code turns it into
  the element's centre pixel. A wrong tap is therefore a bug we can find in
  the log, not a guess by the model.
* **Context:** the prompt is rebuilt every step and holds only the current
  screen plus one code-written line per past step ("3. click [5] Save ->
  screen did NOT change"). It never grows as a chat.
* **Harness (V3 only):** wait until the screen is stable, tell the model when
  an action had no effect, loop guard (block a third identical no-effect
  action), status bar with scratch notes, and a check step before "done".
* **Guardrails (all versions, in code, not in the prompt):** step budget =
  AndroidWorld's `complexity × 10`. Payments are banned completely: the agent
  may act only inside a closed list of payment-free apps, every tap is
  hit-tested against the tree, and typed text is checked for card and IBAN
  patterns. Details: `docs/DESIGN.md`, `gui_agent/guardrails.py`.

## 3. Evaluation setup

* 3 runs per task and version; task parameters from AndroidWorld's own seed
  formula with base seed 30, so run *n* of V1, V2 and V3 is the **same task
  instance**.
* Machine: MacBook Air M4 13", 16 GB RAM. Emulator: Pixel 6 profile,
  Android 13 (API 33), arm64.
* PASS = the agent reported "complete" **and** AndroidWorld's checker
  returned 1.0. A correct device state without "complete" is a FAIL.
* Every run is screen-recorded (`recording.mp4`) and has a step-by-step page
  (`trajectory.html`) with one screenshot per step.
* **Replaced runs (transparency):** the emulator crashed several times on
  this machine. Runs that ended as ERROR (crash) or whose recording was
  missing or incomplete were re-run with the same seed *before* any analysis.
  The rule was fixed in advance and applied regardless of the result: two of
  the five replaced runs were PASSes. The originals are kept in
  `runs/log_replaced.csv`. ERROR rows are never counted in a rate.
* **Known confound:** the first V1/V2 batch ran with 2 GB emulator RAM, the
  re-runs and V3 with 4 GB. The last five V3 runs were started by
  `scripts/finish_v3.sh`, which restarts the emulator before every run.
* ERROR runs in total: 11 (all V3, all emulator crashes), listed in
  `runs/summary.md` and excluded from every rate.

## 4. Results

### Success rate (PASS / runs)

| task | V1 screenshot + coordinates | V2 tree + index | V3 V2 + full harness |
|---|---|---|---|
| ContactsAddContact | 2/3 | 1/3 | 0/3 |
| MarkorCreateNote | 2/3 | 1/3 | 0/3 |
| MarkorCreateNoteAndSms | 1/3 | 0/3 | 0/3 |
| **all tasks** | **5/9 (56 %)** | **2/9 (22 %)** | **0/9 (0 %)** |

### Same task instance, side by side

| task | seed | V1 | V2 | V3 |
|---|---|---|---|---|
| Contacts | 1155463587 | PASS (11) | PASS (11) | FAIL (12) |
| Contacts | 1324763856 | FAIL (12) | FAIL (12) | FAIL (11) |
| Contacts | 596600690 | PASS (11) | FAIL (9) | FAIL (12) |
| Markor | 1448135622 | PASS (9) | FAIL (16) | FAIL (16) |
| Markor | 2337133809 | PASS (11) | FAIL (9) | FAIL (16) |
| Markor | 1196614525 | FAIL (9) | PASS (9) | FAIL (10) |
| Note + SMS | 3221046986 | FAIL (18) | FAIL (16) | FAIL (18) |
| Note + SMS | 3411394365 | PASS (16) | FAIL (18) | FAIL (18) |
| Note + SMS | 3564688147 | FAIL (18) | FAIL (16) | FAIL (18) |

(steps used in brackets)

### Cost

| | V1 | V2 | V3 |
|---|---|---|---|
| model time per step | 23.5 s | 6.3 s | 12.7 s |
| average run time | 368 s | 137 s | 251 s |
| prompt tokens per model call | 1906 | 1008 | 1200 |
| average steps | 12.8 | 12.9 | 14.6 |
| invalid model replies | 0 | 0 | 0 |

With 3 runs per task the success-rate differences are within noise. One
changed run moves a task by 33 points. The cost differences are large, but
note the emulator-RAM confound (section 3) when comparing them.

## 5. Failure analysis in depth: V2, ContactsAddContact, run 3

* **Goal:** "Create a new contact for Isla Martin. Their number is
  +15256606183."
* **What happened:**
  1. Steps 1–4: the agent opens Contacts and taps "Create contact". Correct.
  2. Step 5: it types `Isla` into `[7] EditText "First name"`. Correct.
  3. Step 6: it taps `[10] EditText "Phone"` and **skips "Last name"**
     entirely. It types the number and saves (steps 7–8).
  4. Step 9: it reports "complete". The checker finds a contact "Isla"
     without the surname and returns FAIL.
* **Failure class:** `lost_value`. A value from the goal ("Martin") never
  reached the device. The symptom is `false_done`, but the root cause is
  the lost value. Our automatic classifier suggested `false_done` because it
  only detects *invented* text, not *omitted* text. **[check video]**
* **Evidence:** in the trajectory, the typed texts are `Isla` and
  `+15256606183` only, and no action targets element `[8] "Last name"`.
* **Not a one-off:** the same omission appears in the V2 setup run before the evaluation (Hugo
  Pereira, "Pereira" missing), in V2 run 2 (Mariam Chen, "Chen" missing) and
  in **all three V3 Contacts runs** (Pereira, Chen, Martin missing). V1 typed
  both names in every Contacts run.
* **Root cause in one sentence:** with a text list of fields, the small model
  treats "the name" as done after the first name field and nothing on the
  screen contradicts it. In the screenshot, the empty "Last name" field
  directly below is visually obvious.

### Other recurring V2 failure patterns **[check video]**

| pattern | runs | suggested class |
|---|---|---|
| Correct device state but never says "complete" (Markor 1: taps "Save" 5×, which shows no visible effect; SMS 2: spends the remaining steps elsewhere) | V2 Markor 1, V2 SMS 2 | not one of the five cleanly; nearest is `grounding` (no-effect loop) |
| Full file name incl. extension typed into the name field, although the extension is a separate field → wrong file name | V2 Markor 2, V2 SMS 1 and V2 SMS 3 (the two SMS runs got partial score 0.5) | `lost_value` |

## 6. Documented improvement: V1 → V2 (observation and grounding)

* **Change:** the screenshot becomes the accessibility tree, and coordinates
  become an element index that our code resolves. Every other setting is
  identical (`configs/v1_baseline.json` vs `configs/v2_index.json`).
* **Why this change:** in V1 the dominant failure was pointing, e.g.
  repeated taps on (768, 86), (500, 300) or (290, 148) that changed nothing.
  Index grounding removes this kind of miss, because the model can only name
  elements that exist (except for the rare pixel fallback).
* **Why in code, not in the prompt:** a prompt rule ("tap precisely") cannot
  make a 4B model locate pixels better. A lookup table can.
* **Before and after, same task instances:**

| | before (V1) | after (V2) |
|---|---|---|
| success rate | 5/9 | 2/9 |
| model time per step | 23.5 s | 6.3 s (3.7× faster) |
| average run time | 368 s | 137 s (2.7× faster, −63 %) |
| prompt tokens per model call | 1906 | 1008 (−47 %) |
| typical failure (our reading of the trajectories) | taps that change nothing (pointing) | values lost or "done" never said |

* **What got worse:** the success rate. Index grounding removed the pointing
  failures; in our reading of the V2 trajectories, values got lost instead
  (hypothesis: the text list hides the spatial layout that shows a second name
  field or a separate extension field). Note: the automatic classifier still
  labels 5 of 7 V2 FAILs `grounding` (mostly no-effect taps on "Save"); these
  labels must be reviewed against the videos. The improvement is real for cost and for the class it
  targeted. It is not an improvement in end-to-end success with this model.

## 7. A failed attempt: V3 (full harness)

V3 adds exactly the mechanisms that should catch V2's failures: a check step
before "done" against lost values, a "no effect" hint and a loop guard
against the Save loop. Result: **0/9**, at twice V2's cost per step
(12.7 s vs 6.3 s), because of the extra stable-screen waits and check calls.

* **The check step does not catch lost values.** In all three V3 Contacts
  runs the surname is missing, the agent reports "complete", and the check
  step (the same 4B model looking at the saved contact) **accepts** it. A
  verifier that is as weak as the actor adds cost, not safety.

* **V3 Markor run 1:** the note is correct. The agent says "complete" in
  step 15, but **our check step rejects it** ("The note has not been
  saved."), because Markor autosaves and the screen never confirms a save.
  In step 16 the agent taps "Save" again and the budget runs out. The safety
  net turned a PASS into a FAIL.
* **V3 Markor run 2:** a detour into Markor's QuickNote screen costs so many
  steps that the budget runs out before the note is finished.
* **V3 Markor run 3:** the agent again types the extension into the name
  field ("final_quick_eagle.md"), then taps "Save" twice without effect. The
  loop guard blocks the next tap three times and ends the run (`loop_abort`).
* **V3 Contacts runs 1 and 3:** after a coordinate tap near the top of the
  form (step 6, x=500 y=150) and typing the first name (step 7), the camera
  app is in front **[check video]**; the agent goes back, but the detour
  costs steps and the surname is again missing.
* **V3 Note + SMS, all three runs:** each note is written, then "Save" shows
  no effect twice, the loop guard blocks further taps, and the agent starts
  looking for another way: Markor's Share menu (run 1 even ends up in Google
  Messages instead of Simple SMS Messenger), reopening the file, Cancel.
  Runs 1 and 3 reach Simple SMS Messenger only at step 17 of 18; run 2 never
  gets there. All three run out of budget. In V2, the agent tapped "Save" once or twice, moved on and
  reached the SMS app by step 9–12. The loop guard and the "no effect" hint
  made the agent believe saving had failed. Positive detail: in V3 SMS run 1
  the agent typed the name and the extension into their separate fields.
* **Lesson:** the harness rules assume that every successful action produces
  a visible change. Markor's autosave violates that assumption, so the
  "no effect" hint, the loop guard and the check step all misfire on "Save".
  The lost-value weakness from V2 remains, because the check step relies on
  the same small model. A useful verifier would read state the UI does not
  show (the file list, the contacts database) or use a stronger model.

## 8. Lessons

1. On a 4B local model, *where* grounding happens matters more than prompt
   wording: moving it into code made each step 3.7× faster (each run 2.7×)
   but exposed a different weakness (lost values).
2. Every safety mechanism encodes an assumption about the UI. The V3 check
   step and loop guard failed precisely where that assumption (visible effect)
   did not hold, and V3 went from 2/9 to 0/9 at twice the cost per step.
3. Three runs per task are enough to find failure patterns, not to rank
   versions: the trajectories, not the success rates, carry the findings.

## 9. How to reproduce

`README.md`, section "Quick start" (`scripts/setup_mac.sh`, then
`python run_eval.py --config configs/<version>.json`, then
`python summarize.py`). Repository: private GitHub repo
`androidworld-gui-agent`, commit `5e1f1a0`.
