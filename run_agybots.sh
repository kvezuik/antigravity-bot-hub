#!/usr/bin/env bash
# Antigravity 2.0 • Desktop Studio Launcher
set -e
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PATH="$HOME/.local/bin:$HOME/.gemini/antigravity-cli/bin:$PATH"
export PYTHONPATH="$HOME/.local/lib/python3.14/site-packages:$DIR:$PYTHONPATH"
if [ -n "$WAYLAND_DISPLAY" ]; then
    export QT_QPA_PLATFORM="wayland;xcb"
fi
exec python3 "$DIR/main.py" "$@"
