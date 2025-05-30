#!/bin/zsh
VENV_PATH="/Users/pk/Desktop/dev/youtube_transcribe/venv"
SCRIPT_PATH="/Users/pk/Desktop/dev/youtube_transcribe/youtube_transcribe.py"
VIDEO_URL="$1"

"$VENV_PATH/bin/python" "$SCRIPT_PATH" "$VIDEO_URL" 