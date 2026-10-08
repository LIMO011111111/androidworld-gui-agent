# Evaluationsläufe AndroidWorld-GUI-Agent, Windows-Laptop, 2026-10-08

## Rahmen

- **Datum:** 2026-10-08, Start der Läufe ca. 12:15 Uhr
- **Rechner:** Windows 11 Pro (10.0.26200), Intel i7-1165G7, 32 GB RAM, keine GPU
- **Emulator:** AVD "AndroidWorldAvd", Pixel 6, x86_64, API 33, Bildschirm 1080x2400, gestartet mit `-no-snapshot -grpc 8554`
- **Modell:** qwen3-vl:4b-instruct (4.4B, Q4_K_M), Digest `ef33995bb2ac` (aus meta.json des Setup-Laufs und doctor.py), Backend Ollama, temperature 0.0, seed 42, num_ctx 8192
- **Ollama-Version:** 0.40.0
- **Python:** 3.11.15 in `.venv`, AndroidWorld mit 116 Tasks in der Registry
- **Agent-Version:** 1.0.0
- **Tasks:** ContactsAddContact, MarkorCreateNote, MarkorCreateNoteAndSms, je 3 Läufe, Basis-Seed 30
- **Hinweis:** `ollama list` zeigt zwei Einträge namens qwen3-vl:4b-instruct (IDs 6bf7b924e48a und ef33995bb2ac). doctor.py und der Setup-Lauf verwenden ef33995bb2ac.

## Vorab-Checks

- 12:15: `adb devices` → emulator-5554 device; `getprop sys.boot_completed` → 1 (Emulator lief bereits, kein Neustart nötig)
- 12:15: `.venv\Scripts\python.exe scripts\doctor.py` → alle Zeilen ok, keine Warnung zu fehlenden Apps. Tree-Prompt 45,4 s (729 Prompt-Tokens), Screenshot-Prompt 113,8 s (1781 Prompt-Tokens).

## Befehle in Reihenfolge

Alle Befehle im Repo-Ordner `androidworld-gui-agent`, vorher `$env:PYTHONIOENCODING="utf-8"`. Konsolenausgaben liegen unter `Praesentation\notes\console`.

1. 12:15 `adb devices`, `adb shell getprop sys.boot_completed`
2. 12:15 `.venv\Scripts\python.exe scripts\doctor.py`
3. 12:15 `.venv\Scripts\python.exe run_eval.py --config configs\v2_index.json` (Konsole: console\v2_index.log) → fertig 13:17, 3 PASS / 6 FAIL / 0 ERROR, Dauer ca. 1 h 02 min
4. 13:18 `.venv\Scripts\python.exe run_eval.py --config configs\v1_baseline.json` (Konsole: console\v1_baseline.log) → abgebrochen ca. 15:05 bei Lauf 7 von 9 (Speichermangel), 6 Läufe fertig: 5 PASS / 1 FAIL
5. 15:28 `pwsh -File scripts\start_emulator.ps1` (Emulator-Neustart)
6. 15:28 `.venv\Scripts\python.exe run_eval.py --config configs\v1_baseline.json --tasks MarkorCreateNoteAndSms` (Konsole: console\v1_baseline_sms.log) → fertig 16:55, 0 PASS / 3 FAIL / 0 ERROR; V1 gesamt 5 PASS / 4 FAIL / 0 ERROR
7. 16:55 `.venv\Scripts\python.exe run_eval.py --config configs\v3_full.json` (Konsole: console\v3_full.log) → fertig 18:06, 0 PASS / 9 FAIL / 0 ERROR, Dauer 1 h 11 min
8. 18:07 `.venv\Scripts\python.exe summarize.py` → runs\summary.md

## Läufe

Spalten: Version · Task · Run · Seed · Steps (Budget) · Ergebnis · vorgeschlagene Fehlerklasse · Dauer · Lauf-Ordner (relativ zu `androidworld-gui-agent\runs`) · was passiert ist

