#!/usr/bin/env bash
#
# Notistory installer — sets up the notification recorder (systemd --user service)
# and the desktop launcher. Works from wherever the repo is cloned; no hardcoded paths.
#
# Usage:
#   ./install.sh              install and start
#   ./install.sh --uninstall  stop, disable, and remove launchers (keeps recorded data)
#
set -euo pipefail

INSTALL_DIR="$(cd "$(dirname "$(readlink -f "$0")")" && pwd)"
PYTHON="$(command -v python3 || true)"
DESKTOP_DIR="$(xdg-user-dir DESKTOP 2>/dev/null || echo "$HOME/Desktop")"
APPS_DIR="$HOME/.local/share/applications"
SYSTEMD_DIR="$HOME/.config/systemd/user"
SERVICE="notistory.service"
LAUNCHER="notistory.desktop"

uninstall() {
  echo "Uninstalling Notistory..."
  systemctl --user disable --now "$SERVICE" 2>/dev/null || true
  rm -f "$SYSTEMD_DIR/$SERVICE" "$APPS_DIR/$LAUNCHER" "$DESKTOP_DIR/$LAUNCHER"
  systemctl --user daemon-reload 2>/dev/null || true
  update-desktop-database "$APPS_DIR" 2>/dev/null || true
  echo "Done. Recorded history is preserved at ~/.local/share/notistory/"
  exit 0
}

[ "${1:-}" = "--uninstall" ] && uninstall

if [ -z "$PYTHON" ]; then
  echo "ERROR: python3 not found on PATH." >&2
  exit 1
fi

echo "Installing Notistory from: $INSTALL_DIR"

# 1) Make scripts executable
chmod +x "$INSTALL_DIR/src/notify-logger.py" \
         "$INSTALL_DIR/src/generate-data.py" \
         "$INSTALL_DIR/bin/open-notistory.sh"

# 2) Install + start the recorder as a user service (paths resolved from template)
mkdir -p "$SYSTEMD_DIR"
sed -e "s|__PYTHON__|$PYTHON|g" -e "s|__INSTALL_DIR__|$INSTALL_DIR|g" \
    "$INSTALL_DIR/systemd/$SERVICE" > "$SYSTEMD_DIR/$SERVICE"
systemctl --user daemon-reload
systemctl --user enable --now "$SERVICE"

# 3) Install the desktop launcher (app menu + Desktop)
mkdir -p "$APPS_DIR"
sed "s|__INSTALL_DIR__|$INSTALL_DIR|g" "$INSTALL_DIR/$LAUNCHER" > "$APPS_DIR/$LAUNCHER"
chmod +x "$APPS_DIR/$LAUNCHER"
if [ -d "$DESKTOP_DIR" ]; then
  cp "$APPS_DIR/$LAUNCHER" "$DESKTOP_DIR/$LAUNCHER"
  chmod +x "$DESKTOP_DIR/$LAUNCHER"
  gio set "$DESKTOP_DIR/$LAUNCHER" metadata::trusted true 2>/dev/null || true
fi
update-desktop-database "$APPS_DIR" 2>/dev/null || true

# 4) Generate the first snapshot so the UI opens to something
"$PYTHON" "$INSTALL_DIR/src/generate-data.py" || true

echo ""
echo "=== Notistory installed ==="
echo "Recorder:"
systemctl --user status "$SERVICE" --no-pager | head -n 3
echo ""
echo "Launch it from the app menu / Desktop ('Notistory'), or run:"
echo "  $INSTALL_DIR/bin/open-notistory.sh"
