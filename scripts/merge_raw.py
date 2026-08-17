#!/usr/bin/env python3
"""Fuegt die Teilergebnisse paralleler Sammellaeufe zusammen.

Die Action sammelt die 33 Ligen in mehreren Jobs gleichzeitig, weil ein
einzelner Lauf ueber den Browser-Weg an die 90 Minuten braucht. Jeder Job
schreibt seine eigene Datei; dieses Skript legt sie uebereinander und
ergaenzt den bestehenden Bestand um die neu geholten Ligen.

    python3 scripts/merge_raw.py teile/*.json.gz

Ligen, die in keinem Teil vorkommen, behalten ihren letzten Stand - eine
Liga, die heute ausfaellt, verschwindet also nicht aus dem Tool.
"""

from __future__ import annotations

import glob
import gzip
import json
import os
import sys
from datetime import datetime, timezone

ZIEL = os.path.join(os.path.dirname(__file__), "..", "data",
                    "players_raw.json.gz")


def lade(pfad: str) -> dict | None:
    try:
        with gzip.open(pfad, "rt", encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError) as exc:
        print(f"  [!] {pfad}: {exc}", file=sys.stderr)
        return None


def main() -> int:
    muster = sys.argv[1:]
    if not muster:
        print("Aufruf: merge_raw.py <datei-oder-muster> ...", file=sys.stderr)
        return 2

    pfade: list[str] = []
    for m in muster:
        pfade.extend(sorted(glob.glob(m)) if any(c in m for c in "*?[") else [m])
    pfade = [p for p in pfade if os.path.exists(p) and os.path.abspath(p)
             != os.path.abspath(ZIEL)]
    if not pfade:
        print("Keine Teildateien gefunden - Bestand bleibt unangetastet.",
              file=sys.stderr)
        return 1

    spieler: list[dict] = []
    quellen: list[dict] = []
    neu_ids: set[str] = set()
    saison = None

    for p in pfade:
        teil = lade(p)
        if not teil or not teil.get("spieler"):
            continue
        saison = saison or teil.get("saison")
        spieler.extend(teil["spieler"])
        quellen.extend(teil.get("quellen", []))
        neu_ids.update(s.get("liga_id") for s in teil["spieler"])
        print(f"  {os.path.basename(p)}: {len(teil['spieler'])} Spieler",
              file=sys.stderr)

    if not spieler:
        print("Alle Teile leer - Bestand bleibt unangetastet.", file=sys.stderr)
        return 1

    # Bestand um die nicht neu geholten Ligen ergaenzen
    if os.path.exists(ZIEL):
        alt = lade(ZIEL)
        if alt:
            behalten = [s for s in alt.get("spieler", [])
                        if s.get("liga_id") not in neu_ids]
            alt_quellen = [q for q in alt.get("quellen", [])
                           if q.get("id") not in neu_ids]
            if behalten:
                print(f"  {len(behalten)} Spieler aus {len(alt_quellen)} nicht "
                      f"erneuerten Ligen uebernommen", file=sys.stderr)
            spieler = behalten + spieler
            quellen = alt_quellen + quellen
            saison = saison or alt.get("saison")

    quellen.sort(key=lambda q: q.get("liga", ""))

    with gzip.open(ZIEL, "wt", encoding="utf-8") as fh:
        json.dump({
            "stand": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "saison": saison,
            "quellen": quellen,
            "spieler": spieler,
        }, fh, ensure_ascii=False, separators=(",", ":"))

    ligen = len({s.get("liga_id") for s in spieler})
    print(f"\n{len(spieler)} Spieler aus {ligen} Ligen -> "
          f"{os.path.relpath(ZIEL)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
