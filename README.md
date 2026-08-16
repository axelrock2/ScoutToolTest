# ScoutToolTest

Scouting-Terminal für 13 europäische Ligen — als reine statische Seite,
ohne Server und ohne laufende Kosten.

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
die aktualisierte `data/players.json`. Über *Actions → Spielerdaten
aktualisieren → Run workflow* lässt er sich auch von Hand starten, wahlweise
für einzelne Ligen oder eine andere Saison.

## Hinweis

Reines Informationswerkzeug. Die Daten stammen aus öffentlich zugänglichen
Quellen und werden ohne Gewähr dargestellt.
