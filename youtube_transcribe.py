from youtube_transcript_api import (
    YouTubeTranscriptApi,
    TranscriptsDisabled,
    NoTranscriptFound,
    VideoUnavailable,
)
from datetime import datetime
import os
import re
import shutil
import sys
import tempfile
import yt_dlp
from notion_client import Client
import json
from dotenv import load_dotenv
import openai

# Load environment variables from .env file
load_dotenv()

# Initialize Notion client
NOTION_TOKEN = os.getenv('NOTION_TOKEN')
NOTION_DATABASE_ID = os.getenv('NOTION_DATABASE_ID')
notion = Client(auth=NOTION_TOKEN) if NOTION_TOKEN else None

# Initialize OpenAI client
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
openai.api_key = OPENAI_API_KEY

def chunk_text(text, chunk_size=2000):
    # Split text into chunks of at most chunk_size
    return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]

def generate_insights(transcript_text):
    if not OPENAI_API_KEY:
        print("OpenAI API key not configured. Set OPENAI_API_KEY environment variable.")
        return None
    
    try:
        print(f"Using OpenAI API key: {OPENAI_API_KEY[:8]}...")  # Print first 8 chars for verification
        print(f"Transcript text being sent to OpenAI API: {transcript_text[:100]}...")  # Print first 100 chars for verification
        prompt = f"""You will be given a transcript of a conversation or speech. Your task is to summarize it and extract insights. Follow these instructions:

1. Read the transcript:
{transcript_text}

2. Write a 3-sentence summary. Be concise and sharp. Avoid phrases like "he said" or "XYZ advocates..." or "they discuss..."—just state the ideas. Start with what the format is (e.g., "Fireside chat with..."). Sentence fragments preferred.

3. Generate 5 bullet points of compelling insights. Tailor these for a highly educated generalist who is a Marketer, Philosopher, AI Builder, Entrepreneur, Technologist, Media and Community builder. Think about relevance, hidden angles, and non-obvious applications. Use short, sharp fragments.

4. Format:
   - First: the 3-sentence summary
   - Then: 5 bullet point insights

Keep the total under 1900 characters. Do not include any commentary or extra text outside the specified output. IMPORTANT: DO NOT SAY "XYZ emphasized" or "He advocates" in any of the sentences in the summary, you can just start with the sentence fragment."""

        print("Sending request to OpenAI API...")
        client = openai.OpenAI()
        response = client.chat.completions.create(
            model="gpt-4.1-nano-2025-04-14",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that provides insightful analysis of transcripts."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2000
        )
        
        print("Received response from OpenAI API")
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error generating insights: {str(e)}")
        print(f"Error type: {type(e)}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        return None

def add_to_notion(title, url, transcript_path, transcript_text):
    if not notion:
        print("Notion integration not configured. Set NOTION_TOKEN and NOTION_DATABASE_ID environment variables.")
        return
    
    try:
        # Generate insights using GPT-4
        insights = generate_insights(transcript_text)
        
        # Chunk transcript for Notion page body
        transcript_chunks = chunk_text(transcript_text, 2000)
        children_blocks = [
            {
                "object": "block",
                "type": "heading_1",
                "heading_1": {
                    "rich_text": [{"type": "text", "text": {"content": "Transcript"}}]
                }
            }
        ]
        for chunk in transcript_chunks:
            children_blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": chunk}}]
                }
            })
            
        # Add insights section if available
        if insights:
            # Chunk insights for Notion page body
            insights_chunks = chunk_text(insights, 2000)
            children_blocks.append({
                "object": "block",
                "type": "heading_1",
                "heading_1": {
                    "rich_text": [{"type": "text", "text": {"content": "AI-Generated Insights"}}]
                }
            })
            for chunk in insights_chunks:
                children_blocks.append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "text": {"content": chunk}}]
                    }
                })
        
        # Create a new page in the database
        new_page = {
            "parent": {"database_id": NOTION_DATABASE_ID},
            "properties": {
                "Title": {
                    "title": [
                        {
                            "text": {
                                "content": title
                            }
                        }
                    ]
                },
                "URL": {
                    "url": url
                },
                "Transcript": {
                    "rich_text": [
                        {
                            "text": {
                                "content": transcript_text[:1900] + "..." if len(transcript_text) > 1900 else transcript_text
                            }
                        }
                    ]
                },
                "Insights": {
                    "rich_text": [
                        {
                            "text": {
                                "content": insights[:1900] + "..." if insights and len(insights) > 1900 else (insights or "No insights generated")
                            }
                        }
                    ]
                },
                "Date": {
                    "date": {
                        "start": datetime.now().isoformat()
                    }
                }
            },
            "children": children_blocks
        }
        
        notion.pages.create(**new_page)
        print(f"Successfully added to Notion database: {title}")
    except Exception as e:
        print(f"Error adding to Notion: {e}")

def get_video_id(url):
    if 'youtube.com/watch?v=' in url:
        return url.split('v=')[1].split('&')[0]
    if 'youtu.be/' in url:
        return url.split('youtu.be/')[1].split('?')[0]
    return url

