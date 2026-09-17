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
| **erhoben** | [Sofascore](https://www.sofascore.com) | über fünfzig Zählwerte: Zweikämpfe, Tacklings, Interceptions, Klärungen, Passquote, lange Bälle, Flanken, Schlüsselpässe, Großchancen, xG/xA, Schüsse, Dribblings, Ballkontakte, Paraden, verhinderte Tore, Fouls *(16 Ligen bis zur 3. Liga; nachgerechnet gegen FotMob/Opta)* |
| **erhoben** | Transfermarkt · Bilder | Spielerfoto, Vereinswappen *(per Verweis, nicht gespeichert)* |
| **berechnet** | dieses Werkzeug | Liga-Note, Positions-Note, Team-Note, Percentile, Liganiveau, Unterbewertet-Index |
| **fehlt** | — | Zweikämpfe unterhalb der 3. Liga, Klärungen, Passquote, Laufleistung, Gewicht |

Die Trennung ist wichtig: Eine **erhobene** Körpergröße und eine
**berechnete** Note sind zweierlei — und was gar nicht vorliegt, gehört
ebenso benannt wie das Vorhandene.

## Spielersuche auf einer Seite

Filter und Treffer stehen seit dem 17.09.2026 auf **einer** Seite: links die
Filter, rechts die Treffer, die sich bei jeder Änderung sofort neu ordnen —
ohne „Suche starten" und ohne Seitenwechsel. Vorher lagen Filter und Treffer
auf zwei Seiten, und die rechte Hälfte der Filterseite blieb leer.

- **Trefferzahl live**, mit einer Zeile, was gerade gefiltert und wie
  sortiert ist.
- **Seltene Filter eingeklappt** (Marktwert, Zweikampfquote, Mindestnote,
  Vertrag, Schalter). Daneben steht, wie viele davon gerade wirken — auch
  der voreingestellte „Nur belastbare Stichprobe" zählt mit, er wirkt ja.
- **Karten oder Tabelle.** Die Tabelle zeigt Foto, Name, Position, Verein
  mit Wappen und Liga, Alter, umgerechnete Note, Liga-Note, Marktwert,
  Vertragsende und Minuten; die Köpfe mit Sortierung sind anklickbar.
- **Stückweise geladen**, je 60 Treffer; die nächste Portion kommt, sobald
  das Listenende in Sicht ist. „Alle Stürmer" waren 1.624 Karten, ganz ohne
  Filter über 12.000 — alle auf einmal machte die Seite träge.
- **Zurück aus der Akte** führt an dieselbe Stelle der Liste, samt
  nachgeladener Portionen — sofern sich an den Filtern nichts geändert hat.
- **Namenssuche ohne Akzente und Umlaute:** „mueller", „muller" und „Müller"
  finden dieselben Spieler, „oyarzabal" auch „Oyarzábal".

### Sortiert nach umgerechneter Note

Nach Liga-Note über mehrere Ligen hinweg sortiert stand Pascal Testroet
(Regionalliga Südwest, 35 Jahre, Note 91) zwischen Haaland und Kane — ein
Percentil gilt aber nur in seiner Liga. Voreingestellt ist deshalb die
**umgerechnete Note**: dieselbe Umrechnung wie in der Kaderanalyse, je
Niveaupunkt Abstand 0,55 Notenpunkte.

- **Bezug** ist die stärkste Liga unter den Treffern — so wird nur nach unten
  umgerechnet, und bei Treffern aus einer einzigen Liga ändert sich nichts.
  Ist genau eine Liga gewählt, gilt deren Niveau.
- **Sortiert** wird ohne Rundung und ohne die Kappung auf 1 bis 99, damit die
  Reihenfolge stetig bleibt; angezeigt wird der gerundete Wert. Die
  Reihenfolge hängt nicht vom Bezug ab — jede Note verschiebt sich um
  denselben Betrag.
- Die **Liga-Note bleibt sichtbar**, auf der Karte neben der umgerechneten,
  in der Tabelle als eigene Spalte. Das Fenster über der Zahl rechnet vor,
  wie sie entsteht.

| Stürmer, alle Ligen | Liga-Note | umgerechnet | Platz vorher | Platz jetzt |
|---|---|---|---|---|
| Erling Haaland (Premier League) | 93 | 93 | 2 | 1 |
| Harry Kane (Bundesliga) | 93 | 85 | 3 | 2 |
| Pascal Testroet (Regionalliga Südwest) | 91 | 47 | 4 | 204 |

**Geprüft, dass die übrigen Listen unverändert sind:** Vereins-Matching
(960 und 17.721 Treffer), Kandidaten der Kaderanalyse (770), Vertragsausläufer
(24 und 4.427) und Merkliste (250) zeigen nach dem Laden aller Portionen
zeichengleich dieselben Karten wie vorher.

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
mehreren gewählten Ligen gibt es keins — dann bleibt die Einordnung auf der
Ergebnisseite weg, statt sich eine der Ligen willkürlich herauszugreifen. Die
Spielersuche sortiert seit dem 17.09.2026 trotzdem vergleichbar: dort gilt die
stärkste Liga unter den Treffern als Bezug (siehe *Sortiert nach umgerechneter
Note*).

## Spielerfotos

In der Spielerakte, der Kaderansicht und — seit dem 14.09.2026 — auch in den
Trefferlisten steht statt der Initialen das Portrait von Transfermarkt.
Anfangs gab es das Portrait bewusst nur in der Akte, aus Rücksicht auf die
Quelle: In einer Ergebnisliste wären es viele Bilder von fremden Servern auf
einmal. Warum die Trefferlisten es heute trotzdem zeigen können, ohne die
Quelle zu belasten, steht unten unter *Fotos und Wappen auch in den
Trefferlisten*.

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

### Warum die Oberligen so wenige Fotos haben

Die Fotoquote liegt in den Oberligen bei 15 bis 58 %, in den übrigen Ligen
deutlich höher. Die naheliegende Vermutung — der Sammler hat dort Lücken —
stimmt nur zu einem kleinen Teil. Nachgezählt am 14.09.2026:

| Verein | Kaderspieler im Bestand | Foto vorher | Foto jetzt | Portraits bei Transfermarkt |
|---|---:|---:|---:|---:|
| Holstein Kiel II | 24 | 17 | 23 | 23 |
| Heider SV | 24 | 8 | 8 | 8 |

Bei Holstein Kiel II fehlten bei uns 6 Fotos; inzwischen sind alle da. Bei
Heider SV fehlte nichts — Transfermarkt führt für 16 der 24 Spieler kein
Portrait.

Über alle 318 Vereine mit niedriger Quote dasselbe Bild. Der Sammler fand
3.638 Portraits: **3.345 waren schon vorhanden**, 291 kamen neu dazu (289
Spieler bekamen erstmals ein Foto, 2 ein neues), 2 gehören Spielern, die
nicht im Bestand stehen. Die Quote stieg von 66,0 auf 67,7 % der 17.170
Spieler in heutigen Kadern. **Die Lücke liegt ganz überwiegend an der Quelle** — für die
meisten Amateurspieler gibt es bei Transfermarkt kein Foto.

Eine erste Fassung dieses Abschnitts behauptete das Gegenteil. Sie hatte die
23 Portraits von Holstein Kiel II mit der Quote der ganzen Liga verglichen,
statt die Fotos genau dieses Vereins in unseren Daten nachzuzählen.

Zwei Schwächen im Sammler gab es trotzdem, und sie sind behoben:

* Die Vereine wurden in fester Reihenfolge abgerufen. Brach ein Lauf ab
  (Zeitbudget, HTTP 405), traf es jedes Mal dieselben Ligen am Ende der
  Liste. Jetzt kommen die Vereine mit der **niedrigsten Fotoquote zuerst**.
* Ohne `--erneuern` galt ein Verein als erledigt, sobald **ein** Spieler
  ein Bild trug. Jetzt wird jeder vollständig gesehene Verein vermerkt
  (`bilder_geprueft`); offen bleiben nur Vereine, die noch nie vollständig
  gesehen wurden und unter 80 % liegen.

Dazu bricht der Sammler nach vier Fehlern in Folge ab und speichert, was er
bis dahin hat — wie der Stammvertrags-Sammler.

### Fotos und Wappen auch in den Trefferlisten

Zuerst gab es Portraits nur in der Spielerakte; die Trefferlisten zeigten
Initialen. Auf Wunsch zeigen jetzt auch die Trefferkarten das Foto und neben
dem Vereinsnamen das Wappen, beides per Verweis direkt von Transfermarkt.

Die Trefferlisten rendern alle Karten auf einmal — bei „Alle Ausläufer" über
8.000. Die Last bleibt trotzdem klein: `loading="lazy"` lässt den Browser nur
Bilder holen, deren Karte in die Nähe des sichtbaren Bereichs kommt. Ein
Wappen lädt je Verein einmal und kommt danach aus dem Zwischenspeicher.

Wie in der Akte liegt das Foto **über** den Initialen und hat keinen
Hintergrund. Hängt ein Abruf, bleiben die Initialen sichtbar; scheitert er,
entfernt sich das Bild. Wo Transfermarkt kein Portrait führt — rund ein
Drittel der Spieler, vor allem in den Amateurligen —, stehen weiter die
Initialen.

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

Hier werden **alle Fotos** geladen. Anfangs geschah das bewusst nur hier und
in der Akte; seit dem 14.09.2026 zeigen auch die Trefferlisten Fotos — so
verzögert geladen, dass nur die Karten im sichtbaren Bereich Bilder holen
(siehe *Fotos und Wappen auch in den Trefferlisten*).

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

## Spielerstatistik von Sofascore

Individuelle Werte fehlten dem Werkzeug von Anfang an — der Grund, weshalb
Innenverteidiger nur über Mannschaftswerte zu bewerten waren und die
Torwartnote keine einzige eigene Kennzahl enthielt. Die Suche nach einer
freien Quelle, 2026 erneut geprüft:

| Quelle | Ergebnis |
|---|---|
| OneFootball | führt keine individuellen Zweikampfwerte |
| FBref, kicker | sperren automatisierte Abrufe (403), auch mit Browser |
| FotMob | 66 Kennzahlen je Liga, aber **je Kennzahl ein eigener Abruf**, keine Zweikämpfe auf Ligaebene und unvollständige Listen |
| **Sofascore** | antwortet, sobald die Anfrage die Kopfzeilen der eigenen Seite trägt — und liefert **82 Felder gesammelt je Liga** |

Ein Abruf bringt 100 Spieler einer Liga mit allen Feldern zugleich — rund
fünf Abrufe je Liga statt eines je Spieler **und Kennzahl**:

```bash
python3 scripts/sofascore.py              # alle abgedeckten Ligen, Saison wie die Noten
python3 scripts/gegenprobe.py             # gegen FotMob nachrechnen
python3 scripts/compute_grades.py
```

### Von zehn auf über fünfzig Kennzahlen

Anfangs wurden zehn Felder angefragt. Dass derselbe Abruf 82 beantwortet,
fiel erst beim Nachsehen auf — die Erweiterung kostete also **keinen
einzigen zusätzlichen Abruf**. Dazugekommen sind:

| Bereich | Kennzahlen |
|---|---|
| Passspiel | Passquote, angekommene Pässe, Pässe im letzten Drittel, lange Bälle, Flanken |
| Chancen | Schlüsselpässe, herausgespielte und vergebene Großchancen, xA |
| Abschluss | xG, Schüsse, Schüsse aufs Tor, Abschlussquote, Tore über xG |
| Defensivaktionen | Klärungen, geblockte Schüsse, ausgespielt worden, Ballgewinne im Angriffsdrittel, Fehler zum Gegentor |
| Ballbesitz | Dribblings, Dribbelquote, Ballkontakte, Ballverluste je 100 Kontakte |
| Torwart | Paraden, **verhinderte Tore**, Zu-Null-Anteil, hohe Bälle, Herauslaufen, gehaltene Elfmeter |

Am meisten ändert das für **Torhüter**: deren Note bestand bis dahin
ausschließlich aus Mannschaftsgegentoren und Verfügbarkeit. Und **xG
liegt jetzt für 13 statt 5 Ligen vor** — Understat deckt nur die fünf
großen ersten Ligen ab, Sofascore alle außer 3. Liga, LaLiga 2 und
Ligue 2.

Gespeichert werden **rohe Saisonsummen**, nicht Werte je 90 Minuten: die
Umrechnung gehört in `compute_grades.py`, damit sich die Darstellung
ändern lässt, ohne neu zu erheben — und damit der Rohwert nachprüfbar
bleibt.

### Kennzahlenblöcke in der Akte

In der Spielerakte stehen sie nach Themen geordnet, zweispaltig, mit
**Rohwert *und* Percentil nebeneinander**. Ein Percentil allein verbirgt,
worauf es beruht: 90 aus 2,1 Tacklings je 90 Minuten ist etwas anderes als
90 aus 0,4.

Welche Blöcke ein Spieler bekommt, hängt von seiner Position ab — und in
welcher Reihenfolge. Ein Torwart mit „Tore / 90: 0,00" wäre kein Befund,
sondern Füllmaterial; ein Innenverteidiger braucht die Zweikämpfe zuerst,
ein Stürmer den Abschluss. Was nicht gezeigt wird, wird auch **nicht
gespeichert** und kann so kein Percentil aus einer Gruppe erzeugen, in der
die Kennzahl nichts bedeutet.

**Graue Balken sind Mengenangaben ohne Wertung.** 1,5 Paraden je 90
Minuten heißen nicht, dass ein Torwart schlechter hält, sondern dass seine
Abwehr weniger zulässt — Neuer steht damit auf Percentil 2 von 23
Bundesliga-Torhütern, während seine *verhinderten Tore* bei 46 liegen.
Dasselbe gilt für Gegentore und Ballkontakte.

**Eigene Datei, nachgeladen.** `data/metriken.json` ist 2,8 MB (631 KB
komprimiert) und wird nur gebraucht, wenn jemand eine Akte öffnet. Beim
Seitenaufruf bleibt es bei `data/players.json`; die Kennzahlen kommen
beim ersten Profil nach. Die **Percentile rechnet das Frontend**, nicht
das Skript — es kennt die Vergleichsgruppe ohnehin, und so steht jede
Zahl nur einmal in der Datei statt zweimal.

**Ein Teil dieser Werte geht seit dem 13.09.2026 in die Note ein** — nach
ausdrücklicher Freigabe, siehe *Erweiterter Notensatz*. Welche Zeile
zählt, steht an der Zeile selbst.

### Erklärfenster

Jede Kennzahl erklärt sich selbst. Wer mit dem Zeiger über eine Zeile fährt
(oder sie mit der Tabulatortaste ansteuert), bekommt ein Fenster mit:

| Zeile | Inhalt |
|---|---|
| Definition | was die Kennzahl misst |
| Rechnung | je 90 Minuten, Anteil in Prozent mit Mindestbasis, oder Saisonsumme |
| Lesart | höher oder niedriger besser — oder Mengenangabe ohne Wertung |
| Vergleich | wie viele Spieler welcher Gruppe und Liga das Percentil bilden |
| Note | ob die Kennzahl in die Liga-Note eingeht |
| Quelle | Anbieter und Saison |

Das gilt für die Kennzahlenblöcke, den Direktvergleich, die Notenparameter
im Stärkenprofil und die Rollenprofile — dort mit den Kennzahlen, aus denen
die Rolle besteht, ihrem Gewicht und dem Percentil des Spielers.

**Gepflegt wird nur die Definition**, in `compute_grades.py` neben der
Rechnung. Rechnung, Mindestbasis, Lesart und Notenzugehörigkeit setzt das
Fenster aus den Angaben zusammen, nach denen ohnehin gerechnet wird. So kann
eine Erklärung der Rechnung nicht widersprechen. Eine neue Kennzahl ohne
Definition bricht den Lauf ab, statt ohne Erklärung zu erscheinen.

Auf Touch-Geräten ohne Zeiger steht die Definition über der Verteilung, die
ein Tippen auf die Zeile öffnet.

Beim Schreiben der Definitionen fiel ein ungenauer Name auf. Sofascore führt
das Feld als „accurate final third passes"; die Kennzahl hieß „Pässe ins
letzte Drittel" und heißt jetzt „Pässe im letzten Drittel". Nur die
Beschriftung ändert sich, nicht der Wert.

### Rollenprofile, Direktvergleich und Verteilung

Drei Ansichten, die aus denselben Kennzahlen entstehen und dieselbe
Vergleichsgruppe benutzen wie die Note (Liga der Note, Positionsgruppe,
ab 450 Minuten).

**Rollenprofil.** Die Note sagt, *wie gut* jemand ist — nicht, *was für
einer*. Ein Innenverteidiger, der aufbaut, ist etwas anderes als einer,
der Kopfbälle gewinnt, auch wenn beide 70 haben. Drei bis vier Rollen je
Positionsgruppe, jede eine gewichtete Auswahl aus den vorhandenen
Kennzahlen; die Übereinstimmung ist der gewichtete Mittelwert der
Percentile darin — dieselbe Rechnung wie bei der Note, nur mit anderer
Auswahl.

| Spieler | Rollenprofil |
|---|---|
| Jonathan Tah | Aufbauverteidiger **88 %**, Luftherrscher 68 %, Zweikampfverteidiger **28 %** |
| Joshua Kimmich | Kreativspieler **98 %**, Aufbau-Sechser 94 %, Balleroberer **42 %** |
| Manuel Neuer | Mitspielender Torwart **59 %**, Strafraum-Torhüter **35 %** |
| Harry Kane | Strafraumstürmer **97 %**, Mitspielender Stürmer 89 % |

**Was das nicht ist:** eine Aussage darüber, wie ein Spieler *eingesetzt*
wird. Dafür bräuchte es Positions- und Laufdaten, die kein freier
Anbieter herausgibt. 88 % bei „Aufbauverteidiger" heißt: seine Zahlen
sehen aus wie die eines Aufbauverteidigers. Ob sein Trainer ihn so
spielen lässt, steht hier nicht.

**Direktvergleich.** Zwei Spieler Zeile für Zeile, die Balken
gegeneinander laufend, Rohwert und Percentil an beiden Enden. Der
senkrechte Strich in den Balken ist der **Median der Vergleichsgruppe** —
ohne ihn sagt ein längerer Balken nur „mehr als der andere", nicht „viel
für diese Position". Verschiedene Ligen oder Positionsgruppen werden
benannt statt verschwiegen: die Rohwerte sind unmittelbar vergleichbar,
die Percentile nicht. Diese Tabelle ist seit dem 16.09.2026 die zweite
Ansicht; zuerst stehen die Diagramme (siehe *Detaillierte Darstellung*).

**Verteilung (Beeswarm).** Ein Klick auf eine Kennzahlzeile zeigt die
ganze Liga als Punktwolke, ein Punkt je Spieler, mit dem Betrachteten in
Grün und dem Vergleichsspieler in Blau. Ein Percentil sagt, *wie viele*
schlechter sind — nicht *wie viel* besser. Percentil 80 kann ein
deutlicher Vorsprung sein oder ein Wimpernschlag, je nachdem wie eng das
Feld liegt. Beispiel: Tahs 5,51 Klärungen je 90 ergeben Percentil 40, der
Median liegt bei 5,47 und das Feld reicht von 2,59 bis 10,56 — der
Percentilwert verbirgt, wie dicht es dort zugeht.

**Radar.** Der Ring bei 50 ist als Ligaschnitt gekennzeichnet (bei
Percentilen ist 50 per Definition der Schnitt) und trägt bei einem
Direktvergleich die zweite Kurve.

### Detaillierte Darstellung und Diagramm-Vergleich

Dieselben Zahlen in einer zweiten Darstellung, nach dem Vorbild der
Auswertungen großer Scouting-Werkzeuge: Percentil-Balken je Themenblock und
Polardiagramme, in denen jedes Kreisstück eine Kennzahl ist. **Nichts davon
ist eine neue Bewertung.** Die Länge ist immer das Percentil oder die
Teilnote, die auch in der Übersicht steht.

**Für einen einzelnen Spieler nur auf Klick.** Die Abschnitte *Kennzahlen*,
*Woraus die Note entsteht* und *Stärkenprofil* tragen im Kopf den Umschalter
„Übersicht | Detailliert". Voreingestellt ist die Übersicht. Ein Klick
schaltet alle drei zugleich um — es ist eine Darstellungsweise, kein
Schalter je Kasten — und bleibt beim Durchsehen weiterer Akten stehen, bis
man zurückschaltet.

| Abschnitt | Übersicht | Detailliert |
|---|---|---|
| Kennzahlen | Zeile mit Rohwert, kleinem Balken, Percentil | Percentil-Balken je Themenblock, Zahl im Balken, Rohwert unter dem Namen, Achse 0 bis 100 |
| Woraus die Note entsteht | Balken je Bereich | Kreis, ein Stück je Bereich der Liga-Note |
| Stärkenprofil | Radar und Balken | Kreis statt Radar, daneben die Balken |

**Im Direktvergleich sind die Diagramme die erste Ansicht**, die Tabelle ist
einen Klick entfernt („Diagramme | Tabelle"). Zuerst die Bereiche der
Liga-Note, der erste Spieler als Fläche und der zweite gestrichelt umrissen;
dann je Themenblock ein Kreis mit beiden Spielern übereinander — vorn der
kürzere Teil, dahinter ragt der längere hinaus. In den Kästchen steht der
Rohwert. Das Erklärfenster über einem Kreisstück nennt beide Werte mit ihrem
Percentil in der jeweils eigenen Liga.

**Farbstufen.** Grün, Oliv und Rot wie in den Vorlagen, aber mit den
Schwellen des Stärkenprofils: ab 70, 40 bis 69, unter 40. Die Vorlagen
färben erst ab 80 grün; das wäre eine andere Einstufung und ist nicht
übernommen. Graue Balken bleiben Mengenangaben ohne Wertung. In den
Vergleichskreisen fehlen sie ganz, weil ein Kreisstück ein Besser oder
Schlechter behauptet, das es dort nicht gibt — die Tabelle führt sie weiter.
Ein Themenblock mit weniger als drei wertbaren Kennzahlen bekommt keinen
Kreis und wird darunter genannt.

**Geprüft, bevor es live ging:**

- **Die Übersicht ist unverändert.** Für neun Akten — mit und ohne
  Vergleich, mit und ohne Einzelkennzahlen, von Kane und Kobel über die
  2. und 3. Liga bis zu einer Note aus der Regionalliga West, dazu La Liga
  gegen die belgische Liga — ist das Ergebnis zeichengleich mit dem Stand
  davor, abgesehen vom Umschalter selbst.
- **Nichts überdeckt sich.** Je 1.153 Kreise aus zufälligen Spielerpaaren
  am Desktop und auf Handybreite: kein Kästchen auf einem anderen, keines
  auf einem Namen, kein Name auf einem anderen. Dafür werden lange Wörter an
  der Wortfuge getrennt („Defensiv-aktionen"), sich berührende Kästchen um
  das kleinstmögliche Stück auseinandergeschoben, und ein Name, der nicht
  passt, wird stufenweise kleiner, nie unter 72 %.
- Auf dem Handy zeichnet die Seite die Kreise mit größerer Schrift; im
  verkleinerten Kreis wäre die Desktop-Schrift nicht lesbar.

### Gegenprobe gegen FotMob (Opta)

Sofascore ist als Quelle umstritten. Der Vorwurf trifft zwei verschiedene
Dinge, die auseinandergehalten gehören:

* Die **Sofascore-Note** (6,0–10,0) ist eine eigene Rechenvorschrift, die
  der Anbieter nicht offenlegt. Sie wird hier **nicht verwendet**.
* Die **Zählwerte** stammen aus derselben Erfassung wie bei den großen
  Anbietern. Ob das stimmt, lässt sich prüfen statt glauben.

`scripts/gegenprobe.py` vergleicht dieselben Spieler derselben Saison mit
FotMob, dessen Ligastatistik offen als JSON liegt und von **Opta** stammt.
Bundesliga, Premier League und Serie A, 9.921 Wertepaare, nur Spieler ab
450 Minuten:

| Kennzahl | Grundlage | Spieler | r | Ø-Abw. | einig |
|---|---|---:|---:|---:|---:|
| Tore | Saisonsumme | 753 | 1,0000 | 0,00 % | **100 %** |
| Vorlagen | Saisonsumme | 725 | 1,0000 | 0,00 % | **100 %** |
| Großchancen kreiert | Saisonsumme | 856 | 1,0000 | 0,00 % | **100 %** |
| xG | Saisonsumme | 1.051 | 0,9999 | 0,96 % | 99,6 % |
| Klärungen | je 90 Min. | 916 | 0,9998 | 1,37 % | 96,5 % |
| angekommene Pässe | je 90 Min. | 920 | 0,9998 | 0,55 % | 83,4 % |
| Tacklings | je 90 Min. | 890 | 0,9989 | 2,01 % | 94,8 % |
| Paraden | je 90 Min. | 57 | 0,9988 | 0,77 % | 100 % |
| gewonnene Dribblings | je 90 Min. | 867 | 0,9987 | 3,83 % | 98,2 % |
| Fouls | je 90 Min. | 881 | 0,9979 | 2,47 % | 96,8 % |
| Interceptions | je 90 Min. | 869 | 0,9978 | 3,48 % | 99,0 % |
| Einsatzminuten | Saisonsumme | 1.136 | 0,9999 | 0,37 % | 78,1 % |

Tore, Vorlagen und Großchancen stimmen bei **jedem einzelnen Spieler**
überein. Die verbleibenden Abweichungen sind zu einem großen Teil
Rundung: FotMob veröffentlicht Werte je 90 Minuten auf **eine**
Nachkommastelle (3,7 statt 3,7113), wir rechnen ungerundet. Der Rest sind
leicht abweichende Einsatzminuten — im Mittel 6,4 Minuten über eine ganze
Saison.

Zwei Fallen, die der erste Durchlauf zeigte und die der zweite behebt:

* **Ohne Mindestspielzeit** entstanden Ausreißer von 13,5 „Vorlagen je
  90". Dahinter stand ein Spieler mit *einer* Vorlage in 10 Minuten
  (Sofascore) beziehungsweise 4 Minuten (FotMob) — das sagt nichts über
  Datenqualität, sondern etwas über Division. Seitdem: ab 450 Minuten.
* **Summen gegen Durchschnitte** zu vergleichen macht jede Korrelation
  wertlos. FotMob liefert je nach Kennzahl beides; der Titel der Liste
  („Tackles per 90" gegen „Top scorer") entscheidet, und das Skript liest
  ihn aus.

Das Ergebnis steht in der **Datenherkunft jeder Spielerakte** — damit ist
es nachlesbar und nicht bloß eine Zusage. Es läuft bei jedem
`update_local.sh` mit (rund 40 Abrufe); `GEGENPROBE=0` schaltet es ab.

**Warum dann nicht gleich FotMob als Quelle?** Zwei Gründe, beide
gemessen: je Kennzahl ein eigener Abruf statt aller in einem — und die
Listen sind unvollständig. Bei den Tacklings standen 286 Spieler, obwohl
385 die Mindestspielzeit erreichten; Torhüter mit 3.060 Minuten fehlten,
während andere geführt wurden. Für Percentile wäre das gefährlich, für
eine Gegenprobe ist es unerheblich: verglichen wird nur, wer in beiden
Listen steht.

### Zweikampfquoten

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

### Aufstellung

Ganz oben in der Kaderanalyse steht diese Startelf auf dem Platz, im 4-2-3-1,
daneben die **Tiefe je Position** mit Startelf und Ersatz, nach Ligaminuten
sortiert. Jeder Spieler — auf dem Platz wie in der Liste — öffnet mit Klick
seine Akte; deren Zurück führt wieder zur Kaderanalyse.

- **Am Spieler:** Foto, Rückennummer, Liga-Note (auf das Niveau der Liga des
  Vereins umgerechnet, wie überall in der Kaderanalyse), Nachname, Zeichen für
  Leihe und für einen Vertrag, der in zwölf Monaten oder früher endet.
- **Der Ring** ist der Rang seiner Position unter den Vereinen der Liga —
  dieselbe Zahl und dieselben Stufen wie in den Balken darunter (obere
  Ligahälfte, Mittelfeld, unteres Drittel). Farbe steht nie allein: unter
  jedem Spieler steht der Rang als Text, etwa „IV · 4./18".
- **Das Erklärfenster** nennt Position, Note mit Herkunft, Spielzeit, Rang und
  Vertrag.

**Lücken.** Die Startelf zählt streng je Position — ein Kader mit drei ZM und
keinem DM hat keinen DM. Gemessen traf das 416 von 629 Vereinen. Für das
*Bild* rückt deshalb der meistgespielte Ersatz einer verwandten Position nach
(etwa ZM auf DM), gestrichelt umrandet und als „ZM → DM" beschriftet: 574
Plätze werden so besetzt. Wo auch das nicht geht — meist bei Vereinen mit zu
wenigen bewerteten Spielern —, bleibt „unbesetzt" stehen (483 Plätze). Die
Analyse selbst, also Ränge, Balken und Empfehlungen, rechnet weiter streng je
Position.

**Geprüft für alle 629 Vereine**, am Desktop und auf Handybreiten von 240 bis
460 Pixel: keine Überlappung zwischen Spielern, nichts ragt über den Platz.
Auf dem Handy stehen die Reihen geschlossen, und der Platz ist 120 statt
105 Meter lang — die höchste nach den Regeln zulässige Länge —, damit fünf
Reihen mit lesbaren Namen untereinander passen. Die Markierungen sind in
Metern nach den Spielregeln gezeichnet, Kreise bleiben also rund. Die
Statusringe halten auf dem Rasen mindestens 3,3:1 Kontrast, die Beschriftung
4,5:1.

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

Das **Stilprofil** gewichtet den Stil, der seit dem 17.09.2026 45 % der
Team-Note ausmacht (siehe *Vereins-Matching: Passung aus Kennzahlen*). Wird
in der Akte ein Verein gewählt, gilt dessen aus der Startelf abgeleiteter
Stil; im Vereins-Matching eingestellte Werte gelten für denselben Verein. Die
Leiste nennt Stand und Herkunft, damit die Zahl nicht überinterpretiert wird.

### Ein Fehler, den das freigelegt hat

`KPOS` trägt die Kaderwerte des Bezugsvereins und wird von
`bedarfNoteFor()` gelesen — dem Kaderbedarf (damals 20 %, heute 15 % der Team-Note). Gesetzt
wurde es aber **nur** von der Kaderanalyse. Das Vereins-Matching rechnete
deshalb gegen das eingebaute Demo-Array (mit Positionskürzeln wie `IV L`
und `ZM R`, die es in den echten Daten gar nicht gibt) oder — nach einem
Besuch der Kaderanalyse — gegen *deren* Verein. Gemessen: Bayern wurde
gegen den Kader von ETSV Hamburg gehalten.

`setzeKPOS()` setzt die Werte jetzt an jeder Stelle, die sie braucht,
statt sich auf einen früheren Aufruf zu verlassen.

## Vereins-Matching: Passung aus Kennzahlen (freigegeben am 17.09.2026)

Die Passung unterschied Spieler kaum. Vier der fünf Stil-Dimensionen hatten
keine Daten — das Modell stammte aus der Zeit vor den Sofascore-Kennzahlen —,
und neutral bei 50 angesetzte Lücken machen alle gleich. Bei
Kaiserslautern lagen die ersten fünf Innenverteidiger gleichauf bei 74,
darunter einer mit 187 Minuten.

**Stil aus Kennzahlen.** Jede Dimension ist ein gewichtetes Mittel aus
Percentilen (je Liga der Note und Positionsgruppe, wie in den
Kennzahlenblöcken); jede Kennzahl steht in genau einer Dimension, sonst
messen zwei Dimensionen dasselbe:

| Dimension | Kennzahlen (Gewicht) |
|---|---|
| Pressing | Ballgewinne im Angriffsdrittel / 90 (2), Tacklings / 90 (1) |
| Ballbesitz | Passquote (2), Ballverluste je 100 Kontakte (1) |
| Konter | Dribblings gewonnen / 90 (2), lange Bälle angekommen / 90 (1) |
| Aufbau | Pässe im letzten Drittel / 90 (2), Pässe angekommen / 90 (1) |
| Standards | Kopfballduelle (1), Kopfbälle gewonnen / 90 (1), Flanken angekommen / 90 (1) |

Gemessen an allen Spielern ab 450 Minuten mit Sofascore-Kennzahlen, bei
neutralem Stilprofil (Stilanteil der Team-Note):

| Gruppe | verschiedene Werte | Streuung | Datenlücken je Spieler |
|---|---|---|---|
| Innenverteidiger | 17 → 69 | 5,4 → 12,3 | 4 → 0 |
| Außenverteidiger | 20 → 67 | 5,7 → 12,6 | 4 → 0 |
| Zentrales Mittelfeld | 19 → 65 | 5,7 → 12,4 | 4 → 0 |
| Offensive | 38 → 70 | 8,6 → 13,2 | 3 → 0 |
| Stürmer | 39 → 69 | 8,4 → 13,8 | 3 → 0 |
| Torhüter | 21 → 44 | 5,2 → 9,3 | 4,2 → 2 |

Torhüter haben weiter zwei Lücken: Pressing und Standards führt Sofascore für
sie nicht.

**Der Stil des Vereins** wird aus seiner Startelf abgeleitet: je Dimension
das Mittel der Spieler, dann der Rang unter den Vereinen der Liga, in fünf
gleich große Stufen geteilt (1 am schwächsten, 5 am stärksten ausgeprägt).
Ein Stil ist also immer relativ zur eigenen Liga. Die Regler im Matching
sind damit vorbelegt und bleiben verstellbar. Beispiele Bundesliga: Union
Berlin Ballbesitz 1 und Standards 4, Bayern und Leverkusen Ballbesitz 5.
Nicht alles überzeugt — Mainz landet beim Pressing auf 1; der Stil aus Zahlen
ist ein Vorschlag, kein Befund über den Trainer.

**Stil allein genügt nicht.** Reiner Stil ignoriert die Qualität: beim
Stürmer hing der Stilwert überhaupt nicht mit der Liga-Note zusammen
(Korrelation 0,01), und für Union Berlin stand ein Stürmer mit Liga-Note 14
unter den ersten fünf. Freigegeben ist deshalb die Mischung:

| Teil der Team-Note | vorher | jetzt |
|---|---|---|
| Stil | 70 % | 45 % |
| Leistung (Liga-Note) | — | 30 % |
| Kaderbedarf | 20 % | 15 % |
| Formation | 10 % | 10 % |

Top 20 der Stürmer für Kaiserslautern mit der Mischung statt reinem Stil:
Liga-Note im Schnitt 75 statt 50, der schwächste 59 statt 19.

**Nur ab 450 Minuten, nur erreichbar.** Das Matching zeigt nur noch Spieler
mit belastbarer Spielzeit. Ist kein Budget eingetragen, gilt dieselbe
Grenze wie bei den Kandidaten der Kaderanalyse: das Anderthalbfache des
teuersten eigenen Spielers, sofern genug Marktwerte vorliegen. Für Union
Berlin standen sonst Kane und Haaland oben; mit der Grenze (30 Mio. €) sind
es Waldschmidt, Krstović und Watkins.

**Ohne Sofascore-Kennzahlen** (Spieler und Vereine unterhalb der 3. Liga)
rechnet der Stil wie bisher über die Notenparameter, mit Datenlücken, die auf
der Karte stehen; ein Vereinsstil lässt sich dort nicht ableiten, die Regler
stehen neutral.

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

### Ein Leihende ist kein Vertragsende

Aufgefallen an **Denis Halinsky** (FK Pardubice): das Werkzeug führte ihn
unter den Ausläufern zum 31.12.2026. Sein Transfermarkt-Profil sagt aber:

```
Vertrag bis:        31.12.2026
Ausgeliehen von:    SK Slavia Prag
Vertrag dort bis:   30.06.2030
```

Der Vertrag läuft also noch dreieinhalb Jahre — was am 31.12. endet, ist
die **Leihe**. Ursache: in der Kaderansicht steht in der Spalte „Vertrag
bis" bei einem Leihspieler das Leihende, ohne dass die Spalte anders hieße.

Die Vereinsseite „Vertragsende" kennzeichnet Leihen seit jeher (grün
hinterlegte Zeile), und dieser Weg war korrekt. Halinsky kam gar nicht
über sie — sein Leihende liegt vor dem ersten abgefragten Sommer, sein
Datum stammte aus der Kaderansicht, und die hatte keine Kennzeichnung.

**Der Marker war die ganze Zeit da**, nur ungenutzt: in der Kaderzeile
trägt die Wappen-Verlinkung ein `title`-Attribut.

```html
<a title="Leihspieler von: SK Slavia Prag; Rückkehr: 31.12.2026" …>
```

Streng davon zu trennen ist `title="Rückkehr nach Leihe von: …"` — das
kennzeichnet einen Spieler, der von einer Leihe **zurück** ist und ganz
normal unter Vertrag steht; sein Datum in der Zeile stimmt. Beide Formen
stehen in derselben Spalte, ein bloßes Suchen nach „Leihe" hätte die
Hälfte falsch einsortiert.

Seitdem:

* Wird eine Leihe erkannt, wird `vertrag_bis` **gar nicht erst gesetzt** —
  das Datum gehört der Leihe, nicht dem Vertrag.
* Der Vermerk wird bei jedem Kaderlauf neu gesetzt **oder entfernt**. Ein
  stehengebliebenes „Leihe bis 2026" hätte einen Spieler dauerhaft aus der
  Ausläufer-Suche herausgehalten, nachdem er fest verpflichtet wurde.
* In der Akte, der Kaderansicht und den Stammdaten steht bei ihm „Leihe
  bis …" statt „Vertrag bis …", dazu der Stammverein.
* In der Ausläufer-Suche erscheint er **nicht mehr** — siehe unten.

### Bei Leihspielern zählt der Vertrag beim Stammverein

Ein erster Schritt sortierte Leihspieler in einen eigenen Abschnitt
„Leihende". Das reichte nicht: Halinsky stand dann zwar nicht mehr unter
den Vertragsenden, aber weiterhin in der Trefferliste zum 31.12.2026.
Gefragt sind aber **nur Spieler, deren Vertrag ausläuft**.

Maßgeblich ist deshalb der Vertrag beim Stammverein. Transfermarkt führt ihn
an zwei Stellen: auf der Profilseite des Spielers (`Vertrag dort bis:
30.06.2030`) und auf der **Leihspieler-Seite des aufnehmenden Vereins**,
Tabelle „Leihklub", Spalten *Vertrag bis* und *Leihende*. Das Skript liest
die Vereinsseite (Begründung unten):

```bash
python3 scripts/leihvertraege.py
```

Die Regel sitzt an **einer** Stelle, `vertragsEnde()`: bei einer Leihe
liefert sie den Vertrag beim Stammverein — oder gar kein Datum. Weil
Treffer, Trefferzahlen im Auswahlfeld, Stichtage und Sortierung alle über
diese Funktion gehen, gilt die Regel überall zugleich.

| Fall | in der Suche |
|---|---|
| Leihe endet, Vertrag beim Stammverein läuft weiter (Halinsky) | **nicht angezeigt** |
| Leihe endet, Vertrag beim Stammverein endet im selben Zeitraum | Abschnitt *Leihspieler mit auslaufendem Vertrag* |
| Vertrag beim Stammverein nicht erfasst | nicht angezeigt |

Wer die Leihenden trotzdem sehen will, schaltet **„Leihenden zusätzlich
zeigen"** ein (Vorgabe: aus). Sie stehen dann in zwei eigenen Abschnitten:
*Leihende — Vertrag läuft weiter* und *Leihende — Vertrag beim Stammverein
unbekannt*. Getrennt, weil das eine eine Auskunft ist und das andere eine
offene Frage.

**Transfermarkt sperrt Profilseiten schneller** als Kader- und
Vertragsseiten. Beim ersten Lauf kamen nach rund zwanzig Abrufen nur noch
Antworten mit 403, der Lauf wurde abgebrochen, bevor er die Sperre
verlängern konnte. Seitdem pausiert das Skript zwischen den Abrufen,
bricht nach vier Fehlern in Folge ab und speichert, was es bis dahin hat —
auch bei einem Abbruch von außen. Den Rest holt der nächste Lauf; wer
schon geprüft ist, wird übersprungen, solange sich seine Leihe nicht
ändert. `update_local.sh` führt den Schritt mit (`LEIHVERTRAEGE=0`
schaltet ihn ab).

**„Nicht abgefragt" und „kein Datum" sind zwei Auskünfte.** Manche
Profilseiten führen die Zeile, aber ohne Wert — `Vertrag dort bis: -`,
etwa bei Andrés Ferrari (ausgeliehen von St. Truiden, mit Kaufoption).
Das ist kein Lesefehler, sondern der Stand bei Transfermarkt. Die Akte
unterscheidet deshalb, ob beim Stammverein kein Vertragsende geführt wird
oder ob der Spieler schlicht noch nicht abgefragt wurde.

**Der erste vollständige Lauf, 14.09.2026.** Mit Pause und Sperren-Erkennung
kam das Skript auf 66 frische Profilseiten, dann vier Fehler in Folge —
Abbruch, gespeichert. Ergebnis:

| | Leihspieler |
|---|---:|
| im heutigen Kader | 844 |
| abgefragt | 100 (12 %) |
| davon mit Vertragsende beim Stammverein | 82 |
| davon ohne Datum bei Transfermarkt (`-`) | 18 |
| noch nicht abgefragt | 744 |

Eine erste Fassung dieser Tabelle nannte 1.073 Leihspieler. Gezählt waren
Datensätze, nicht Spieler: wer in der Notensaison für zwei Mannschaften
spielte, steht zweimal im Bestand. Seitdem zählen Sammler und Prüfung je
Spieler.

Halinsky steht jetzt mit **Vertrag bei Slavia Prag bis 30.06.2030** im
Bestand — genau die Angabe seines Transfermarkt-Profils. Unter den
bewerteten Leihspielern mit bekanntem Stammvertrag endet er bei 3 bis zum
Sommer 2027 (bei 2 davon zugleich mit der Leihe), bei 16 in der Saison
2027/28, bei 36 später.

**Was das für die Suche heißt:** Solange ein Leihspieler nicht abgefragt
ist, gibt es für ihn kein Vertragsdatum — und er erscheint nicht unter den
Ausläufern. Das ist gewollt, denn ein unbekannter Vertrag ist kein
auslaufender. Es heißt aber auch: echte Ausläufer unter noch nicht abgefragten
Leihspielern bleiben unsichtbar, bis sie erfasst sind. Über die
Profilseiten hätte das bei rund 60 bis 70 Abrufen je Lauf viele Läufe
gedauert — deshalb der Umstieg.

**Umstieg auf die Vereinsseite.** Die Profilseite kostet einen Abruf je
Spieler. Die Leihspieler-Seite des aufnehmenden Vereins führt dieselbe
Angabe für alle seine Leihspieler auf einmal: Die 844 Leihspieler
verteilen sich auf **290 aufnehmende Vereine** — 290 Abrufe statt 844, auf
einer Seitenart, die am selben Tag 665 Abrufe ohne Sperre vertrug. Den
aufnehmenden Verein kennen wir bei jedem Leihspieler, er liegt immer in
unseren Ligen.

Gegengeprüft, bevor das der Standard wurde:

| Spieler | gelesen auf | Vertrag bis | laut Profilseite |
|---|---|---|---|
| Denis Halinsky | FK Pardubice, Tabelle „Leihklub" | 30.06.2030 | 30.06.2030 |
| Dominik Sarapata | FC Kopenhagen, Tabelle „Leihe an" | 30.06.2029 | 30.06.2029 |

Gelesen wird **spaltengenau**: die letzten beiden zentrierten Zellen einer
Zeile sind *Vertrag bis* und *Leihende*, „-" heißt unbekannt. Bei Pardubice
fehlte in zwei von vier Zeilen eines der beiden Daten — wer nur die Daten
einer Zeile der Reihe nach nimmt, vertauscht dann Vertragsende und
Leihende. Steht ein Leihspieler auf der Seite seines Vereins gar nicht,
bleibt er ungeprüft, statt als „kein Datum" zu gelten.

Hat ein Spieler schon einen Wert von der Profilseite, vergleicht das Skript
beide und benennt jede Abweichung. Die Akte nennt die Quelle des jeweiligen
Werts. Der Profilseiten-Weg bleibt als `--profil` erhalten.

**Der Lauf über die Vereinsseiten, 14.09.2026.** 289 Seiten, keine einzige
Antwort mit 403, keine Sperre:

| | Leihspieler |
|---|---:|
| im heutigen Kader | 844 |
| erfasst | **842** |
| davon mit Vertragsende beim Stammverein | 722 |
| davon ohne Datum bei Transfermarkt (`-`) | 120 |
| auf der Seite ihres Vereins nicht geführt | 2 |

Die eingebaute Gegenprobe lief über alle 100 Spieler, die schon einen Wert
von der Profilseite hatten: **100 gleich, 0 abweichend**. Auch das Leihende
stimmte in jedem Fall mit der Kaderansicht überein.

Unter den 636 bewerteten Leihspielern endet der Vertrag beim Stammverein
bei **13 bis zum Sommer 2027** — bei 11 davon zugleich mit der Leihe —, bei
253 in der Saison 2027/28 und bei 287 später. Die 13 sind die echten
Ausläufer, die vorher unsichtbar waren: vor dem Umstieg war ihr
Stammvertrag schlicht noch nicht abgefragt.

**Abschluss.** Die 2 Leihspieler, die auf der Seite ihres Vereins fehlten,
kamen über ihre Profilseite dazu: Gustavo Mancha (Rio Ave, von Olympiakos,
Vertrag dort bis 30.06.2029) und Jaroud Kanze (FC Pipinsried, von Wacker
Burghausen, bis 30.06.2027 — endet mit der Leihe). Damit sind **alle 844
Leihspieler abgefragt**: 724 mit Vertragsende beim Stammverein, 120 ohne;
842 Werte stammen von der Vereinsseite, 2 von der Profilseite.

Die 120 ohne Datum sind eine **Lücke der Quelle**, nicht des Sammlers. In
einer Stichprobe von 8 zeigt auch die Profilseite jedes Mal `Vertrag dort
bis: -`. In der Suche erscheinen diese Spieler deshalb nicht als Ausläufer;
mit „Leihenden zusätzlich zeigen" stehen sie im eigenen Abschnitt *Vertrag
beim Stammverein unbekannt*.

**Überall gleich behandelt.** Die Regel galt anfangs nur in der
Ausläufer-Suche. Ein Durchgang über alle Stellen, die Vertragsdaten
verwenden, fand drei weitere:

| Stelle | vorher | jetzt |
|---|---|---|
| Hinweise in der Akte | „Vertrag läuft in X Monaten ab" kannte nur den aufnehmenden Verein — bei Kanze gelbe Ampel, aber kein Hinweis | Hinweis auf den Vertrag beim Stammverein |
| Kopfzeile der Akte | keine Kennzeichnung der Leihe | Kennzeichen „Leihe bis … · Vertrag bis …" |
| Bericht zum Herunterladen | Leihe nicht erwähnt | Stammverein, Leihende und Vertrag beim Stammverein |
| Bericht, unbekannter Vertrag | „Stabil (> 12 Monate)", grün — für **jeden** Spieler ohne Vertragsdatum | „Unbekannt", neutral |

Die letzte Zeile war ein älterer Fehler, der mit Leihen nichts zu tun hatte
und erst bei diesem Durchgang auffiel. Die Filter der Spielersuche
arbeiten mit der Vertragsampel; die richtet sich bei Leihen schon nach dem
Stammvertrag und brauchte keine Änderung.

In der **Datenherkunft** jeder Akte steht die Leihspieler-Seite jetzt als
eigene Quelle. Richtiggestellt ist dort auch eine überholte Aussage: Die
Kaderansicht kennzeichne keine Leihspieler — genau an diesem Vermerk
erkennt der Kaderlauf sie inzwischen.

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

## Leistungsdaten wie bei Transfermarkt

Direkt unter den Stammdaten steht in jeder Akte die schlichte Zählung, wie
sie das Transfermarkt-Profil zeigt — ohne Percentil, ohne Farbe:

| Wettbewerb | Spiele | Mögliche Spiele | Tore | Vorlagen | Gelb | Gelb-Rot | Rot | Minuten |
|---|---|---|---|---|---|---|---|---|
| Bundesliga · FC Bayern München | 31 | 34 | 36 | 5 | 1 | 0 | 0 | 2.382' |

- **Saison und Liga sind die der Note** (2025/26). Wer seither den Verein
  gewechselt hat, steht mit dem Verein von damals da.
- **Nur Ligaspiele.** Transfermarkt zählt im Profil auch Pokal und
  Europapokal mit, dort kann die Summe höher sein. Das steht unter der
  Tabelle, damit ein Nachschlagen nicht nach einem Fehler aussieht.
- **„Mögliche Spiele“** sind die Ligaspiele der Mannschaft laut
  Abschlusstabelle. Wer während der Saison kam oder ging, war nicht für
  alle spielberechtigt.
- **Zwei Mannschaften in einer Saison** — etwa Zweitvertretung und
  Profikader, bei 1.263 Spielern — stehen wie bei Transfermarkt als eigene
  Zeilen, dazu die Summe. Die Zeile, auf der die Note beruht, ist markiert.
- Jeder Spaltenkopf erklärt sich im Fenster: Definition, Umfang, Quelle.

**Nichts neu abgerufen.** Die Zahlen lagen seit dem Kaderlauf in
`data/players_raw.json.gz`; `compute_grades.py` gab davon bisher nur
Einsätze und Minuten weiter, jetzt auch Tore, Vorlagen, Karten und die
Spiele der Mannschaft (Feld `ld`, bei weiteren Mannschaften unter
`auch_in`). Geprüft: Alle 17.721 Spieler stimmen mit den Rohdaten überein,
und außer dem neuen Feld ist `players.json` unverändert — Noten,
Kennzahlen, Datenstand. Die Datei wächst um 856 KB, komprimiert übertragen
sind es rund 110 KB mehr.

## Bericht zum Herunterladen

Aus jeder Akte lässt sich ein Bericht als eigenständige HTML-Datei erzeugen,
für Papier gesetzt. Seit dem 17.09.2026 enthält er auch, was die Akte
inzwischen zeigt:

| Abschnitt | Kompakt | Ausführlich |
|---|---|---|
| Leistungsdaten (wie oben, samt weiterer Mannschaften und Summe) | ja | ja |
| Rollenprofil | beste Rolle in einem Satz, mit den drei tragenden Kennzahlen | alle Rollen mit Wert |
| Kennzahlenblöcke mit Rohwert und Percentil | — | ja |

Die Zahlen stammen aus denselben Funktionen wie die Akte, können also nicht
von ihr abweichen. Fehlt eine Grundlage — für Spieler unterhalb der 3. Liga
führt Sofascore keine Einzelkennzahlen —, steht dort ein Satz statt eines
leeren Abschnitts.

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
| Torwart | **verhinderte Tore / 90**, Defensive der Mannschaft, Einsatzanteil | **Paradenquote** |
| Innenverteidigung | Zweikampfquote, Defensive der Mannschaft, Einsatzanteil | **Defensivaktionen / 90**, **Passquote** |
| Außenverteidigung | — | Zweikampfquote, **Defensivaktionen**, **Schlüsselpässe**, Defensive, Einsatzanteil, Vorlagen |
| Zentrales Mittelfeld | — | **Passquote**, **Pässe im letzten Drittel**, **Defensivaktionen**, **Schlüsselpässe**, Zweikampfquote, Teamtore, Scorerpunkte, Vorlagen, Einsatzanteil |
| Offensive | Scorerpunkte / 90 | **xG / 90**, **xA / 90**, **Schlüsselpässe**, Teamtore, Vorlagen, Tore / 90 |
| Sturm | Tore / 90 | **xG / 90**, **Abschlussquote**, Teamtore, Scorerpunkte / 90 |

Fett: seit dem 13.09.2026 dabei (siehe *Erweiterter Notensatz* weiter unten).

Der Effekt der Positionsgewichtung war schon vorher deutlich: Bayerns
Innenverteidigung stieg von Platz 8 auf **Platz 1 der Liga**, Heidenheim
fiel auf Platz 17. Die Abwehrnoten folgen den tatsächlichen Gegentoren —
Dortmund (34 Gegentore) führt, Heidenheim (72) schließt ab.

**Die Defensive der Mannschaft ist ein Mannschaftswert**, kein individueller.
Das Profil kennzeichnet sie als solchen. Ihr Gewicht ist unverändert, ihr
*Anteil* an der Note aber gesunken, weil individuelle Kennzahlen
dazugekommen sind: bei Torhütern von 38 auf 21 %, bei Innenverteidigern
von 25 auf 18 %, bei Außenverteidigern von 20 auf 12 %. Wo es keine
individuellen Daten gibt — Regional- und Oberliga —, bleibt alles wie
zuvor, und die Akte sagt es dort ausdrücklich.

### Erweiterter Notensatz (freigegeben am 13.09.2026)

Bis dahin bestand die Note eines **Torhüters** aus Mannschaftsgegentoren
und Verfügbarkeit — aus nichts, was er selbst getan hat. Mit der
Sofascore-Erweiterung gibt es genug individuelle Werte, um das zu ändern.

**Die Regel: bestehende Gewichte bleiben unangetastet, neue Kennzahlen
kommen hinzu.** Ein erster Entwurf, der auch die alten Gewichte umstellte,
verschob die Noten von Regional- und Oberliga um im Median 3 Punkte,
obwohl es dort keine einzige neue Zahl gibt. Eine Zusicherung im Code
(`KENNZAHLEN_BISHER`) prüft das jetzt bei jedem Lauf.

Gemessen beim Umstellen:

| Spielklasse | Spieler | unverändert | Median-Verschiebung | max |
|---|---:|---:|---:|---:|
| 1 (Erste Ligen) | 3.557 | 7,6 % | 4 | 25 |
| 2 (Zweite Ligen) | 2.200 | 6,8 % | 4 | 25 |
| 3 (3. Liga) | 418 | 7,4 % | 4 | 18 |
| 4–5 (Regional-, Oberliga) | 6.490 | **100 %** | 0 | 0 |

Beispiele aus der Bundesliga:

| Spieler | vorher | nachher | Grund |
|---|---:|---:|---|
| Janis Blaswich | 34 | 59 | verhinderte 3,8 Tore über Erwartung |
| Daniel Batz | 40 | 57 | verhinderte 9,1 Tore über Erwartung |
| Exequiel Palacios | 37 | 53 | 90,7 % Passquote, 25,4 Pässe im letzten Drittel |
| Frederik Rönnow | 39 | 25 | kassierte 8,8 Tore **mehr** als erwartet |
| Rani Khedira | 59 | 43 | 66,6 % Passquote, 0,51 Schlüsselpässe / 90 |
| Nico Schlotterbeck | 79 | 68 | Dortmunds starke Abwehr zählt weniger für ihn |

**Zwei Einschränkungen, die dazugehören.** Die Passquote belohnt auch den
sicheren Querpass; bei Innenverteidigern hat sie Gewicht 2 von 17, also
12 %. Und die Defensivaktionen hängen leicht davon ab, wie viel Ball die
Mannschaft hat — nachgemessen in der Bundesliga: Korrelation −0,21 bei
Innenverteidigern, −0,11 im Mittelfeld. Messbar, aber schwach; Kimmichs
3,2 Aktionen je 90 sind nicht Bayerns Ballbesitz geschuldet, Goretzka
kommt beim selben Verein auf 5,0. Eine Ballbesitz-Korrektur (Padj.) wäre
eine Verfeinerung, keine Reparatur. Auf Rückfrage entschieden am 14.09.2026:
**nicht umgesetzt** — zu wenig Wirkung für eine zusätzliche Rechenschicht,
für die der Ballbesitz je Mannschaft erst erhoben werden müsste.

**In der Akte ist jede Zeile gekennzeichnet**, die in die Note eingeht —
mit einem kleinen Zeichen *Note* neben dem Namen. Was die Note aus
mehreren Zeilen zusammensetzt (Defensivaktionen, Paradenquote), steht im
Kopftext. So muss niemand den Beteuerungen glauben, er kann nachsehen.

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

Dieselbe Ehrlichkeit gilt beim Vereins-Matching: Wo keine Sofascore-Kennzahlen
vorliegen (unterhalb der 3. Liga), lassen sich *Pressing*, *Aufbau* und
*Standards* nicht berechnen und werden als **Datenlücke** ausgewiesen statt mit
einer erfundenen Zahl gefüllt. Bis zur 3. Liga kommen alle fünf
Stil-Dimensionen seit dem 17.09.2026 aus Kennzahlen.

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
