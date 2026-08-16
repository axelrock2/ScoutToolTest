#!/usr/bin/env python3
"""Sammelt Kader- und Leistungsdaten fuer alle konfigurierten Ligen.

Laeuft in der GitHub Action (serverseitig, daher kein CORS und kein Proxy
noetig) und schreibt das Ergebnis nach data/players_raw.json.

Ausfallsichere Bauweise:
  * jeder Verein wird einzeln versucht; Fehler ueberspringen nur diesen Verein
  * das Ergebnis enthaelt einen Statusbericht je Liga (sichtbar im Frontend)
  * schlaegt ALLES fehl, bleibt eine vorhandene Datei unangetastet

Zwei Seiten je Verein:
  /kader/verein/<id>/plus/1                    -> Profil (Alter, Vertrag, Marktwert)
  /leistungsdaten/verein/<id>/plus/1?saison_id -> Leistung (Einsaetze, Tore, Minuten)

Lokal testen (eine Liga, schnell):
    python3 scripts/build_players.py --ligen buli2 --max-vereine 3
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from leagues import LEAGUES, by_frontend_id          # noqa: E402
from tm_client import cell_text, fetch               # noqa: E402

TARGET = os.path.join(os.path.dirname(__file__), "..", "data", "players_raw.json")

# Saison, aus der die Leistungsdaten stammen. 2025 = Spielzeit 2025/26.
SAISON = int(os.environ.get("SCOUT_SAISON", "2025"))

# Transfermarkt-Positionsbezeichnung -> Kuerzel im Frontend
POS_MAP = {
    "torwart": "TW",
    "innenverteidiger": "IV",
    "linker verteidiger": "LV",
    "rechter verteidiger": "RV",
    "abwehr": "IV",
    "defensives mittelfeld": "DM",
    "zentrales mittelfeld": "ZM",
    "offensives mittelfeld": "OM",
    "linkes mittelfeld": "LA",
    "rechtes mittelfeld": "RA",
    "mittelfeld": "ZM",
    "linksaussen": "LA",
    "rechtsaussen": "RA",
    "hängende spitze": "OM",
    "mittelstürmer": "ST",
    "sturm": "ST",
}


# ---------------------------------------------------------------- Parser-Hilfen

def _num(text: str) -> int | None:
    """'3.060'' -> 3060 ; '34' -> 34 ; '-' -> None"""
    if not text:
        return None
    cleaned = re.sub(r"[^\d]", "", text.replace(".", ""))
    return int(cleaned) if cleaned else None


def _marktwert(text: str) -> int | None:
    """'1,80 Mio. €' -> 1800000 ; '500 Tsd. €' -> 500000"""
    if not text or "-" == text.strip():
        return None
    m = re.search(r"([\d.,]+)\s*(Mio|Tsd)", text)
    if not m:
        return None
    zahl = float(m.group(1).replace(".", "").replace(",", "."))
    return int(zahl * (1_000_000 if m.group(2) == "Mio" else 1_000))


def _hoehe(text: str) -> int | None:
    """'1,92m' -> 192"""
    m = re.search(r"(\d),(\d{2})", text or "")
    return int(m.group(1)) * 100 + int(m.group(2)) if m else None


def _alter(text: str) -> int | None:
    """'27.07.2001 (25)' -> 25"""
    m = re.search(r"\((\d{1,2})\)", text or "")
    return int(m.group(1)) if m else None


def _datum(text: str) -> str | None:
    """'30.06.2027' -> '2027-06-30'"""
    m = re.search(r"(\d{2})\.(\d{2})\.(\d{4})", text or "")
    return f"{m.group(3)}-{m.group(2)}-{m.group(1)}" if m else None


def _pos(text: str) -> str:
    key = (text or "").strip().lower().replace("ß", "ss")
    for name, code in POS_MAP.items():
        if key.startswith(name.replace("ß", "ss")):
            return code
    return "ZM"


def _spieler_id(row) -> str | None:
    for href in row.css('a::attr(href)'):
        m = re.search(r"/profil/spieler/(\d+)", str(href))
        if m:
            return m.group(1)
    return None


