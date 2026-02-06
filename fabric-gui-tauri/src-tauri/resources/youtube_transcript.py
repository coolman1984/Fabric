#!/usr/bin/env python3
"""
Fabric YouTube Transcript Fetcher (yt-dlp version)
This version uses yt-dlp for more reliable transcript extraction,
bypassing YouTube's IP blocking that affects youtube-transcript-api.
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
    
    # Regex to match VTT timestamp lines
    timestamp_pattern = re.compile(r'(\d{1,2}:\d{2}:\d{2}\.\d{3})\s*-->')
    # Regex to remove VTT formatting tags
    vtt_tag_pattern = re.compile(r'<[^>]*>')
    
    for line in lines:
        line = line.strip()
        
        # Skip WEBVTT header, empty lines, and metadata
        if not line or line == 'WEBVTT' or line.startswith('NOTE') or \
           line.startswith('STYLE') or line.startswith('Kind:') or \
           line.startswith('Language:'):
            continue
        
        # Check for timestamp line
        timestamp_match = timestamp_pattern.match(line)
        if timestamp_match:
            # Extract and format timestamp (HH:MM:SS or MM:SS)
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
        
        # Skip numeric sequence identifiers
        if re.match(r'^\d+$', line):
            continue
        
        # This is transcript text
        clean_text = vtt_tag_pattern.sub('', line).strip()
        if clean_text:
            if include_timestamps and current_timestamp:
                # Check for duplicates within 10 seconds
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
    """
    Get transcript using yt-dlp.
    This method is more reliable against IP blocking.
    """
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    
    # Create temporary directory for yt-dlp output
    with tempfile.TemporaryDirectory(prefix=f"fabric-yt-{video_id}-") as temp_dir:
        output_template = os.path.join(temp_dir, "%(title)s.%(ext)s")
        
        # Build yt-dlp command
        cmd = [
            sys.executable, "-m", "yt_dlp",
            "--write-auto-subs",
            "--skip-download",
            "--sub-format", "vtt",
            "-o", output_template,
        ]
        
        # Add language preference
        if language:
            lang_opts = f"{language},{language[:2]}.*,{language[:2]}"
            cmd.extend(["--sub-langs", lang_opts])
        
        cmd.append(video_url)
        
        # Run yt-dlp
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120
            )
        except subprocess.TimeoutExpired:
            return None, "Timeout while fetching transcript"
        except FileNotFoundError:
            return None, "yt-dlp not found. Install with: pip install yt-dlp"
        
        # Check for common errors
        stderr = result.stderr.lower() if result.stderr else ""
        if "429" in stderr or "too many requests" in stderr:
            return None, "Rate limit exceeded. Please wait and try again."
        if "sign in" in stderr or "bot" in stderr:
            return None, "YouTube requires authentication. Try using cookies."
        
        # Find VTT file
        vtt_files = list(Path(temp_dir).glob("*.vtt"))
        if not vtt_files:
            # Try without language restriction
            cmd_retry = [
                sys.executable, "-m", "yt_dlp",
                "--write-auto-subs",
                "--skip-download",
                "--sub-format", "vtt",
                "-o", output_template,
                video_url
            ]
            subprocess.run(cmd_retry, capture_output=True, text=True, timeout=120)
            vtt_files = list(Path(temp_dir).glob("*.vtt"))
        
        if not vtt_files:
            return None, f"No transcript available for video {video_id}"
        
        # Read and parse VTT file
        vtt_content = vtt_files[0].read_text(encoding='utf-8', errors='ignore')
        transcript = parse_vtt_file(vtt_content, include_timestamps)
        
        if not transcript.strip():
            return None, "Transcript is empty"
        
        return transcript, None


def format_transcript_for_ai(transcript, video_url):
    """Format transcript for AI processing."""
    # Truncate if too long
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
    parser = argparse.ArgumentParser(description='Fabric YouTube Transcript Fetcher (yt-dlp)')
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
    
    transcript, error = get_transcript_ytdlp(
        video_id,
        include_timestamps=args.timestamps,
        language=args.lang
    )
    
    if error:
        print(json.dumps({"error": error}))
        sys.exit(1)
    
    formatted = format_transcript_for_ai(transcript, f"https://www.youtube.com/watch?v={video_id}")
    
    print(json.dumps({
        "transcript": formatted,
        "video_id": video_id
    }))


if __name__ == "__main__":
    main()
