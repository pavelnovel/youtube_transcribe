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
- Integrates with Notion to store transcripts and AI-generated insights
- Uses OpenAI's GPT-4 to generate comprehensive insights from transcripts

## Notion Integration

The script can automatically save transcripts and AI-generated insights to your Notion workspace. To use this feature:

1. Create a Notion integration at https://www.notion.so/my-integrations
2. Create a Notion page and share it with your integration
3. Set the following environment variables:
   - `NOTION_API_KEY`: Your Notion integration token
   - `NOTION_PAGE_ID`: The ID of your Notion page (from the page URL)

The script will:
- Create a new page in your Notion workspace for each video
- Save the full transcript with timestamps
- Generate and save AI-powered insights including:
  - Key points and main takeaways
  - Topic analysis
  - Action items and recommendations
  - Technical concepts and definitions
  - Questions for further exploration

## Advanced Features & Suggestions

### Alfred Workflow Integration

For macOS users, you can enhance your workflow by integrating this tool with Alfred:

1. Create a custom Alfred workflow that:
   - Triggers on a custom keyword (e.g., "ytranscribe")
   - Accepts a YouTube URL as input
   - Runs the script with the provided URL
   - Shows a notification when the transcript and insights are ready

2. Benefits of Alfred integration:
   - Quick access to transcript generation from anywhere
   - Keyboard-driven workflow without leaving your current context
   - Customizable notifications for completion status
   - Ability to chain with other Alfred workflows

3. Example Alfred workflow structure:
   ```
   Keyword Input → Script Filter → Run Script → Notification
   ```

This integration is particularly useful for:
- Researchers who frequently need to transcribe YouTube content
- Content creators who want to quickly save video insights
- Students who need to capture lecture content efficiently

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

## OpenAI API Compatibility (Important!)

If you want to use the AI-powered insights feature (which sends the transcript to GPT-4 for summarization and insights), you must use the new OpenAI Python API format (openai>=1.0.0).

**If you see an error like:**

```
You tried to access openai.ChatCompletion, but this is no longer supported in openai>=1.0.0 - see the README at https://github.com/openai/openai-python for the API.
```

This means your code or dependencies are using the old OpenAI API call style. The correct way (as of 2024) is:

```python
client = openai.OpenAI()
response = client.chat.completions.create(
    model="gpt-4.1-nano-2025-04-14",
    messages=[...],
    ...
)
```

**How to fix:**
- Make sure your code uses the new `client.chat.completions.create`

**Do NOT use:**
```python
openai.ChatCompletion.create(...)
```
This will not work with openai>=1.0.0.

If you update your dependencies and see this error, update your code as shown above.

## Recent Updates and Learnings

- **OpenAI API Compatibility**: Ensure you use the new OpenAI Python API format (openai>=1.0.0) for generating insights. The old `openai.ChatCompletion.create` is no longer supported. Use `client.chat.completions.create` instead.
- **Notion API Chunking**: Insights are now chunked into 2000-character blocks before being added to Notion to avoid API length errors. This ensures all content is saved correctly.