def _spieler_name(row) -> str:
    for a in row.css('a[href*="/profil/spieler/"]'):
        txt = cell_text(a)
        if txt:
            return txt
    return ""


# ------------------------------------------------------------------- Abschnitte

def vereine_der_liga(tm_id: str, saison: int) -> list[tuple[str, str]]:
    """[(verein_id, slug), ...] der Liga IN DIESER SAISON.

    Ohne saison_id liefert Transfermarkt die aktuelle Spielzeit. Dann landen
    Aufsteiger faelschlich in der hoeheren Liga, obwohl ihre Saisonwerte in
    der unteren erzielt wurden - und die Percentile verglichen sie mit der
    falschen Gruppe.
    """
    page = fetch(f"/x/startseite/wettbewerb/{tm_id}/plus/?saison_id={saison}")
    gefunden: dict[str, str] = {}
    for href in page.css("a::attr(href)"):
        m = re.search(r"/([^/]+)/startseite/verein/(\d+)", str(href))
        if m:
            gefunden.setdefault(m.group(2), m.group(1))
    return sorted(gefunden.items())


def kader(verein_id: str, slug: str, saison: int) -> tuple[str, dict[str, dict]]:
    """(Vereinsname, Profildaten je Spieler-ID) fuer die angegebene Saison."""
    page = fetch(f"/{slug}/kader/verein/{verein_id}/plus/1?saison_id={saison}")

    kopf = page.css("h1.data-header__headline-wrapper") or page.css("h1")
    name = cell_text(kopf[0]) if kopf else slug.replace("-", " ").title()

    out: dict[str, dict] = {}
    for row in page.css("table.items > tbody > tr"):
        tds = row.css("td")
        if len(tds) < 13:
            continue
        pid = _spieler_id(row)
        if not pid:
            continue
        c = [cell_text(td) for td in tds]
        out[pid] = {
            "id": pid,
            "name": _spieler_name(row),
            "rueckennummer": _num(c[0]),
            "position": _pos(c[4]),
            "position_lang": c[4],
            "alter": _alter(c[5]),
            "groesse_cm": _hoehe(c[7]),
            "fuss": (c[8] or "").lower() or None,
            "vertrag_bis": _datum(c[11]),
            "marktwert_eur": _marktwert(c[12]),
        }
    return name, out


def leistung(verein_id: str, slug: str, saison: int) -> dict[str, dict]:
    """Saisonwerte je Spieler-ID.

    Spaltenregel (auf mehreren Vereinen geprueft): ab 'Im Kader' entspricht
    Kopfzeile[i] der Zelle[i+3]; davor liegen Bild- und Namensspalten.
    """
    page = fetch(
        f"/{slug}/leistungsdaten/verein/{verein_id}/plus/1?saison_id={saison}"
    )
    out: dict[str, dict] = {}
    for row in page.css("table.items > tbody > tr"):
        tds = row.css("td")
        if len(tds) < 18:
            continue
        pid = _spieler_id(row)
        if not pid:
            continue
        c = [cell_text(td) for td in tds]
        einsaetze = _num(c[8])
        if not einsaetze:
            continue                       # Saison nicht fuer diesen Verein gespielt
        out[pid] = {
            "einsaetze": einsaetze,
            "tore": _num(c[9]) or 0,
            "vorlagen": _num(c[10]) or 0,
            "gelbe": _num(c[11]) or 0,
            "gelbrot": _num(c[12]) or 0,
            "rot": _num(c[13]) or 0,
            "minuten": _num(c[17]) or 0,
        }
    return out


# ------------------------------------------------------------------------ Lauf

