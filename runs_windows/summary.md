# Evaluation summary

## Success rate (PASS / runs)

| task | v2_index | v1_baseline | v3_full |
|---|---|---|---|
| ContactsAddContact | 0/3 (0 %) | 3/3 (100 %) | 0/3 (0 %) |
| MarkorCreateNote | 3/3 (100 %) | 2/3 (67 %) | 0/3 (0 %) |
| MarkorCreateNoteAndSms | 0/3 (0 %) | 0/3 (0 %) | 0/3 (0 %) |
| **all tasks** | **3/9 (33 %)** | **5/9 (56 %)** | **0/9 (0 %)** |

## Same task instance, side by side

Runs with the same seed have identical task parameters.

| task | seed | v2_index | v1_baseline | v3_full |
|---|---|---|---|---|
| ContactsAddContact | 1155463587 | FAIL in 10 steps [lost_value] | PASS in 9 steps | FAIL in 12 steps [grounding] |
| ContactsAddContact | 1324763856 | FAIL in 10 steps [lost_value] | PASS in 8 steps | FAIL in 9 steps [lost_value] |
| ContactsAddContact | 596600690 | FAIL in 10 steps [lost_value] | PASS in 9 steps | FAIL in 11 steps [lost_value] |
| MarkorCreateNote | 1448135622 | PASS in 10 steps | PASS in 10 steps | FAIL in 16 steps [grounding] |
| MarkorCreateNote | 2337133809 | PASS in 14 steps | PASS in 11 steps | FAIL in 14 steps [grounding] |
| MarkorCreateNote | 1196614525 | PASS in 11 steps | FAIL in 9 steps [false_done] | FAIL in 10 steps [grounding] |
| MarkorCreateNoteAndSms | 3221046986 | FAIL in 18 steps [grounding] | FAIL in 17 steps [grounding] | FAIL in 18 steps [grounding] |
| MarkorCreateNoteAndSms | 3411394365 | FAIL in 16 steps [lost_value] | FAIL in 18 steps [grounding] | FAIL in 17 steps [grounding] |
| MarkorCreateNoteAndSms | 3564688147 | FAIL in 14 steps [false_done] | FAIL in 18 steps [grounding] | FAIL in 18 steps [grounding] |

## Cost

| agent | runs | avg steps | avg steps (PASS only) | avg run time (s) | model time per step (s) | prompt tokens per model call | invalid replies |
|---|---|---|---|---|---|---|---|
| v2_index | 9 | 12.6 | 11.7 | 412.6 | 27.9 | 1069 | 0 |
| v1_baseline | 9 | 12.1 | 9.4 | 1150.2 | 89.8 | 1905 | 0 |
| v3_full | 9 | 13.9 | — | 468.1 | 27.7 | 1120 | 0 |

## Failure classes (FAIL runs)

A class followed by (?) in log.md is still an unreviewed suggestion.

| agent | FAIL runs | grounding | too_early | lost_value | wrong_app | false_done | reviewed |
|---|---|---|---|---|---|---|---|
| v2_index | 6 | 1 | 0 | 4 | 0 | 1 | 5/6 |
| v1_baseline | 4 | 3 | 0 | 0 | 0 | 1 | 0/4 |
| v3_full | 9 | 7 | 0 | 2 | 0 | 0 | 3/9 |
