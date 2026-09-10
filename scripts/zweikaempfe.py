#!/usr/bin/env python3
"""Holt Zweikampfquoten der Notensaison von Sofascore.

Warum Sofascore? Individuelle Defensivwerte fehlten dem Werkzeug bisher
ganz - der Grund, weshalb Innenverteidiger nur ueber Mannschaftswerte zu
bewerten waren. Geprueft wurden:

    OneFootball   fuehrt keine individuellen Zweikampfwerte
    FBref, kicker sperren automatisierte Abrufe (403)
    FotMob        66 Kennzahlen je Liga, aber Zweikaempfe nur je Spielerseite
    Sofascore     antwortet, sobald die Anfrage die Kopfzeilen der eigenen
                  Seite traegt - und liefert die Werte gesammelt je Liga

Ein Abruf liefert 100 Spieler einer Liga mit frei waehlbaren Feldern, also
rund fuenf Abrufe je Liga statt eines je Spieler.

    python3 scripts/zweikaempfe.py                 # alle abgedeckten Ligen
    python3 scripts/zweikaempfe.py --ligen buli

Danach compute_grades.py laufen lassen.

Abdeckung: alle ersten und zweiten Ligen sowie die 3. Liga. Fuer die
Regional- und Oberligen fuehrt Sofascore keine Spielerstatistik - dort
bleibt das Feld leer, statt geschaetzt zu werden.
"""

from __future__ import annotations

import argparse
import gzip
import json
import os
import re
import sys
import time
import unicodedata
from datetime import date, datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from leagues import LEAGUES                          # noqa: E402

BESTAND = os.environ.get("SCOUT_TARGET") or os.path.join(
    os.path.dirname(__file__), "..", "data", "players_raw.json.gz")
BASIS = "https://www.sofascore.com/api/v1"
# Ohne diese Kopfzeilen antwortet die Schnittstelle mit 403 - auch einem
# echten Browser gegenueber. Sie erwartet Anfragen von der eigenen Seite.
KOPF = {"Referer": "https://www.sofascore.com/",
        "Origin": "https://www.sofascore.com",
        "Accept": "application/json, text/plain, */*"}
PAUSE = float(os.environ.get("SOFA_DELAY", "1.5"))

# frontend_id -> Sofascore unique-tournament-id (aus den Laenderlisten)
TURNIERE = {
    "buli": 35, "buli2": 44, "l3": 491,
    "pl": 17, "champ": 18,
    "laliga": 8, "laliga2": 54,
    "seriea": 23, "serieb": 53,
    "ligue1": 34, "ligue2": 182,
    "jupiler": 38, "primeira": 238, "oebuli": 45,
    "ekstraklasa": 202, "chance-liga": 172,
}

FELDER = ("minutesPlayed,appearances,totalDuelsWon,totalDuelsWonPercentage,"
          "groundDuelsWon,groundDuelsWonPercentage,aerialDuelsWon,"
          "aerialDuelsWonPercentage,tackles,interceptions")

_letzter = 0.0


def hol(pfad: str) -> dict:
    """JSON von Sofascore; wirft bei allem ausser 200."""
    global _letzter
    from scrapling.fetchers import Fetcher
    warte = PAUSE - (time.time() - _letzter)
    if warte > 0:
        time.sleep(warte)
    _letzter = time.time()
    p = Fetcher.get(BASIS + pfad, headers=KOPF, timeout=25, retries=1,
                    stealthy_headers=True)
    if p.status != 200:
        raise RuntimeError(f"HTTP {p.status}")
    t = p.html_content
    # Die Antwort traegt hinter dem JSON gelegentlich ein Anhaengsel;
    # raw_decode liest nur das eigentliche Objekt.
    return json.JSONDecoder().raw_decode(t[t.index("{"):])[0]


def saison_id(turnier: int, jahr: str) -> int | None:
    """Sofascore-Saison zum Kurzjahr '25/26' (manche Ligen: '2025/2026')."""
    lang = "20" + jahr[:2] + "/20" + jahr[3:]
    for s in hol(f"/unique-tournament/{turnier}/seasons").get("seasons", []):
        if str(s.get("year")) in (jahr, lang):
            return s["id"]
    return None


def liga_werte(turnier: int, saison: int) -> list[dict]:
    """Alle Spieler der Liga mit Einsatzzeit, seitenweise zu je 100."""
    out, seite = [], 0
    while True:
        d = hol(f"/unique-tournament/{turnier}/season/{saison}/statistics"
                f"?limit=100&offset={seite * 100}&order=-minutesPlayed"
                f"&accumulation=total&fields={FELDER}")
        out.extend(d.get("results", []))
        seite += 1
        if seite >= int(d.get("pages") or 1):
            return out


