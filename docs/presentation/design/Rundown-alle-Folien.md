# Rundown: das ganze Projekt und jede Folie erklärt

Für alle fünf im Team, besonders für die, die nicht im Code waren. Dieses Dokument erklärt, was wir gebaut haben, warum, was dabei herauskam, und dann jede Folie des Decks (49 Folien, Stand 08.10. abends, Commit `dd068e2`): was drauf steht, was dahinter steckt, woher die Zahlen kommen, und welche Fragen dazu kommen können. Belas Sprechtext pro Folie steht zusätzlich in `Sprechtext-Folien.md`; dieses Dokument ist das "Warum" dahinter.

---

## Teil 1: Das Projekt in zehn Minuten

### Die Aufgabe

Wir sollten einen GUI-Agenten für AndroidWorld bauen. AndroidWorld ist eine Benchmark-Umgebung von Google: ein Android-Emulator (ein virtuelles Pixel-6-Handy) plus 116 Aufgaben, die ein Agent auf diesem Handy lösen soll, zum Beispiel "Lege einen Kontakt für Hugo Pereira mit der Nummer +13920741751 an". AndroidWorld hat für jede Aufgabe einen Checker, der am Ende den Gerätezustand prüft (steht der Kontakt wirklich in der Kontaktdatenbank?) und 1 oder 0 zurückgibt, manchmal 0,5 für teilweise erledigt.

Die Vorgaben des Dozenten: eine Agent-Klasse mit einer einzigen Methode `step()`; drei Aufgaben, je eine pro Schwierigkeitsstufe; jede Aufgabe dreimal laufen lassen, mit Bildschirmaufnahme; Fehler erklären mit fünf festen Fehlerklassen; eine dokumentierte Verbesserung mit Vorher-Nachher-Zahlen; Schutzregeln (Guardrails) im Code, nicht im Prompt: ein Schrittlimit und ein Zahlungsverbot; alles reproduzierbar.

### Was ein GUI-Agent ist

Ein GUI-Agent ist ein Sprachmodell, das ein Handy bedient wie ein Mensch: Es sieht den Bildschirm, entscheidet sich für eine Aktion (tippen, Text eingeben, scrollen, App öffnen), die Aktion wird ausgeführt, dann sieht es den neuen Bildschirm, und so weiter. Das Modell hat keinen Zugriff auf die App von innen, nur auf das, was ein Nutzer auch sehen würde.

Unser Agent läuft in einer Schleife. Jeder Durchlauf ist ein `step()`:

1. **Beobachten:** den aktuellen Bildschirm holen (als Screenshot oder als Textliste der Elemente).
2. **Prompt bauen:** Aufgabe, bisherige Schritte (eine Zeile pro Schritt), aktueller Bildschirm.
3. **Modell fragen:** genau ein Aufruf, Antwort ist ein JSON mit einer Aktion.
4. **Prüfen:** ist das JSON gültig? Wenn nicht, einmal mit der Fehlermeldung nachfragen.
5. **Grounding:** die Aktion auf Pixelkoordinaten übersetzen.
6. **Guardrails:** ist die Aktion erlaubt? (Zahlungsverbot, nur erlaubte Apps, kein Tippen auf dem Home-Screen)
7. **Ausführen** auf dem Emulator.
8. **Protokollieren:** hat sich der Bildschirm verändert? Eine Zeile in die Historie.

Das Modell macht nur Schritt 3. Alles andere ist unser Code, und das ist der Kernpunkt des ganzen Vortrags: Das Modell entscheidet, der Code drumherum (die "Harness") macht es sicher, messbar und ehrlich.

### Das Modell

`qwen3-vl:4b-instruct`: ein Vision-Language-Modell von Alibaba mit 4,4 Milliarden Parametern, das Bilder und Text versteht. Es läuft lokal auf dem Laptop über Ollama (ein Programm, das Modelle lokal bereitstellt, wie ein kleiner Server). "Q4_K_M" heißt: die Gewichte sind auf 4 Bit komprimiert, damit es in den Arbeitsspeicher passt (ca. 3,3 GB). Temperatur 0 und fester Seed bedeuten: Bei gleicher Eingabe antwortet das Modell immer gleich. Für V5 und V6 haben wir das größere Geschwister `qwen3-vl:8b-instruct` (6,1 GB) genommen.

Wichtig für die Fragerunde: Nichts verlässt den Laptop. Keine Cloud, keine API-Kosten. Dafür ist das Modell klein und langsam: 6 bis 90 Sekunden pro Schritt, je nach Rechner und Version.

### Die drei Aufgaben

| Stufe | Aufgabe | Was passieren muss | Schrittbudget |
|---|---|---|---|
| Warm-up | ContactsAddContact | Kontakte-App öffnen, Vorname, Nachname, Nummer eintippen, speichern | 12 |
| Real work | MarkorCreateNote | Markor (ein Notiz-Editor) öffnen, neue Datei mit vorgegebenem Namen anlegen, Text eintippen, speichern | 16 |
| Multi-app | MarkorCreateNoteAndSms | wie oben, dann den Text per SMS an eine Nummer schicken (zweite App) | 18 |

Das Schrittbudget kommt von AndroidWorld: Jede Aufgabe hat eine "complexity", das Budget ist complexity × 10. Ist es aufgebraucht, endet der Lauf als FAIL, egal wie der Bildschirm aussieht.

### Die sechs Versionen

Die Grundregel war: pro Version genau eine Änderung, damit man weiß, was gewirkt hat.

| Version | Was anders ist | Idee dahinter |
|---|---|---|
| V1 | Modell sieht den Screenshot, gibt Koordinaten aus | Baseline, so machen es die meisten Papers |
| V2 | Modell sieht die Textliste der Elemente (Accessibility Tree), gibt eine Elementnummer aus, der Code rechnet die Koordinaten | Zeigen ist schwer für kleine Modelle; wenn der Code zeigt, kann das Modell nicht danebentippen |
| V3 | V2 plus fünf Harness-Mechanismen auf einmal: warten bis der Bildschirm ruhig ist, Hinweis "deine Aktion hat nichts geändert", Loop-Guard, Statusleiste, Prüfschritt vor "fertig" | Die V2-Fehler mit Sicherheitsnetzen abfangen |
| V4 | V2 plus Goal-Tracker im Code: Code liest die Werte aus der Aufgabe (Name, Nummer, Dateiname, Text), zeigt jeden Schritt, welche noch nicht getippt sind, und blockt "fertig", solange einer fehlt | Verlorene Werte ohne zweiten Modellaufruf verhindern |
| V5 | V2 mit dem 8B-Modell | Ist es ein Wissens- oder ein Harness-Problem? |
| V6 | V5 plus zwei Code-Fixes: vorbelegtes Feld vor dem Tippen leeren; nach Save/Send um "fertig" bitten, wenn alle Werte getippt sind | Die zwei Muster angehen, die alle Versionen überlebt haben |

### Die Ergebnisse

Zwei Rechner: Belas Windows-Laptop (V1–V3, 27 Läufe, keine Abstürze, deshalb die Haupttabelle im Deck) und Liams MacBook Air M4 (V1–V6, 54 gewertete Läufe, 11 Emulator-Abstürze, die mit demselben Seed wiederholt wurden).

