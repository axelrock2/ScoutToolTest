# ScoutToolTest

**→ [axelrock2.github.io/ScoutToolTest](https://axelrock2.github.io/ScoutToolTest/)**

Scouting-Terminal für 33 Wettbewerbe — von der Premier League bis zur
Oberliga. Reine statische Seite, ohne Server und ohne laufende Kosten.

## Liganiveau statt Spielklasse

Ein Percentil gilt nur innerhalb seiner Liga. Note 85 aus der Oberliga
neben Note 85 aus der Bundesliga zu stellen, wäre eine stillschweigende
Gleichsetzung. Das Tool leitet deshalb je Liga ein **Niveau** aus dem
Median-Marktwert ab — aussagekräftiger als die bloße Spielklasse:

| Niveau | Liga |
|---|---|
| 98 | Premier League |
| 80 | Bundesliga, Serie A |
| 63 | Championship **und** Jupiler Pro League |
| 53 | 2. Bundesliga |
| 47 | Österreich Bundesliga, Ligue 2 |
| 37 | 3. Liga |
| 19 | Regionalliga |
| 12 | Oberliga *(geschätzt, dort fehlen Marktwerte)* |

Die Championship liegt gleichauf mit Belgiens erster Liga, Österreich
unter der Ligue 2 — das bildet die Spielklasse allein nicht ab.

Im Vereins-Matching wird die Passung um diesen Abstand bereinigt, sonst
schlüge ein Regionalliga-Torjäger einen soliden Bundesligaspieler. Die
Karte zeigt zusätzlich eine **eingeordnete Note**, ausdrücklich als
Schätzung — gemessen ist nur der Wert in der eigenen Liga.

**Suchradius und Budget** begrenzen das Matching auf realistische Ziele.
Ohne sie empfahl das Tool einem Oberligisten folgerichtig Weltklasse-
spieler: Freiburg mit 15 Mio. € Budget bekommt jetzt Marc Guiu statt
Haaland, ein Oberligist Regionalligaspieler für 50–600 Tsd. €.

## Wie die Daten hereinkommen

Die Seite braucht **kein Backend**. Die Daten werden nachts serverseitig in
einer GitHub Action gesammelt und liegen als JSON im Repository:

```
scripts/build_players.py   →  data/players_raw.json   (Rohdaten)
scripts/compute_grades.py  →  data/players.json       (Percentile + Noten)
index.html                 →  liest nur data/players.json
```

Der frühere Ansatz (FastAPI auf `localhost:8000`) ist damit hinfällig: Er
funktionierte nur auf dem eigenen Rechner, nicht auf GitHub Pages, und
scheiterte an CORS. Der jetzige Weg hat kein CORS-Problem, weil das Frontend
eine Datei aus demselben Verzeichnis liest.

Schlägt das Laden fehl, zeigt die Seite die eingebauten Demo-Daten und
markiert das in der Kopfzeile — sie ist also nie leer.

## Ligen

| Land | Ligen |
|---|---|
| Deutschland | Bundesliga, 2. Bundesliga |
| England | Premier League, Championship |
| Spanien | La Liga, LaLiga 2 |
| Italien | Serie A, Serie B |
| Frankreich | Ligue 1, Ligue 2 |
| Belgien | Jupiler Pro League |
| Portugal | Liga Portugal |
| Österreich | Bundesliga |

Dazu der **deutsche Unterbau**: 3. Liga, alle fünf Regionalligen und alle
vierzehn Oberligen — zusammen 33 Wettbewerbe und rund 620 Vereine.

Eine Liga ergänzen = eine Zeile in `scripts/leagues.py`.

## Kennzahlen — und was bewusst fehlt

Ausgewiesen werden nur Werte, die sich aus frei verfügbaren Quellen
belegen lassen:

- Tore / 90, Vorlagen / 90, Scorerpunkte / 90
- **Anteil an den Toren der Mannschaft** — zehn Tore in einem Team mit 30
  Toren wiegen schwerer als zehn in einem Team mit 90
- **Einsatzanteil an den Saisonspielen** (statt roher Einsatzzahl, so sind
  Ligen mit unterschiedlich vielen Spieltagen vergleichbar)
- **Defensive der Mannschaft** — Gegentore je Spiel aus der Ligatabelle
- Minuten je Einsatz, Disziplin (Karten, invertiert)
- Profil: Alter, Größe, Fuß, Marktwert, Vertragsende

### Positionsspezifisch gewichtet

Ungewichtet zählte jede Kennzahl gleich viel. Für Stürmer ging das auf, für
Innenverteidiger nicht: deren Note bestand fast nur aus Einsätzen, Minuten
und Karten — also aus Verfügbarkeit, nicht aus Spielstärke. Jede Position
hat deshalb ihr eigenes Profil mit Gewichten:

| Position | dreifach | zweifach |
|---|---|---|
| Torwart | Defensive der Mannschaft, Einsatzanteil | — |
| Innenverteidigung | Defensive der Mannschaft, Einsatzanteil | — |
| Außenverteidigung | — | Defensive, Einsatzanteil, Vorlagen / 90 |
| Zentrales Mittelfeld | — | Anteil an Teamtoren, Scorerpunkte, Vorlagen, Einsatzanteil |
| Offensive | Scorerpunkte / 90 | Anteil an Teamtoren, Vorlagen, Tore / 90 |
| Sturm | Tore / 90 | Anteil an Teamtoren, Scorerpunkte / 90 |

Der Effekt ist deutlich: Bayerns Innenverteidigung stieg von Platz 8 auf
**Platz 1 der Liga**, Heidenheim fiel auf Platz 17. Die Abwehrnoten folgen
jetzt den tatsächlichen Gegentoren — Dortmund (34 Gegentore) führt, Heidenheim
(72) schließt ab.

**Die Defensive der Mannschaft ist ein Mannschaftswert**, kein individueller.
Das Profil kennzeichnet sie als solchen. Ein Innenverteidiger einer starken
Abwehr bekommt davon einen guten Wert, auch wenn sein eigener Anteil daran
nicht messbar ist — individuelle Zweikampf- und Passdaten führt keine freie
Quelle.

### Erweiterte Werte: xG (nur fünf Ligen)

Für Premier League, La Liga, Bundesliga, Serie A und Ligue 1 kommen von
[Understat](https://understat.com) **xG, xA, Schlüsselpässe, Schüsse und
Aufbaubeteiligung** dazu — rund 2.200 Spieler. Sie zeigen die *Qualität* der
Chancen, nicht nur ihre Zahl: Harry Kane traf 36-mal bei 29,58 xG, also
6,42 Tore über Erwartung.

**Diese Werte gehen bewusst nicht in die Liga-Note ein.** Sie liegen nur für
5 der 33 Ligen vor; eine Note daraus wäre mit den übrigen 28 nicht
vergleichbar. Sie stehen als eigener Abschnitt in der Spielerakte.

Nicht verfügbar bleiben **individuelle Defensivdaten** (Zweikämpfe,
Tacklings, Klärungen). FBref und Sofascore hätten sie, antworten aber mit
HTTP 403 — auch über den Browser-Weg. OneFootball führt öffentlich gar keine
Spielerstatistiken.

Dieselbe Ehrlichkeit gilt beim Vereins-Matching: die Stil-Dimensionen
*Pressing* und *Aufbau* lassen sich ohne Ereignisdaten nicht seriös
berechnen und werden als **Datenlücke** ausgewiesen statt mit einer
erfundenen Zahl gefüllt.

### Datenlage im deutschen Unterbau

Je tiefer die Spielklasse, desto dünner die Quelle. Das Tool bildet das ab,
statt Lücken zu kaschieren:

| Stufe | Einsätze, Tore, Vorlagen, Minuten | Marktwert vorhanden | Unterbewertet-Index |
|---|---|---|---|
| 1. Ligen | vollständig | 98 % | ja |
| 2. Ligen | vollständig | 96 % | ja |
| 3. Liga | vollständig | 94 % | ja |
| Regionalliga | vollständig | 86 % | ja |
| Oberliga | vollständig | **2 %** | **entfällt** |

Leistungsdaten reichen bis in die 5. Liga hinunter — Einsätze, Tore,
Vorlagen und Minuten sind dort genauso gepflegt wie oben. Marktwerte
dagegen brechen in der Oberliga weg. Der Unterbewertet-Index wird deshalb
je Vergleichsgruppe abgeschaltet, sobald zu wenige Werte vorliegen; sonst
erschiene dort jeder überdurchschnittliche Spieler automatisch als
unterbewertet. Die Spielerakte nennt den Grund, die Karte zeigt „k. A.".

Jede Staffel ist eine **eigene Vergleichsgruppe**: ein Stürmer der Oberliga
Westfalen wird mit Stürmern der Oberliga Westfalen verglichen, nicht mit der
Bayernliga.

Percentile werden immer innerhalb derselben Liga **und** Positionsgruppe
gebildet — ein Innenverteidiger der 2. Bundesliga wird mit
Innenverteidigern der 2. Bundesliga verglichen.

Spieler unter 450 Saisonminuten werden **nicht verworfen**, sondern als
dünne Stichprobe gekennzeichnet (Hinweis auf der Karte, Schalter „Nur
belastbare Stichprobe" in der Filterleiste). Der Vergleichsmaßstab selbst
entsteht aber nur aus Spielern oberhalb der Schwelle — sonst würden
Kurzeinsätze mit einem Tor die Percentile verzerren.

## Selbst laufen lassen

```bash
pip install -r requirements.txt

# Schnelltest: zwei Vereine einer Liga
python3 scripts/build_players.py --ligen buli2 --max-vereine 2
python3 scripts/compute_grades.py

# Vollständiger Lauf (alle 13 Ligen, ca. 15 Minuten)
python3 scripts/build_players.py
python3 scripts/compute_grades.py
```

Lokal ansehen (nötig, weil `fetch` unter `file://` nicht funktioniert):

```bash
python3 -m http.server 8777
```

Abgerufene Seiten landen 6 Stunden lang in `.cache/`, damit Testläufe die
Quelle nicht unnötig belasten.

## Aktualisieren

**Der verlässliche Weg läuft auf dem eigenen Rechner:**

```bash
./scripts/update_local.sh
```

Sammelt alle 33 Ligen, berechnet die Noten, committet und pusht. GitHub
Pages baut die Seite danach von allein neu. Für einen Teillauf:
`./scripts/update_local.sh buli,buli2`, zum Ausprobieren ohne Push
`PUSH=0 ./scripts/update_local.sh`.

### Warum nicht in der GitHub Action?

**Transfermarkt blockt Rechenzentren.** Aus einem GitHub-Runner kommt erst
HTTP 202 zurück (Bot-Abwehr), inzwischen 403 — auch mit installiertem
Browser über den Stealth-Weg. Vom privaten Anschluss antwortet dieselbe
Adresse mit 200, und zwar in 0,6 s statt 4,5 s. Ein voller Durchlauf
dauert lokal Minuten, im Runner über eine Stunde, sofern er überhaupt
durchkommt.

Die Action (`.github/workflows/players.yml`) bleibt als Zweitweg
erhalten und versucht es sonntags. Fällt die Blockade, springt sie von
allein wieder an. Sie sammelt dann rotierend drei von acht Gruppen pro
Lauf, höchstens zwei gleichzeitig — sieben parallel lösten die Abwehr
sofort aus.

### Zwei Fallen, die Daten gekostet haben

**Werte nur aus der eigenen Liga.** Ohne den Parameter
`reldata=<Wettbewerb>&<Saison>` liefert Transfermarkt alle Pflichtspiele
zusammen. Harry Kane stand so mit 51 Einsätzen und 61 Toren in den Daten
statt mit 31 und 36 aus der Bundesliga. Das maß Spieler mit Europapokal an
Spielern ohne — Serhou Guirassy fiel nach der Korrektur von Note 83 auf 74.

**`data/players_raw.json.gz` gehört ins Repository.** Der Sammellauf
ergänzt den vorhandenen Bestand; ohne die Datei startet er bei null. Ein
Lauf mit nur einer Liga hat so einmal 17.296 Spieler durch 346 ersetzt.
Gepackt sind es 0,7 MB. Zusätzlich bricht `compute_grades.py` ab, wenn ein
Lauf den Bestand auf unter die Hälfte schrumpfen würde
(`SCOUT_SCHRUMPFEN_OK=1` übergeht das).

**Ein Teillauf darf die übrigen Ligen nicht löschen.** `build_players.py`
führt deshalb zusammen statt zu überschreiben, `merge_raw.py` tut dasselbe
für parallele Teilergebnisse. Eine Liga, die heute ausfällt, behält ihren
letzten Stand.

## Hinweis

Reines Informationswerkzeug. Die Daten stammen aus öffentlich zugänglichen
Quellen und werden ohne Gewähr dargestellt.