| Version | Task | Run | Seed | Steps (Budget) | Ergebnis | Fehlerklasse (Vorschlag) | Dauer | Lauf-Ordner | Was passiert ist |
|---|---|---|---|---|---|---|---|---|---|
| v2_index | ContactsAddContact | 1 | 1155463587 | 10 (12) | FAIL | wrong_app | 6 min 01 s | `v2_index\ContactsAddContact\run1_20261008-121534` | Blockierter Tap auf Home-Screen (Search), dann open_app contacts; Vorname "Hugo" per Koordinate eingetippt (x=500 y=384), Nachname "Pereira" nie eingegeben; Telefonnummer in Phone-Feld, Save, dann "complete" gemeldet; Checker sagt FAIL. 1 Aktion ohne Bildschirmänderung. |
| v2_index | ContactsAddContact | 2 | 1324763856 | 10 (12) | FAIL | wrong_app | 6 min 07 s | `v2_index\ContactsAddContact\run2_20261008-122136` | Gleicher Ablauf wie Run 1: blockierter Tap auf Home-Screen (Search), open_app contacts, wait (90 s), Create contact; Vorname "Mariam" per Index in First name, Nachname "Chen" nie eingegeben; Nummer ins Phone-Feld, Save, "complete" gemeldet; Checker FAIL. 1 Aktion ohne Bildschirmänderung. |
| v2_index | ContactsAddContact | 3 | 596600690 | 10 (12) | FAIL | wrong_app | 6 min 49 s | `v2_index\ContactsAddContact\run3_20261008-122743` | Drittes Mal dasselbe Muster: navigate_back statt navigate_home, blockierter Tap auf Home-Screen (Search), open_app contacts, wait (119 s), Create contact; Vorname "Isla" per Koordinate (x=500 y=384), Nachname "Martin" nie eingegeben; Nummer ins Phone-Feld, Save, "complete"; Checker FAIL. |
| v2_index | MarkorCreateNote | 1 | 1448135622 | 10 (16) | PASS | – | 6 min 33 s | `v2_index\MarkorCreateNote\run1_20261008-123432` | Erster PASS. open_app markor, Klick per Koordinate (x=880 y=860, 89 s) auf den Plus-Button, Dateiname per Index ins Feld "my_note" getippt, Klick auf ".md", OK; Notiztext per Koordinate (x=500 y=300, 98 s) eingegeben, zweimal Save, "complete"; Checker PASS. |
| v2_index | MarkorCreateNote | 2 | 2337133809 | 14 (16) | PASS | – | 8 min 24 s | `v2_index\MarkorCreateNote\run2_20261008-124106` | PASS trotz Umweg: Ziel war eine .txt-Datei; Agent klickte dreimal auf das Feld ".md" (Schritt 5 bis 7, ohne Effekt), fand dann den Typ-Spinner und wählte "Plain Text", OK; Text per Koordinate (x=500 y=300, 100 s), zweimal Save, "complete"; Checker PASS. |
| v2_index | MarkorCreateNote | 3 | 1196614525 | 11 (16) | PASS | – | 5 min 39 s | `v2_index\MarkorCreateNote\run3_20261008-124931` | PASS, glattester Lauf: open_app markor, diesmal Plus-Button per Index ([1] ImageButton "Create a new file or folder", 20 s statt 89 s), Dateiname per Index, .md, OK; Text per Koordinate (x=500 y=300, 96 s), dreimal Save, "complete"; Checker PASS. |
| v2_index | MarkorCreateNoteAndSms | 1 | 3221046986 | 18 (18) | FAIL | grounding | 7 min 53 s | `v2_index\MarkorCreateNoteAndSms\run1_20261008-125510` | FAIL mit Teilpunkten 0,50 bei vollem Budget. Markor: dreimal Plus-Button geklickt, Dateiname "fair_ant_XOdi.txt" ins Namensfeld getippt (Dateityp blieb vermutlich .md), Text per Index, Save; dann zurück, Home, open_app simple sms messenger, Nummer eingetragen, Text getippt, zweimal SMS-Button, "complete" im 18. Schritt; Checker FAIL. 4 Aktionen ohne Bildschirmänderung. |
| v2_index | MarkorCreateNoteAndSms | 2 | 3411394365 | 16 (18) | FAIL | wrong_app | 7 min 45 s | `v2_index\MarkorCreateNoteAndSms\run2_20261008-130304` | FAIL mit Teilpunkten 0,50. Blockierter Tap auf Home-Screen (Search), open_app markor, Dateiname "2023_06_01_fierce_violin.txt" ins Namensfeld (Dateityp nicht umgestellt), Text per Koordinate (100 s), Save; zweimal zurück, open_app simple sms messenger, Nummer, Text, SMS-Button einmal, "complete" bei Schritt 16; Checker FAIL. |
| v2_index | MarkorCreateNoteAndSms | 3 | 3564688147 | 14 (18) | FAIL | wrong_app | 6 min 38 s | `v2_index\MarkorCreateNoteAndSms\run3_20261008-131049` | FAIL mit Teilpunkten 0,50, kürzester SMS-Lauf. Blockierter Tap auf Home-Screen (Search), open_app markor, Dateiname "lively_goat_LEKc.md" (hier passend .md), Text per Koordinate (88 s), Save; direkt open_app simple sms messenger, Nummer, Text, SMS einmal, "complete" bei Schritt 14; Checker FAIL. |
| v1_baseline | ContactsAddContact | 1 | 1155463587 | 9 (12) | PASS | – | 14 min 46 s | `v1_baseline\ContactsAddContact\run1_20261008-131825` | PASS, ohne Umwege: open_app contacts, wait, Klick auf Plus-Button (x=860 y=835), Vorname "Hugo" (y=384) und Nachname "Pereira" (y=468) getrennt eingetippt, Klick ins Nummernfeld (y=610), Nummer, Klick auf Save (x=768 y=86), "complete"; Checker PASS. Jeder Schritt 83 bis 112 s. |
| v1_baseline | ContactsAddContact | 2 | 1324763856 | 8 (12) | PASS | – | 10 min 58 s | `v1_baseline\ContactsAddContact\run2_20261008-133312` | PASS, kürzester Lauf bisher: open_app contacts, wait, Plus-Button (x=860 y=835), Vorname "Mariam" (y=384), Nachname "Chen" (y=464), Nummer direkt ins Feld (y=614) ohne vorherigen Klick, Save (x=768 y=86), "complete"; Checker PASS. |
| v1_baseline | ContactsAddContact | 3 | 596600690 | 9 (12) | PASS | – | 13 min 25 s | `v1_baseline\ContactsAddContact\run3_20261008-134410` | PASS, gleiche Koordinatenfolge wie Run 1: open_app contacts, wait, Plus-Button (x=860 y=835), Vorname "Isla" (y=384), Nachname "Martin" (y=464), Klick ins Nummernfeld (y=610), Nummer, Save (x=768 y=86), "complete"; Checker PASS. Schritte 85 bis 105 s. |
| v1_baseline | MarkorCreateNote | 1 | 1448135622 | 10 (16) | PASS | – | 16 min 06 s | `v1_baseline\MarkorCreateNote\run1_20261008-135736` | PASS nach ADB-Timeout beim App-Start (wiederholt, Schritt 1 dann 39 s). Plus-Button (x=880 y=860), Klick ins Namensfeld (x=342 y=399), Dateiname getippt, OK-Button (x=846 y=462), Text per Koordinate (x=500 y=300), dreimal Klick auf Save (x=749 y=86), "complete"; Checker PASS. |
| v1_baseline | MarkorCreateNote | 2 | 2337133809 | 11 (16) | PASS | – | 16 min 48 s | `v1_baseline\MarkorCreateNote\run2_20261008-141343` | PASS bei der .txt-Aufgabe: Plus-Button, Dateiname ohne Endung ins Namensfeld, dann drei Klicks (x=850 y=290, x=499 y=357, x=848 y=632), vermutlich Typ-Dropdown, Auswahl Plain Text und OK; Text per Koordinate, dreimal Save (x=749 y=86), "complete"; Checker PASS. |
| v1_baseline | MarkorCreateNote | 3 | 1196614525 | 9 (16) | FAIL | false_done | 14 min 56 s | `v1_baseline\MarkorCreateNote\run3_20261008-143031` | Erster V1-FAIL: begann mit "scroll up" auf dem Home-Screen, open_app markor, navigate_home, nochmal open_app markor; dann Plus-Button, Dateiname, OK, Text per Koordinate und direkt "complete" ohne Save; Checker FAIL, Fehlerklasse false_done (?). 1 Aktion ohne Bildschirmänderung. |
| v1_baseline | MarkorCreateNoteAndSms | 1 | 3221046986 | 17 (18) | FAIL | grounding | 28 min 09 s | `v1_baseline\MarkorCreateNoteAndSms\run1_20261008-152919` | Wiederholung nach Emulator-Neustart (Original run1_20261008-144527 abgebrochen). FAIL mit Teilpunkten 0,50: Markor-Teil sauber (Name, ".txt" ins Endungsfeld, OK, Text, Save), dann SMS-App, ein Tap ins Leere, Nummer und Text eingetippt, Klick auf x=930 y=600 (vermutlich Senden), "complete" bei Schritt 17; Checker FAIL. 4 Aktionen ohne Bildschirmänderung. |
| v1_baseline | MarkorCreateNoteAndSms | 2 | 3411394365 | 18 (18) | FAIL | grounding | 29 min 47 s | `v1_baseline\MarkorCreateNoteAndSms\run2_20261008-155729` | FAIL mit Teilpunkten 0,50 bei vollem Budget. Markor-Teil in 6 Schritten (Dateiname ohne Endung, Typ .txt nicht gesetzt, Text, Save); SMS-App: fünfmal derselbe Klick auf x=277 y=148 ohne Effekt, dann Nummer, Bestätigen, Text, Senden-Klick, "complete" als 18. Schritt; Checker FAIL. 6 Aktionen ohne Bildschirmänderung. |
| v1_baseline | MarkorCreateNoteAndSms | 3 | 3564688147 | 18 (18) | FAIL | grounding | 27 min 32 s | `v1_baseline\MarkorCreateNoteAndSms\run3_20261008-162717` | FAIL durch Schrittlimit, einziger Lauf des Tages ohne "complete". Markor-Teil in 8 Schritten (Name inkl. .md, drei Klicks im Typ-Dialog, Text, Save); SMS-App: viermal Klick auf x=500 y=300 ohne Effekt, dann Plus-Button, zwei Klicks ins Nummernfeld, Text getippt, letzter Schritt Klick auf Senden-Position, Budget aus; Checker FAIL ohne Teilpunkte. |
| v3_full | ContactsAddContact | 1 | 1155463587 | 12 (12) | FAIL | wrong_app | 5 min 58 s | `v3_full\ContactsAddContact\run1_20261008-165552` | FAIL durch Schrittlimit: blockierter Tap auf Home-Screen, open_app contacts, dann Klick per Koordinate (x=869 y=951) der in ein Untermenü führte, danach 7 Schritte scroll down / "Other tools" ohne Bildschirmänderung, navigate_back, erst im 12. Schritt "Create contact"; Budget aus, Kontakt nie angelegt. |
| v3_full | ContactsAddContact | 2 | 1324763856 | 9 (12) | FAIL | grounding | 4 min 59 s | `v3_full\ContactsAddContact\run2_20261008-170151` | FAIL wie bei V2: navigate_home und navigate_back ohne Effekt, open_app contacts, wait, Create contact per Index, Vorname "Mariam" ins First-name-Feld, Nachname "Chen" nie eingegeben, Nummer, Save, "complete" (Prüfschritt hat es durchgelassen, 45 s); Checker FAIL. |
| v3_full | ContactsAddContact | 3 | 596600690 | 11 (12) | FAIL | grounding | 4 min 29 s | `v3_full\ContactsAddContact\run3_20261008-170650` | FAIL: vier Navigationsschritte (back, home, back, back) ohne Bildschirmänderung, dann open_app contacts, Create contact, Vorname "Isla", Nachname "Martin" nie eingegeben, Nummer, Save, "complete" (Prüfschritt 45 s); Checker FAIL. |
| v3_full | MarkorCreateNote | 1 | 1448135622 | 16 (16) | FAIL | grounding | 9 min 13 s | `v3_full\MarkorCreateNote\run1_20261008-171120` | FAIL durch Schrittlimit, obwohl die Notiz korrekt gespeichert war ("device state was correct, but the agent never reported done"). Nach Name, OK und Text zweimal Save ohne sichtbare Bildschirmänderung, dann zweimal Save vom Loop-Guard geblockt, danach Irrweg über More options / File settings / zurück / Notiz öffnen / Text ins Suchfeld; Budget aus. |
| v3_full | MarkorCreateNote | 2 | 2337133809 | 14 (16) | FAIL | grounding | 6 min 22 s | `v3_full\MarkorCreateNote\run2_20261008-172033` | FAIL durch Loop-Abbruch (neu: stop_reason loop_abort). Bis Schritt 7 sauber per Index (Name inkl. .txt, Spinner Plain Text, OK, Text), dann zweimal Save ohne Bildschirmänderung, zweimal Save geblockt, dreimal Klick auf den Dateinamen ohne Effekt, dritter geblockt, Guard beendet den Lauf; Checker FAIL ohne Teilpunkte. |
| v3_full | MarkorCreateNote | 3 | 1196614525 | 10 (16) | FAIL | grounding | 4 min 42 s | `v3_full\MarkorCreateNote\run3_20261008-172656` | FAIL durch Loop-Abbruch: fünf saubere Index-Schritte (open_app, Plus, Name inkl. .md, OK, Text), dann fünfmal Save hintereinander (2x ohne Bildschirmänderung, 3x vom Loop-Guard geblockt), Guard beendet den Lauf nach Schritt 10; Checker FAIL, state_score 0. |
| v3_full | MarkorCreateNoteAndSms | 1 | 3221046986 | 18 (18) | FAIL | grounding | 8 min 28 s | `v3_full\MarkorCreateNoteAndSms\run1_20261008-173138` | FAIL durch Schrittlimit, Teilpunkte 0,50, SMS-App nie geöffnet. Notiz angelegt (Name, OK, Text), dann Save-Schleife (2x ohne Effekt, 1x geblockt), zurück, nochmal Save, zurück, zweite Datei "fair_ant_XOdi.txt" begonnen, im Typ-Dialog Plain Text / todo.txt / Empty file geklickt, Budget aus. |
| v3_full | MarkorCreateNoteAndSms | 2 | 3411394365 | 17 (18) | FAIL | grounding | 12 min 56 s | `v3_full\MarkorCreateNoteAndSms\run2_20261008-174007` | FAIL durch Loop-Abbruch, SMS-App nie geöffnet. Nach ADB-Timeouts beim Start: wait (110 s), Plus, Dateiname getippt, dann "olin.txt" mitten in den Namen eingefügt (Ergebnis "2023_06_01_fieolin.txtrce_violin"), OK, Text eingegeben, Save-Schleife (2x ohne Effekt, 1x geblockt), dann 4x Klick auf den verstümmelten Dateinamen, Guard bricht ab; Checker FAIL ohne Teilpunkte. |
| v3_full | MarkorCreateNoteAndSms | 3 | 3564688147 | 18 (18) | FAIL | grounding | 13 min 02 s | `v3_full\MarkorCreateNoteAndSms\run3_20261008-175304` | FAIL durch Schrittlimit, SMS-App nie geöffnet. Zwei ADB-Timeouts (App-Start, Texteingabe). Dateiname eingegeben, dann statt OK erneut Plus-Button, Dialog-Chaos: Notiztext ins Namensfeld eines zweiten Dialogs getippt (Datei "IgnorIgnorance is bliss." entstanden), Klicks darauf ohne Effekt, am Ende More options / Share; Checker FAIL ohne Teilpunkte. |

