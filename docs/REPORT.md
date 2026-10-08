# GUI agent for AndroidWorld: project report

> All 54 scored runs (6 versions × 3 tasks × 3 runs) are complete; numbers
> are from `runs/summary.md`. The six runs discussed in detail below were
> reviewed against their step screenshots (`screens/step_NN.jpg`) and are
> marked `failure_reviewed = yes` in `runs/log.csv`, with the corrected class.

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
  re-runs and V3 with 4 GB. The last five V3 runs and all V4, V5 and V6
  runs were started by `scripts/finish_v3.sh` / `scripts/run_all.sh`, which
  restart the emulator before every run.
* ERROR runs in total: 11 (all V3, all emulator crashes), listed in
  `runs/summary.md` and excluded from every rate.

## 4. Results

### Success rate (PASS / runs)

| task | V1 screenshot + coordinates | V2 tree + index | V3 V2 + full harness | V4 V2 + goal-value tracker | V5 V2 with the 8B model | V6 V5 + two code fixes |
|---|---|---|---|---|---|---|
| ContactsAddContact | 2/3 | 1/3 | 0/3 | 0/3 | 2/3 | 0/3 |
| MarkorCreateNote | 2/3 | 1/3 | 0/3 | 1/3 | 1/3 | 1/3 |
| MarkorCreateNoteAndSms | 1/3 | 0/3 | 0/3 | 0/3 | 0/3 | 0/3 |
| **all tasks** | **5/9 (56 %)** | **2/9 (22 %)** | **0/9 (0 %)** | **1/9 (11 %)** | **3/9 (33 %)** | **1/9 (11 %)** |

### Same task instance, side by side

| task | seed | V1 | V2 | V3 | V4 | V5 | V6 |
|---|---|---|---|---|---|---|---|
| Contacts | 1155463587 | PASS (11) | PASS (11) | FAIL (12) | FAIL (12) | FAIL (12) | FAIL (12) |
| Contacts | 1324763856 | FAIL (12) | FAIL (12) | FAIL (11) | FAIL (12) | PASS (12) | FAIL (12) |
| Contacts | 596600690 | PASS (11) | FAIL (9) | FAIL (12) | FAIL (12) | PASS (8) | FAIL (12) |
| Markor | 1448135622 | PASS (9) | FAIL (16) | FAIL (16) | PASS (11) | PASS (11) | FAIL (13) |
| Markor | 2337133809 | PASS (11) | FAIL (9) | FAIL (16) | FAIL (16) | FAIL (9) | FAIL (14) |
| Markor | 1196614525 | FAIL (9) | PASS (9) | FAIL (10) | FAIL (16) | FAIL (16) | PASS (14) |
| Note + SMS | 3221046986 | FAIL (18) | FAIL (16) | FAIL (18) | FAIL (18) | FAIL (18) | FAIL (18) |
| Note + SMS | 3411394365 | PASS (16) | FAIL (18) | FAIL (18) | FAIL (18) | FAIL (18) | FAIL (18) |
| Note + SMS | 3564688147 | FAIL (18) | FAIL (16) | FAIL (18) | FAIL (18) | FAIL (18) | FAIL (17) |

(steps used in brackets)

### Cost

| | V1 | V2 | V3 | V4 | V5 | V6 |
|---|---|---|---|---|---|---|
| model time per step | 23.5 s | 6.3 s | 12.7 s | 9.3 s | 7.3 s | 14.6 s* |
| average run time | 368 s | 137 s | 251 s | 195 s | 153 s | 301 s* |
| prompt tokens per model call | 1906 | 1008 | 1200 | 1051 | 1009 | 1043 |
| average steps | 12.8 | 12.9 | 14.6 | 14.8 | 13.6 | 14.4 |
| invalid model replies | 0 | 0 | 0 | 0 | 1 | 0 |

\* V6 uses the same model and almost the same prompt size as V5, yet took
twice as long per step; the first six steps of the first run took 26–76 s
each, later runs 10–15 s. The machine was under other load, so the V6 time
figures are not comparable (section 7d).

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
  only detects *invented* text, not *omitted* text. Confirmed on the
  screenshots: after "Isla" the focus moves to the empty "Last name" field,
  the agent taps "Phone" instead, and saves with "Last name" empty.
  Class corrected to `lost_value` in the log.
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

