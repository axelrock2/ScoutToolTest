#!/usr/bin/env python3
"""Holt die Verletzungshistorie von Transfermarkt.

Ein Abruf je Spieler - fuer alle 16761 waeren das gut sieben Stunden.
Deshalb nach Note absteigend und in Portionen: wer schon geholt wurde,
wird uebersprungen, der naechste Lauf macht weiter. Ab Note 70 sind es
rund 2200 Spieler, also etwa eine Stunde.

    python3 scripts/verletzungen.py                 # ab Note 70, 600 Stueck
    python3 scripts/verletzungen.py --ab-note 80
    python3 scripts/verletzungen.py --max 2000

Quelle steht im Datensatz: jeder Eintrag traegt "quelle": "transfermarkt".
"""

from __future__ import annotations

import argparse
import gzip
import json
import os
import re
import sys
import time
from datetime import date, datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tm_client import cell_text, fetch                # noqa: E402

BESTAND = os.path.join(os.path.dirname(__file__), "..", "data",
                       "players_raw.json.gz")
NOTEN = os.path.join(os.path.dirname(__file__), "..", "data", "players.json")
BUDGET_MIN = float(os.environ.get("SCOUT_BUDGET_MIN", "0")) or None


def _tage(text: str) -> int | None:
    m = re.search(r"(\d+)", (text or "").replace(".", ""))
    return int(m.group(1)) if m else None


def _datum(text: str) -> str | None:
    m = re.search(r"(\d{2})\.(\d{2})\.(\d{4})", text or "")
    return f"{m.group(3)}-{m.group(2)}-{m.group(1)}" if m else None


def historie(spieler_id: str) -> dict:
    """Verletzungen eines Spielers samt Kennzahlen.

    Die Seite fuehrt zwei Tabellen - die Einzelfaelle und eine Uebersicht
    je Saison. Ausgewertet wird die erste; erkennbar an sechs Spalten.
    """
    page = fetch(f"/x/verletzungen/spieler/{spieler_id}")
    faelle: list[dict] = []
    for row in page.css("table.items > tbody > tr"):
        c = [cell_text(td) for td in row.css("td")]
        if len(c) < 6 or not re.match(r"\d{2}/\d{2}", c[0] or ""):
            continue
        faelle.append({
            "saison": c[0],
            "art": c[1],
            "von": _datum(c[2]),
            "bis": _datum(c[3]),
            "tage": _tage(c[4]),
            "verpasste_spiele": _tage(c[5]) or 0,
        })

    heute = date.today().isoformat()
    letzte_drei = [f for f in faelle
                   if f["von"] and f["von"] >= f"{date.today().year - 3}-01-01"]

    def summe(liste, feld):
        return sum(f[feld] or 0 for f in liste)

    arten: dict[str, int] = {}
    for f in faelle:
        schluessel = (f["art"] or "").strip()
        if schluessel:
            arten[schluessel] = arten.get(schluessel, 0) + 1

    return {
        "quelle": "transfermarkt",
        "geholt": heute,
        "faelle": faelle[:30],                  # aeltestes interessiert selten
        "anzahl": len(faelle),
        "tage_gesamt": summe(faelle, "tage"),
        "spiele_gesamt": summe(faelle, "verpasste_spiele"),
        "anzahl_3j": len(letzte_drei),
        "tage_3j": summe(letzte_drei, "tage"),
        "spiele_3j": summe(letzte_drei, "verpasste_spiele"),
        "haeufigste": sorted(arten.items(), key=lambda x: -x[1])[:3],
        # Kein Enddatum in der obersten Zeile heisst: laeuft noch.
        "aktuell_verletzt": bool(faelle and not faelle[0]["bis"]),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ab-note", type=int, default=70,
                    help="nur Spieler ab dieser Liga-Note (Vorgabe 70)")
    ap.add_argument("--max", type=int, default=600,
                    help="hoechstens so viele je Lauf (Vorgabe 600)")
    ap.add_argument("--erneuern", action="store_true",
                    help="auch bereits geholte noch einmal abrufen")
    args = ap.parse_args()

    for pfad in (BESTAND, NOTEN):
        if not os.path.exists(pfad):
            print(f"{pfad} fehlt - zuerst sammeln und bewerten.", file=sys.stderr)
            return 1

    with open(NOTEN, encoding="utf-8") as fh:
        noten = {str(p["id"]): p["ln"] for p in json.load(fh)["players"]}
    with gzip.open(BESTAND, "rt", encoding="utf-8") as fh:
        bestand = json.load(fh)

    # Nach Note absteigend: die interessanten Spieler zuerst.
    offen = []
    for sp in bestand["spieler"]:
        note = noten.get(str(sp["id"]))
        if note is None or note < args.ab_note:
            continue
        if sp.get("verletzungen") and not args.erneuern:
            continue
        offen.append((note, sp))
    offen.sort(key=lambda x: -x[0])
    offen = offen[:args.max]

    gesamt = sum(1 for sp in bestand["spieler"]
                 if noten.get(str(sp["id"]), 0) >= args.ab_note)
    schon = gesamt - len([1 for sp in bestand["spieler"]
                          if noten.get(str(sp["id"]), 0) >= args.ab_note
                          and not sp.get("verletzungen")])
    print(f"Ab Note {args.ab_note}: {gesamt} Spieler, {schon} bereits geholt. "
          f"Dieser Lauf: {len(offen)}.", file=sys.stderr)

    start = time.time()
    geholt = fehler = 0
    gesehen: dict[str, dict] = {}
    for note, sp in offen:
        if BUDGET_MIN and (time.time() - start) / 60 > BUDGET_MIN:
            print(f"  Zeitbudget von {BUDGET_MIN:.0f} min erreicht.",
                  file=sys.stderr)
            break
        pid = str(sp["id"])
        if pid in gesehen:                       # Doppeleintraege teilen sich
            sp["verletzungen"] = gesehen[pid]
            continue
        try:
            h = historie(pid)
            sp["verletzungen"] = h
            gesehen[pid] = h
            geholt += 1
            if geholt % 100 == 0:
                print(f"  {geholt} geholt ...", file=sys.stderr)
        except Exception as exc:
            fehler += 1
            if fehler <= 5:
                print(f"  [!] {sp.get('name','?')}: {str(exc)[:70]}",
                      file=sys.stderr)

    # Doppeleintraege desselben Spielers mitversorgen
    for sp in bestand["spieler"]:
        pid = str(sp["id"])
        if pid in gesehen and not sp.get("verletzungen"):
            sp["verletzungen"] = gesehen[pid]

    if not geholt:
        print("Nichts geholt - Bestand bleibt unangetastet.", file=sys.stderr)
        return 0

    bestand["stand"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with gzip.open(BESTAND, "wt", encoding="utf-8") as fh:
        json.dump(bestand, fh, ensure_ascii=False, separators=(",", ":"))
    print(f"\n{geholt} Verletzungshistorien geholt ({fehler} Fehler). "
          f"Danach compute_grades.py laufen lassen.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
