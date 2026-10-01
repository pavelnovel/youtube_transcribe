#!/usr/bin/env bash
# Portable runner: uses the venv next to this script, works from any directory.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PYTHON="$SCRIPT_DIR/venv/bin/python"

if [ ! -x "$VENV_PYTHON" ]; then
    echo "Virtual environment not found at $SCRIPT_DIR/venv" >&2
    echo "Create it with: python3 -m venv venv && venv/bin/pip install -r requirements.txt" >&2
    exit 1
fi

exec "$VENV_PYTHON" "$SCRIPT_DIR/youtube_transcribe.py" "$@"
