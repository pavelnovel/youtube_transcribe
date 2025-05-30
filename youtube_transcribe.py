from youtube_transcript_api import YouTubeTranscriptApi
from pytube import YouTube
from datetime import datetime
import os
import re
import sys
import yt_dlp
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound, VideoUnavailable

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
        base_path = os.path.dirname(os.path.abspath(__file__))  # Always points to your script's folder
        transcript_dir = os.path.join(base_path, "transcripts")
        os.makedirs(transcript_dir, exist_ok=True)
        title = get_video_title(url)
        filename = os.path.join(transcript_dir, f"{title}_{timestamp}.txt")
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"YouTube Transcript for Video: {title}\nVideo ID: {video_id}\nGenerated on: {datetime.now():%Y-%m-%d %H:%M:%S}\n{'='*50}\n\n")
            for entry in transcript:
                m, s = divmod(int(entry['start']), 60)
                f.write(f"[{m:02d}:{s:02d}] {entry['text']}\n")
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
