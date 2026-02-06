#!/usr/bin/env python3
"""
Fabric YouTube Transcript Fetcher
Supports multiple methods with automatic fallback:
1. yt-dlp (most reliable)
2. youtube-transcript-api (fallback)
3. Clear error messages when rate limited
"""

import sys
import json
import re
import os
import argparse
import subprocess
import tempfile
from pathlib import Path


def extract_video_id(url_or_id):
    """Extract YouTube video ID from URL or return ID if already an ID."""
    url_or_id = url_or_id.strip()
    
    # Already a video ID (11 characters, alphanumeric + - _)
    if re.match(r'^[a-zA-Z0-9_-]{11}$', url_or_id):
        return url_or_id
    
    # Standard YouTube URL patterns
    patterns = [
        r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([a-zA-Z0-9_-]{11})',
        r'(?:youtube\.com/v/)([a-zA-Z0-9_-]{11})',
        r'[?&]v=([a-zA-Z0-9_-]{11})',
        r'youtube\.com/shorts/([a-zA-Z0-9_-]{11})',
        r'youtube\.com/live/([a-zA-Z0-9_-]{11})',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url_or_id)
        if match:
            return match.group(1)
    
    return None


def parse_vtt_file(vtt_content, include_timestamps=False):
    """Parse VTT content and extract clean transcript text."""
    lines = vtt_content.split('\n')
    seen_segments = {}
    result_lines = []
    current_timestamp = None
    
    timestamp_pattern = re.compile(r'(\d{1,2}:\d{2}:\d{2}\.\d{3})\s*-->')
    vtt_tag_pattern = re.compile(r'<[^>]*>')
    
    for line in lines:
        line = line.strip()
        
        if not line or line == 'WEBVTT' or line.startswith('NOTE') or \
           line.startswith('STYLE') or line.startswith('Kind:') or \
           line.startswith('Language:'):
            continue
        
        timestamp_match = timestamp_pattern.match(line)
        if timestamp_match:
            ts = timestamp_match.group(1)
            parts = ts.split(':')
            if len(parts) == 3:
                hours = int(parts[0])
                minutes = int(parts[1])
                seconds = int(float(parts[2]))
                if hours > 0:
                    current_timestamp = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                else:
                    current_timestamp = f"{minutes:02d}:{seconds:02d}"
            continue
        
        if re.match(r'^\d+$', line):
            continue
        
        clean_text = vtt_tag_pattern.sub('', line).strip()
        if clean_text:
            if include_timestamps and current_timestamp:
                if clean_text not in seen_segments:
                    result_lines.append(f"[{current_timestamp}] {clean_text}")
                    seen_segments[clean_text] = current_timestamp
            else:
                if clean_text not in seen_segments:
                    result_lines.append(clean_text)
                    seen_segments[clean_text] = True
    
    if include_timestamps:
        return '\n'.join(result_lines)
    else:
        return ' '.join(result_lines)


def get_transcript_ytdlp(video_id, include_timestamps=False, language='en'):
    """Get transcript using yt-dlp."""
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    
    with tempfile.TemporaryDirectory(prefix=f"fabric-yt-{video_id}-") as temp_dir:
        output_template = os.path.join(temp_dir, "%(id)s.%(ext)s")
        
        # Build minimal yt-dlp command (no cookies - they often fail on Windows)
        cmd = [
            sys.executable, "-m", "yt_dlp",
            "--write-auto-subs",
            "--write-subs",
            "--skip-download",
            "--sub-format", "vtt",
            "--quiet",
            "--no-warnings",
            "-o", output_template,
        ]
        
        if language:
            cmd.extend(["--sub-langs", f"{language},{language[:2]}"])
        
        cmd.append(video_url)
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        except subprocess.TimeoutExpired:
            return None, "TIMEOUT"
        except FileNotFoundError:
            return None, "YT_DLP_NOT_FOUND"
        
        # Check output for 429 errors
        if "429" in (result.stderr or "") or "Too Many Requests" in (result.stderr or ""):
            return None, "RATE_LIMITED"
        
        # Find VTT files
        vtt_files = list(Path(temp_dir).glob("*.vtt"))
        
        if not vtt_files:
            return None, "NO_TRANSCRIPT"
        
        vtt_content = vtt_files[0].read_text(encoding='utf-8', errors='ignore')
        transcript = parse_vtt_file(vtt_content, include_timestamps)
        
        if not transcript.strip():
            return None, "EMPTY_TRANSCRIPT"
        
        return transcript, None


