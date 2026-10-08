# Presentation outline (about 10 minutes, 10 slides)

All numbers from `runs/summary.md` (27 scored runs).

1. **Title.** GUI agent for AndroidWorld: what a 4B local model can and cannot do on a phone.
2. **Setup in one picture.** MacBook Air M4 → Android emulator (Pixel 6, API 33) → our agent (`step()`) → qwen3-vl 4B via Ollama. Three tasks: Contacts (warm-up), Markor note (real work), note + SMS (multi-app).
3. **Agent design.** One step = observe → prompt → 1 model call → parse → resolve to pixels → guardrails → execute → log. Context: current screen + one code-written line per past step.
4. **Guardrails in code.** Step budget = complexity × 10. Payment ban = closed app list + hit-test of every tap + card/IBAN check on typed text. Point out that this is not a prompt rule.
5. **Three versions, one change at a time.** V1 screenshot + coordinates → V2 tree + index (grounding moves into code) → V3 + harness (stable-screen wait, no-effect hint, loop guard, check before done).
6. **Results table.** Success 5/9 → 2/9 → 0/9. Model time per step 23.5 s → 6.3 s → 12.7 s. Tokens 1906 → 1008 → 1200. Message: V2 is 3.7× faster per step, not more successful.
7. **Failure analysis (live video clip).** V2 Contacts run 3, "Isla Martin": the agent types "Isla", skips "Last name", saves and says done → `lost_value`. The same pattern appears in 2 scored V2 runs and all 3 V3 runs, and the V3 check step accepts it; V1 never made it.
8. **Failure patterns overview.** V1: pointing (taps that change nothing). V2: lost values (surname, file extension in the wrong field), and a correct state without saying "done".
9. **Failed attempt: V3.** The check step rejects a correct note ("not saved") because Markor autosaves; the loop guard and "no effect" hint make the agent think saving failed, so all 3 SMS runs burn their budget on detours (Share menu, wrong messaging app). Lesson: every safety net encodes an assumption about the UI.
10. **Lessons and what we would do next.** Grounding in code > prompt rules; verify state from the app's data (file list, contacts DB), not from the screen; 3 runs find patterns, not rankings. Plus honest limits: emulator crashes, replaced runs listed in `log_replaced.csv`.

Backup slides: replaced-runs rule, per-seed side-by-side table, payment-ban code excerpt.
