#!/usr/bin/env bash
# Antigravity 2.0 • Grok Bot Studio Launcher
set -e
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PATH="$HOME/.local/bin:$HOME/.gemini/antigravity-cli/bin:$PATH"
python3 "$DIR/main.py" "$@"
