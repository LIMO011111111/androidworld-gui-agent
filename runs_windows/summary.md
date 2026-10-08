> **Machine:** Windows 11 laptop (CPU only), 08.10.2026, Ollama 0.40.0, model
> `qwen3-vl:4b-instruct` Q4_K_M digest `ef33995bb2ac`, emulator Pixel 6 / API 33 x86_64,
> 4 GB emulator RAM throughout. 27 scored runs, 0 ERROR (one run repeated after the
> emulator process was killed by the OS; no replaced run is counted twice).
> **Code:** the 08.10. morning snapshot of this repository, which predates commit
> `43ed042` by two small refinements (home-screen taps logged under their own rule,
> focus-only clicks not counted as "no effect"). Configs identical to `configs/`.
> The Mac evaluation lives in `runs/`; the two are not merged because the model
> digests differ (different Ollama builds), so they are two models by the project rule.

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
| ContactsAddContact | 1155463587 | FAIL in 10 steps [wrong_app] | PASS in 9 steps | FAIL in 12 steps [wrong_app] |
| ContactsAddContact | 1324763856 | FAIL in 10 steps [wrong_app] | PASS in 8 steps | FAIL in 9 steps [grounding] |
| ContactsAddContact | 596600690 | FAIL in 10 steps [wrong_app] | PASS in 9 steps | FAIL in 11 steps [grounding] |
| MarkorCreateNote | 1448135622 | PASS in 10 steps | PASS in 10 steps | FAIL in 16 steps [grounding] |
| MarkorCreateNote | 2337133809 | PASS in 14 steps | PASS in 11 steps | FAIL in 14 steps [grounding] |
| MarkorCreateNote | 1196614525 | PASS in 11 steps | FAIL in 9 steps [false_done] | FAIL in 10 steps [grounding] |
| MarkorCreateNoteAndSms | 3221046986 | FAIL in 18 steps [grounding] | FAIL in 17 steps [grounding] | FAIL in 18 steps [grounding] |
| MarkorCreateNoteAndSms | 3411394365 | FAIL in 16 steps [wrong_app] | FAIL in 18 steps [grounding] | FAIL in 17 steps [grounding] |
| MarkorCreateNoteAndSms | 3564688147 | FAIL in 14 steps [wrong_app] | FAIL in 18 steps [grounding] | FAIL in 18 steps [grounding] |

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
| v2_index | 6 | 1 | 0 | 0 | 5 | 0 | 0/6 |
| v1_baseline | 4 | 3 | 0 | 0 | 0 | 1 | 0/4 |
| v3_full | 9 | 8 | 0 | 0 | 1 | 0 | 0/9 |