## Vorkommnisse

(ERROR-Läufe, Emulator-Neustarts, Wiederholungen, jeweils mit Uhrzeit und Grund)
- 13:58, V1 MarkorCreateNote Run 1, erster Schritt: ADB-Timeout beim App-Start ("Failed to execute ADB command (try 1 of 3)", "am start -W ... markor" nach 5,0 s abgebrochen, Traceback subprocess.TimeoutExpired). Emulator laut adb devices weiterhin online; AndroidWorld wiederholt den Befehl bis zu dreimal. Lauf wurde nicht abgebrochen, Beobachtung läuft.
- 14:46, V1 MarkorCreateNoteAndSms Run 1, erster Schritt: zweiter ADB-Timeout beim Start von Markor (gleiche Meldung wie 13:58, try 1 of 3). Emulator online, AndroidWorld wiederholt. Beide Timeouts traten beim ersten Markor-Start nach einem Task-Wechsel auf.
- ca. 15:05, V1 MarkorCreateNoteAndSms Run 1 bei Schritt 15 von 18: der run_eval-Prozess wurde von Claude Code beendet, weil der Arbeitsspeicher des Laptops kritisch knapp war (Meldung: "stopped because the system is running low on memory"). Um 15:08 zeigt adb devices kein Gerät mehr, Emulator-Prozess nicht mehr vorhanden, 9,3 GB von 31,7 GB frei. Lauf-Ordner v1_baseline\MarkorCreateNoteAndSms\run1_20261008-144527 ist unvollständig (keine result.json, keine Zeile in log.csv). Der Lauf hatte bis dahin: Markor-Teil erledigt, SMS-App geöffnet, dann 4x Klick auf x=500 y=300 und 1x x=500 y=198. Betroffen: V1 MarkorCreateNoteAndSms Run 1, 2, 3 noch offen. Fertige V1-Läufe (6) sind unberührt.
- 15:28: Emulator-Neustart nach Freigabe durch Bela (pwsh -File scripts\start_emulator.ps1, -no-snapshot -grpc 8554). Grund: Abbruch durch Speichermangel um ca. 15:05. Danach Wiederholung nur der offenen V1-Läufe MarkorCreateNoteAndSms Run 1 bis 3 (--tasks MarkorCreateNoteAndSms).
- 15:57: Wiederholung V1 MarkorCreateNoteAndSms Run 1 fertig (FAIL, regulär beendet). Ordner run1_20261008-152919 ist der gültige Lauf, run1_20261008-144527 bleibt als abgebrochenes Original liegen (ohne result.json, nicht in log.csv).
- 17:41, V3 MarkorCreateNoteAndSms Run 2, erster Schritt: dritter ADB-Timeout beim Start von Markor (try 1 of 3), direkt danach zusätzlich "Failed to execute ADB command (try 1 of 3): [adb -P 5037 start-server]". Emulator laut adb devices online. Beobachtung, ob AndroidWorld den Lauf fortsetzt.
- 17:49: V3 MarkorCreateNoteAndSms Run 2 lief nach den ADB-Timeouts regulär weiter und endete als FAIL (loop_abort), kein ERROR, keine Wiederholung nötig.
- 17:53 und ca. 18:02, V3 MarkorCreateNoteAndSms Run 3: ADB-Timeout beim Markor-Start und ein weiterer bei "adb shell input text Ignorance" (Schritt 12). Lauf lief weiter, FAIL regulär, kein ERROR.
- 18:06: alle 27 Läufe beendet. Insgesamt 0 ERROR, 1 Wiederholung (V1 MarkorCreateNoteAndSms Run 1 nach Speicher-Abbruch), 1 Emulator-Neustart (15:27).

