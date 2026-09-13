#!/usr/bin/env python3
"""Rechnet die Sofascore-Werte gegen FotMob (Opta) nach.

Warum das hier steht
--------------------
Sofascore ist als Quelle umstritten. Der Vorwurf trifft zwei verschiedene
Dinge, die auseinandergehalten gehoeren:

  * Die Sofascore-NOTE (6,0 bis 10,0) ist eine eigene Rechenvorschrift,
    die der Anbieter nicht offenlegt. Sie wird hier nicht verwendet.
  * Die ZAEHLWERTE - Paesse, Zweikaempfe, Tacklings - stammen aus
    derselben Erfassung wie bei den grossen Anbietern. Ob das stimmt,
    laesst sich pruefen, statt es zu glauben. Genau das tut dieses Skript.

FotMob veroeffentlicht seine Ligastatistik als offene JSON-Datei und
bezieht sie von Opta. Verglichen werden dieselben Spieler, dieselbe
Saison, dieselben Kennzahlen - je Kennzahl Korrelation, mittlere
Abweichung und der groesste Einzelausreisser.

Das Ergebnis wandert in den Bestand und von dort in die Datenherkunft
auf der Seite. Es ist damit nachlesbar und nicht bloss eine Zusage.

    python3 scripts/gegenprobe.py
    python3 scripts/gegenprobe.py --ligen buli,pl

Warum nicht gleich FotMob als Quelle? Zwei Gruende, beide gemessen:
je Kennzahl ein eigener Abruf statt aller in einem, und die Listen sind
unvollstaendig - bei den Tacklings standen 286 Spieler in der Liste,
obwohl 385 die Mindestspielzeit erreichten. Fuer Percentile waere das
gefaehrlich, fuer eine Gegenprobe ist es unerheblich: verglichen wird
nur, wer in beiden Listen steht.
"""

from __future__ import annotations

import argparse
import gzip
import json
import math
import os
import re
import sys
import time
from datetime import date, datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from leagues import LEAGUES                                    # noqa: E402
from sofascore import schluessel, verein_passt                 # noqa: E402

BESTAND = os.environ.get("SCOUT_TARGET") or os.path.join(
    os.path.dirname(__file__), "..", "data", "players_raw.json.gz")
PAUSE = float(os.environ.get("FOTMOB_DELAY", "1.0"))

# frontend_id -> (FotMob-Liga-ID, Pfadname). Der Pfadname ist FotMob
# gleichgueltig, er steht nur der Lesbarkeit halber da.
LIGEN = {
    "buli":    (54, "bundesliga"),
    "pl":      (47, "premier-league"),
    "seriea":  (55, "serie-a"),
    "laliga":  (87, "laliga"),
    "ligue1":  (53, "ligue-1"),
}
VORGABE = ["buli", "pl", "seriea"]

# FotMob-Statistik -> (Sofascore-Kurzname, Anzeigename)
#
# Ausgewaehlt sind Kennzahlen, die beide Anbieter gleich definieren.
# Weggelassen ist alles, wo schon die Definition abweicht (etwa
# "Zweikaempfe": FotMob fuehrt sie auf Ligaebene gar nicht).
KENNZAHLEN = {
    "mins_played":        ("min",  "Einsatzminuten"),
    "goals":              ("tore", "Tore"),
    "goal_assist":        ("vorl", "Vorlagen"),
    "expected_goals":     ("xg",   "xG"),
    "total_tackle":       ("tkl",  "Tacklings"),
    "interception":       ("int",  "Interceptions"),
    "effective_clearance": ("klr", "Klärungen"),
    "accurate_pass":      ("pa",   "angekommene Pässe"),
    "won_contest":        ("dr",   "gewonnene Dribblings"),
    "big_chance_created": ("gck",  "herausgespielte Großchancen"),
    "saves":              ("par",  "Paraden"),
    "fouls":              ("fo",   "Fouls"),
}

_letzter = 0.0


def hol(url: str):
    global _letzter
    from scrapling.fetchers import Fetcher
    warte = PAUSE - (time.time() - _letzter)
    if warte > 0:
        time.sleep(warte)
    _letzter = time.time()
    p = Fetcher.get(url, timeout=30, retries=1, stealthy_headers=True)
    if p.status != 200:
        raise RuntimeError(f"HTTP {p.status}")
    return p.html_content or ""


def saison_id(liga_id: int, pfad: str, saison: str) -> int | None:
    """FotMob-Saison-ID zur Saison '2025-2026'.

    Sie steht nur in der Seite, nicht in einer Liste: die Statistikdateien
    liegen unter /stats/<liga>/season/<id>/<kennzahl>.json, und die Seite
    verlinkt sie. Wichtig ist der Parameter ?season= - ohne ihn kommt die
    LAUFENDE Saison, und verglichen wuerden drei Spieltage gegen
    vierunddreissig.
    """
    h = hol(f"https://www.fotmob.com/leagues/{liga_id}/stats/{pfad}"
            f"?season={saison}")
    ids = set(re.findall(rf"/stats/{liga_id}/season/(\d+)", h))
    return int(ids.pop()) if len(ids) == 1 else None


