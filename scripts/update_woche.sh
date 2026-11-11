#!/usr/bin/env bash
# Woechentliche Aktualisierung - laeuft von selbst ueber launchd
# (scripts/zeitplan.sh), laesst sich aber auch von Hand starten:
#
#   ./scripts/update_woche.sh                # Wochenlauf
#   TRANSFERTEIL=1 ./scripts/update_woche.sh # Vertraege, Leihen, Fotos erzwingen
#   PUSH=0 ./scripts/update_woche.sh         # nur lokal, nichts uebertragen
#
# Warum ein eigener Lauf neben update_local.sh? Der Volllauf dauerte zuletzt
# rund fuenfeinhalb Stunden - zu lang, um ihn unbemerkt im Hintergrund laufen
# zu lassen. Die Saison 2025/26 ist abgeschlossen; ihre Leistungsdaten aendern
# sich nie mehr. Woechentlich noetig ist nur, was sich bewegt:
#
#   jede Woche        heutige Kader, Marktwerte, Wechsel (rund 670 Abrufe)
#                     Leistungsdaten der laufenden Saison (rund 1.300 Abrufe)
#                     Noten neu rechnen, Mischnote aus beiden Saisons
#   Transferperioden  Vertragsenden mit Optionen, Leihvertraege, Spielerfotos:
#                     jede Woche im Sommerfenster (1.7.-2.9.) und im
#                     Winterfenster (1.1.-2.2.), danach einmal nach Schluss,
#                     damit der Endstand drin ist. Ausserhalb aendert sich daran
#                     kaum etwas - so festgelegt am 02.11.2026. Die Wechsel
#                     selbst erfasst der woechentliche Kaderschritt.
#
# Gemessen: rund 1,5 s je Abruf, also gut 45 Minuten je Woche und eine Stunde
# mehr in den Transferperioden. Jeder Schritt meldet sein Ergebnis in data/status.json;
# die Seite zeigt es in der Datenherkunft. Ein ausgefallener Schritt wird
# dort sichtbar statt still uebersprungen.

set -uo pipefail
cd "$(dirname "$0")/.."

PUSH="${PUSH:-1}"
PY="${PY:-python3}"
for kandidat in .venv/bin/python "$HOME/Faceless Channel/.venv/bin/python"; do
  [ -x "$kandidat" ] && PY="$kandidat" && break
done
export SCOUT_BUDGET_MIN="${SCOUT_BUDGET_MIN:-90}"
SAISON_NEU="$("$PY" -c 'from datetime import date;h=date.today();print(h.year if h.month>=7 else h.year-1)')"
ROH_NEU="data/players_raw_${SAISON_NEU}.json.gz"
KURZ_NEU="$(printf '%s/%02d' "${SAISON_NEU:2:2}" $(( (10#${SAISON_NEU:2:2} + 1) % 100 )))"
START="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

# --- Nur ein Lauf zur Zeit ------------------------------------------------
# Zwei Sammler auf demselben Bestand haben schon Daten gekostet. Dieselbe
# Sperre setzt update_local.sh.
SPERRE=".lauf.lock"
if ! mkdir "$SPERRE" 2>/dev/null; then
  alt_pid="$(cat "$SPERRE/pid" 2>/dev/null || echo)"
  if [ -n "$alt_pid" ] && kill -0 "$alt_pid" 2>/dev/null; then
    echo "Es laeuft bereits eine Aktualisierung (PID $alt_pid) - dieser Lauf entfaellt."
    exit 0
  fi
  echo "Verwaiste Sperre entfernt (PID ${alt_pid:-?} laeuft nicht mehr)."
  rm -rf "$SPERRE"; mkdir "$SPERRE"
fi
echo $$ > "$SPERRE/pid"
trap 'rm -rf "$SPERRE"' EXIT

# Waehrend des Laufs nicht einschlafen (nur Leerlauf-Ruhezustand; ein
# zugeklappter Laptop schlaeft trotzdem - der naechste Lauf holt nach).
command -v caffeinate >/dev/null && caffeinate -i -w $$ &

