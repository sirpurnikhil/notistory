#!/usr/bin/env bash
# Regenerate the notification snapshot, then open the UI in the default browser.
set -euo pipefail

# Resolve the project directory from this script's location (clone anywhere).
DIR="$(cd "$(dirname "$(readlink -f "$0")")/.." && pwd)"

# This is launched from a desktop icon with no visible terminal, so a failure here must
# be surfaced to the user instead of silently doing nothing.
ERR_LOG="$(mktemp)"
if ! python3 "$DIR/src/generate-data.py" 2>"$ERR_LOG"; then
  MSG="Notistory couldn't refresh the notification history. Run $DIR/bin/notistory-diagnose.sh for details."
  echo "$MSG" >&2
  cat "$ERR_LOG" >&2
  rm -f "$ERR_LOG"
  if command -v notify-send >/dev/null 2>&1; then
    notify-send -u critical "Notistory error" "$MSG"
  elif command -v zenity >/dev/null 2>&1; then
    zenity --error --text="$MSG" 2>/dev/null
  fi
  exit 1
fi
rm -f "$ERR_LOG"

xdg-open "$DIR/src/index.html" >/dev/null 2>&1 &
