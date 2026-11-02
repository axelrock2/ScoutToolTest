#!/usr/bin/env python3
"""Mischnote: abgeschlossene Notensaison plus laufende Saison nach Minuten.

Freigegeben am 02.11.2026 (Variante "Mischnote K = 1.800").

Die Noten beruhten bis dahin allein auf der Saison 2025/26. Die laufende
Saison einfach an ihre Stelle zu setzen, waere nach zehn Spieltagen Zufall:
gemessen in Regionalliga West und Oberliga Westfalen haette sich jede zweite
Note um 15 Punkte oder mehr bewegt, und die Noten beider Saisons haengen in
derselben Liga nur maessig zusammen (Korrelation 0,36 bis 0,43). Deshalb
zaehlt die neue Saison nach Einsatzminuten:

    Note = (Minuten neu x Note neu + K x Note alt) / (Minuten neu + K)

mit K = 1.800 Minuten, also rund zwanzig volle Spiele. Nach einer halben
Saison traegt die neue Saison rund ein Drittel, nach einer ganzen rund 60 %.

Regeln, jede mit Grund:
  - Die neue Saison zaehlt erst ab der Mindestspielzeit (450 Minuten) - wie
    jede Note. Darunter bleibt die alte Note stehen.
  - Ohne belastbare alte Note gilt die neue allein. So werden Neuzugaenge
    bewertbar, die bisher ohne Note im Kader standen.
  - Die alte Note wird vorher auf das Niveau der Liga der neuen Saison
    umgerechnet - dieselbe Formel und Schwelle wie im Frontend
    (0,55 Punkte je Niveaupunkt, erst ab 6 Punkten Abstand).
  - Ligen mit Sofascore-Kennzahlen (bis zur 3. Liga) bleiben vorerst bei der
    alten Note: Sofascore liefert seit Herbst 2026 nicht mehr, und eine neue
    Note nur aus Transfermarkt-Werten waere ein anderes Notenmodell als die
    alte. Freischalten mit MISCH_SOFASCORE_LIGEN=1, sobald die Werte der
    neuen Saison vorliegen - vorher die Wirkung messen.
  - Kennzahlen, Teilnoten und Leistungsdaten der alten Saison bleiben
    unveraendert stehen; die Akte nennt, woraus sich die Note zusammensetzt.

Aufruf (nach compute_grades.py):
    python3 scripts/mische_noten.py
"""

from __future__ import annotations

import gzip
import json
import os
import subprocess
import sys
import tempfile
from collections import Counter
from datetime import date

HIER = os.path.dirname(os.path.abspath(__file__))
DATEN = os.path.join(HIER, "..", "data")
K = int(os.environ.get("MISCH_K", "1800"))
NIVEAU_FAKTOR = 0.55
NIVEAU_SCHWELLE = 6

# Ligen, deren Noten auf Sofascore-Kennzahlen beruhen (siehe sofascore.py).
SOFASCORE_LIGEN = {"buli", "buli2", "l3", "pl", "champ", "laliga", "laliga2",
                   "seriea", "serieb", "ligue1", "ligue2", "jupiler",
                   "primeira", "oebuli", "ekstraklasa", "chance-liga"}


def laufende_saison() -> int:
    h = date.today()
    return h.year if h.month >= 7 else h.year - 1


def bonus(alter) -> int:
    """Altersbonus der Potenzial-Note, wie in compute_grades.py."""
    a = alter or 27
    return max(0, min(12, (26 - a) * 2)) if a < 26 else 0


def auf_niveau(ln: int, von: float, nach: float) -> int:
    diff = nach - von
    if abs(diff) < NIVEAU_SCHWELLE:
        return ln
    return max(1, min(99, round(ln - NIVEAU_FAKTOR * diff)))


def kompakt(reihen: list, p: dict) -> list:
    """Leistungszeilen ohne Wiederholung: Liga und Verein stehen nur, wenn sie
    von den heutigen Angaben des Spielers abweichen (spart rund 1 MB)."""
    out = []
    for r in reihen:
        z = {"sp": r.get("sp"), "min": r.get("min"), "ld": r.get("ld")}
        if r.get("club") != p.get("club"):
            z["club"] = r.get("club")
        if r.get("liga") != p.get("liga"):
            z["liga"] = r.get("liga")
        if r.get("liga_id") and r.get("liga_id") != p.get("liga_id"):
            z["liga_id"] = r["liga_id"]
        out.append(z)
    return out


