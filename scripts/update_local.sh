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
#   GEGENPROBE=0 ./scripts/update_local.sh # ohne die FotMob-Gegenprobe
#   LEIHVERTRAEGE=0 ./scripts/update_local.sh  # ohne Stammvertraege der Leihspieler
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

echo
echo "== Spielerstatistik (Sofascore, bis zur 3. Liga) =="
if [ -n "$LIGEN" ]; then
  "$PY" scripts/sofascore.py --ligen "$LIGEN" \
    || echo "  Sofascore uebersprungen - Bestand bleibt gueltig"
else
  "$PY" scripts/sofascore.py || echo "  Sofascore uebersprungen - Bestand bleibt gueltig"
fi

# Gegenprobe gegen FotMob (Opta). Kostet rund zwanzig Abrufe und sagt,
# ob die Sofascore-Zaehlwerte mit einem zweiten Anbieter uebereinstimmen.
# Das Ergebnis steht danach in der Datenherkunft auf der Seite.
if [ "${GEGENPROBE:-1}" = "1" ]; then
  echo
  echo "== Gegenprobe (FotMob/Opta gegen Sofascore) =="
  "$PY" scripts/gegenprobe.py || echo "  Gegenprobe uebersprungen - alter Stand bleibt"
fi

# Vertrag beim Stammverein fuer Leihspieler - ein Abruf je AUFNEHMENDEM
# Verein (Leihspieler-Seite, rund 290), nicht je Spieler. Erst dieses Datum
# sagt, ob ein Leihspieler wirklich frei wird. --erneuern, weil sich
# Vertraege beim Stammverein auch waehrend einer Leihe aendern und bei rund
# 290 Abrufen ein voller Abgleich tragbar ist. Das Skript pausiert zwischen
# den Abrufen, bricht nach mehreren Fehlern in Folge ab und speichert, was
# es hat.
if [ "${LEIHVERTRAEGE:-1}" = "1" ]; then
  echo
  echo "== Vertraege beim Stammverein (Leihspieler) =="
  "$PY" scripts/leihvertraege.py --erneuern || echo "  Leihvertraege uebersprungen - Bestand bleibt gueltig"
fi

# Auslaufende Vertraege. Ein Abruf je Verein und Sommer, also rund 1200
# Seiten - deutlich weniger als der Kaderlauf, aber kein Nebenbei. Wer nur
# schnell die Kader auffrischen will, setzt VERTRAEGE=0.
# Beide Schritte zusammen kosten rund zwei Abrufe je Verein.
if [ "${VERTRAEGE:-1}" = "1" ]; then
  # Zuerst Vereine und HEUTIGE Kader der laufenden Saison. Der Sammellauf
  # oben liest die Notensaison; wer seither gewechselt ist, welche Vereine
  # auf- oder abgestiegen sind, ist daran nicht zu erkennen. Dieser Schritt
  # ordnet jeden Spieler seinem heutigen Verein zu, nimmt Neuzugaenge auf
  # und fuellt Vertragsenden, Marktwerte, Groesse und Fuss aus der
  # aktuellen Ansicht. Bilder- und Vertragslauf bauen darauf auf.
  echo
  echo "== Vereine und Kader der laufenden Saison =="
  if [ -n "$LIGEN" ]; then
    "$PY" scripts/build_players.py --saison-aktuell --ligen "$LIGEN" \
      || echo "  uebersprungen - Bestand bleibt gueltig"
  else
    "$PY" scripts/build_players.py --saison-aktuell \
      || echo "  uebersprungen - Bestand bleibt gueltig"
  fi

  # --erneuern: alle Vereine, nicht nur solche ohne ein einziges Foto. Sonst
  # bekaemen Neuzugaenge bei Vereinen, die schon Fotos haben, nie eins - und
  # genau die zeigt die Kaderansicht. Rund 20 Minuten.
  echo
  echo "== Spielerfotos (Adressen) =="
  if [ -n "$LIGEN" ]; then
    "$PY" scripts/bilder.py --erneuern --ligen "$LIGEN" \
      || echo "  uebersprungen - Bestand bleibt gueltig"
  else
    "$PY" scripts/bilder.py --erneuern || echo "  uebersprungen - Bestand bleibt gueltig"
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

# Identitaet ausdruecklich: die Erkennung ueber die Git-Konfiguration ist auf
# diesem Rechner schon ausgefallen, und die Historie ist oeffentlich.
GIT_ID=(-c user.name="Raoul Worek" -c user.email="raoulworek@Air-von-Raoul.fritz.box")

kein_netz() {
  echo "Kein Zugriff auf GitHub - die neuen Daten liegen committet auf diesem Rechner." >&2
  echo "Sobald wieder Netz da ist, genuegt ein neuer Lauf; er uebertraegt sie nach." >&2
  echo "Von Hand geht es auch:  git pull --rebase origin main && git push origin main" >&2
  exit 1
}

# metriken.json gehoert dazu: compute_grades.py schreibt sie im selben Lauf,
# und die Akte laedt sie fuer die Kennzahlen. Fehlte sie im Commit, stuenden
# neue Noten neben alten Kennzahlen (am 23.09.2026 genau so passiert).
git add data/players.json data/players_raw.json.gz data/metriken.json
if git diff --staged --quiet; then
  echo "Keine neuen Daten zum Einchecken."
else
  git "${GIT_ID[@]}" commit -q -m "Spielerdaten aktualisiert ($(date +%d.%m.%Y))"
fi

# Auch ohne neue Daten uebertragen, was noch lokal liegt. Genau daran
# scheiterte der Lauf vom 23.09.2026: der Commit war da, nur der Push fehlte,
# und ein zweiter Lauf haette ihn mit "Keine Aenderungen" liegen lassen.
git fetch -q origin || kein_netz
if [ -z "$(git log --oneline origin/main..HEAD)" ]; then
  echo "Nichts zu uebertragen - der Stand auf GitHub ist aktuell."
  exit 0
fi

git "${GIT_ID[@]}" pull --rebase --autostash -q origin main || kein_netz
git push -q origin main || kein_netz
echo "Gepusht. GitHub Pages baut die Seite in ein bis zwei Minuten neu."
