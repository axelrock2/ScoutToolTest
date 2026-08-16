#!/usr/bin/env python3
"""Rechnet Rohwerte in Percentile um und erzeugt data/players.json.

Percentile werden immer innerhalb derselben Liga UND derselben
Positionsgruppe gebildet - ein Innenverteidiger der 2. Bundesliga wird
also mit Innenverteidigern der 2. Bundesliga verglichen, nicht mit
Stuermern der Premier League.

Ehrlichkeitshinweis: die Kennzahlen stammen aus frei verfuegbaren Quellen
(Transfermarkt). xG, xA und progressive Carries sind dort NICHT enthalten
und werden daher auch nicht ausgewiesen. Lieber sechs echte Werte als
zwanzig geschaetzte.

Lauf:  python3 scripts/compute_grades.py
"""

from __future__ import annotations

import json
import os
import sys
from datetime import date, datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from leagues import by_frontend_id                  # noqa: E402

QUELLE = os.path.join(os.path.dirname(__file__), "..", "data", "players_raw.json")
ZIEL = os.path.join(os.path.dirname(__file__), "..", "data", "players.json")

MIN_MINUTEN = 450          # darunter ist die Stichprobe zu duenn

# Positionsgruppen fuer den Vergleich
GRUPPE = {
    "TW": "TW",
    "IV": "IV", "LV": "AV", "RV": "AV",
    "DM": "ZM", "ZM": "ZM",
    "OM": "OFF", "LA": "OFF", "RA": "OFF",
    "ST": "ST",
}

# Kennzahlen je Gruppe: (Anzeigename, Schluessel, hoeher_ist_besser)
KENNZAHLEN = {
    "TW":  [("Einsätze", "einsaetze", True),
            ("Gespielte Minuten", "minuten", True),
            ("Minuten je Einsatz", "min_pro_einsatz", True),
            ("Disziplin (Karten inv.)", "karten_pro90", False)],
    "IV":  [("Gespielte Minuten", "minuten", True),
            ("Minuten je Einsatz", "min_pro_einsatz", True),
            ("Einsätze", "einsaetze", True),
            ("Disziplin (Karten inv.)", "karten_pro90", False),
            ("Torgefahr bei Standards", "tore_pro90", True)],
    "AV":  [("Vorlagen / 90", "vorlagen_pro90", True),
            ("Gespielte Minuten", "minuten", True),
            ("Minuten je Einsatz", "min_pro_einsatz", True),
            ("Scorerpunkte / 90", "scorer_pro90", True),
            ("Disziplin (Karten inv.)", "karten_pro90", False)],
    "ZM":  [("Scorerpunkte / 90", "scorer_pro90", True),
            ("Vorlagen / 90", "vorlagen_pro90", True),
            ("Gespielte Minuten", "minuten", True),
            ("Minuten je Einsatz", "min_pro_einsatz", True),
            ("Tore / 90", "tore_pro90", True),
            ("Disziplin (Karten inv.)", "karten_pro90", False)],
    "OFF": [("Scorerpunkte / 90", "scorer_pro90", True),
            ("Vorlagen / 90", "vorlagen_pro90", True),
            ("Tore / 90", "tore_pro90", True),
            ("Gespielte Minuten", "minuten", True),
            ("Minuten je Einsatz", "min_pro_einsatz", True),
            ("Disziplin (Karten inv.)", "karten_pro90", False)],
    "ST":  [("Tore / 90", "tore_pro90", True),
            ("Scorerpunkte / 90", "scorer_pro90", True),
            ("Vorlagen / 90", "vorlagen_pro90", True),
            ("Minuten je Einsatz", "min_pro_einsatz", True),
            ("Gespielte Minuten", "minuten", True),
            ("Disziplin (Karten inv.)", "karten_pro90", False)],
}


# Alle vorkommenden Anzeigenamen, einmalig. Die Reihenfolge ist der
# Index, den die params der Spieler referenzieren.
KENNZAHL_NAMEN = sorted({anzeige for felder in KENNZAHLEN.values()
                         for anzeige, _, _ in felder})
