# Run log

One row per run. `failure_class` is a suggestion until
`failure_reviewed` is set to `yes` in log.csv after watching the recording.

| agent | task | run | model | observation | grounding | steps (budget) | verifier | failure_class | recording | note |
|---|---|---|---|---|---|---|---|---|---|---|
| v2_index | ContactsAddContact | 1 of 1 | qwen3-vl:4b-instruct (Q4_K_M, ollama) | tree | index | 10 (12) | FAIL | wrong_app (?) | v2_index/ContactsAddContact/run1_20261007-154906/recording.mp4 | 1 action(s) blocked outside the allowed apps or on the home screen; 3 action(s) did not change the screen; agent reported complete, verifier says fail |
