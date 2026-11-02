#!/usr/bin/env bash
# Zeitplan fuer den Wochenlauf (scripts/update_woche.sh) auf diesem Mac.
#
#   ./scripts/zeitplan.sh an        # einrichten: dienstags 07:00
#   ./scripts/zeitplan.sh aus       # wieder entfernen
#   ./scripts/zeitplan.sh status    # eingerichtet? letzter Lauf?
#   ./scripts/zeitplan.sh jetzt     # sofort einmal laufen lassen
#
# launchd startet den Lauf dienstags um 07:00 - dann sind die Spiele vom
# Wochenende und Montag eingetragen. Schlaeft der Mac zu der Zeit, holt
# launchd den Lauf beim naechsten Aufwachen nach (verpasste Termine werden
# zu einem Lauf zusammengefasst). Ist er ganz ausgeschaltet, entfaellt der
# Termin; der naechste Dienstag holt alles nach.

set -euo pipefail
cd "$(dirname "$0")/.."
REPO="$(pwd)"
LABEL="de.scouttool.wochenlauf"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
LOGS="$HOME/Library/Logs/ScoutTool"
DOMAIN="gui/$(id -u)"

case "${1:-status}" in
  an)
    mkdir -p "$HOME/Library/LaunchAgents" "$LOGS"
    cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>$LABEL</string>
  <key>ProgramArguments</key>
  <array>
    <string>/bin/bash</string>
    <string>$REPO/scripts/update_woche.sh</string>
  </array>
  <key>WorkingDirectory</key><string>$REPO</string>
  <key>StartCalendarInterval</key>
  <dict>
    <key>Weekday</key><integer>2</integer>
    <key>Hour</key><integer>7</integer>
    <key>Minute</key><integer>0</integer>
  </dict>
  <key>EnvironmentVariables</key>
  <dict>
    <key>PATH</key><string>/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
  </dict>
  <key>StandardOutPath</key><string>$LOGS/wochenlauf.log</string>
  <key>StandardErrorPath</key><string>$LOGS/wochenlauf.log</string>
  <key>ProcessType</key><string>Background</string>
  <key>LowPriorityIO</key><true/>
</dict>
</plist>
EOF
    launchctl bootout "$DOMAIN/$LABEL" 2>/dev/null || true
    launchctl bootstrap "$DOMAIN" "$PLIST"
    echo "Eingerichtet: dienstags 07:00, Protokoll in $LOGS/wochenlauf.log"
    ;;
  aus)
    launchctl bootout "$DOMAIN/$LABEL" 2>/dev/null || true
    rm -f "$PLIST"
    echo "Zeitplan entfernt."
    ;;
  jetzt)
    launchctl kickstart "$DOMAIN/$LABEL" && echo "Gestartet - Protokoll: $LOGS/wochenlauf.log"
    ;;
  status)
    if launchctl print "$DOMAIN/$LABEL" >/dev/null 2>&1; then
      echo "Zeitplan aktiv (dienstags 07:00)."
    else
      echo "Kein Zeitplan eingerichtet."
    fi
    if [ -f data/status.json ]; then
      /usr/bin/python3 -c 'import json;s=json.load(open("data/status.json"));print("Letzter Lauf:",s.get("ende"),"-",s.get("ergebnis"));[print("  ",x["name"]+":",x["status"],x.get("detail","")[:90]) for x in s.get("schritte",[])]'
    fi
    [ -f "$LOGS/wochenlauf.log" ] && { echo "--- Protokoll (Ende)"; tail -5 "$LOGS/wochenlauf.log"; } || true
    ;;
  *) echo "Aufruf: $0 an|aus|status|jetzt" >&2; exit 1 ;;
esac
