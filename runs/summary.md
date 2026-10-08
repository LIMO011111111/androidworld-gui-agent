# Evaluation summary

## Success rate (PASS / runs)

| task | v1_baseline | v2_index | v3_full | v4_tracker | v5_8b | v6_fixes |
|---|---|---|---|---|---|---|
| ContactsAddContact | 2/3 (67 %) | 1/3 (33 %) | 0/3 (0 %) | 0/3 (0 %) | 2/3 (67 %) | 0/3 (0 %) |
| MarkorCreateNote | 2/3 (67 %) | 1/3 (33 %) | 0/3 (0 %) | 1/3 (33 %) | 1/3 (33 %) | 1/3 (33 %) |
| MarkorCreateNoteAndSms | 1/3 (33 %) | 0/3 (0 %) | 0/3 (0 %) | 0/3 (0 %) | 0/3 (0 %) | 0/3 (0 %) |
| **all tasks** | **5/9 (56 %)** | **2/9 (22 %)** | **0/9 (0 %)** | **1/9 (11 %)** | **3/9 (33 %)** | **1/9 (11 %)** |

## Same task instance, side by side

Runs with the same seed have identical task parameters.

| task | seed | v1_baseline | v2_index | v3_full | v4_tracker | v5_8b | v6_fixes |
|---|---|---|---|---|---|---|---|
| ContactsAddContact | 1324763856 | FAIL in 12 steps [grounding] | FAIL in 12 steps [grounding] | FAIL in 11 steps [too_early] | FAIL in 12 steps [grounding] | PASS in 12 steps | FAIL in 12 steps [grounding] |
| ContactsAddContact | 596600690 | PASS in 11 steps | FAIL in 9 steps [lost_value] | FAIL in 12 steps [lost_value] | FAIL in 12 steps [grounding] | PASS in 8 steps | FAIL in 12 steps [grounding] |
| MarkorCreateNote | 1196614525 | FAIL in 9 steps [false_done] | PASS in 9 steps | FAIL in 10 steps [grounding] | FAIL in 16 steps [grounding] | FAIL in 16 steps [grounding] | PASS in 14 steps |
| MarkorCreateNoteAndSms | 3221046986 | FAIL in 18 steps [grounding] | FAIL in 16 steps [lost_value] | FAIL in 18 steps [grounding] | FAIL in 18 steps [grounding] | FAIL in 18 steps [grounding] | FAIL in 18 steps [grounding] |
| MarkorCreateNoteAndSms | 3411394365 | PASS in 16 steps | FAIL in 18 steps [grounding] | FAIL in 18 steps [grounding] | FAIL in 18 steps [grounding] | FAIL in 18 steps [grounding] | FAIL in 18 steps [grounding] |
| MarkorCreateNoteAndSms | 3564688147 | FAIL in 18 steps [grounding] | FAIL in 16 steps [false_done] | FAIL in 18 steps [grounding] | FAIL in 18 steps [grounding] | FAIL in 18 steps [grounding] | FAIL in 17 steps [false_done] |
| ContactsAddContact | 1155463587 | PASS in 11 steps | PASS in 11 steps | FAIL in 12 steps [lost_value] | FAIL in 12 steps [grounding] | FAIL in 12 steps [grounding] | FAIL in 12 steps [grounding] |
| MarkorCreateNote | 1448135622 | PASS in 9 steps | FAIL in 16 steps [grounding] | FAIL in 16 steps [grounding] | PASS in 11 steps | PASS in 11 steps | FAIL in 13 steps [grounding] |
| MarkorCreateNote | 2337133809 | PASS in 11 steps | FAIL in 9 steps [grounding] | FAIL in 16 steps [grounding] | FAIL in 16 steps [grounding] | FAIL in 9 steps [grounding] | FAIL in 14 steps [grounding] |

## Cost

| agent | runs | avg steps | avg steps (PASS only) | avg run time (s) | model time per step (s) | prompt tokens per model call | invalid replies |
|---|---|---|---|---|---|---|---|
| v1_baseline | 9 | 12.8 | 11.6 | 367.8 | 23.5 | 1906 | 0 |
| v2_index | 9 | 12.9 | 10.0 | 136.6 | 6.3 | 1008 | 0 |
| v3_full | 9 | 14.6 | — | 251.0 | 12.7 | 1200 | 0 |
| v4_tracker | 9 | 14.8 | 11.0 | 195.4 | 9.3 | 1051 | 0 |
| v5_8b | 9 | 13.6 | 10.3 | 152.7 | 7.3 | 1009 | 1 |
| v6_fixes | 9 | 14.4 | 14.0 | 300.7 | 14.6 | 1043 | 0 |

## Failure classes (FAIL runs)

A class followed by (?) in log.md is still an unreviewed suggestion.

| agent | FAIL runs | grounding | too_early | lost_value | wrong_app | false_done | reviewed |
|---|---|---|---|---|---|---|---|
| v1_baseline | 4 | 3 | 0 | 0 | 0 | 1 | 0/4 |
| v2_index | 7 | 4 | 0 | 2 | 0 | 1 | 3/7 |
| v3_full | 9 | 6 | 1 | 2 | 0 | 0 | 2/9 |
| v4_tracker | 8 | 8 | 0 | 0 | 0 | 0 | 0/8 |
| v5_8b | 6 | 6 | 0 | 0 | 0 | 0 | 0/6 |
| v6_fixes | 8 | 7 | 0 | 0 | 0 | 1 | 1/8 |

