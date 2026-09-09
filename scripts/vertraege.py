#!/usr/bin/env python3
"""Holt auslaufende Vertraege von Transfermarkt.

Quelle ist die Vereinsseite "Vertragsende":

    /<verein>/vertragsende/verein/<id>?vertragsendeJahr=<jahr>

Sie fuehrt genau die Spieler, deren Vertrag im gewaehlten Sommer endet -
mitsamt einer etwaigen Vertragsoption ("beidseitig 2 Jahre", "Kaufoption",
"vereinsseitig 1 Jahr") und farblich markiert, ob es sich um einen
Leihspieler handelt. Beides steht in der Kaderansicht nicht und ist fuer
die Bewertung eines Auslaeufers entscheidend: eine Verlaengerungsoption
macht aus einem freien Transfer keinen, und ein endendes Leihgeschaeft
ist ueberhaupt kein Vertragsende.

Ein Abruf je Verein und Jahr - also rund 700 statt 17000 Abrufen, wie es
ein Weg ueber die Spielerprofile waere.

    python3 scripts/vertraege.py                    # kommender + folgender Sommer
    python3 scripts/vertraege.py --jahre 2027       # nur der kommende
    python3 scripts/vertraege.py --ligen buli,buli2
    python3 scripts/vertraege.py --erneuern         # auch schon geprueftes neu

Vorher sollte build_players.py --kader-aktuell gelaufen sein: nur daher
weiss dieses Werkzeug, wer heute noch im Kader steht - und nur fuer die
laesst sich aus einem fehlenden Eintrag "Vertrag laeuft laenger" schliessen.
Fehlt der Kaderstand, werden ausschliesslich die gefundenen Auslaeufer
geschrieben.

Danach compute_grades.py laufen lassen.

Was in den Bestand geschrieben wird
-----------------------------------
    vertrag       nur bei Auslaeufern: {bis, option, leihe, quelle, geholt}
    vertrag_scan  bei JEDEM geprueften Kaderspieler: die geprueften Jahre

Der zweite Eintrag ist der wichtigere Teil der Herkunft: nur mit ihm
laesst sich "Vertrag laeuft laenger" von "nicht nachgesehen" trennen.
Spieler, die nicht mehr im Kader ihres Vereins stehen, bekommen ihn
nicht - sie tauchen auf der Vereinsseite gar nicht erst auf, ihr Fehlen
sagt also nichts ueber ihren Vertrag aus.
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
from tm_client import cell_text, fetch               # noqa: E402

BESTAND = os.path.join(os.path.dirname(__file__), "..", "data",
                       "players_raw.json.gz")
BUDGET_MIN = float(os.environ.get("SCOUT_BUDGET_MIN", "0")) or None


def kommender_sommer(heute: date | None = None) -> int:
    """Jahr des naechsten 30. Juni.

    Ab Juli zaehlt der Sommer des Folgejahres: im September 2026 laeuft
    die Spielzeit 2026/27, die naechsten Vertraege enden am 30.06.2027.
    """
    h = heute or date.today()
    return h.year + 1 if h.month >= 7 else h.year


def _datum(text: str) -> str | None:
    m = re.search(r"(\d{2})\.(\d{2})\.(\d{4})", text or "")
    return f"{m.group(3)}-{m.group(2)}-{m.group(1)}" if m else None


def auslaufende(verein_id: str, jahr: int) -> dict[str, dict]:
    """{spieler_id: {bis, option, leihe}} fuer einen Verein und ein Jahr.

    Ein leeres Ergebnis ist ein gueltiges Ergebnis - Vereine ohne
    Auslaeufer in diesem Sommer gibt es durchaus (gemessen: Arsenal).
    """
    page = fetch(f"/x/vertragsende/verein/{verein_id}"
                 f"?vertragsendeJahr={jahr}")
    out: dict[str, dict] = {}
    for row in page.css("table.items > tbody > tr"):
        pid = None
        for href in row.css("a::attr(href)"):
            m = re.search(r"/profil/spieler/(\d+)", str(href))
            if m:
                pid = m.group(1)
                break
        if not pid:
            continue
        zellen = [cell_text(td) for td in row.css("td")]
        bis = next((_datum(z) for z in zellen
                    if re.fullmatch(r"\d{2}\.\d{2}\.\d{4}", z)), None)
        if not bis:
            continue
        # Die Optionsspalte steht zwischen Vertragsende und Marktwert.
        # "-" heisst: keine Option vereinbart.
        option = None
        for i, z in enumerate(zellen):
            if re.fullmatch(r"\d{2}\.\d{2}\.\d{4}", z) and i + 1 < len(zellen):
                kandidat = zellen[i + 1].strip()
                if kandidat and kandidat != "-":
                    option = kandidat
                break
        # Leihspieler sind auf der Seite gruen hinterlegt. Ihr "Vertrags-
        # ende" ist das Ende der Leihe, nicht das des Vertrags beim
        # Stammverein - ohne diese Unterscheidung waere die Suche falsch.
        klasse = str(row.attrib.get("class") or "")
        out[pid] = {"bis": bis, "option": option,
                    "leihe": "gruen" in klasse}
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--jahre", default="",
                    help="Kommagetrennt, z. B. 2027,2028. "
                         "Vorgabe: kommender und folgender Sommer.")
    ap.add_argument("--ligen", default="", help="nur diese frontend_ids")
    ap.add_argument("--max-vereine", type=int, default=0,
                    help="hoechstens so viele Vereine (zum Testen)")
    ap.add_argument("--erneuern", action="store_true",
                    help="auch Vereine erneut abrufen, die schon geprueft sind")
    args = ap.parse_args()

    if args.jahre:
        jahre = [int(j) for j in args.jahre.replace(" ", "").split(",") if j]
    else:
        erstes = kommender_sommer()
        jahre = [erstes, erstes + 1]

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

    # Vereine aus dem Bestand - kein zusaetzlicher Abruf noetig.
    vereine: dict[str, tuple[str, str]] = {}       # vid -> (name, liga_id)
    for sp in bestand["spieler"]:
        if erlaubt and sp["liga_id"] not in erlaubt:
            continue
        vereine.setdefault(sp["verein_id"], (sp["verein"], sp["liga_id"]))

    marke = ",".join(str(j) for j in jahre)
    if not args.erneuern:
        # Ein Verein gilt als erledigt, wenn ALLE seine Kaderspieler den
        # Stempel dieser Jahre tragen - und er ueberhaupt welche hat.
        bestaetigt: set[str] = set()
        offenstehend: set[str] = set()
        for sp in bestand["spieler"]:
            if sp["verein_id"] not in vereine or sp.get("nicht_mehr_im_kader"):
                continue
            if (sp.get("vertrag_scan") or {}).get("jahre") == marke:
                bestaetigt.add(sp["verein_id"])
            else:
                offenstehend.add(sp["verein_id"])
        fertig = bestaetigt - offenstehend
        vereine = {v: d for v, d in vereine.items() if v not in fertig}

    offen = sorted(vereine.items(), key=lambda x: x[1][1])
    if args.max_vereine:
        offen = offen[:args.max_vereine]

    print(f"Jahre {marke} - {len(offen)} Vereine, "
          f"{len(offen) * len(jahre)} Abrufe.", file=sys.stderr)

    start = time.time()
    heute = date.today().isoformat()
    treffer: dict[tuple[str, str], dict] = {}      # (vid, pid) -> vertrag
    geprueft: set[str] = set()
    fehler = 0

    for vid, (name, liga_id) in offen:
        if BUDGET_MIN and (time.time() - start) / 60 > BUDGET_MIN:
            print(f"  Zeitbudget von {BUDGET_MIN:.0f} min erreicht.",
                  file=sys.stderr)
            break
        vollstaendig = True
        for jahr in jahre:
            try:
                for pid, eintrag in auslaufende(vid, jahr).items():
                    treffer[(vid, pid)] = {**eintrag, "quelle": "transfermarkt",
                                           "geholt": heute}
            except Exception as exc:
                vollstaendig = False
                fehler += 1
                if fehler <= 8:
                    print(f"  [!] {name} ({jahr}): {str(exc)[:70]}",
                          file=sys.stderr)
        # Nur vollstaendig gepruefte Vereine gelten als geprueft - sonst
        # sagte ein fehlender Eintrag "Vertrag laeuft laenger", obwohl der
        # Abruf schlicht scheiterte.
        if vollstaendig:
            geprueft.add(vid)
            if len(geprueft) % 50 == 0:
                print(f"  {len(geprueft)} Vereine, {len(treffer)} "
                      f"Auslaeufer ...", file=sys.stderr)

    if not geprueft:
        print("Nichts geholt - Bestand bleibt unangetastet.", file=sys.stderr)
        return 0

    # Wo ist die Kaderzugehoerigkeit ueberhaupt bekannt?
    #
    # "Kein Eintrag" heisst nur dann "Vertrag laeuft laenger", wenn der
    # Spieler heute noch im Kader steht - sonst fehlt er auf der
    # Vereinsseite, weil er den Verein verlassen hat. Diese Unterscheidung
    # trifft allein build_players.py --kader-aktuell (nicht_mehr_im_kader).
    # Ohne sie wird der Vermerk NICHT gesetzt: lieber keine Auskunft als
    # eine unbelegte. Die gefundenen Auslaeufer selbst sind davon nicht
    # betroffen - sie sind beobachtet, nicht erschlossen.
    ligen_mit_kaderstand = {sp["liga_id"] for sp in bestand["spieler"]
                            if sp.get("nicht_mehr_im_kader")}
    ohne_kaderstand = sorted({liga for _, (_, liga) in offen}
                             - ligen_mit_kaderstand)
    if ohne_kaderstand:
        print(f"  Kein Kaderstand für {', '.join(ohne_kaderstand)} - dort "
              f"nur gefundene Ausläufer, kein Vermerk 'Vertrag läuft länger'.\n"
              f"  Erst 'build_players.py --kader-aktuell --ligen "
              f"{','.join(ohne_kaderstand)}' laufen lassen, dann hier "
              f"--erneuern.", file=sys.stderr)

    mit_vertrag = ohne = 0
    for sp in bestand["spieler"]:
        vid = sp["verein_id"]
        if vid not in geprueft:
            continue
        eintrag = treffer.get((vid, str(sp["id"])))
        if eintrag:
            sp["vertrag"] = eintrag
            # Die Kaderansicht kennt das Datum haeufig nicht; hier steht es.
            if not sp.get("vertrag_bis") and not eintrag["leihe"]:
                sp["vertrag_bis"] = eintrag["bis"]
            mit_vertrag += 1
        else:
            sp.pop("vertrag", None)           # verlaengert oder abgegeben
        if sp.get("nicht_mehr_im_kader") or sp["liga_id"] not in ligen_mit_kaderstand:
            # Auch einen frueher gesetzten Vermerk wieder entfernen: der
            # Spieler kann den Verein seither verlassen haben.
            sp.pop("vertrag_scan", None)
        else:
            sp["vertrag_scan"] = {"jahre": marke, "geholt": heute,
                                  "quelle": "transfermarkt"}
            ohne += 1

    bestand["stand"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with gzip.open(BESTAND, "wt", encoding="utf-8") as fh:
        json.dump(bestand, fh, ensure_ascii=False, separators=(",", ":"))
    print(f"\n{len(geprueft)} Vereine geprueft, {mit_vertrag} Auslaeufer, "
          f"{ohne} Kaderspieler mit gesichertem Vertragsstand "
          f"({fehler} Fehler).\nDanach compute_grades.py laufen lassen.",
          file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
