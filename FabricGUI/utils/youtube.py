"""
YouTube Transcript Extractor

Extracts transcripts from YouTube videos for summarization.
No OAuth required - uses publicly available captions.
Updated for youtube-transcript-api 1.2.4
"""

import re
from typing import Optional, Tuple


def extract_video_id(url_or_id: str) -> Optional[str]:
    """
    Extract YouTube video ID from URL or return ID if already an ID.
    
    Supports:
    - https://www.youtube.com/watch?v=VIDEO_ID
    - https://youtu.be/VIDEO_ID
    - https://www.youtube.com/embed/VIDEO_ID
    - Just the VIDEO_ID itself
    """
    url_or_id = url_or_id.strip()
    
    # Already a video ID (11 characters, alphanumeric + - _)
    if re.match(r'^[a-zA-Z0-9_-]{11}$', url_or_id):
        return url_or_id
    
    # Standard YouTube URL patterns
    patterns = [
        r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([a-zA-Z0-9_-]{11})',
        r'(?:youtube\.com/v/)([a-zA-Z0-9_-]{11})',
        r'[?&]v=([a-zA-Z0-9_-]{11})',  # Handle URL with extra params
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url_or_id)
        if match:
            return match.group(1)
    
    return None


def get_transcript(video_url: str, languages: list[str] = None) -> Tuple[str, Optional[str]]:
    """
    Get transcript from a YouTube video.
    
    Args:
        video_url: YouTube URL or video ID
        languages: Preferred languages (default: ['en', 'en-US'])
    
    Returns:
        Tuple of (transcript_text, error_message)
        If successful, error_message is None
        If failed, transcript_text is empty and error_message explains why
    """
    if languages is None:
        languages = ['en', 'en-US', 'en-GB']
    
    video_id = extract_video_id(video_url)
    if not video_id:
        return "", f"Could not extract video ID from: {video_url}"
    
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        
        # Create API instance (v1.2.4 requires instantiation)
        ytt_api = YouTubeTranscriptApi()
        
        # Fetch transcript
        try:
            fetched_transcript = ytt_api.fetch(video_id, languages=languages)
        except Exception:
            # Fallback: try without language preference
            try:
                fetched_transcript = ytt_api.fetch(video_id)
            except Exception as e:
                return "", f"Could not fetch transcript: {str(e)}"
        
        # Convert to readable text
        lines = []
        for snippet in fetched_transcript:
            text = snippet.text.strip() if hasattr(snippet, 'text') else str(snippet.get('text', '')).strip()
            if text:
                lines.append(text)
        
        full_text = ' '.join(lines)
        
        # Clean up common issues
        full_text = re.sub(r'\s+', ' ', full_text)  # Multiple spaces
        full_text = full_text.replace('[Music]', '').replace('[Applause]', '')
        full_text = full_text.strip()
        
        if not full_text:
            return "", "Transcript is empty"
        
        return full_text, None
        
    except ImportError:
        return "", "youtube-transcript-api not installed. Run: pip install youtube-transcript-api"
    except Exception as e:
        return "", f"Error fetching transcript: {str(e)}"


def is_youtube_url(text: str) -> bool:
    """Check if the text looks like a YouTube URL."""
    text = text.strip()
    return any(pattern in text.lower() for pattern in [
        'youtube.com/watch',
        'youtu.be/',
        'youtube.com/embed',
        'youtube.com/v/'
    ])


def format_transcript_for_ai(transcript: str, video_url: str) -> str:
    """
    Format transcript for AI processing.
    
    Args:
        transcript: Raw transcript text
        video_url: Original video URL
    
    Returns:
        Formatted text for AI input
    """
    # Truncate if too long (most AI models have context limits)
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