| | V1 | V2 | V3 | V4 | V5 | V6 |
|---|---|---|---|---|---|---|
| Windows, Erfolg | 5/9 | 3/9 | 0/9 | – | – | – |
| Mac, Erfolg | 5/9 | 2/9 | 0/9 | 1/9 | 3/9 | 1/9 |
| Mac, Modellzeit pro Schritt | 23,5 s | 6,3 s | 12,7 s | 9,3 s | 7,3 s | 14,6 s* |

\* V6 lief, während der Laptop anderweitig belastet war; die Zeit ist keine Eigenschaft von V6.

Die Geschichte, die diese Zahlen erzählen:

**V1 → V2:** Der Wechsel von Screenshot auf Textliste hat jeden Schritt dreimal schneller und halb so teuer gemacht (1.900 → 1.000 Tokens) und die Taps ins Leere beseitigt. Aber die Erfolgsquote ist gesunken, weil ein neuer Fehler aufgetaucht ist: Mit der Textliste "vergisst" das 4B-Modell den Nachnamen. Es tippt "Hugo", springt zum Telefonfeld, speichert und meldet "fertig". Im Screenshot ist das leere Feld "Last name" direkt darunter sichtbar; in der Textliste ist es nur eine Zeile unter vielen.

**V3:** Alle Sicherheitsnetze zusammen haben die Quote auf null gebracht. Der Grund ist ein einziger: Alle Netze nehmen an, dass eine erfolgreiche Aktion den Bildschirm sichtbar verändert. Markor speichert aber automatisch, ohne Bestätigung. Also sagt der Hinweis "deine Aktion hat nichts geändert", der Loop-Guard blockt den nächsten Save, der Prüfschritt sagt "nicht gespeichert", und der Agent sucht verzweifelt andere Wege (Teilen-Menü, falsche SMS-App) bis das Budget aus ist. Und der Prüfschritt (dasselbe 4B-Modell, das noch einmal auf den Bildschirm schaut) hat den fehlenden Nachnamen dreimal von dreimal durchgewinkt.

**V4:** Der Code-Tracker war richtig gedacht, aber das Veto hat nie gefeuert. Stattdessen hat das 4B-Modell mit dem zusätzlichen Textblock im Prompt angefangen, auf dem Home-Screen elfmal "zurück" zu drücken. Lehre: Für ein so kleines Modell ist jede Zeile Prompt ein Eingriff ins Verhalten, kein neutraler Ort für Information.

**V5:** Das 8B-Modell hat den Nachnamen nie wieder verloren, bei nur 16 % mehr Zeit pro Schritt. Zwei von drei Kontakt-Läufen bestanden. Aber zwei Muster blieben: Bei Markor tippt es 6- bis 14-mal auf das Feld mit der Dateiendung ".md", statt hineinzuschreiben, und nach korrektem Speichern sagt es oft nicht "fertig".

**V6:** Zwei Code-Fixes genau für diese zwei Muster. Beide haben in den fehlgeschlagenen Läufen nie gegriffen: Die Endungsfeld-Schleife besteht aus Klicks, nicht aus Tippen, also hatte die Lösch-Regel nichts zu löschen. Und den "sag fertig"-Hinweis hatten wir an eine sichtbare Bildschirmänderung gekoppelt; Markors Save ändert nichts, also kam der Hinweis dort nie. Derselbe Denkfehler wie in V3, von uns wiederholt.

### Die fünf Dinge, die wir gelernt haben

1. Wo das Grounding passiert, zählt mehr als die Prompt-Formulierung: in Code dreimal schneller, keine Taps ins Leere.
2. Jedes Sicherheitsnetz enthält eine Annahme über die App. Wo die Annahme nicht gilt (Markor speichert ohne sichtbare Änderung), macht das Netz aus einem Erfolg einen Fehlschlag.
3. Ein Prüfer, der so schwach ist wie der Handelnde, kostet Zeit und bringt keine Sicherheit.
4. Modellgröße schließt Wissenslücken (der Nachname), nicht Interaktions- oder Abschlusslücken (das Endungsfeld, das fehlende "fertig").
5. Drei Läufe pro Aufgabe reichen, um Muster zu finden, nicht, um Versionen zu ranken. Ein Lauf verschiebt eine Aufgabe um 33 Punkte.

---

## Teil 2: Glossar

**Accessibility Tree (Tree, Textliste):** Android stellt für Screenreader eine Liste aller sichtbaren Elemente bereit, mit Typ, Beschriftung und Position. Beispiel: `[7] EditText "First name" (100,380)-(980,460)`. Wir geben dem Modell diese Liste statt des Bildes. Vorteil: billig, exakte Koordinaten. Nachteil: Was keine Beschreibung hat, ist unsichtbar, und das räumliche Layout geht verloren.

**Grounding:** die Übersetzung von "ich will auf Speichern tippen" in eine Pixelkoordinate. In V1 macht das Modell das (es gibt x, y aus); ab V2 gibt es eine Elementnummer aus, und unser Code schlägt die Mitte des Elements nach.

**Harness:** alles um das Modell herum: Schleife, Prompt-Aufbau, Validierung, Grounding, Guardrails, Protokoll. Der Dozent nennt fünf Teile: loop control, context assembly, tool dispatch, error recovery, guardrails.

**Guardrail:** eine Regel im Code, die eine Modellentscheidung blockiert, bevor sie ausgeführt wird. Hat keinen Ausschalter. Unsere: Schrittlimit, Zahlungsverbot (zwei Ebenen), App-Whitelist, kein Tippen auf dem Home-Screen, Loop-Guard (nur V3).

**Seed:** Startwert eines Zufallsgenerators. AndroidWorld erzeugt aus dem Seed die konkreten Werte einer Aufgabe (welcher Name, welche Nummer). Gleicher Seed heißt gleiche Aufgabe, deshalb sind "Run 2 von V1" und "Run 2 von V5" dieselbe Aufgabe. Beim Modell sorgt der Seed 42 zusammen mit Temperatur 0 dafür, dass gleiche Eingabe gleiche Ausgabe gibt.

**Temperatur:** steuert, wie zufällig das Modell das nächste Wort wählt. 0 heißt: immer das wahrscheinlichste. Macht Läufe wiederholbar.

**Quantisierung (Q4_K_M):** Kompression der Modellgewichte auf 4 Bit pro Zahl. Macht das Modell viermal kleiner und schneller, minimal ungenauer.

**Digest:** Prüfsumme der Modelldatei, wie ein Fingerabdruck. Gleicher Name, anderer Digest heißt: andere Datei, formal anderes Modell. Belas und Liams Ollama-Versionen hatten verschiedene Digests, deshalb vergleichen wir Einzelläufe nicht über Rechner hinweg.

**Verifier / Checker:** AndroidWorlds Prüfung des Gerätezustands am Ende. 1,0 = erledigt, 0 = nicht, 0,5 = teilweise (z. B. Notiz existiert, SMS wurde nicht gesendet).

**PASS-Regel:** Ein Lauf ist nur PASS, wenn der Agent selbst "complete" gemeldet hat UND der Checker 1,0 sagt. Ein richtiger Bildschirm, bei dem der Agent nie "fertig" sagt, ist ein FAIL. Das ist streng, aber ehrlich: Ein Agent, der nicht weiß, wann er fertig ist, ist nicht fertig.

