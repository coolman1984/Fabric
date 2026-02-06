#!/usr/bin/env python3
"""
Fabric YouTube Transcript Fetcher - Multi-Method Edition
Supports multiple fallback methods to always get transcripts:

1. Webshare Rotating Proxies (most reliable!)
2. Direct yt-dlp with browser cookies
3. Supadata API (free tier, 100/month)
4. youtube-transcript.io fallback
5. youtube-transcript-api fallback

No configuration needed - automatically tries all methods!
"""

import sys
import os
import json
import re
import subprocess
import tempfile
import random
from pathlib import Path
from typing import Optional, Tuple, List, Dict

# Try to import requests
try:
    import requests
except ImportError:
    subprocess.run([sys.executable, "-m", "pip", "install", "requests", "-q"])
    import requests


# ============================================================================
# WEBSHARE PROXY MANAGEMENT
# ============================================================================

def load_webshare_proxies() -> List[Dict]:
    """Load Webshare proxies from config file."""
    # Print search paths to stderr for debugging
    script_dir = Path(__file__).parent
    cwd = Path.cwd()
    
    paths_to_check = [
        script_dir / "webshare_proxies.json",
        script_dir.parent / "resources" / "webshare_proxies.json",
        cwd / "webshare_proxies.json",
        cwd / "src-tauri" / "resources" / "webshare_proxies.json",
        # Absolute project path fallback
        Path("G:/Fabric/fabric-gui-tauri/src-tauri/resources/webshare_proxies.json")
    ]
    
    # Try searching up the directory tree as well
    search_dir = script_dir
    for _ in range(5):
        paths_to_check.append(search_dir / "webshare_proxies.json")
        paths_to_check.append(search_dir / "src-tauri" / "resources" / "webshare_proxies.json")
        search_dir = search_dir.parent
    
    for config_path in paths_to_check:
        try:
           if config_path.exists():
                with open(config_path) as f:
                    data = json.load(f)
                    username = data.get("username", "")
                    password = data.get("password", "")
                    proxies = data.get("proxies", [])
                    
                    if not proxies:
                        continue
                        
                    # Build proxy URLs with auth
                    result = []
                    for p in proxies:
                        proxy_url = f"http://{username}:{password}@{p['host']}:{p['port']}"
                        result.append({
                            "url": proxy_url,
                            "host": p["host"],
                            "country": p.get("country", "US"),
                            "city": p.get("city", "Unknown")
                        })
                    return result
        except Exception:
            continue
    
    print(f"DEBUG: No proxy config found. Script dir: {script_dir}", file=sys.stderr)
    return []


def get_random_proxy() -> Optional[str]:
    """Get a random proxy URL from Webshare."""
    proxies = load_webshare_proxies()
    if proxies:
        return random.choice(proxies)["url"]
    return None


# ============================================================================
# VIDEO ID EXTRACTION
# ============================================================================

def extract_video_id(url_or_id: str) -> Optional[str]:
    """Extract YouTube video ID from URL or return ID if already an ID."""
    url_or_id = url_or_id.strip()
    
    if re.match(r'^[a-zA-Z0-9_-]{11}$', url_or_id):
        return url_or_id
    
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


# ============================================================================
# METHOD 1: SUPADATA API (100 free/month, no rate limits!)
# ============================================================================

