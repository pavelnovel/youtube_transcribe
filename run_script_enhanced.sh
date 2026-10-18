#!/bin/zsh
# Enhanced Alfred script for YouTube transcription with playlist support

VENV_PATH="/Users/pk/Desktop/dev/youtube_transcribe/venv"
SCRIPT_PATH="/Users/pk/Desktop/dev/youtube_transcribe/youtube_transcribe_enhanced.py"
ORIGINAL_SCRIPT_PATH="/Users/pk/Desktop/dev/youtube_transcribe/youtube_transcribe.py"

# Change to the correct directory
cd "/Users/pk/Desktop/dev/youtube_transcribe"

# Get the query from Alfred
QUERY="$1"

# Determine which script to use based on query
if [[ "$QUERY" == *"playlist"* ]] || [[ "$QUERY" == *"list="* ]]; then
    # Use enhanced script for playlists
    echo "🎵 Detected playlist - using enhanced transcriber"
    "$VENV_PATH/bin/python" "$SCRIPT_PATH" "$QUERY"
elif [[ "$QUERY" == *"--whisper"* ]] || [[ "$QUERY" == *"-w"* ]]; then
    # Use enhanced script with Whisper
    echo "🎤 Using Whisper transcription"
    "$VENV_PATH/bin/python" "$SCRIPT_PATH" "$QUERY" --whisper
else
    # Use enhanced script for single videos (defaults to YouTube API)
    echo "📺 Processing single video"
    "$VENV_PATH/bin/python" "$SCRIPT_PATH" "$QUERY"
fi 