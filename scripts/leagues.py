#!/usr/bin/env python3
"""Liga-Konfiguration fuer das Scout-Tool.

Eine Liga hinzufuegen = eine Zeile in LEAGUES. Die Transfermarkt-ID steht
in der URL der Liga-Startseite, z. B.
    transfermarkt.de/bundesliga/startseite/wettbewerb/L1  ->  "L1"

`frontend_id` ist der Schluessel, den index.html im Liga-Filter verwendet.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class League:
    tm_id: str          # Transfermarkt-Wettbewerbs-ID
    frontend_id: str    # id im Frontend (LIGEN-Array)
    name: str
    land: str           # 3-Buchstaben-Code, wie im Frontend
    stufe: int          # 1 = erste Liga, 2 = zweite Liga


LEAGUES: list[League] = [
    # --- Deutschland ---
    League("L1",  "buli",      "Bundesliga",            "GER", 1),
    League("L2",  "buli2",     "2. Bundesliga",         "GER", 2),
    # --- England ---
    League("GB1", "pl",        "Premier League",        "ENG", 1),
    League("GB2", "champ",     "Championship",          "ENG", 2),
    # --- Spanien ---
    League("ES1", "laliga",    "La Liga",               "ESP", 1),
    League("ES2", "laliga2",   "LaLiga 2",              "ESP", 2),
    # --- Italien ---
    League("IT1", "seriea",    "Serie A",               "ITA", 1),
    League("IT2", "serieb",    "Serie B",               "ITA", 2),
    # --- Frankreich ---
    League("FR1", "ligue1",    "Ligue 1",               "FRA", 1),
    League("FR2", "ligue2",    "Ligue 2",               "FRA", 2),
    # --- Belgien / Portugal / Oesterreich ---
    League("BE1", "jupiler",   "Jupiler Pro League",    "BEL", 1),
    League("PO1", "primeira",  "Liga Portugal",         "POR", 1),
    League("A1",  "oebuli",    "Österreich Bundesliga", "AUT", 1),

    # ---------------------------------------------------------------
    # Deutscher Unterbau. Bewusst weniger tief ausgewertet: ab der
    # Oberliga fuehrt Transfermarkt keine Marktwerte mehr, daher entfaellt
    # dort der Unterbewertet-Index. Einsaetze, Tore, Vorlagen und Minuten
    # sind dagegen bis in die 5. Liga vorhanden und werden voll genutzt.
    # ---------------------------------------------------------------
    League("L3",   "l3",       "3. Liga",               "GER", 3),

    # 4. Liga - fuenf Staffeln, jede ist eine eigene Vergleichsgruppe
    League("RLN3", "rl-nord",  "Regionalliga Nord",     "GER", 4),
    League("RLN4", "rl-nordost", "Regionalliga Nordost", "GER", 4),
    League("RLW3", "rl-west",  "Regionalliga West",     "GER", 4),
    League("RLSW", "rl-suedwest", "Regionalliga Südwest", "GER", 4),
    League("RLB3", "rl-bayern", "Regionalliga Bayern",  "GER", 4),

    # 5. Liga - vierzehn Staffeln
    League("OBLF", "ol-nord",      "NOFV-Oberliga Nord",        "GER", 5),
    League("OBLG", "ol-sued",      "NOFV-Oberliga Süd",         "GER", 5),
    League("OBLN", "ol-nds",       "Oberliga Niedersachsen",    "GER", 5),
    League("OBLJ", "ol-hamburg",   "Oberliga Hamburg",          "GER", 5),
    League("OBLK", "ol-bremen",    "Bremenliga",                "GER", 5),
    League("OBLL", "ol-sh",        "Oberliga Schleswig-Holst.", "GER", 5),
    League("OLW3", "ol-westfalen", "Oberliga Westfalen",        "GER", 5),
    League("OLNI", "ol-niederrhein", "Oberliga Niederrhein",    "GER", 5),
    League("OLMR", "ol-mittelrhein", "Mittelrheinliga",         "GER", 5),
    League("OBLC", "ol-hessen",    "Hessenliga",                "GER", 5),
    League("OLRP", "ol-rps",       "Oberliga Rheinland-Pf./Saar", "GER", 5),
    League("OBLB", "ol-bw",        "Oberliga Baden-Württemberg", "GER", 5),
    League("OLB1", "ol-bayern-n",  "Bayernliga Nord",           "GER", 5),
    League("OLB2", "ol-bayern-s",  "Bayernliga Süd",            "GER", 5),
]


def nach_stufe(stufe: int) -> list[League]:
    return [lg for lg in LEAGUES if lg.stufe == stufe]


def by_frontend_id(fid: str) -> League | None:
    for lg in LEAGUES:
        if lg.frontend_id == fid:
            return lg
    return None