SCHRITTE=()
schritt() {   # Name, Status (ok|uebersprungen|fehler|gesperrt), Detail, Sekunden
  SCHRITTE+=("$1|$2|$3|$4")
  echo "  -> $1: $2${3:+ ($3)}"
}
TEILAUSFALL=0
laufe() {     # Name, Befehl ... - meldet ok/teilweise/fehler mit Laufzeit
  local name="$1"; shift
  local t0=$SECONDS ausgabe rc
  ausgabe="$("$@" 2>&1)"; rc=$?
  printf '%s\n' "$ausgabe" | tail -40
  local letzte; letzte="$(printf '%s\n' "$ausgabe" | grep -v '^\[20' | grep -v '^\s*$' | tail -1 | cut -c1-160)"
  # Ausfaelle einzelner Ligen oder Vereine ([X], [!], [-]) beenden das Skript
  # nicht mit Fehlercode. Bis 11.11.2026 hiess so ein Schritt trotzdem "ok" -
  # am 04.11. und 10.11. fehlten so unbemerkt je zehn Ligen.
  local ausfaelle; ausfaelle="$(printf '%s\n' "$ausgabe" | grep -cE '^ *\[(X|!|-)\]')"
  TEILAUSFALL=0
  if [ $rc -ne 0 ]; then schritt "$name" fehler "$letzte" $((SECONDS - t0))
  elif [ "$ausfaelle" -gt 0 ]; then
    TEILAUSFALL=1
    schritt "$name" teilweise "$ausfaelle Ausfaelle, z. B. $(printf '%s\n' "$ausgabe" | grep -E '^ *\[(X|!|-)\]' | head -1 | sed 's/^ *//' | cut -c1-110)" $((SECONDS - t0))
  else schritt "$name" ok "$letzte" $((SECONDS - t0)); fi
  return $rc
}

netz_warten() {   # bis zu 15 Minuten
  for i in $(seq 1 30); do
    curl -s -m 10 -o /dev/null https://www.transfermarkt.de && curl -s -m 10 -o /dev/null https://github.com && return 0
    sleep 30
  done
  return 1
}

# Sammelschritt mit einem zweiten Versuch. Faellt unterwegs das Netz aus -
# etwa weil der Mac zugeklappt wurde -, wartet der Lauf auf das Netz und holt
# den Schritt einmal nach. Bereits gelesene Seiten liegen im Zwischenspeicher
# (6 Stunden); der zweite Versuch kostet deshalb nur die fehlenden Abrufe.
sammeln() {   # Name, Befehl ...
  laufe "$@"
  if [ "$TEILAUSFALL" = 1 ]; then
    echo "  Teilausfall - warte auf Netz und versuche es einmal erneut."
    if netz_warten; then
      unset "SCHRITTE[$((${#SCHRITTE[@]}-1))]"
      local name="$1"; shift
      laufe "$name (2. Versuch)" "$@"
    fi
  fi
}

echo "== Netz =="
netz_warten || { echo "Kein Netz nach 15 Minuten - Lauf entfaellt."; exit 1; }
"$PY" -c "import scrapling" 2>/dev/null || { echo "scrapling fehlt: $PY -m pip install -r requirements.txt" >&2; exit 1; }

echo; echo "== Heutige Kader, Marktwerte, Wechsel =="
sammeln "Kader $SAISON_NEU" "$PY" scripts/build_players.py --saison-aktuell

echo; echo "== Leistungsdaten der laufenden Saison =="
# Ohne --frisch: eine Liga, die heute ganz oder teilweise ausfaellt, behaelt
# ihren letzten vollstaendigen Stand (build_players.py).
sammeln "Leistungsdaten $SAISON_NEU" env SCOUT_SAISON="$SAISON_NEU" SCOUT_TARGET="$ROH_NEU" \
  "$PY" scripts/build_players.py

echo; echo "== Sofascore (laufende Saison) =="
# Ein Probeabruf, kein Dauerfeuer: liefert die Bundesliga nicht, entfallen
# die uebrigen Ligen. Seit Herbst 2026 antwortet Sofascore mit HTTP 403.
if [ "${SOFASCORE:-1}" != "1" ]; then
  schritt "Sofascore" uebersprungen "SOFASCORE=0" 0
elif [ ! -f "$ROH_NEU" ]; then
  schritt "Sofascore" uebersprungen "keine Leistungsdaten der laufenden Saison" 0
