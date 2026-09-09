#!/usr/bin/env python3
"""Rechnet Rohwerte in Percentile um und erzeugt data/players.json.

Percentile werden immer innerhalb derselben Liga UND derselben
Positionsgruppe gebildet - ein Innenverteidiger der 2. Bundesliga wird
also mit Innenverteidigern der 2. Bundesliga verglichen, nicht mit
Stuermern der Premier League.

Ehrlichkeitshinweis: die Kennzahlen stammen aus frei verfuegbaren Quellen
(Transfermarkt). xG, xA und progressive Carries sind dort NICHT enthalten
und werden daher auch nicht ausgewiesen. Lieber sechs echte Werte als
zwanzig geschaetzte.

Lauf:  python3 scripts/compute_grades.py
"""

from __future__ import annotations

import gzip
import json
import os
import sys
from datetime import date, datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from leagues import LEAGUES, by_frontend_id         # noqa: E402

QUELLE = os.path.join(os.path.dirname(__file__), "..", "data",
                      "players_raw.json.gz")
ZIEL = os.path.join(os.path.dirname(__file__), "..", "data", "players.json")

MIN_MINUTEN = 450          # darunter ist die Stichprobe zu duenn

# Positionsgruppen fuer den Vergleich
GRUPPE = {
    "TW": "TW",
    "IV": "IV", "LV": "AV", "RV": "AV",
    "DM": "ZM", "ZM": "ZM",
    "OM": "OFF", "LA": "OFF", "RA": "OFF",
    "ST": "ST",
}

# Kennzahlen je Gruppe: (Anzeigename, Schluessel, hoeher_ist_besser, Gewicht)
#
# Warum gewichtet? Vorher zaehlte jede Kennzahl gleich viel. Fuer Stuermer
# ging das auf, fuer Innenverteidiger nicht: deren Note bestand fast nur aus
# Einsaetzen, Minuten und Karten - also aus Verfuegbarkeit, nicht aus
# Spielstaerke.
#
# Was jetzt dazukommt, stammt aus der Ligatabelle (ein Abruf je Liga):
#   * Gegentore der Mannschaft je Spiel - der einzige belegbare
#     Defensivwert. Ausdruecklich ein MANNSCHAFTSWERT, kein individueller;
#     im Frontend als solcher gekennzeichnet.
#   * Anteil an den Toren der Mannschaft - zeigt, wie viel der Offensive
#     ueber diesen Spieler laeuft. Zehn Tore in einem Team mit 30 Toren
#     wiegen schwerer als zehn in einem Team mit 90.
#   * Einsatzanteil an den Saisonspielen statt roher Einsatzzahl - so sind
#     Ligen mit unterschiedlich vielen Spieltagen vergleichbar.
TEAM_KENNZAHLEN = {"team_gegentore_pro_spiel"}

KENNZAHLEN = {
    "TW":  [("Defensive der Mannschaft", "team_gegentore_pro_spiel", False, 3),
            ("Einsatzanteil der Saison", "einsatz_anteil", True, 3),
            ("Minuten je Einsatz", "min_pro_einsatz", True, 1),
            ("Disziplin (Karten inv.)", "karten_pro90", False, 1)],

    "IV":  [("Defensive der Mannschaft", "team_gegentore_pro_spiel", False, 3),
            ("Einsatzanteil der Saison", "einsatz_anteil", True, 3),
            ("Minuten je Einsatz", "min_pro_einsatz", True, 1),
            ("Torgefahr bei Standards", "tore_pro90", True, 1),
            ("Disziplin (Karten inv.)", "karten_pro90", False, 1)],

    "AV":  [("Defensive der Mannschaft", "team_gegentore_pro_spiel", False, 2),
            ("Einsatzanteil der Saison", "einsatz_anteil", True, 2),
            ("Vorlagen / 90", "vorlagen_pro90", True, 2),
            ("Anteil an Teamtoren", "tor_anteil", True, 1),
            ("Disziplin (Karten inv.)", "karten_pro90", False, 1)],

    "ZM":  [("Anteil an Teamtoren", "tor_anteil", True, 2),
            ("Scorerpunkte / 90", "scorer_pro90", True, 2),
            ("Vorlagen / 90", "vorlagen_pro90", True, 2),
            ("Einsatzanteil der Saison", "einsatz_anteil", True, 2),
            ("Defensive der Mannschaft", "team_gegentore_pro_spiel", False, 1),
            ("Disziplin (Karten inv.)", "karten_pro90", False, 1)],

    "OFF": [("Scorerpunkte / 90", "scorer_pro90", True, 3),
            ("Anteil an Teamtoren", "tor_anteil", True, 2),
            ("Vorlagen / 90", "vorlagen_pro90", True, 2),
            ("Tore / 90", "tore_pro90", True, 2),
            ("Einsatzanteil der Saison", "einsatz_anteil", True, 1),
            ("Disziplin (Karten inv.)", "karten_pro90", False, 1)],

    "ST":  [("Tore / 90", "tore_pro90", True, 3),
            ("Anteil an Teamtoren", "tor_anteil", True, 2),
            ("Scorerpunkte / 90", "scorer_pro90", True, 2),
            ("Vorlagen / 90", "vorlagen_pro90", True, 1),
            ("Einsatzanteil der Saison", "einsatz_anteil", True, 1),
            ("Disziplin (Karten inv.)", "karten_pro90", False, 1)],
}