# Buchstaben, die NFKD nicht zerlegt - "Dzwigala" kam sonst als "dzwiga a"
# heraus und fand seinen Transfermarkt-Namen nicht.
_UMSCHRIFT = str.maketrans({"ł": "l", "Ł": "L", "ø": "o", "Ø": "O", "æ": "ae",
                            "Æ": "Ae", "ß": "ss", "đ": "d", "Đ": "D", "ı": "i",
                            "þ": "th", "Þ": "Th", "ð": "d", "Ð": "D", "œ": "oe",
                            "Œ": "Oe"})


def schluessel(name: str) -> str:
    """Wie in understat.py: ohne Akzente und Zusaetze, klein."""
    ohne = unicodedata.normalize("NFKD", (name or "").translate(_UMSCHRIFT))
    ohne = "".join(c for c in ohne if not unicodedata.combining(c))
    ohne = re.sub(r"[^a-zA-Z ]", " ", ohne).lower()
    return " ".join(t for t in ohne.split() if len(t) > 1)


# Vereinsnamen weichen ab ("Borussia M'gladbach" / "Borussia
# Moenchengladbach", "1. FC Koeln" / "1.FC Koeln"). Verglichen werden die
# kennzeichnenden Woerter, Rechtsformen und Kuerzel zaehlen nicht.
_FUELL = {"fc", "sv", "sc", "vfl", "vfb", "tsg", "fsv", "ac", "as", "ss", "us",
          "cf", "cd", "rc", "ud", "sd", "rcd", "afc", "club", "de", "del", "la",
          "the", "und", "real", "sporting", "football", "calcio", "1899", "04",
          "05", "07", "1846", "1860", "ii"}


def verein_woerter(name: str) -> set[str]:
    return {w for w in schluessel(name).split() if w not in _FUELL and len(w) > 2}


def verein_passt(a: str, b: str) -> bool:
    wa, wb = verein_woerter(a), verein_woerter(b)
    if not wa or not wb:
        return False
    if wa & wb:
        return True
    # Abkuerzungen wie "m'gladbach" gegen "moenchengladbach": gleiche
    # Endung von mindestens sieben Zeichen reicht.
    return any(x[-7:] == y[-7:] for x in wa for y in wb if len(x) >= 7 and len(y) >= 7)


def zweite_stufe(sname: str, team: str, ziel: dict[str, list],
                 minuten: int) -> list:
    """Zuordnung, wenn der Name nicht woertlich passt - nur beim selben Verein.

    Drei Faelle, alle gemessen in der Bundesliga:
      * andere Reihenfolge      "Kim Min-jae"      / "Min-jae Kim"
      * Zusatzname              "Rasmus Kristensen" / "Rasmus Nissen Kristensen"
      * Kurzform des Vornamens  "Ezequiel Fernandez" / "Equi Fernandez"
    Ohne passenden Verein wird nichts zugeordnet - lieber eine Luecke als
    die Quote eines anderen Spielers.
    """
    sw = schluessel(sname).split()
    if not sw:
        return []
    beim_verein = [sp for liste in ziel.values() for sp in liste
                   if verein_passt(sp["verein"], team)]
    def eindeutig(treffer):
        return treffer if len({sp["id"] for sp in treffer}) == 1 else []
    menge = set(sw)
    # gleiche Woerter, andere Reihenfolge - oder einer hat Zusatznamen
    t = [sp for sp in beim_verein
         if (lambda tw: tw == menge or (len(menge & tw) >= 2
                                        and (menge <= tw or tw <= menge)))
            (set(schluessel(sp["name"]).split()))]
    if eindeutig(t):
        return t
    # gleicher Nachname, beim Verein nur einmal vertreten - und die
    # Einsatzminuten beider Quellen passen zusammen. Ohne diese Probe koennte
    # ein Nachwuchsspieler gleichen Namens, den wir nicht fuehren, die Quote
    # des Stammspielers ueberschreiben.
    t = [sp for sp in beim_verein
         if schluessel(sp["name"]).split()[-1:] == sw[-1:]
         and minuten_passen(sp, minuten)]
    return eindeutig(t)


def minuten_passen(sp: dict, sofa_minuten: int) -> bool:
    tm = int((sp.get("leistung") or {}).get("minuten") or 0)
    return abs(tm - sofa_minuten) <= max(270, 0.25 * max(tm, sofa_minuten))