**Stop-Gründe:** `model_done` (Agent sagt complete), `model_infeasible` (Agent gibt auf), `step_limit` (Budget aus), `loop_abort` (V3: dreimal dieselbe wirkungslose Aktion), `error` (Emulator oder Modellserver abgestürzt; zählt nicht in die Quote).

**Fehlerklassen (fünf, vom Dozenten vorgegeben):** `grounding` (daneben getippt oder Tap ohne Wirkung), `too_early` (gehandelt, bevor der Bildschirm fertig geladen war), `lost_value` (ein Wert aus der Aufgabe ging verloren oder wurde erfunden), `wrong_app` (falsche App), `false_done` ("fertig" gesagt, aber nicht fertig). Unser Code schlägt eine Klasse vor; ein Mensch bestätigt sie am Video.

**ReAct:** das Muster Reason → Act → Observe: das Modell schreibt einen kurzen Gedanken, dann eine Aktion, dann sieht es das Ergebnis. Unser JSON hat ein Feld `thought` und ein Feld `action`.

**KV-Cache / stabiler Prefix:** Das Modell kann den Anfang eines Prompts wiederverwenden, wenn er sich nicht ändert. Deshalb steht bei uns das Unveränderliche (Rolle, Regeln, Aktionsraum) vorn und das Veränderliche (Status, aktueller Bildschirm) hinten.

**Schema-constrained decoding:** Wir geben Ollama ein JSON-Schema mit; das Modell kann physisch nur Antworten erzeugen, die dem Schema entsprechen. Ergebnis: null ungültige Antworten in fast allen Läufen.

**Replaced runs:** Läufe, die durch Emulator-Absturz als ERROR endeten, wurden mit demselben Seed wiederholt. Die Regel stand vor der Auswertung fest und wurde unabhängig vom Ergebnis angewendet (zwei der ersetzten Läufe waren PASS). Originale liegen in `runs/log_replaced.csv`.

---

## Teil 3: Folie für Folie

Nummern sind die Browser-Foliennummern (Divider zählen mit). "Zahlenquelle" sagt, wo die Zahl im Repo steht.

### Kapitel 0: Einstieg

**Folie 1, Titel.** "Agentic AI in Modern Business. A GUI agent for AndroidWorld, and where it breaks." Der Untertitel ist Programm: Wir zeigen nicht, dass es funktioniert, sondern wo es bricht und warum. Das Modell wird hier bewusst nicht genannt; das kommt auf Folie 7 und 23, weil es Pflicht ist, es zu nennen.

**Folie 2, Agenda.** Fünf Kapitel: Aufgabe, Bau, Messung, Was passiert ist, Was wir geändert und gelernt haben. "One agent, six versions" in Kapitel 2 ist die Zusammenfassung des Vorgehens. Wer diese Folie hat, sagt einen Satz pro Kapitel und ist nach 30 Sekunden weiter.

### Kapitel 1: The assignment (Folien 3 bis 5)

**Folie 3, Divider.**

**Folie 4, Build an agent that operates a phone, measure it, improve it.** Drei Spalten. "The task": eine Klasse, ein `step()`, der Agent sieht nur Pixel und Buttons (keine API in die App). "The goal": kein Demo, sondern Messung; 3 Aufgaben × 3 Läufe × 3 Versionen; Fehler erklärt; jede Version vorher/nachher. "The guidelines": Modell frei, aber nennen; Guardrails im Code; eine Aufgabe pro Schwierigkeitsstufe. Hintergrund: Das sind wörtlich die Vorgaben aus dem Syllabus und den Tag-1-Folien. Mögliche Frage: "Warum nur eine Klasse?" Antwort: Damit die gesamte Logik an einer Stelle lesbar ist und der Dozent sie vergleichen kann.

**Folie 5, The three tasks.** Tabelle mit Stufe, Aufgabenname, dem Text, den der Agent bekommt, und dem Budget (12, 16, 18). Die Platzhalter {name}, {number}, {file_name}, {text} werden pro Lauf aus dem Seed gefüllt. Warum diese drei: Kontakte isoliert das Grundproblem (richtiges Feld finden, richtigen Wert tippen); Markor hat echte UI-Reibung (Dialog mit getrenntem Endungsfeld, Editor, der ohne Bestätigung speichert); Note+SMS braucht zwei Apps und einen Wert, der den App-Wechsel überleben muss. Mögliche Frage: "Warum nicht schwierigere Aufgaben?" Antwort: Der Dozent wollte eine pro Stufe; und schon die mittlere bricht das Modell.

### Kapitel 2: How we built it (Folien 6 bis 14)

**Folie 6, Divider.**

**Folie 7, Which model we use and how it is configured.** Tabelle: qwen3-vl:4b-instruct, 4,4B Parameter; läuft auf dem Laptop via Ollama (localhost:11434); Q4_K_M; ca. 3,3 GB Speicher (Rechnung: 4,4 Mrd. × 0,5 Byte + Projektor fürs Bild); Kontextfenster 8.192 Tokens (Ollama-Standard 4.096 war zu klein für Tree plus Bild); Temperatur 0, Seed 42, top-p Standard; maximal 400 Ausgabetokens, JSON-Schema. Rechts: kostenlos nach Download, langsam, nur klein; die Variante "instruct" antwortet sofort, "thinking"-Varianten würden erst lange nachdenken; jeder Lauf speichert Name, Größe, Quantisierung, Digest. Zusatz in der Modellzeile: V5/V6 auf dem Mac mit 8B (6,1 GB). Mögliche Frage: "Warum kein GPT/Claude?" Antwort: lokal, kostenlos, reproduzierbar, und der Dozent hat Lokalmodelle empfohlen; ein Cloud-Modell wäre ein sinnvoller nächster Vergleich (Limitations-Folie).

**Folie 8, Agent design: the eight stages of one step().** Acht Kästen: 0 Budget prüfen, 1 Beobachten, 2 Entscheiden (einziger Kasten mit "M" für Modell), 3 Validieren, 4 Grounding, 5 Check (Guardrails), 6 Ausführen, 7 Feedback. Darunter die Tabelle, die die fünf Harness-Teile des Dozenten auf unsere Stufen abbildet: Loop control = Stufe 0 und Stop-Regeln; Context assembly = Stufe 1, `prompts.py`, `memory.py`; Tool dispatch = Stufen 4 und 6; Error recovery = Stufen 3 und 7; Guardrails = Stufe 5, `guardrails.py`. Die Botschaft: sieben von acht Stufen sind unser Code. Mögliche Frage: "Was passiert, wenn das Modell Unsinn antwortet?" Antwort: Stufe 3, Validierung mit einmaliger Wiederholung, die Fehlermeldung geht in den Prompt; durch das Schema kommt das praktisch nie vor (0 bis 1 ungültige Antworten pro 9 Läufe).

**Folie 9, One step of the ReAct loop.** Links ein echter Schritt 5 aus dem Contacts-Lauf: Gedanke ("The Create contact button is visible and accessible"), Aktion (click index 1), Beobachtung (Bildschirm geändert, neuer Tree mit 12 Elementen, Historienzeile). Rechts die Tabelle, die die Tool-Kategorien aus Tag 3 auf uns abbildet: Reason = der Gedanke; Act = unsere zehn Aktionen; Collaboration/Nutzerkommunikation gibt es nicht (nur `infeasible` als Aufgeben); Observe = Tree oder Screenshot; AndroidWorld liefert beides als "Computer Use"-Plugin; Tool-Discovery/MCP brauchen wir nicht, weil die zehn Aktionen fest sind. Hintergrund: Diese Folie verbindet unseren Agenten mit dem Vorlesungsvokabular. Wenn Zeit knapp ist, Kandidat fürs Backup.