KENNZAHL_INDEX = {name: i for i, name in enumerate(KENNZAHL_NAMEN)}


def kennwerte(s: dict) -> dict | None:
    """Leitet die Rohkennzahlen eines Spielers ab.

    Auch Spieler mit wenig Einsatzzeit werden zurueckgegeben - sie fliegen
    nicht raus, sondern werden als "duenne Datenbasis" gekennzeichnet. Die
    Vergleichsverteilung entsteht spaeter trotzdem nur aus Spielern ueber
    MIN_MINUTEN, sonst wuerden Kurzeinsaetze die Percentile verzerren.
    """
    L = s.get("leistung")
    if not L or not L.get("minuten"):
        return None
    minuten = L["minuten"]
    p90 = minuten / 90.0
    karten = L["gelbe"] + L["gelbrot"] * 2 + L["rot"] * 3
    return {
        "einsaetze": L["einsaetze"],
        "minuten": minuten,
        "min_pro_einsatz": minuten / max(L["einsaetze"], 1),
        "tore_pro90": L["tore"] / p90,
        "vorlagen_pro90": L["vorlagen"] / p90,
        "scorer_pro90": (L["tore"] + L["vorlagen"]) / p90,
        "karten_pro90": karten / p90,
        "belastbar": minuten >= MIN_MINUTEN,
    }


def percentil(wert: float, alle: list[float], hoeher_besser: bool) -> int:
    """Anteil der Vergleichsgruppe, der schlechter ist (0-100)."""
    if len(alle) < 2:
        return 50
    schlechter = sum(1 for a in alle if (a < wert if hoeher_besser else a > wert))
    gleich = sum(1 for a in alle if a == wert)
    return max(0, min(100, round(100 * (schlechter + 0.5 * gleich) / len(alle))))


def kategorie(p: int) -> str:
    return "top" if p >= 70 else ("low" if p < 40 else "mid")


def vertrags_ampel(bis: str | None) -> tuple[str, int | None]:
    """('red'|'yellow'|'green', Restmonate)"""
    if not bis:
        return "yellow", None
    try:
        ende = datetime.strptime(bis, "%Y-%m-%d").date()
    except ValueError:
        return "yellow", None
    monate = (ende.year - date.today().year) * 12 + (ende.month - date.today().month)
    if monate <= 6:
        return "red", monate
    if monate <= 12:
        return "yellow", monate
    return "green", monate


def mw_text(eur: int | None) -> str:
    if not eur:
        return "k. A."
    if eur >= 1_000_000:
        return f"{eur / 1_000_000:.1f}".replace(".", ",") + " Mio."
    return f"{eur // 1000} Tsd."


def initialen(name: str) -> str:
    teile = [t for t in name.split() if t]
    if len(teile) >= 2:
        return (teile[0][0] + teile[-1][0]).upper()
    return (name[:2] or "??").upper()