def liste(liga_id: int, sid: int, stat: str) -> tuple[str, list[dict]]:
    t = hol(f"https://data.fotmob.com/stats/{liga_id}/season/{sid}/{stat}.json")
    d = json.JSONDecoder().raw_decode(t[t.index("{"):])[0]
    tl = (d.get("TopLists") or [{}])[0]
    return str(tl.get("Title") or ""), list(tl.get("StatList") or [])


# Verglichen wird nur, wer beiderseits genug gespielt hat. Grund: ein
# Spieler mit vier Einsatzminuten und einer Vorlage steht mit 22,5
# Vorlagen je 90 in der Liste. Weichen die Minutenangaben dann um sechs
# Minuten voneinander ab, ergibt das eine "Abweichung" von 13,5 - die
# nichts ueber die Datenqualitaet sagt, sondern ueber die Division.
MIN_MINUTEN = 450


def art_der_liste(titel: str, eintraege: list[dict]) -> tuple[str, float]:
    """('p90'|'summe', Toleranz).

    FotMob rundet, wir nicht. Bei den "per 90"-Listen auf EINE Stelle
    (3,7113 steht dort als 3,7), bei Werten wie xG auf zwei. Die Toleranz
    haelt fest, was reine Rundung ist und was ein echter Unterschied
    waere; ganzzahlige Listen (Tore, Vorlagen, Paesse) vertragen keine.
    """
    art = "p90" if "per 90" in titel.lower() else "summe"
    ganz = all(float(e.get("StatValue") or 0).is_integer() for e in eintraege)
    return art, (0.0 if ganz else 0.05)