# Alle vorkommenden Anzeigenamen, einmalig. Die Reihenfolge ist der
# Index, den die params der Spieler referenzieren.
KENNZAHL_NAMEN = sorted({anzeige for felder in KENNZAHLEN.values()
                         for anzeige, _, _, _ in felder})
KENNZAHL_INDEX = {name: i for i, name in enumerate(KENNZAHL_NAMEN)}


# Niveau-Skala. Der Median-Marktwert einer Liga ist ein brauchbarer Mass-
# stab fuer ihre Staerke - und aussagekraeftiger als die blosse Spielklasse:
# die Championship liegt gleichauf mit der belgischen ersten Liga, die
# oesterreichische Bundesliga unter der franzoesischen Ligue 2.
#
# Abgebildet wird logarithmisch, weil sich die Marktwerte ueber drei
# Groessenordnungen erstrecken. 20 Tsd. € Median ergibt 0, 20 Mio. € ergibt
# 100.
NIVEAU_UNTEN = 20_000
NIVEAU_OBEN = 20_000_000

# Fuer die Oberligen fuehrt die Quelle keine Marktwerte. Der Wert ist daher
# geschaetzt (eine Klasse unter der Regionalliga) und wird als solcher
# gekennzeichnet, statt eine Messung vorzutaeuschen.
NIVEAU_GESCHAETZT = {5: 12}


def niveau_aus_marktwert(median_eur: float) -> int:
    import math
    if median_eur <= 0:
        return 0
    spanne = math.log10(NIVEAU_OBEN) - math.log10(NIVEAU_UNTEN)
    roh = (math.log10(median_eur) - math.log10(NIVEAU_UNTEN)) / spanne
    return max(0, min(100, round(roh * 100)))


# Kennzahl -> Bereich. Damit laesst sich die Note aufschluesseln, statt
# sie als eine Zahl stehen zu lassen: eine 66 aus lauter
# Mannschaftswerten sagt etwas anderes als eine 66 aus eigenen Toren.
BEREICH = {
    "tore_pro90": "offensiv",
    "vorlagen_pro90": "offensiv",
    "scorer_pro90": "offensiv",
    "tor_anteil": "offensiv",
    "team_gegentore_pro_spiel": "defensiv",
    "einsatz_anteil": "verfuegbarkeit",
    "min_pro_einsatz": "verfuegbarkeit",
    "minuten": "verfuegbarkeit",
    "einsaetze": "verfuegbarkeit",
    "karten_pro90": "disziplin",
}
BEREICH_NAME = {
    "offensiv": "Offensive",
    "defensiv": "Defensive (Mannschaft)",
    "verfuegbarkeit": "Verfügbarkeit",
    "disziplin": "Disziplin",
}


# ---------------------------------------------------------------------
# Liganiveau: UEFA-Koeffizient und Marktwert gemischt
#
# Der Marktwert allein verzerrte systematisch. La Liga und Serie A haben
# niedrigere Median-Marktwerte als die Bundesliga, sind im Europapokal
# aber erfolgreicher - tiefere Kader, mehr Wettbewerb. Portugal stand bei
# 57, liegt im UEFA-Ranking aber vor Belgien.
#
# Quelle: UEFA-Fuenfjahreskoeffizient, Laenderwertung 2025/26
# (kassiesa.net/uefa, Methode 5), Einzeljahre 21/22 bis 25/26.
#
# JUENGERE JAHRE WIEGEN SCHWERER. Das Werkzeug bewertet Spieler der Saison
# 2025/26; Ergebnisse aus 2021/22 sagen wenig ueber die Staerke einer Liga
# heute. Mit dieser Gewichtung zieht Spanien an Italien vorbei - im
# juengsten Jahr liegt Italien mit 19,0 hinter Spanien (22,1) und
# Deutschland (21,8), sein Vorsprung in der Fuenfjahressumme stammt aus
# den aelteren Jahren.
#
# Zu beachten: der Abstand zwischen 84, 85 und 86 liegt innerhalb der
# Messgenauigkeit. Diese Ligen sind praktisch gleich stark - die
# Rangfolge dazwischen sollte niemand ueberdeuten.
UEFA_JAHRE = {                    # 21/22, 22/23, 23/24, 24/25, 25/26
    "ENG": [21.000, 23.000, 17.375, 29.464, 28.680],
    "ITA": [15.714, 22.357, 21.000, 21.875, 19.000],
    "ESP": [18.428, 16.571, 16.062, 23.892, 22.093],
    "GER": [16.214, 17.125, 19.357, 18.421, 21.785],
    "FRA": [18.416, 12.583, 16.250, 17.928, 18.321],
    "POR": [12.916, 12.500, 11.000, 16.250, 20.500],
    "BEL": [6.600, 14.200, 14.400, 15.650, 11.400],
    "POL": [4.625, 7.750, 6.875, 11.750, 15.750],
    "CZE": [6.700, 6.750, 13.500, 10.550, 11.025],
    "AUT": [10.400, 4.900, 4.800, 9.650, 4.100],
}
UEFA_GEWICHTE = [1, 2, 4, 6, 9]
ANTEIL_UEFA = 0.6                 # Rest: Marktwert

