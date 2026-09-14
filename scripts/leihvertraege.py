#!/usr/bin/env python3
"""Holt fuer Leihspieler das Vertragsende beim STAMMVEREIN.

Die Kaderansicht verraet nur, dass jemand ausgeliehen ist und wann die
Leihe endet ("Leihspieler von: SK Slavia Prag; Rueckkehr: 31.12.2026").
Wie lange sein Vertrag beim Stammverein laeuft, steht allein auf seiner
Profilseite:

    Vertrag bis:        31.12.2026
    Ausgeliehen von:    SK Slavia Prag
    Vertrag dort bis:   30.06.2030

Fuer Scouting entscheidet genau die letzte Zeile: laeuft der Vertrag dort
im selben Sommer aus wie die Leihe, wird der Spieler tatsaechlich frei -
laeuft er bis 2030, kostet er Abloese.

Ein Abruf je Spieler, deshalb nur fuer Leihspieler (rund 1.100) und mit
Zeitbudget. Wer schon geprueft ist, wird uebersprungen, solange sich die
Leihe nicht geaendert hat.

Transfermarkt sperrt Profilseiten deutlich schneller als Kader- und
Vertragsseiten: beim ersten Lauf kamen nach rund zwanzig Abrufen nur noch
Antworten mit 403. Deshalb pausiert das Skript zwischen den Abrufen
(SCOUT_PAUSE, Vorgabe 3 s), bricht nach mehreren Fehlern in Folge ab und
speichert, was es bis dahin hat - auch bei Abbruch von aussen. Weiter-
zumachen wuerde eine Sperre nur verlaengern, und die traefe dann auch den
naechsten Kaderlauf.

    python3 scripts/leihvertraege.py                 # alle offenen
    python3 scripts/leihvertraege.py --probe --max 5 # nur ansehen
    python3 scripts/leihvertraege.py --erneuern      # auch schon gepruefte

Danach compute_grades.py laufen lassen.
"""

from __future__ import annotations

import argparse
import gzip
import json
import os
import re
import signal
import sys
import time
from datetime import date, datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tm_client import fetch                          # noqa: E402

BESTAND = os.environ.get("SCOUT_TARGET") or os.path.join(
    os.path.dirname(__file__), "..", "data", "players_raw.json.gz")
BUDGET_MIN = float(os.environ.get("SCOUT_BUDGET_MIN", "0")) or None
PAUSE = float(os.environ.get("SCOUT_PAUSE", "3"))
MAX_IN_FOLGE = 4          # so viele Fehler hintereinander -> Sperre, Abbruch

# <span …--regular>Vertrag dort bis:</span> <span …--bold>30.06.2030</span>
_DORT_BIS = re.compile(
    r"Vertrag dort bis:\s*</span>\s*<span[^>]*>\s*(\d{2}\.\d{2}\.\d{4})\s*</span>")
_VON = re.compile(
    r"Ausgeliehen von:\s*</span>\s*<span[^>]*>\s*<a[^>]*title=\"([^\"]+)\"")


def iso(tag: str) -> str:
    t, m, j = tag.split(".")
    return f"{j}-{m}-{t}"


def stammvertrag(spieler_id: str) -> dict:
    """{'bis': ISO|None, 'von': Verein|None} von der Profilseite.

    'bis' None heisst: die Seite fuehrt keine Zeile "Vertrag dort bis" -
    etwa, weil die Leihe inzwischen in einen festen Wechsel uebergegangen
    ist. Das ist eine Auskunft, kein Fehler; ein fehlgeschlagener Abruf
    wirft dagegen.
    """
    h = fetch(f"/x/profil/spieler/{spieler_id}").html_content or ""
    if "info-table" not in h:
        raise RuntimeError("keine Profilseite erhalten")
    m = _DORT_BIS.search(h)
    v = _VON.search(h)
    return {"bis": iso(m.group(1)) if m else None,
            "von": v.group(1) if v else None}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max", type=int, default=0, help="hoechstens so viele Spieler")
    ap.add_argument("--probe", action="store_true", help="nur anzeigen, nichts schreiben")
    ap.add_argument("--erneuern", action="store_true",
                    help="auch Spieler abrufen, die schon geprueft sind")
    args = ap.parse_args()

    with gzip.open(BESTAND, "rt", encoding="utf-8") as fh:
        bestand = json.load(fh)

    offen = [s for s in bestand["spieler"]
             if s.get("leihe") and s.get("aktuell")
             and (args.erneuern or "stammvertrag_geprueft" not in s["leihe"])]
    if args.max:
        offen = offen[:args.max]
    print(f"{len(offen)} Leihspieler abzurufen.", file=sys.stderr)

    # Abbruch von aussen (kill, Strg-C) wie ein regulaeres Ende behandeln:
    # das bis dahin Geholte wird gespeichert, statt verloren zu gehen.
    def _stopp(*_):
        raise KeyboardInterrupt
    signal.signal(signal.SIGTERM, _stopp)

    start = time.time()
    ok = ohne = fehler = in_folge = 0
    try:
        for i, s in enumerate(offen):
            if BUDGET_MIN and (time.time() - start) / 60 > BUDGET_MIN:
                print("  Zeitbudget erreicht - der Rest folgt beim naechsten Lauf.",
                      file=sys.stderr)
                break
            if i:
                time.sleep(PAUSE)
            try:
                r = stammvertrag(str(s["id"]))
            except Exception as exc:
                fehler += 1
                in_folge += 1
                if fehler <= 8:
                    print(f"  [!] {s['name']}: {str(exc)[:70]}", file=sys.stderr)
                if in_folge >= MAX_IN_FOLGE:
                    print(f"  {in_folge} Fehler in Folge - Transfermarkt sperrt "
                          f"offenbar. Abbruch, Bisheriges wird gespeichert.",
                          file=sys.stderr)
                    break
                continue
            in_folge = 0
            if args.probe:
                print(f"  {s['name']:28s} Leihe von {s['leihe'].get('von')} bis "
                      f"{s['leihe'].get('bis')} | Profil: von {r['von']}, "
                      f"Vertrag dort bis {r['bis']}", file=sys.stderr)
            s["leihe"]["stammvertrag_bis"] = r["bis"]
            s["leihe"]["stammvertrag_geprueft"] = date.today().isoformat()
            if r["bis"]:
                ok += 1
            else:
                ohne += 1
    except KeyboardInterrupt:
        print("  Abgebrochen - Bisheriges wird gespeichert.", file=sys.stderr)

    print(f"\n{ok} mit Vertragsende beim Stammverein, {ohne} ohne Angabe, "
          f"{fehler} Fehler.", file=sys.stderr)
    if args.probe or not (ok or ohne):
        print("Nichts geschrieben.", file=sys.stderr)
        return 0
    bestand["stand"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with gzip.open(BESTAND, "wt", encoding="utf-8") as fh:
        json.dump(bestand, fh, ensure_ascii=False, separators=(",", ":"))
    print("Gespeichert. Danach compute_grades.py laufen lassen.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
