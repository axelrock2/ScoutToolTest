# ScoutToolTest

**→ [axelrock2.github.io/ScoutToolTest](https://axelrock2.github.io/ScoutToolTest/)**

Scouting-Terminal für 35 Wettbewerbe — von der Premier League bis zur
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
| Polen | Ekstraklasa |
| Tschechien | Chance Liga |

Dazu der **deutsche Unterbau**: 3. Liga, alle fünf Regionalligen und alle
vierzehn Oberligen — zusammen 35 Wettbewerbe und rund 650 Vereine.

Polen und Tschechien stehen in der UEFA-Fünfjahreswertung inzwischen vor
Österreich (Polen 12., Tschechien 10., Österreich 17.) — als Markt für
Mitteleuropa also ergiebiger, als die Aufmerksamkeit vermuten ließe.

Eine Liga ergänzen = eine Zeile in `scripts/leagues.py`.

## Datenherkunft

Jede Angabe lässt sich einer Quelle zuordnen — nachlesbar in jeder
Spielerakte unter *Datenherkunft*, in Kurzform auf der Startseite.

| Art | Quelle | Was daher stammt |
|---|---|---|
| **erhoben** | [Transfermarkt](https://www.transfermarkt.de) | Stammdaten, Marktwert, Vertrag, Einsätze, Tore, Vorlagen, Karten, Minuten, Mannschaftswerte, Verletzungshistorie |
| **erhoben** | Transfermarkt · Vereinsseite *Vertragsende* | Auslaufender Vertrag, Vertragsoption, Leihe |
| **erhoben** | [Understat](https://understat.com) | xG, npxG, xA, Schlüsselpässe, Schüsse, Aufbaubeteiligung *(nur 5 Ligen)* |
| **erhoben** | [Sofascore](https://www.sofascore.com) | Zweikampfquote gesamt/Boden/Luft, Tacklings, Interceptions *(16 Ligen bis zur 3. Liga)* |
| **erhoben** | Transfermarkt · Bilder | Spielerfoto, Vereinswappen *(per Verweis, nicht gespeichert)* |
| **berechnet** | dieses Werkzeug | Liga-Note, Positions-Note, Team-Note, Percentile, Liganiveau, Unterbewertet-Index |
| **fehlt** | — | Zweikämpfe unterhalb der 3. Liga, Klärungen, Passquote, Laufleistung, Gewicht |

Die Trennung ist wichtig: Eine **erhobene** Körpergröße und eine
**berechnete** Note sind zweierlei — und was gar nicht vorliegt, gehört
ebenso benannt wie das Vorhandene.

## Mehrere Ligen auf einmal

Der Liga-Filter ist eine Mehrfachauswahl — in der Spielersuche wie bei den
Vertragsausläufern. Ein natives `<select multiple>` verlangt Strg-Klick und
zeigt bei 35 Einträgen entweder eine winzige oder eine sehr lange Liste;
stattdessen klappt ein Feld mit Kästchen auf, nach Spielklasse gruppiert.
Jede Gruppenüberschrift schaltet ihre Gruppe als Ganzes, dazu gibt es
*Alle* und *Nur erste Ligen*.

**Keine Auswahl heißt „alle"** — der häufigste Fall, und er erspart es, 35
Kästchen anzuhaken, nur um nichts einzuschränken.

Eine Einschränkung, die dazugehört: Die *eingeordnete Note* rechnet eine
Liga-Note auf ein Zielniveau um und braucht dafür **ein** Zielniveau. Bei
mehreren gewählten Ligen gibt es keins — dann bleibt die Einordnung weg,
statt sich eine der Ligen willkürlich herauszugreifen.

## Spielerfotos

In der Spielerakte steht statt der Initialen das Portrait von
Transfermarkt — **nur dort**, nicht in den Trefferlisten. Der Grund ist
Rücksicht auf die Quelle: In einer Ergebnisliste wären es fünfzig Bilder je
Seite von fremden Servern, in der Akte ist es genau eines, und man schaut
einen Spieler ohnehin einzeln an.

Die Adresse trägt einen Zeitstempel:

```
https://img.a.transfermarkt.technology/portrait/medium/607720-1737037032.jpg
```

Ohne ihn antwortet der Server mit **404** — aus der Spieler-ID allein lässt
sie sich also nicht bilden. Geführt wird sie in der *schlichten*
Kaderansicht (`/kader/verein/<id>`, ohne `/plus/1`), dort im Attribut
`data-src`, weil Transfermarkt die Bilder nachlädt. Die ausführliche
Ansicht, die `build_players.py` ohnehin abruft, enthält sie nicht — daher
ein eigener Lauf, ein Abruf je Verein:

```bash
python3 scripts/bilder.py
python3 scripts/compute_grades.py
```

Gespeichert wird **nur der veränderliche Teil des Dateinamens** —
Zeitstempel *und Endung*, etwa `1701639955.png`; die ID steht ohnehin im
Datensatz, der unveränderte Teil einmal als `bild_basis`. Das kostet einen
Bruchteil dessen, was ganze Adressen kosten würden.

Die Endung muss mit: **rund ein Fünftel der Portraits sind PNG**, nicht
JPG. Sie wegzulassen und im Frontend `.jpg` anzuhängen hieß, dass jeder
fünfte Spieler mit hinterlegtem Bild keins bekam — aufgefallen an Cheick
Souaré, dessen Portrait eine `.png` ist. Ältere Datenstände ohne Endung
bekommen weiterhin `.jpg`, damit ein Frontend-Update ihnen nicht alles
nimmt.

**Der Rückfall auf die Initialen trägt sich selbst.** Das Bild liegt über
den Initialen und ist bis zum Laden durchsichtig — es hat *bewusst keine
Hintergrundfarbe*. So stehen die Initialen da, solange geladen wird, und
bleiben stehen, wenn nie etwas ankommt. Auf `onerror` allein wäre kein
Verlass: Ein hängender Abruf löst es nicht aus, und genau das passiert,
wenn ein Netz die Adresse blockiert statt sie abzulehnen.

Grenzen:

| | |
|---|---|
| Abdeckung | 100 % bis zur 3. Liga, 92–97 % in Regionalliga und Oberliga, in den schwächsten fünftklassigen Staffeln unter 30 % |
| Nur heutiger Kader | Wer den Verein verlassen hat, steht dort nicht mehr; sein Bild gäbe es nur über die Profilseite — ein Abruf **je Spieler**, also Stunden statt Minuten. Diese Spieler behalten die Initialen. |
| Platzhalter | Wo Transfermarkt kein Foto hat, liefert es `default.jpg`. Der wird verworfen — eine graue Silhouette sagt weniger als die Initialen. |
| Hotlinking | Die Bilder liegen weiter bei Transfermarkt und werden beim Öffnen einer Akte von dort geladen, nicht hier gespeichert. Wird der Verweis eines Tages gesperrt, greift der Rückfall. |

## Kaderansicht

Im Vereins-Matching öffnet **„Kader ansehen"** den Kader des gewählten
Vereins — aufgebaut wie der Kader auf Transfermarkt:

- Positionsgruppen **Torwart · Abwehr · Mittelfeld · Sturm**, darin die
  dort übliche Reihenfolge (Innenverteidiger vor linkem und rechtem
  Verteidiger, defensives vor zentralem und offensivem Mittelfeld,
  Linksaußen, Rechtsaußen, Mittelstürmer), dann die Rückennummer
- Spalten #, Spieler mit Foto und Position, Alter, Größe, Fuß, Vertrag bis,
  Marktwert — dazu die Liga-Note
- Kopf mit Wappen, Kadergröße, Ø-Alter, Gesamt- und Ø-Marktwert
- alternativ sortiert nach Liga-Note, Marktwert oder Alter

Hier werden **alle Fotos** geladen — in den Trefferlisten bewusst nicht,
weil dort Dutzende auf einmal von fremden Servern kämen.

Gezeigt wird der **vollständige** heutige Kader, auch Spieler ohne Note:
Neuzugänge aus nicht erfassten Ligen und Spieler ohne Einsatz in der
Notensaison — gedämpft, ohne Note, der Name verweist auf Transfermarkt.
Dafür gibt `compute_grades.py` sie als eigene kompakte Liste aus
(`ohne_note_spieler`, 4.942 Spieler); vorher kannte das Werkzeug nur
Spieler *mit* Note, und bei Bayern fehlte etwa Saibari.

Die **Startelf** der Kaderanalyse ist markiert; ein Stern an der Note heißt,
sie wurde in einer anderen Liga erspielt. Eine Zeile öffnet die
Spielerakte, deren Zurück-Knopf dann zum Kader führt; zurück im Matching
ist der Verein wieder ausgewählt.

## Scout-Fazit

Neutral und aus den Daten, nicht werbend. Früher stand dort „überzeugt vor
allem bei …", höchstens eine Schwäche und „wirtschaftlich interessant" —
ein Verkaufstext. Jetzt drei Absätze:

| Absatz | Inhalt |
|---|---|
| **Einordnung** | Verein und Liga heute; wo die Note erspielt wurde; was die Liga-Note bedeutet (gewichteter Durchschnitt der Percentile, 50 = Ligaschnitt) und gegen wie viele Spieler verglichen wird; bei Wechslern die umgerechnete Note; Stichprobe |
| **Stärken und Schwächen** | stärkster und schwächster Bereich, bis zu drei Kennzahlen darüber und darunter — Mannschaftswerte als solche gekennzeichnet —, Zweikampfquote, bei Offensivspielern xG gegen Tore, Anteil der Mannschaftswerte an der Note |
| **Rahmen** | Verletzungen (mit Stand), Vertrag samt Option oder Leihe, Marktwert gegen Leistungsniveau — auch wenn er *höher* liegt —, und was die Daten nicht enthalten |

Regeln für den Ton: Zahlen statt Adjektiven, keine Empfehlung, ein Mangel
wird genauso ausgesprochen wie eine Stärke. Aussagen, die eine Saison nicht
tragen kann, stehen auch nicht da — eine Chancenverwertung über dem
Erwartungswert heißt „ob sie sich wiederholt, lässt sich aus einer Saison
nicht ablesen", nicht „wird sich fortsetzen" und nicht „wird einbrechen".

## Zweikampfquoten

Individuelle Defensivwerte fehlten dem Werkzeug von Anfang an — der Grund,
weshalb Innenverteidiger nur über Mannschaftswerte zu bewerten waren. Die
Suche nach einer freien Quelle, 2026 erneut geprüft:

| Quelle | Ergebnis |
|---|---|
| OneFootball | führt keine individuellen Zweikampfwerte |
| FBref, kicker | sperren automatisierte Abrufe (403), auch mit Browser |
| FotMob | 66 Kennzahlen je Liga (Tacklings, Interceptions, Klärungen …), Zweikämpfe aber nur auf jeder einzelnen Spielerseite |
| **Sofascore** | antwortet, sobald die Anfrage die Kopfzeilen der eigenen Seite trägt — und liefert die Werte **gesammelt je Liga** |

Ein Abruf bringt 100 Spieler einer Liga mit frei wählbaren Feldern — rund
fünf Abrufe je Liga statt eines je Spieler:

```bash
python3 scripts/zweikaempfe.py            # alle abgedeckten Ligen, Saison wie die Noten
python3 scripts/compute_grades.py
```

Erfasst: **Zweikampfquote gesamt, am Boden, in der Luft**, dazu Tacklings
und Interceptions — für alle ersten und zweiten Ligen und die 3. Liga
(16 Ligen, 8.339 bewertete Spieler). Für Regional- und Oberligen führt
Sofascore keine Spielerstatistik; dort bleibt das Feld leer und die Akte
sagt es, statt zu schätzen.

**Zuordnung ohne gemeinsame ID.** Sofascore und Transfermarkt schreiben
Namen verschieden. Zuerst zählt der Name innerhalb der Liga; wo er nicht
wörtlich passt, eine zweite Stufe — aber **nur beim selben Verein**:
andere Reihenfolge („Kim Min-jae" / „Min-jae Kim"), Zusatzname („Rasmus
Kristensen" / „Rasmus Nissen Kristensen"), Kurzform („Ezequiel" / „Equi")
und Buchstaben, die die Akzententfernung nicht auflöst („Dźwigała"). Die
Nachnamen-Stufe prüft zusätzlich, ob die Einsatzminuten beider Quellen
zusammenpassen — sonst könnte ein Nachwuchsspieler gleichen Namens die
Quote des Stammspielers überschreiben. Bundesliga: 498 von 499 zugeordnet.

**Vergleich wie bei der Note:** je Liga und Position, nur mit belastbarer
Stichprobe (ab 40 Zweikämpfen und 450 Minuten). 58 % sind bei einem
Innenverteidiger etwas anderes als bei einem Stürmer — Kane gewinnt 52,7 %
und liegt damit unter den Bundesliga-Stürmern bei Percentil 98.

**In der Liga-Note — für Abwehr und Mittelfeld** (auf Rückfrage
entschieden). Die Zweikampfquote ist die erste *individuelle*
Defensivkennzahl; bis dahin bestand die Note eines Innenverteidigers aus
Mannschaftsgegentoren und Verfügbarkeit.

| Gruppe | Gewicht der Zweikampfquote | Anteil an der Note |
|---|---|---|
| Innenverteidiger | 3 — so viel wie die Mannschaftsdefensive | 25 % |
| Außenverteidiger | 2 | 20 % |
| Mittelfeld (DM und ZM) | 2 | 17 % |

DM und ZM bilden **eine** Vergleichsgruppe; die Quote gilt deshalb für
beide — nur für den DM wären die Noten innerhalb derselben Gruppe
unterschiedlich zusammengesetzt. Offensivspieler, Stürmer und Torhüter
bleiben unberührt.

Wo die Quote fehlt — unterhalb der 3. Liga, bei zu kleiner Stichprobe
(unter 40 Zweikämpfen) oder ohne Zuordnung —, wird sie **übersprungen und
die übrigen Gewichte neu verteilt**, nicht als schlechter Wert gelesen.
Gemessen: 13.250 Spieler unverändert, 3.407 Noten verschoben (Median
5 Punkte). Bundesliga-Innenverteidiger: Amos Pieper (71,8 %) steigt um 15,
Tapsoba (55,0 %) fällt um 13; die Spitze — Orbán, Anton, Schlotterbeck —
bleibt.

In der Akte steht die Quote als eigener Bereich *Zweikämpfe
(individuell)*, getrennt von der *Defensive (Mannschaft)*.

**Filter und Sortierung** in der Spielersuche: *Min. Zweikampfquote* und
*Sortieren: Zweikampfquote ↓*. Beides nur mit belastbarer Stichprobe; wer
keine hat, fällt beim Filter heraus und steht beim Sortieren am Ende — die
Ergebniszeile sagt es.

Beim Abgleich aufgefallen: Die Jupiler League war für 2025/26 nur mit
15 von 16 Vereinen gesammelt — Sint-Truiden fehlte, der Verein hatte keine
einzige Note. Nachgeholt (31 Spieler, 24 mit Einsätzen).

## Vereinswappen

In jeder Spielerakte steht das Wappen des heutigen Vereins vor dem
Vereinsnamen, per Verweis von Transfermarkt geladen wie die Fotos. Anders
als dort genügt die Vereins-ID — die Adresse trägt keinen Zeitstempel
(`…/wappen/normquad/<id>.png`). Lädt es nicht, verschwindet es; der Name
steht ohnehin daneben.

## Kader 2026/27, Noten 2025/26

Zwei Saisons, zwei Aussagen — und beide stehen ausdrücklich da:

| | Saison | Warum |
|---|---|---|
| **Vereine und Kader** | 2026/27 | Wer heute wo spielt: Schalke, Paderborn, Elversberg in der Bundesliga, Heidenheim, St. Pauli, Wolfsburg nicht mehr; Goretzka nicht mehr bei Bayern |
| **Noten** | 2025/26 | Die letzte *vollständige* Spielzeit. Nach zwei, drei Spieltagen wäre jedes Percentil Zufall — ein Doppelpack machte einen Durchschnittsstürmer zur Nummer eins |

```bash
python3 scripts/build_players.py --saison-aktuell   # Vereine + heutige Kader
```

Ein Abruf je Liga für die Vereinsliste, einer je Verein für den heutigen
Kader. Jeder Spieler bekommt seinen heutigen Verein (`aktuell`);
Neuzugänge aus nicht erfassten Ligen kommen als Datensatz **ohne Note**
hinzu — sie gehören zum Kader, eine Note lässt sich für sie nicht rechnen,
und die Kaderanalyse sagt, wie viele es sind („22 bewertete Spieler + 1
ohne Note"). Die Saison ergibt sich aus dem Datum (`SCOUT_AKTUELL`
überschreibt).

**Die Note bleibt dort, wo sie erspielt wurde.** Ein Aufsteiger steht heute
in der Bundesliga, sein Percentil aber gilt in der 2. Bundesliga. Karte und
Akte sagen das („Note aus 2025/26: FC Schalke 04 · 2. Bundesliga"), und
auch die Position bleibt die der Notensaison — die Note ist ein Percentil
innerhalb dieser Positionsgruppe.

Die **Liganiveaus** beschreiben die Ligen, in denen die Noten erspielt
wurden, und bleiben die freigegebenen Werte. Sonst verschöbe allein der
Auf- und Abstieg dreier Vereine das Niveau, obwohl sich keine einzige Note
ändert.

Zwei Kennzeichen, die man nicht verwechseln darf: *nicht mehr im Kader*
heißt, der Spieler hat den Verein verlassen; *Verein nicht mehr erfasst*
heißt, der Verein selbst spielt in keiner erfassten Liga mehr — dort steht
er durchaus noch im Kader. Unterscheiden lässt sich das nur mit den
Vereinslisten *aller* Ligen; ein Teillauf setzt es deshalb nicht.

## Kaderanalyse: Startelf statt Kaderschnitt

Grundlage jeder Kaderbewertung ist die **Startelf**. Früher zählte der
Schnitt *aller* Spieler einer Position — ein Nachwuchsspieler mit drei
Einsatzminuten zog Bayerns defensives Mittelfeld von 78 (Kimmich) auf 50.

Aufstellungen führt die Quelle kostenlos nicht; die Startelf wird aus den
Ligaminuten der Notensaison abgeleitet: je Position der meistgespielte
Spieler, in der Innenverteidigung die zwei meistgespielten — zusammen elf.
Nachwuchsspieler fallen damit von selbst heraus, ohne ein eigenes Merkmal.

**Die Bank geht getrennt ein.** Der Bedarf richtet sich allein nach der
Startelf; ob ein Ausfall aufzufangen wäre, steht als eigener Abschnitt
*Kadertiefe* — „kein Ersatz im Kader" oder „bester Ersatz 20+ Punkte unter
der Startelf". Zwei Aussagen statt einer vermischten.

**Noten aus anderen Ligen werden umgerechnet.** Seit die Kader aus 2026/27
stammen, stehen in einem Kader Noten aus verschiedenen Ligen nebeneinander
— bei den Bundesligisten 179 von 449 Spielern. Roh übernommen hätte der
Aufsteiger Elversberg die beste Startelf der Bundesliga gehabt, gemessen an
Zweitliga-Percentilen. Umgerechnet wird mit derselben Formel und Schwelle
wie die *eingeordnete Note* auf den Karten, sodass Karte und Kaderanalyse
dieselbe Zahl zeigen; die Umrechnung ist sichtbar („64 (80 in der
2. Bundesliga)").

| Bundesliga, Startelf | roh | umgerechnet |
|---|---|---|
| SV Elversberg | Rang 1 | Rang 7 |
| FC Bayern | Rang 2 | Rang 1 |
| FC Schalke 04 | Rang 8 | Rang 12 |

Dieselbe Grundlage gilt überall, wo ein Kader bewertet wird: im Ligavergleich
(sonst stünde Bayerns Startelf gegen den Schnitt aller Spieler der
Konkurrenz), in der Einschätzung „für diesen Verein" und im Kaderbedarf der
Team-Note.

Eine bekannte Schwäche, bewusst so belassen: Bei Rotation ist „meiste
Minuten" ein Münzwurf — in Bayerns Offensivmittelfeld liegt Karl
(1.282 Min.) vor Gnabry (1.228 Min.).

## Passung direkt in der Spielerakte

Die Passungsanalyse gab es bisher nur in eine Richtung: erst einen Verein
wählen, dann Spieler dazu suchen. Aus der Merkliste heraus ist die Frage
umgekehrt — *dieser* Spieler steht fest, gesucht ist der Verein, zu dem er
passt.

In der Akte sitzt deshalb unter den drei Noten eine Leiste **„Passung
prüfen gegen"** mit allen Vereinen und einer Formationswahl. Sobald ein
Verein gewählt ist, füllt sich die gesperrte Team-Note, und es erscheinen
die vollständige Passungsanalyse sowie die Einschätzung *für diesen
Verein*. Der gewählte Verein bleibt beim Blättern durch die Merkliste
stehen — beim Durchsehen einer Liste will man alle gegen denselben Verein
halten.

Kommt der Verein aus dem Suchweg (Vereins-Matching, Kaderanalyse), ist er
in der Akte **nicht** umzustellen: dort gehört er zur Suche. Die Leiste
sagt das dann auch.

Das **Stilprofil** (70 % der Team-Note) lässt sich weiterhin nur im
Vereins-Matching einstellen; die Leiste nennt den aktuellen Stand, damit
die Zahl nicht überinterpretiert wird.

### Ein Fehler, den das freigelegt hat

`KPOS` trägt die Kaderwerte des Bezugsvereins und wird von
`bedarfNoteFor()` gelesen — dem Kaderbedarf, 20 % der Team-Note. Gesetzt
wurde es aber **nur** von der Kaderanalyse. Das Vereins-Matching rechnete
deshalb gegen das eingebaute Demo-Array (mit Positionskürzeln wie `IV L`
und `ZM R`, die es in den echten Daten gar nicht gibt) oder — nach einem
Besuch der Kaderanalyse — gegen *deren* Verein. Gemessen: Bayern wurde
gegen den Kader von ETSV Hamburg gehalten.

`setzeKPOS()` setzt die Werte jetzt an jeder Stelle, die sie braucht,
statt sich auf einen früheren Aufruf zu verlassen.

## Merkliste

Ein Stern in jeder Spielerakte legt den Spieler in einen Ordner; über
denselben Stern lassen sich neue Ordner anlegen. Ein Spieler kann in
mehreren Ordnern liegen. Die Übersicht (Kachel 05) listet alle Ordner mit
Anzahl, öffnet sie in der gewohnten Trefferansicht und erlaubt Umbenennen
und Löschen. Beim Umbenennen auf einen vorhandenen Namen werden die Ordner
**zusammengelegt**, nicht überschrieben.

**Gespeichert wird im Browser des Betrachters** (`localStorage`). Das ist
keine Bequemlichkeit, sondern die einzige Möglichkeit: Die Seite ist
statisch, es gibt keinen Server, der etwas ablegen könnte. Also gilt — die
Ordner liegen auf *diesem* Gerät in *diesem* Browser, wandern nicht mit und
sind für niemanden sonst sichtbar. Ein privates Fenster oder gelöschte
Websitedaten bedeuten: weg. Das steht auch auf der Seite selbst, statt es
den Nutzer herausfinden zu lassen.

Spieler, die im aktuellen Datenstand nicht mehr vorkommen, werden auf der
Ordnerkarte gesondert ausgewiesen (*„2 nicht mehr im Datenstand"*) —
stillschweigend zu verschwinden wäre schlimmer als der Hinweis.

## Vertragsausläufer

Vierte Suchfunktion, eigene Seite. Sie beantwortet eine andere Frage als
die Spielersuche: nicht *wer ist gut*, sondern *wer ist bald zu haben — und
zu welchen Bedingungen*.

Quelle ist eine eigene Transfermarkt-Seite je Verein und Sommer:

```
/<verein>/vertragsende/verein/<id>?vertragsendeJahr=2027
```

Sie führt drei Dinge, die die Kaderansicht **nicht** hat:

| Angabe | Warum sie zählt |
|---|---|
| gesichertes Enddatum | Die Kaderansicht lässt es bei rund der Hälfte der Spieler offen |
| **Vertragsoption** | „beidseitig 2 Jahre“, „vereinsseitig 1 Jahr“, „Kaufoption“ — wird sie gezogen, wird der Spieler nicht frei |
| **Leihe** | Dort endet die *Leihe*, nicht der Vertrag beim Stammverein. Ein Leihende als „ablösefrei“ auszuweisen wäre schlicht falsch |

Deshalb trägt jeder Treffer ein Kennzeichen: *ablösefrei ab 07/2027*,
*Ausläufer + Option*, *Leihe bis 07/2027* — oder *Vertrag bis … · Option
unbekannt*, wenn das Datum nur aus der Kaderansicht stammt. Leihen sind
standardmäßig ausgeblendet, ein Schalter blendet zusätzlich alle Spieler
mit Verlängerungsoption aus.

### Gesucht wird in Zeitfenstern, nicht in Jahreszahlen

Ein Scout fragt nicht „endet der Vertrag 2027", sondern „wer ist im Winter
zu haben und wer im Sommer":

| Fenster | Bedeutung |
|---|---|
| **Winterpause 2026/27** | Vertrag endet im Winter — ablösefrei ab Januar 2027 |
| **Vor dem 30.06.27** | Läuft *früher* aus als zum üblichen Sommertermin: Winterausläufer und die englischen Mai-Verträge. Der 30.06. selbst zählt hier **nicht** mit — sonst wäre es schlicht „alles bis zum Sommer" |
| **Saisonende 2026/27** | ablösefrei ab Sommer 2027; ab 1. Januar ist ein **Vorvertrag** mit Vereinen anderer Verbände möglich, im Winter also die letzte Gelegenheit auf Ablöse |
| **Saison 2027/28** | ein Jahr später, jetzt noch mit Ablöse |

Das dritte Fenster ist bewusst eng: Es umfasst zwölf Spieler statt 4.225.
Der 30.06. ist der Standardtermin, gefragt sind hier die Ausnahmen davon.

Die Grenzen liegen bei **Ende August**, nicht am Jahreswechsel: englische
Verträge enden am 31.05., deutsche am 30.06., manche am 31.12. — erst ein
Saisonschnitt fasst sie richtig zusammen.

Wer es genauer will, wählt **einzelne Stichtage** an: eine Liste aller
Termine, die in den Daten tatsächlich vorkommen (21 Stück), jeder mit
seiner Trefferzahl. So lassen sich auch Termine aus *verschiedenen*
Fenstern kombinieren — etwa der 31.12.2026 und der 30.06.2027. Eine solche
Auswahl **ersetzt** das Zeitfenster, statt sich mit ihm zu verrechnen: wer
den 31.12. anklickt, während oben „Saisonende" steht, bekäme sonst null
Treffer und keinen Hinweis, warum. Das Fenster wird dabei sichtbar
gesperrt, *Zurück zum Zeitfenster* hebt es wieder auf.

Die Winterfälle kommen aus einer anderen Quelle als die Sommerfälle: Die
Vertragsende-Seite beginnt beim **nächsten** Sommer, `vertragsendeJahr=2026`
liefert nichts mehr. Enden zum 31.12.2026 stehen daher nur in der
Kaderansicht — ohne Angabe zur Option, und genau so gekennzeichnet.

Wer seinen Verein verlassen hat, erscheint hier nicht: sein Vertragsdatum
stammt vom alten Verein und sagt heute nichts mehr.

**Ein Abruf je Verein und Sommer** — rund 1.200 statt 17.000, wie es der
Weg über die Spielerprofile wäre:

```bash
python3 scripts/build_players.py --kader-aktuell   # vorher: wer steht noch im Kader?
python3 scripts/vertraege.py                       # kommender + folgender Sommer
python3 scripts/vertraege.py --jahre 2027          # nur der kommende
python3 scripts/vertraege.py --ligen buli,buli2
python3 scripts/compute_grades.py                  # danach immer
```

Die Reihenfolge ist keine Förmlichkeit: Wer den Verein verlassen hat, steht
auf dessen Vertragsende-Seite nicht mehr — sein Fehlen sagt dann nichts über
seinen Vertrag. Erst `--kader-aktuell` trennt beides. Fehlt dieser Schritt
für eine Liga, schreibt `vertraege.py` dort **nur die gefundenen Ausläufer**
und verzichtet auf den Vermerk „Vertrag läuft länger" — und sagt das beim
Lauf auch. `update_local.sh` erledigt beides in der richtigen Folge.

Das Jahr ist nicht fest verdrahtet: `kommender_sommer()` leitet es aus dem
Datum ab (ab Juli zählt der Sommer des Folgejahres), und die Auswahl im
Frontend kommt aus den Daten selbst.

**Was nicht geprüft wurde, wird nicht behauptet.** Jeder geprüfte
Kaderspieler trägt den Vermerk, welche Sommer nachgesehen wurden. Nur damit
lässt sich *„Vertrag läuft länger“* von *„nicht nachgesehen“* trennen —
ohne diese Unterscheidung wäre die Suche eine Behauptung statt einer
Auskunft. Spieler, die ihren Verein verlassen haben, bekommen den Vermerk
bewusst nicht: sie stehen auf der Vereinsseite gar nicht mehr, ihr Fehlen
sagt also nichts über ihren Vertrag.

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

### Drei Fallen, die Daten gekostet haben

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

**Ein Volllauf löschte alles später Hinzugekommene.** `sammle()` baut jeden
Datensatz neu auf und kennt nur die Felder der Kader- und Leistungsseite.
Bei einem Teillauf fällt das nicht auf, weil die übrigen Ligen unangetastet
bleiben — ein Lauf über *alle* Ligen dagegen warf Verletzungshistorie,
Vertragsdaten und xG weg, allein die Verletzungen rund zehn Stunden Abrufe.
`build_players.py` trägt sie jetzt über die Spieler-ID zurück; für bereits
entstandene Lücken gibt es `scripts/rette_bestand.py <sicherung.json.gz>`.
Dieselbe Falle steckte in `merge_raw.py`, dem Zusammenführungsschritt der
GitHub-Action: Er schrieb nur vier Schlüssel und hätte zusätzlich die
Bildadresse und die Vereinslisten der laufenden Saison verloren. Er rettet
jetzt dasselbe wie `build_players.py`.

**Und ein Merksatz dazu:** Ein laufendes Shell-Skript nicht bearbeiten.
Bash liest Skripte über einen Byte-Offset nach; werden Zeilen davor
eingefügt, setzt es an verschobener Stelle fort. Aufgetreten als
`./scripts/update_local.sh: line 47: ld_players.py: command not found` —
das Sammeln war durch, alle Schritte danach fielen aus.

## Hinweis

Reines Informationswerkzeug. Die Daten stammen aus öffentlich zugänglichen
Quellen und werden ohne Gewähr dargestellt.
