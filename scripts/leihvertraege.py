#!/usr/bin/env python3
"""Holt fuer Leihspieler das Vertragsende beim STAMMVEREIN.

Die Kaderansicht verraet nur, dass jemand ausgeliehen ist und wann die
Leihe endet ("Leihspieler von: SK Slavia Prag; Rueckkehr: 31.12.2026").
Wie lange sein Vertrag beim Stammverein laeuft, steht an zwei Stellen:

    Profilseite des Spielers        "Vertrag dort bis: 30.06.2030"
    Leihspieler-Seite des Vereins   Tabelle "Leihklub": Vertrag bis | Leihende

Fuer Scouting entscheidet genau dieses Datum: laeuft der Vertrag beim
Stammverein im selben Sommer aus wie die Leihe, wird der Spieler frei -
laeuft er bis 2030, kostet er Abloese.

Warum die Vereinsseite der Standard ist
---------------------------------------
Die Profilseite kostet einen Abruf je Spieler, und Transfermarkt sperrt
Profilseiten nach rund 60 bis 70 Abrufen (gemessen am 14.09.2026: 100 von
844 Leihspielern, dann vier Fehler in Folge). Die Leihspieler-Seite des
AUFNEHMENDEN Vereins fuehrt dieselbe Angabe fuer alle seine Leihspieler auf
einmal - rund 290 Abrufe statt 844, auf einer Seitenart, die am selben Tag
665 Abrufe ohne Sperre vertrug.

Gegengeprueft, bevor die Vereinsseite zum Standard wurde:
    Halinsky  bei FK Pardubice   Vertrag bis 30.06.2030  (Profil: 30.06.2030)
    Sarapata  bei FC Kopenhagen  Vertrag bis 30.06.2029  (Profil: 30.06.2029)

Die Daten werden SPALTENGENAU gelesen - die letzten beiden zentrierten
Zellen einer Zeile sind "Vertrag bis" und "Leihende", "-" heisst
unbekannt. Bei Pardubice fehlte in zwei von vier Zeilen eines der beiden
Daten; wer nur die Daten einer Zeile der Reihe nach nimmt, vertauscht dann
Vertragsende und Leihende.

Beide Wege pausieren zwischen den Abrufen (SCOUT_PAUSE), brechen nach vier
Fehlern in Folge ab und speichern, was sie haben - auch bei einem Abbruch
von aussen.

    python3 scripts/leihvertraege.py                    # alle offenen
    python3 scripts/leihvertraege.py --probe --vereine 1496
    python3 scripts/leihvertraege.py --erneuern         # auch schon gepruefte
    python3 scripts/leihvertraege.py --profil --max 50  # alter Weg, je Spieler

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
PAUSE = float(os.environ.get("SCOUT_PAUSE", "2"))
MAX_IN_FOLGE = 4          # so viele Fehler hintereinander -> Sperre, Abbruch

# <span …--regular>Vertrag dort bis:</span> <span …--bold>30.06.2030</span>
_DORT_BIS = re.compile(
    r"Vertrag dort bis:\s*</span>\s*<span[^>]*>\s*(\d{2}\.\d{2}\.\d{4})\s*</span>")
_VON = re.compile(
    r"Ausgeliehen von:\s*</span>\s*<span[^>]*>\s*<a[^>]*title=\"([^\"]+)\"")
_DATUM = re.compile(r"^\d{2}\.\d{2}\.\d{4}$")


def iso(tag: str) -> str:
    t, m, j = tag.split(".")
    return f"{j}-{m}-{t}"


def stammvertrag(spieler_id: str) -> dict:
    """{'bis': ISO|None, 'von': Verein|None} von der Profilseite (alter Weg).

    'bis' None heisst: die Seite fuehrt keine Zeile "Vertrag dort bis" oder
    nur "-". Das ist eine Auskunft, kein Fehler; ein fehlgeschlagener
    Abruf wirft dagegen.
    """
    h = fetch(f"/x/profil/spieler/{spieler_id}").html_content or ""
    if "info-table" not in h:
        raise RuntimeError("keine Profilseite erhalten")
    m = _DORT_BIS.search(h)
    v = _VON.search(h)
    return {"bis": iso(m.group(1)) if m else None,
            "von": v.group(1) if v else None}


def _tabellen(h: str) -> list[tuple[list[str], list[str]]]:
    """[(Spaltenkoepfe, Zeilen-HTML)] je Tabelle 'items'.

    Nur die aeusseren Zeilen (class odd/even): in jeder steckt eine
    verschachtelte Tabelle fuer Foto und Name, deren Zeilen sonst als eigene
    Spielerzeilen gezaehlt wuerden.
    """
    out = []
    for m in re.finditer(r'<table class="items"', h):
        kopf_ende = h.find("<tbody", m.start())
        if kopf_ende < 0:
            continue
        koepfe = [re.sub(r"<[^>]+>|\s+", " ", k).strip()
                  for k in re.findall(r"<th[^>]*>(.*?)</th>",
                                      h[m.start():kopf_ende], re.S)]
        naechste = h.find('<table class="items"', kopf_ende)
        body = h[kopf_ende:(naechste if naechste > 0 else len(h))]
        starts = [x.start() for x in re.finditer(r'<tr class="(?:odd|even)', body)]
        zeilen = [body[s:(starts[i + 1] if i + 1 < len(starts) else len(body))]
                  for i, s in enumerate(starts)]
        out.append((koepfe, zeilen))
    return out


def leihklub_tabelle(verein_id: str) -> dict[str, dict] | None:
    """{spieler_id: {'bis': roh, 'leihende': roh}} der AUSGELIEHENEN Spieler.

    Roh heisst: der Zellinhalt, wie er dasteht - ein Datum oder "-". Was
    daraus wird, entscheidet der Aufrufer.

    None heisst: die Seite hat keine Tabelle "Leihklub". Kein Fehler, aber
    auch keine Auskunft - betroffene Spieler bleiben ungeprueft.
    """
    h = fetch(f"/x/leihspieler/verein/{verein_id}").html_content or ""
    if "<table" not in h:
        raise RuntimeError("keine Vereinsseite erhalten")
    for koepfe, zeilen in _tabellen(h):
        if "Leihklub" not in koepfe:
            continue
        out: dict[str, dict] = {}
        for z in zeilen:
            pid = re.search(r"/profil/spieler/(\d+)", z)
            zellen = [re.sub(r"<[^>]+>|\s+", " ", c).strip()
                      for c in re.findall(r'<td class="zentriert"[^>]*>(.*?)</td>', z, re.S)]
            if pid and len(zellen) >= 2:
                out[pid.group(1)] = {"bis": zellen[-2], "leihende": zellen[-1]}
        return out
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max", type=int, default=0,
                    help="hoechstens so viele Vereine (mit --profil: Spieler)")
    ap.add_argument("--vereine", default="",
                    help="nur Leihspieler dieser aufnehmenden Vereine (IDs)")
    ap.add_argument("--probe", action="store_true", help="nur anzeigen, nichts schreiben")
    ap.add_argument("--erneuern", action="store_true",
                    help="auch Spieler abrufen, die schon geprueft sind")
    ap.add_argument("--profil", action="store_true",
                    help="alter Weg: Profilseite je Spieler statt Vereinsseite")
    args = ap.parse_args()

    with gzip.open(BESTAND, "rt", encoding="utf-8") as fh:
        bestand = json.load(fh)

    offen = [s for s in bestand["spieler"]
             if s.get("leihe") and s.get("aktuell")
             and (args.erneuern or "stammvertrag_geprueft" not in s["leihe"])]
    if args.vereine:
        nur = {v.strip() for v in args.vereine.split(",") if v.strip()}
        offen = [s for s in offen if s["aktuell"]["verein_id"] in nur]

    # Abbruch von aussen (kill, Strg-C) wie ein regulaeres Ende behandeln:
    # das bis dahin Geholte wird gespeichert, statt verloren zu gehen.
    def _stopp(*_):
        raise KeyboardInterrupt
    signal.signal(signal.SIGTERM, _stopp)

    heute = date.today().isoformat()
    start = time.time()
    z = {"ok": 0, "ohne": 0, "nicht_gelistet": 0, "unlesbar": 0,
         "abweichend": 0, "fehler": 0, "gleich_profil": 0, "abweichend_profil": 0}
    in_folge = 0

    # Ein Spieler kann mehrfach im Bestand stehen (Einsaetze fuer zwei
    # Mannschaften in der Notensaison). Gesetzt wird jeder Datensatz,
    # GEZAEHLT jeder Spieler einmal - sonst stand Tomas Jelinek im Probelauf
    # doppelt in der Bilanz.
    gezaehlt: dict[str, set[str]] = {}

    def zaehle(schluessel: str, s: dict) -> bool:
        ids = gezaehlt.setdefault(schluessel, set())
        if str(s["id"]) in ids:
            return False
        ids.add(str(s["id"]))
        z[schluessel] += 1
        return True

    def setze(s: dict, bis: str | None, quelle: str) -> None:
        s["leihe"]["stammvertrag_bis"] = bis
        s["leihe"]["stammvertrag_geprueft"] = heute
        s["leihe"]["stammvertrag_quelle"] = quelle
        zaehle("ok" if bis else "ohne", s)

    try:
        if args.profil:
            liste = offen[:args.max] if args.max else offen
            print(f"{len(liste)} Leihspieler abzurufen (Profilseiten).", file=sys.stderr)
            for i, s in enumerate(liste):
                if BUDGET_MIN and (time.time() - start) / 60 > BUDGET_MIN:
                    print("  Zeitbudget erreicht.", file=sys.stderr)
                    break
                if i:
                    time.sleep(PAUSE)
                try:
                    r = stammvertrag(str(s["id"]))
                except Exception as exc:
                    z["fehler"] += 1
                    in_folge += 1
                    if z["fehler"] <= 8:
                        print(f"  [!] {s['name']}: {str(exc)[:70]}", file=sys.stderr)
                    if in_folge >= MAX_IN_FOLGE:
                        print(f"  {in_folge} Fehler in Folge - Transfermarkt sperrt "
                              f"offenbar. Abbruch, Bisheriges wird gespeichert.",
                              file=sys.stderr)
                        break
                    continue
                in_folge = 0
                setze(s, r["bis"], "profilseite")
        else:
            je_verein: dict[str, list[dict]] = {}
            for s in offen:
                je_verein.setdefault(s["aktuell"]["verein_id"], []).append(s)
            # Vereine mit den meisten offenen Leihen zuerst: bricht ein Lauf
            # ab, ist so der groesste Teil schon erfasst.
            vereine = sorted(je_verein.items(), key=lambda x: -len(x[1]))
            if args.max:
                vereine = vereine[:args.max]
            print(f"{len({str(s['id']) for _, v in vereine for s in v})} Leihspieler bei "
                  f"{len(vereine)} Vereinen abzurufen (Leihspieler-Seiten).",
                  file=sys.stderr)
            for i, (vid, spieler) in enumerate(vereine):
                if BUDGET_MIN and (time.time() - start) / 60 > BUDGET_MIN:
                    print("  Zeitbudget erreicht - der Rest folgt beim naechsten Lauf.",
                          file=sys.stderr)
                    break
                if i:
                    time.sleep(PAUSE)
                try:
                    tabelle = leihklub_tabelle(vid)
                except Exception as exc:
                    z["fehler"] += 1
                    in_folge += 1
                    if z["fehler"] <= 8:
                        print(f"  [!] Verein {vid}: {str(exc)[:70]}", file=sys.stderr)
                    if in_folge >= MAX_IN_FOLGE:
                        print(f"  {in_folge} Fehler in Folge - Transfermarkt sperrt "
                              f"offenbar. Abbruch, Bisheriges wird gespeichert.",
                              file=sys.stderr)
                        break
                    continue
                in_folge = 0
                for s in spieler:
                    e = (tabelle or {}).get(str(s["id"]))
                    if e is None:
                        # Auf der Vereinsseite nicht gefuehrt: ungeprueft lassen,
                        # nicht als "kein Datum" markieren.
                        zaehle("nicht_gelistet", s)
                        continue
                    vb, le = e["bis"], e["leihende"]
                    if not (_DATUM.match(vb) or vb == "-"):
                        zaehle("unlesbar", s)
                        continue
                    if _DATUM.match(le) and iso(le) != s["leihe"].get("bis"):
                        if zaehle("abweichend", s) and z["abweichend"] <= 5:
                            print(f"  [~] {s['name']}: Leihende laut Vereinsseite {le}, "
                                  f"laut Kaderansicht {s['leihe'].get('bis')}",
                                  file=sys.stderr)
                    if args.probe and str(s["id"]) not in gezaehlt.get("ok", set()) | gezaehlt.get("ohne", set()):
                        print(f"  {s['name'][:26]:26s} bei {s['aktuell']['verein'][:22]:22s} "
                              f"| Vertrag bis {vb:10s} | Leihende {le:10s} "
                              f"| Kaderansicht: Leihe bis {s['leihe'].get('bis')}",
                              file=sys.stderr)
                    neu_bis = iso(vb) if _DATUM.match(vb) else None
                    # Gegenprobe: stammt der bisherige Wert von der Profilseite,
                    # muss die Vereinsseite dasselbe sagen. Abweichungen werden
                    # benannt, nicht stillschweigend ueberschrieben.
                    alt = s["leihe"]
                    if (alt.get("stammvertrag_geprueft")
                            and alt.get("stammvertrag_quelle", "profilseite") == "profilseite"):
                        if alt.get("stammvertrag_bis") == neu_bis:
                            zaehle("gleich_profil", s)
                        else:
                            if zaehle("abweichend_profil", s) and z["abweichend_profil"] <= 8:
                                print(f"  [≠] {s['name']}: Vereinsseite {vb}, Profilseite "
                                      f"{alt.get('stammvertrag_bis') or '-'}", file=sys.stderr)
                    setze(s, neu_bis, "leihspieler-seite")
    except KeyboardInterrupt:
        print("  Abgebrochen - Bisheriges wird gespeichert.", file=sys.stderr)

    print(f"\n{z['ok']} mit Vertragsende beim Stammverein, {z['ohne']} ohne Angabe, "
          f"{z['nicht_gelistet']} auf der Vereinsseite nicht gefuehrt, "
          f"{z['unlesbar']} unlesbar, {z['abweichend']} mit abweichendem Leihende, "
          f"{z['fehler']} Fehler.", file=sys.stderr)
    if z["gleich_profil"] or z["abweichend_profil"]:
        print(f"Gegenprobe mit der Profilseite: {z['gleich_profil']} gleich, "
              f"{z['abweichend_profil']} abweichend.", file=sys.stderr)
    if args.probe or not (z["ok"] or z["ohne"]):
        print("Nichts geschrieben.", file=sys.stderr)
        return 0
    bestand["stand"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with gzip.open(BESTAND, "wt", encoding="utf-8") as fh:
        json.dump(bestand, fh, ensure_ascii=False, separators=(",", ":"))
    print("Gespeichert. Danach compute_grades.py laufen lassen.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