def get_transcript_api(video_id, include_timestamps=False, languages=None):
    """Get transcript using youtube-transcript-api (fallback method)."""
    if languages is None:
        languages = ['en', 'en-US', 'en-GB']
    
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        
        ytt = YouTubeTranscriptApi()
        
        try:
            data = ytt.fetch(video_id, languages=languages)
        except:
            try:
                data = ytt.fetch(video_id)
            except Exception as e:
                error_str = str(e).lower()
                if "429" in error_str or "too many" in error_str or "blocking" in error_str:
                    return None, "RATE_LIMITED"
                return None, "API_ERROR"
        
        lines = []
        for snippet in data:
            text = getattr(snippet, 'text', '').strip() if hasattr(snippet, 'text') else str(snippet.get('text', '')).strip()
            start = getattr(snippet, 'start', 0) if hasattr(snippet, 'start') else snippet.get('start', 0)
            
            if text:
                if include_timestamps:
                    minutes = int(start) // 60
                    seconds = int(start) % 60
                    lines.append(f"[{minutes:02d}:{seconds:02d}] {text}")
                else:
                    lines.append(text)
        
        if include_timestamps:
            transcript = '\n'.join(lines)
        else:
            transcript = ' '.join(lines)
        
        # Cleanup
        transcript = re.sub(r'\s+', ' ', transcript)
        transcript = transcript.replace('[Music]', '').replace('[Applause]', '')
        transcript = transcript.strip()
        
        if not transcript:
            return None, "EMPTY_TRANSCRIPT"
        
        return transcript, None
        
    except ImportError:
        return None, "API_NOT_INSTALLED"
    except Exception as e:
        return None, "API_ERROR"


def format_transcript_for_ai(transcript, video_url):
    """Format transcript for AI processing."""
    max_chars = 30000
    if len(transcript) > max_chars:
        transcript = transcript[:max_chars] + "\n\n[Transcript truncated due to length...]"
    
    return f"""The following is a transcript from a YouTube video:
URL: {video_url}

---
TRANSCRIPT:
{transcript}
---

Please analyze this transcript according to the pattern instructions."""


def main():
    parser = argparse.ArgumentParser(description='Fabric YouTube Transcript Fetcher')
    parser.add_argument('url_pos', nargs='?', help='YouTube URL or Video ID')
    parser.add_argument('--url', help='YouTube URL or Video ID (alternative)')
    parser.add_argument('--timestamps', action='store_true', help='Include timestamps')
    parser.add_argument('--lang', default='en', help='Language code (default: en)')
    
    args = parser.parse_args()
    
    url = args.url if args.url else args.url_pos
    
    if not url:
        print(json.dumps({"error": "No URL provided"}))
        sys.exit(1)
    
    video_id = extract_video_id(url)
    if not video_id:
        print(json.dumps({"error": f"Invalid YouTube URL or ID: {url}"}))
        sys.exit(1)
    
    # Try yt-dlp first
    transcript, error = get_transcript_ytdlp(video_id, args.timestamps, args.lang)
    
    # If yt-dlp fails, try youtube-transcript-api
    if error and error != "RATE_LIMITED":
        transcript, error = get_transcript_api(video_id, args.timestamps)
    
    # Handle errors with user-friendly messages
    if error:
        error_messages = {
            "RATE_LIMITED": (
                "YouTube is rate-limiting your IP address (HTTP 429). "
                "This typically happens after many requests. Solutions:\n"
                "1. Wait 15-30 minutes and try again\n"
                "2. Use a VPN to change your IP address\n"
                "3. Try from a different network (mobile hotspot)"
            ),
            "NO_TRANSCRIPT": f"No transcript available for video {video_id}. The video may not have captions.",
            "EMPTY_TRANSCRIPT": "The transcript is empty or could not be parsed.",
            "TIMEOUT": "Request timed out. Please try again.",
            "YT_DLP_NOT_FOUND": "yt-dlp not found. Install with: pip install yt-dlp",
            "API_NOT_INSTALLED": "youtube-transcript-api not installed. Install with: pip install youtube-transcript-api",
            "API_ERROR": "Failed to fetch transcript. The video may be private, age-restricted, or have no captions."
        }
        print(json.dumps({"error": error_messages.get(error, f"Unknown error: {error}")}))
        sys.exit(1)
    
    formatted = format_transcript_for_ai(transcript, f"https://www.youtube.com/watch?v={video_id}")
    
    print(json.dumps({
        "transcript": formatted,
        "video_id": video_id
    }))


if __name__ == "__main__":
    main()