### Other recurring V2 failure patterns (reviewed on the screenshots for V2 Markor 1 and SMS 1)

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
  app is in front (confirmed: the tap opened the "Add photo" dialog, the
  typing then landed in `com.android.camera`); the agent goes back, but
  the detour costs steps and the surname is again missing. Class corrected
  from the runner's `too_early` to `lost_value` in the log.
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

## 7b. A second failed attempt: V4 (goal-value tracker)

V4 is V2 plus one change, aimed at the most frequent failure (`lost_value`):
code extracts the literal values from the goal (name parts, phone number,
file-name stem, note text), shows every step which of them were not typed
yet, and vetoes "complete" while one was never typed (no model call). The
change is in `gui_agent/goal_values.py`, config `configs/v4_tracker.json`.
Result: **1/9** (V2: 2/9), at 9.3 s per step (V2: 6.3 s).

* **The code veto never fired.** In no V4 run did the agent say "complete"
  with a value missing. Its only "complete" (Markor run 1) had every value
  typed, and that run passed, on a seed where V2 failed.
* **The extra prompt text changed behaviour in ways we did not intend:**
  * **Contacts, all 3 runs:** the agent goes home and then presses "back"
    eleven times on the home screen, never opening the app. Its logged
    thoughts (run 1) never mention the tracker. Every step says "the
    Contacts app is not visible here, I should navigate back to find it".
    It looks for the app on screen and forgets the `open_app` action. V2
    made the same mistake but then *tapped* the search bar. Our home-screen
    guardrail blocked that tap with the message "open the app with
    open_app", and V2 obeyed in the next step. In V4 the agent picked "back"
    instead of a tap, so the guardrail never spoke, and without a "screen
    did not change" hint nothing told it that "back" did nothing. V2's
    Contacts success thus depended on a guardrail *message*. Why the
    4B model picked "back" instead of the tap is not visible in the logs; the
    tracker block is the only prompt difference to V2.
  * **Markor runs 2 and 3, SMS runs 1 and 2:** the dialog's extension field
    shows ".md" because Markor remembers the last type, but the goal wants
    ".txt". The tracker's hint ("the extension goes into the extension
    field") made the agent go for that field, which is correct. But it
    *taps* the field 10–15 times instead of typing into it. Without V3's
    "no effect" feedback it never notices, and the budget runs out. In V2 the
    agent had simply typed "name.txt" into the name field.
  * **SMS run 3:** the device state was correct (note created, SMS sent),
    but the agent never said "complete". This is the same miss as in V2.
* **Lesson:** for a 4B model the prompt is not a neutral place to put
  information. One extra block of correct, helpful text came with two of
  three tasks falling into degenerate loops. The loops themselves come from
  missing feedback: the agent never learns that "back" or a tap changed
  nothing. A clean next experiment would keep the code
  veto and drop the prompt block (veto only), to separate the two effects.

## 7c. A bigger model: V5 (V2 with qwen3-vl 8B)

V5 is V2 with exactly one change: `qwen3-vl:8b-instruct` (Q4_K_M, 6.1 GB)
instead of the 4B model. Config `configs/v5_8b.json`. Result: **3/9**
(V2 with 4B: 2/9), at 7.3 s per step (4B: 6.3 s) and the same token count,
so the bigger model costs only 16 % more time on this machine.

* **The surname problem is gone.** The 8B model typed first name, last
  name and number in all three Contacts runs (the 4B model dropped the
  surname in 5 of 6 V2/V3 runs). Two Contacts runs pass; the third fails
  only because the agent tapped the photo area, wandered into "Add photo"
  and ran out of budget one step before the number.
* **The Markor extension field now blocks the 8B model too.** In Note+SMS
  runs 1 and 2 the agent taps the ".md" extension field 6 and 14 times
  without typing into it. The 4B model did the same in V4. This is a UI
  interaction the model family does not know how to do (replace the
  prefilled text of a field).
* **"Done" is still not said.** Markor run 3 and Note+SMS run 3 end with
  the correct device state and no "complete"; in run 3 the agent even opens
  a Reload menu twice. Note+SMS run 1 reaches the SMS app with the right
  number and text and gets partial credit 0.5, then the budget ends.
* **Reading:** model size fixed one failure class (`lost_value` on names)
  and left the two others (extension field, never saying "done") untouched.
  Those are interaction and termination problems, not knowledge problems.