def sammle(ligen: list, max_vereine: int | None) -> tuple[list[dict], list[dict]]:
    spieler: list[dict] = []
    bericht: list[dict] = []

    for lg in ligen:
        stand = {"liga": lg.name, "id": lg.frontend_id, "land": lg.land}
        try:
            clubs = vereine_der_liga(lg.tm_id, SAISON)
        except Exception as exc:
            stand.update(status="fehlt", grund=str(exc)[:150], spieler=0)
            bericht.append(stand)
            print(f"  [X] {lg.name}: {exc}", file=sys.stderr)
            continue

        if max_vereine:
            clubs = clubs[:max_vereine]

        vor = len(spieler)
        ok_clubs = 0
        for vid, slug in clubs:
            try:
                verein_name, profile = kader(vid, slug, SAISON)
                try:
                    stats = leistung(vid, slug, SAISON)
                except Exception:
                    stats = {}                # Leistungsseite optional
                for pid, prof in profile.items():
                    if not prof["name"]:
                        continue
                    spieler.append({
                        **prof,
                        "verein": verein_name,
                        "verein_id": vid,
                        "liga": lg.name,
                        "liga_id": lg.frontend_id,
                        "land": lg.land,
                        "saison": f"{SAISON}/{str(SAISON + 1)[2:]}",
                        "leistung": stats.get(pid),
                    })
                ok_clubs += 1
            except Exception as exc:
                print(f"  [!] {lg.name} / {slug}: {exc}", file=sys.stderr)

        stand.update(
            status="ok" if ok_clubs else "fehlt",
            vereine=f"{ok_clubs}/{len(clubs)}",
            spieler=len(spieler) - vor,
        )
        bericht.append(stand)
        print(f"  [ok] {lg.name}: {ok_clubs}/{len(clubs)} Vereine, "
              f"{len(spieler) - vor} Spieler", file=sys.stderr)

    return spieler, bericht


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ligen", help="Komma-Liste von frontend_id, sonst alle")
    ap.add_argument("--max-vereine", type=int, help="nur die ersten N je Liga (Test)")
    ap.add_argument("--frisch", action="store_true",
                    help="Bestand verwerfen statt ergaenzen")
    args = ap.parse_args()

    ligen = LEAGUES
    if args.ligen:
        gewaehlt = [by_frontend_id(x.strip()) for x in args.ligen.split(",")]
        ligen = [lg for lg in gewaehlt if lg]

    print(f"Sammle {len(ligen)} Ligen, Saison {SAISON}/{str(SAISON + 1)[2:]} ...",
          file=sys.stderr)
    spieler, bericht = sammle(ligen, args.max_vereine)

    if not spieler:
        print("Kein einziger Spieler geladen - vorhandene Datei bleibt "
              "unangetastet.", file=sys.stderr)
        return 1

    # Bereits vorhandene Ligen erhalten, sofern sie in diesem Lauf nicht
    # angefasst wurden. So laesst sich der Bestand schrittweise erweitern,
    # und eine Liga, die heute ausfaellt, behaelt ihren letzten Stand.
    if not args.frisch and os.path.exists(TARGET):
        try:
            with open(TARGET, encoding="utf-8") as fh:
                alt = json.load(fh)
            neu_ids = {lg.frontend_id for lg in ligen}
            behalten = [s for s in alt.get("spieler", [])
                        if s.get("liga_id") not in neu_ids]
            alt_bericht = [q for q in alt.get("quellen", [])
                           if q.get("id") not in neu_ids]
            if behalten:
                print(f"  {len(behalten)} Spieler aus {len(alt_bericht)} frueheren "
                      f"Ligen uebernommen", file=sys.stderr)
            spieler = behalten + spieler
            bericht = alt_bericht + bericht
        except (OSError, ValueError) as exc:
            print(f"  Bestand nicht lesbar, schreibe neu: {exc}", file=sys.stderr)

    bericht.sort(key=lambda q: q.get("liga", ""))

    os.makedirs(os.path.dirname(TARGET), exist_ok=True)
    with open(TARGET, "w", encoding="utf-8") as fh:
        json.dump({
            "stand": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "saison": f"{SAISON}/{str(SAISON + 1)[2:]}",
            "quellen": bericht,
            "spieler": spieler,
        }, fh, ensure_ascii=False, separators=(",", ":"))

    mit_stats = sum(1 for s in spieler if s.get("leistung"))
    print(f"\n{len(spieler)} Spieler geschrieben ({mit_stats} mit Saisonwerten) "
          f"-> {os.path.relpath(TARGET)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
