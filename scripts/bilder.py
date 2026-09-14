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
import signal
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
    ap.add_argument("--probe", action="store_true",
                    help="nur zaehlen, wie viele Vereine offen sind")
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

    # Die HEUTIGEN Vereine, sofern bekannt (build_players.py
    # --saison-aktuell) - sonst die der Notensaison. Nur so kommen auch
    # Aufsteiger und Neuzugaenge zu ihrem Bild.
    vereine: dict[str, tuple[str, str]] = {}       # vid -> (name, liga_id)
    if bestand.get("ligen_aktuell"):
        for liga_id, liste in bestand["ligen_aktuell"].items():
            if erlaubt and liga_id not in erlaubt:
                continue
            for e in liste:
                vereine.setdefault(e["id"], (e["name"], liga_id))
    else:
        for sp in bestand["spieler"]:
            if erlaubt and sp["liga_id"] not in erlaubt:
                continue
            vereine.setdefault(sp["verein_id"], (sp["verein"], sp["liga_id"]))

    # Fotoquote je heutigem Verein. Sie entscheidet zweierlei: welche
    # Vereine ohne --erneuern noch abgerufen werden - und in welcher
    # Reihenfolge. Die schwaechsten zuerst: bricht ein Lauf ab (Zeitbudget,
    # HTTP 405), traf es sonst immer dieselben Ligen am Ende der Liste. So
    # blieben die Oberligen bei 16 % stehen, obwohl Transfermarkt etwa fuer
    # Holstein Kiel II 23 von 24 Portraits fuehrt.
    je: dict[str, list[int]] = {}
    for sp in bestand["spieler"]:
        vid = (sp.get("aktuell") or {}).get("verein_id")
        if vid:
            t = je.setdefault(vid, [0, 0])
            t[0] += 1
            t[1] += bool(sp.get("bild"))
    quote = {vid: (b / n if n else 0.0) for vid, (n, b) in je.items()}
    geprueft = bestand.setdefault("bilder_geprueft", {})

    if not args.erneuern:
        # Erledigt ist ein Verein, wenn ihn ein frueherer Lauf schon
        # vollstaendig gesehen hat - dann fehlen die Bilder an der Quelle,
        # nicht bei uns (Heider SV: 16 von 24 ohne Portrait) -, oder wenn
        # ohnehin fast alle seine Spieler eins haben. Vorher galt ein Verein
        # als erledigt, sobald EIN Spieler ein Bild trug.
        vereine = {v: d for v, d in vereine.items()
                   if v not in geprueft and quote.get(v, 0.0) < 0.8}

    offen = sorted(vereine.items(), key=lambda x: (quote.get(x[0], 0.0), x[1][1]))
    if args.max_vereine:
        offen = offen[:args.max_vereine]

    print(f"{len(offen)} Vereine abzurufen.", file=sys.stderr)
    if args.probe:
        return 0

    # Wie in leihvertraege.py: eine Serie von Fehlern heisst Sperre. Dann
    # aufhoeren, statt sie mit weiteren Abrufen zu verlaengern - und das
    # bis dahin Geholte speichern, auch bei einem Abbruch von aussen.
    def _stopp(*_):
        raise KeyboardInterrupt
    signal.signal(signal.SIGTERM, _stopp)

    start = time.time()
    gefunden: dict[str, str] = {}       # spieler_id -> "<stempel>.<endung>"
    vereine_ok = fehler = in_folge = 0
    try:
        for vid, (name, _liga) in offen:
            if BUDGET_MIN and (time.time() - start) / 60 > BUDGET_MIN:
                print(f"  Zeitbudget von {BUDGET_MIN:.0f} min erreicht.",
                      file=sys.stderr)
                break
            try:
                gefunden.update(portraits(vid))
                geprueft[vid] = date.today().isoformat()
                vereine_ok += 1
                in_folge = 0
                if vereine_ok % 50 == 0:
                    print(f"  {vereine_ok} Vereine, {len(gefunden)} Bilder ...",
                          file=sys.stderr)
            except Exception as exc:
                fehler += 1
                in_folge += 1
                if fehler <= 8:
                    print(f"  [!] {name}: {str(exc)[:70]}", file=sys.stderr)
                if in_folge >= 4:
                    print("  4 Fehler in Folge - Transfermarkt sperrt offenbar. "
                          "Abbruch, Bisheriges wird gespeichert.", file=sys.stderr)
                    break
    except KeyboardInterrupt:
        print("  Abgebrochen - Bisheriges wird gespeichert.", file=sys.stderr)

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