def main() -> int:
    if not os.path.exists(QUELLE):
        print(f"{QUELLE} fehlt - zuerst build_players.py laufen lassen.",
              file=sys.stderr)
        return 1

    with open(QUELLE, encoding="utf-8") as fh:
        roh = json.load(fh)

    # 1) Kennwerte ableiten, Spieler ohne belastbare Stichprobe aussortieren
    kandidaten = []
    for s in roh["spieler"]:
        kw = kennwerte(s)
        if kw:
            kandidaten.append((s, kw))

    # 2) Vergleichsgruppen bilden: (Liga, Positionsgruppe)
    gruppen: dict[tuple, list] = {}
    for s, kw in kandidaten:
        g = GRUPPE.get(s["position"], "ZM")
        gruppen.setdefault((s["liga_id"], g), []).append((s, kw))

    # 3) Percentile je Gruppe
    spieler_out = []
    for (liga_id, g), mitglieder in gruppen.items():
        felder = KENNZAHLEN[g]

        # Vergleichsmassstab nur aus Spielern mit belastbarer Spielzeit.
        # Fehlen die (kleine Staffeln), dient die ganze Gruppe als Notbehelf.
        basis = [(s, kw) for s, kw in mitglieder if kw["belastbar"]] or mitglieder
        verteilung = {
            key: [kw[key] for _, kw in basis] for _, key, _ in felder
        }

        # Ab der Oberliga fuehrt Transfermarkt keine Marktwerte mehr. Ohne
        # sie ist der Unterbewertet-Index sinnlos - er wuerde jeden Spieler
        # ueber Durchschnitt als unterbewertet ausweisen. Dann lieber weglassen.
        mw_werte = [s.get("marktwert_eur") for s, _ in basis]
        hat_marktwerte = sum(1 for m in mw_werte if m) >= max(3, len(basis) // 3)
        mw_verteilung = [m or 0 for m in mw_werte]

        for s, kw in mitglieder:
            # Nur Index und Wert speichern: der Anzeigename steht einmal in
            # kennzahlen[] am Dateianfang, statt sich je Spieler zu
            # wiederholen, und "cat" leitet das Frontend aus p ab. Bei
            # 18 000 Spielern spart das mehrere Megabyte.
            params = [{
                "i": KENNZAHL_INDEX[anzeige],
                "p": percentil(kw[key], verteilung[key], hoch),
            } for anzeige, key, hoch in felder]

            # Leistungsnote: Mittel der Percentile
            ln = round(sum(p["p"] for p in params) / len(params))

            # Potenzialnote: Leistung plus Altersbonus
            alter = s.get("alter") or 27
            bonus = max(0, min(12, (26 - alter) * 2)) if alter < 26 else 0
            pn = min(99, ln + bonus)

            # Unterbewertet-Index: Leistungspercentil minus Marktwertpercentil
            if hat_marktwerte and s.get("marktwert_eur"):
                mw_p = percentil(s["marktwert_eur"], mw_verteilung, True)
                underval = ln - mw_p
            else:
                underval = None

            ampel, monate = vertrags_ampel(s.get("vertrag_bis"))

            spieler_out.append({
                "id": int(s["id"]),
                "ini": initialen(s["name"]),
                "name": s["name"],
                "pos": s["position"],
                "club": s["verein"],
                "liga": s["liga"],
                "liga_id": s["liga_id"],
                "stufe": (by_frontend_id(s["liga_id"]).stufe
                          if by_frontend_id(s["liga_id"]) else 1),
                "land": s["land"],
                "age": alter,
                "foot": s.get("fuss") or "k. A.",
                "height": f"{s['groesse_cm']} cm" if s.get("groesse_cm") else "k. A.",
                "weight": "k. A.",          # Transfermarkt fuehrt kein Gewicht
                "number": s.get("rueckennummer") or 0,
                "contract": ampel,
                "contract_until": s.get("vertrag_bis"),
                "mv": mw_text(s.get("marktwert_eur")),
                "mv_eur": s.get("marktwert_eur"),
                "ln": ln,
                "pn": pn,
                "underval": underval is not None and underval >= 10,
                "underval_index": underval,
                "minuten": kw["minuten"],
                "einsaetze": kw["einsaetze"],
                "belastbar": kw["belastbar"],
                "params": params,
                # flags und fazit entstehen im Frontend (flagsFuer/fazitFuer).
                # Als Text mitgeliefert waeren sie rund 8 MB - fast die
                # Haelfte der Datei - obwohl sie nur beim Oeffnen eines
                # einzelnen Profils gebraucht werden. Alle Eingangswerte
                # dafuer stehen ohnehin im Datensatz.
            })

    # Ein Spieler kann in einer Saison fuer mehrere Mannschaften auflaufen -
    # typisch Zweitvertretung plus Profikader. Beide Eintraege stehen zu
    # lassen erzeugt Doppel in der Trefferliste, und showProfile() faende
    # immer nur den ersten. Massgeblich ist der Einsatz mit den meisten
    # Minuten; die uebrigen bleiben als Zusatz erhalten, denn ein Kurzeinsatz
    # in der hoeheren Liga ist fuer Scouting eine Information, kein Rauschen.
    nach_id: dict[int, list[dict]] = {}
    for p in spieler_out:
        nach_id.setdefault(p["id"], []).append(p)

    zusammengefasst = []
    for eintraege in nach_id.values():
        eintraege.sort(key=lambda p: -p["minuten"])
        haupt = eintraege[0]
        if len(eintraege) > 1:
            haupt["auch_in"] = [{
                "liga": w["liga"], "club": w["club"], "stufe": w["stufe"],
                "minuten": w["minuten"], "einsaetze": w["einsaetze"],
            } for w in eintraege[1:]]
        zusammengefasst.append(haupt)

    doppelte = len(spieler_out) - len(zusammengefasst)
    spieler_out = zusammengefasst
    spieler_out.sort(key=lambda p: (-p["ln"], p["name"]))

    # 4) Ligenliste fuer das Frontend (aus den echten Daten)
    ligen: dict[str, dict] = {}
    for s in roh["spieler"]:
        lg = by_frontend_id(s["liga_id"])
        eintrag = ligen.setdefault(s["liga_id"], {
            "id": s["liga_id"], "name": s["liga"],
            "land": s["land"], "stufe": lg.stufe if lg else 1,
            "vereine": set(),
        })
        eintrag["vereine"].add(s["verein"])

    # Wie viele bewertete Spieler je Liga - macht duenne Datenlage sichtbar
    bewertet_je_liga: dict[str, int] = {}
    for p in spieler_out:
        bewertet_je_liga[p["liga_id"]] = bewertet_je_liga.get(p["liga_id"], 0) + 1

    # Anteil der Spieler mit Marktwert je Liga. Ein blosses "ja/nein" waere
    # irrefuehrend: in den Oberligen fuehrt die Quelle bei rund 2 Prozent
    # einen Wert - zu wenig fuer den Unterbewertet-Index, aber nicht null.
    def mw_anteil(liga_id: str) -> int:
        gruppe = [p for p in spieler_out if p["liga_id"] == liga_id]
        if not gruppe:
            return 0
        return round(100 * sum(1 for p in gruppe if p["mv_eur"]) / len(gruppe))

    ligen_liste = [{**v, "vereine": sorted(v["vereine"]),
                    "bewertet": bewertet_je_liga.get(v["id"], 0),
                    "marktwert_anteil": mw_anteil(v["id"])}
                   for v in ligen.values()]
    ligen_liste.sort(key=lambda l: (l["stufe"], l["land"], l["name"]))

    os.makedirs(os.path.dirname(ZIEL), exist_ok=True)
    with open(ZIEL, "w", encoding="utf-8") as fh:
        json.dump({
            "stand": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "saison": roh.get("saison"),
            "quellen": roh.get("quellen", []),
            "hinweis": ("Kennzahlen aus frei verfügbaren Quellen. "
                        "xG/xA/progressive Carries sind darin nicht enthalten "
                        "und werden bewusst nicht ausgewiesen."),
            "mindestminuten": MIN_MINUTEN,
            "kennzahlen": KENNZAHL_NAMEN,
            "ligen": ligen_liste,
            "players": spieler_out,
        }, fh, ensure_ascii=False, separators=(",", ":"))

    fest = sum(1 for p in spieler_out if p["belastbar"])
    if doppelte:
        print(f"{doppelte} Doppeleintraege zusammengefasst (Spieler mit "
              f"Einsaetzen fuer mehrere Mannschaften)", file=sys.stderr)
    print(f"{len(spieler_out)} Spieler bewertet, davon {fest} mit belastbarer "
          f"Spielzeit (ab {MIN_MINUTEN} Min) - von {len(roh['spieler'])} "
          f"gesammelt -> {os.path.relpath(ZIEL)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
