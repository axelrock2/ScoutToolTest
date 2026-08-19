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
import gzip
import json
import os
import re
import sys
import time
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from leagues import LEAGUES, by_frontend_id          # noqa: E402
from tm_client import cell_text, fetch               # noqa: E402

# Gepackt abgelegt: ungepackt sind es 9 MB, gzip macht daraus 0,7 MB.
# Die Datei MUSS im Repository liegen, sonst startet ein Lauf in der Action
# ohne Bestand - und ein Teillauf ueberschriebe dann alle uebrigen Ligen.
#
# SCOUT_TARGET setzt einen anderen Ausgabepfad. Damit koennen mehrere
# Laeufe parallel je eine Teilmenge sammeln (siehe Matrix in der Action);
# merge_raw.py fuegt die Teile anschliessend zusammen.
TARGET = os.environ.get("SCOUT_TARGET") or os.path.join(
    os.path.dirname(__file__), "..", "data", "players_raw.json.gz")

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


def liga_tabelle(tm_id: str, saison: int) -> dict[str, dict]:
    """Abschlusstabelle der Liga: {verein_id: {spiele, tore, gegentore, punkte}}.

    Ein Abruf je Liga - und die einzige frei verfuegbare Quelle fuer
    Defensivleistung. Individuelle Zweikampf- oder Passwerte fuehrt
    Transfermarkt nicht; die Gegentore der Mannschaft sind das Beste, was
    sich fuer Innenverteidiger und Torhueter belegen laesst.
    """
    page = fetch(f"/x/tabelle/wettbewerb/{tm_id}/saison_id/{saison}")
    out: dict[str, dict] = {}
    for row in page.css("table.items > tbody > tr"):
        vid = None
        for href in row.css("a::attr(href)"):
            m = re.search(r"/verein/(\d+)", str(href))
            if m:
                vid = m.group(1)
                break
        if not vid:
            continue
        c = [cell_text(td) for td in row.css("td")]
        tore = next((x for x in c if re.fullmatch(r"\d+:\d+", x)), None)
        if not tore:
            continue
        geschossen, kassiert = (int(x) for x in tore.split(":"))
        zahlen = [int(x) for x in c if x.isdigit()]
        spiele = zahlen[1] if len(zahlen) > 1 else None
        out[vid] = {
            "spiele": spiele,
            "tore": geschossen,
            "gegentore": kassiert,
            "punkte": zahlen[-1] if zahlen else None,
        }
    return out


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


