#!/usr/bin/env python3
"""
Enhanced YouTube Transcriber with Playlist Support and Whisper Integration
Combines ideas from bulk_transcribe_youtube_videos_from_playlist with existing Notion/AI features
Usage: python3 youtube_transcribe_enhanced.py "{query}"
Query can be: single video URL, playlist URL, or video ID
"""

import asyncio
import json
import os
import re
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Union

import openai
import yt_dlp
from dotenv import load_dotenv
from notion_client import Client
from tqdm import tqdm
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound, VideoUnavailable

# Optional Whisper support
try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    print("Whisper not available. Install with: pip install openai-whisper")

# Load environment variables
load_dotenv()

# Configuration
NOTION_TOKEN = os.getenv('NOTION_TOKEN')
NOTION_DATABASE_ID = os.getenv('NOTION_DATABASE_ID')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
TRANSCRIPTS_DIR = os.getenv("TRANSCRIPTS_DIR", os.path.expanduser("~/Desktop/content/youtube_transcripts"))

# Initialize clients
notion = Client(auth=NOTION_TOKEN) if NOTION_TOKEN else None
openai.api_key = OPENAI_API_KEY

class EnhancedYouTubeTranscriber:
    def __init__(self, use_whisper: bool = False, whisper_model: str = "base"):
        self.use_whisper = use_whisper and WHISPER_AVAILABLE
        self.whisper_model = None
        if self.use_whisper:
            print(f"Loading Whisper model: {whisper_model}")
            self.whisper_model = whisper.load_model(whisper_model)
        
        os.makedirs(TRANSCRIPTS_DIR, exist_ok=True)
        self.semaphore = asyncio.Semaphore(3)  # Limit concurrent downloads
    
    def extract_video_info(self, url: str) -> Dict:
        """Extract video information using yt-dlp."""
        try:
            with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                return ydl.extract_info(url, download=False)
        except Exception as e:
            print(f"Error extracting video info: {e}")
            return {}
    
    def get_playlist_videos(self, url: str) -> List[Dict]:
        """Extract all video URLs from a playlist."""
        try:
            with yt_dlp.YoutubeDL({'quiet': True, 'extract_flat': True}) as ydl:
                info = ydl.extract_info(url, download=False)
                if 'entries' in info:
                    videos = []
                    for entry in info['entries']:
                        if entry:
                            videos.append({
                                'id': entry.get('id', ''),
                                'title': entry.get('title', 'Unknown'),
                                'url': f"https://www.youtube.com/watch?v={entry.get('id', '')}"
                            })
                    return videos
        except Exception as e:
            print(f"Error extracting playlist: {e}")
        return []
    
    def get_video_id(self, url: str) -> str:
        """Extract video ID from various YouTube URL formats."""
        patterns = [
            r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
            r'youtu\.be\/([0-9A-Za-z_-]{11})',
            r'^([0-9A-Za-z_-]{11})$'  # Direct video ID
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return url
    
    def clean_filename(self, text: str) -> str:
        """Clean text for safe filename usage."""
        return re.sub(r'[\\/*?:"<>|]', "", text)
    
    async def download_audio_whisper(self, video_url: str, video_id: str) -> Optional[str]:
        """Download audio for Whisper transcription."""
        try:
            audio_path = f"/tmp/{video_id}.mp3"
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': audio_path,
                'quiet': True,
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }]
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([video_url])
            
            return audio_path if os.path.exists(audio_path) else None
        except Exception as e:
            print(f"Error downloading audio: {e}")
            return None
    
    def transcribe_with_whisper(self, audio_path: str) -> Dict:
        """Transcribe audio using Whisper."""
        try:
            result = self.whisper_model.transcribe(
                audio_path,
                word_timestamps=True,
                verbose=False
            )
            
            # Convert to our standard format
            segments = []
            for segment in result.get('segments', []):
                segments.append({
                    'text': segment['text'].strip(),
                    'start': round(segment['start'], 2),
                    'end': round(segment['end'], 2),
                    'confidence': round(segment.get('avg_logprob', 0), 2)
                })
            
            return {
                'text': result['text'],
                'segments': segments,
                'language': result.get('language', 'unknown')
            }
        except Exception as e:
            print(f"Error with Whisper transcription: {e}")
            return {'text': '', 'segments': [], 'language': 'unknown'}
    
    def transcribe_with_youtube_api(self, video_id: str) -> Dict:
        """Transcribe using YouTube's API."""
        try:
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
            
            text = ""
            segments = []
            for entry in transcript_list:
                text += f"{entry['text']} "
                segments.append({
                    'text': entry['text'],
                    'start': round(entry['start'], 2),
                    'end': round(entry['start'] + entry['duration'], 2),
                    'confidence': 1.0  # YouTube API doesn't provide confidence
                })
            
            return {
                'text': text.strip(),
                'segments': segments,
                'language': 'auto-detected'
            }
        except (TranscriptsDisabled, NoTranscriptFound, VideoUnavailable) as e:
            print(f"YouTube API error: {e}")
            return {'text': '', 'segments': [], 'language': 'unknown'}
    
    def chunk_text(self, text: str, chunk_size: int = 2000) -> List[str]:
        """Split text into chunks."""
        return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
    
    def generate_insights(self, transcript_text: str) -> Optional[str]:
        """Generate AI insights using OpenAI."""
        if not OPENAI_API_KEY:
            return None
        
        try:
            prompt = f"""You will be given a transcript of a conversation or speech. Your task is to summarize it and extract insights. Follow these instructions:

1. Read the transcript:
{transcript_text[:4000]}  # Limit to avoid token limits

2. Write a 3-sentence summary. Be concise and sharp. Avoid phrases like "he said" or "XYZ advocates..."—just state the ideas. Start with what the format is (e.g., "Fireside chat with..." or "Video from..."). Sentence fragments preferred.

3. Generate 5 bullet points of compelling insights. Tailor these for a highly educated generalist who is a Marketer, Philosopher, AI Builder, Entrepreneur, Technologist, Media and Community builder. Think about relevance, hidden angles, and non-obvious applications. Use short, sharp fragments.

4. Format:
   - First: the 3-sentence summary
   - Then: 5 bullet point insights

Keep the total under 1900 characters. Do not include any commentary or extra text outside the specified output."""

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
            
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error generating insights: {e}")
            return None
    
    def add_to_notion(self, title: str, url: str, transcript_data: Dict, insights: Optional[str]):
        """Add transcript and insights to Notion database."""
        if not notion:
            return
        
        try:
            transcript_text = transcript_data['text']
            transcript_chunks = self.chunk_text(transcript_text, 2000)
            
            children_blocks = [
                {
                    "object": "block",
                    "type": "heading_1",
                    "heading_1": {"rich_text": [{"type": "text", "text": {"content": "Transcript"}}]}
                }
            ]
            
            for chunk in transcript_chunks:
                children_blocks.append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {"rich_text": [{"type": "text", "text": {"content": chunk}}]}
                })
            
            if insights:
                children_blocks.append({
                    "object": "block",
                    "type": "heading_1", 
                    "heading_1": {"rich_text": [{"type": "text", "text": {"content": "AI-Generated Insights"}}]}
                })
                
                insights_chunks = self.chunk_text(insights, 2000)
                for chunk in insights_chunks:
                    children_blocks.append({
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {"rich_text": [{"type": "text", "text": {"content": chunk}}]}
                    })
            
            new_page = {
                "parent": {"database_id": NOTION_DATABASE_ID},
                "properties": {
                    "Title": {"title": [{"text": {"content": title}}]},
                    "URL": {"url": url},
                    "Transcript": {"rich_text": [{"text": {"content": transcript_text[:1900] + "..." if len(transcript_text) > 1900 else transcript_text}}]},
                    "Insights": {"rich_text": [{"text": {"content": insights[:1900] + "..." if insights and len(insights) > 1900 else (insights or "No insights generated")}}]},
                    "Date": {"date": {"start": datetime.now().isoformat()}}
                },
                "children": children_blocks
            }
            
            notion.pages.create(**new_page)
            print(f"✅ Added to Notion: {title}")
        except Exception as e:
            print(f"❌ Error adding to Notion: {e}")
    
    def save_transcript_files(self, title: str, video_id: str, url: str, transcript_data: Dict, insights: Optional[str]) -> str:
        """Save transcript in multiple formats."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        clean_title = self.clean_filename(title)
        base_filename = f"{clean_title}_{timestamp}"
        
        # Text file
        txt_path = Path(TRANSCRIPTS_DIR) / f"{base_filename}.txt"
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(f"YouTube Transcript: {title}\n")
            f.write(f"Video ID: {video_id}\n")
            f.write(f"URL: {url}\n")
            f.write(f"Generated: {datetime.now():%Y-%m-%d %H:%M:%S}\n")
            f.write(f"Method: {'Whisper' if self.use_whisper else 'YouTube API'}\n")
            f.write(f"Language: {transcript_data.get('language', 'unknown')}\n")
            f.write("="*80 + "\n\n")
            f.write(transcript_data['text'])
            
            if insights:
                f.write(f"\n\n{'='*80}\n")
                f.write("AI-GENERATED INSIGHTS\n")
                f.write("="*80 + "\n\n")
                f.write(insights)
        
        # JSON file with metadata
        json_path = Path(TRANSCRIPTS_DIR) / f"{base_filename}.json"
        json_data = {
            'title': title,
            'video_id': video_id,
            'url': url,
            'generated_at': datetime.now().isoformat(),
            'method': 'Whisper' if self.use_whisper else 'YouTube API',
            'language': transcript_data.get('language', 'unknown'),
            'transcript': transcript_data['text'],
            'segments': transcript_data.get('segments', []),
            'insights': insights
        }
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
        
        return str(txt_path)
    
    async def process_video(self, video_info: Dict, pbar: Optional[tqdm] = None) -> bool:
        """Process a single video."""
        async with self.semaphore:
            try:
                video_id = video_info['id']
                title = video_info['title']
                url = video_info['url']
                
                if pbar:
                    pbar.set_description(f"Processing: {title[:50]}...")
                
                # Choose transcription method
                if self.use_whisper:
                    # Download audio and transcribe with Whisper
                    audio_path = await self.download_audio_whisper(url, video_id)
                    if audio_path:
                        transcript_data = self.transcribe_with_whisper(audio_path)
                        # Cleanup
                        if os.path.exists(audio_path):
                            os.remove(audio_path)
                    else:
                        # Fallback to YouTube API
                        transcript_data = self.transcribe_with_youtube_api(video_id)
                else:
                    transcript_data = self.transcribe_with_youtube_api(video_id)
                
                if not transcript_data['text']:
                    print(f"❌ No transcript available for: {title}")
                    return False
                
                # Generate insights
                insights = self.generate_insights(transcript_data['text'])
                
                # Save files
                txt_path = self.save_transcript_files(title, video_id, url, transcript_data, insights)
                
                # Add to Notion
                self.add_to_notion(title, url, transcript_data, insights)
                
                print(f"✅ Completed: {title}")
                print(f"📄 Saved to: {txt_path}")
                
                if pbar:
                    pbar.update(1)
                
                return True
                
            except Exception as e:
                print(f"❌ Error processing video {video_info.get('title', 'Unknown')}: {e}")
                if pbar:
                    pbar.update(1)
                return False
    
    async def process_videos(self, videos: List[Dict]):
        """Process multiple videos with progress tracking."""
        if not videos:
            print("No videos to process")
            return
        
        print(f"\n🚀 Processing {len(videos)} video(s)...")
        
        with tqdm(total=len(videos), desc="Transcribing videos") as pbar:
            tasks = [self.process_video(video, pbar) for video in videos]
            results = await asyncio.gather(*tasks, return_exceptions=True)
        
        successful = sum(1 for r in results if r is True)
        print(f"\n✅ Successfully processed {successful}/{len(videos)} videos")
        print(f"📁 Transcripts saved to: {TRANSCRIPTS_DIR}")
    
    def run(self, query: str, use_whisper: bool = False):
        """Main entry point - supports single videos, playlists, or video IDs."""
        query = query.strip()
        
        # Determine if it's a playlist or single video
        if 'playlist' in query.lower() or 'list=' in query:
            print("🎵 Detected playlist URL")
            videos = self.get_playlist_videos(query)
            if not videos:
                print("❌ Could not extract videos from playlist")
                return
        else:
            # Single video
            video_id = self.get_video_id(query)
            if not query.startswith('http'):
                url = f"https://www.youtube.com/watch?v={video_id}"
            else:
                url = query
            
            # Get video info
            info = self.extract_video_info(url)
            if not info:
                print(f"❌ Could not get video info for: {query}")
                return
            
            videos = [{
                'id': video_id,
                'title': info.get('title', 'Unknown Title'),
                'url': url
            }]
        
        # Process videos
        asyncio.run(self.process_videos(videos))

def main():
    """Main function for command-line usage."""
    if len(sys.argv) < 2:
        print("Usage: python3 youtube_transcribe_enhanced.py \"{query}\"")
        print("Query can be: YouTube URL, playlist URL, or video ID")
        sys.exit(1)
    
    query = sys.argv[1]
    
    # Check for optional Whisper flag
    use_whisper = len(sys.argv) > 2 and sys.argv[2].lower() in ['--whisper', '-w']
    
    # Initialize and run transcriber
    transcriber = EnhancedYouTubeTranscriber(use_whisper=use_whisper)
    transcriber.run(query, use_whisper)

if __name__ == "__main__":
    main() 