## Auffälligkeiten für die Fehleranalyse

(nur Beobachtungen aus der Konsolenausgabe, keine Interpretation)
- V2 ContactsAddContact Run 1: Agent meldet "status complete", Checker sagt FAIL (Zeile "agent reported complete, verifier says fail"). Nachname wurde nie eingegeben, Save trotzdem gedrückt.
- V2 ContactsAddContact Run 1, Schritt 2: Guardrail-Block, Tap auf Home-Screen-Element [6] FrameLayout "Search" ("BLOCKED: do not tap or type on the home screen"). Danach korrekt open_app contacts.
- V2 ContactsAddContact Run 1, Schritt 7: trotz Tree-Grounding ein input_text per Koordinate (x=500 y=384), result.json zählt pixel_fallback_steps=2. Schritt 8 dann wieder per Index [10] EditText "Phone".
- V2 ContactsAddContact Run 1, Schritt 4: Aktion "wait" direkt nach open_app, 96,0 s Modellzeit; Schritt 7 (input_text per Koordinate) 88,9 s. Übrige Schritte 14 bis 31 s.
- Konsole, mehrfach vor und zwischen den Läufen: "WARNING:absl:Could not get a11y tree, retrying." (vor Run 1 einmal, vor Run 2 dreimal). Läufe liefen danach weiter.
- V2 ContactsAddContact Run 1, Schritt 5: Dialog mit Button "Don’t allow" (Berechtigungsabfrage der Contacts-App) musste erst weggeklickt werden, kostet einen Schritt des Budgets.
- V2 ContactsAddContact Run 2: identisches Muster wie Run 1 (Schritt 2 BLOCKED auf Home-Screen [6] FrameLayout "Search", Schritt 4 wait mit 90,2 s, Nachname fehlt, "status complete" → FAIL). Diesmal kein "Don’t allow"-Dialog, dafür ein eigener Klick ins Phone-Feld vor dem input_text (Schritt 7).
- V2 ContactsAddContact Run 2, Schritt 10: der abschließende "status complete" brauchte 96,2 s Modellzeit (Run 1: 14,4 s).
- V2 ContactsAddContact Run 3: Muster zum dritten Mal identisch (BLOCKED Search auf Home-Screen, wait 119,0 s, Vorname per Koordinate x=500 y=384 wie in Run 1, Nachname fehlt, "status complete" → FAIL). Alle drei Contacts-Läufe: genau 10 Schritte, Fehlerklasse wrong_app (?), 1 blockierte Aktion, 1 Aktion ohne Effekt.
- V2 ContactsAddContact, alle 3 Läufe: die Aktion "wait" nach open_app ist jeweils der langsamste Schritt (96,0 s / 90,2 s / 119,0 s). input_text per Koordinate ebenfalls langsam (88,9 s / 105,9 s), input_text per Index 20 bis 24 s.
- V2 MarkorCreateNote Run 1 (PASS): zwei Koordinaten-Aktionen trotz Tree-Grounding (Schritt 2 click x=880 y=860, Schritt 7 input_text x=500 y=300), beide mit 89 bis 98 s die langsamsten Schritte. Schritt 8 und 9: zweimal hintereinander click [4] TextView "Save" (Doppel-Save), hat dem Ergebnis nicht geschadet.
- V2 MarkorCreateNote Run 2 (PASS): drei identische Klicks hintereinander auf [2] EditText ".md" (Schritt 5, 6, 7), erst dann Wechsel zum Spinner "new_file_dialog__type" → "Plain Text". Kostete 3 Schritte; kein Loop-Guard in V2 aktiv (Config loop_guard=false).
- V2 MarkorCreateNote Run 1 und 2: gleiches Vorgehen beider Läufe, Plus-Button per Koordinate x=880 y=860 (88 bis 89 s), Notiztext per Koordinate x=500 y=300 (98 bis 100 s), danach jeweils zweimal Save.
- V2 MarkorCreateNote Run 3 (PASS): dreimal hintereinander click [4] TextView "Save" (Schritt 8 bis 10). Mehrfach-Save in allen drei Markor-Läufen (2x, 2x, 3x). Der Plus-Button wurde hier per Index getroffen (Run 1 und 2: per Koordinate), die Notiztext-Eingabe in allen drei Läufen per Koordinate x=500 y=300 mit 96 bis 100 s.
- V2 MarkorCreateNote: 3 von 3 PASS, 10 / 14 / 11 Schritte bei Budget 16.
- V2 MarkorCreateNoteAndSms Run 1 (FAIL, Teilpunkte 0,50): Dateiname inklusive Endung ".txt" ins Namensfeld [1] "my_note" getippt, Dateityp-Feld/Spinner nicht angefasst (in MarkorCreateNote Run 2 hatte der Agent den Spinner noch genutzt). Dreimal hintereinander click [1] "Create a new file or folder" (Schritt 2 bis 4), zweimal click [8] Button "SMS" (Schritt 16, 17). Budget 18 genau aufgebraucht, "status complete" als letzter Schritt. Vorgeschlagene Fehlerklasse: grounding (?).
- V2 MarkorCreateNoteAndSms Run 1: alle Aktionen per Index, keine Koordinaten-Fallbacks; Schrittzeiten durchgehend 17 bis 34 s (ohne "wait" und ohne Koordinaten-Eingaben).
- V2 MarkorCreateNoteAndSms Run 2 (FAIL, Teilpunkte 0,50): wie Run 1 Dateiname mit ".txt" ins Namensfeld getippt, Dateityp-Spinner nicht genutzt. SMS-Teil lief ohne Wiederholungen durch (Start a conversation → Nummer → Bestätigen → Text → SMS). Erneut "status complete" → FAIL. Fehlerklasse diesmal wrong_app (?) wegen des Guardrail-Blocks in Schritt 1, Run 1 war grounding (?).
- Guardrail-Block "do not tap or type on the home screen" auf [6] FrameLayout "Search" nun in 4 von 8 V2-Läufen als erste oder zweite Aktion (ContactsAddContact 1 bis 3, MarkorCreateNoteAndSms 2).
- V2 MarkorCreateNoteAndSms Run 3 (FAIL, Teilpunkte 0,50): Dateiname war diesmal .md, also kein Dateityp-Problem, trotzdem nur 0,50 vom Checker. SMS-Teil identisch zu Run 2 (Start a conversation → Nummer → Bestätigen → Text → SMS). Alle 3 SMS-Läufe: Teilpunkte genau 0,50, "status complete" → FAIL.
- V2 gesamt: 3 PASS, 6 FAIL, 0 ERROR. Alle 9 Läufe endeten mit "status complete" (stop_reason model_done), nie durch das Schrittlimit. In allen 6 FAIL-Läufen steht "agent reported complete, verifier says fail".
- V2 gesamt: Koordinaten-Fallback trotz Tree-Grounding in 7 von 9 Läufen (input_text at x=500 y=384 bzw. y=300, click x=880 y=860); diese Schritte dauerten 88 bis 106 s, Index-Aktionen 15 bis 34 s.
- V1 ContactsAddContact Run 1 (PASS): V1 tippte den Nachnamen in ein eigenes Feld (y=468), was V2 in allen drei Contacts-Läufen ausgelassen hatte. Gleicher Seed, gleiche Aufgabe (Hugo Pereira) wie V2 Run 1 (FAIL). Kein Guardrail-Block, kein Tap auf dem Home-Screen: V1 begann direkt mit open_app contacts.
- V1 Schrittzeiten: 83 bis 112 s pro Schritt (Screenshot-Prompt), V2 per Index 15 bis 34 s. V1 Lauf 1 dauerte 14 min 46 s gegenüber 6 min bei V2 für dieselbe Aufgabe.
- V1 ContactsAddContact Run 2 (PASS): gleiche Koordinatenfolge wie Run 1 (Plus x=860 y=835, Vorname y=384, Nachname y=464 bis 468, Nummer y=610 bis 614, Save x=768 y=86), ein Schritt weniger, weil kein separater Klick ins Nummernfeld. Erneut "wait" als zweiter Schritt (82,5 s). Vor dem Lauf dreimal "Could not get a11y tree, retrying" in der Konsole, obwohl V1 den Tree gar nicht nutzt.
- V1 ContactsAddContact Run 1 und 2: open_app contacts beim ersten Schritt 111,7 s, beim zweiten Lauf 29,2 s.
- Reproduzierbarkeit (für die Folien, Bela 13:50): Kollege meldet vom Mac V1 5/9 und V2 2/9 PASS, hier V2 3/9 bei gleichem Skript, Modell, Seeds und Temperatur 0. Zu vergleichen: ContactsAddContact Run 1 (Seed 1155463587, Hugo Pereira) auf beiden Rechnern, dazu Digest und Ollama-Version aus den meta.json.
- V1 ContactsAddContact: 3 von 3 PASS (V2: 0 von 3). Alle drei V1-Läufe mit nahezu identischer Koordinatenfolge und immer eigenem Schritt für den Nachnamen. Alle drei V1-Läufe beginnen mit open_app contacts und dann "wait" (82 bis 98 s), nie mit einem Tap auf den Home-Screen.
- V1 MarkorCreateNote Run 1 (PASS): dreimal derselbe Klick auf Save (x=749 y=86, Schritt 7 bis 9), also Mehrfach-Save auch bei V1 (bei V2 in allen Markor-Läufen gesehen). Schritt 4 (input_text Dateiname per Koordinate) mit 140,4 s der langsamste Schritt des Tages. Dateiendung .md nicht separat gesetzt, war Standard.
- V1 MarkorCreateNote Run 2 (PASS): bei der .txt-Aufgabe hat V1 den Dateityp offenbar über drei gezielte Klicks umgestellt (Schritt 4 bis 6), ohne Wiederholungen; V2 brauchte dafür drei wirkungslose Klicks auf ".md" plus Spinner. Erneut dreimal Save (Schritt 8 bis 10). Lauf 16 min 48 s, V2 für denselben Seed 8 min 24 s.
- V1 MarkorCreateNote Run 3 (FAIL, false_done ?): der Save-Klick fehlt komplett, nach dem Text kam sofort "status complete" (in den vorherigen Markor-Läufen von V1 wurde Save jeweils dreimal geklickt). Vier verlorene Schritte am Anfang (scroll up, open_app, navigate_home, open_app). V2 hatte denselben Seed bestanden (11 Schritte). Jeder Schritt 82 bis 119 s.
- V1 MarkorCreateNoteAndSms Run 1 (FAIL, Teilpunkte 0,50, grounding ?): V1 hat die Endung ".txt" ins eigene Endungsfeld getippt (x=788 y=229), also den Dateityp korrekt behandelt, anders als V2. Trotzdem nur 0,50 vom Checker, wie alle drei V2-SMS-Läufe. Konsole: "1 tap(s) landed on no UI element; 4 action(s) did not change the screen". Im SMS-Teil 7 Schritte bis zum vermuteten Senden, Budget bis auf 1 Schritt aufgebraucht.
- Damit haben alle bisherigen 4 SMS-Läufe (3x V2, 1x V1) exakt 0,50 Teilpunkte und enden mit "agent reported complete, verifier says fail".
- V1 MarkorCreateNoteAndSms Run 2 (FAIL, 0,50, grounding ?): fünfmal hintereinander click x=277 y=148 in der SMS-App (Schritt 9 bis 13), alle ohne Bildschirmänderung, kein Loop-Guard in V1. Dateiendung .txt diesmal nicht gesetzt (in Run 1 hatte V1 sie ins Endungsfeld getippt). Letzter Schritt "status complete" mit 120,6 s. 5 von 5 SMS-Läufen bisher mit genau 0,50 Teilpunkten.
- V1 MarkorCreateNoteAndSms Run 3 (FAIL, step_limit, grounding ?): einziger Lauf aller 18 V1/V2-Läufe, der durch das Schrittlimit endete statt durch "status complete". Viermal click x=500 y=300 in der SMS-App ohne Effekt (Schritt 10 bis 13), die Nummer wurde nie eingetippt (nur Klicks ins Feld), Text wurde getippt, Senden als 18. Schritt. Keine Teilpunkte (0 statt 0,50 wie bei den anderen 5 SMS-Läufen).
- V1 gesamt: 5 PASS, 4 FAIL, 0 ERROR (1 Lauf wiederholt wegen Speicher-Abbruch). V1 ContactsAddContact 3/3 (V2 0/3), MarkorCreateNote 2/3 (V2 3/3), MarkorCreateNoteAndSms 0/3 (V2 0/3). In den V1-SMS-Läufen wiederholte Klicks auf dieselbe Koordinate in der SMS-App (5x, 4x), bei V2 keine Wiederholungen im SMS-Teil.
- Konsolenausgabe mit Dauer: V1 gesamt ca. 2 h 55 min reine Laufzeit (13:18 bis 15:05 plus 15:29 bis 16:55), V2 1 h 02 min.
- V3 ContactsAddContact Run 1 (FAIL, step_limit, wrong_app ?): V3 zeigt jetzt pro Schritt "screen changed / did NOT change". Der Koordinaten-Klick x=869 y=951 (statt Index) traf offenbar nicht den Plus-Button (V1 nutzte x=860 y=835), der Agent landete in einem Menü mit "Other tools" und verbrachte 7 Schritte mit scroll down und Klicks ohne Effekt, trotz Hinweis "screen did NOT change" und Loop-Guard (max_loop_blocks=3, kein Block in der Konsole sichtbar). Konsole: "2 action(s) only showed an effect after an extra wait". Neu in V3: Warnung "Skipping app snapshot loading: Snapshot not found ... com.google.android.contacts" vor und nach dem Lauf.
- V3 ContactsAddContact Run 2 (FAIL, grounding ?): gleiches Muster wie V2 (Nachname fehlt, trotzdem "status complete"). Der V3-Prüfschritt vor done (verify_before_done) hat den fehlenden Nachnamen nicht erkannt, Schritt 9 dauerte 45,0 s gegenüber 14 bis 18 s bei V2. Erste zwei Schritte navigate_home / navigate_back mit "screen did NOT change". Vorgeschlagene Klasse grounding (?), beobachtet eher lost_value / false_done.
- V3 ContactsAddContact Run 3 (FAIL, grounding ?): vier Navigationsaktionen am Anfang, alle mit "screen did NOT change", kein sichtbarer Loop-Guard-Eingriff in der Konsole. Danach wieder Nachname ausgelassen und "status complete" (45,4 s). V3 ContactsAddContact 0/3, identisches Nachname-Muster wie V2 in 5 von 6 Tree-Läufen; der Prüfschritt vor done hat es in beiden V3-Fällen durchgelassen.
- V3 MarkorCreateNote Run 1 (FAIL, step_limit): erster Fall von "device state was correct, but the agent never reported done" (das Muster, das der Kollege vom Mac gemeldet hatte). Save in Markor ändert den Bildschirm nicht, V3 meldet dem Modell "screen did NOT change", das Modell klickt erneut Save, der Loop-Guard blockt den 3. und 4. Versuch ("you already tried exactly this action 2 times"), danach 5 Schritte Irrweg bis zum Budget-Ende. Bei V2 (ohne Hinweis und Guard) hatte das Modell nach 2 bis 3x Save einfach "complete" gemeldet und bestanden. Schritt 2 (Plus-Button per Koordinate) 112,0 s.
- V3 MarkorCreateNote Run 1: letzter Schritt input_text des Notiztexts ins Markor-Suchfeld [1] EditText "Search", also Text in ein falsches Feld.
- V3 MarkorCreateNote Run 2 (FAIL, loop_abort): erster Lauf, den der Loop-Guard selbst beendet hat (max_loop_blocks=3 erreicht). Gleiche Save-Schleife wie Run 1 (2x ohne Effekt, 2x geblockt), danach 3x Klick auf den Dateinamen [0] TextView. Diesmal kein "device state was correct" in der Konsole, state_score 0 (siehe result.json), obwohl Dateiname inkl. .txt und Typ Plain Text gesetzt waren. V2 hatte denselben Seed mit 14 Schritten bestanden.
- V3 MarkorCreateNote Run 3 (FAIL, loop_abort): reinste Form der Save-Schleife, fünfmal in Folge click [4] TextView "Save", das Modell hat die Guard-Meldung "Choose a different action" dreimal ignoriert. V3 MarkorCreateNote 0/3 (V2 3/3, V1 2/3), alle drei V3-Markor-Läufe scheitern an derselben Stelle: Save ändert den Bildschirm nicht, V3 meldet das als Misserfolg, das Modell wiederholt. Bei Run 2 und 3 state_score 0, bei Run 1 war der Zustand korrekt.
- V3 MarkorCreateNoteAndSms Run 1 (FAIL, step_limit, 0,50): die Save-Schleife frisst das Budget, bevor der SMS-Teil beginnt; die SMS-App wurde in 18 Schritten nie geöffnet. Nach dem Loop-Guard-Block weicht das Modell auf navigate_back aus und beginnt eine zweite Datei mit demselben Namen. Teilpunkte 0,50 vermutlich für die Notiz. Bei V2 hatte derselbe Seed den SMS-Teil erreicht (18 Schritte, ebenfalls 0,50).
- V3 MarkorCreateNoteAndSms Run 2 (FAIL, loop_abort, 0 Punkte): Schritt 5 fügt "olin.txt" in das bereits gefüllte Namensfeld ein, der Dateiname wird zu "2023_06_01_fieolin.txtrce_violin" (Textfeld-Cursor stand offenbar mitten im Text). Danach wieder Save-Schleife plus Klick-Schleife auf den Dateinamen. Drei Tracebacks am Anfang (ADB am start, adb start-server und ein dritter), Schritt 1 dennoch ausgeführt (46,5 s), Schritt 2 "wait" 110,3 s. Schrittzeiten in diesem Lauf 20 bis 110 s, deutlich höher als in den V3-Läufen davor.
- V3 MarkorCreateNoteAndSms Run 3 (FAIL, step_limit, 0 Punkte): Notiztext "Ignorance is bliss." wurde ins Dateinamen-Feld getippt, Ergebnis eine Datei namens "IgnorIgnorance is bliss." (ADB-Timeout bei "input text Ignorance" mitten in der Eingabe, danach doppelt getippt). Schritt 8 Klick per Koordinate 127,1 s. Letzter Schritt "Share" im Markor-Menü, also der richtige Weg zum SMS-Teil, aber zu spät.
- V3 gesamt: 0 PASS, 9 FAIL, 0 ERROR. Stop-Gründe: 4x step_limit, 3x loop_abort, 2x model_done (beide Contacts, Nachname fehlt). Kein einziger V3-Lauf hat den SMS-Teil erreicht. Hauptmuster in 6 von 9 Läufen: Save in Markor ändert den Bildschirm nicht, "screen did NOT change"-Hinweis führt zu Wiederholung, Loop-Guard blockt, Modell verliert den Faden. Bei V2 (gleiche Beobachtung, keine Hinweise) wurden 3/3 Markor-Läufe bestanden.
- ADB-Timeouts ("Failed to execute ADB command, try 1 of 3") traten im Tagesverlauf häufiger auf: 13:58, 14:46, 17:41 (2x), 17:53, 18:0x (input text). Alle wurden von AndroidWorld wiederholt, kein Lauf endete als ERROR.