## Runs excluded as ERROR

| agent | task | run | note |
|---|---|---|---|
| v3_full | ContactsAddContact | 2 of 3 | AdbControllerError: Error executing adb command: [adb -P 5037 -s emulator-5554 shell settings get global airplane_mode_on]
Caused by: Command '['~/Library/Android/sdk/platform-tools/adb', '-P', '5037', '-s', 'emulator-5554', 'shell', 'settings', 'get', 'global', 'airplane_mode_on']' returned non-zero exit status 1.
adb stdout: [b'adb: device offline\n']
adb stderr: [None]; recording: no recording could be pulled from the device |
| v3_full | ContactsAddContact | 3 of 3 | AdbControllerError: Error executing adb command: [adb -P 5037 -s emulator-5554 shell whoami]
Caused by: Command '['~/Library/Android/sdk/platform-tools/adb', '-P', '5037', '-s', 'emulator-5554', 'shell', 'whoami']' returned non-zero exit status 1.
adb stdout: [b"adb: device 'emulator-5554' not found\n"]
adb stderr: [None] |
| v3_full | MarkorCreateNote | 1 of 3 | AdbControllerError: Error executing adb command: [adb -P 5037 -s emulator-5554 shell whoami]
Caused by: Command '['~/Library/Android/sdk/platform-tools/adb', '-P', '5037', '-s', 'emulator-5554', 'shell', 'whoami']' returned non-zero exit status 1.
adb stdout: [b"adb: device 'emulator-5554' not found\n"]
adb stderr: [None] |
| v3_full | MarkorCreateNote | 2 of 3 | AdbControllerError: Error executing adb command: [adb -P 5037 -s emulator-5554 shell whoami]
Caused by: Command '['~/Library/Android/sdk/platform-tools/adb', '-P', '5037', '-s', 'emulator-5554', 'shell', 'whoami']' returned non-zero exit status 1.
adb stdout: [b"adb: device 'emulator-5554' not found\n"]
adb stderr: [None] |
| v3_full | MarkorCreateNote | 3 of 3 | AdbControllerError: Error executing adb command: [adb -P 5037 -s emulator-5554 shell whoami]
Caused by: Command '['~/Library/Android/sdk/platform-tools/adb', '-P', '5037', '-s', 'emulator-5554', 'shell', 'whoami']' returned non-zero exit status 1.
adb stdout: [b"adb: device 'emulator-5554' not found\n"]
adb stderr: [None] |
| v3_full | MarkorCreateNoteAndSms | 1 of 3 | AdbControllerError: Error executing adb command: [adb -P 5037 -s emulator-5554 shell whoami]
Caused by: Command '['~/Library/Android/sdk/platform-tools/adb', '-P', '5037', '-s', 'emulator-5554', 'shell', 'whoami']' returned non-zero exit status 1.
adb stdout: [b"adb: device 'emulator-5554' not found\n"]
adb stderr: [None] |
| v3_full | MarkorCreateNoteAndSms | 2 of 3 | AdbControllerError: Error executing adb command: [adb -P 5037 -s emulator-5554 shell whoami]
Caused by: Command '['~/Library/Android/sdk/platform-tools/adb', '-P', '5037', '-s', 'emulator-5554', 'shell', 'whoami']' returned non-zero exit status 1.
adb stdout: [b"adb: device 'emulator-5554' not found\n"]
adb stderr: [None] |
| v3_full | MarkorCreateNoteAndSms | 3 of 3 | AdbControllerError: Error executing adb command: [adb -P 5037 -s emulator-5554 shell whoami]
Caused by: Command '['~/Library/Android/sdk/platform-tools/adb', '-P', '5037', '-s', 'emulator-5554', 'shell', 'whoami']' returned non-zero exit status 1.
adb stdout: [b"adb: device 'emulator-5554' not found\n"]
adb stderr: [None] |
| v3_full | MarkorCreateNote | 1 of 3 | AdbControllerError: Error executing adb command: [adb -P 5037 -s emulator-5554 shell settings get global airplane_mode_on]
Caused by: Command '['~/Library/Android/sdk/platform-tools/adb', '-P', '5037', '-s', 'emulator-5554', 'shell', 'settings', 'get', 'global', 'airplane_mode_on']' returned non-zero exit status 1.
adb stdout: [b'adb: device offline\n']
adb stderr: [None]; recording: no recording could be pulled from the device |
| v3_full | MarkorCreateNote | 2 of 3 | AdbControllerError: Error executing adb command: [adb -P 5037 -s emulator-5554 shell whoami]
Caused by: Command '['~/Library/Android/sdk/platform-tools/adb', '-P', '5037', '-s', 'emulator-5554', 'shell', 'whoami']' returned non-zero exit status 1.
adb stdout: [b"adb: device 'emulator-5554' not found\n"]
adb stderr: [None] |
| v3_full | MarkorCreateNote | 3 of 3 | AdbControllerError: Error executing adb command: [adb -P 5037 -s emulator-5554 shell whoami]
Caused by: Command '['~/Library/Android/sdk/platform-tools/adb', '-P', '5037', '-s', 'emulator-5554', 'shell', 'whoami']' returned non-zero exit status 1.
adb stdout: [b"adb: device 'emulator-5554' not found\n"]
adb stderr: [None] |