**Folie 10, Pixels see everything but point badly. The tree is precise but incomplete.** Links Screenshot (V1): sieht alles, auch WebViews und Zeichnungen; ca. 1.900 Prompt-Tokens pro Schritt; das Modell muss die Zeile selbst finden. Rechts Tree (V2–V6): vier Beispielzeilen; ca. 980 Tokens, exakte Grenzen; was keine Beschreibung hat, existiert nicht. Neue Zeile: V4 bis V6 behalten den Tree und ändern das Drumherum. Hintergrund: Das ist "die erste echte Designentscheidung" laut Dozent, und unser dokumentierter Vorher-Nachher-Vergleich. Zahlenquelle: `summary.md`, Spalte prompt tokens. Mögliche Frage: "Warum nicht beides?" Antwort: Option `observation: both` existiert in der Config, nie gefahren, Kostenfrage; steht in der Outlook-Folie.

**Folie 11, How the agent points: coordinates vs. index.** Links V1: `{"action_type": "click", "x": 540, "y": 735}`, das Modell erzeugt die Zahlen; 20 Pixel daneben ist ein Tap in die Lücke zwischen zwei Zeilen, und niemand meldet einen Fehler. Rechts V2+: `{"action_type": "click", "index": 3}`, der Code schlägt Element 3 nach; entweder es existiert oder nicht, ein sichtbarer, loggbarer Fehler. Hintergrund: "Die meisten GUI-Agent-Fehler sind Zeigefehler" (Tag 1). Das ist der Kern der Verbesserung V1 → V2.

**Folie 12, Old screens are never resent.** Links der Prompt-Aufbau: System (Rolle, Aktionsraum, Regeln; stabil, gecacht), dann GOAL, HISTORY (eine Zeile pro Schritt, von Code geschrieben, z. B. "2. click [6] Search -> BLOCKED: home screen"), CURRENT SCREEN (nur dieser Schritt), STATUS (am Ende, am volatilsten). Rechts drei Punkte: ein Tool-Call-Loop, aber komprimiert (20 behaltene Screenshots würden 20.000+ Tokens kosten); stabiler Prefix zuerst, damit der KV-Cache trifft; Historie und Status schreibt der Code, nicht das Modell, "BLOCKED" oder "changed nothing" sind also Fakten. Hintergrund: Tag 2 Context Engineering, eins zu eins angewendet. Wichtig und ehrlich: Nur der System-Prefix wird tatsächlich gecacht, weil sich alles danach ändert. Mögliche Frage: "Hat das Modell ein Gedächtnis?" Antwort: Nur die acht letzten Historienzeilen; ältere fallen weg. Ab V3 zusätzlich eine Notizzeile, die einen Wert (die Telefonnummer) in die nächste App mitnimmt.

**Folie 13, The action space: ten actions, one schema.** Die zehn Aktionen: click, long_press, input_text, scroll, open_app, navigate_back, navigate_home, keyboard_enter, wait, status. Das Schema wird Ollama übergeben: `action_type` ist ein Enum, `index` eine Zahl, `app_name` ein Enum der erlaubten Apps, `goal_status` complete oder infeasible. Drei Punkte: Schema für constrained decoding; open_app nur mit exaktem Namen aus der Liste; toleranter Parser, strikte Validierung, ein Retry mit Fehlermeldung. Hintergrund: Tag 3 "tools are the action space", Tag 1 Reihenfolge "erst Decoding einschränken, dann validieren und wiederholen, erst dann am Prompt drehen". Mögliche Frage: "Warum kein Scrollen mit Koordinaten / kein Drag?" Antwort: AndroidWorld bietet mehr Aktionen; wir haben die zehn genommen, die die drei Aufgaben brauchen.

**Folie 14, Guardrails: in the code, before the action, no off switch.** Links vier Punkte: Schrittlimit; Zahlungsverbot Ebene 1 (App-Scope: nur erlaubte Apps); Ebene 2 (Deny-Regeln: Elemente mit Pay/Buy/Checkout-Beschriftung, Kartennummern mit Luhn-Prüfung, IBANs); Loop-Guard (nur V3). Rechts ein echter Guardrail-Treffer aus V2: Schritt 2 wollte auf die Home-Screen-Suche tippen, "BLOCKED: do not tap or type on the home screen. Open the app you need with open_app and its exact name", Schritt 3 macht es richtig. Hintergrund: Pflichtanforderung; Tag 4 "enforcement layer, not prompt rule". Die ausführliche Fassung steht im Backup B9. Mögliche Frage: "Hat das Zahlungsverbot je gefeuert?" Antwort: Nein, in 81 Läufen null Zahlungsversuche; die Home-Screen-Regel dagegen hat sechsmal auf dem Mac gefeuert, und auf dieser Folie sieht man, dass sie dem Modell hilft, nicht nur blockt.

### Kapitel 3: How we measured (Folien 15 bis 17)

**Folie 15, Divider.**

**Folie 16, A run ends for one of five reasons. Only one of them can be a PASS.** Tabelle der fünf Stop-Gründe (siehe Glossar) mit "wer entscheidet" und "kann PASS sein?". Nur `model_done` kann PASS sein, und nur, wenn der Checker zustimmt. Rechts die PASS-Definition: Agent hat "complete" gemeldet UND Checker gibt 1,0. Hintergrund: Diese Strenge ist eine bewusste Entscheidung; sie macht einige richtige Bildschirme zu FAILs (siehe Limitations). Mögliche Frage: "Ist das nicht unfair?" Antwort: Ein Agent, der nicht weiß, dass er fertig ist, würde in der echten Welt weiterklicken; das zählen wir als Fehler, und wir benennen es als Muster.

**Folie 17, Written while the run happens, in the lecture's format.** Eine echte Log-Zeile: task, run, model, observation, grounding, steps (budget), verifier, failure_class, recording, note. Geschrieben in `runs/log.csv` in dem Moment, in dem der Lauf endet, mit einer vorgeschlagenen Fehlerklasse; ein Mensch bestätigt sie am Video (Spalte failure_reviewed). Rechts die fünf Klassen. Hintergrund: Tag 1 Folie 52, der Dozent sagte wörtlich, die Präsentation am Freitag sei diese Tabelle, sortiert. Mögliche Frage: "Wer hat die Klassen zugeordnet?" Antwort: Code schlägt vor (Backup B8 erklärt wie), Mensch prüft; die im Vortrag gezeigten Läufe sind geprüft.

### Kapitel 4: What happened (Folien 18 bis 21)

**Folie 18, Divider.**

**Folie 19, V1 results: 5 of 9 pass, every failure is in the two harder tasks.** Belas Windows-Tabelle, neun Zeilen. Contacts 3/3, Markor 2/3 (Run 3: "complete" gemeldet, ohne je Save zu tippen, false_done), Note+SMS 0/3 (alle drei: Notiz gespeichert, Teilpunkte 0,5, dann in der SMS-App wiederholte Taps ohne Wirkung, grounding). Fußnote: Windows-Laptop, 0 ERROR, (?) = Vorschlag des Runners. Hintergrund: Das ist die Baseline, ehrlich. Der Dozent will genau diese Tabelle sehen. Zahlenquelle: `runs_windows/log.csv`.

