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
]


def by_frontend_id(fid: str) -> League | None:
    for lg in LEAGUES:
        if lg.frontend_id == fid:
            return lg
    return None
