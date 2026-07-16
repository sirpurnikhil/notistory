#!/usr/bin/env bash
# Regenerate the notification snapshot, then open the UI in the default browser.
set -euo pipefail

# Resolve the project directory from this script's location (clone anywhere).
DIR="$(cd "$(dirname "$(readlink -f "$0")")/.." && pwd)"

python3 "$DIR/src/generate-data.py"
xdg-open "$DIR/src/index.html" >/dev/null 2>&1 &