**Folie 20, It typed "Hugo", never "Pereira", and said it was done.** Belas Trace eines V2-Laufs, mit eingebettetem Video (8× Geschwindigkeit) und sechs Schritten: Home-Screen-Tap geblockt, open_app contacts, "Hugo" in First name, Nummer in Phone, Save, "complete" → FAIL. Der eigene Gedanke des Modells in Schritt 11: "The contact has been successfully created." Klasse: lost_value, nicht false_done, weil das Symptom ("fertig" gesagt) eine Ursache hat (der Nachname hat das Gerät nie erreicht). "Not a one-off": in 5 von 6 tree-basierten Contacts-Läufen (V2, V3) fehlt der Nachname; V1 hat beide Namen jedes Mal getippt. Hintergrund: Pflicht "mindestens ein Fehler im Detail". Mögliche Frage: "Warum vergisst es den Nachnamen?" Antwort (ehrlich): Wir sehen es im Log, nicht im Kopf des Modells; die beste Hypothese ist, dass in der Textliste "Name" nach dem ersten Feld als erledigt gilt und nichts auf dem Bildschirm widerspricht; im Screenshot ist das leere Feld direkt darunter sichtbar. Und: Mit dem 8B-Modell verschwindet das Problem komplett (Folie 26d).

**Folie 21, Reliability check: strong on constraints, weak on verification. V3 added it, and it misfired.** Tabelle mit den Tag-4-Hebeln: Goal clarity, Observable state, Feedback, Verification, Recovery, Constraints, jeweils für V1/V2 und V3. V1/V2: Feedback schwach (nur "executed"), keine Prüfung vor "fertig" (der fehlende Nachname geht durch). V3: Feedback "deine Aktion hat nichts geändert" ist bei Save falsch (Markor speichert ohne sichtbare Änderung); Prüfschritt mit demselben 4B-Modell hat den fehlenden Nachnamen 3 von 3 Mal akzeptiert; Loop-Guard hat bei Save gefeuert und drei Läufe beendet; Constraints haben in allen Läufen gehalten. Unten der Satz: Jeder V3-Mechanismus nimmt an, dass eine erfolgreiche Aktion den Bildschirm ändert. Hintergrund: Das ist die Diagnose, die Kapitel 5 vorbereitet.

### Kapitel 5: What we changed and learned (Folien 22 bis 32), Liams Block

**Folie 22, Divider.** "One change at a time, the before-and-after numbers, where a fix belongs, and what is left open."

**Folie 23 (22b), Six sentences that 81 runs on two machines support.** Der Einstieg: sechs Sätze, jeder mit Beleg. (1) Grounding in Code: 3× schneller, keine Taps ins Leere (V1 → V2, beide Rechner). (2) Mit dem Tree verliert das 4B-Modell den Nachnamen in 5 von 6 Contacts-Läufen, das 8B-Modell in 0 von 6 (V2+V3 vs. V5+V6, Mac; V6 Run 2 kam nie bis zum Formular und zählt nicht als "verloren"). (3) Jeder Harness-Mechanismus hat Schritte gekostet und keiner die Quote erhöht (Schritte pro Lauf 12,9 → 14,6 (V3) → 14,8 (V4); Erfolg 2/9 → 0/9 und 1/9). (4) Richtiger Bildschirm ohne "fertig" in jeder Version ab V2 (V2 Markor 1, V3 Markor 1, V4 SMS 3, V5 Markor 3, V6 Contacts 3). (5) Keine Aufgabeninstanz bestand in allen sechs Versionen; die zwei .txt-Notizen nie nach V1 (Backup B12). (6) Zahlungsverbot musste nie feuern; Home-Screen-Regel in V2, V3, V6 (sechs geblockte Taps auf dem Mac, gezählt aus `result.json` → stats.blocked.home_screen). Wie man es hält: drei der sechs laut sagen, den Rest stehen lassen, 60 Sekunden.

**Folie 24 (23), What changed between the versions: one change for V2, five more for V3.** Belas Tabelle: Observation, Grounding, Harness-Zusätze, Modell (hier wird qwen3-vl:4b-instruct genannt, Pflicht), Tasks/Seeds, Guardrails, für V1, V2, V3. Unten: V1 → V2 ist eine Änderung, also zuordenbar; V2 → V3 stapelt fünf, also ein Pakettest. Mögliche Frage: "Warum fünf auf einmal?" Antwort: Zeit; jede einzeln wären fünf weitere Tage Läufe gewesen. Deshalb haben wir V4 bis V6 wieder als Einzeländerungen gefahren.

**Folie 25 (24), V2 is 3× faster and cheaper, and less successful. V3 is worse again.** Belas Balkendiagramm (56 %, 33 %, 0 %, Windows) und die Kostentabelle: Modellzeit pro Schritt 90 s → 28 s → 27 s; Tokens 1.905 → 1.069 → 1.120; Zeit pro Lauf 19 → 7 → 8 min; ungültige Antworten 0. Die Pflicht-Vorher-Nachher-Folie. Zahlenquelle: `runs_windows/summary.md`. Mögliche Frage: "Warum ist Windows so viel langsamer als der Mac (90 s vs. 23 s)?" Antwort: CPU-Inferenz auf einem i7 ohne GPU gegen Apple Silicon mit gemeinsamem Speicher.

**Folie 26 (25), Where the fix belongs: code fixed pointing and app choice, not judgement.** Tabelle mit fünf Fehlern: was wir versucht haben, wo wir es platziert haben (immer Programs = Code), ob es gewirkt hat, wo es wirklich hingehört. Grounding: Index statt Koordinaten, ja. Wrong_app: open_app nur per Name, ja, hielt in allen 81 Läufen. Lost_value: Statusleiste (V3), nein; gehört zu "Parameters: das 8B-Modell hat es behoben (V5), ein Code-Tracker nicht (V4)". False_done: Prüfschritt (V3), nein, derselbe schwache Prüfer; gehört zu einem stärkeren Modell oder zu Code, der den Zustand liest. Save-Schleife: Hinweis + Loop-Guard (V3), ging nach hinten los; gehört zu Instructions, ein Satz in einer Markor-Skill-Datei. Hintergrund: Die Tag-5-Tabelle "Knowledge, Instructions, Programs, Parameters": "Eine Regel, die nie umgangen werden darf → Programs. Ein Urteil, das man in einem Satz sagen kann → Instructions." Das ist starkes Q&A-Material, weil es zeigt, dass wir unsere eigenen Entscheidungen bewerten.

**Folie 27 (26), Run again on a MacBook: same ranking, same failure patterns, different single runs.** Tabelle Windows gegen Mac: V1 5/9 vs. 5/9, V2 3/9 vs. 2/9, V3 0/9 vs. 0/9, ERROR 0 vs. 11 (wiederholt), V1-Modellzeit 90 s vs. 23 s, Ollama 0.40.0/ef33995b vs. 0.35.1/ee4b975b. Rechts: gleiches Skript, gleiche Seeds, Temperatur 0; gleiche Muster; Einzelläufe anders, weil die Modelldatei nicht derselbe Build ist. Unten das Dozentenzitat: "If you change quantisation, or switch model, re-run your evaluation. It is a different model." Hintergrund: Reproduzierbarkeit live. Antwort auf "wie oft habt ihr es laufen lassen?": 81 Läufe auf zwei Rechnern.

