#!/usr/bin/env bash
# Vollstaendige Aktualisierung vom eigenen Rechner aus.
#
# Warum nicht in der GitHub Action? Transfermarkt blockt Rechenzentren.
# Aus einem Runner kommt HTTP 202 oder 403 zurueck, selbst ueber den
# Browser-Weg. Vom privaten Anschluss aus antwortet dieselbe Adresse mit
# 200, und zwar in rund 0,6 s statt 4,5 s - der Lauf dauert hier also
# Minuten statt Stunden.
#
#   ./scripts/update_local.sh              # Tagesplan: alle 33 Ligen
#   ./scripts/update_local.sh buli,buli2   # nur diese Ligen
#   PUSH=0 ./scripts/update_local.sh       # ohne Push, nur lokal
#   VERTRAEGE=0 ./scripts/update_local.sh  # ohne den Vertragsende-Lauf
#
set -euo pipefail

cd "$(dirname "$0")/.."

LIGEN="${1:-}"
PUSH="${PUSH:-1}"
PY="${PY:-python3}"

# Einzelne Abrufe bleiben gelegentlich minutenlang haengen (curl beachtet den
# Timeout beim Verbindungsaufbau nicht). Ohne Obergrenze zog sich ein
# Volllauf dadurch schon einmal ueber 14 Stunden. Nicht erreichte Ligen
# behalten ihren Stand, der naechste Lauf holt sie nach.
export SCOUT_BUDGET_MIN="${SCOUT_BUDGET_MIN:-90}"

# Virtuelle Umgebung nutzen, falls vorhanden
for kandidat in .venv/bin/python "$HOME/Faceless Channel/.venv/bin/python"; do
  [ -x "$kandidat" ] && PY="$kandidat" && break
done

echo "Python: $PY"
"$PY" -c "import scrapling" 2>/dev/null || {
  echo "scrapling fehlt. Einmalig einrichten:" >&2
  echo "  $PY -m pip install -r requirements.txt" >&2
  exit 1
}

echo
echo "== Sammeln =="
if [ -n "$LIGEN" ]; then
  "$PY" scripts/build_players.py --ligen "$LIGEN"
else
  "$PY" scripts/build_players.py
fi

echo
echo "== xG-Werte (Understat, nur Topligen) =="
"$PY" scripts/understat.py || echo "  xG uebersprungen - Bestand bleibt gueltig"

# Auslaufende Vertraege. Ein Abruf je Verein und Sommer, also rund 1200
# Seiten - deutlich weniger als der Kaderlauf, aber kein Nebenbei. Wer nur
# schnell die Kader auffrischen will, setzt VERTRAEGE=0.
# Beide Schritte zusammen kosten rund zwei Abrufe je Verein.
if [ "${VERTRAEGE:-1}" = "1" ]; then
  # Zuerst die HEUTIGEN Kader. Der Sammellauf oben liest die Kaderansicht
  # der Saison 2025/26; wer den Verein seither verlassen hat, ist daran
  # nicht zu erkennen. Genau das braucht der Vertragslauf aber: nur bei
  # einem Spieler, der noch im Kader steht, heisst ein fehlender Eintrag
  # "Vertrag laeuft laenger". Nebenbei fuellt dieser Schritt Vertragsenden,
  # Marktwerte, Groesse und Fuss aus der aktuellen Ansicht.
  echo
  echo "== Heutige Kader (Wechsel, Vertraege, Marktwerte) =="
  if [ -n "$LIGEN" ]; then
    "$PY" scripts/build_players.py --kader-aktuell --ligen "$LIGEN" \
      || echo "  uebersprungen - Bestand bleibt gueltig"
  else
    "$PY" scripts/build_players.py --kader-aktuell \
      || echo "  uebersprungen - Bestand bleibt gueltig"
  fi

  echo
  echo "== Auslaufende Vertraege (Transfermarkt) =="
  if [ -n "$LIGEN" ]; then
    "$PY" scripts/vertraege.py --ligen "$LIGEN" \
      || echo "  uebersprungen - Bestand bleibt gueltig"
  else
    "$PY" scripts/vertraege.py || echo "  uebersprungen - Bestand bleibt gueltig"
  fi
fi

echo
echo "== Noten berechnen =="
"$PY" scripts/compute_grades.py

echo
echo "== Frontend pruefen =="
"$PY" scripts/check_frontend.py || {
  echo "Syntaxfehler in index.html - nicht uebertragen." >&2
  exit 1
}

echo
echo "== Uebertragen =="
if [ "$PUSH" != "1" ]; then
  echo "PUSH=0 gesetzt - nur lokal geaendert."
  exit 0
fi

git add data/players.json data/players_raw.json.gz
if git diff --staged --quiet; then
  echo "Keine Aenderungen."
  exit 0
fi
git commit -q -m "Spielerdaten aktualisiert ($(date +%d.%m.%Y))"
git pull --rebase --autostash -q origin main
git push -q origin main
echo "Gepusht. GitHub Pages baut die Seite in ein bis zwei Minuten neu."