def get_transcript_supadata(video_id: str, include_timestamps: bool = False) -> Tuple[Optional[str], Optional[str]]:
    """
    Get transcript using Supadata API.
    Free tier: 100 requests/month, no credit card required.
    """
    try:
        url = f"https://api.supadata.ai/v1/youtube/transcript?videoId={video_id}"
        
        headers = {
            "Accept": "application/json",
            "User-Agent": "Fabric-GUI/1.0"
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            if "content" in data:
                # Supadata returns segments with text and optional timestamps
                segments = data.get("content", [])
                
                if isinstance(segments, list):
                    lines = []
                    for seg in segments:
                        text = seg.get("text", "").strip() if isinstance(seg, dict) else str(seg).strip()
                        if include_timestamps and isinstance(seg, dict) and "start" in seg:
                            start = int(seg["start"])
                            mins, secs = divmod(start, 60)
                            lines.append(f"[{mins:02d}:{secs:02d}] {text}")
                        else:
                            lines.append(text)
                    
                    transcript = "\n".join(lines) if include_timestamps else " ".join(lines)
                    return transcript, None
                else:
                    return str(segments), None
            
            if "transcript" in data:
                return data["transcript"], None
            
            if "text" in data:
                return data["text"], None
        
        elif response.status_code == 429:
            return None, "SUPADATA_RATE_LIMIT"
        elif response.status_code == 404:
            return None, "SUPADATA_NOT_FOUND"
        else:
            return None, f"SUPADATA_ERROR_{response.status_code}"
            
    except requests.exceptions.Timeout:
        return None, "SUPADATA_TIMEOUT"
    except Exception as e:
        return None, f"SUPADATA_ERROR: {str(e)[:50]}"


# ============================================================================
# METHOD 1B: YOUTUBE-TRANSCRIPT.IO (Free, reliable third-party service)
# ============================================================================

def get_transcript_io(video_id: str, include_timestamps: bool = False) -> Tuple[Optional[str], Optional[str]]:
    """
    Get transcript using youtube-transcript.io API.
    Free tier available, handles rate limiting on their end.
    """
    try:
        # Method 1: Direct API
        url = f"https://youtube-transcript.io/api/transcript?videoId={video_id}"
        
        headers = {
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            if "transcript" in data:
                segments = data["transcript"]
                if isinstance(segments, list):
                    lines = []
                    for seg in segments:
                        text = seg.get("text", "").strip() if isinstance(seg, dict) else str(seg)
                        if include_timestamps and isinstance(seg, dict) and "start" in seg:
                            start = float(seg.get("start", 0))
                            mins, secs = divmod(int(start), 60)
                            lines.append(f"[{mins:02d}:{secs:02d}] {text}")
                        else:
                            lines.append(text)
                    transcript = "\n".join(lines) if include_timestamps else " ".join(lines)
                    if transcript.strip():
                        return transcript, None
                elif isinstance(segments, str):
                    return segments, None
        
        # Method 2: Alternative endpoint (youtubetranscript.com)
        alt_url = f"https://youtubetranscript.com/?server_vid2={video_id}"
        response = requests.get(alt_url, headers=headers, timeout=20)
        
        if response.status_code == 200:
            # Parse XML response
            import xml.etree.ElementTree as ET
            try:
                root = ET.fromstring(response.text)
                lines = []
                for text_elem in root.findall('.//text'):
                    text = text_elem.text or ""
                    text = text.strip()
                    if text and "sorry" not in text.lower() and "blocking" not in text.lower():
                        if include_timestamps:
                            start = float(text_elem.get('start', 0))
                            mins, secs = divmod(int(start), 60)
                            lines.append(f"[{mins:02d}:{secs:02d}] {text}")
                        else:
                            lines.append(text)
                
                if lines:
                    transcript = "\n".join(lines) if include_timestamps else " ".join(lines)
                    return transcript, None
            except ET.ParseError:
                pass
        
        return None, "TRANSCRIPT_IO_FAILED"
        
    except requests.exceptions.Timeout:
        return None, "TRANSCRIPT_IO_TIMEOUT"
    except Exception as e:
        return None, f"TRANSCRIPT_IO_ERROR: {str(e)[:50]}"


# ============================================================================
# METHOD 2: YT-DLP (may be rate limited)
# ============================================================================

def parse_vtt(vtt_content: str, include_timestamps: bool = False) -> str:
    """Parse VTT content and extract clean transcript."""
    lines = vtt_content.split('\n')
    seen = {}
    result = []
    current_ts = None
    
    ts_pattern = re.compile(r'(\d{1,2}:\d{2}:\d{2}\.\d{3})\s*-->')
    tag_pattern = re.compile(r'<[^>]*>')
    
    for line in lines:
        line = line.strip()
        
        if not line or line == 'WEBVTT' or line.startswith(('NOTE', 'STYLE', 'Kind:', 'Language:')):
            continue
        
        ts_match = ts_pattern.match(line)
        if ts_match:
            ts = ts_match.group(1)
            parts = ts.split(':')
            if len(parts) == 3:
                h, m, s = int(parts[0]), int(parts[1]), int(float(parts[2]))
                current_ts = f"{h:02d}:{m:02d}:{s:02d}" if h > 0 else f"{m:02d}:{s:02d}"
            continue
        
        if re.match(r'^\d+$', line):
            continue
        
        clean = tag_pattern.sub('', line).strip()
        if clean and clean not in seen:
            seen[clean] = True
            if include_timestamps and current_ts:
                result.append(f"[{current_ts}] {clean}")
            else:
                result.append(clean)
    
    return '\n'.join(result) if include_timestamps else ' '.join(result)


def get_transcript_ytdlp(video_id: str, include_timestamps: bool = False, proxy: Optional[str] = None, use_cookies: bool = True) -> Tuple[Optional[str], Optional[str]]:
    """Get transcript using yt-dlp. Supports proxy and browser cookies."""
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    
    with tempfile.TemporaryDirectory(prefix=f"fabric-{video_id}-") as temp_dir:
        output = os.path.join(temp_dir, "%(id)s.%(ext)s")
        
        cmd = [
            sys.executable, "-m", "yt_dlp",
            "--write-auto-subs", "--write-subs",
            "--skip-download",
            "--sub-format", "vtt",
            "--quiet", "--no-warnings",
            "-o", output,
        ]
        
        # Try browser cookies first (uses logged-in session to avoid rate limits)
        if use_cookies:
            # Try Edge first (most common on Windows), then Chrome, Firefox
            for browser in ["edge", "chrome", "firefox", "brave", "opera"]:
                cmd_with_cookies = cmd.copy()
                cmd_with_cookies.extend(["--cookies-from-browser", browser])
                if proxy:
                    cmd_with_cookies.extend(["--proxy", proxy])
                cmd_with_cookies.append(video_url)
                
                try:
                    result = subprocess.run(cmd_with_cookies, capture_output=True, text=True, timeout=45)
                    
                    # Check for rate limiting
                    if "429" not in (result.stderr or "") and "Too Many Requests" not in (result.stderr or ""):
                        vtt_files = list(Path(temp_dir).glob("*.vtt"))
                        if vtt_files:
                            content = vtt_files[0].read_text(encoding='utf-8', errors='ignore')
                            transcript = parse_vtt(content, include_timestamps)
                            if transcript.strip():
                                return transcript, None
                except subprocess.TimeoutExpired:
                    continue
                except Exception:
                    continue
        
        # Fallback: try without cookies
        if proxy:
            cmd.extend(["--proxy", proxy])
        cmd.append(video_url)
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=45)
        except subprocess.TimeoutExpired:
            return None, "YTDLP_TIMEOUT"
        except FileNotFoundError:
            return None, "YTDLP_NOT_FOUND"
        
        if "429" in (result.stderr or "") or "Too Many Requests" in (result.stderr or ""):
            return None, "YTDLP_RATE_LIMITED"
        
        vtt_files = list(Path(temp_dir).glob("*.vtt"))
        if not vtt_files:
            return None, "YTDLP_NO_SUBS"
        
        content = vtt_files[0].read_text(encoding='utf-8', errors='ignore')
        transcript = parse_vtt(content, include_timestamps)
        
        if not transcript.strip():
            return None, "YTDLP_EMPTY"
        
        return transcript, None


# ============================================================================
# METHOD 3: YOUTUBE-TRANSCRIPT-API
# ============================================================================

def get_transcript_api(video_id: str, include_timestamps: bool = False) -> Tuple[Optional[str], Optional[str]]:
    """Get transcript using youtube-transcript-api."""
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        
        ytt = YouTubeTranscriptApi()
        
        try:
            data = ytt.fetch(video_id, languages=['en', 'en-US', 'en-GB'])
        except:
            try:
                data = ytt.fetch(video_id)
            except Exception as e:
                if "429" in str(e).lower() or "blocking" in str(e).lower():
                    return None, "API_RATE_LIMITED"
                return None, "API_ERROR"
        
        lines = []
        for snippet in data:
            text = getattr(snippet, 'text', '').strip() if hasattr(snippet, 'text') else str(snippet.get('text', '')).strip()
            start = getattr(snippet, 'start', 0) if hasattr(snippet, 'start') else snippet.get('start', 0)
            
            if text:
                if include_timestamps:
                    m, s = divmod(int(start), 60)
                    lines.append(f"[{m:02d}:{s:02d}] {text}")
                else:
                    lines.append(text)
        
        transcript = '\n'.join(lines) if include_timestamps else ' '.join(lines)
        transcript = re.sub(r'\s+', ' ', transcript).strip()
        
        if not transcript:
            return None, "API_EMPTY"
        
        return transcript, None
        
    except ImportError:
        return None, "API_NOT_INSTALLED"
    except Exception as e:
        return None, f"API_ERROR: {str(e)[:50]}"


# ============================================================================
# MAIN: TRY ALL METHODS
# ============================================================================

def get_transcript(video_id: str, include_timestamps: bool = False) -> Tuple[str, Optional[str]]:
    """
    Try all methods to get a transcript.
    Returns (transcript, error) - at least one will be non-None.
    Priority: Webshare proxies -> yt-dlp with cookies -> Other fallbacks
    """
    errors = []
    
    # Method 0: Try Webshare rotating proxies FIRST (most reliable!)
    webshare_proxies = load_webshare_proxies()
    if webshare_proxies:
        # Shuffle proxies for random rotation
        random.shuffle(webshare_proxies)
        
        for i, proxy in enumerate(webshare_proxies[:5]):  # Try up to 5 proxies
            proxy_url = proxy["url"]
            country = proxy.get("country", "?")
            
            # Try yt-dlp with this proxy
            transcript, error = get_transcript_ytdlp(video_id, include_timestamps, proxy=proxy_url, use_cookies=False)
            if transcript:
                return transcript, None
            
            # If rate limited on this proxy, try next one
            if error and "RATE_LIMITED" in error:
                continue
            elif error:
                errors.append(f"Webshare[{country}]: {error}")
                break  # Non-rate-limit error, try other methods
    else:
        errors.append("Webshare: No proxies configured")
    
    # Method 1: Try yt-dlp with browser cookies (local, may be rate limited)
    transcript, error = get_transcript_ytdlp(video_id, include_timestamps, use_cookies=True)
    if transcript:
        return transcript, None
    if error:
        errors.append(f"yt-dlp: {error}")
    
    # Method 2: Try Supadata API
    transcript, error = get_transcript_supadata(video_id, include_timestamps)
    if transcript:
        return transcript, None
    if error:
        errors.append(f"Supadata: {error}")
    
    # Method 3: Try youtube-transcript.io
    transcript, error = get_transcript_io(video_id, include_timestamps)
    if transcript:
        return transcript, None
    if error:
        errors.append(f"Transcript.io: {error}")
    
    # Method 4: Try youtube-transcript-api
    transcript, error = get_transcript_api(video_id, include_timestamps)
    if transcript:
        return transcript, None
    if error:
        errors.append(f"API: {error}")
    
    # Method 4: Try yt-dlp with saved proxy (if available)
    proxy_config = Path(__file__).parent.parent / "NetworkBypass" / "bypass_config.json"
    if not proxy_config.exists():
        proxy_config = Path(__file__).parent / "proxy_config.json"
    
    if proxy_config.exists():
        try:
            with open(proxy_config) as f:
                config = json.load(f)
            if config.get("active_proxy"):
                p = config["active_proxy"]
                proxy_url = f"{p.get('proxy_type', 'http')}://{p['host']}:{p['port']}"
                transcript, error = get_transcript_ytdlp(video_id, include_timestamps, proxy=proxy_url)
                if transcript:
                    return transcript, None
                if error:
                    errors.append(f"Proxy: {error}")
        except:
            pass
    
    # All methods failed
    return "", "All methods failed:\n" + "\n".join(errors)


def format_for_ai(transcript: str, video_url: str) -> str:
    """Format transcript for AI processing."""
    max_chars = 30000
    if len(transcript) > max_chars:
        transcript = transcript[:max_chars] + "\n\n[Transcript truncated...]"
    
    return f"""The following is a transcript from a YouTube video:
URL: {video_url}

---
TRANSCRIPT:
{transcript}
---

Please analyze this transcript according to the pattern instructions."""


# ============================================================================
# CLI
# ============================================================================

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Multi-method YouTube Transcript Fetcher')
    parser.add_argument('url_pos', nargs='?', help='YouTube URL or Video ID')
    parser.add_argument('--url', help='YouTube URL or Video ID')
    parser.add_argument('--timestamps', action='store_true', help='Include timestamps')
    parser.add_argument('--lang', default='en', help='Language (default: en)')
    
    args = parser.parse_args()
    url = args.url or args.url_pos
    
    if not url:
        print(json.dumps({"error": "No URL provided"}))
        sys.exit(1)
    
    video_id = extract_video_id(url)
    if not video_id:
        print(json.dumps({"error": f"Invalid YouTube URL: {url}"}))
        sys.exit(1)
    
    transcript, error = get_transcript(video_id, args.timestamps)
    
    if error:
        # Print JSON error to stderr so Rust can capture it
        print(json.dumps({"error": error}), file=sys.stderr)
        sys.exit(1)
    
    formatted = format_for_ai(transcript, f"https://www.youtube.com/watch?v={video_id}")
    print(json.dumps({"transcript": formatted, "video_id": video_id}))


if __name__ == "__main__":
    main()