def eintrag(r: dict) -> dict | None:
    minuten = int(r.get("minutesPlayed") or 0)
    if not minuten:
        return None
    def zahl(k):
        v = r.get(k)
        return round(float(v), 1) if v is not None else None
    gewonnen = int(r.get("totalDuelsWon") or 0)
    pct = zahl("totalDuelsWonPercentage")
    return {
        "quelle": "sofascore",
        "geholt": date.today().isoformat(),
        "minuten": minuten,
        "quote": pct,
        "gewonnen": gewonnen,
        # Gesamtzahl aus Quote und Gewonnenen - Sofascore fuehrt sie nicht
        # als eigenes Feld, sie entscheidet aber, wie belastbar die Quote ist.
        "gesamt": round(gewonnen * 100 / pct) if pct else gewonnen,
        "boden_quote": zahl("groundDuelsWonPercentage"),
        "luft_quote": zahl("aerialDuelsWonPercentage"),
        "luft_gewonnen": int(r.get("aerialDuelsWon") or 0),
        "tacklings": int(r.get("tackles") or 0),
        "interceptions": int(r.get("interceptions") or 0),
        "sofascore_id": (r.get("player") or {}).get("id"),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ligen", default="", help="nur diese frontend_ids")
    ap.add_argument("--saison", default="",
                    help="Kurzjahr wie 25/26; Vorgabe: die Notensaison des Bestands")
    args = ap.parse_args()

    if not os.path.exists(BESTAND):
        print(f"{BESTAND} fehlt - zuerst sammeln.", file=sys.stderr)
        return 1
    with gzip.open(BESTAND, "rt", encoding="utf-8") as fh:
        bestand = json.load(fh)

    # Notensaison "2025/26" -> "25/26". Die Zweikaempfe muessen aus
    # DERSELBEN Saison stammen wie die Noten, sonst stuende eine Quote aus
    # zwei Spieltagen neben einer Note aus 34.
    jahr = args.saison or re.sub(r"^20(\d\d)/(\d\d)$", r"\1/\2",
                                 str(bestand.get("saison") or "2025/26"))
    ligen = [x.strip() for x in args.ligen.split(",") if x.strip()] or list(TURNIERE)
    unbekannt = [x for x in ligen if x not in TURNIERE]
    if unbekannt:
        print(f"Keine Sofascore-Zuordnung fuer: {', '.join(unbekannt)}",
              file=sys.stderr)
        ligen = [x for x in ligen if x in TURNIERE]

    # Bestand nach Liga der Notensaison und Namensschluessel
    nach_liga: dict[str, dict[str, list]] = {}
    for sp in bestand["spieler"]:
        if sp.get("leistung"):
            nach_liga.setdefault(sp["liga_id"], {}) \
                     .setdefault(schluessel(sp.get("name", "")), []).append(sp)

    namen = {lg.frontend_id: lg.name for lg in LEAGUES}
    gesamt = 0
    for fid in ligen:
        try:
            sid = saison_id(TURNIERE[fid], jahr)
            if not sid:
                print(f"  [X] {namen[fid]}: keine Saison {jahr}", file=sys.stderr)
                continue
            werte = liga_werte(TURNIERE[fid], sid)
        except Exception as exc:
            print(f"  [X] {namen[fid]}: {exc}", file=sys.stderr)
            continue

        ziel = nach_liga.get(fid, {})
        treffer = mehrdeutig = 0
        for r in werte:
            e = eintrag(r)
            if not e:
                continue
            sname = (r.get("player") or {}).get("name", "")
            kandidaten = ziel.get(schluessel(sname))
            if not kandidaten:
                kandidaten = zweite_stufe(sname, (r.get("team") or {}).get("name", ""),
                                          ziel, e["minuten"])
            if not kandidaten:
                continue
            # Mehrere Datensaetze desselben Spielers (Wechsel innerhalb der
            # Liga) teilen sich die Werte; mehrere VERSCHIEDENE Spieler
            # gleichen Namens werden ueber den Verein getrennt.
            if len({k["id"] for k in kandidaten}) > 1:
                team = (r.get("team") or {}).get("name", "")
                kandidaten = [k for k in kandidaten if verein_passt(k["verein"], team)]
                if len({k["id"] for k in kandidaten}) != 1:
                    mehrdeutig += 1
                    continue
            for k in kandidaten:
                k["duelle"] = e
            treffer += 1
        gesamt += treffer
        print(f"  [ok] {namen[fid]:24s} {treffer:4d} von {len(werte)} zugeordnet"
              + (f", {mehrdeutig} mehrdeutig ausgelassen" if mehrdeutig else ""),
              file=sys.stderr)

    if not gesamt:
        print("Nichts zugeordnet - Bestand bleibt unangetastet.", file=sys.stderr)
        return 0
    bestand["stand"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with gzip.open(BESTAND, "wt", encoding="utf-8") as fh:
        json.dump(bestand, fh, ensure_ascii=False, separators=(",", ":"))
    print(f"\n{gesamt} Spieler mit Zweikampfwerten ({jahr}). "
          f"Danach compute_grades.py laufen lassen.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