else
  t0=$SECONDS
  probe="$(SCOUT_TARGET="$ROH_NEU" "$PY" scripts/sofascore.py --ligen buli --saison "$KURZ_NEU" 2>&1)"
  if printf '%s' "$probe" | grep -q "\[X\]"; then
    schritt "Sofascore" gesperrt "$(printf '%s' "$probe" | grep '\[X\]' | head -1 | sed 's/^ *//' | cut -c1-120)" $((SECONDS - t0))
  else
    laufe "Sofascore" env SCOUT_TARGET="$ROH_NEU" "$PY" scripts/sofascore.py --saison "$KURZ_NEU"
  fi
fi

# --- Transferteil -----------------------------------------------------------
# Faellig im Transferfenster und einmal nach dessen Schluss. Das Datum des
# letzten Transferteils steht in data/status.json; fehlt es, gilt der juengste
# Vertragsabruf im Bestand (vertrag.geholt).
TRANSFER_INFO="$("$PY" - <<'PYCODE'
import gzip, json
from datetime import date
h = date.today()
fenster = [(date(y, 7, 1), date(y, 9, 2)) for y in (h.year - 1, h.year)] + \
          [(date(y, 1, 1), date(y, 2, 2)) for y in (h.year, h.year + 1)]
try:
    letzter = json.load(open("data/status.json")).get("transferteil", "")
except Exception:
    letzter = ""
if not letzter:
    try:
        roh = json.load(gzip.open("data/players_raw.json.gz", "rt", encoding="utf-8"))
        daten = [s[k]["geholt"] for s in roh["spieler"] for k in ("vertrag", "vertrag_scan")
                 if isinstance(s.get(k), dict) and s[k].get("geholt")]
        letzter = max(daten) if daten else ""
    except Exception:
        letzter = ""
offen = next(((a, e) for a, e in fenster if a <= h <= e), None)
zu = max((e for a, e in fenster if e < h), default=None)
if offen:
    print(f"ja|Transferfenster bis {offen[1]:%d.%m.}|{letzter}")
elif zu and letzter < zu.isoformat():
    print(f"ja|Endstand nach dem Fenster bis {zu:%d.%m.}|{letzter}")
else:
    naechst = min(a for a, e in fenster if a > h)
    print(f"nein|ausserhalb der Transferperioden, naechster Lauf ab {naechst:%d.%m.%Y}|{letzter}")
PYCODE
)"
TRANSFER_FAELLIG="${TRANSFER_INFO%%|*}"; TRANSFER_REST="${TRANSFER_INFO#*|}"
TRANSFER_GRUND="${TRANSFER_REST%%|*}"; TRANSFERTEIL_ZULETZT="${TRANSFER_REST#*|}"
if [ "${TRANSFERTEIL:-0}" = "1" ] || [ "$TRANSFER_FAELLIG" = "ja" ]; then
  echo; echo "== Transferteil: Vertraege, Leihvertraege, Fotos (${TRANSFER_GRUND:-erzwungen}) =="
  laufe "Vertragsenden" "$PY" scripts/vertraege.py --erneuern
  laufe "Leihvertraege" "$PY" scripts/leihvertraege.py --erneuern
  laufe "Spielerfotos" "$PY" scripts/bilder.py --erneuern
  TRANSFERTEIL_ZULETZT="$(date +%Y-%m-%d)"
else
  schritt "Vertraege, Leihen, Fotos" uebersprungen "$TRANSFER_GRUND" 0
fi

echo; echo "== Noten =="
laufe "Noten" "$PY" scripts/compute_grades.py || { echo "Notenlauf gescheitert - nichts uebertragen." >&2; exit 1; }
laufe "Mischnote" "$PY" scripts/mische_noten.py || { echo "Mischnote gescheitert - nichts uebertragen." >&2; exit 1; }
laufe "Frontend" "$PY" scripts/check_frontend.py || { echo "Syntaxfehler in index.html - nicht uebertragen." >&2; exit 1; }

# --- Plausibilitaet vor dem Veroeffentlichen ---------------------------------
# Zweites Netz unter der Zusammenfuehrung: schrumpft ein Bestand um mehr als
# 10 % gegenueber dem veroeffentlichten Stand, geht er nicht hinaus. Die
# Daten werden auf den letzten Stand zurueckgesetzt, nur der Laufstatus wird
# uebertragen - die Seite sagt dann, dass dieser Lauf verworfen wurde.
SCHRUMPF="$("$PY" - "$ROH_NEU" <<'PYCODE'
import gzip, json, subprocess, sys
def anzahl(d):
    return len(d.get("spieler") or d.get("players") or [])
