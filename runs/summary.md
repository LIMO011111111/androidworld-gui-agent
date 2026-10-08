# Evaluation summary

## Success rate (PASS / runs)

| task | v1_baseline | v2_index |
|---|---|---|
| ContactsAddContact | 1/3 (33 %) | 1/3 (33 %) |
| MarkorCreateNote | 2/3 (67 %) | 1/3 (33 %) |
| MarkorCreateNoteAndSms | 1/3 (33 %) | 0/1 (0 %) |
| **all tasks** | **4/9 (44 %)** | **2/7 (29 %)** |

## Same task instance, side by side

Runs with the same seed have identical task parameters.

| task | seed | v1_baseline | v2_index |
|---|---|---|---|
| ContactsAddContact | 1155463587 | FAIL in 10 steps [grounding] | PASS in 11 steps |
| ContactsAddContact | 1324763856 | FAIL in 12 steps [grounding] | FAIL in 12 steps [grounding] |
| ContactsAddContact | 596600690 | PASS in 11 steps | FAIL in 9 steps [false_done] |
| MarkorCreateNote | 1448135622 | PASS in 13 steps | FAIL in 16 steps [grounding] |
| MarkorCreateNote | 2337133809 | PASS in 16 steps | FAIL in 9 steps [grounding] |
| MarkorCreateNote | 1196614525 | FAIL in 9 steps [false_done] | PASS in 9 steps |
| MarkorCreateNoteAndSms | 3221046986 | FAIL in 18 steps [grounding] | FAIL in 16 steps [grounding] |
| MarkorCreateNoteAndSms | 3411394365 | PASS in 16 steps | — |
| MarkorCreateNoteAndSms | 3564688147 | FAIL in 18 steps [grounding] | — |

## Cost

| agent | runs | avg steps | avg steps (PASS only) | avg run time (s) | model time per step (s) | prompt tokens per model call | invalid replies |
|---|---|---|---|---|---|---|---|
| v1_baseline | 9 | 13.7 | 14.0 | 392.8 | 22.3 | 1907 | 0 |
| v2_index | 7 | 11.7 | 10.0 | 102.6 | 4.7 | 981 | 0 |

## Failure classes (FAIL runs)

A class followed by (?) in log.md is still an unreviewed suggestion.

| agent | FAIL runs | grounding | too_early | lost_value | wrong_app | false_done | reviewed |
|---|---|---|---|---|---|---|---|
| v1_baseline | 5 | 4 | 0 | 0 | 0 | 1 | 0/5 |
| v2_index | 5 | 4 | 0 | 0 | 0 | 1 | 0/5 |

## Runs excluded as ERROR

| agent | task | run | note |
|---|---|---|---|
| v2_index | MarkorCreateNoteAndSms | 2 of 3 | AdbControllerError: Error executing adb command: [adb -P 5037 -s emulator-5554 shell settings get global airplane_mode_on]
Caused by: Command '['~/Library/Android/sdk/platform-tools/adb', '-P', '5037', '-s', 'emulator-5554', 'shell', 'settings', 'get', 'global', 'airplane_mode_on']' returned non-zero exit status 1.
adb stdout: [b"adb: device 'emulator-5554' not found\n"]
adb stderr: [None]; recording: screenrecord exited at once: * daemon not running; starting now at tcp:5037
* daemon started successfully
adb: device offline |
| v2_index | MarkorCreateNoteAndSms | 3 of 3 | AdbControllerError: Error executing adb command: [adb -P 5037 -s emulator-5554 shell whoami]
Caused by: Command '['~/Library/Android/sdk/platform-tools/adb', '-P', '5037', '-s', 'emulator-5554', 'shell', 'whoami']' returned non-zero exit status 1.
adb stdout: [b"adb: device 'emulator-5554' not found\n"]
adb stderr: [None] |