## 7d. Two targeted code fixes: V6 (V5 + replace prefilled text + done hint)

V6 is V5 (8B model, V2 settings) plus two code changes aimed at the two
patterns that survived every version: (1) `input_text` into a field that
already holds text other than its hint clears the field first (the
extension-field problem); (2) once every goal value has been typed and a
save/send button was pressed, the history line of that step asks the model
to reply "complete" if the goal is done (the never-said-done problem). No
tracker block, no veto (both hurt in V4). Config `configs/v6_fixes.json`.
Result: **1/9** (V5: 3/9).

* **Neither fix reached the failing runs.** The extension field is a
  *tap* loop, not a typing problem: in Note+SMS runs 1 and 2 the agent taps
  the ".md" field 8 and 14 times and never calls `input_text` on it, so the
  clearing rule has nothing to clear. The done hint fired exactly once
  (Note+SMS run 3, after the "SMS" button); the agent pressed the button
  again, went home and then said "complete", with the checker at 0.5. On
  the screenshots the SMS shows as sent after the first tap and the second
  tap hits an empty field; which half the checker rejected is not visible
  on screen. Class set to `false_done` in the log. On Markor "Save" the hint never fired, because we gated
  it on a visible screen change, and Markor's Save changes nothing: the
  same assumption that broke V3, repeated by us in V6.
* **Markor run 3 passed** on the seed where V5 reached the correct state
  and never said "done": this time the agent said "complete" one step
  after Save. Whether the hint played a role is not visible in the log (it
  did not fire); one run is not evidence either way.
* **New loops appeared.** Markor runs 1 and 2 tap "Create a new file or
  folder" 6 and 7 times without effect and then type the full file name
  including the extension into the name field (`…yacht.md`, `….txt` with
  the ".md" field still set) and report "complete": FAIL. Contacts run 2
  presses "back" three times and "Create contact" twice without effect.
  Contacts run 3 reaches the correct state at step 12 of 12, so the hint
  would have come one step too late.
* **Run-to-run variance.** V5 and V6 use the same model, the same seeds
  and temperature 0, and the V6 code changes do not touch the Contacts flow
  until a value is typed; still Contacts went from 2/3 to 0/3. The
  emulator's timing changes the tree the model sees, and the small model
  reacts to every such difference. Three runs per task cannot separate a
  code effect from this noise.
* **Cost caveat:** the 14.6 s per step is not a property of V6. The first
  run's early steps took up to 76 s with an idle emulator, which points to
  other load on the laptop; later runs were at 10–15 s. A clean cost
  comparison would need a re-run.
* **Lesson:** a code fix only helps if the failing trajectories actually
  pass through it. Both V6 fixes were written from the logs of V4/V5 and
  both were gated on a condition (an `input_text` call; a visible change)
  that the failing runs do not meet. Reading the trajectories more closely
  before coding would have shown that.

## 8. Lessons

1. On a 4B local model, *where* grounding happens matters more than prompt
   wording: moving it into code made each step 3.7× faster (each run 2.7×)
   but exposed a different weakness (lost values).
2. Every safety mechanism encodes an assumption about the UI. The V3 check
   step and loop guard failed precisely where that assumption (visible effect)
   did not hold, and V3 went from 2/9 to 0/9 at twice the cost per step.
3. For a 4B model, extra prompt text is an intervention of its own: V4's
   correct, code-generated hint came with new loops, while its code veto
   never needed to fire.
4. Doubling the model (V5) fixed the lost surnames at +16 % time per step,
   but not the extension-field loop or the missing "done": those need
   code, not parameters.
5. Three runs per task are enough to find failure patterns, not to rank
   versions: the trajectories, not the success rates, carry the findings.
   V5 → V6 shows the scale of the noise: same model, same seeds, no code on
   the Contacts path, and Contacts moved from 2/3 to 0/3.
6. A targeted code fix is only as good as the condition it fires on. Both
   V6 fixes were built from the logs and both missed the failing runs,
   one of them because we repeated V3's "visible change" assumption.

## 9. How to reproduce

`README.md`, section "Quick start" (`scripts/setup_mac.sh`, then
`python run_eval.py --config configs/<version>.json`, then
`python summarize.py`). Repository: private GitHub repo
`androidworld-gui-agent`, commit `dd068e2` (final content), see `git log` for later edits.
