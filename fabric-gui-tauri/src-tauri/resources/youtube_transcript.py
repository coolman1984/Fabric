import sys
import json
import re
import argparse
from youtube_transcript_api import YouTubeTranscriptApi

def extract_video_id(url_or_id):
    url_or_id = url_or_id.strip()
    if re.match(r'^[a-zA-Z0-9_-]{11}$', url_or_id):
        return url_or_id
    patterns = [
        r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([a-zA-Z0-9_-]{11})',
        r'(?:youtube\.com/v/)([a-zA-Z0-9_-]{11})',
        r'[?&]v=([a-zA-Z0-9_-]{11})',
        r'youtube\.com/shorts/([a-zA-Z0-9_-]{11})',
    ]
    for pattern in patterns:
        match = re.search(pattern, url_or_id)
        if match:
            return match.group(1)
    return None

def format_transcript_for_ai(transcript, video_url):
    return f"""The following is a transcript from a YouTube video:
URL: {video_url}

---
TRANSCRIPT:
{transcript}
---

Please analyze this transcript according to the pattern instructions."""

def get_transcript(video_url, languages=['en', 'en-US', 'en-GB'], include_timestamps=False):
    video_id = extract_video_id(video_url)
    if not video_id:
        return {"error": f"Invalid YouTube URL or ID: {video_url}"}

    try:
        # In version 1.2.4, we need to instantiate the class
        ytt = YouTubeTranscriptApi()
        
        try:
            data = ytt.fetch(video_id, languages=languages)
        except:
            # Fallback to no language preference
            data = ytt.fetch(video_id)
            
        if include_timestamps:
            lines = []
            for t in data:
                # Handle both attribute and subscript access for robustness
                start = getattr(t, 'start', None) if not isinstance(t, dict) else t.get('start')
                text = getattr(t, 'text', '') if not isinstance(t, dict) else t.get('text', '')
                
                start_int = int(start) if start is not None else 0
                minutes = start_int // 60
                seconds = start_int % 60
                timestamp = f"[{minutes:02d}:{seconds:02d}] "
                lines.append(f"{timestamp}{text}")
            full_text = "\n".join(lines)
        else:
            full_text = ' '.join([getattr(t, 'text', '') if not isinstance(t, dict) else t.get('text', '') for t in data])
            
        # Clean up
        full_text = re.sub(r'\s+', ' ', full_text)
        full_text = full_text.replace('[Music]', '').replace('[Applause]', '')
        full_text = full_text.strip()
        
        formatted_text = format_transcript_for_ai(full_text, video_url)
            
        return {"transcript": formatted_text, "video_id": video_id}
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Fabric YouTube Transcript Fetcher')
    parser.add_argument('url_pos', nargs='?', help='YouTube URL or Video ID')
    parser.add_argument('--url', help='YouTube URL or Video ID (alternative)')
    parser.add_argument('--timestamps', action='store_true', help='Include timestamps')
    
    args = parser.parse_args()
    
    url = args.url if args.url else args.url_pos
    
    if not url:
        print(json.dumps({"error": "No URL provided"}))
        sys.exit(1)
        
    result = get_transcript(url, include_timestamps=args.timestamps)
    print(json.dumps(result))