def korrelation(paare: list[tuple[float, float]]) -> float | None:
    n = len(paare)
    if n < 10:
        return None
    sx = sum(a for a, _ in paare) / n
    sy = sum(b for _, b in paare) / n
    zx = math.sqrt(sum((a - sx) ** 2 for a, _ in paare))
    zy = math.sqrt(sum((b - sy) ** 2 for _, b in paare))
    if zx == 0 or zy == 0:
        return None
    oben = sum((a - sx) * (b - sy) for a, b in paare)
    return oben / (zx * zy)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ligen", default="", help="frontend_ids, Vorgabe: "
                                                + ",".join(VORGABE))
    args = ap.parse_args()

    if not os.path.exists(BESTAND):
        print(f"{BESTAND} fehlt - zuerst sammeln.", file=sys.stderr)
        return 1
    with gzip.open(BESTAND, "rt", encoding="utf-8") as fh:
        bestand = json.load(fh)

    saison = str(bestand.get("saison") or "2025/26")          # "2025/26"
    fm_saison = "20" + saison[2:4] + "-20" + saison[-2:] \
        if len(saison) == 7 else saison.replace("/", "-")     # "2025-2026"

    ligen = [x.strip() for x in args.ligen.split(",") if x.strip()] or VORGABE
    ligen = [x for x in ligen if x in LIGEN]
    namen = {lg.frontend_id: lg.name for lg in LEAGUES}

    # Bestand nach Liga der Notensaison und Namensschluessel
    nach_liga: dict[str, dict[str, list]] = {}
    for sp in bestand["spieler"]:
        if sp.get("sofa"):
            nach_liga.setdefault(sp["liga_id"], {}) \
                     .setdefault(schluessel(sp.get("name", "")), []).append(sp)

    # je Kennzahl alle Wertepaare ueber alle geprueften Ligen
    paare: dict[str, list] = {k: [] for k in KENNZAHLEN}
    toleranzen: dict[str, float] = {}
    grundlagen: dict[str, str] = {}
    geprueft: list[str] = []
    for fid in ligen:
        liga_id, pfad = LIGEN[fid]
        try:
            sid = saison_id(liga_id, pfad, fm_saison)
            if not sid:
                print(f"  [X] {namen[fid]}: keine Saison {fm_saison}",
                      file=sys.stderr)
                continue
        except Exception as exc:
            print(f"  [X] {namen[fid]}: {exc}", file=sys.stderr)
            continue
        ziel = nach_liga.get(fid, {})
        treffer_liga = 0
        for stat, (kurz, _anzeige) in KENNZAHLEN.items():
            try:
                titel, eintraege = liste(liga_id, sid, stat)
            except Exception as exc:
                print(f"  [!] {namen[fid]}/{stat}: {exc}", file=sys.stderr)
                continue
            art, toleranz = art_der_liste(titel, eintraege)
            toleranzen[stat] = toleranz
            grundlagen[stat] = ("je 90 Minuten" if art == "p90"
                                else "Saisonsumme")
            for e in eintraege:
                kandidaten = ziel.get(schluessel(e.get("ParticipantName", "")))
                if not kandidaten:
                    continue
                if len({k["id"] for k in kandidaten}) > 1:
                    team = e.get("TeamName") or ""
                    kandidaten = [k for k in kandidaten
                                  if verein_passt(k["verein"], team)]
                    if len({k["id"] for k in kandidaten}) != 1:
                        continue
                sofa = kandidaten[0]["sofa"]
                if kurz not in sofa:
                    continue
                minuten = float(e.get("MinutesPlayed") or 0)
                if minuten < MIN_MINUTEN or float(sofa["min"]) < MIN_MINUTEN:
                    continue
                wert = float(e.get("StatValue") or 0)
                if art == "p90":
                    # FotMob rechnet schon um; wir mit unserer eigenen
                    # Minutenzahl, sonst schlaege ein Minutenunterschied
                    # als Abweichung der Kennzahl durch.
                    a = float(sofa[kurz]) * 90.0 / float(sofa["min"])
                    b = wert
                else:
                    a, b = float(sofa[kurz]), wert
                paare[stat].append((a, b, kandidaten[0]["name"]))
                treffer_liga += 1
        geprueft.append(namen[fid])
        print(f"  [ok] {namen[fid]:24s} {treffer_liga:5d} Wertepaare",
              file=sys.stderr)

    ergebnis = []
    for stat, (kurz, anzeige) in KENNZAHLEN.items():
        p = paare[stat]
        if len(p) < 10:
            continue
        r = korrelation([(a, b) for a, b, _ in p])
        abw = [abs(a - b) for a, b, _ in p]
        groesster = max(p, key=lambda x: abs(x[0] - x[1]))
        # Anteil der Paare, die im Rahmen der Rundung uebereinstimmen -
        # aussagekraeftiger als ein Mittelwert, den einzelne Ausreisser
        # verschieben. Bei ganzzahligen Listen heisst das: auf den Wert
        # genau gleich.
        # Toleranz: FotMobs Rundung plus ein Prozent. Das Prozent steht
        # dafuer, dass beide Anbieter die Einsatzminuten leicht
        # unterschiedlich zaehlen - bei 96 Paessen je 90 Minuten macht ein
        # Unterschied von 15 Minuten schon 0,3 Paesse aus, ohne dass ein
        # einziger Pass anders gezaehlt waere.
        tol = toleranzen.get(stat, 0.0)
        genau = sum(1 for a, b, _ in p
                    if abs(a - b) <= tol + 0.01 * max(abs(a), abs(b)) + 1e-9)
        mittel = sum(abs(a) for a, _, _ in p) / len(p)
        ergebnis.append({
            "kennzahl": anzeige,
            "grundlage": grundlagen.get(stat, ""),
            "n": len(p),
            "r": round(r, 4) if r is not None else None,
            "abweichung": round(sum(abw) / len(abw), 3),
            # Die aussagekraeftigste Zahl: mittlere Abweichung im
            # Verhaeltnis zur Groesse der Kennzahl. 0,2 Paesse sind bei 96
            # etwas anderes als 0,2 Tacklings bei 1,5.
            "abweichung_prozent": round(100.0 * (sum(abw) / len(abw)) / mittel, 2)
                                  if mittel else None,
            "gleich_anteil": round(100.0 * genau / len(p), 1),
            "groesste_abweichung": round(abs(groesster[0] - groesster[1]), 2),
            "groesste_bei": groesster[2],
        })

    if not ergebnis:
        print("Keine vergleichbaren Werte - Bestand bleibt unangetastet.",
              file=sys.stderr)
        return 0

    rs = [e["r"] for e in ergebnis if e["r"] is not None]
    schwaechste = min(ergebnis, key=lambda e: e["r"] if e["r"] is not None else 2)
    bestand["gegenprobe"] = {
        "stand": date.today().isoformat(),
        "mindestminuten": MIN_MINUTEN,
        "gegen": "FotMob (Datenbasis Opta)",
        "saison": saison,
        "ligen": geprueft,
        "paare": sum(e["n"] for e in ergebnis),
        "r_min": round(min(rs), 4) if rs else None,
        "r_mittel": round(sum(rs) / len(rs), 4) if rs else None,
        "schwaechste": schwaechste["kennzahl"],
        "kennzahlen": ergebnis,
    }
    bestand["stand"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with gzip.open(BESTAND, "wt", encoding="utf-8") as fh:
        json.dump(bestand, fh, ensure_ascii=False, separators=(",", ":"))

    print(f"\n{'Kennzahl':30s} {'Grundlage':14s} {'n':>5s} {'r':>7s} "
          f"{'Ø-Abw':>8s} {'Ø-Abw%':>7s} {'einig':>7s}  groesste Abweichung",
          file=sys.stderr)
    for e in ergebnis:
        print(f"{e['kennzahl']:30s} {e['grundlage']:14s} {e['n']:5d} "
              f"{(e['r'] if e['r'] is not None else 0):7.4f} "
              f"{e['abweichung']:8.3f} "
              f"{(e['abweichung_prozent'] or 0):6.2f}% "
              f"{e['gleich_anteil']:6.1f}%  "
              f"{e['groesste_abweichung']} ({e['groesste_bei']})",
              file=sys.stderr)
    print(f"\nGegenprobe gespeichert. Danach compute_grades.py laufen lassen.",
          file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