## Ergebnis

Alle 27 Läufe beendet um 18:06. Reine Laufzeit: V2 1 h 02 min (12:15 bis 13:17), V1 2 h 55 min (13:18 bis 15:05 und 15:29 bis 16:55), V3 1 h 11 min (16:55 bis 18:06). Gesamt ca. 5 h 08 min Laufzeit, 5 h 51 min Wanduhr inkl. Emulator-Neustart.

### PASS / FAIL / ERROR pro Version und Task

| Version | Task | PASS | FAIL | ERROR | Ø Dauer pro Lauf |
|---|---|---|---|---|---|
| V1 Screenshot+Koordinaten | ContactsAddContact | 3 | 0 | 0 | 13.1 min |
| V1 Screenshot+Koordinaten | MarkorCreateNote | 2 | 1 | 0 | 16.0 min |
| V1 Screenshot+Koordinaten | MarkorCreateNoteAndSms | 0 | 3 | 0 | 28.5 min |
| **V1 Screenshot+Koordinaten** | **alle** | **5** | **4** | **0** | **19.2 min** |
| V2 Tree+Index | ContactsAddContact | 0 | 3 | 0 | 6.3 min |
| V2 Tree+Index | MarkorCreateNote | 3 | 0 | 0 | 6.9 min |
| V2 Tree+Index | MarkorCreateNoteAndSms | 0 | 3 | 0 | 7.4 min |
| **V2 Tree+Index** | **alle** | **3** | **6** | **0** | **6.9 min** |
| V3 Tree+Index+Harness | ContactsAddContact | 0 | 3 | 0 | 5.2 min |
| V3 Tree+Index+Harness | MarkorCreateNote | 0 | 3 | 0 | 6.8 min |
| V3 Tree+Index+Harness | MarkorCreateNoteAndSms | 0 | 3 | 0 | 11.5 min |
| **V3 Tree+Index+Harness** | **alle** | **0** | **9** | **0** | **7.8 min** |