# Ligen ohne UEFA-Wert haengen an ihrer ersten Liga. Ihr Abstand dorthin
# bleibt, wie ihn die Marktwerte ausweisen - dieses Verhaeltnis ist
# bemerkenswert stabil (Championship/PL 0,65, 2. BL/BL 0,66,
# LaLiga2/LaLiga 0,65).
ELTERNLIGA = {
    "champ": "pl", "buli2": "buli", "laliga2": "laliga",
    "serieb": "seriea", "ligue2": "ligue1",
    "l3": "buli2",
    "rl-nord": "buli2", "rl-nordost": "buli2", "rl-west": "buli2",
    "rl-suedwest": "buli2", "rl-bayern": "buli2",
}


def uefa_niveau() -> dict[str, float]:
    """Gewichteter UEFA-Koeffizient je Land, auf 0-100 gestaucht.

    Gestaucht per Wurzel, weil der Koeffizient von wenigen Spitzenvereinen
    getrieben wird: linear uebersetzt fiele Oesterreich unter die deutsche
    3. Liga, was die Breite der Liga voellig verfehlt.
    """
    import math
    roh = {land: sum(v * g for v, g in zip(werte, UEFA_GEWICHTE))
                 / sum(UEFA_GEWICHTE)
           for land, werte in UEFA_JAHRE.items()}
    hoechster = max(roh.values())
    return {land: 100 * math.sqrt(v / hoechster) for land, v in roh.items()}


# ---------------------------------------------------------------------
# Datenherkunft
#
# Jede Zahl im Werkzeug muss sich einer Quelle zuordnen lassen - sonst
# laesst sich nicht beurteilen, wie belastbar sie ist. Die Uebersicht
# wandert in die Ausgabedatei und wird im Frontend angezeigt.
#
# "abgeleitet" heisst: von diesem Werkzeug berechnet, nicht gemessen.
# ---------------------------------------------------------------------
HERKUNFT = {
    "transfermarkt": {
        "name": "Transfermarkt",
        "url": "https://www.transfermarkt.de",
        "art": "erhoben",
        "felder": ["Name", "Alter", "Position", "Größe", "Fuß", "Rückennummer",
                   "Marktwert", "Vertragsende", "Verein", "Liga",
                   "Einsätze", "Tore", "Vorlagen", "Karten", "Minuten",
                   "Spiele/Tore/Gegentore der Mannschaft",
                   "Verletzungshistorie"],
        "hinweis": "Leistungsdaten nur aus der jeweiligen Liga "
                   "(ohne Pokal und Europapokal).",
    },
    "transfermarkt_vertrag": {
        "name": "Transfermarkt · Vertragsende",
        "url": "https://www.transfermarkt.de",
        "art": "erhoben",
        "felder": ["Auslaufender Vertrag", "Vertragsoption", "Leihe"],
        "hinweis": "Eigene Vereinsseite je Sommer. Nur sie führt die "
                   "Vertragsoption und markiert Leihspieler - die "
                   "Kaderansicht tut beides nicht. Geprüft werden die "
                   "beiden kommenden Sommer; wo nichts steht, läuft der "
                   "Vertrag länger oder der Verein wurde noch nicht "
                   "geprüft (auf der Trefferkarte unterschieden).",
    },
    "transfermarkt_bild": {
        "name": "Transfermarkt · Spielerfoto",
        "url": "https://www.transfermarkt.de",
        "art": "erhoben",
        "felder": ["Portrait in der Spielerakte"],
        "hinweis": "Wird beim Öffnen einer Akte direkt von Transfermarkt "
                   "geladen, nicht hier gespeichert. Nur für Spieler im "
                   "heutigen Kader; wo kein Foto vorliegt, stehen die "
                   "Initialen.",
    },
    "understat": {
        "name": "Understat",
        "url": "https://understat.com",
        "art": "erhoben",
        "felder": ["xG", "npxG", "xA", "Schlüsselpässe", "Schüsse",
                   "Aufbaubeteiligung"],
        "hinweis": "Nur die fünf großen ersten Ligen. Geht bewusst NICHT "
                   "in die Liga-Note ein.",
    },
    "abgeleitet": {
        "name": "Von diesem Werkzeug berechnet",
        "url": None,
        "art": "abgeleitet",
        "felder": ["Liga-Note", "Positions-Note", "Team-Note", "Percentile",
                   "Anteil an Teamtoren", "Einsatzanteil", "Liganiveau",
                   "Eingeordnete Note", "Unterbewertet-Index",
                   "Verletzungsanfälligkeit"],
        "hinweis": "Berechnet aus den erhobenen Werten. Percentile gelten "
                   "je Liga und Position.",
    },
    "fehlt": {
        "name": "Nicht verfügbar",
        "url": None,
        "art": "fehlt",
        "felder": ["Zweikämpfe", "Tacklings", "Klärungen", "Passquote",
                   "Laufleistung", "Charakter", "Gewicht"],
        "hinweis": "Individuelle Defensiv- und Laufdaten führen nur "
                   "kostenpflichtige Anbieter; frei zugängliche Quellen "
                   "(FBref, Sofascore, kicker) sperren den Zugriff.",
    },
}


