#!/usr/bin/env bash
# Collects a local diagnostic report for bug reports — never uploads anything.
# Deliberately excludes notification content (summary/body): only counts, sizes,
# versions, and service/journal status are captured.
set -uo pipefail

DIR="$(cd "$(dirname "$(readlink -f "$0")")/.." && pwd)"
DATA_DIR="$HOME/.local/share/notistory"
CONFIG_DIR="$HOME/.config/notistory"
LOG_PATH="$DATA_DIR/notifications.jsonl"
OUT="$DATA_DIR/diagnostic-report.txt"
SERVICE="notistory.service"

{
  echo "=== Notistory diagnostic report ==="
  echo "Generated: $(date -Iseconds)"
  echo

  echo "--- Version ---"
  if command -v git >/dev/null 2>&1 && git -C "$DIR" rev-parse --short HEAD >/dev/null 2>&1; then
    echo "Commit: $(git -C "$DIR" rev-parse --short HEAD) ($(git -C "$DIR" branch --show-current 2>/dev/null))"
  else
    echo "Commit: unknown (not a git checkout, or git not installed)"
  fi
  echo

  echo "--- OS / Desktop ---"
  [ -f /etc/os-release ] && grep -E '^(NAME|VERSION)=' /etc/os-release
  echo "Desktop: ${XDG_CURRENT_DESKTOP:-unknown}"
  echo "Session type: ${XDG_SESSION_TYPE:-unknown}"
  echo

  echo "--- Python / dependencies ---"
  echo "python3: $(command -v python3 || echo 'NOT FOUND')"
  python3 --version 2>&1
  python3 -c "import dbus; print('dbus-python:', dbus.__version__)" 2>&1
  python3 -c "import gi; print('python3-gi: OK')" 2>&1
  echo

  echo "--- Service status ---"
  systemctl --user status "$SERVICE" --no-pager 2>&1 | head -n 10
  echo

  echo "--- Recent journal (last 50 lines) ---"
  journalctl --user -u "$SERVICE" -n 50 --no-pager 2>&1
  echo

  echo "--- Storage ---"
  if [ -f "$LOG_PATH" ]; then
    echo "Log size: $(du -h "$LOG_PATH" | cut -f1)"
    echo "Log entries: $(wc -l < "$LOG_PATH")"
  else
    echo "Log file not found at $LOG_PATH"
  fi
  echo

  echo "--- Config (config.json) ---"
  if [ -f "$CONFIG_DIR/config.json" ]; then
    cat "$CONFIG_DIR/config.json"
  else
    echo "No config.json (defaults in use)"
  fi
  echo

} > "$OUT" 2>&1

echo "Diagnostic report written to: $OUT"
echo "It contains no notification content — safe to attach to a GitHub issue."
echo
echo "File a bug report here (attach the report above):"
echo "  https://github.com/sirpurnikhil/notistory/issues/new/choose"

if command -v xdg-open >/dev/null 2>&1; then
  xdg-open "https://github.com/sirpurnikhil/notistory/issues/new/choose" >/dev/null 2>&1 &
fi
