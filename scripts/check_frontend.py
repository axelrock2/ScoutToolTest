#!/usr/bin/env python3
"""Prueft index.html auf Syntaxfehler im JavaScript.

Anlass: ein ueberzaehliges Anfuehrungszeichen legte einmal die gesamte
Seite lahm - sichtbar war nur eine leere Trefferliste, der Fehler stand
in der Browserkonsole. So etwas darf nicht bis zur Veroeffentlichung
durchrutschen.

Braucht node. Fehlt es, wird die Pruefung uebersprungen statt zu
scheitern - sie ist eine Absicherung, keine Voraussetzung.

    python3 scripts/check_frontend.py
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SEITE = Path(__file__).resolve().parent.parent / "index.html"


def main() -> int:
    if not SEITE.exists():
        print(f"{SEITE} fehlt", file=sys.stderr)
        return 1

    node = shutil.which("node")
    if not node:
        print("node nicht gefunden - Pruefung uebersprungen", file=sys.stderr)
        return 0

    html = SEITE.read_text(encoding="utf-8")
    bloecke = re.findall(r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>", html, re.S)
    if not bloecke:
        print("kein Skriptblock gefunden", file=sys.stderr)
        return 1

    fehler = 0
    for nr, code in enumerate(bloecke, 1):
        with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False,
                                         encoding="utf-8") as fh:
            fh.write(code)
            pfad = fh.name
        ergebnis = subprocess.run([node, "--check", pfad],
                                  capture_output=True, text=True)
        Path(pfad).unlink(missing_ok=True)
        if ergebnis.returncode != 0:
            fehler += 1
            print(f"Skriptblock {nr}: Syntaxfehler", file=sys.stderr)
            for zeile in ergebnis.stderr.splitlines()[:6]:
                print(f"   {zeile}", file=sys.stderr)

    if fehler:
        return 1
    zeichen = sum(len(b) for b in bloecke)
    print(f"index.html: {len(bloecke)} Skriptblock(e), {zeichen} Zeichen, "
          f"Syntax in Ordnung")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
