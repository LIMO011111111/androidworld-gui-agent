# Sprechtext zu den Folien

**Nummern = Foliennummer im Browser** (Stand 08.10., nach dem Umbau in fünf Kapitel; Trennfolien zählen mit).

Stand 08.10.2026. Pro Folie: was drauf steht, was dazu gesagt wird, was die Zuhörer mitnehmen sollen. Wird fortgeschrieben, sobald eine Folie abgenommen ist.

---

## Folie 1: Titel

**Auf der Folie:** Titel „Agentic AI in Modern Business", Untertitel „A GUI agent for AndroidWorld, and where it breaks", die fünf Namen, TUM-Zeile, Uhrenturm.

**Was du sagst (15 Sekunden):** „Wir sind Gruppe … und haben einen Agenten gebaut, der ein Android-Handy bedient. Der Untertitel sagt schon, worum es geht: wo er bricht. Das war die Aufgabe, und das zeigen wir."

Der Modellname kommt hier bewusst nicht vor, er wird auf Folie 7 und 23 genannt.

---

## Folie 2: Agenda

**Auf der Folie:** die fünf Kapitel mit je einem Satz.

**Was du sagst (20 Sekunden):** „Fünf Kapitel: Was die Aufgabe war. Wie wir den Agenten gebaut haben. Wie wir gemessen haben. Was dabei herauskam. Und was wir geändert und gelernt haben." Nicht mehr. Die Sätze unter den Kapiteln nicht vorlesen.

Hinweis: Jede Folie trägt oben links ihr Kapitel, so sieht das Publikum jederzeit, wo wir sind.

---

## Folie 4: The assignment

**Überschrift:** Build an agent that operates a phone, measure it, improve it

**Auf der Folie:** drei Spalten mit je drei Stichpunkten.

| The task | The goal | The guidelines |
|---|---|---|
| A GUI agent for AndroidWorld | Not a demo: a measured result | Any model, but name it |
| One class, one `step()` | 3 tasks × 3 runs × 3 versions | Guardrails in code, not in the prompt |
| The agent only sees pixels and buttons | Failures explained, every version measured before and after | One task per difficulty row |

**Reihenfolge beim Sprechen:** erst die Aufgabe, dann das Ziel, dann die Regeln. Ungefähr 60 Sekunden.

### Spalte 1: The task

**1. A GUI agent for AndroidWorld**
GUI-Agent heißt: ein Programm, das eine grafische Oberfläche bedient, also das, was ein Mensch auf dem Handy sieht. AndroidWorld ist ein Testpaket von Google. Es enthält 116 Aufgaben wie „Kontakt anlegen" oder „Wecker stellen", die in echten Apps auf einem simulierten Handy (Emulator) laufen. Zu jeder Aufgabe gehört ein Prüfer, der hinterher im Gerät nachschaut, ob die Aufgabe wirklich erledigt ist.

**2. One class, one step()**
Das war die technische Vorgabe des Dozenten: Der ganze Agent ist eine Klasse mit einer Methode `step()`. Jeder Aufruf macht genau drei Dinge: Bildschirm anschauen, eine einzige Aktion wählen (tippen, Text eingeben, wischen), und melden, ob die Aufgabe fertig ist. Dieser Aufruf wird in einer Schleife wiederholt, bis „fertig" gemeldet wird oder das Schrittlimit erreicht ist.

**3. The agent only sees pixels and buttons**
Das ist der Unterschied zu einem normalen Programm: Es gibt keine Schnittstelle, über die man der Kontakte-App sagen könnte „leg diesen Kontakt an". Der Agent muss wie ein Mensch den Plus-Button finden, ins Namensfeld tippen, Text eingeben und speichern. Genau deshalb ist das schwer, und deshalb heißt der Untertitel der Präsentation „where it breaks".

### Spalte 2: The goal

**4. Not a demo: a measured result**
Zitat des Dozenten aus Tag 1: „My first question is: how many times did you run it?" Ein Video, in dem der Agent einmal klappt, zählt nicht. Verlangt ist eine Zahl: Wie oft von wie vielen Versuchen hat es geklappt?

**5. 3 tasks × 3 runs × 3 versions**
Drei Aufgaben, jede dreimal laufen lassen, mit drei Versionen des Agenten: 27 Läufe. Jeder Lauf bekommt eine Zeile in der Log-Tabelle. Ob ein Lauf bestanden ist, entscheidet der Prüfer von AndroidWorld, nicht der Agent selbst. Der Agent darf zwar „fertig" sagen, aber PASS gibt es nur, wenn der Prüfer das Ergebnis auch im Gerät findet.

**6. Failures explained, every version measured before and after**
Für jeden Fehlschlag wird eine Fehlerklasse vergeben, also warum es schiefging. Und jede Verbesserung muss mit Zahlen belegt sein: Erfolgsquote vorher, Erfolgsquote nachher. V1 ist der Ausgangspunkt, V2 ändert genau eine Sache (damit man weiß, woran ein Unterschied liegt), V3 packt die restlichen Fixes drauf.

### Spalte 3: The guidelines

**7. Any model, but name it**
Das Sprachmodell war frei wählbar: lokal auf dem Laptop, eigener Server oder Cloud-API. Pflicht ist nur, den Modellnamen in der Präsentation zu nennen. Und: Wer das Modell oder die Quantisierung (die komprimierte Variante des Modells) wechselt, hat ein anderes Modell und muss alle Läufe wiederholen. Unser Modell kommt auf Folie 7.

