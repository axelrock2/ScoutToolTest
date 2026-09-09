#!/usr/bin/env python3
"""Holt die Adressen der Spielerportraits von Transfermarkt.

Warum ein eigener Lauf? Die Bildadresse traegt einen Zeitstempel:

    https://img.a.transfermarkt.technology/portrait/medium/607720-1737037032.jpg

Ohne ihn antwortet der Server mit 404 - aus der Spieler-ID allein laesst
sich die Adresse also nicht bilden. Gefuehrt wird sie in der SCHLICHTEN
Kaderansicht (/kader/verein/<id>, ohne /plus/1), und dort im Attribut
data-src, weil Transfermarkt die Bilder nachlaedt. Die ausfuehrliche
Ansicht, die build_players.py ohnehin abruft, enthaelt sie nicht.

Ein Abruf je Verein - rund 620 statt 17000, wie es ein Weg ueber die
Spielerprofile waere.

    python3 scripts/bilder.py                  # alle Vereine
    python3 scripts/bilder.py --ligen buli
    python3 scripts/bilder.py --erneuern       # auch schon geholte neu

Danach compute_grades.py laufen lassen.

Gespeichert wird nur der veraenderliche Teil des Dateinamens, also
Zeitstempel und Endung ("1701639955.png"): die Spieler-ID steht ohnehin im
Datensatz, und der unveraenderte Teil gehoert einmal in die Ausgabedatei
statt neuntausendmal. Die Endung MUSS mit - etwa ein Fuenftel der
Portraits sind PNG.

Grenzen, die dazugehoeren
-------------------------
  * Nur der HEUTIGE Kader. Wer den Verein verlassen hat, steht dort nicht
    mehr; sein Bild gaebe es nur ueber die Profilseite, also ein Abruf je
    Spieler - Stunden statt Minuten. Diese Spieler behalten ihre
    Initialen.
  * Wo Transfermarkt kein Bild hat, liefert es "default.jpg". Dieser
    Platzhalter wird verworfen - eine graue Silhouette sagt weniger als
    die Initialen.
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

from leagues import LEAGUES                          # noqa: E402
from tm_client import fetch                          # noqa: E402

BESTAND = os.path.join(os.path.dirname(__file__), "..", "data",
                       "players_raw.json.gz")
BUDGET_MIN = float(os.environ.get("SCOUT_BUDGET_MIN", "0")) or None

# Aus Zeitstempel und Spieler-ID entsteht die Adresse wieder. Steht auch
# in der Ausgabedatei, damit das Frontend sie nicht fest verdrahtet.
BILD_BASIS = "https://img.a.transfermarkt.technology/portrait/medium/"

# Die Endung gehoert dazu: rund ein Fuenftel der Portraits sind PNG, nicht
# JPG. Sie wegzulassen und im Frontend ".jpg" anzuhaengen hiess, dass jeder
# fuenfte Spieler kein Bild bekam (aufgefallen an Cheick Souare).
_PORTRAIT = re.compile(r"/portrait/[^/]+/(\d+)-(\d+\.(?:jpg|png|webp))")


def portraits(verein_id: str) -> dict[str, str]:
    """{spieler_id: "<zeitstempel>.<endung>"} aus der schlichten Kaderansicht."""
    page = fetch(f"/x/kader/verein/{verein_id}")
    out: dict[str, str] = {}
    for attr in ("data-src", "src"):
        for wert in page.css(f"img::attr({attr})"):
            m = _PORTRAIT.search(str(wert))
            if m:
                out.setdefault(m.group(1), m.group(2))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ligen", default="", help="nur diese frontend_ids")
    ap.add_argument("--max-vereine", type=int, default=0,
                    help="hoechstens so viele Vereine (zum Testen)")
    ap.add_argument("--erneuern", action="store_true",
                    help="auch Vereine erneut abrufen, die schon Bilder haben")
    args = ap.parse_args()

    if not os.path.exists(BESTAND):
        print(f"{BESTAND} fehlt - zuerst sammeln.", file=sys.stderr)
        return 1
    with gzip.open(BESTAND, "rt", encoding="utf-8") as fh:
        bestand = json.load(fh)

    erlaubt = None
    if args.ligen:
        erlaubt = {x.strip() for x in args.ligen.split(",") if x.strip()}
        unbekannt = erlaubt - {lg.frontend_id for lg in LEAGUES}
        if unbekannt:
            print(f"Unbekannte Ligen: {', '.join(sorted(unbekannt))}",
                  file=sys.stderr)
            return 1

    vereine: dict[str, tuple[str, str]] = {}       # vid -> (name, liga_id)
    for sp in bestand["spieler"]:
        if erlaubt and sp["liga_id"] not in erlaubt:
            continue
        vereine.setdefault(sp["verein_id"], (sp["verein"], sp["liga_id"]))

    if not args.erneuern:
        # Ein Verein gilt als erledigt, sobald irgendein Kaderspieler von
        # ihm ein Bild traegt. Genauer ginge es nur mit einem eigenen
        # Vermerk - fuer Bilder waere das uebertrieben: fehlt eines,
        # stehen dort Initialen, kein falscher Wert.
        fertig = {sp["verein_id"] for sp in bestand["spieler"]
                  if sp.get("bild")}
        vereine = {v: d for v, d in vereine.items() if v not in fertig}

    offen = sorted(vereine.items(), key=lambda x: x[1][1])
    if args.max_vereine:
        offen = offen[:args.max_vereine]

    print(f"{len(offen)} Vereine abzurufen.", file=sys.stderr)

    start = time.time()
    gefunden: dict[str, str] = {}       # spieler_id -> "<stempel>.<endung>"
    vereine_ok = fehler = 0
    for vid, (name, _liga) in offen:
        if BUDGET_MIN and (time.time() - start) / 60 > BUDGET_MIN:
            print(f"  Zeitbudget von {BUDGET_MIN:.0f} min erreicht.",
                  file=sys.stderr)
            break
        try:
            gefunden.update(portraits(vid))
            vereine_ok += 1
            if vereine_ok % 50 == 0:
                print(f"  {vereine_ok} Vereine, {len(gefunden)} Bilder ...",
                      file=sys.stderr)
        except Exception as exc:
            fehler += 1
            if fehler <= 8:
                print(f"  [!] {name}: {str(exc)[:70]}", file=sys.stderr)

    if not gefunden:
        print("Nichts geholt - Bestand bleibt unangetastet.", file=sys.stderr)
        return 0

    gesetzt = 0
    for sp in bestand["spieler"]:
        ts = gefunden.get(str(sp["id"]))
        if ts and sp.get("bild") != ts:
            sp["bild"] = ts
            gesetzt += 1

    bestand["bild_basis"] = BILD_BASIS
    bestand["stand"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with gzip.open(BESTAND, "wt", encoding="utf-8") as fh:
        json.dump(bestand, fh, ensure_ascii=False, separators=(",", ":"))
    print(f"\n{vereine_ok} Vereine abgerufen, {len(gefunden)} Portraits, "
          f"{gesetzt} Spielern zugeordnet ({fehler} Fehler).\n"
          f"Danach compute_grades.py laufen lassen.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
