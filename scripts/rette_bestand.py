#!/usr/bin/env python3
"""Traegt Verletzungs-, Vertrags- und xG-Daten aus einer Sicherung nach.

Notfallwerkzeug. Gebraucht wird es, wenn ein Volllauf von build_players.py
mit der alten Fassung gelaufen ist: sammle() baut jeden Datensatz neu auf
und kannte nur die Felder der Kader- und Leistungsseite, alles spaeter
Hinzugekommene fiel weg. Seit dem Rettungsblock in build_players.py
passiert das nicht mehr - fuer bereits entstandene Luecken bleibt dieses
Skript.

    python3 scripts/rette_bestand.py sicherung.json.gz
    python3 scripts/rette_bestand.py sicherung.json.gz --probe   # nur zaehlen

Zugeordnet wird ueber die Spieler-ID. Vorhandene Felder werden NICHT
ueberschrieben - was der neue Lauf selbst geholt hat, ist aktueller.
"""

from __future__ import annotations

import argparse
import gzip
import json
import os
import sys
from datetime import datetime, timezone

ZIEL = os.path.join(os.path.dirname(__file__), "..", "data",
                    "players_raw.json.gz")

# nicht_mehr_im_kader fehlt hier bewusst: der Vermerk gilt fuer einen
# Stichtag und wird von build_players.py --kader-aktuell neu gesetzt.
FELDER = ("verletzungen", "vertrag", "vertrag_scan", "xg")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("sicherung", help="players_raw.json.gz aus der Sicherung")
    ap.add_argument("--probe", action="store_true",
                    help="nur zeigen, was nachgetragen wuerde")
    args = ap.parse_args()

    for pfad in (args.sicherung, ZIEL):
        if not os.path.exists(pfad):
            print(f"{pfad} fehlt.", file=sys.stderr)
            return 1

    with gzip.open(args.sicherung, "rt", encoding="utf-8") as fh:
        sicherung = json.load(fh)
    with gzip.open(ZIEL, "rt", encoding="utf-8") as fh:
        bestand = json.load(fh)

    vorrat: dict[str, dict] = {}
    for sp in sicherung["spieler"]:
        habe = {k: sp[k] for k in FELDER if sp.get(k)}
        if habe:
            vorrat.setdefault(str(sp.get("id")), {}).update(habe)

    je_feld = {k: 0 for k in FELDER}
    spieler = 0
    for sp in bestand["spieler"]:
        habe = vorrat.get(str(sp.get("id")))
        if not habe:
            continue
        neu = False
        for k, v in habe.items():
            if not sp.get(k):
                sp[k] = v
                je_feld[k] += 1
                neu = True
        if neu:
            spieler += 1

    uebersicht = ", ".join(f"{k} {v}" for k, v in je_feld.items() if v)
    if not spieler:
        print("Nichts nachzutragen - der Bestand ist vollstaendig.",
              file=sys.stderr)
        return 0
    if args.probe:
        print(f"Probe: {spieler} Spieler wuerden ergaenzt ({uebersicht}).",
              file=sys.stderr)
        return 0

    bestand["stand"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with gzip.open(ZIEL, "wt", encoding="utf-8") as fh:
        json.dump(bestand, fh, ensure_ascii=False, separators=(",", ":"))
    print(f"{spieler} Spieler ergaenzt ({uebersicht}).\n"
          f"Danach compute_grades.py laufen lassen.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