def leistung(verein_id: str, slug: str, saison: int,
             tm_liga: str) -> dict[str, dict]:
    """Saisonwerte je Spieler-ID - NUR AUS DIESER LIGA.

    Der Parameter reldata=<Wettbewerb>&<Saison> ist entscheidend: ohne ihn
    liefert Transfermarkt alle Pflichtspiele zusammen. Harry Kane stand so
    mit 51 Einsaetzen und 61 Toren in den Daten statt mit 31 und 36 aus der
    Bundesliga - Champions League und Pokal mitgezaehlt.

    Das verzerrte zweierlei: Spieler mit Europapokal wurden an Spielern
    ohne gemessen, und der Anteil an den Teamtoren rechnete Tore aus allen
    Wettbewerben gegen die Ligatore der Mannschaft.

    Spaltenregel (auf mehreren Vereinen geprueft): ab 'Im Kader' entspricht
    Kopfzeile[i] der Zelle[i+3]; davor liegen Bild- und Namensspalten.
    """
    page = fetch(
        f"/{slug}/leistungsdaten/verein/{verein_id}/plus/1"
        f"?reldata={tm_liga}%26{saison}"
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

    # Zeitbudget. Einzelne Abrufe koennen minutenlang haengen: curl beachtet
    # den gesetzten Timeout beim Verbindungsaufbau nicht zuverlaessig, und
    # ein blockierender C-Aufruf laesst sich aus Python nicht unterbrechen.
    # Statt das Ganze abstuerzen zu lassen, hoeren wir geordnet auf - dank
    # der Zusammenfuehrung behalten die uebrigen Ligen ihren letzten Stand.
    budget = float(os.environ.get("SCOUT_BUDGET_MIN", "0")) * 60
    start = time.monotonic()

    def zeit_um() -> bool:
        return bool(budget) and (time.monotonic() - start) > budget

    for lg in ligen:
        stand = {"liga": lg.name, "id": lg.frontend_id, "land": lg.land}

        if zeit_um():
            stand.update(status="uebersprungen", grund="Zeitbudget erschoepft",
                         spieler=0)
            bericht.append(stand)
            print(f"  [-] {lg.name}: Zeitbudget erschoepft, uebersprungen",
                  file=sys.stderr)
            continue
        try:
            clubs = vereine_der_liga(lg.tm_id, SAISON)
        except Exception as exc:
            stand.update(status="fehlt", grund=str(exc)[:150], spieler=0)
            bericht.append(stand)
            print(f"  [X] {lg.name}: {exc}", file=sys.stderr)
            continue

        if max_vereine:
            clubs = clubs[:max_vereine]

        # Ein Abruf je Liga liefert Spiele, Tore und Gegentore aller Vereine.
        # Ohne diese Werte gaebe es fuer Abwehrpositionen gar keinen
        # Leistungsbezug - individuelle Defensivdaten fuehrt die Quelle nicht.
        try:
            tabelle = liga_tabelle(lg.tm_id, SAISON)
        except Exception as exc:
            tabelle = {}
            print(f"  [!] {lg.name}: Tabelle nicht lesbar ({exc})", file=sys.stderr)

        vor = len(spieler)
        ok_clubs = 0
        for vid, slug in clubs:
            if zeit_um():
                print(f"  [-] {lg.name}: Zeitbudget waehrend der Liga erschoepft",
                      file=sys.stderr)
                break
            try:
                verein_name, profile = kader(vid, slug, SAISON)
                try:
                    stats = leistung(vid, slug, SAISON, lg.tm_id)
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
                        "team": tabelle.get(vid),
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
    ap.add_argument("--nur-leistung", action="store_true",
                    help="nur die Leistungsdaten erneuern (eine Seite je "
                         "Verein statt zwei), Profile bleiben unangetastet")
    ap.add_argument("--nur-tabellen", action="store_true",
                    help="nur die Ligatabellen holen und dem Bestand "
                         "hinzufuegen (ein Abruf je Liga statt zwei je Verein)")
    args = ap.parse_args()

    ligen = LEAGUES
    if args.ligen:
        gewaehlt = [by_frontend_id(x.strip()) for x in args.ligen.split(",")]
        ligen = [lg for lg in gewaehlt if lg]

    # Nur die Leistungsdaten erneuern. Noetig geworden, weil sie bis dahin
    # alle Wettbewerbe umfassten; die Kaderprofile bleiben gueltig.
    if args.nur_leistung:
        if not os.path.exists(TARGET):
            print(f"{TARGET} fehlt - zuerst regulaer sammeln.", file=sys.stderr)
            return 1
        with gzip.open(TARGET, "rt", encoding="utf-8") as fh:
            bestand = json.load(fh)

        # Vereine je Liga aus dem Bestand, kein zusaetzlicher Abruf noetig
        clubs_je_liga: dict[str, dict[str, str]] = {}
        for sp in bestand["spieler"]:
            clubs_je_liga.setdefault(sp["liga_id"], {})[sp["verein_id"]] = sp["verein"]

        gewaehlt = {lg.frontend_id: lg for lg in ligen}
        erneuert = 0
        for fid, clubs in clubs_je_liga.items():
            lg = gewaehlt.get(fid)
            if not lg:
                continue
            neu_stats: dict[str, dict] = {}
            ok = 0
            for vid in clubs:
                try:
                    slug = "x"          # Transfermarkt ignoriert den Namensteil
                    neu_stats.update({(vid, k): v for k, v in
                                      leistung(vid, slug, SAISON, lg.tm_id).items()})
                    ok += 1
                except Exception as exc:
                    print(f"  [!] {lg.name} / {vid}: {exc}", file=sys.stderr)
            for sp in bestand["spieler"]:
                if sp["liga_id"] != fid:
                    continue
                treffer = neu_stats.get((sp["verein_id"], sp["id"]))
                sp["leistung"] = treffer
                if treffer:
                    erneuert += 1
            print(f"  [ok] {lg.name}: {ok}/{len(clubs)} Vereine", file=sys.stderr)

        bestand["stand"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
        with gzip.open(TARGET, "wt", encoding="utf-8") as fh:
            json.dump(bestand, fh, ensure_ascii=False, separators=(",", ":"))
        print(f"\n{erneuert} Spieler mit Ligawerten erneuert", file=sys.stderr)
        return 0

    # Nur die Mannschaftswerte nachtragen. Die Tabelle einer Liga ist ein
    # einziger Abruf - fuer alle 33 Ligen also 33 statt rund 1200 Seiten.
    if args.nur_tabellen:
        if not os.path.exists(TARGET):
            print(f"{TARGET} fehlt - zuerst regulaer sammeln.", file=sys.stderr)
            return 1
        with gzip.open(TARGET, "rt", encoding="utf-8") as fh:
            bestand = json.load(fh)

        tabellen: dict[str, dict] = {}
        for lg in ligen:
            try:
                t = liga_tabelle(lg.tm_id, SAISON)
                tabellen[lg.frontend_id] = t
                print(f"  [ok] {lg.name}: {len(t)} Vereine", file=sys.stderr)
            except Exception as exc:
                print(f"  [X] {lg.name}: {exc}", file=sys.stderr)

        getroffen = 0
        for sp in bestand["spieler"]:
            t = tabellen.get(sp.get("liga_id"), {}).get(sp.get("verein_id"))
            if t:
                sp["team"] = t
                getroffen += 1

        bestand["stand"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
        with gzip.open(TARGET, "wt", encoding="utf-8") as fh:
            json.dump(bestand, fh, ensure_ascii=False, separators=(",", ":"))
        print(f"\n{getroffen} Spieler mit Mannschaftswerten versehen "
              f"-> {os.path.relpath(TARGET)}", file=sys.stderr)
        return 0

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
            with gzip.open(TARGET, "rt", encoding="utf-8") as fh:
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
    with gzip.open(TARGET, "wt", encoding="utf-8") as fh:
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
