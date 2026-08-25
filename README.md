# ScoutToolTest

**→ [axelrock2.github.io/ScoutToolTest](https://axelrock2.github.io/ScoutToolTest/)**

Scouting-Terminal für 33 Wettbewerbe — von der Premier League bis zur
Oberliga. Reine statische Seite, ohne Server und ohne laufende Kosten.

## Liganiveau statt Spielklasse

Ein Percentil gilt nur innerhalb seiner Liga. Note 85 aus der Oberliga
neben Note 85 aus der Bundesliga zu stellen, wäre eine stillschweigende
Gleichsetzung. Das Tool weist deshalb jeder Liga ein **Niveau** zu — aus
zwei Quellen gemischt:

**60 % UEFA-Fünfjahreskoeffizient** (Länderwertung 2025/26, Europapokal-
ergebnisse) und **40 % Median-Marktwert**. Jüngere Jahre wiegen dabei
deutlich schwerer (Gewichte 1·2·4·6·9 für 21/22 bis 25/26): Das Werkzeug
bewertet Spieler der Saison 2025/26, Ergebnisse von 2021/22 sagen wenig
über die Stärke einer Liga heute.

| Niveau | Liga |
|---|---|
| 100 | Premier League |
| 86 | Bundesliga |
| 85 | Serie A |
| 84 | La Liga |
| 80 | Ligue 1 |
| 71 | Liga Portugal |
| 68 | Jupiler Pro League |
| 65 | Championship |
| 57 | 2. Bundesliga |
| 55 | LaLiga 2 |
| 52 | Serie B |
| 49 | Ligue 2 |
| 48 | Österreich Bundesliga |
| 38 | 3. Liga |
| 20 | Regionalliga |
| 12 | Oberliga *(geschätzt, dort fehlen Marktwerte)* |

**Warum nicht Marktwert allein?** Der verzerrte systematisch: La Liga und
Serie A haben niedrigere Median-Marktwerte als die Bundesliga, sind im
Europapokal aber erfolgreicher. Portugal stand bei 57, liegt im
UEFA-Ranking aber vor Belgien.

**Der Abstand zwischen 84, 85 und 86 liegt innerhalb der Messgenauigkeit.**
Diese drei Ligen sind praktisch gleich stark — die Rangfolge dazwischen
sollte niemand überdeuten.

Ligen ohne eigenen UEFA-Wert (zweite Ligen, deutscher Unterbau) erben den
Abstand zu ihrer ersten Liga, wie ihn die Marktwerte ausweisen. Dieses
Verhältnis ist bemerkenswert stabil: Championship/PL 0,65, 2. BL/BL 0,66,
LaLiga2/LaLiga 0,65.

Der UEFA-Koeffizient wird dabei per Wurzel gestaucht — er wird von wenigen
Spitzenvereinen getrieben; linear übersetzt fiele Österreich unter die
deutsche 3. Liga, was die Breite der Liga völlig verfehlt.

Im Vereins-Matching wird die Passung um diesen Abstand bereinigt, sonst
schlüge ein Regionalliga-Torjäger einen soliden Bundesligaspieler. Die
Karte zeigt zusätzlich eine **eingeordnete Note**, ausdrücklich als
Schätzung — gemessen ist nur der Wert in der eigenen Liga.

**Suchradius und Budget** begrenzen das Matching auf realistische Ziele.
Ohne sie empfahl das Tool einem Oberligisten folgerichtig Weltklasse-
spieler: Freiburg mit 15 Mio. € Budget bekommt jetzt Marc Guiu statt
Haaland, ein Oberligist Regionalligaspieler für 50–600 Tsd. €.

## Gestaltung

Helle, warme Fläche statt Nachtgrün: Papierton, weiße Karten mit kaum
sichtbarem Schatten, ein einziges tiefes Grün als Akzent. Abstände tragen
die Ordnung, nicht Rahmen oder Leuchteffekte.

**Helle und dunkle Ansicht** lassen sich über den Schalter rechts in der
Kopfleiste wechseln. Beim ersten Besuch entscheidet die Systemeinstellung
(`prefers-color-scheme`), danach gilt die getroffene Wahl — gespeichert im
Browser. Gesetzt wird sie im Seitenkopf, bevor gezeichnet wird, damit beim
Laden nicht kurz die falsche Welt aufblitzt.

Die Startseite verzichtet auf einen Slogan. Sie führt mit dem, was das
Werkzeug tatsächlich hat: bewertete Spieler, Wettbewerbe, Saison und
Datenstand — live aus den geladenen Daten gefüllt. Der frühere Werbetext
nannte obendrein veraltete Zahlen (16 Ligen statt 33).

Beim Scrollen blenden Abschnitte und Karten leicht versetzt ein, die
Kopfzone tritt sanft zurück, Karten heben sich beim Überfahren minimal an.

Zwei Vorkehrungen, damit daraus kein Schaden entsteht:

- **Inhalt hängt nie von einer Animation ab.** Die ausblendende Klasse
  setzt allein das Skript — ohne Skript, bei abgeschalteten
  Bewegungseffekten (`prefers-reduced-motion`) oder bei einem Fehler
  bleibt alles sofort sichtbar. Ein Sicherheitsnetz blendet nach zwei
  Sekunden ein, was noch verborgen ist.
- **Die Effekte liegen in einem eigenen Skriptblock** nach der Anwendung
  und rufen keine ihrer Funktionen auf. Fällt dieser Block aus, läuft das
  Werkzeug unverändert weiter.

Das Aussehen ist rein additiv ergänzt — keine bestehende Regel wurde
umgeschrieben, keine Klasse umbenannt.

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

## Datenherkunft

Jede Angabe lässt sich einer Quelle zuordnen — nachlesbar in jeder
Spielerakte unter *Datenherkunft*, in Kurzform auf der Startseite.

| Art | Quelle | Was daher stammt |
|---|---|---|
| **erhoben** | [Transfermarkt](https://www.transfermarkt.de) | Stammdaten, Marktwert, Vertrag, Einsätze, Tore, Vorlagen, Karten, Minuten, Mannschaftswerte, Verletzungshistorie |
| **erhoben** | [Understat](https://understat.com) | xG, npxG, xA, Schlüsselpässe, Schüsse, Aufbaubeteiligung *(nur 5 Ligen)* |
| **berechnet** | dieses Werkzeug | Liga-Note, Positions-Note, Team-Note, Percentile, Liganiveau, Unterbewertet-Index |
| **fehlt** | — | Zweikämpfe, Tacklings, Klärungen, Passquote, Laufleistung, Gewicht |

Die Trennung ist wichtig: Eine **erhobene** Körpergröße und eine
**berechnete** Note sind zweierlei — und was gar nicht vorliegt, gehört
ebenso benannt wie das Vorhandene.

## Verletzungshistorie

Aus Transfermarkt, kostenlos: Art, Zeitraum, Ausfalltage und verpasste
Spiele je Verletzung, dazu die Summen der letzten drei Jahre.

Das kostet **einen Abruf je Spieler** — für alle 16.761 wären es gut
sieben Stunden. Geholt wird deshalb nach Note absteigend und in Portionen;
wer schon erfasst ist, wird übersprungen:

```bash
python3 scripts/verletzungen.py                # ab Note 70, 600 Stück
python3 scripts/verletzungen.py --ab-note 80
```

Aktuell erfasst: **1.019 Spieler** (alle mit Note 70+, soweit im Zeitbudget
erreicht). Wer 90 Ausfalltage oder mehr in drei Jahren hat, trägt das
Kennzeichen bereits auf der Trefferkarte — dafür muss man kein Profil
öffnen. Ein Schalter in der Filterleiste blendet solche Spieler aus;
Spieler **ohne** Historie fallen dabei nicht heraus, fehlende Daten dürfen
niemanden aussortieren.

## Woraus eine Note entsteht

Eine einzelne Zahl verdeckt, worauf sie beruht. Die Spielerakte schlüsselt
sie deshalb auf — nach Bereichen (Offensive, Defensive, Verfügbarkeit,
Disziplin), mit der Größe der Vergleichsgruppe und den zugrunde liegenden
Spielminuten.

**Entscheidend dabei: der Mannschaftsanteil.** Für Abwehrpositionen gibt es
keine individuellen Daten, dort trägt die Defensive der Mannschaft einen
großen Teil der Note. Genau daher schwanken Bewertungen zwischen Vereinen.
Die Akte beziffert das:

| Spieler | Liga-Note | davon aus Mannschaftswerten |
|---|---|---|
| Erling Haaland (ST) | 94 | **0 %** — ganz seine eigene Leistung |
| Filip Stanković (TW) | 90 | **38 %** — gut ein Drittel vom Verein |

Ab 30 Prozent erscheint ein ausdrücklicher Warnhinweis.

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

**Saison 2025/26.** Die Spielzeit 2026/27 hat erst wenige Spieltage —
Percentile aus zwei Spielen wären Zufall. Umstellen lohnt etwa ab dem
10. Spieltag mit `SCOUT_SAISON=2026 ./scripts/update_local.sh`.

Für Premier League, La Liga, Bundesliga, Serie A und Ligue 1 kommen von
[Understat](https://understat.com) **xG, xA, Schlüsselpässe, Schüsse und
Aufbaubeteiligung** dazu — rund 2.200 Spieler. Sie zeigen die *Qualität* der
Chancen, nicht nur ihre Zahl: Harry Kane traf 36-mal bei 29,58 xG, also
6,42 Tore über Erwartung.

**Diese Werte gehen bewusst nicht in die Liga-Note ein.** Sie liegen nur für
5 der 33 Ligen vor; eine Note daraus wäre mit den übrigen 28 nicht
vergleichbar. Sie stehen als eigener Abschnitt in der Spielerakte.

### Videomaterial über YouTube

Die Spielerakte verlinkt unter dem Namen zwei YouTube-Suchen — einmal
**nur den Namen**, einmal **Name + Verein**.

Bewusst ohne Zusatzwort wie „highlights": Das schnitte Spielszenen,
Interviews und Vereinsvideos weg und liefe im Unterbau, wo es gar keine
Zusammenschnitte gibt, oft ins Leere. Der Vereinsname in der zweiten
Variante grenzt ein, wenn der Spielername mehrdeutig ist. Bewegtbild ist unterhalb
der Profiligen oft die einzige frei verfügbare Quelle über die Zahlen
hinaus — und kostet nichts.

### Bewusst kostenfrei — und was das kostet

Das Werkzeug nutzt ausschließlich frei zugängliche Quellen. Das ist eine
Entscheidung, keine Notlage — sie hat aber eine klare Konsequenz:
**individuelle Defensivdaten gibt es nicht.**

Geprüft wurde systematisch:

| Quelle | Hat Zweikämpfe/Tacklings? | Zugänglich? |
|---|---|---|
| Transfermarkt | nein | ✅ |
| Understat | nein (nur offensiv) | ✅ |
| fussballdaten.de | nein | ✅ |
| OneFootball | führt gar keine Spielerstatistiken | — |
| FBref | **ja** | ❌ HTTP 403, auch per Browser |
| Sofascore | **ja** | ❌ HTTP 403 |
| kicker (Zweikampfwerte) | **ja** | ❌ HTTP 403 |

Das Muster: Wer die Daten hat, blockt. Wer offen ist, hat sie nicht.
Kostenpflichtige Anbieter (Wyscout, StatsBomb, Opta) hätten sie — sind
aber bewusst ausgeschlossen.

**Für Abwehrpositionen heißt das:** Bewertet wird die Defensive der
Mannschaft, nicht die Einzelleistung. Innerhalb eines Vereins trennen sich
Innenverteidiger nur über Einsatzanteil und Disziplin. Das ist eine echte
Grenze des Werkzeugs, keine Ungenauigkeit — und sie wird im Profil
ausgewiesen statt kaschiert.

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

Es läuft **kein Zeitplan**. Aktualisiert wird bei Benutzung — der Bestand
einer abgeschlossenen Saison veraltet ohnehin kaum, es ändern sich vor
allem Marktwerte und Verträge.

Die Seite weist selbst darauf hin: Ab sieben Tagen erscheint das Alter in
der Kopfzeile, ab vierzehn Tagen zusätzlich ein Hinweis auf der Startseite
samt Befehl.

**Der verlässliche Weg läuft auf dem eigenen Rechner:**

```bash
./scripts/update_local.sh
```

### Nach dem Transferschluss

Leistungsdaten einer abgelaufenen Saison ändern sich nie mehr — Verträge,
Marktwerte und Vereinszugehörigkeit dagegen sehr wohl. Dafür genügt ein
Abruf je Verein statt eines vollen Laufs:

```bash
python3 scripts/build_players.py --kader-aktuell
python3 scripts/compute_grades.py
```

Das zieht aus den **heutigen** Kadern nach: Vertragsenden, Marktwerte,
Größe und Fuß. Wer dort nicht mehr auftaucht, hat den Verein verlassen und
wird als *„nicht mehr im Kader"* gekennzeichnet — seine Leistungsdaten
stammen dann erkennbar aus seiner Zeit beim alten Verein.

Der Grund für den eigenen Modus: Die Kaderansicht einer **vergangenen**
Saison führt gar keine Vertragsspalte. Vertragsenden gibt es nur im
aktuellen Kader.

Weitere Teilläufe:

| Befehl | Holt |
|---|---|
| `--kader-aktuell` | Verträge, Marktwerte, Wechsel (1 Seite je Verein) |
| `--nur-kader` | Kaderprofile der Saison: Größe, Fuß, Position |
| `--nur-leistung` | Einsätze, Tore, Minuten (1 Seite je Verein) |
| `--nur-tabellen` | Ligatabellen (1 Seite je **Liga**, unter 1 Minute) |
| `--ligen buli,buli2` | nur bestimmte Ligen |

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