**8. Guardrails in code, not in the prompt**
Guardrails sind Sicherheitsregeln. Der Dozent verlangt, dass sie im Programmcode stehen und nicht als Bitte im Prompt („bitte nichts kaufen"), weil das Modell einen Prompt ignorieren kann, den Code aber nicht. Pflichtminimum: ein Schrittlimit (der Agent darf nicht endlos laufen) und ein vollständiges Zahlungsverbot.

**9. One task per difficulty row**
Die Aufgabenliste des Dozenten hat drei Schwierigkeitsstufen (Warm-up, Real work, Multi-app & memory). Aus jeder Stufe musste eine Aufgabe kommen. Begründung des Dozenten: Wer nur leichte Aufgaben nimmt, findet nie heraus, wo der Agent bricht. Außerdem muss jeder Lauf als Bildschirmvideo aufgezeichnet werden, plus ein Schritt-für-Schritt-Protokoll (Trajectory), was der Agent gesehen und getan hat.

### Was die Zuhörer mitnehmen sollen

Die Aufgabe war nicht „bau einen Agenten", sondern „bau einen Agenten und miss ehrlich, wo er versagt". Alles Weitere in der Präsentation folgt aus diesen Regeln.

### Mögliche Rückfragen

- „Warum drei Versionen?" V1 ist die einfachste Variante, V2 ändert genau eine Sache, damit der Effekt zuordenbar ist, V3 enthält die restlichen Fixes. Nur V1 → V2 ist ein sauberer Vergleich, V2 → V3 bündelt mehrere Änderungen.
- „Was ist ein Emulator?" Ein simuliertes Android-Handy, das auf dem Laptop läuft. Gleiche Apps, gleiches System, nur ohne Hardware.

---

## Folie 5: Use case, die drei Tasks

**Überschrift:** The three tasks: a contact, a note, a note sent by SMS

**Auf der Folie:** eine Tabelle mit vier Spalten.

| Difficulty | Task | What the agent is told | Budget |
|---|---|---|---|
| Warm-up | ContactsAddContact | Create a new contact for {name}. Their number is {number}. | 12 |
| Real work | MarkorCreateNote | Create a new note in Markor named {file_name} with the following text: {text} | 16 |
| Multi-app & memory | MarkorCreateNoteAndSms | Create a note named {file_name} with {text}. Share its entire content with {number} via SMS. | 18 |

Darunter ein Satz: Die Klammern füllt AndroidWorld bei jedem Lauf neu. Budget = Komplexität × 10, gedeckelt durch unser Limit.

**Worum es geht:** Auf Folie 4 wurde gesagt, dass pro Schwierigkeitsstufe ein Task Pflicht war. Hier wird gezeigt, welche drei wir gewählt haben und warum. Ungefähr 60 Sekunden.

### Spalte für Spalte

**1. Difficulty**
Die drei Stufen stammen aus der Task-Liste des Dozenten. Warm-up ist eine App, ein Formular. Real work ist mehr Schritte in einer App. Multi-app & memory heißt: zwei Apps, und der Agent muss sich etwas aus App eins merken, um es in App zwei zu verwenden.

**2. Task**
Das sind die Namen, die AndroidWorld den Aufgaben gibt. Kontakt anlegen in der Kontakte-App. Markor ist ein Notiz-Editor für Textdateien, eine Open-Source-App, die in AndroidWorld vorinstalliert ist. Der dritte Task kombiniert Markor mit der SMS-App.

**3. What the agent is told**
Das ist wörtlich der Text, den der Agent als Aufgabe bekommt. Die geschweiften Klammern sind Platzhalter. AndroidWorld setzt bei jedem Lauf einen anderen Namen, eine andere Nummer, einen anderen Text ein. Der Agent kann also nichts auswendig lernen, jeder Lauf ist ein echter Test. Der Prüfer von AndroidWorld weiß, was eingesetzt wurde, und schaut hinterher nach, ob genau das im Gerät steht.

**4. Budget**
Jede Aufgabe hat in AndroidWorld eine Komplexitätszahl. Wir erlauben zehn Schritte pro Komplexitätspunkt, also 12, 16 und 18 Schritte. Wer das Budget aufbraucht, ohne fertig zu sein, ist durchgefallen. Unser hartes Limit liegt bei 20 Schritten, darüber geht nie etwas.

### Warum genau diese drei (der eigentliche Punkt der Folie)

Wir wollten nicht drei Aufgaben, bei denen der Agent gut aussieht, sondern eine Treppe. Kontakt anlegen sollte klappen, sonst stimmt etwas Grundsätzliches nicht. Die Notiz testet Texteingabe und Dateinamen. Der dritte Task zwingt den Agenten, den Notiztext in eine zweite App zu tragen. Das ist die Stelle, an der kleine Modelle typischerweise den Wert verlieren. Diese Fehlerklasse heißt bei uns lost_value, sie kommt später wieder.

### Was die Zuhörer mitnehmen sollen

Die Tasks sind so gewählt, dass die Schwierigkeit steigt und der Agent irgendwo bricht. Genau das wollen wir sehen.

### Vor dem Vortrag prüfen

- Die Budget-Zahlen 12 / 16 / 18 stammen aus den Mac-Läufen. Nach den Windows-Läufen in `meta.json` nachsehen, ob sie identisch sind.

### Mögliche Rückfragen

- „Warum keine noch schwerere Aufgabe?" Mit einem kleinen Modell dauert ein Lauf mehrere Minuten. Drei Tasks mal drei Läufe mal drei Versionen sind 27 Läufe. Eine vierte Aufgabe hätte die Zeit gesprengt.
- „Was ist Markor?" Ein Open-Source-Editor für Markdown- und Textdateien, in AndroidWorld vorinstalliert.

### Exkurs: Was das Budget bedeutet (gehört zu Folie 5, kann auch bei Folie 16 „When a run stops" kommen)

Das Budget ist die Anzahl Schritte, die der Agent für einen Lauf bekommt. Ein Schritt ist ein Aufruf von `step()`: einmal Bildschirm anschauen, eine Aktion ausführen. Tippen auf den Plus-Button ist ein Schritt, Name eintippen der nächste, Speichern wieder einer.

Zwei Zahlen spielen zusammen:

1. **Unser hartes Limit: 20 Schritte.** Steht im Code als Guardrail und gilt immer. Mehr als 20 Schritte gibt es nie.
2. **Das Aufgaben-Budget: Komplexität × 10.** AndroidWorld gibt jeder Aufgabe eine Komplexitätszahl (grob: wie viele Handgriffe ein Mensch braucht). Kontakt anlegen 1,2, Notiz 1,6, Notiz plus SMS 1,8. Mal zehn ergibt 12, 16 und 18.

Regel im Code: Das Aufgaben-Budget darf das harte Limit nur senken, nie erhöhen. Bei unseren drei Tasks liegt es immer unter 20, also gilt pro Lauf nur die Aufgabenzahl. Die 20 würde erst greifen, wenn eine Aufgabe rechnerisch mehr als 20 bekäme.

**Beispiel Kontakt anlegen, Budget 12:**

- Fertig in 9 Schritten, Prüfer bestätigt: PASS.
- Fertig genau im 12. Schritt, Prüfer bestätigt: PASS.
- Nach 12 Schritten nicht fertig: Lauf wird sofort abgebrochen, Stop-Grund `step_limit`, FAIL. Einen 13. Schritt gibt es nicht.

**Zwei Dinge, die oft verwechselt werden:**

1. „Fertig" heißt: Der Agent hat `done` gemeldet. Wenn er nach 9 Schritten den Kontakt gespeichert hat, aber nie „done" sagt und weiter tippt, läuft er bis Schritt 12 und ist FAIL. Das Budget zählt Schritte, nicht Erfolg.
2. „done" allein reicht nicht. PASS gibt es nur, wenn der Agent „done" sagt **und** der Prüfer von AndroidWorld das Ergebnis im Gerät findet. Sagt er „done", aber der Nachname fehlt, ist das FAIL mit Fehlerklasse `false_done`. Genau das war unser Windows-Lauf vom 08.10.

**Warum das wichtig ist:**

- Ohne Limit könnte der Agent endlos im Kreis tippen. Das ist eine der drei Arten aus Tag 1, wie die Schleife bricht; das Schrittlimit ist die Pflicht-Guardrail dagegen.
- Das Budget macht Läufe vergleichbar: Jede Version bekommt für dieselbe Aufgabe dieselbe Anzahl Versuche.
- In der Log-Zeile steht später „steps 11 (12)": 11 gebraucht von 12 erlaubt. Daran sieht man, ob der Agent knapp oder locker durchkam.

**Kurzform für den Vortrag:** „Jeder Lauf hat ein festes Schrittbudget. Fertig und bestätigt innerhalb des Budgets ist PASS, alles andere ist FAIL."

---

## Folie 7: The model

**Überschrift:** Which model we use and how it is configured

**Auf der Folie:** links eine Tabelle mit sieben Zeilen, rechts vier Stichpunkte.

**Worum es geht:** Hier wird zum ersten Mal das Modell genannt (Pflicht). Dazu die Begriffe aus Tag 1: Wo läuft ein Modell, wie viel Speicher braucht es, was bedeuten Temperatur und Seed. Ungefähr 90 Sekunden.

### Die Tabelle, Zeile für Zeile

**1. Model: qwen3-vl:4b-instruct, 4.4B parameters**
Ein Modell von Alibaba. „VL" heißt Vision-Language: Es kann Bilder sehen und Text lesen. 4,4 Milliarden Parameter, das ist klein. Große Cloud-Modelle haben hunderte Milliarden.

**2. Where it runs: laptop, Ollama server**
Ollama ist ein Programm, das Modelle lokal auf dem Rechner laufen lässt. Der Agent schickt jeden Schritt an diesen lokalen Server, nicht ins Internet. Kein Screenshot verlässt den Laptop.

**3. Quantisation: Q4_K_M, 4 bits per weight**
Quantisierung heißt, die Zahlen im Modell werden gröber gespeichert, hier mit 4 Bit statt 16. Das Modell wird kleiner und schneller, verliert aber etwas Genauigkeit. Deshalb sagt der Dozent: Wechselt man die Quantisierung, ist es ein anderes Modell.

**4. Memory for weights: 3.3 GB**
Die Rechnung aus Tag 1: Parameter mal Bytes pro Parameter. 4,4 Milliarden mal ein halbes Byte sind 2,2 GB, dazu der Bildteil des Modells, macht etwa 3,3 GB. Das passt in den Arbeitsspeicher eines normalen Laptops.

**5. Context window: 8,192 tokens**
Das Kontextfenster ist, wie viel Text das Modell auf einmal sehen kann. Tokens sind Textbausteine, ungefähr ein Wort oder Wortteil. Der Ollama-Standard ist 4.096, das war zu klein, weil Bildschirmbaum, Screenshot, Aufgabe und Verlauf nicht hineinpassten. Also verdoppelt.

**6. Sampling: temperature 0, seed 42**
Temperatur steuert den Zufall. Bei 0 nimmt das Modell immer das wahrscheinlichste nächste Wort: keine Kreativität, dafür dasselbe Ergebnis bei gleicher Eingabe. Der Seed ist der Startwert des Zufallsgenerators, fest auf 42. Beides zusammen macht Läufe wiederholbar. Top-p haben wir nicht angefasst, bei Temperatur 0 spielt es keine Rolle.

**7. Output: max 400 tokens, JSON-schema constrained**
Das Modell darf pro Schritt höchstens 400 Tokens antworten, und die Antwort muss einem festen Format entsprechen. Das Format kommt auf Folie 13.

### Die vier Stichpunkte rechts

**Free after download, slow, small only**
Tag 1 nennt drei Orte, wo ein Modell laufen kann: Laptop, eigener Server, Cloud-API. Laptop kostet nichts, ist aber langsam und nur für kleine Modelle. Wir haben den Laptop gewählt. Ein Wechsel zur Cloud wäre eine Zeile in der Konfiguration.

**Temperature 0 + fixed seed, so a result can be repeated**
Pointe aus Tag 1: „A demo that worked once tells you almost nothing."

**The variant that answers at once, not the one that thinks first**
Qwen3-VL gibt es in zwei Ausführungen desselben Modells. Die „Thinking"-Ausführung schreibt vor jeder Antwort erst einen langen inneren Gedankengang (oft hunderte Wörter) und antwortet dann. Die „Instruct"-Ausführung antwortet direkt. Bei einem Agenten, der pro Lauf bis zu 20 Mal gefragt wird, würde das Nachdenken jeden Schritt um ein Vielfaches verlängern. Deshalb die direkte Ausführung. Im Modellnamen steht das als `-instruct`.

**Every run records name, size, quantisation and digest**
Jeder Lauf speichert in einer Datei (`meta.json`), welches Modell genau lief, inklusive Prüfsumme (Digest). Ändert sich eine der Angaben, ist es ein anderes Modell und alles muss neu laufen.

### Was die Zuhörer mitnehmen sollen

Klein, lokal, deterministisch. Wir haben bewusst ein schwaches Modell genommen, damit der Harness zeigen muss, was er kann.

### Mögliche Rückfragen

- „Warum so ein kleines Modell?" Es läuft auf jedem Gruppenlaptop ohne Kosten, und die Fehler eines kleinen Modells zeigen deutlicher, welche Teile des Harness etwas bringen.
- „Was ist top-p?" Ein zweiter Zufallsregler: Das Modell wählt nur aus den wahrscheinlichsten Wörtern, deren Wahrscheinlichkeiten zusammen p ergeben. Bei Temperatur 0 wird ohnehin immer das eine wahrscheinlichste gewählt, also ohne Wirkung.

---

## Folie 8: Agent design

**Überschrift:** Agent design: the eight stages of one step()

**Auf der Folie:** oben eine Kette aus acht Kästchen (Stufe 0 bis 7), jedes unten rechts mit C (Code) oder M (Modell) markiert, das Modell-Kästchen blau. Darunter eine Tabelle mit den fünf Harness-Teilen aus der Vorlesung und der Stufe, in der jeder bei uns steckt.

**Um was es geht:** Wie unser Agent innen aufgebaut ist. Pflichtinhalt „Agent-Design". Ungefähr 90 Sekunden.

**Was man verstehen soll:** Der Agent ist nicht „das Modell". Der Agent ist eine feste Kette aus acht Stufen, die bei jedem Schritt in derselben Reihenfolge durchläuft. Nur eine Stufe ist das Modell. Die anderen sieben sind unser Code. Der Dozent nennt diesen Code den Harness. Wenn wir den Agenten verbessern, ändern wir den Harness, nicht das Modell.

### Die acht Stufen

| Stufe | Was passiert | Wer |
|---|---|---|
| 0 budget | Ist noch ein Schritt übrig? Sonst Abbruch | Code |
| 1 observe | Bildschirm lesen: Screenshot (V1) oder Liste der Bedienelemente (V2, V3) | Code |
| 2 decide | Das Modell wählt genau eine Aktion, als JSON, z. B. „tippe auf Element 3" | **Modell** |
| 3 validate | Code prüft die Antwort (gültiges JSON? Aktionstyp bekannt? Element vorhanden?), bei Fehler einmal neu versuchen | Code |
| 4 ground | Aus „Element 3" wird eine Pixelposition, per Nachschlagen im Code | Code |
| 5 check | Guardrails: Zahlungsverbot, erlaubte Apps, Schleifenwächter | Code |
| 6 act | Aktion auf dem Gerät ausführen | Code |
| 7 feedback | Hat sich der Bildschirm geändert? Eine Zeile Verlauf schreiben, die das Modell im nächsten Schritt sieht | Code |

Dann wieder von vorn, bis das Modell „done" meldet oder das Budget aufgebraucht ist.

### Die Tabelle darunter

Tag 1 sagt: Ein Harness hat fünf Teile. Die Tabelle zeigt, wo jeder bei uns steckt. Nicht vorlesen, nur darauf zeigen: „Die fünf Harness-Teile aus der Vorlesung stecken alle in dieser Kette, hier die Zuordnung."

| Harness-Teil | Stufe bei uns |
|---|---|
| Loop control (wann das Modell wieder gefragt wird, wann Schluss ist) | Stufe 0 + Stop-Regeln |
| Context assembly (was ins Kontextfenster kommt) | Stufe 1 |
| Tool dispatch (aus JSON einen echten Tipp machen) | Stufen 4 und 6 |
| Error recovery (Antwort kaputt, keine Wirkung: nochmal, reparieren oder aufgeben) | Stufen 3 und 7 |
| Guardrails (was verboten ist, was geloggt wird) | Stufe 5 |

### Bild zum Erklären: die Abteilung um den Sachbearbeiter

Ein Sachbearbeiter soll Formulare am Handy ausfüllen, aber die Firma vertraut ihm nicht ganz. Also baut sie einen Ablauf um ihn herum: Einer prüft, ob er heute noch Aufträge machen darf (budget). Einer legt ihm ein Foto vom Bildschirm hin (observe). **Der Sachbearbeiter schaut hin und sagt: „Tipp auf Element 3"** (decide). Einer prüft, ob das eine gültige Anweisung ist (validate). Einer schaut nach, wo Element 3 genau liegt (ground). Einer prüft, ob das erlaubt ist (check). Einer tippt (act). Einer notiert, was passiert ist (feedback).

Der Sachbearbeiter ist das Modell. Alle anderen sind Code, den wir geschrieben haben. Die ganze Abteilung ist der Agent.

### Wie Code und Modell zusammenspielen

Der Code bereitet alles vor, stellt dem Modell eine Frage, bekommt eine Antwort, erledigt alles danach. Das Modell sieht nie das Handy direkt. Es bekommt vom Code einen Text (in V1 auch ein Bild), antwortet mit einer Aktion im JSON-Format, und der Code macht daraus eine echte Berührung auf dem Bildschirm.

**Wichtig:** Das Modell entscheidet nicht, ob die Aufgabe erledigt ist. Es entscheidet bei jedem Schritt, **was als Nächstes getan wird**. Es darf „fertig" sagen, aber das ist nur seine Behauptung. Ob die Aufgabe wirklich erledigt ist, entscheidet der Prüfer von AndroidWorld, der hinterher ins Gerät schaut. Das Modell kann „fertig" sagen und trotzdem FAIL bekommen: Fehlerklasse false_done.

### Warum es wichtig ist, das zu sagen

1. **Es erklärt, was wir gebaut haben.** Das Modell haben wir heruntergeladen. Unsere Arbeit sind die sieben Code-Stufen.
2. **Es erklärt, warum unsere Verbesserungen wirken.** V1 zu V2 ändert nur Stufe 1 und 4 (wie das Modell den Bildschirm sieht, wer die Position bestimmt). Das Modell blieb gleich, das Ergebnis wurde anders. Der Code um das Modell herum entscheidet mit.
3. **Es ist die Kernbotschaft des Kurses.** Tag 1: Der Harness ist alles um das Modell herum, und keine der drei Arten, wie ein Agent scheitert, wird durch ein klügeres Modell behoben. Unser Schlusssatz: „The model decides. The harness makes it safe, measurable and honest."

### Was du sagst, in dieser Reihenfolge

1. „Unser Agent ist eine Pipeline mit acht Stufen. Jeder Schritt läuft sie einmal durch."
2. Die Kette kurz abgehen, ein Halbsatz pro Kästchen. Das blaue betonen: „Nur hier ist das Modell. Die sieben anderen sind unser Code, deshalb das C und das M."
3. „Die fünf Harness-Teile aus der Vorlesung verteilen sich auf die Code-Kästchen, hier die Zuordnung."
4. Schlusssatz: „Das Modell sagt nur, was als Nächstes getan wird. Alles davor und danach ist unser Code. Zusammen ist das der Agent."

### Mögliche Rückfragen

- „Warum ist Grounding nicht im Modell?" Wenn der Code die Position nachschlägt, ist ein Zeigefehler sichtbar und dem Code zuzuordnen. Rät das Modell die Position, weiß man nie, ob es falsch gesehen oder falsch gezeigt hat. Kommt auf Folie 11.
- „Was habt ihr selbst geschrieben?" Alle sieben Code-Stufen: Beobachtung, Prompt-Aufbau, Validierung, Grounding, Guardrails, Ausführung, Verlauf. Das Modell und AndroidWorld sind fertige Bausteine.
- Die Sprechernotiz zitiert den Course Reader: nur Harness geändert, Genauigkeit von 53 auf 66 Prozent. Vor dem Vortrag die Stelle im Reader nachschlagen, falls der Dozent nachfragt.

---

## Folie 9: One step of the ReAct loop

**Überschrift:** One step of the ReAct loop: reason → act → observe

**Auf der Folie:** links Schritt 5 aus unserem Kontakt-Lauf, aufgeteilt in REASON / ACT / OBSERVE. Rechts eine Tabelle: Werkzeug-Kategorien aus der Vorlesung, je mit Phase und dem, was bei uns dazugehört.

**Um was es geht:** Folie 8 zeigte die Kette mit acht Stufen. Folie 9 zeigt einen einzigen echten Durchlauf und gibt dem Muster seinen Namen: ReAct. Ungefähr 60 Sekunden.

**Was ReAct ist:** Aus „Reason" und „Act" zusammengesetzt. Ein Agent handelt nicht einfach, sondern tut bei jedem Schritt drei Dinge: überlegen (Reason), handeln (Act), das Ergebnis anschauen (Observe). Dann wieder von vorn. Das Überlegen ist nicht versteckt, sondern Teil der Antwort und landet im Log. Deshalb kann man hinterher nachlesen, was sich das Modell gedacht hat.

### Links: der Trace

- **REASON:** Das Modell schreibt: „Ich muss einen Kontakt für Hugo Pereira anlegen. Der Button ‚Create contact' ist sichtbar."
- **ACT:** Das Modell gibt die Aktion aus: click, index 1. Also tippe auf Element 1, den Button.
- **OBSERVE:** Unser Code tippt, liest den Bildschirm neu und stellt fest: Bildschirm hat sich geändert, neue Liste mit 12 Elementen. Er schreibt die Verlaufszeile „5. click [1] Create contact -> executed". Die bekommt das Modell im nächsten Schritt zu sehen.

### Rechts: die Tabelle

Die Vorlesung sortiert Werkzeuge eines Agenten in Kategorien. Die Tabelle beantwortet: Welche haben wir, und in welche Phase des Loops gehören sie?

| Zeile | Was sie sagt |
|---|---|
| Reason / no tool | Fürs Überlegen gibt es kein Werkzeug. Das ist der Gedanke des Modells selbst, wir schreiben ihn nur ins Log |
| Act / Execution tools | Werkzeuge zum Handeln. Unsere acht: tippen, lange drücken, Text eingeben, scrollen, App öffnen, zurück, Home, Enter |
| Act / Collaboration, user communication | Werkzeuge, um mit einem Menschen oder anderen Agenten zu reden. Haben wir nicht. Der Agent kann nur „infeasible" melden, wenn er aufgibt |
| Observe / Perception tools | Werkzeuge zum Wahrnehmen. Bei uns: Bildschirm lesen, als Tree oder Screenshot |
| Act + Observe / Plugin „Computer Use" | Die Vorlesung nennt „Computer Use" als Beispiel für ein fertiges Paket aus Wahrnehmen und Handeln. Bei uns ist dieses Paket AndroidWorld: Es liefert den Bildschirm und die Aktionen |
| before the loop / Tool discovery, MCP | Mechanismen, mit denen ein Agent erst herausfindet, welche Werkzeuge es gibt. Passiert vor dem Loop, nicht darin. Bei zehn festen Aktionen unnötig |

**Was man verstehen soll:** Unser Agent hat nur zwei Sorten Werkzeuge, Wahrnehmen und Handeln. Alles andere (Kommunikation, Werkzeugsuche, MCP) lohnt erst bei vielen oder wechselnden Werkzeugen. Wir haben zehn feste.

### Was du sagst, in dieser Reihenfolge

1. „Das Muster heißt ReAct: überlegen, handeln, beobachten. Hier ein echter Schritt."
2. Links die drei Zeilen in eigenen Worten.
3. „Rechts die Werkzeug-Kategorien aus der Vorlesung. Wir haben Wahrnehmen und Handeln. Kommunikation und Werkzeugsuche brauchen wir nicht, zehn feste Aktionen reichen."

### Mögliche Rückfragen

- „Was ist MCP?" Model Context Protocol, ein Standard, über den ein Modell fremde Werkzeuge entdecken und ansprechen kann. Sinnvoll bei vielen Werkzeugen, bei zehn festen nicht.
- „Warum acht Aktionen in der Tabelle, aber zehn auf der nächsten Folie?" Acht Ausführungs-Aktionen plus „wait" (warten) und „status" (fertig oder unmöglich melden). Die zwei letzten handeln nicht auf dem Gerät.

---

## Folie 10: What the agent sees

**Überschrift:** Pixels see everything but point badly. The tree is precise but incomplete.

**Auf der Folie:** zwei Spalten. Links „Screenshot" mit Marke V1, rechts „Accessibility tree" mit Marken V2 und V3 und einem echten Ausschnitt aus unserem Lauf.

**Um was es geht:** Die erste große Designentscheidung: Wie bekommt das Modell den Bildschirm zu sehen? Das ist Stufe 1 (observe) aus der Kette. Es gibt zwei Wege, und wir haben beide gebaut: V1 nimmt den einen, V2 und V3 den anderen. Diese Folie ist der Grund für unseren Vorher-Nachher-Vergleich. Ungefähr 60 Sekunden.

**Was man verstehen soll:** Ein Screenshot zeigt alles, ist aber teuer, und das Modell muss selbst herausfinden, wo was ist. Der Accessibility Tree ist eine Textliste aller Bedienelemente mit Nummern und exakten Positionen: billig und präzise, aber was keinen Namen hat, fehlt darin. Keiner der beiden Wege ist einfach „besser", es ist ein Tausch.

### Links: Screenshot (V1)

- Sieht jeden Pixel, auch Webinhalte und Zeichnungen.
- Etwa 1.900 Tokens pro Schritt. Zitat Dozent: „the most expensive thing in the window".
- Das Modell muss die Zeile selbst finden und die Position selbst raten.

### Rechts: Accessibility tree (V2, V3)

Beispiel aus unserem Lauf:

```
[1] ImageButton "Create contact"
[2] Button "Don't allow"
[7] EditText "First name"
[10] EditText "Phone"
```

- Etwa 980 Tokens pro Schritt, exakte Positionen.
- Was keine Beschreibung hat, ist einfach nicht da.

### Begriffe

- **Accessibility Tree:** Android führt für Screenreader (Hilfe für Blinde) eine Liste aller Elemente auf dem Bildschirm: Typ, Beschriftung, Position. Wir lesen diese Liste aus und geben sie dem Modell als Text, jede Zeile mit einer Nummer. Das Modell antwortet dann „tippe auf 7" statt „tippe bei Pixel 540, 812".
- **Tokens pro Schritt:** Was das Modell pro Anfrage lesen muss. Ein Screenshot kostet fast doppelt so viel wie die Liste. Bei bis zu 20 Schritten summiert sich das, und das Kontextfenster ist mit 8.192 begrenzt.

### Was du sagst, in dieser Reihenfolge

1. „Der Dozent nennt das die erste echte Designentscheidung des Projekts: Was sieht das Modell?"
2. Links: „V1 bekommt den Screenshot. Sieht alles, kostet fast 1.900 Tokens, und das Modell muss die Position selbst raten."
3. Rechts: „V2 und V3 bekommen die Liste der Bedienelemente, so sieht die aus. Halb so teuer, exakte Positionen, aber was keine Beschriftung hat, existiert für das Modell nicht."
4. Überleitung: „Wir haben beide gebaut, das ist unser Vorher-Nachher. Die zweite Hälfte der Entscheidung ist, wer die Position bestimmt: nächste Folie."

### Vor dem Vortrag prüfen

- Die Zahlen 1.900 und 980 stammen aus den Mac-Läufen. Nach den Windows-Läufen aus `summary.md` nachziehen.

### Mögliche Rückfragen

- „Warum nicht beides zusammen geben?" Geht, kostet dann die Summe der Tokens. Mit 8.192 Kontext und einem 4B-Modell wollten wir erst messen, was jede Quelle allein bringt.
- „Was fehlt im Tree typisch?" Alles, was nur gezeichnet ist: Inhalte in Web-Ansichten, Karten, Diagramme, Icons ohne Beschriftung.

### Marken für die Versionen (gilt im ganzen Deck)

Jede Version hat ab jetzt eine feste Marke: **V1** grau, **V2** hellblau, **V3** TUM-blau. Sie steht überall dort, wo eine Folie eine Version nennt.

---

## Folie 11: How it points

**Überschrift:** How the agent points: coordinates vs. index

**Auf der Folie:** zwei Kästen nebeneinander. Links „By coordinate" mit Marke V1, rechts „By index" mit Marken V2 und V3, jeweils mit der echten Modellantwort und zwei Sätzen Erklärung. Sonst nichts.

**Um was es geht:** Die zweite Hälfte der Designentscheidung. Folie 10 war: Was sieht das Modell? Folie 11 ist: Wer bestimmt, **wo** getippt wird? Das ist Stufe 4 (ground) aus der Kette. Grounding heißt: aus „Ich will das Namensfeld" eine konkrete Stelle auf dem Bildschirm machen. Ungefähr 60 Sekunden.

**Was man verstehen soll:** In V1 rät das Modell die Pixelkoordinaten selbst. In V2 und V3 sagt das Modell nur eine Nummer aus der Liste, und unser Code schlägt die Position nach. Der Unterschied ist nicht nur Genauigkeit, sondern: Wenn es schiefgeht, weiß man in V2, wer schuld war. Das ist die eine Änderung zwischen V1 und V2.

### Links: By coordinate (V1)

```
{"action_type": "click", "x": 540, "y": 735}
```

Das Modell erzeugt die Zahlen selbst. 20 Pixel daneben, und der Tipp landet zwischen zwei Zeilen. Niemand meldet einen Fehler, der Lauf geht einfach weiter.

### Rechts: By index (V2, V3)

```
{"action_type": "click", "index": 3}
```

Unser Code sucht Element 3 in der Liste aus Folie 10. Entweder es ist da oder nicht. Gibt es kein Element 3, bekommt das Modell die Fehlermeldung und darf einmal neu antworten. Der Fehler ist sichtbar und wird geloggt.

### Der Satz, den du mündlich sagst (stand vorher auf der Folie)

„In V1 werden die Zahlen des Modells nie geprüft, ein falscher Tipp bleibt stumm. In V2 und V3 muss die Nummer in der Liste existieren, ein falscher Tipp wird von unserem Code abgefangen, bevor er passiert."

### Was du sagst, in dieser Reihenfolge

1. „Der Dozent sagt: Die meisten Fehler von GUI-Agenten sind Zeigefehler, keine Denkfehler. Der schwere Schritt ist das Zeigen."
2. Links: „In V1 muss das Modell die Pixelkoordinate selbst ausgeben. Liegt es 20 Pixel daneben, tippt es ins Leere, und keiner merkt es."
3. Rechts: „In V2 sagt das Modell nur ‚Element 3'. Unser Code schlägt nach, wo das liegt. Gibt es kein Element 3, bekommen wir eine Fehlermeldung."
4. Schlusssatz: „Wo das Grounding passiert, entscheidet, wen man verantwortlich machen kann. Und ein kleines Modell ist besser darin, eine Zeile zu wählen, als einen Pixel zu treffen."

### Dozentenzitate dazu (Tag 1)

- „Most GUI-agent failures are pointing failures, not reasoning failures."
- „Where grounding happens decides who you can blame."

### Mögliche Rückfragen

- „Was, wenn das Element nicht in der Liste ist?" Dann kann V2 es nicht antippen. Das ist die Schwäche des Trees von Folie 10. V3 hat dafür keine Lösung; das wäre ein Fall für einen Screenshot-Fallback, den wir nicht gebaut haben.
- „Woher weiß das Modell, welche Nummer das Namensfeld hat?" Aus der Liste, die es in jedem Schritt bekommt: jede Zeile hat eine Nummer, einen Typ und eine Beschriftung, z. B. `[7] EditText "First name"`.

---

## Folie 12: What the model sees each step

**Überschrift:** Old screens are never resent: one line per step, status last

**Auf der Folie:** links ein echter Prompt aus unserem Kontakt-Lauf (Schritt 4), rechts drei Punkte mit kurzer Erklärung.

**Um was es geht:** Was genau in der Anfrage an das Modell steht, und wie wir verhindern, dass sie mit jedem Schritt länger wird. Das ist Stufe 1 und 2 der Kette: das, was der Code dem Modell hinlegt, bevor es entscheidet. Zwei Konzepte aus der Vorlesung stecken drin: die Multi-Turn-Schleife mit Tool Calls und der KV-Cache. Ungefähr 90 Sekunden, eine der dichteren Folien.

**Was man verstehen soll:** Ein naiver Agent hängt bei jedem Schritt den neuen Bildschirm an den Verlauf an. Nach 20 Schritten sind das 20 Screenshots, über 20.000 Tokens, und das Kontextfenster (8.192) ist längst voll. Wir bauen die Anfrage stattdessen jeden Schritt neu: Der alte Bildschirm fliegt raus, nur eine Textzeile pro Schritt bleibt. Die Kosten pro Schritt bleiben flach. Und die Reihenfolge ist bewusst: Was sich nie ändert, steht vorn, was sich ständig ändert, ganz hinten.

### Der Prompt links, von oben nach unten

| Block | Was es ist |
|---|---|
| system (grau) | Rolle, erlaubte Aktionen, Regeln. Ändert sich im ganzen Lauf nie |
| GOAL | Die Aufgabe, hier: Kontakt Hugo Pereira anlegen |
| HISTORY (blau) | Eine Zeile pro bisherigem Schritt, von unserem Code geschrieben: „1. navigate_home -> executed", „2. click Search -> BLOCKED" |
| CURRENT SCREEN | Die Liste der Bedienelemente, nur vom aktuellen Schritt |
| STATUS (blau) | Schritt 4 von 12, aktuelle App, gemerkte Notiz (die Telefonnummer). Steht ganz am Ende |

### Die drei Punkte rechts

**1. A tool-call loop, but compressed**
Die Vorlesung zeigt die Schleife: Modell entscheidet, Programm führt aus, Ergebnis kommt als Nachricht zurück. Bei uns genauso, nur wird der Prompt jeden Schritt neu gebaut statt angehängt. Der alte Bildschirm fliegt raus, eine Textzeile pro Schritt bleibt.

**2. Stable prefix first, volatile last, so the KV cache hits**
Der KV-Cache ist der Zwischenspeicher des Modells. Wenn der Anfang der Anfrage identisch zur letzten ist, muss das Modell ihn nicht neu durchrechnen. Deshalb steht das Unveränderliche (Rolle, Regeln, erlaubte Aktionen) vorn und die Statuszeile, die sich jeden Schritt ändert, ganz hinten.

**3. History and status are written by code, not by the model**
Das Modell schreibt seinen Verlauf nicht selbst, das macht der Code. „BLOCKED" oder „hat nichts geändert" ist dann eine Tatsache, keine Einschätzung des Modells. In V3 kommt die Notizzeile dazu, die einen Wert (z. B. die Telefonnummer) in die nächste App mitnimmt: unser Fix für die Fehlerklasse lost_value.

### Was du sagst, in dieser Reihenfolge

1. „Das ist eine echte Anfrage an das Modell, Schritt 4 von unserem Kontakt-Lauf."
2. Von oben nach unten durchgehen, ein Satz pro Block. Betonen: „Der alte Bildschirm ist nicht mehr drin, nur die Zeile ‚Schritt 3: App geöffnet'."
3. „Warum diese Reihenfolge? Was sich nicht ändert, steht vorn, dann kann das Modell es wiederverwenden. Die Statuszeile ändert sich jeden Schritt, also steht sie ganz hinten."
4. „Und der Verlauf wird von unserem Code geschrieben, nicht vom Modell. Wenn da steht ‚BLOCKED', dann war das so."

### Falls der Dozent nachfragt (Ehrlichkeits-Hinweis)

Weil die User-Nachricht jeden Schritt neu ist, trifft der Cache nur den System-Teil. Anhängen würde mehr cachen, aber das Fenster wächst mit jedem Screenshot. Wir haben uns für flache Kosten pro Schritt entschieden.

### Mögliche Rückfragen

- „Wie viel bleibt dann pro Schritt?" In V2 etwa 980 Tokens, egal ob Schritt 2 oder Schritt 12. Das ist die Zahl von Folie 10.
- „Was ist ein KV-Cache?" Das Modell rechnet für jedes gelesene Token Zwischenergebnisse aus (Keys und Values). Die werden gespeichert. Kommt dieselbe Textfolge wieder, werden die gespeicherten Werte genommen statt neu gerechnet. Das spart Zeit, funktioniert aber nur für einen unveränderten Anfang.

---

## Folie 13: The action space

**Überschrift:** The action space: ten actions, one schema

**Auf der Folie:** links oben die zehn Aktionen, links unten ein Auszug aus dem Schema (dem Formular für die Antwort). Rechts drei Stichpunkte.

**Um was es geht:** Was der Agent überhaupt tun darf, und wie wir sicherstellen, dass das Modell nichts anderes ausgibt. Das ist Stufe 2 und 3 der Kette: wie das Modell antwortet und wie der Code die Antwort prüft. Ungefähr 60 Sekunden.

**Was man verstehen soll:** Das Modell darf nicht frei formulieren. Es bekommt ein festes Formular (ein JSON-Schema) mit zehn erlaubten Aktionen und erlaubten App-Namen. Dieses Formular geht an den Modellserver, der dann technisch keine andere Antwort erzeugen kann. Was nicht im Formular steht, kann gar nicht erst entstehen. Danach prüft unser Code trotzdem noch einmal und lässt bei Fehlern einen Versuch zu.

### Die zehn Aktionen

click (tippen) · long_press (lange drücken) · input_text (Text eingeben) · scroll (wischen) · open_app (App per Namen öffnen) · navigate_back (zurück) · navigate_home (Startbildschirm) · keyboard_enter (Enter) · wait (warten) · status (melden: fertig oder unmöglich)

### Das Schema (das Formular)

| Feld | Erlaubt |
|---|---|
| action_type | nur eine der zehn Aktionen |
| index | eine ganze Zahl: die Nummer aus der Liste der Bedienelemente |
| app_name | nur Namen aus der Liste: contacts, markor, simple sms messenger, … |
| goal_status | nur „complete" oder „infeasible" |

### Die drei Punkte rechts

**1. Schema handed to Ollama for constrained decoding**
Constrained decoding heißt: Der Modellserver bekommt das Schema und lässt beim Erzeugen der Antwort nur Zeichen zu, die ins Schema passen. Ein Tippfehler im Aktionsnamen oder eine erfundene App sind damit unmöglich. Die Vorlesung gibt die Reihenfolge vor: erst das Erzeugen einschränken, dann prüfen und wiederholen, erst zuletzt am Prompt drehen. Wir machen alle drei.

**2. open_app only by exact name from the allow-list**
Apps werden nur über ihren exakten Namen geöffnet, nie über die Suchleiste des Handys. Die Suche findet gern die falsche App. Das ist der Fix für die Fehlerklasse wrong_app.

**3. Tolerant parsing, strict validation, one retry with the error**
Beim Einlesen sind wir großzügig (Leerzeichen, Zeilenumbrüche egal), beim Prüfen streng (die Nummer muss in der Liste existieren). Scheitert die Prüfung, bekommt das Modell die Fehlermeldung und darf einmal neu antworten. Ergebnis bisher: null ungültige Antworten in 16 Läufen (Mac-Stand, nach den Windows-Läufen aus summary.md aktualisieren).

### Was du sagst, in dieser Reihenfolge

1. „Der Agent kann genau zehn Dinge. Das ist der ganze Aktionsraum."
2. „Diese zehn plus die erlaubten App-Namen stehen in einem Schema, das wir dem Modellserver geben. Der kann dann nichts anderes erzeugen. Eine erfundene App ist technisch unmöglich."
3. „Apps werden nur per exaktem Namen geöffnet, nie über die Suche."
4. „Und trotzdem prüfen wir jede Antwort noch einmal im Code. Scheitert das, ein Versuch mit der Fehlermeldung. In 16 Läufen war keine einzige Antwort ungültig."

### Mögliche Rückfragen

- „Was passiert, wenn das Modell Element 99 will?" Das Schema erlaubt jede ganze Zahl, also kann 99 entstehen. Die Prüfung im Code fängt es: Element 99 gibt es nicht in der Liste, Fehlermeldung ans Modell, ein neuer Versuch. Scheitert auch der, wird der Schritt als Fehler gezählt.
- „Warum zehn Aktionen und nicht mehr?" Weniger Auswahl heißt weniger Fehlermöglichkeiten für ein kleines Modell. Die zehn decken alles ab, was die drei Tasks brauchen.

---

## Folie 14: Guardrails

**Überschrift:** Guardrails: in the code, before the action, no off switch

**Auf der Folie:** links die vier Regeln, rechts eine echte Verlaufszeile aus unserem Windows-Lauf, in der eine Regel gefeuert hat. Schließt das Kapitel „How we built it" ab.

**Um was es geht:** Die Sicherheitsregeln, die der Dozent als Pflicht verlangt hat: Schrittlimit und Zahlungsverbot. Das ist Stufe 5 (check) der Kette. Ungefähr 60 Sekunden.

**Was man verstehen soll:** Diese Regeln stehen im Code, nicht im Prompt. Ein Prompt sagt dem Modell „bitte nicht bezahlen", und das Modell kann das ignorieren. Code prüft jede Aktion, bevor sie ausgeführt wird, und blockiert sie, egal was das Modell will. Es gibt keinen Schalter, um das abzustellen. In allen drei Versionen gleich.

### Die vier Regeln (das sind alle, die es gibt)

| Regel | Was sie tut |
|---|---|
| **Step limit** | Harte Obergrenze von 20 Schritten. Das Aufgaben-Budget (12, 16, 18) darf sie nur senken, nie erhöhen |
| **Payment ban, layer 1: app scope** | Der Agent darf nur innerhalb einer festen Liste von Offline-Apps handeln (Kontakte, Markor, SMS). Landet er woanders, etwa auf dem Startbildschirm oder im Play Store, darf er nur noch zurück, Home, warten oder eine erlaubte App öffnen |
| **Payment ban, layer 2: deny rules** | Zusätzlich: keine Aktion auf Elementen mit „Pay", „Buy", „Subscribe", keine Karten- oder IBAN-Felder, keine gültige Kartennummer tippen. Greift auch, falls Schicht 1 versagt |
| **Loop guard** (V3) | Dieselbe Aktion auf unverändertem Bildschirm: zweimal erlaubt, beim dritten Mal blockiert. Gegen endloses Im-Kreis-Tippen |

Die Liste erlaubter Apps für open_app (Fix für wrong_app) war auf Folie 13.

### Rechts: die Regel in Aktion

```
2. click [6] "Search"
   -> BLOCKED: do not tap or type on the home screen.
      Open the app you need with open_app and its exact name.
3. open_app contacts -> executed
```

Schritt 2 unseres Windows-Laufs: Das Modell wollte auf die Suchleiste des Startbildschirms tippen. Der Code hat das abgelehnt (Schicht 1, App-Scope: Startbildschirm ist keine erlaubte App) und dem Modell in den Verlauf geschrieben, warum. Schritt 3: Das Modell öffnet die App per Namen, richtig. Es ist dieselbe Verlaufszeile, die auf Folie 12 im Prompt steht.

### Was du sagst, in dieser Reihenfolge

1. „Pflicht waren Schrittlimit und Zahlungsverbot. Beides steht im Code, nicht im Prompt. Ein Prompt kann ignoriert werden, Code nicht."
2. Die vier Regeln je ein Satz. Beim Zahlungsverbot betonen: zwei Schichten, falls eine versagt.
3. Rechts: „So sieht das im Lauf aus. Schritt 2 wollte das Modell auf die Suche tippen, der Code hat Nein gesagt und erklärt warum. Schritt 3 war richtig."
4. Überleitung: „So ist der Agent gebaut. Jetzt: Wie haben wir gemessen?"

### Beleg, falls gefragt („Habt ihr das Zahlungsverbot getestet?")

Ja, mit einem automatischen Test: Ein Skript spielt ein Modell, das ein Bezahlformular ausfüllt, Enter drückt und auf „Pay" tippt. Null dieser Aktionen erreichen das Gerät. Der Test liegt in `tests/test_guardrails.py`; insgesamt laufen 209 automatische Tests grün (Zahl nach dem Abgleich mit dem Repo nochmal prüfen).

### Mögliche Rückfragen

- „Warum zwei Schichten beim Zahlungsverbot?" Schicht 1 verhindert, dass der Agent überhaupt in eine Bezahl-App kommt. Schicht 2 fängt den Fall ab, dass innerhalb einer erlaubten App ein Bezahlknopf auftaucht, etwa ein In-App-Kauf.
- „Was passiert bei BLOCKED mit dem Schrittbudget?" Der Schritt zählt. Eine blockierte Aktion kostet also einen Schritt, aber das Modell bekommt die Begründung und kann im nächsten Schritt korrigieren.

---

## Folie 16: When a run stops, and what counts

**Überschrift:** A run ends for one of five reasons. Only one of them can be a PASS.

**Auf der Folie:** links die Tabelle der fünf Stop-Gründe, rechts die PASS-Regel.

**Um was es geht:** Erste Folie im Kapitel „How we measured". Bevor Zahlen kommen, muss klar sein, was ein Lauf ist, wann er endet und was als bestanden gilt. Ohne diese Regeln kann niemand die Ergebnisse ab Folie 19 einordnen. Ungefähr 60 Sekunden.

**Was man verstehen soll:** Ein Lauf endet auf genau eine von fünf Arten. Nur eine davon, dass das Modell selbst „fertig" sagt, kann überhaupt ein PASS werden. Und auch dann nur, wenn der Prüfer von AndroidWorld zustimmt. Das ist das Budget-Thema von Folie 5, jetzt vollständig.

### Die Tabelle

| Stop-Grund | Wer hat entschieden | Kann PASS sein? |
|---|---|---|
| model_done | das Modell meldet „complete" | ja, wenn der Prüfer zustimmt |
| model_infeasible | das Modell gibt auf („unmöglich") | nein |
| step_limit | der Code: Budget aufgebraucht | nein, auch wenn der Bildschirm richtig aussieht |
| loop_abort | der Code: gleiche Aktion, gleicher Bildschirm, dreimal blockiert (nur V3) | nein |
| error | Emulator oder Modellserver abgestürzt | ERROR, zählt nicht in die Quote |

### Rechts: PASS heißt beides

1. Der Agent selbst hat „complete" gemeldet.
2. Der Prüfer von AndroidWorld schaut ins Gerät und gibt 1.0 zurück („Ergebnis vorhanden und richtig").

Schritte aufbrauchen zählt nie als fertig. Ein richtiger Bildschirm ohne Meldung ist trotzdem FAIL: Der Agent muss wissen, dass er fertig ist.

### Was du sagst, in dieser Reihenfolge

1. „Bevor wir Zahlen zeigen: Was ist ein Lauf, und wann ist er bestanden?"
2. Die Tabelle von oben nach unten, je ein Halbsatz. Betonen: „Nur die erste Zeile kann ein PASS werden."
3. Rechts: „PASS braucht zwei Dinge: Der Agent sagt fertig, und der Prüfer bestätigt. Sagt der Agent fertig und der Prüfer sagt nein, ist das FAIL, und zwar die gefährlichste Sorte, weil sie still ist. Dazu gleich mehr."
4. „ERROR heißt: Unsere Infrastruktur ist abgestürzt, nicht der Agent. Diese Läufe zählen nicht in die Quote, werden aber wiederholt."

### Vor dem Vortrag prüfen

- loop_abort gibt es nur in V3. Wenn die V3-Läufe fertig sind, nachsehen, ob es einmal gefeuert hat. Wenn nie: Zeile behalten, im Vortrag sagen „kam in unseren Läufen nicht vor".

### Mögliche Rückfragen

- „Warum zählt ein richtiger Bildschirm ohne Meldung nicht?" Weil ein Agent, der nicht weiß, wann er fertig ist, im echten Einsatz unbrauchbar ist. Er würde weitertippen. Das Wissen „ich bin fertig" ist Teil der Aufgabe.
- „Wer schreibt den Prüfer?" AndroidWorld selbst, pro Aufgabe. Wir haben daran nichts geändert. Der Prüfer liest den Gerätezustand (z. B. die Kontaktdatenbank), nicht den Bildschirm.

---

## Folie 17: One row per run

**Überschrift:** Written while the run happens, in the lecture's format

**Auf der Folie:** oben die echte Log-Zeile aus unserem Windows-Lauf (08.10.), darunter links „wie sie entsteht", rechts die fünf Fehlerklassen.

**Um was es geht:** Letzte Folie im Kapitel „How we measured". Was wir pro Lauf aufschreiben. Der Dozent hat dieses Format vorgegeben und gesagt: „Die Präsentation am Freitag ist diese Tabelle, sortiert." Hier eine echte Zeile, auf Folie 19 die ganze Tabelle. Ungefähr 60 Sekunden.

**Was man verstehen soll:** Jeder Lauf hinterlässt genau eine Zeile mit zehn Feldern. Sie wird automatisch in dem Moment geschrieben, in dem der Lauf endet, nicht hinterher aus dem Gedächtnis. Jeder gescheiterte Lauf bekommt eine Fehlerklasse aus einer festen Liste von fünf Wörtern, damit man Fehler zählen und vergleichen kann.

### Die Zeile, Feld für Feld

| Feld | Wert | Bedeutung |
|---|---|---|
| task | ContactsAddContact | welche Aufgabe |
| run | 1 of 3 | der wievielte von drei Läufen |
| model | qwen3-vl:4b-instruct (Q4_K_M, local, Ollama) | Modellname, Pflichtangabe |
| observation | accessibility tree | was das Modell sah (Folie 10) |
| grounding | by index | wie es gezeigt hat (Folie 11) |
| steps | 11 (budget 12) | gebraucht von erlaubt |
| verifier | FAIL | Urteil des Prüfers |
| failure_class | lost_value | warum, in einem Wort (Wurzel: der Nachname kam nie an; das stille „fertig" ist das Symptom) |
| recording | runs/…/recording.mp4 | das Bildschirmvideo |
| note | typed „Hugo", never „Pereira"; reported complete | ein Satz, was passiert ist |

### Die fünf Fehlerklassen

| Klasse | Bedeutung |
|---|---|
| grounding | richtige Absicht, falsche Stelle getippt |
| too_early | „fertig" gesagt, bevor die letzte Aktion (z. B. Speichern) gemacht war |
| lost_value | ein Wert (Name, Nummer, Text) ging zwischen Schritten oder Apps verloren |
| wrong_app | in der falschen App gelandet |
| false_done | „fertig" gesagt, aber das Ergebnis stimmt nicht |

### Was du sagst, in dieser Reihenfolge

1. „Der Dozent hat das Format vorgegeben. Das ist eine echte Zeile aus unserem Lauf."
2. Nicht alle Felder vorlesen. Drei herausgreifen: steps 11 von 12, verifier FAIL, failure_class lost_value. „Das Modell hat ‚Hugo' getippt, nie ‚Pereira', und trotzdem fertig gemeldet."
3. „Die Zeile wird automatisch geschrieben, wenn der Lauf endet. Der Code schlägt die Fehlerklasse vor, ein Mensch prüft sie am Video."
4. „Fünf Fehlerklassen, feste Liste, eine pro Lauf. Damit kann man Fehler zählen statt nur erzählen."
5. Überleitung: „Und jetzt die ganze Tabelle."

### Hinweis

Dieselbe Zeile taucht auf Folie 20 als „ein Fehler Schritt für Schritt" wieder auf. Absicht: hier die Zeile, dort das Video dazu.

### Mögliche Rückfragen

- „Wer entscheidet die Fehlerklasse?" Der Code schlägt vor, anhand von Stop-Grund und Prüfer. Der Mensch schaut das Video und bestätigt oder korrigiert. Bei unserem Lauf hatte der Code wrong_app geraten, der Verlauf zeigte lost_value (Nachname nie getippt).
- „Warum genau diese fünf Klassen?" Vorgabe des Dozenten. Sie decken die typischen Arten ab, wie ein GUI-Agent scheitert, und sind grob genug, dass man sie am Video eindeutig zuordnen kann.

---

## Folie 19: V1 results

**Überschrift:** V1 results: 5 of 9 pass, every failure is in the two harder tasks

**Auf der Folie:** die Log-Tabelle der neun V1-Läufe vom Windows-Laptop (08.10.2026), eine Zeile pro Lauf. Darunter: 0 ERROR-Läufe, (?) = vom Code vorgeschlagen.

**Um was es geht:** Erste Folie im Kapitel „What happened". Die Tabelle, die der Dozent sehen will. Ungefähr 60 Sekunden.

**Was man verstehen soll:** V1 ist der Maßstab. Nicht die Quote allein zählt, sondern welche Aufgaben scheitern und woran. Muster: Je mehr Apps und Schritte, desto schlechter. Alle drei SMS-Läufe scheitern an derselben Stelle.

### Die Tabelle

| Task | Run | Steps (Budget) | Verifier | Fehlerklasse | Note |
|---|---|---|---|---|---|
| Contacts | 1, 2, 3 | 9, 8, 9 (12) | PASS ×3 | | |
| Markor-Notiz | 1, 2 | 10, 11 (16) | PASS ×2 | | |
| Markor-Notiz | 3 | 9 (16) | FAIL | false_done (?) | „fertig" gemeldet, ohne je Save zu tippen |
| Notiz + SMS | 1 | 17 (18) | FAIL | grounding (?) | Notiz gespeichert (Teilpunkte 0,5), ein Tipp ins Leere in der SMS-App |
| Notiz + SMS | 2 | 18 (18) | FAIL | grounding (?) | Notiz gespeichert (0,5), fünfmal dieselbe Stelle getippt, nichts passiert |
| Notiz + SMS | 3 | 18 (18) | FAIL | grounding (?) | Nummer nie eingetippt, viermal dieselbe Stelle, Budget aus |

### Was du sagst, in dieser Reihenfolge

1. „Das ist die Log-Tabelle für V1, neun Läufe, fünf bestanden, kein einziger Absturz."
2. „Kontakt anlegen: drei von drei. Die Notiz: zwei von drei. Beim dritten hat das Modell ‚fertig' gesagt, ohne auf Speichern zu tippen. Das ist false_done, die stille Sorte."
3. „Notiz plus SMS: null von drei. Alle drei scheitern am gleichen Ort, in der SMS-App. Das Modell tippt vier-, fünfmal auf dieselbe Koordinate, und nichts passiert. Richtige Absicht, falsche Stelle: grounding. Genau das Problem, das der Dozent als häufigstes genannt hat."
4. „Teilpunkte 0,5 heißt: Die Notiz war richtig, nur die SMS fehlte."
5. Überleitung: „Einen Fehler schauen wir uns jetzt Schritt für Schritt an."

### Vor dem Vortrag prüfen

- Die drei (?) an den Videos bzw. am Trajectory-HTML bestätigen (Mehrfachklicks auf dieselbe Koordinate sind dort sichtbar). Dann die Fragezeichen von der Folie nehmen.
- Kosten V1 auf diesem Laptop: 90 s Modellzeit pro Schritt, ca. 19 min pro Lauf (Screenshot auf CPU). Kommt auf Folie 24.

### Mögliche Rückfragen

- „Warum ist Contacts 3/3, wenn V1 doch schlecht zeigt?" Bei einem Formular mit drei Feldern sieht das Modell im Screenshot das leere Nachnamensfeld direkt unter dem Vornamen. In der Textliste von V2 fehlt dieser visuelle Hinweis. Das wird auf Folie 23 der Kern der Geschichte.
- „Was heißt Teilpunkte 0,5?" AndroidWorlds Prüfer gibt bei der SMS-Aufgabe je einen halben Punkt für Notiz und SMS. PASS braucht 1,0.
- „Warum nur Windows-Zahlen?" Die Mac-Läufe des Kollegen hatten 11 Abstürze und einen RAM-Wechsel mitten in der Messung. Die Windows-Messung lief ohne Störung durch. Die Mac-Zahlen kommen als Reproduzierbarkeits-Folie.

---

## Folie 20: One failure, step by step

**Überschrift:** It typed "Hugo", never "Pereira", and said it was done (V2)

**Auf der Folie:** links ein Zeitraffer aus den elf Schritt-Screenshots des Laufs (ein Bild pro Schritt, 1,4 s je Bild, Endschirm 3 s), startet automatisch, Endlosschleife, ohne Ton. Rechts die entscheidenden Schritte, der wörtliche Gedanke des Modells bei Schritt 11 und die Einordnung.

**Um was es geht:** Pflichtinhalt „mindestens ein gescheiterter Versuch analysiert". Derselbe Lauf wie die Log-Zeile auf Folie 17, jetzt mit Bild. Ungefähr 75 Sekunden.

**Was man verstehen soll:** Das Modell hat den Nachnamen weggelassen und trotzdem „fertig" gesagt. Das Gefährliche: Nichts hat gewarnt. Der Agent war überzeugt, alles sei erledigt. Und es ist kein Einzelfall, sondern das Hauptmuster der Tree-Versionen.

### Die Schritte rechts

| Schritt | Was passierte |
|---|---|
| 2 | Tipp auf die Suche des Startbildschirms, vom Harness blockiert (die Guardrail von Folie 14) |
| 3 | App Kontakte per Namen geöffnet, richtig |
| 7 | „Hugo" ins Feld Vorname |
| 9 | Nummer ins Feld Telefon. Das Feld Nachname wurde nie angefasst |
| 10 | Save |
| 11 | „fertig" gemeldet. Prüfer: FAIL |

Gedanke des Modells bei Schritt 11, wörtlich: „The contact has been successfully created."

**Einordnung:** Klasse **lost_value**. Ein Wert aus der Aufgabe (der Nachname) kam nie auf dem Gerät an. Das stille „fertig" ist nur das Symptom. Unser automatischer Klassifizierer hatte wrong_app vorgeschlagen (wegen des blockierten Tipps); der Verlauf entscheidet. Kein Einzelfall: In 5 von 6 Kontakt-Läufen mit Tree (V2, V3) fehlt der Nachname. V1 hat in allen drei Läufen beide Namen getippt.

### Was du sagst, in dieser Reihenfolge

1. „Das ist der Lauf von der Log-Zeile vorhin. Links läuft die Aufnahme in Zeitraffer, rechts die Schritte."
2. Die Schritte durchgehen. Bei Schritt 2 kurz: „Da greift die Guardrail." Bei Schritt 9 betonen: „Vom Vornamen direkt zur Nummer. Das Feld Nachname wird übersprungen."
3. „Schritt 11, das Modell sagt fertig, und denkt wörtlich: Der Kontakt wurde erfolgreich erstellt. Der Prüfer sagt nein."
4. „Fehlerklasse lost_value: Der Nachname kam nie an. Dass das Modell trotzdem fertig sagt, ist nur die Folge."
5. „Und das ist kein Ausreißer. Mit der Textliste fehlt der Nachname in fünf von sechs Läufen. Mit Screenshot nie. Warum, das kommt in Kapitel 5."

### Technik

- Das Video startet automatisch (reveal.js `data-autoplay`), läuft in Schleife, ohne Ton. Datei: `deck/assets/failure-contacts-steps.mp4`, gebaut aus `screens/step_01.jpg` bis `step_11.jpg` des Laufs (die echte Aufnahme hat 4 min mit langen Wartezeiten auf das Modell, deshalb die Schritt-Bilder). Original: `runs_setup/v2_index/ContactsAddContact/run1_20261008-103339/recording.mp4`.
- Vor dem Vortrag im Präsentationsbrowser prüfen, dass das Video abspielt. Es ist stumm gesetzt, damit Autoplay erlaubt ist.

### Hinweis

Dieser Lauf ist der Setup-Lauf von heute Morgen (vor der gewerteten Evaluation). Die drei gewerteten V2-Läufe zeigen dasselbe Muster. Falls gefragt: „Wir zeigen den ersten Lauf, bei dem wir das Muster gesehen haben; es wiederholt sich in den gewerteten Läufen."

### Mögliche Rückfragen

- „Warum lässt das Modell den Nachnamen weg?" Hypothese: In der Textliste stehen „[7] EditText First name" und „[8] EditText Last name" als zwei Zeilen. Das kleine Modell hält „den Namen" nach dem ersten Feld für erledigt, und nichts in der Liste widerspricht. Im Screenshot ist das leere Feld direkt unter dem Vornamen sichtbar.
- „Hat V3 das nicht abgefangen? Da gibt es doch einen Prüfschritt vor done." Nein. Der Prüfschritt nutzt dasselbe kleine Modell, und das hat den fehlenden Nachnamen in allen drei V3-Läufen durchgewinkt. Ein Prüfer, der so schwach ist wie der Handelnde, bringt Kosten, keine Sicherheit. Kommt auf Folie 21 und 28.

---

## Folie 21: Was it reliable?

**Überschrift:** Reliability check: strong on constraints, weak on verification. V3 added it, and it misfired.

**Auf der Folie:** Tabelle mit den sechs Zuverlässigkeits-Hebeln aus der Vorlesung, je eine Spalte für V1/V2 und für V3. Darunter ein Satz zur gemeinsamen Ursache.

**Um was es geht:** Letzte Folie im Kapitel „What happened", die Diagnose. Ungefähr 90 Sekunden, die wichtigste Analysefolie.

**Was man verstehen soll:** V1 und V2 sind stark bei den Regeln und bei dem, was der Agent sieht. Schwach sind sie bei der Prüfung vor „fertig". Genau da kommt lost_value durch. V3 hat diese Prüfung eingebaut, dazu Rückmeldung und Schleifenwächter. Alle drei haben geschadet, aus einem Grund: Sie nehmen an, dass eine erfolgreiche Aktion den Bildschirm sichtbar ändert. In Markor stimmt das nicht, Save speichert automatisch ohne sichtbare Änderung.

### Die Tabelle

| Hebel | Frage | V1 / V2 | V3 |
|---|---|---|---|
| Goal clarity | Was zählt als Erfolg? | ✓ Aufgabentext plus Prüfer von AndroidWorld | ✓ gleich |
| Observable state | Was sieht der Agent? | ✓ aktueller Bildschirm jeden Schritt, Verlaufszeilen | ✓ gleich |
| Feedback | Weiß er, was passiert ist? | schwach: nur „executed" | „deine Aktion hat nichts geändert": falsch bei Save, Markor speichert ohne sichtbare Änderung |
| Verification | Hat das Ergebnis funktioniert? | keine Prüfung vor „fertig": der fehlende Nachname geht durch | Prüfschritt mit demselben 4B-Modell: hat den fehlenden Nachnamen 3 von 3 Mal durchgewinkt |
| Recovery | Nochmal, anders, zurück oder Stopp? | ungültiges JSON: Retry mit Fehlermeldung (2×). Timeout 300 s: ERROR | plus Loop-Guard (gleiche Aktion dreimal blockiert): hat bei Save gefeuert, 3 Läufe beendet |
| Constraints | Welche Regeln erzwingt das System? | ✓ im Code: Schrittlimit, Zahlungsverbot, App-Scope | ✓ gleich, hielt in allen 27 Läufen |

Satz unten: Jeder V3-Mechanismus nimmt an, dass eine erfolgreiche Aktion den Bildschirm ändert. Wo das nicht gilt, macht das Sicherheitsnetz aus einem PASS ein FAIL.

### Was du sagst, in dieser Reihenfolge

1. „Die Vorlesung gibt sechs Hebel vor, um Zuverlässigkeit zu prüfen. Wir haben unsere Versionen daran gemessen."
2. „Grün ist, was bei allen Versionen hält: klares Ziel, sichtbarer Zustand, Regeln im Code. In 27 Läufen hat keine Guardrail versagt."
3. „Orange ist die Schwachstelle von V1 und V2: keine Prüfung, bevor der Agent fertig sagt. So kam der fehlende Nachname durch."
4. „V3 sollte genau das lösen: Prüfschritt vor fertig, Rückmeldung bei wirkungslosen Aktionen, Schleifenwächter. Ergebnis: null von neun."
5. „Der Grund steht unten: Alle drei Mechanismen nehmen an, dass eine erfolgreiche Aktion etwas Sichtbares ändert. Markor speichert automatisch, der Bildschirm bleibt gleich. Also meldet V3 ‚nichts passiert', das Modell tippt nochmal Save, der Wächter bricht ab. Und der Prüfschritt nutzt dasselbe schwache Modell, das den Fehler gemacht hat. Ein Prüfer, der so schwach ist wie der Handelnde, kostet Zeit und bringt keine Sicherheit."
6. Überleitung: „Was wir daraus gelernt haben, und wo ein Fix wirklich hingehört: letztes Kapitel."

### Mögliche Rückfragen

- „Wie hätte man den Prüfschritt richtig gebaut?" Nicht den Bildschirm prüfen, sondern den Zustand, den die Oberfläche nicht zeigt: die Kontaktdatenbank, die Dateiliste. Oder ein stärkeres Modell nur für die Prüfung. Kommt auf Folie 25.
- „Warum hat V2 Markor bestanden, V3 nicht, bei gleichen Aufgaben?" V2 hatte keinen Hinweis und keinen Wächter. Es tippte zwei-, dreimal Save, sagte fertig, und der Prüfer fand die Datei. V3 hat sich an genau dieser Stelle festgebissen.

---

## Folie 23: Was sich zwischen den Versionen geändert hat

**Überschrift:** What changed between the versions: one change for V2, five more for V3

**Auf der Folie:** eine Tabelle mit drei Spalten V1, V2, V3. Oben die zwei Zeilen, die sich ändern (Observation, Grounding), dann die Zeile „Harness additions" (nur V3 hat etwas), darunter drei Zeilen, die in allen Versionen gleich sind. Unten ein Satz: V1 → V2 ist eine Änderung, V2 → V3 sind fünf.

**Um was es geht:** Erste Folie im Kapitel „What we changed and learned". Pflichtinhalt „eine dokumentierte Verbesserung". Bevor man Ergebnisse vergleicht, muss klar sein, was sich überhaupt unterscheidet. Ungefähr 60 Sekunden.

### Das Grundprinzip, in einfachen Worten

Stell dir vor, du änderst an einem Rezept gleichzeitig die Backzeit und die Mehlsorte, und der Kuchen wird schlechter. Du weißt dann nicht, woran es lag. Änderst du nur die Backzeit, weißt du es. Genau so haben wir V2 gebaut: nur eine Sache anders als V1. Wenn V2 anders abschneidet, liegt es an dieser einen Sache.

Bei V3 haben wir fünf Dinge auf einmal dazugebaut. Das war Absicht, aus Zeitgründen (fünf Einzelversionen mal neun Läufe wären 45 weitere Läufe, über fünf Stunden). Der Preis: Wenn V3 anders abschneidet, wissen wir nicht, welcher der fünf Teile es war. V3 beantwortet nur: Hilft das ganze Paket, ja oder nein? Das sagen wir offen. Das nennt die Folie „Pakettest".

### Die Tabelle, Zeile für Zeile

| Zeile | V1 | V2 | V3 | Was es heißt |
|---|---|---|---|---|
| Observation | Screenshot | Accessibility Tree | Tree | Was das Modell vom Bildschirm bekommt: Bild (V1) oder Textliste der Bedienelemente (V2, V3). Folie 10 |
| Grounding | Koordinaten vom Modell | Index, im Code aufgelöst | Index | Wer bestimmt, wo getippt wird: das Modell rät Pixel (V1), oder es nennt eine Nummer und der Code schlägt die Position nach (V2, V3). Folie 11 |
| Harness additions | keine | keine | fünf Mechanismen | Nur V3 hat zusätzliche Code-Bausteine um das Modell herum, siehe unten |
| Modell, Temperatur, Seed | qwen3-vl:4b-instruct, Q4_K_M, lokal, T = 0, fester Seed | identisch | identisch | Dasselbe Modell, dieselben Einstellungen. Hier wird der Modellname genannt (Pflicht) |
| Tasks, Seeds, Prompt-Aufbau | 3 Tasks, dieselben 9 Aufgaben-Instanzen | identisch | identisch | Jede Version bekommt exakt dieselben neun Aufgaben mit denselben Namen, Nummern, Texten |
| Guardrails | Schrittlimit, Zahlungsverbot, App-Scope | identisch | identisch | Die Sicherheitsregeln von Folie 14 sind in allen Versionen gleich und immer an |

**„Identisch" heißt:** Diese Zeile ist in allen drei Versionen wörtlich gleich. Beide Versionen sind derselbe Programmcode; der Unterschied ist eine Konfigurationsdatei (`configs/v1_baseline.json`, `v2_index.json`, `v3_full.json`), die in jeden Lauf kopiert wird. Deshalb kann man hinterher für jeden Lauf nachlesen, welche Version lief.

### Die fünf V3-Mechanismen, einzeln erklärt

1. **Stabilen Bildschirm abwarten (stable-screen wait):** Nach jeder Aktion wartet der Code, bis sich der Bildschirm nicht mehr verändert, bevor er ihn liest. Sonst sieht das Modell einen halb aufgebauten Bildschirm. Gegen Fehlerklasse too_early.
2. **Hinweis „keine Wirkung" (no-effect hint):** Wenn eine Aktion den Bildschirm nicht verändert hat, schreibt der Code das in den Verlauf: „your action changed nothing". Das Modell soll dann etwas anderes probieren.
3. **Loop-Guard:** Dieselbe Aktion auf unverändertem Bildschirm wird beim dritten Mal blockiert. Gegen endloses Im-Kreis-Tippen (das Muster der V1-SMS-Läufe).
4. **Statuszeile mit Notizen (status bar):** Der Code hält am Ende des Prompts fest: Schritt X von Y, aktuelle App, gemerkte Werte wie die Telefonnummer. Gegen verlorene Werte beim App-Wechsel (lost_value).
5. **Prüfung vor fertig (check step):** Bevor „fertig" gilt, bekommt das Modell den Bildschirm noch einmal und muss bestätigen, dass die Aufgabe wirklich erledigt ist. Gegen falsches „fertig" (false_done).

Alle fünf stammen aus den Empfehlungen der Vorlesung für einen robusten Harness. Warum sie trotzdem nicht geholfen haben, steht auf Folie 21 und 28.

### Warum die V2-Änderung (falls gefragt)

V1 scheiterte an Tipps ins Leere: In den SMS-Läufen tippte es vier- bis sechsmal auf dieselbe Koordinate, ohne dass etwas passierte. Mit dem Index kann das Modell nur Elemente benennen, die es in der Liste gibt. Einen Tipp ins Leere gibt es damit nicht mehr.

### Was du sagst, in dieser Reihenfolge

1. „Drei Versionen, derselbe Code, nur die Konfiguration ist anders. Dasselbe Modell, qwen3-vl 4B, dieselben Seeds, dieselben neun Aufgaben."
2. „V1 zu V2: genau eine Änderung. Was das Modell sieht, und wie es zeigt. Warum: V1 scheiterte an Tipps ins Leere. Mit dem Index kann das Modell nur auf Elemente zeigen, die existieren."
3. „V2 zu V3: fünf Mechanismen auf einmal, alles, was die Vorlesung für einen robusten Harness empfiehlt. Das ist bewusst ein Paket. Wenn es hilft, wissen wir nicht genau, welcher Teil. Wenn es schadet, auch nicht. Die Zahlen gleich."

### Mögliche Rückfragen

- „Warum habt ihr V3 nicht auch als Einzeländerungen gemacht?" Fünf Einzelversionen mal neun Läufe wären 45 weitere Läufe, bei 7 Minuten pro Lauf über fünf Stunden. Das Paket war die ehrliche Abkürzung, und wir sagen offen, dass es nicht zuordenbar ist.
- „Was heißt Aufgaben-Instanz?" Die Aufgabe „Kontakt anlegen" mit konkreten Werten, z. B. Hugo Pereira mit einer bestimmten Nummer. AndroidWorld erzeugt die Werte aus einem Seed (Startwert). Gleicher Seed, gleiche Werte. So bekommt Lauf 1 in V1, V2 und V3 exakt denselben Kontakt.

---

## Folie 24: Before / after

**Überschrift:** V2 is 3× faster and cheaper, and less successful. V3 is worse again.

**Auf der Folie:** links Balken in den Versionsfarben (V1 56 %, V2 33 %, V3 0 %), rechts die Kostentabelle.

**Um was es geht:** Die Vorher-Nachher-Zahlen, Pflichtinhalt. Ungefähr 75 Sekunden.

**Was man verstehen soll:** Die Änderung hat getroffen, was sie treffen sollte: keine Tipps ins Leere mehr, dreimal schneller, 44 Prozent weniger Tokens. Aber die Erfolgsquote ist gesunken, weil eine andere Schwäche sichtbar wurde (der verlorene Nachname). V3 hat es noch schlechter gemacht. Das ist ehrlich, und genau die Art Ergebnis, die der Dozent verlangt: gemessen, nicht gehofft.

| | V1 | V2 | V3 |
|---|---|---|---|
| Erfolgsquote | 5/9 (56 %) | 3/9 (33 %) | 0/9 |
| Modellzeit pro Schritt | 90 s | 28 s | 27 s |
| Prompt-Tokens pro Aufruf | 1.905 | 1.069 | 1.120 |
| Zeit pro Lauf | 19 min | 7 min | 8 min |
| ungültige Antworten | 0 | 0 | 0 |

### Was du sagst

1. „Vorher 5 von 9, nachher 3 von 9. Die Änderung hat die Erfolgsquote nicht verbessert."
2. „Aber sie hat getroffen, was sie sollte: Tipps ins Leere gibt es in V2 nicht mehr, jeder Schritt ist dreimal schneller, ein Lauf dauert 7 statt 19 Minuten."
3. „Was dafür sichtbar wurde: der verlorene Nachname. Die Textliste hat das Zeigeproblem gelöst und ein Wahrnehmungsproblem aufgedeckt."
4. „V3 mit allen Fixes: null von neun, aus den Gründen von vorhin."
5. „Einschränkung: Mit drei Läufen pro Aufgabe verschiebt ein einziger Lauf eine Aufgabe um 33 Punkte. Diese Zahlen reichen, um Muster zu finden, nicht, um Versionen zu ranken."

### Mögliche Rückfragen

- „Warum ist V1 so langsam, 90 Sekunden pro Schritt?" Der Screenshot wird auf der CPU des Laptops verarbeitet, keine Grafikkarte. Auf dem Mac des Kollegen mit M4-Chip waren es 23 Sekunden. Kommt auf die Reproduzierbarkeits-Folie.
- „Ist V2 dann überhaupt eine Verbesserung?" Für Kosten und für die Fehlerklasse, die sie treffen sollte (grounding): ja. Für die Erfolgsquote mit diesem Modell: nein. Beides sagen.

### Begriffe auf der Folie

- **Modellzeit pro Schritt:** wie lange das Modell pro Anfrage rechnet. V1 ist langsam, weil der Screenshot auf der CPU verarbeitet wird.
- **Prompt-Tokens pro Aufruf:** wie viel Text das Modell pro Anfrage lesen muss (Folie 10: Screenshot ist teurer als Liste).
- **Zeit pro Lauf:** Modellzeit plus Warten auf den Emulator, über alle Schritte eines Laufs.
- **Ungültige Antworten:** wie oft das Modell etwas ausgab, das nicht ins Schema passte (Folie 13): nie, in 27 Läufen.

---

## Folie 25: Where the fix belongs

**Überschrift:** Where the fix belongs: code fixed pointing and app choice, not judgement

**Auf der Folie:** Tabelle mit fünf Fehlern: was wir versucht haben, wo wir den Fix abgelegt haben (immer Programs), ob es funktioniert hat, und wo er wirklich hingehört. Unten die vier Orte aus der Vorlesung mit zwei Regeln.

**Um was es geht:** Die Vorlesung sagt, ein Fix hat vier mögliche Orte: **Knowledge** (Wissen, das man dem Modell gibt, z. B. Dokumente), **Instructions** (Anweisungen im Prompt), **Programs** (Code um das Modell herum), **Parameters** (ein anderes oder größeres Modell). Die Folie geht jeden Fehler durch und fragt: Wo haben wir den Fix hingelegt, hat es funktioniert, wo gehört er wirklich hin? Ungefähr 75 Sekunden.

**Was man verstehen soll:** Wir haben alle Fixes in Code gelegt. Das hat funktioniert, wo es um Mechanik ging (Zeigen, App-Wahl). Es hat nicht funktioniert, wo es um Urteil ging (Ist der Kontakt vollständig? Ist gespeichert?). Für Urteil braucht es ein stärkeres Modell oder Code, der den echten Zustand liest statt den Bildschirm. App-Eigenheiten wie Markors Autosave gehören in einen Satz Anweisung, nicht in einen generischen Mechanismus.

### Die Tabelle

| Fehler | Was wir versucht haben | Ort | Hat es funktioniert? | Wo es wirklich hingehört |
|---|---|---|---|---|
| grounding | Index statt Koordinaten (V2) | Programs | ja: keine Tipps ins Leere mehr | Programs, so wie gemacht |
| wrong_app | open_app nur per exaktem Namen | Programs | ja: hielt in allen 27 Läufen | Programs, so wie gemacht |
| lost_value | Statuszeile mit Notizen (V3) | Programs | nein: der Nachname wurde nie gelesen, nicht vergessen | Programs, aber früher: dem Modell Tree plus Screenshot geben, oder vor „fertig" den Gerätezustand prüfen |
| false_done | Prüfschritt vor fertig (V3) | Programs | nein: der Prüfer war dasselbe 4B-Modell | Parameters: stärkeres Modell nur für die Prüfung. Oder Programs, die Zustand lesen, den die Oberfläche nicht zeigt |
| Save-Schleife | Hinweis „keine Wirkung" plus Loop-Guard (V3) | Programs | nach hinten losgegangen: Markor speichert automatisch, keine sichtbare Änderung | Instructions: ein Satz in einer Markor-Skill-Datei, „Save zeigt keine Bestätigung" |

Unten: die vier Orte aus der Vorlesung, dazu zwei Regeln: Eine Regel, die nie umgangen werden darf → Programs. Ein Urteil, das man in einem Satz sagen kann → Instructions.

### Die Zeile lost_value, weil sie die schwierigste ist

Die Notizzeile in V3 sollte Werte festhalten, damit sie beim App-Wechsel nicht verloren gehen. Aber der Nachname ging nicht beim Wechsel verloren, er wurde nie ins Formular getippt. Das Modell hat ihn in der Textliste schlicht übersehen. Ein Fix muss also früher ansetzen: Entweder das Modell sieht Liste und Bild zusammen (dann sieht es das leere Feld), oder der Code prüft vor „fertig" die Kontaktdatenbank statt den Bildschirm.

### Was du sagst, in dieser Reihenfolge

1. „Die Vorlesung nennt vier Orte für einen Fix: Wissen, Anweisungen, Code, Modell. Wir haben alles in Code gelegt. Hier das Ergebnis pro Fehler."
2. „Die zwei grünen Zeilen: Zeigen und App-Wahl. Mechanik. Code hat das gelöst."
3. „Die drei orangen: Da ging es um Urteil. Ist der Name vollständig, ist gespeichert. Code mit demselben schwachen Modell als Prüfer kann das nicht. Dafür braucht es ein stärkeres Modell oder Code, der den echten Zustand liest."
4. „Und die letzte Zeile: Markor speichert automatisch. Das ist Wissen über eine App in einem Satz. Das gehört in eine Anweisung, nicht in einen generischen Schleifenwächter, der dann überall feuert."
5. Überleitung: „Kann man diesen Zahlen trauen? Zwei Folien dazu."

### Mögliche Rückfragen

- „Warum nicht einfach den Prompt ändern?" Anweisungen sind billig, werden aber vom Modell still ignoriert. Eine Regel, die nie umgangen werden darf, gehört in Code. Eine App-Eigenheit, die das Modell nur wissen muss, gehört in eine Anweisung.
- „Was heißt ‚Gerätezustand prüfen'?" Statt auf den Bildschirm zu schauen, liest der Code direkt die Daten: die Kontaktdatenbank, die Dateiliste von Markor. Das macht AndroidWorlds Prüfer auch so. Unser V3-Prüfschritt hat nur den Bildschirm angeschaut, mit demselben Modell.

---

## Folie 26: Same code, second machine

**Überschrift:** Run again on a MacBook: same ranking, same failure patterns, different single runs

**Auf der Folie:** links eine Tabelle Windows gegen Mac (Erfolgsquoten V1 bis V3, ERROR-Läufe, V1-Modellzeit, Ollama-Version und Modell-Digest), rechts drei Punkte, unten das Dozentenzitat.

**Um was es geht:** Reproduzierbarkeit, live gezeigt. Der Dozent hat am ersten Tag gefragt: „Wie oft habt ihr es laufen lassen?" Antwort: 54 Läufe auf zwei Rechnern. Hier ist der Kollege mit seinen Mac-Läufen sichtbar. Ungefähr 60 Sekunden.

**Was man verstehen soll:** Dasselbe Skript auf einem zweiten Rechner liefert dieselbe Rangfolge und dieselben Fehlermuster. Einzelne Läufe gehen anders aus, und der Grund ist bekannt: Die Modelldatei ist nicht derselbe Build. Das bestätigt eine Regel aus der Vorlesung, die man leicht für Pedanterie hält: Ein anderer Digest ist ein anderes Modell. Wir haben es gemessen.

### Die Tabelle

| | Windows-Laptop (Bela) | MacBook Air M4 (Kollege) |
|---|---|---|
| V1 | 5 / 9 | 5 / 9 |
| V2 | 3 / 9 | 2 / 9 |
| V3 | 0 / 9 | 0 / 9 |
| ERROR-Läufe | 0 | 11, wiederholt |
| V1 Modellzeit pro Schritt | 90 s | 23 s |
| Ollama / Modell-Digest | 0.40.0 / ef33995b | 0.35.1 / ee4b975b |

Rechts: gleiches Skript, gleiche Seeds, Temperatur 0. Gleiche Muster: Nachname fehlt mit Tree, V3 hängt bei Save. Einzelläufe anders: Modelldatei nicht derselbe Build.

### Begriffe

- **Digest:** eine Prüfsumme der Modelldatei, wie ein Fingerabdruck. Gleicher Name, anderer Digest heißt: Die Datei ist nicht identisch, z. B. weil Ollama das Modell zwischen Version 0.35 und 0.40 neu gebaut hat.
- **ERROR-Läufe:** Läufe, bei denen Emulator oder Modellserver abgestürzt sind. Zählen nicht in die Quote, wurden auf dem Mac wiederholt.
- **Seed:** Startwert, aus dem AndroidWorld die Aufgabenwerte (Namen, Nummern) erzeugt. Gleicher Seed, gleiche Aufgabe, auf beiden Rechnern.

### Was du sagst, in dieser Reihenfolge

1. „Unser Kollege hat dieselben 27 Läufe auf seinem MacBook gemacht. Gleiche Rangfolge: V1 vorn, V3 bei null."
2. „Gleiche Fehlermuster: Der Nachname fehlt mit der Textliste, V3 bleibt bei Save hängen."
3. „Einzelne Läufe gehen anders aus. Der Grund steht unten: andere Ollama-Version, anderer Modell-Digest. Gleicher Name, andere Datei. Der Dozent hat uns gewarnt, dass das ein anderes Modell ist. Wir sehen es in den Zahlen."
4. „Deshalb zeigen wir die Windows-Läufe als Haupttabelle: null Abstürze, gleiche Einstellung durchgehend. Die Mac-Läufe hatten elf Abstürze und einen RAM-Wechsel mitten in der Messung."

### Vor dem Vortrag prüfen

- Die Mac-Zahlen stammen aus dem Berichtsentwurf des Kollegen. Wenn er `summary.md` schickt, Ollama-Version und Digest gegenprüfen. Rechnername „MacBook Air M4" von ihm bestätigen lassen.

### Mögliche Rückfragen

- „Wenn es ein anderes Modell ist, darf man die beiden überhaupt nebeneinander zeigen?" Ja, genau deshalb stehen sie nebeneinander und nicht in einer gemeinsamen Tabelle. Wir mischen die Zahlen nicht. Wir zeigen, dass die Erkenntnis auf beiden Rechnern gilt, die Einzelwerte aber nicht übertragbar sind.
- „Warum ist V1 auf dem Mac viermal schneller?" Apple-Chip mit Grafikbeschleunigung für das Modell; auf dem Windows-Laptop rechnet die CPU. Für die Erfolgsquote spielt das keine Rolle, für die Laufzeit schon.

---

## Folie 27: Reproduce it (Run it yourself)

**Überschrift:** One command per version. The config is the whole agent.

**Auf der Folie:** oben der eine Befehl, mit dem man eine Version komplett laufen lässt, darunter vier Punkte, die sagen, warum jemand anderes dieselbe Tabelle nachbauen kann.

**Um was es geht:** Reproduzierbarkeit ist ein Bewertungskriterium des Projekts. Die Folie beantwortet die Frage: Könnte jemand, der unser Repository herunterlädt, genau unsere Zahlen nachstellen? Ungefähr 45 Sekunden.

**Was man verstehen soll:** Alles, was ein Ergebnis beeinflusst, ist festgeschrieben und wird pro Lauf gespeichert. Es gibt nichts, was nur in unseren Köpfen oder auf einem bestimmten Laptop existiert.

### Der Befehl

```
python run_eval.py --config configs/v2_index.json
```

Ein Befehl startet alle neun Läufe einer Version (drei Tasks mal drei Läufe). Die Datei hinter `--config` ist die Version: `v1_baseline.json`, `v2_index.json` oder `v3_full.json`. Deshalb der Satz in der Überschrift: Die Konfiguration ist der ganze Agent. Der Programmcode ist für alle drei Versionen derselbe.

### Die vier Punkte

1. **Dieselben Aufgaben-Seeds für jede Version.** AndroidWorld erzeugt die konkreten Werte einer Aufgabe (Namen, Nummern, Texte) aus einem Startwert, dem Seed. Wir benutzen AndroidWorlds eigene Formel. So bekommt Lauf 1 in V1, V2 und V3 exakt denselben Kontakt, und jeder, der das Skript startet, auch.
2. **Temperatur 0, fester Modell-Seed, alles pro Lauf gespeichert.** Das Modell würfelt nicht. Und jeder Lauf schreibt in seine `meta.json`, welches Modell genau lief: Name, Größe, Quantisierung, Digest (Prüfsumme der Datei). Zitat aus der Vorlesung: Wer Quantisierung oder Modell wechselt, muss alles neu laufen lassen, es ist ein anderes Modell. Folie 26 hat gezeigt, dass das stimmt.
3. **AndroidWorld auf einen Stand festgenagelt, Setup-Skripte für Mac und Windows, 209 automatische Tests ohne Emulator.** Das Repository zeigt auf eine feste Version von AndroidWorld, damit niemand mit einer neueren, anderen Version arbeitet. Ein Skript pro Betriebssystem installiert alles. Die Tests prüfen den Code (Guardrails, Parsen, Grounding), ohne dass ein Emulator laufen muss.
4. **Jeder Lauf hinterlässt Spuren:** `trajectory.jsonl` (jeder Schritt mit Prompt, Antwort des Modells, Aktion, Wirkung), Screenshots mit markiertem Tipp, `recording.mp4` (das Bildschirmvideo) und eine Zeile in der Log-Tabelle. Das ist genau das Material, mit dem wir die Fehler analysiert haben; jeder andere kann es auch.

### Was du sagst, in dieser Reihenfolge

1. „Ein Befehl pro Version, mehr nicht. Die Version ist eine Konfigurationsdatei, der Code ist für alle gleich."
2. „Dieselben Aufgaben für jede Version und für jeden, der es nachstartet, weil die Werte aus festen Seeds kommen."
3. „Jeder Lauf speichert, welches Modell genau lief, bis zur Prüfsumme. Und jeder Lauf hinterlässt Verlauf, Screenshots, Video und eine Log-Zeile."
4. „Setup-Skripte für Mac und Windows, AndroidWorld auf einem festen Stand. Unser Kollege hat es auf dem Mac nachgestellt, ich auf Windows."

### Vor dem Vortrag prüfen

- Die Zahl 209 Tests nach dem Zusammenführen mit dem Repo des Kollegen nochmal zählen (`pytest`).
- Wenn das Deck als PDF ins Repo geht: Pfad in der README nennen.

### Mögliche Rückfragen

- „Warum trotzdem andere Einzelergebnisse auf dem Mac?" Weil der Modell-Digest anders war (Folie 26). Mit identischer Modelldatei und Temperatur 0 wären die Antworten gleich; der Emulator kann trotzdem minimal anders reagieren (Zeitpunkt, an dem ein Bildschirm aufgebaut ist).
- „Wo liegt der Code?" Privates GitHub-Repository `androidworld-gui-agent`, Zugang über den Kollegen; Abgabe laut Syllabus über Moodle.

---

## Folie 28: Key findings (What we learned)

**Überschrift:** Four things the runs told us that a demo would not have

**Auf der Folie:** vier fette Sätze mit je einem Halbsatz Beleg darunter. Orangefarbene Akzente, die einzige Stelle im Deck mit Orange: Das sind die Lektionen.

**Um was es geht:** Letzte Inhaltsfolie vor dem Schlusssatz. Pflichtinhalt „Key findings". Das ist, was der Dozent sich merken soll. Jede Zeile ist eine Erkenntnis, die nur durch Messen entstanden ist, nicht durch eine Vorführung. Ungefähr 60 bis 75 Sekunden.

### Die vier Erkenntnisse, erklärt

**1. Where grounding happens matters more than prompt wording.**
Wo das Zeigen passiert (im Modell oder im Code), hat mehr bewirkt als jede Formulierung im Prompt. Als wir das Zeigen in den Code verlegt haben (V2), wurde jeder Schritt dreimal schneller, und die Tipps ins Leere verschwanden. Gleichzeitig wurde eine neue Schwäche sichtbar: verlorene Werte (der Nachname). Beleg: Folie 24.

**2. Every safety mechanism encodes an assumption about the app.**
Jeder Sicherheitsmechanismus enthält eine Annahme darüber, wie die App sich verhält. Hinweis, Loop-Guard und Prüfschritt von V3 nehmen alle an, dass eine erfolgreiche Aktion den Bildschirm sichtbar verändert. Markor speichert automatisch, ohne sichtbare Änderung. Deshalb sind alle drei bei Save falsch angesprungen. Aus 2 von 9 (Mac) bzw. 3 von 9 (Windows) wurden 0 von 9. Beleg: Folie 21.

**3. A verifier as weak as the actor adds cost, not safety.**
Ein Prüfer, der genauso schwach ist wie der Handelnde, bringt Kosten, aber keine Sicherheit. Unser Prüfschritt vor „fertig" war dasselbe 4B-Modell, das den Fehler gemacht hatte. Es hat den fehlenden Nachnamen jedes Mal durchgewinkt und dabei jeden Schritt teurer gemacht. Beleg: Folien 20 und 21.

**4. Three runs per task find patterns, not rankings.**
Drei Läufe pro Aufgabe reichen, um Muster zu finden, nicht, um Versionen zu ranken. Ein einziger Lauf verschiebt eine Aufgabe um 33 Prozentpunkte. Die Erkenntnisse stecken in den Verläufen (was ist Schritt für Schritt passiert), nicht in den Quoten. Beleg: Folien 24 und 26.

### Was du sagst, in dieser Reihenfolge

Die vier fetten Sätze vorlesen, in eigenen Worten, je einen Halbsatz Beleg dazu. Nicht ausschweifen, die Belege sind alle schon gezeigt worden. Danach direkt zur Schlussfolie: „Und das bringt uns zu unserem Schlusssatz."

Punkt 1 bis 3 sind die Lektionen aus der Analyse des Kollegen, bestätigt durch die Windows-Läufe. Punkt 4 ist die methodische Lektion aus der Vorlesung („how many times did you run it?"), an unseren Zahlen belegt.

### Mögliche Rückfragen

- „Was würdet ihr als Nächstes tun?" Zwei Dinge: dem Modell Liste und Bild zusammen geben (gegen den übersehenen Nachnamen), und den Prüfschritt auf den Gerätezustand setzen statt auf den Bildschirm (Kontaktdatenbank, Dateiliste). Beides steht auf Folie 25.
- „War das Projekt dann ein Misserfolg?" Nein. Die Aufgabe war, zu messen, wo der Agent bricht, und das belegt zu erklären. Das haben wir mit 54 Läufen auf zwei Rechnern. Ein Agent, der auf dem Papier besser aussieht, aber nie gemessen wurde, wäre der Misserfolg gewesen.

---

## Folien 29 bis 31: Schluss

- **Folie 29 (Kernsatz, dunkelblau):** „The model decides. The harness makes it safe, measurable and honest." Ein Satz, mehr nicht: „Das Modell entscheidet. Der Harness macht es sicher, messbar und ehrlich. Das war unser Projekt."
- **Folie 30 (Thank you):** spiegelt die Titelfolie, Namen, „Questions?". Hier stehen bleiben für die Fragerunde.
- **Folie 31 (Backup-Trenner):** nur weiterblättern, wenn eine Frage eine der fünf Backup-Folien braucht.

---

## Backup B3: Skills, user memory, RAG (nur für die Fragerunde)

Aus dem Hauptteil genommen (08.10.), weil die Folie dreimal „nicht gebaut" sagt und die Story unterbricht. Liegt hinter dem Schluss als Backup. Die Antworten auch ohne Folie parat haben:

- **„Warum keine Skills?"** Gebaut (eine Tipp-Datei pro App, kommt nur in den Prompt, solange die App offen ist), aber in allen drei Versionen aus. Ein Tipp verändert den Agenten; dann wäre V1 gegen V2 nicht mehr sauber vergleichbar. Zeigt die Fehleranalyse eine App-Falle (z. B. Markors Dialog für die Dateiendung), wäre ein Einzeiler in der Skill-Datei der richtige Ort: ein Urteil in einem Satz gehört in Instructions.
- **„Warum kein User Memory?"** Langzeitgedächtnis über Sitzungen hinweg bringt nichts, weil jeder Lauf frisch startet mit neuen Namen und Nummern. Das einzige Gedächtnis ist die Notizzeile innerhalb eines Laufs in V3.
- **„Warum kein RAG?"** RAG holt Wissen aus Dokumenten. Unser Problem ist nicht fehlendes Wissen, sondern Wahrnehmung: Der Agent liest den Bildschirm falsch oder sagt zu früh „fertig". Was er braucht, ist der aktuelle Bildschirm, und den liefert der Tree jeden Schritt.

Satz für alle drei: „Wir haben die Konzepte geprüft und bewusst weggelassen, weil unser Engpass Wahrnehmung ist, nicht Wissen."