**Folie 28 (26b), A bigger model fixed the lost surname. Two code fixes never fired.** Die Übersicht der drei Mac-Experimente: Tabelle V2 / V4 / V5 / V6 mit Erfolg (2/9, 1/9, 3/9, 1/9), Contacts (1/3, 0/3, 2/3, 0/3), Läufe mit verlorenem Nachnamen (2, 0, 0, 0), Modellzeit (6,3 / 9,3 / 7,3 / 14,6 s unter Last). Drei Punkte: V4 Veto nie gefeuert, Modell hat Schleifen gedreht; V5 +16 % Zeit, Nachname nie wieder verloren, Endungsfeld und fehlendes "fertig" bleiben; V6 Endungsfeld ist eine Tipp-Schleife, nicht Tippen, Hinweis wartete auf sichtbare Änderung. Unten: gleiches Modell, gleiche Seeds, Contacts 2/3 → 0/3 zwischen V5 und V6, drei Läufe finden Muster, keine Rangfolge. Zahlenquelle: `runs/summary.md` (Mac). Diese Folie ist die Landkarte; 26c und 26d sind die Beweise.

**Folie 29 (26c), V4: the code veto never fired. The prompt block did.** Links zwei Traces auf demselben Seed (Hugo Pereira): V2 geht Home, tippt auf die Suche, wird geblockt, die Nachricht sagt "nimm open_app", Schritt 3 macht es richtig, PASS in 11. V4 geht Home und drückt dann elfmal "zurück", step_limit. Rechts der wörtliche Gedanke des Modells, Schritt 4 bis 12 identisch: "I need to open the Contacts app… Since it's not visible on this screen, I should navigate back to find it." Vier Punkte: Es sucht die App auf dem Bildschirm und vergisst open_app; V2 machte denselben Fehler, tippte aber, die Guardrail antwortete; V4 drückt "back", darauf feuert keine Regel, nichts antwortet; der Tracker-Block wird in keinem Gedanken erwähnt und ist der einzige Prompt-Unterschied; alle drei Contacts-Läufe 0/3, 36 Schritte, kein Feld je berührt. Hintergrund: Das ist das stärkste Argument dafür, dass Prompt-Text bei kleinen Modellen ein Eingriff ist. Ehrliche Grenze: Warum das Modell "back" statt Tap wählt, steht nicht im Log. Zahlenquelle: `runs/v4_tracker/ContactsAddContact/run1_*/trajectory.jsonl`.

**Folie 30 (26d), The 8B model types the surname in 8 steps. The hint it ignores.** Links V5 Contacts Run 3 (Isla Martin): Create contact, "Isla", "Martin" in Last name, Nummer, Save, complete, PASS in 8 Schritten. V2 auf demselben Seed: "Isla", dann direkt Phone, Save, complete, FAIL. Gleicher Bildschirm, gleicher Prompt, 4B gegen 8B. Rechts V6 Note+SMS Run 3: Schritt 13 Text in die SMS, Schritt 14 SMS-Button, in der Historienzeile steht jetzt der Hinweis "All values from the goal are typed and you pressed a save/send button: if the goal is fully done, reply status complete now", Schritt 15 SMS-Button nochmal mit demselben Hinweis, Schritt 16 Home, Schritt 17 complete, Checker 0,5. Drei Punkte: Der Hinweis wird gelesen und der Button trotzdem nochmal gedrückt; bei Markor-Save erscheint er nie, weil Save nichts auf dem Bildschirm ändert und wir ihn an eine Änderung gekoppelt haben; 0,5 heißt Notiz da, SMS nicht angekommen, zweimal "SMS" drücken ist kein Senden [am Video prüfen]. Zahlenquelle: V5/V6-Lauflogs. Wie man es hält: "Das eine, was geholfen hat, und das eine, was nicht geholfen hat, als Läufe statt als Quoten."

**Folie 31 (27), One command per version. The config is the whole agent.** `python run_eval.py --config configs/v2_index.json`. Vier Punkte: gleiche Seeds für jede Version (AndroidWorlds Seed-Formel, Basis 30); Temperatur 0 und Modell-Seed, Name/Größe/Quantisierung/Digest pro Lauf gespeichert; AndroidWorld auf einen Commit gepinnt, Setup-Skripte für macOS und Windows, 226 Unit-Tests ohne Emulator; jeder Lauf hinterlässt trajectory.jsonl, Screenshots mit markiertem Tap, recording.mp4, eine Log-Zeile. Hintergrund: Bewertungskriterium Reproduzierbarkeit. Wer das Repo klont, baut die Tabelle nach.

**Folie 32 (28), Four things the runs told us that a demo would not have.** Die vier Findings (siehe Teil 1, Punkte 1, 2, 3, 5), jedes mit Beleg in der Unterzeile. Orange Linie markiert: Das ist die Essenz.

**Folie 33 (28b), What these numbers cannot tell you.** Sechs Grenzen in einer Tabelle, je mit Bedeutung und Beleg: 3 Läufe pro Aufgabe (Beleg: V5 → V6 Contacts 2/3 → 0/3 ohne Codeänderung auf dem Pfad); zwei Rechner, zwei Modelldateien (Digests); Emulator-Rauschen auf dem Mac (11 Abstürze, RAM-Wechsel 2 → 4 GB mitten in V1/V2, V6 unter Last); Fehlerklassen sind Vorschläge (nur gezeigte Läufe am Video bestätigt); strenge PASS-Regel (richtiger Zustand ohne "fertig" ist FAIL, 0,5 ist FAIL); kleine lokale Modelle, drei Aufgaben, "both" nie getestet, 3 von 116 Aufgaben. Wie man es hält: zwei Zeilen laut, die anderen stehen lassen; die Folie ist da, damit niemand diese Fragen stellen muss.

**Folie 34 (28c), What we would do next, in this order.** Fünf Schritte nach Nutzen pro Aufwand: (1) Zustand vom Gerät lesen statt vom Bildschirm: adb kann die Kontaktdatenbank und Markors Dateiliste lesen; das ist der Verifier, den V3 gebraucht hätte, modellunabhängig. (2) Observation "both": Tree fürs Zeigen, Screenshot fürs Layout; der Nachname ging nur mit dem Tree verloren; die Option existiert. (3) App-Wissen als Instructions: eine Markor-Skill-Datei mit "Save zeigt keine Bestätigung; Name und Endung sind getrennte Felder"; der Mechanismus (`use_skills`) ist gebaut und war aus, um V1 → V2 sauber zu halten. (4) Actor und Verifier trennen: 4B handelt, 8B prüft (V5 zeigt, dass 8B das Formular richtig liest; ein Prüfaufruf pro Lauf ist billig). (5) Done-Hint-Bedingung reparieren (beim Commit-Tap feuern, nicht bei sichtbarer Änderung), dann zehn Läufe pro Aufgabe auf einem Rechner, damit man ranken darf. Jeder Punkt folgt aus einer gemessenen Schwäche.