def neue_saison_bewerten(roh_neu: str) -> dict:
    """Die laufende Saison mit demselben Notenlauf wie die alte bewerten -
    in eine Zwischendatei, die echte players.json bleibt unberuehrt."""
    with tempfile.TemporaryDirectory() as tmp:
        ziel = os.path.join(tmp, "players.json")
        env = dict(os.environ, SCOUT_QUELLE=roh_neu, SCOUT_ZIEL=ziel)
        lauf = subprocess.run([sys.executable, os.path.join(HIER, "compute_grades.py")],
                              env=env, capture_output=True, text=True)
        if lauf.returncode != 0:
            raise RuntimeError("Notenlauf der neuen Saison gescheitert:\n" + lauf.stderr[-800:])
        with open(ziel, encoding="utf-8") as fh:
            return json.load(fh)


def main() -> int:
    ziel = os.environ.get("MISCH_ZIEL") or os.path.join(DATEN, "players.json")
    with open(ziel, encoding="utf-8") as fh:
        d = json.load(fh)

    alt_jahr = int(str(d.get("saison") or "2025/26")[:4])
    neu_jahr = int(os.environ.get("MISCH_SAISON") or laufende_saison())
    if neu_jahr <= alt_jahr:
        print(f"Laufende Saison {neu_jahr} ist die Notensaison - nichts zu mischen.")
        return 0
    if neu_jahr > alt_jahr + 1:
        # Ab Juli 2027: 2026/27 muss erst selbst Notensaison werden, sonst
        # mischte dieses Skript 2025/26 mit 2027/28 und liesse eine ganze
        # Saison aus. Lieber ungemischt lassen und es sagen.
        print(f"Saisonwechsel noetig: Notensaison {d.get('saison')}, laufend {neu_jahr} - "
              f"Note bleibt ungemischt, bis {neu_jahr - 1} Notensaison ist.")
        return 0
    roh_neu = os.environ.get("MISCH_ROH") or os.path.join(DATEN, f"players_raw_{neu_jahr}.json.gz")
    if not os.path.exists(roh_neu):
        print(f"{roh_neu} fehlt - Note bleibt bei {d.get('saison')}.", file=sys.stderr)
        return 0
    with gzip.open(roh_neu, "rt", encoding="utf-8") as fh:
        roh = json.load(fh)
    mit_sofa = os.environ.get("MISCH_SOFASCORE_LIGEN") == "1"

    neu_d = neue_saison_bewerten(roh_neu)
    min_min = d.get("mindestminuten") or 450
    niveau = {l["id"]: l.get("niveau") for l in d["ligen"]}
    lname = {l["id"]: l["name"] for l in d["ligen"]}
    saison_neu = f"{neu_jahr}/{str(neu_jahr + 1)[2:]}"

    # Spieltage je Liga (haeufigste Zahl Mannschaftsspiele im Rohbestand)
    spieltage: dict[str, int] = {}
    je: dict[str, Counter] = {}
    for s in roh["spieler"]:
        n = (s.get("team") or {}).get("spiele")
        if n:
            je.setdefault(s["liga_id"], Counter())[n] += 1
    for lid, c in je.items():
        spieltage[lid] = c.most_common(1)[0][0]

    alt = {p["id"]: p for p in d["players"]}
    ohne = {o["id"]: o for o in d.get("ohne_note_spieler", [])}
    zaehl = Counter()

    for n in neu_d["players"]:
        pid = n["id"]
        lid = n["liga_id"]
        reihen = [{"liga": n.get("liga"), "liga_id": lid, "club": n.get("club"), "sp": n.get("einsaetze"),
                   "min": n.get("minuten"), "ld": n.get("ld")}]
        reihen += [{"liga": a["liga"], "club": a["club"], "sp": a.get("einsaetze"),
                    "min": a.get("minuten"), "ld": a.get("ld")} for a in n.get("auch_in", []) if a.get("ld")]
        p = alt.get(pid)
        if p is not None:
            p["ld_neu"] = kompakt(reihen, p)   # Leistungsdaten der laufenden Saison, fuer die Akte

        if not n.get("belastbar"):
            continue                          # unter der Mindestspielzeit: alte Note bleibt
        if lid in SOFASCORE_LIGEN and not mit_sofa:
            zaehl["gehalten"] += 1
            continue
        neu_info = {"ln": n["ln"], "min": n["minuten"], "liga": lname.get(lid, n.get("liga")),
                    "liga_id": lid, "club": n.get("club")}

        if p is not None and p.get("belastbar"):
            von = p.get("niveau") if isinstance(p.get("niveau"), (int, float)) else niveau.get(p["liga_id"], 50)
            nach = niveau.get(lid, 50)
            ln_alt = auf_niveau(p["ln"], von, nach)
            w = n["minuten"] / (n["minuten"] + K)
            p["misch"] = {"w": round(100 * w),
                          "alt": {"ln": p["ln"], "auf": ln_alt, "min": p.get("minuten"),
                                  "liga": p.get("note_liga") or p.get("liga"),
                                  "club": p.get("note_club") or p.get("club")},
                          "neu": neu_info}
            p["ln"] = round(w * n["ln"] + (1 - w) * ln_alt)
            p["pn"] = min(99, p["ln"] + bonus(p.get("age")))
            # Die Mischnote steht auf dem Niveau der Liga der neuen Saison.
            p["niveau"] = nach
            for k in ("note_club", "note_liga", "note_liga_id", "note_stufe"):
                p.pop(k, None)
            if lid != p["liga_id"]:
                p.update(note_club=n.get("club"), note_liga=lname.get(lid), note_liga_id=lid,
                         note_stufe=n.get("stufe"))
            zaehl["gemischt"] += 1
            continue

        # Keine belastbare alte Note: die neue Saison gilt allein.
        felder = ("ln", "pn", "params", "teilnoten", "anteil_team", "basis", "belastbar",
                  "niveau", "underval", "underval_index")
        info = {"w": 100, "alt": ({"ln": p["ln"], "min": p.get("minuten"), "duenn": True}
                                  if p is not None else None), "neu": neu_info}
        if p is not None:
            for k in felder:
                if k in n:
                    p[k] = n[k]
            p["niveau"] = niveau.get(lid, p.get("niveau"))
            for k in ("note_club", "note_liga", "note_liga_id", "note_stufe"):
                p.pop(k, None)
            if lid != p["liga_id"]:
                p.update(note_club=n.get("club"), note_liga=lname.get(lid), note_liga_id=lid,
                         note_stufe=n.get("stufe"))
            p["misch"] = info
            zaehl["nur_neu_war_duenn"] += 1
            continue

        # Bisher ohne Note im Kader (oder gar nicht erfasst): neu aufnehmen.
        q = dict(n)
        q["niveau"] = niveau.get(lid, q.get("niveau"))
        q["misch"] = info
        q["ld_neu"] = kompakt(reihen, q)
        # Was nur der Hauptbestand kennt - Vertrag, Bild, Rueckennummer -,
        # aus dem Eintrag "ohne Note" uebernehmen.
        o = ohne.pop(pid, None)
        if o:
            for k in ("bild", "contract_until", "number", "mv", "mv_eur"):
                if o.get(k) not in (None, "") and not q.get(k):
                    q[k] = o[k]
            for l in d["ligen"]:
                if l["id"] == o.get("liga_id") and o.get("club") in (l.get("ohne_note") or {}):
                    l["ohne_note"][o["club"]] -= 1
                    if l["ohne_note"][o["club"]] <= 0:
                        del l["ohne_note"][o["club"]]
        for l in d["ligen"]:
            if l["id"] == q["liga_id"]:
                l["bewertet"] = (l.get("bewertet") or 0) + 1
        # Die Leistungszeile der Akte zeigt sonst die neue Saison doppelt.
        q.update(minuten=0, einsaetze=0)
        q.pop("ld", None)
        d["players"].append(q)
        alt[pid] = q
        zaehl["nur_neu_aufgenommen"] += 1

    d["ohne_note_spieler"] = list(ohne.values()) if d.get("ohne_note_spieler") is not None else []
    d["notenbasis"] = {
        "alt": d.get("saison"), "neu": saison_neu, "k": K, "mindestminuten": min_min,
        "stand_neu": roh.get("stand"), "spieltage": spieltage,
        "gehalten": sorted(SOFASCORE_LIGEN) if not mit_sofa else [],
        "gemischt": zaehl["gemischt"],
        "nur_neu": zaehl["nur_neu_war_duenn"] + zaehl["nur_neu_aufgenommen"],
    }
    with open(ziel, "w", encoding="utf-8") as fh:
        json.dump(d, fh, ensure_ascii=False, separators=(",", ":"))
    print(f"Mischnote {d.get('saison')} + {saison_neu} (K = {K}): {zaehl['gemischt']} gemischt, "
          f"{zaehl['nur_neu_war_duenn']} bisher duenn, {zaehl['nur_neu_aufgenommen']} neu bewertet, "
          f"{zaehl['gehalten']} in Sofascore-Ligen gehalten.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
