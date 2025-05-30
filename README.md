# YouTube Transcribe

A Python utility for downloading YouTube video transcripts and saving them to text files and Notion database entries.

## Features

- Downloads transcripts from YouTube videos using URL or ID
- Fetches video title for filename using yt-dlp
- Timestamps each transcript entry in MM:SS format
- Saves transcripts with metadata in organized format
- Handles various YouTube URL formats (youtube.com, youtu.be)
- Interactive mode when no arguments provided
- Automatic filename sanitization
- Auto-creates transcripts directory
- Integrates with Notion to store transcripts and AI-generated insights
- Uses OpenAI's GPT-4.1 nano for transcript insights

## Notion Integration

The script can save transcripts and AI-generated insights to your Notion workspace. To use this feature:

1. Create a Notion integration at https://www.notion.so/my-integrations
2. Create a Notion database and share it with your integration
3. Set these environment variables:
   - `NOTION_TOKEN`: Your Notion integration token (secret)
   - `NOTION_DATABASE_ID`: The ID of your Notion database (from the database URL)

The script will:
- Create a new page in your Notion database for each video
- Save the full transcript with timestamps
- Generate and save AI-powered insights including key points and takeaways

## Alfred Workflow Integration

For macOS users, integrate this tool with Alfred:

1. Create a custom Alfred workflow that:
   - Triggers on a keyword (e.g., "ytt")
   - Accepts a YouTube URL as input
   - Runs the script with the provided URL
   - Shows completion notification

2. Benefits:
   - Quick access from anywhere
   - Keyboard-driven workflow
   - Customizable notifications
   - Chain with other Alfred workflows

3. Example workflow structure:
   ```
   Keyword Input → Script Filter → Run Script → Notification
   ```

Useful for:
- Researchers transcribing YouTube content
- Content creators saving video insights
- Students capturing lecture content
- Anyone wanting to learn and build a knowledge base

## Setup

1. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install youtube-transcript-api pytube yt-dlp notion-client python-dotenv openai
```

3. Create a `.env` file in the project root with your API keys:
```bash
NOTION_TOKEN=your_notion_token
NOTION_DATABASE_ID=your_database_id  # This is from your Notion database URL
OPENAI_API_KEY=your_openai_api_key
```

## Usage

### Command Line Arguments

Run with a YouTube URL:
```bash
python youtube_transcribe.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

Run with a youtu.be URL:
```bash
python youtube_transcribe.py "https://youtu.be/dQw4w9WgXcQ"
```

Run with video ID:
```bash
python youtube_transcribe.py "dQw4w9WgXcQ"
```

### Interactive Mode

Run without arguments:
```bash
python youtube_transcribe.py
```

The script will prompt: `What's the YouTube URL?`

## Output

Transcripts are saved in the `transcripts/` directory with the format:
`[Video Title]_[YYYYMMDD_HHMMSS].txt`

Each transcript file includes:
- Video title (cleaned for filename safety)
- Video ID
- Generation timestamp
- Timestamped transcript entries in `[MM:SS] text` format

## Error Handling

The script handles common issues:
- Videos with disabled transcripts: "Transcripts are disabled for this video."
- Videos without available transcripts: "No transcript found for this video."  
- Unavailable videos: "The video is unavailable."
- Video title fetch failures: Falls back to "unknown_title"
- Invalid URLs or video IDs: Generic error handling

## Dependencies

- `youtube-transcript-api`: Fetching YouTube transcripts
- `pytube`: Video metadata (legacy support)
- `yt-dlp`: Reliable video title fetching and metadata
- `notion-client`: Notion API integration
- `python-dotenv`: Environment variable management
- `openai`: OpenAI API integration for insights generation
- `re`: Filename sanitization (built-in)
- `os`: File system operations (built-in)
- `sys`: Command line arguments (built-in)
- `datetime`: Timestamps (built-in)

## File Structure

```
youtube_transcribe/
├── youtube_transcribe.py    # Main script
├── transcripts/            # Output directory (auto-created)
│   ├── Video Title_20250522_104740.txt
│   └── Another Video_20250521_230328.txt
└── venv/                   # Virtual environment
```

The script automatically creates the `transcripts/` directory if it doesn't exist.

## Recent Updates

- **OpenAI API Compatibility**: Uses new OpenAI Python API format (openai>=1.0.0) for generating insights. Use `client.chat.completions.create` instead of deprecated `openai.ChatCompletion.create`.
- **Notion API Chunking**: Insights are chunked into 2000-character blocks before being added to Notion to avoid API length errors.