def kennwerte(s: dict) -> dict | None:
    """Leitet die Rohkennzahlen eines Spielers ab.

    Auch Spieler mit wenig Einsatzzeit werden zurueckgegeben - sie fliegen
    nicht raus, sondern werden als "duenne Datenbasis" gekennzeichnet. Die
    Vergleichsverteilung entsteht spaeter trotzdem nur aus Spielern ueber
    MIN_MINUTEN, sonst wuerden Kurzeinsaetze die Percentile verzerren.
    """
    L = s.get("leistung")
    if not L or not L.get("minuten"):
        return None
    minuten = L["minuten"]
    p90 = minuten / 90.0
    karten = L["gelbe"] + L["gelbrot"] * 2 + L["rot"] * 3

    # Mannschaftswerte aus der Ligatabelle. Fehlen sie, bleiben die
    # betreffenden Kennzahlen leer statt geraten zu werden.
    T = s.get("team") or {}
    spiele = T.get("spiele") or 0
    team_tore = T.get("tore") or 0
    team_gegen = T.get("gegentore")

    werte = {
        "einsaetze": L["einsaetze"],
        "minuten": minuten,
        "min_pro_einsatz": minuten / max(L["einsaetze"], 1),
        "tore_pro90": L["tore"] / p90,
        "vorlagen_pro90": L["vorlagen"] / p90,
        "scorer_pro90": (L["tore"] + L["vorlagen"]) / p90,
        "karten_pro90": karten / p90,
        "belastbar": minuten >= MIN_MINUTEN,
    }
    if spiele:
        werte["einsatz_anteil"] = min(1.0, L["einsaetze"] / spiele)
        if team_gegen is not None:
            werte["team_gegentore_pro_spiel"] = team_gegen / spiele
    if team_tore:
        werte["tor_anteil"] = (L["tore"] + L["vorlagen"]) / team_tore
    return werte


def percentil(wert: float, alle: list[float], hoeher_besser: bool) -> int:
    """Anteil der Vergleichsgruppe, der schlechter ist (0-100)."""
    if len(alle) < 2:
        return 50
    schlechter = sum(1 for a in alle if (a < wert if hoeher_besser else a > wert))
    gleich = sum(1 for a in alle if a == wert)
    return max(0, min(100, round(100 * (schlechter + 0.5 * gleich) / len(alle))))


def kategorie(p: int) -> str:
    return "top" if p >= 70 else ("low" if p < 40 else "mid")


def vertrags_ampel(bis: str | None) -> tuple[str, int | None]:
    """('none'|'red'|'yellow'|'green', Restmonate)

    Ohne Datum "none", nicht "yellow": ein unbekannter Vertrag darf nicht
    aussehen wie einer, der in einem Jahr auslaeuft. Betroffen sind vor
    allem Spieler, die ihren Verein verlassen haben - deren Vertragsende
    steht nur noch beim neuen Verein.
    """
    if not bis:
        return "none", None
    try:
        ende = datetime.strptime(bis, "%Y-%m-%d").date()
    except ValueError:
        return "none", None
    monate = (ende.year - date.today().year) * 12 + (ende.month - date.today().month)
    if monate <= 6:
        return "red", monate
    if monate <= 12:
        return "yellow", monate
    return "green", monate


