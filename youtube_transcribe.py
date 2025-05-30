from youtube_transcript_api import YouTubeTranscriptApi
from pytube import YouTube
from datetime import datetime
import os
import re
import sys
import yt_dlp
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound, VideoUnavailable
from notion_client import Client
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize Notion client
NOTION_TOKEN = os.getenv('NOTION_TOKEN')
NOTION_DATABASE_ID = os.getenv('NOTION_DATABASE_ID')
notion = Client(auth=NOTION_TOKEN) if NOTION_TOKEN else None

def chunk_text(text, chunk_size=2000):
    # Split text into chunks of at most chunk_size
    return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]

def add_to_notion(title, url, transcript_path, transcript_text):
    if not notion:
        print("Notion integration not configured. Set NOTION_TOKEN and NOTION_DATABASE_ID environment variables.")
        return
    
    try:
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

def save_transcript(video_id, url):
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_path = os.path.dirname(os.path.abspath(__file__))
        transcript_dir = os.path.join(base_path, "transcripts")
        os.makedirs(transcript_dir, exist_ok=True)
        title = get_video_title(url)
        filename = os.path.join(transcript_dir, f"{title}_{timestamp}.txt")
        
        # Prepare transcript text
        transcript_text = f"YouTube Transcript for Video: {title}\nVideo ID: {video_id}\nGenerated on: {datetime.now():%Y-%m-%d %H:%M:%S}\n{'='*50}\n\n"
        for entry in transcript:
            transcript_text += f"{entry['text']}\n"
        
        # Save to file
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(transcript_text)
        
        # Add to Notion database with transcript content
        add_to_notion(title, url, filename, transcript_text)
        
        print(filename)
    except TranscriptsDisabled:
        print("Transcripts are disabled for this video.")
    except NoTranscriptFound:
        print("No transcript found for this video.")
    except VideoUnavailable:
        print("The video is unavailable.")
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
