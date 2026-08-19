#!/usr/bin/env python3
"""Holt xG-Daten von Understat und ergaenzt den Bestand.

Understat deckt nur die fuenf grossen ersten Ligen ab. Die Werte fliessen
deshalb NICHT in die Liga-Note ein - sonst waeren Spieler dieser fuenf
Ligen anders bewertet als die uebrigen 28. Sie stehen als Zusatzangabe in
der Spielerakte, klar als solche gekennzeichnet.

Ein Abruf je Liga liefert Spieler und Mannschaften zugleich. Der
Endpunkt braucht die Kopfzeile X-Requested-With, sonst antwortet er mit
404; die normale Ligaseite liefert ohne Browser nur eine Huelle.

    python3 scripts/understat.py
"""

from __future__ import annotations

import gzip
import json
import os
import re
import sys
import unicodedata

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

BESTAND = os.path.join(os.path.dirname(__file__), "..", "data",
                       "players_raw.json.gz")
SAISON = int(os.environ.get("SCOUT_SAISON", "2025"))

# Understat-Liga -> frontend_id in leagues.py
LIGEN = {
    "Bundesliga": "buli",
    "EPL": "pl",
    "La_liga": "laliga",
    "Serie_A": "seriea",
    "Ligue_1": "ligue1",
}


def hole(liga: str, saison: int) -> dict:
    from scrapling.fetchers import Fetcher
    p = Fetcher.get(f"https://understat.com/getLeagueData/{liga}/{saison}",
                    timeout=30, retries=1,
                    headers={"X-Requested-With": "XMLHttpRequest"})
    if p.status != 200:
        raise RuntimeError(f"HTTP {p.status}")
    roh = re.sub(r"^<html><body>|</body></html>$", "",
                 (p.html_content or "").strip())
    return json.loads(roh)


def schluessel(name: str) -> str:
    """Namen vergleichbar machen: ohne Akzente, ohne Zusaetze, klein.

    Understat und Transfermarkt schreiben Namen unterschiedlich
    ('Kevin Vogt' vs 'Kevin Vogt', 'Nico Schlotterbeck' vs 'N. Schlotterbeck').
    Verglichen wird deshalb nur ueber Vor- und Nachnamen ohne Sonderzeichen.
    """
    ohne = unicodedata.normalize("NFKD", name)
    ohne = "".join(c for c in ohne if not unicodedata.combining(c))
    ohne = re.sub(r"[^a-zA-Z ]", " ", ohne).lower()
    teile = [t for t in ohne.split() if len(t) > 1]
    return " ".join(teile)


def main() -> int:
    if not os.path.exists(BESTAND):
        print(f"{BESTAND} fehlt - zuerst sammeln.", file=sys.stderr)
        return 1
    with gzip.open(BESTAND, "rt", encoding="utf-8") as fh:
        bestand = json.load(fh)

    # Bestand nach (liga_id, Namensschluessel) aufschluesseln
    nach_liga: dict[str, dict[str, list]] = {}
    for sp in bestand["spieler"]:
        nach_liga.setdefault(sp.get("liga_id"), {}) \
                 .setdefault(schluessel(sp.get("name", "")), []).append(sp)

    gesamt_treffer = 0
    for uliga, fid in LIGEN.items():
        try:
            daten = hole(uliga, SAISON)
        except Exception as exc:
            print(f"  [X] {uliga}: {exc}", file=sys.stderr)
            continue

        ziel = nach_liga.get(fid, {})
        treffer = 0
        for u in daten.get("players", []):
            k = schluessel(u.get("player_name", ""))
            kandidaten = ziel.get(k)
            if not kandidaten or len(kandidaten) > 1:
                continue          # unbekannt oder nicht eindeutig -> auslassen
            minuten = int(u.get("time") or 0)
            if not minuten:
                continue
            p90 = minuten / 90.0
            kandidaten[0]["xg"] = {
                "xG": round(float(u["xG"]), 2),
                "npxG": round(float(u["npxG"]), 2),
                "xA": round(float(u["xA"]), 2),
                "xG90": round(float(u["xG"]) / p90, 3),
                "xA90": round(float(u["xA"]) / p90, 3),
                "schluesselpaesse90": round(int(u["key_passes"]) / p90, 3),
                "schuesse90": round(int(u["shots"]) / p90, 3),
                "aufbau90": round(float(u["xGBuildup"]) / p90, 3),
                # Tore minus erwartete Tore: trifft er besser als die
                # Chancenqualitaet hergibt?
                "ueber_xg": round(int(u["goals"]) - float(u["xG"]), 2),
                "minuten": minuten,
            }
            treffer += 1

        gesamt_treffer += treffer
        print(f"  [ok] {uliga:12} {treffer:4} von {len(daten.get('players', []))} "
              f"Spielern zugeordnet", file=sys.stderr)

    bestand["xg_quelle"] = "understat.com"
    with gzip.open(BESTAND, "wt", encoding="utf-8") as fh:
        json.dump(bestand, fh, ensure_ascii=False, separators=(",", ":"))
    print(f"\n{gesamt_treffer} Spieler mit xG-Werten versehen", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