def get_video_title(url):
    try:
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(url, download=False)
            title = info.get('title', 'unknown_title')
            # Clean the title to be safe for filenames
            title = re.sub(r'[\\/*?:"<>|]', "", title)
            return title
    except Exception as e:
        print(f"Could not fetch video title: {e}")
        return "unknown_title"

def format_timestamp(seconds):
    # Format seconds as MM:SS
    total = int(seconds)
    return f"{total // 60:02d}:{total % 60:02d}"

def download_audio(url):
    """Download the best audio track of a YouTube video to a temp dir.

    Returns (tmpdir, audio_path), or (None, None) on failure. Caller cleans up tmpdir.
    """
    tmpdir = tempfile.mkdtemp(prefix="whisper_audio_")
    try:
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(tmpdir, 'audio.%(ext)s'),
            'quiet': True,
            'noplaylist': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        files = [f for f in os.listdir(tmpdir) if os.path.isfile(os.path.join(tmpdir, f))]
        if not files:
            print("Whisper fallback: audio download produced no file.")
            shutil.rmtree(tmpdir, ignore_errors=True)
            return None, None
        return tmpdir, os.path.join(tmpdir, files[0])
    except Exception as e:
        print(f"Whisper fallback: could not download audio: {e}")
        shutil.rmtree(tmpdir, ignore_errors=True)
        return None, None

def _patch_av_metadata_errors():
    """Compatibility shim: faster-whisper 1.2.x passes metadata_errors to
    av.open(), but PyAV >= 15 no longer accepts that kwarg. Retry without it
    when the installed av rejects it, so transcription works with whatever
    av version pip resolves."""
    try:
        import av
    except Exception:
        return
    _orig_open = av.open
    def _open(*args, **kwargs):
        try:
            return _orig_open(*args, **kwargs)
        except TypeError as e:
            if "metadata_errors" in kwargs and "metadata_errors" in str(e):
                kwargs.pop("metadata_errors")
                return _orig_open(*args, **kwargs)
            raise
    av.open = _open

def transcribe_audio_file(audio_path, model_name=None):
    """Transcribe a local audio file with faster-whisper (open-source, runs on CPU).

    Returns a list of (start_seconds, text) tuples, or None on failure.
    """
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        print("Whisper fallback needs faster-whisper: pip install -r requirements.txt")
        return None
    _patch_av_metadata_errors()
    model_name = model_name or os.getenv('WHISPER_MODEL', 'base')
    try:
        print(f"Transcribing audio locally with Whisper ({model_name} model)...")
        model = WhisperModel(model_name, device="cpu", compute_type="int8")
        segments, _info = model.transcribe(audio_path)
        return [(seg.start, seg.text.strip()) for seg in segments if seg.text.strip()]
    except Exception as e:
        print(f"Whisper fallback: transcription failed: {e}")
        return None

def transcribe_with_whisper(url):
    """Fallback transcription: download audio, transcribe locally. Free, no API keys."""
    tmpdir, audio_path = download_audio(url)
    if not audio_path:
        return None
    try:
        return transcribe_audio_file(audio_path)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

def save_transcript(video_id, url):
    try:
        # youtube-transcript-api v1.x: instance-based API returning snippet objects
        transcript = YouTubeTranscriptApi().fetch(video_id)
        segments = [(entry.start, entry.text) for entry in transcript]
        source = "YouTube captions"
    except (TranscriptsDisabled, NoTranscriptFound):
        print("No captions available for this video — falling back to local Whisper transcription (free, runs on this machine).")
        segments = transcribe_with_whisper(url)
        if not segments:
            print("No transcript found for this video.")
            return
        source = "Whisper (local transcription)"
    except VideoUnavailable:
        print("The video is unavailable.")
        return
    except Exception as e:
        print(f"Error: {e}")
        return

    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_path = os.path.dirname(os.path.abspath(__file__))
        transcript_dir = os.path.join(base_path, "transcripts")
        os.makedirs(transcript_dir, exist_ok=True)
        title = get_video_title(url)
        filename = os.path.join(transcript_dir, f"{title}_{timestamp}.txt")

        # Prepare transcript text
        transcript_text = f"YouTube Transcript for Video: {title}\nVideo ID: {video_id}\nSource: {source}\nGenerated on: {datetime.now():%Y-%m-%d %H:%M:%S}\n{'='*50}\n\n"
        for start, text in segments:
            transcript_text += f"[{format_timestamp(start)}] {text}\n"

        # Save to file
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(transcript_text)

        # Add to Notion database with transcript content
        add_to_notion(title, url, filename, transcript_text)

        print(filename)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) >= 2:
        url = sys.argv[1].strip()
    else:
        url = input("What's the YouTube URL? ").strip()
    video_id = get_video_id(url)
    # If the input is not a full URL, construct one
    if not url.startswith("http"):
        url = f"https://www.youtube.com/watch?v={video_id}"
    save_transcript(video_id, url)  # Pass the final, valid URL