**Folie 35 (29), Takeaway.** "The model decides. The harness makes it safe, measurable and honest." Ein Satz, dann Danke.

**Folie 36 (30), Thank you.** Team, Kurs, Datum.

### Backup (Folien 37 bis 49), nur für die Fragerunde

**Folie 37 (31), Backup-Divider.** Listet, was folgt.

**Folie 38 (B1), V2 log rows.** Belas neun V2-Zeilen inklusive der zwei ERROR-Läufe (Emulator verloren, wiederholt). Für die Frage "zeig mal die ganze Tabelle".

**Folie 39 (B2), V3 stacks the remaining fixes.** Die fünf V3-Mechanismen mit der Fehlerklasse, die jeder adressieren sollte (too_early, grounding/Save-Schleife, lost_value, false_done), und das Ergebnis 0/9 auf beiden Rechnern.

**Folie 40 (B3), Skills, user memory, RAG.** Tabelle: Skills (gebaut: eine Tipp-Datei pro App, nur geladen, wenn die App vorne ist; in allen Versionen aus, weil ein Tipp den Agenten verändert und den V1 → V2-Vergleich bräche), User memory (nicht gebaut; nur die Notizzeile innerhalb eines Laufs in V3; jeder Lauf startet frisch mit neuen Werten), RAG (nicht gebaut; es gibt nichts abzurufen, der Agent braucht den aktuellen Bildschirm, und den liefert der Tree jeden Schritt). Für die Frage "warum habt ihr kein RAG/Memory?": Es war eine Entscheidung, keine Lücke, und wir können die Tag-2-Konzepte einordnen.

**Folie 41 (B4), The reward comes from the environment, never from the agent's own report.** Tag-5-Vokabular auf uns: Quelle des Rewards = AndroidWorlds Checker (verifizierbare Regel, der billigste und verlässlichste Reward); Information = eine Zahl, 1/0/0,5; Timing = einmal am Ende; Pfad = ein Ergebnis-Reward ist blind für den Weg, deshalb loggen wir Schritte, Fehlerklasse, Aufnahme. Rechts: 46 % eines V2-Laufs ist Warten auf den Emulator, nicht auf das Modell (102 s pro Lauf, 55 s davon Modell). "Reward hacking, unsere Version": "complete" sagen ohne zu prüfen; der Agent versucht es (false_done), der Verifier bezahlt es nicht.

**Folie 42 (B5), Same loop as one RL training step. Our update went into the harness, not the weights.** Links: ein RL-Trainingsschritt (Versuche, Reward, Vergleich, Update) neben unserer Evaluation (3 Läufe, AndroidWorld-Verifier, V1 gegen V2 auf denselben Instanzen, Update = eine Config-Änderung und neu laufen). Rechts die Tag-5-Faustregeln: Format instabil → SFT (bei uns nein, 0 ungültige Antworten); Domänenwissen fehlt → Mid-Training/Retrieval (nein, der Bildschirm ist das Wissen); Erfolg > 0, verlässlicher Reward, gute Strategie selten → RL (ja, das wäre unser Fall, aber ein Versuch kostet 2 bis 7 Minuten auf einem echten Emulator, nicht 10.000 Versuche in 10 Sekunden). Zitate: "A cheap simulator favours classic RL; costly or irreversible interaction favours an LLM agent." Für die Frage "warum habt ihr nicht trainiert?"

**Folie 43 (B6), Goal-value tracker: what code reads out of the goal.** Die fünf Extraktionsregeln in Reihenfolge (Freitext nach "with the following text:", Anführungszeichen, Dateiname mit Stamm und Endung getrennt, Telefonnummern nach den letzten 7 Ziffern, Folgen großgeschriebener Wörter ohne App-Namen und Verben), die Matching-Regel (Groß/Klein, Leerzeichen, Bindestriche, Punkt am Ende ignoriert; getippte Stücke werden auch zusammengesetzt), und rechts der STATUS-Block, wie ihn das Modell in V4 gesehen hat. Drei Punkte: jeden Schritt als letzter Block im Prompt; "complete" mit fehlendem Wert wird zurückgewiesen, höchstens zweimal, ohne Modellaufruf; in V4 kam es nie dazu, der Block allein hat das Verhalten verändert. Quelle: `gui_agent/goal_values.py`. Dieselbe Extraktion nutzt der Fehlerklassifizierer und der V6-Hinweis.

**Folie 44 (B7), Two code rules, their firing conditions, and why the failing runs never met them.** Tabelle: Regel "clear prefilled text" feuert, wenn input_text in ein editierbares Element geht, das Text zeigt, der nicht sein Platzhalter ist, der neue Text ihn nicht fortsetzt und der Agent ihn nicht selbst getippt hat; Wirkung: alles markieren und löschen vor dem Tippen; in den 9 V6-Läufen 0×, weil die Endungsfeld-Schleife aus 8 bis 14 Klicks besteht und nie aus input_text. Regel "done hint" feuert bei einem Tap auf Save/Send/SMS/OK/Done/Create/Add, wenn alle Werte getippt sind, kein Aktionsfehler vorliegt und der Bildschirm sich geändert hat; Wirkung: Satz in der Historienzeile; 1× (Note+SMS Run 3), bei Markor-Save nie, weil Save nichts ändert. Unten: beide Regeln aus den V4/V5-Logs geschrieben und an eine Bedingung gekoppelt, die die Fehlläufe nicht erfüllen; die Bildschirm-Bedingung ist V3s Autosave-Fehler, wiederholt; Fix: beim Commit-Tap feuern.

**Folie 45 (B8), How the suggested failure class is computed: root cause first, then symptom.** Reihenfolge und Signale: 1 wrong_app (open_app für eine App außerhalb der Liste, Aktion außerhalb der erlaubten Apps, oder Home-Screen-Taps ohne je eine App zu betreten), 2 lost_value (getippter Text, der nicht in der Aufgabe steht, oder manche Werte getippt und andere nie, während der Agent "complete" sagte), 3 grounding (≥ 2 Aktionen ohne Bildschirmänderung, oder ein Loop-Guard-Block, oder ein Tap auf kein Element plus eine wirkungslose Aktion), 4 too_early (Wirkung erst nach dem zusätzlichen Warten; nur mit wait_for_stable messbar, also V3), 5 false_done ("complete" gemeldet, Verifier FAIL, nichts von oben), sonst grounding (?) mit "check the recording". Jede Log-Zeile trägt die Beweiskette ("goal value(s) never typed: 'Martin'; 2 action(s) did not change the screen") und das Review-Flag. Ein einzelner Tap ins Leere reicht nicht für grounding, weil der Tree nur Blatt-Elemente listet und ein korrekter Tap auf das Padding einer Zeile auch "nichts trifft". Quelle: `gui_agent/failure.py`.