probleme = []
for pfad in (sys.argv[1], "data/players_raw.json.gz", "data/players.json"):
    gz = pfad.endswith(".gz")
    alt = subprocess.run(["git", "show", "HEAD:" + pfad], capture_output=True)
    if alt.returncode:
        continue                              # noch nie veroeffentlicht
    try:
        a = anzahl(json.loads(gzip.decompress(alt.stdout) if gz else alt.stdout))
        n = anzahl(json.load(gzip.open(pfad, "rt", encoding="utf-8") if gz
                             else open(pfad, encoding="utf-8")))
    except Exception as exc:
        probleme.append(f"{pfad} nicht lesbar ({exc})")
        continue
    if a and n < 0.9 * a:
        probleme.append(f"{pfad.split('/')[-1]}: {a} -> {n} Spieler")
print("; ".join(probleme))
PYCODE
)"
DATEN=(data/players.json data/players_raw.json.gz data/metriken.json "$ROH_NEU")
if [ -n "$SCHRUMPF" ]; then
  schritt "Plausibilitaet" fehler "verworfen, Bestand geschrumpft: $SCHRUMPF" 0
  git checkout -- "${DATEN[@]}" 2>/dev/null
  VEROEFFENTLICHEN=0
else
  schritt "Plausibilitaet" ok "kein Bestand um mehr als 10 % geschrumpft" 0
  VEROEFFENTLICHEN=1
fi

# --- Status fuer die Seite ---------------------------------------------------
printf '%s\n' "${SCHRITTE[@]}" | START="$START" TRANSFERTEIL_ZULETZT="$TRANSFERTEIL_ZULETZT" "$PY" -c '
import json, os, sys
from datetime import datetime, timezone
schritte = []
for z in sys.stdin.read().splitlines():
    if not z.strip(): continue
    name, status, detail, sek = (z.split("|", 3) + ["", "", "", "0"])[:4]
    schritte.append({"name": name, "status": status, "detail": detail, "sekunden": int(sek or 0)})
fehler = [s for s in schritte if s["status"] in ("fehler", "gesperrt", "teilweise")]
json.dump({"art": "wochenlauf", "start": os.environ["START"],
           "ende": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "ergebnis": "teilweise" if fehler else "ok",
           "transferteil": os.environ["TRANSFERTEIL_ZULETZT"], "schritte": schritte},
          open("data/status.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
'

melden() {
  command -v osascript >/dev/null && osascript -e "display notification \"$1\" with title \"ScoutTool\"" 2>/dev/null || true
}

echo; echo "== Uebertragen =="
if [ "$PUSH" != "1" ]; then
  echo "PUSH=0 gesetzt - nur lokal geaendert."; melden "Wochenlauf fertig (nicht uebertragen)"; exit 0
fi
GIT_ID=(-c user.name="Raoul Worek" -c user.email="raoulworek@Air-von-Raoul.fritz.box")
kein_netz() {
  echo "Kein Zugriff auf GitHub - die neuen Daten liegen committet auf diesem Rechner." >&2
  echo "Der naechste Lauf uebertraegt sie nach; von Hand: git pull --rebase origin main && git push origin main" >&2
  melden "Wochenlauf fertig, Uebertragen gescheitert (kein Netz)"; exit 1
}
if [ "$VEROEFFENTLICHEN" = 1 ]; then
  git add data/players.json data/players_raw.json.gz data/metriken.json data/status.json
  [ -f "$ROH_NEU" ] && git add "$ROH_NEU"
else
  git add data/status.json                    # nur der Hinweis, dass verworfen wurde
fi
if ! git diff --staged --quiet; then
  git "${GIT_ID[@]}" commit -q -m "Spielerdaten aktualisiert, Wochenlauf ($(date +%d.%m.%Y))"
fi
git fetch -q origin || kein_netz
if [ -z "$(git log --oneline origin/main..HEAD)" ]; then
  echo "Nichts zu uebertragen."; melden "Wochenlauf fertig - keine Aenderungen"; exit 0
fi
git "${GIT_ID[@]}" pull --rebase --autostash -q origin main || kein_netz
git push -q origin main || kein_netz
echo "Gepusht. GitHub Pages baut die Seite in ein bis zwei Minuten neu."
melden "Wochenlauf fertig und uebertragen"