Kosten laut summary.md: Modellzeit pro Schritt V1 89,8 s, V2 27,9 s, V3 27,7 s; Prompt-Tokens pro Aufruf V1 1905, V2 1069, V3 1120.

### Stop-Gründe

| Version | model_done | step_limit | loop_abort |
|---|---|---|---|
| V1 Screenshot+Koordinaten | 8 | 1 | 0 |
| V2 Tree+Index | 9 | 0 | 0 |
| V3 Tree+Index+Harness | 2 | 4 | 3 |

### Wiederholte Läufe

- V1 MarkorCreateNoteAndSms Run 1: Original `v1_baseline\MarkorCreateNoteAndSmsun1_20261008-144527` bei Schritt 15/18 abgebrochen (Speichermangel, Prozess beendet, Emulator weg), Wiederholung `run1_20261008-152919` nach Emulator-Neustart 15:27. Nur dieser eine Lauf; kein Lauf endete als ERROR.

### Aufnahmen, die wir anschauen sollten (alle FAIL-Läufe)

Pfade relativ zu `androidworld-gui-agentuns\`.

| Version | Task | Run | Klasse (Vorschlag) | trajectory.html | recording.mp4 |
|---|---|---|---|---|---|
| V1 | MarkorCreateNote | 3 | false_done | `v1_baseline\MarkorCreateNote\run3_20261008-143031	rajectory.html` | `v1_baseline\MarkorCreateNote\run3_20261008-143031ecording.mp4` |
| V1 | MarkorCreateNoteAndSms | 1 | grounding | `v1_baseline\MarkorCreateNoteAndSms\run1_20261008-152919	rajectory.html` | `v1_baseline\MarkorCreateNoteAndSms\run1_20261008-152919ecording.mp4` |
| V1 | MarkorCreateNoteAndSms | 2 | grounding | `v1_baseline\MarkorCreateNoteAndSms\run2_20261008-155729	rajectory.html` | `v1_baseline\MarkorCreateNoteAndSms\run2_20261008-155729ecording.mp4` |
| V1 | MarkorCreateNoteAndSms | 3 | grounding | `v1_baseline\MarkorCreateNoteAndSms\run3_20261008-162717	rajectory.html` | `v1_baseline\MarkorCreateNoteAndSms\run3_20261008-162717ecording.mp4` |
| V2 | ContactsAddContact | 1 | wrong_app | `v2_index\ContactsAddContact\run1_20261008-121534	rajectory.html` | `v2_index\ContactsAddContact\run1_20261008-121534ecording.mp4` |
| V2 | ContactsAddContact | 2 | wrong_app | `v2_index\ContactsAddContact\run2_20261008-122136	rajectory.html` | `v2_index\ContactsAddContact\run2_20261008-122136ecording.mp4` |
| V2 | ContactsAddContact | 3 | wrong_app | `v2_index\ContactsAddContact\run3_20261008-122743	rajectory.html` | `v2_index\ContactsAddContact\run3_20261008-122743ecording.mp4` |
| V2 | MarkorCreateNoteAndSms | 1 | grounding | `v2_index\MarkorCreateNoteAndSms\run1_20261008-125510	rajectory.html` | `v2_index\MarkorCreateNoteAndSms\run1_20261008-125510ecording.mp4` |
| V2 | MarkorCreateNoteAndSms | 2 | wrong_app | `v2_index\MarkorCreateNoteAndSms\run2_20261008-130304	rajectory.html` | `v2_index\MarkorCreateNoteAndSms\run2_20261008-130304ecording.mp4` |
| V2 | MarkorCreateNoteAndSms | 3 | wrong_app | `v2_index\MarkorCreateNoteAndSms\run3_20261008-131049	rajectory.html` | `v2_index\MarkorCreateNoteAndSms\run3_20261008-131049ecording.mp4` |
| V3 | ContactsAddContact | 1 | wrong_app | `v3_full\ContactsAddContact\run1_20261008-165552	rajectory.html` | `v3_full\ContactsAddContact\run1_20261008-165552ecording.mp4` |
| V3 | ContactsAddContact | 2 | grounding | `v3_full\ContactsAddContact\run2_20261008-170151	rajectory.html` | `v3_full\ContactsAddContact\run2_20261008-170151ecording.mp4` |
| V3 | ContactsAddContact | 3 | grounding | `v3_full\ContactsAddContact\run3_20261008-170650	rajectory.html` | `v3_full\ContactsAddContact\run3_20261008-170650ecording.mp4` |
| V3 | MarkorCreateNote | 1 | grounding | `v3_full\MarkorCreateNote\run1_20261008-171120	rajectory.html` | `v3_full\MarkorCreateNote\run1_20261008-171120ecording.mp4` |
| V3 | MarkorCreateNote | 2 | grounding | `v3_full\MarkorCreateNote\run2_20261008-172033	rajectory.html` | `v3_full\MarkorCreateNote\run2_20261008-172033ecording.mp4` |
| V3 | MarkorCreateNote | 3 | grounding | `v3_full\MarkorCreateNote\run3_20261008-172656	rajectory.html` | `v3_full\MarkorCreateNote\run3_20261008-172656ecording.mp4` |
| V3 | MarkorCreateNoteAndSms | 1 | grounding | `v3_full\MarkorCreateNoteAndSms\run1_20261008-173138	rajectory.html` | `v3_full\MarkorCreateNoteAndSms\run1_20261008-173138ecording.mp4` |
| V3 | MarkorCreateNoteAndSms | 2 | grounding | `v3_full\MarkorCreateNoteAndSms\run2_20261008-174007	rajectory.html` | `v3_full\MarkorCreateNoteAndSms\run2_20261008-174007ecording.mp4` |
| V3 | MarkorCreateNoteAndSms | 3 | grounding | `v3_full\MarkorCreateNoteAndSms\run3_20261008-175304	rajectory.html` | `v3_full\MarkorCreateNoteAndSms\run3_20261008-175304ecording.mp4` |

Besonders lohnend: V2 ContactsAddContact Run 1 gegen V1 Run 1 (gleicher Seed 1155463587, FAIL vs. PASS, Nachname), V3 MarkorCreateNote Run 1 (Zustand korrekt, nie fertig gemeldet, Save-Schleife), V3 MarkorCreateNoteAndSms Run 2 (verstümmelter Dateiname).

### Offene Punkte für Bericht und Folien

- Reproduzierbarkeits-Folie Mac vs. Windows (Bela, 13:50): Vergleich mit den Läufen des Kollegen, gleicher Seed, anderes Ergebnis.
- failure_class in log.csv ist überall noch Vorschlag (failure_reviewed leer). Beobachtet: V2/V3 Contacts eher lost_value bzw. false_done statt wrong_app/grounding; V3 Markor eher "nie fertig gemeldet" (too_early passt nicht, false_done passt nicht; Klasse klären).
- Zwei Einträge qwen3-vl:4b-instruct in `ollama list` (6bf7b924e48a, ef33995bb2ac), verwendet wurde ef33995bb2ac.