**Folie 46 (B9), Payment ban: two layers, six deny rules, no off switch.** Ebene 1 App-Scope: open_app nur per exaktem Namen aus der Whitelist; jede Aktion in einer App außerhalb des Scopes wird geblockt, außer Verlassen; Home-Screen-Taps geblockt. Ebene 2 Deny-Regeln a bis f: Zahlungs-App öffnen; alles außer Verlassen in einer solchen App; alles außer Verlassen auf einem Zahlungsformular; Taps und Tippen auf oder neben Elementen mit Pay/Buy/Checkout/Add-to-cart-Beschriftung, jedes Element unter dem Tap-Punkt wird geprüft, auch die Zeile um die Beschriftung; Tippen oder Enter ohne bekanntes Ziel, während ein Zahlungselement sichtbar ist; Tippen einer Kartennummer (13 bis 19 Ziffern, Luhn-Prüfsumme) oder IBAN (mod-97-Prüfsumme), am Stück oder in aufeinanderfolgenden Stücken. Eine geblockte Aktion kostet einen Schritt und sagt dem Modell warum. Quelle: `gui_agent/guardrails.py`, Test: ein gescriptetes Modell, das "Pay" tippt, erzeugt null Geräteaktionen.

**Folie 47 (B10), One config file per version: what each one switches on.** Links die Flag-Matrix V1 bis V6 (Modell, Observation/Grounding, wait_for_stable, screen_change_hint, loop_guard, status_bar, verify_before_done, goal_tracker, replace_prefilled_text/done_hint); genau eine Zeile ändert sich pro Versionssprung, außer bei V3. Rechts, was nie angefasst wurde: Temperatur 0 / Seed 42; Kontext 8.192 / Ausgabe 400 Tokens; Timeout 300 s → ERROR; 2 Parse-Retries; 8 Historienzeilen; maximal 70 Tree-Elemente, Statusleiste des Handys entfernt; Screenshot maximal 1.024 px; Budget min(20, complexity × 10); maximal 2 Done-Zurückweisungen; Skills aus, Zahlungsverbot immer an. Quelle: `gui_agent/config.py`, `configs/*.json`; jeder Lauf kopiert seine Config in `meta.json`.

**Folie 48 (B11), MacBook Air M4, all 54 scored runs: success and cost.** Die vollständige Mac-Tabelle: Erfolg pro Aufgabe und Version, Modellzeit pro Schritt, Zeit pro Lauf, Tokens, Schritte, ungültige Antworten. Fußnote zu V6 (unter Last) und zu den 11 ERROR-Läufen. Quelle: `runs/summary.md`.

**Folie 49 (B12), The same nine task instances through every version.** Neun Zeilen (je Aufgabe und Seed, mit dem konkreten Namen oder Dateinamen), sechs Spalten mit PASS/FAIL und Schrittzahl. Beobachtungen: Keine Instanz besteht in allen Versionen; die .txt-Notizen (Endungsfeld muss geändert werden) bestehen nach V1 nie; Hugo Pereira besteht in V1 und V2, ab V3 nie (V4 Back-Schleife, V5/V6 Umwege). Zeilen zeigen das Rauschen, Spalten das Muster. Für die Frage "ist das nicht alles Zufall?"

---

## Teil 4: Rollenvorschlag und Zeit

| Wer | Folien | Minuten |
|---|---|---|
| Sprecher 1 | 1 bis 5 (Einstieg, Aufgabe, drei Tasks) | 3 |
| Sprecher 2 | 6 bis 14 (Modell, Agent-Design, Beobachtung, Zeigen, Prompt, Aktionen, Guardrails) | 7 |
| Sprecher 3 | 15 bis 17 (Messung) | 2 |
| Bela | 18 bis 21 (V1-Ergebnisse, der eine Fehler, Reliability) | 5 |
| Liam | 22 bis 36 (Kapitel 5 komplett) | 10 |

Wer Folien 6 bis 14 übernimmt, sollte Folie 8 (acht Stufen) und Folie 12 (Prompt-Aufbau) sicher erklären können; die anderen Folien in dem Block sind Tabellen, die man zeigen und in einem Satz kommentieren kann. Wenn die Probe über 27 Minuten liegt: Folie 9 und 12 ins Backup, und auf 28 (26b) nur die Tabelle zeigen, die drei Punkte weglassen.

---

## Teil 5: Fragen, die kommen können, mit Antworten

**"Warum ist V1 besser als alles danach?"** Weil V1 mit dem Screenshot das räumliche Layout sieht: das leere Feld "Last name" direkt unter "First name", das Endungsfeld neben dem Namensfeld. Die Textliste ist präziser beim Zeigen, aber ärmer in genau dieser Information. V1 ist dafür viermal so teuer pro Schritt und tippt bei den SMS-Aufgaben ins Leere. Keine Version gewinnt überall.

**"Ist 5/9 gegen 3/9 überhaupt ein Unterschied?"** Nein, nicht statistisch, und das sagen wir auf der Limitations-Folie selbst. Was zählt, sind die Muster in den Trajektorien: Taps ins Leere in V1, verlorene Nachnamen in V2/V3, Schleifen in V4, das Endungsfeld in allen. Die Muster sind auf beiden Rechnern gleich.

**"Warum kein großes Cloud-Modell?"** Lokal, kostenlos, reproduzierbar, nichts verlässt den Laptop; und der Punkt des Projekts war, wo ein kleines Modell bricht und was die Harness dagegen kann. Ein Cloud-Modell wäre der nächste sinnvolle Vergleich.

**"Hat das Zahlungsverbot je gegriffen?"** Nein, in 81 Läufen null Zahlungsversuche; die Aufgaben führen nicht in Zahlungs-Apps. Es ist getestet (Unit-Tests mit gescriptetem Modell) und hat keinen Ausschalter. Die Home-Screen-Regel hat dagegen sechsmal gefeuert, und man sieht auf Folie 14, dass sie dem Modell hilft.

**"Warum habt ihr V3 nicht in fünf einzelne Versionen zerlegt?"** Zeit. Ein Lauf dauert 2 bis 7 Minuten, neun Läufe eine Stunde, und der Emulator stürzt auf dem Mac regelmäßig ab. V4 bis V6 waren wieder Einzeländerungen.

**"Was ist mit Memory, RAG, Skills?"** Backup B3: Skills sind gebaut und bewusst aus; Memory und RAG wären für diese Aufgaben ohne Nutzen, jeder Lauf startet frisch und das Wissen ist der Bildschirm.

**"Warum habt ihr nicht trainiert?"** Backup B5: Unser Fall erfüllt die RL-Bedingungen, aber ein Versuch kostet Minuten auf einem echten Emulator; der Dozent selbst: Wenn Wissen und Anweisungen reichen, braucht man kein RL.

**"Was war der größte Fehler?"** Zweimal dieselbe Annahme: dass eine erfolgreiche Aktion den Bildschirm sichtbar ändert. In V3 hat das alle Sicherheitsnetze bei Markor fehlzünden lassen; in V6 haben wir den Done-Hint an genau diese Annahme gekoppelt. Lehre: vor dem Coden die Trajektorie lesen, ob der Pfad überhaupt durch die neue Regel führt.

**"Was würdet ihr als Erstes ändern?"** Den Gerätezustand per adb prüfen statt den Bildschirm: Kontaktdatenbank und Dateiliste lesen, bevor "fertig" akzeptiert wird. Das fängt beide Hauptfehler, mit jedem Modell, und kostet keinen Modellaufruf.

**"Wie reproduziere ich das?"** Repo klonen, `scripts/setup_mac.sh` oder `setup_windows.ps1`, `python run_eval.py --config configs/<version>.json`, `python summarize.py`. Gleiche Seeds, Temperatur 0, Modell-Digest wird pro Lauf gespeichert; anderer Digest heißt andere Zahlen, aber gleiche Muster.
