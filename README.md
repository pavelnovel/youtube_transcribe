# YouTube Transcribe

A Python utility for downloading and saving YouTube video transcripts to text files.

## Features

- Downloads transcripts from YouTube videos using video URL or ID
- Automatically fetches video title for filename using yt-dlp
- Timestamps each transcript entry in MM:SS format
- Saves transcripts in organized format with metadata
- Handles various YouTube URL formats (youtube.com, youtu.be)
- Interactive mode when no arguments provided
- Automatic filename sanitization for safe file storage
- Creates transcripts directory automatically

## Setup

1. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install youtube-transcript-api pytube yt-dlp
```

## Usage

### Command Line Arguments

Run the script with a YouTube URL:
```bash
python youtube_transcribe.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

Run with a youtu.be short URL:
```bash
python youtube_transcribe.py "https://youtu.be/dQw4w9WgXcQ"
```

Run with just the video ID:
```bash
python youtube_transcribe.py "dQw4w9WgXcQ"
```

### Interactive Mode

Run without arguments for interactive input:
```bash
python youtube_transcribe.py
```

The script will prompt: `What's the YouTube URL?`

## Output

Transcripts are saved in the `transcripts/` directory with the format:
`[Video Title]_[YYYYMMDD_HHMMSS].txt`

### Example Output File

```
YouTube Transcript for Video: AI Agents, Clearly Explained
Video ID: FwOTs4UxQS4
Generated on: 2025-05-22 10:47:42
==================================================

[00:03] AI. AI. AI. AI. AI.
[00:07] AI. You know, more agentic. Agentic
[00:10] capabilities. An AI agent. Agents.
...
```

Each transcript file includes:
- Video title (cleaned for filename safety)
- Video ID
- Generation timestamp
- Timestamped transcript entries in `[MM:SS] text` format

## Error Handling

The script handles common issues with informative error messages:
- Videos with disabled transcripts: "Transcripts are disabled for this video."
- Videos without available transcripts: "No transcript found for this video."  
- Unavailable videos: "The video is unavailable."
- Video title fetch failures: Falls back to "unknown_title"
- Invalid URLs or video IDs: Generic error handling

## Dependencies

- `youtube-transcript-api`: For fetching YouTube transcripts
- `pytube`: For video metadata (legacy support)
- `yt-dlp`: For reliable video title fetching and metadata
- `re`: For filename sanitization (built-in)
- `os`: For file system operations (built-in)
- `sys`: For command line arguments (built-in)
- `datetime`: For timestamps (built-in)

## File Structure

```
youtube_transcribe/
├── youtube_transcribe.py    # Main script
├── transcripts/            # Output directory (auto-created)
│   ├── Video Title_20250522_104740.txt
│   └── Another Video_20250521_230328.txt
└── venv/                   # Virtual environment
```

The script automatically creates the `transcripts/` directory relative to the script location if it doesn't exist.