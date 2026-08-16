#!/usr/bin/env python3
"""Abrufschicht fuer Transfermarkt.

Bauweise wie build_news.py im Aktien-Cockpit: jeder Abruf wird einzeln
versucht, Fehler brechen nie den Gesamtlauf ab.

Zwei Stufen, absteigend nach Geschwindigkeit:
  1. Fetcher        - reines HTTP, ~0,6 s pro Seite (Normalfall)
  2. StealthyFetcher - echter Browser, nur wenn Stufe 1 blockiert wird

Zwischenspeicher unter .cache/ verhindert, dass Testlaeufe die Seite
erneut belasten. In der GitHub Action ist der Cache leer, dort zaehlt
nur der hoefliche Abstand zwischen den Abrufen (DELAY).
"""

from __future__ import annotations

import hashlib
import os
import random
import time

CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", ".cache")
BASE = "https://www.transfermarkt.de"
DELAY = float(os.environ.get("TM_DELAY", "1.2"))   # Sekunden zwischen Abrufen
RETRIES = 3
CACHE_TTL = 6 * 3600                                # 6 Stunden

_last_call = 0.0
_stealth_needed = False   # einmal blockiert -> direkt Stufe 2 nutzen


def _cache_path(url: str) -> str:
    key = hashlib.sha1(url.encode()).hexdigest()[:16]
    return os.path.join(CACHE_DIR, f"{key}.html")


def _read_cache(url: str) -> str | None:
    p = _cache_path(url)
    if not os.path.exists(p):
        return None
    if time.time() - os.path.getmtime(p) > CACHE_TTL:
        return None
    try:
        with open(p, encoding="utf-8") as fh:
            return fh.read()
    except OSError:
        return None


def _write_cache(url: str, html: str) -> None:
    os.makedirs(CACHE_DIR, exist_ok=True)
    try:
        with open(_cache_path(url), "w", encoding="utf-8") as fh:
            fh.write(html)
    except OSError:
        pass


def _throttle() -> None:
    """Hoeflicher Abstand zwischen Abrufen, leicht zufaellig."""
    global _last_call
    wait = DELAY + random.uniform(0, 0.4) - (time.time() - _last_call)
    if wait > 0:
        time.sleep(wait)
    _last_call = time.time()


def fetch(path: str, use_cache: bool = True):
    """Holt eine Transfermarkt-Seite und gibt ein Scrapling-Objekt zurueck.

    Wirft nur, wenn alle Versuche beider Stufen scheitern - der Aufrufer
    faengt das ab und markiert die Quelle im Statusbericht als fehlend.
    """
    from scrapling.fetchers import Fetcher, StealthyFetcher
    from scrapling.parser import Selector

    url = path if path.startswith("http") else BASE + path

    if use_cache:
        cached = _read_cache(url)
        if cached is not None:
            return Selector(cached)

    global _stealth_needed
    last_err: Exception | None = None

    for attempt in range(RETRIES):
        try:
            _throttle()
            if not _stealth_needed:
                page = Fetcher.get(url, timeout=30)
                if page.status == 200:
                    _write_cache(url, page.html_content)
                    return page
                if page.status in (403, 429):
                    _stealth_needed = True     # ab jetzt Browser verwenden
                else:
                    last_err = RuntimeError(f"HTTP {page.status}")

            if _stealth_needed:
                page = StealthyFetcher.fetch(
                    url, headless=True, network_idle=True,
                    solve_cloudflare=True, timeout=120000,
                )
                if page.status == 200:
                    _write_cache(url, page.html_content)
                    return page
                last_err = RuntimeError(f"HTTP {page.status} (stealth)")
        except Exception as exc:          # Netzfehler, Zeitueberschreitung
            last_err = exc

        time.sleep(2 ** attempt)          # 1 s, 2 s, 4 s

    raise RuntimeError(f"{url}: {last_err}")


def cell_text(td) -> str:
    """Sichtbarer Text einer Tabellenzelle, Leerraum normalisiert."""
    parts = [" ".join(str(t).split()) for t in td.css("::text") if str(t).strip()]
    return " ".join(parts).strip()
