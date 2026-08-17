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
- Gespielte Minuten, Einsätze, Minuten je Einsatz
- Disziplin (Karten, invertiert)
- Profil: Alter, Größe, Fuß, Marktwert, Vertragsende

**Nicht enthalten sind xG, xA und progressive Carries.** Diese Werte stammen
von kostenpflichtigen Anbietern (Opta, StatsBomb, Wyscout) und sind für 13
Ligen nicht frei zu bekommen. Sie werden deshalb weder angezeigt noch
geschätzt.

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

## Automatischer Lauf

`.github/workflows/players.yml` läuft täglich um 02:40 UTC und committet
die aktualisierten Daten. Über *Actions → Spielerdaten aktualisieren →
Run workflow* lässt er sich auch von Hand starten, wahlweise für einzelne
Ligen oder eine andere Saison.

Zwei Eigenheiten, die beim Einrichten Zeit gekostet haben:

**Transfermarkt blockt Rechenzentren.** Aus einem GitHub-Runner kommt
HTTP 202 zurück — eine Bot-Abwehrseite —, während dieselbe Adresse von
einem privaten Anschluss 200 liefert. Deshalb installiert die Action einen
Browser und nutzt den Stealth-Weg.

**`data/players_raw.json.gz` gehört ins Repository.** Der Sammellauf
ergänzt den vorhandenen Bestand; ohne die Datei startet er bei null. Ein
Lauf mit nur einer Liga hat so einmal 17.296 Spieler durch 346 ersetzt.
Gepackt sind es 0,7 MB. Zusätzlich bricht `compute_grades.py` ab, wenn ein
Lauf den Bestand auf unter die Hälfte schrumpfen würde
(`SCOUT_SCHRUMPFEN_OK=1` übergeht das).

## Hinweis

Reines Informationswerkzeug. Die Daten stammen aus öffentlich zugänglichen
Quellen und werden ohne Gewähr dargestellt.