def mw_text(eur: int | None) -> str:
    if not eur:
        return "k. A."
    if eur >= 1_000_000:
        return f"{eur / 1_000_000:.1f}".replace(".", ",") + " Mio."
    return f"{eur // 1000} Tsd."


def initialen(name: str) -> str:
    teile = [t for t in name.split() if t]
    if len(teile) >= 2:
        return (teile[0][0] + teile[-1][0]).upper()
    return (name[:2] or "??").upper()


def main() -> int:
    if not os.path.exists(QUELLE):
        print(f"{QUELLE} fehlt - zuerst build_players.py laufen lassen.",
              file=sys.stderr)
        return 1

    with gzip.open(QUELLE, "rt", encoding="utf-8") as fh:
        roh = json.load(fh)

    # 1) Kennwerte ableiten, Spieler ohne belastbare Stichprobe aussortieren
    kandidaten = []
    for s in roh["spieler"]:
        kw = kennwerte(s)
        if kw:
            kandidaten.append((s, kw))

    # 2) Vergleichsgruppen bilden: (Liga, Positionsgruppe)
    gruppen: dict[tuple, list] = {}
    for s, kw in kandidaten:
        g = GRUPPE.get(s["position"], "ZM")
        gruppen.setdefault((s["liga_id"], g), []).append((s, kw))

    # 3) Percentile je Gruppe
    spieler_out = []
    for (liga_id, g), mitglieder in gruppen.items():
        felder = KENNZAHLEN[g]

        # Vergleichsmassstab nur aus Spielern mit belastbarer Spielzeit.
        # Fehlen die (kleine Staffeln), dient die ganze Gruppe als Notbehelf.
        basis = [(s, kw) for s, kw in mitglieder if kw["belastbar"]] or mitglieder
        # Fehlende Werte fliegen aus der Verteilung, statt als 0 zu
        # verzerren - etwa wenn fuer eine Liga keine Tabelle lesbar war.
        verteilung = {
            key: [kw[key] for _, kw in basis if key in kw]
            for _, key, _, _ in felder
        }

        # Ab der Oberliga fuehrt Transfermarkt keine Marktwerte mehr. Ohne
        # sie ist der Unterbewertet-Index sinnlos - er wuerde jeden Spieler
        # ueber Durchschnitt als unterbewertet ausweisen. Dann lieber weglassen.
        mw_werte = [s.get("marktwert_eur") for s, _ in basis]
        hat_marktwerte = sum(1 for m in mw_werte if m) >= max(3, len(basis) // 3)
        mw_verteilung = [m or 0 for m in mw_werte]

        for s, kw in mitglieder:
            # Nur Index und Wert speichern: der Anzeigename steht einmal in
            # kennzahlen[] am Dateianfang, statt sich je Spieler zu
            # wiederholen, und "cat" leitet das Frontend aus p ab. Bei
            # 18 000 Spielern spart das mehrere Megabyte.
            params = []
            gewichte = []
            bereiche = []
            for anzeige, key, hoch, gewicht in felder:
                if key not in kw or len(verteilung.get(key, [])) < 5:
                    continue          # Kennzahl liegt fuer diesen Fall nicht vor
                wert = percentil(kw[key], verteilung[key], hoch)
                # Gewicht und Team-Kennzeichen haengen nur an Position und
                # Kennzahl, nicht am Spieler. Sie stehen einmal unter
                # "profile" am Dateianfang - je Spieler mitgespeichert waeren
                # es bei 17000 Spielern rund ein Megabyte.
                params.append({"i": KENNZAHL_INDEX[anzeige], "p": wert})
                gewichte.append(gewicht)
                bereiche.append((BEREICH.get(key, "sonstiges"), wert, gewicht,
                                 key in TEAM_KENNZAHLEN))
            if not params:
                continue

            # Leistungsnote: gewichtetes Mittel der Percentile. Ungewichtet
            # bestimmten Verfuegbarkeitswerte die Note der Abwehrspieler.
            ln = round(sum(p["p"] * g for p, g in zip(params, gewichte))
                       / sum(gewichte))

            # Note aufschluesseln: je Bereich ein gewichtetes Mittel, dazu
            # der Anteil, den Mannschaftswerte an der Gesamtnote haben.
            # Genau daher ruehrt das Schwanken von Verein zu Verein - ein
            # Innenverteidiger einer starken Abwehr profitiert davon, ohne
            # dass sein eigener Beitrag messbar waere.
            teilnoten = {}
            for bereich in set(b[0] for b in bereiche):
                teile = [(w, g) for b, w, g, _ in bereiche if b == bereich]
                if teile:
                    teilnoten[bereich] = round(
                        sum(w * g for w, g in teile) / sum(g for _, g in teile))
            team_gewicht = sum(g for _, _, g, ist_team in bereiche if ist_team)
            anteil_team = round(100 * team_gewicht / sum(gewichte))

            # Potenzialnote: Leistung plus Altersbonus
            alter = s.get("alter") or 27
            bonus = max(0, min(12, (26 - alter) * 2)) if alter < 26 else 0
            pn = min(99, ln + bonus)

            # Unterbewertet-Index: Leistungspercentil minus Marktwertpercentil
            if hat_marktwerte and s.get("marktwert_eur"):
                mw_p = percentil(s["marktwert_eur"], mw_verteilung, True)
                underval = ln - mw_p
            else:
                underval = None

            ampel, monate = vertrags_ampel(s.get("vertrag_bis"))

            spieler_out.append({
                "id": int(s["id"]),
                "ini": initialen(s["name"]),
                "name": s["name"],
                "pos": s["position"],
                "club": s["verein"],
                "liga": s["liga"],
                "liga_id": s["liga_id"],
                "stufe": (by_frontend_id(s["liga_id"]).stufe
                          if by_frontend_id(s["liga_id"]) else 1),
                "land": s["land"],
                "age": alter,
                # Absicherung: durch die frueher spaltenbasierte Erkennung
                # steckte in "fuss" teils die Koerpergroesse. Nur echte
                # Fusswerte durchlassen, alles andere gilt als unbekannt.
                "foot": (s.get("fuss")
                         if s.get("fuss") in ("rechts", "links", "beidfüßig")
                         else "k. A."),
                "height": f"{s['groesse_cm']} cm" if s.get("groesse_cm") else "k. A.",
                "weight": "k. A.",          # Transfermarkt fuehrt kein Gewicht
                "number": s.get("rueckennummer") or 0,
                "contract": ampel,
                "contract_until": s.get("vertrag_bis"),
                "mv": mw_text(s.get("marktwert_eur")),
                "mv_eur": s.get("marktwert_eur"),
                "ln": ln,
                "pn": pn,
                "underval": underval is not None and underval >= 10,
                "underval_index": underval,
                "minuten": kw["minuten"],
                "einsaetze": kw["einsaetze"],
                "belastbar": kw["belastbar"],
                # Steht nach dem Transferschluss nicht mehr im Kader seines
                # Vereins - fuer Scouting eine Information, kein Fehler.
                **({"weg": 1} if s.get("nicht_mehr_im_kader") else {}),
                # xG-Werte von Understat, nur fuer die fuenf grossen ersten
                # Ligen vorhanden. Sie fliessen BEWUSST NICHT in die Note
                # ein - sonst waeren diese fuenf Ligen anders bewertet als
                # die uebrigen 28 und der Ligavergleich waere hinfaellig.
                **({"xg": s["xg"]} if s.get("xg") else {}),
                "params": params,
                "teilnoten": teilnoten,
                # Wie viel der Note stammt aus Mannschaftswerten?
                "anteil_team": anteil_team,
                # Worauf die Note beruht - Groesse der Vergleichsgruppe und
                # eigene Spielzeit. Eine 90 aus einer Gruppe von acht ist
                # etwas anderes als eine 90 aus einer Gruppe von achtzig.
                "basis": {"gruppe": len(basis), "minuten": kw["minuten"]},
                **({"verletzungen": s["verletzungen"]}
                   if s.get("verletzungen") else {}),
                # Auslaufender Vertrag, direkt von der Transfermarkt-Seite
                # "Vertragsende" (scripts/vertraege.py). Die Option ist der
                # eigentliche Gewinn: mit einer Verlaengerungsoption ist ein
                # Auslaeufer kein freier Transfer. "leihe" ebenso - dort
                # endet die Leihe, nicht der Vertrag beim Stammverein.
                **({"auslauf": {
                       "bis": s["vertrag"]["bis"],
                       **({"option": s["vertrag"]["option"]}
                          if s["vertrag"].get("option") else {}),
                       **({"leihe": 1} if s["vertrag"].get("leihe") else {}),
                   }} if s.get("vertrag") else {}),
                # Welche Sommer nachgesehen wurden. Nur damit laesst sich
                # "Vertrag laeuft laenger" von "nicht geprueft" trennen -
                # ohne diese Angabe waere die Auslaeufer-Suche eine
                # Behauptung statt einer Auskunft.
                **({"vgeprueft": s["vertrag_scan"]["jahre"]}
                   if s.get("vertrag_scan") else {}),
                # Zeitstempel des Portraits. Nur er wird gespeichert - die
                # Adresse setzt das Frontend aus bild_basis, ID und ihm
                # zusammen. Fehlt er, bleiben die Initialen stehen.
                **({"bild": s["bild"]} if s.get("bild") else {}),
                # flags und fazit entstehen im Frontend (flagsFuer/fazitFuer).
                # Als Text mitgeliefert waeren sie rund 8 MB - fast die
                # Haelfte der Datei - obwohl sie nur beim Oeffnen eines
                # einzelnen Profils gebraucht werden. Alle Eingangswerte
                # dafuer stehen ohnehin im Datensatz.
            })

    # Ein Spieler kann in einer Saison fuer mehrere Mannschaften auflaufen -
    # typisch Zweitvertretung plus Profikader. Beide Eintraege stehen zu
    # lassen erzeugt Doppel in der Trefferliste, und showProfile() faende
    # immer nur den ersten. Massgeblich ist der Einsatz mit den meisten
    # Minuten; die uebrigen bleiben als Zusatz erhalten, denn ein Kurzeinsatz
    # in der hoeheren Liga ist fuer Scouting eine Information, kein Rauschen.
    nach_id: dict[int, list[dict]] = {}
    for p in spieler_out:
        nach_id.setdefault(p["id"], []).append(p)

    zusammengefasst = []
    for eintraege in nach_id.values():
        eintraege.sort(key=lambda p: -p["minuten"])
        haupt = eintraege[0]
        if len(eintraege) > 1:
            haupt["auch_in"] = [{
                "liga": w["liga"], "club": w["club"], "stufe": w["stufe"],
                "minuten": w["minuten"], "einsaetze": w["einsaetze"],
            } for w in eintraege[1:]]
            # Vertragsangaben aus jedem Eintrag uebernehmen: der Kader mit
            # den meisten Minuten ist oft die Zweitvertretung, gefuehrt
            # wird der Vertrag aber beim Profikader.
            for w in eintraege[1:]:
                for feld in ("auslauf", "vgeprueft", "bild"):
                    if feld not in haupt and feld in w:
                        haupt[feld] = w[feld]
        zusammengefasst.append(haupt)

    doppelte = len(spieler_out) - len(zusammengefasst)
    spieler_out = zusammengefasst
    spieler_out.sort(key=lambda p: (-p["ln"], p["name"]))

    # 4) Ligenliste fuer das Frontend (aus den echten Daten)
    ligen: dict[str, dict] = {}
    for s in roh["spieler"]:
        lg = by_frontend_id(s["liga_id"])
        eintrag = ligen.setdefault(s["liga_id"], {
            "id": s["liga_id"], "name": s["liga"],
            "land": s["land"], "stufe": lg.stufe if lg else 1,
            "vereine": set(),
        })
        eintrag["vereine"].add(s["verein"])

    # Wie viele bewertete Spieler je Liga - macht duenne Datenlage sichtbar
    bewertet_je_liga: dict[str, int] = {}
    for p in spieler_out:
        bewertet_je_liga[p["liga_id"]] = bewertet_je_liga.get(p["liga_id"], 0) + 1

    # Anteil der Spieler mit Marktwert je Liga. Ein blosses "ja/nein" waere
    # irrefuehrend: in den Oberligen fuehrt die Quelle bei rund 2 Prozent
    # einen Wert - zu wenig fuer den Unterbewertet-Index, aber nicht null.
    def mw_anteil(liga_id: str) -> int:
        gruppe = [p for p in spieler_out if p["liga_id"] == liga_id]
        if not gruppe:
            return 0
        return round(100 * sum(1 for p in gruppe if p["mv_eur"]) / len(gruppe))

    def marktwert_niveau(liga_id: str, stufe: int) -> tuple[int, bool]:
        """Niveau allein aus dem Median-Marktwert. (Wert, geschaetzt?)"""
        werte = sorted(p["mv_eur"] for p in spieler_out
                       if p["liga_id"] == liga_id and p["mv_eur"])
        if len(werte) >= 20:
            median = werte[len(werte) // 2]
            return niveau_aus_marktwert(median), False
        return NIVEAU_GESCHAETZT.get(stufe, 50), True

    unorm = uefa_niveau()

    def niveau_fuer(liga_id: str, stufe: int, land: str) -> tuple[int, bool, str]:
        """(Niveau 0-100, geschaetzt?, Grundlage)

        Erste Ligen mit UEFA-Wert: Mischung aus Europapokalerfolg und
        Marktwert. Alle uebrigen erben den Abstand zu ihrer ersten Liga,
        wie ihn die Marktwerte ausweisen - fuer sie gibt es keinen
        eigenen UEFA-Wert.
        """
        mw, geschaetzt = marktwert_niveau(liga_id, stufe)

        if stufe == 1 and land in unorm:
            gemischt = round(ANTEIL_UEFA * unorm[land] + (1 - ANTEIL_UEFA) * mw)
            return gemischt, False, "uefa+marktwert"

        eltern = ELTERNLIGA.get(liga_id)
        if eltern:
            eltern_mw, _ = marktwert_niveau(eltern, 1 if eltern in
                                            ("pl", "buli", "laliga", "seriea",
                                             "ligue1") else 2)
            eltern_land = next((l.land for l in LEAGUES
                                if l.frontend_id == eltern), None)
            eltern_neu = niveau_fuer(eltern, 1 if eltern_land in unorm and
                                     eltern not in ELTERNLIGA else 2,
                                     eltern_land)[0]
            if eltern_mw:
                verhaeltnis = mw / eltern_mw
                return round(eltern_neu * verhaeltnis), geschaetzt, "abgeleitet"

        return mw, geschaetzt, "marktwert"

    ligen_liste = []
    for v in ligen.values():
        niv, geschaetzt, grundlage = niveau_fuer(v["id"], v["stufe"], v["land"])
        ligen_liste.append({**v, "vereine": sorted(v["vereine"]),
                            "bewertet": bewertet_je_liga.get(v["id"], 0),
                            "marktwert_anteil": mw_anteil(v["id"]),
                            "niveau": niv,
                            "niveau_geschaetzt": geschaetzt,
                            "niveau_grundlage": grundlage})

    # Niveau auch am Spieler, damit das Frontend nicht nachschlagen muss
    niveau_je_liga = {l["id"]: l["niveau"] for l in ligen_liste}
    for p in spieler_out:
        p["niveau"] = niveau_je_liga.get(p["liga_id"], 50)
    ligen_liste.sort(key=lambda l: (l["stufe"], l["land"], l["name"]))

    # Schutz gegen stillen Datenverlust. Genau das ist einmal passiert: die
    # Action lief mit nur einer Liga, fand keinen Bestand zum Ergaenzen
    # (die Rohdatei war nicht eingecheckt) und ersetzte 17296 Spieler durch
    # 346. Lieber laut abbrechen als eine geschrumpfte Datei schreiben.
    if os.path.exists(ZIEL) and not os.environ.get("SCOUT_SCHRUMPFEN_OK"):
        try:
            with open(ZIEL, encoding="utf-8") as fh:
                vorher = len(json.load(fh).get("players", []))
        except (OSError, ValueError):
            vorher = 0
        if vorher and len(spieler_out) < vorher * 0.5:
            print(f"ABBRUCH: {len(spieler_out)} Spieler wuerden {vorher} "
                  f"ersetzen - das ist weniger als die Haelfte. Fehlt der "
                  f"Bestand in data/players_raw.json.gz? Mit "
                  f"SCOUT_SCHRUMPFEN_OK=1 laesst sich das uebergehen.",
                  file=sys.stderr)
            return 1

    os.makedirs(os.path.dirname(ZIEL), exist_ok=True)
    with open(ZIEL, "w", encoding="utf-8") as fh:
        json.dump({
            "stand": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "saison": roh.get("saison"),
            "quellen": roh.get("quellen", []),
            "hinweis": ("Kennzahlen aus frei verfügbaren Quellen. "
                        "xG/xA/progressive Carries sind darin nicht enthalten "
                        "und werden bewusst nicht ausgewiesen."),
            "mindestminuten": MIN_MINUTEN,
            "bild_basis": roh.get("bild_basis"),
            "kennzahlen": KENNZAHL_NAMEN,
            "herkunft": HERKUNFT,
            "bereiche": BEREICH_NAME,
            "profile": {
                g: [{"i": KENNZAHL_INDEX[a], "g": gew,
                     **({"team": 1} if k in TEAM_KENNZAHLEN else {})}
                    for a, k, _, gew in felder]
                for g, felder in KENNZAHLEN.items()
            },
            "positionsgruppe": GRUPPE,
            "ligen": ligen_liste,
            "players": spieler_out,
        }, fh, ensure_ascii=False, separators=(",", ":"))

    fest = sum(1 for p in spieler_out if p["belastbar"])
    if doppelte:
        print(f"{doppelte} Doppeleintraege zusammengefasst (Spieler mit "
              f"Einsaetzen fuer mehrere Mannschaften)", file=sys.stderr)
    print(f"{len(spieler_out)} Spieler bewertet, davon {fest} mit belastbarer "
          f"Spielzeit (ab {MIN_MINUTEN} Min) - von {len(roh['spieler'])} "
          f"gesammelt -> {os.path.relpath(ZIEL)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
