#!/usr/bin/env python3
"""
Fabric Auto-Bypass - Automatic YouTube Rate Limit Bypass

This script automatically:
1. Fetches free proxies from multiple sources
2. Tests them for YouTube access
3. Picks the best working one
4. Saves configuration for the Fabric GUI

Just run it and it does everything automatically!

Usage:
    python auto_bypass.py          # Auto-configure and test
    python auto_bypass.py --test   # Quick test with current config
    python auto_bypass.py --reset  # Reset to direct connection
"""

import sys
import os
import json
import time
import socket
import subprocess
import concurrent.futures
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional, List, Tuple
from datetime import datetime

# Add requests with retry support
try:
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
except ImportError:
    print("Installing required packages...")
    subprocess.run([sys.executable, "-m", "pip", "install", "requests", "-q"])
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry


# ============================================================================
# CONFIGURATION
# ============================================================================

CONFIG_FILE = Path(__file__).parent / "bypass_config.json"
FABRIC_GUI_CONFIG = Path(__file__).parent.parent / "fabric-gui-tauri" / "proxy_config.json"

# Proxy sources - these are free public proxy lists
PROXY_SOURCES = [
    "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=10000&country=all&ssl=yes&anonymity=all",
    "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt",
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
    "https://raw.githubusercontent.com/hookzof/socks5_list/master/proxy.txt",
    "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt",
]

# Test URL to verify proxy works with YouTube
YOUTUBE_TEST_URL = "https://www.youtube.com/watch?v=jNQXAC9IVRw"  # First YouTube video ever


@dataclass
class ProxyConfig:
    host: str
    port: int
    proxy_type: str = "http"
    latency_ms: float = 0
    last_tested: str = ""
    youtube_works: bool = False
    
    def to_url(self) -> str:
        return f"{self.proxy_type}://{self.host}:{self.port}"
    
    def to_env(self) -> dict:
        url = self.to_url()
        return {"HTTP_PROXY": url, "HTTPS_PROXY": url, "http_proxy": url, "https_proxy": url}


# ============================================================================
# PROXY FETCHER
# ============================================================================

def fetch_proxies() -> List[ProxyConfig]:
    """Fetch proxies from all sources."""
    print("🔍 Fetching proxies from public lists...")
    proxies = []
    seen = set()
    
    session = requests.Session()
    retries = Retry(total=2, backoff_factor=0.5)
    session.mount('https://', HTTPAdapter(max_retries=retries))
    session.mount('http://', HTTPAdapter(max_retries=retries))
    
    for source in PROXY_SOURCES:
        try:
            response = session.get(source, timeout=10)
            for line in response.text.strip().split('\n'):
                line = line.strip()
                if ':' in line and line not in seen:
                    parts = line.split(':')
                    if len(parts) >= 2:
                        host = parts[0].strip()
                        try:
                            port = int(parts[1].strip())
                            if 1 <= port <= 65535:
                                seen.add(line)
                                proxies.append(ProxyConfig(host=host, port=port))
                        except ValueError:
                            continue
        except Exception as e:
            continue
    
    print(f"   Found {len(proxies)} unique proxies")
    return proxies[:100]  # Limit to 100 for faster testing


# ============================================================================
# PROXY TESTER
# ============================================================================

def test_proxy(proxy: ProxyConfig) -> Optional[ProxyConfig]:
    """Test if a proxy works and can access YouTube."""
    try:
        proxy_url = proxy.to_url()
        proxies = {"http": proxy_url, "https": proxy_url}
        
        # Quick connectivity test
        start = time.time()
        response = requests.get(
            "https://www.google.com/",
            proxies=proxies,
            timeout=8,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"}
        )
        latency = (time.time() - start) * 1000
        
        if response.status_code != 200:
            return None
        
        proxy.latency_ms = latency
        proxy.last_tested = datetime.now().isoformat()
        
        # Test YouTube access (quick check)
        yt_response = requests.get(
            "https://www.youtube.com/",
            proxies=proxies,
            timeout=10,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"}
        )
        
        proxy.youtube_works = yt_response.status_code == 200 and "youtube" in yt_response.text.lower()
        
        return proxy if proxy.youtube_works else None
        
    except Exception:
        return None


def test_proxies_parallel(proxies: List[ProxyConfig], max_workers: int = 20) -> List[ProxyConfig]:
    """Test multiple proxies in parallel."""
    print(f"🧪 Testing {len(proxies)} proxies (this may take a minute)...")
    working = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(test_proxy, p): p for p in proxies}
        done_count = 0
        
        for future in concurrent.futures.as_completed(futures):
            done_count += 1
            result = future.result()
            if result:
                working.append(result)
                print(f"   ✓ Found working proxy: {result.host}:{result.port} ({result.latency_ms:.0f}ms)")
            
            # Progress indicator every 20 proxies
            if done_count % 20 == 0:
                print(f"   Progress: {done_count}/{len(proxies)} tested, {len(working)} working")
    
    # Sort by latency (fastest first)
    working.sort(key=lambda p: p.latency_ms)
    
    print(f"   Found {len(working)} working proxies with YouTube access")
    return working


# ============================================================================
# YOUTUBE TRANSCRIPT TEST
# ============================================================================

def test_youtube_transcript(proxy: Optional[ProxyConfig] = None) -> Tuple[bool, str]:
    """Test if YouTube transcript works with the given proxy."""
    env = os.environ.copy()
    
    if proxy:
        env.update(proxy.to_env())
        print(f"   Testing with proxy: {proxy.to_url()}")
    else:
        print("   Testing with direct connection...")
    
    # Find the transcript script
    script_paths = [
        Path(__file__).parent.parent / "fabric-gui-tauri" / "src-tauri" / "resources" / "youtube_transcript.py",
        Path(__file__).parent / "youtube_transcript.py",
    ]
    
    script_path = None
    for p in script_paths:
        if p.exists():
            script_path = p
            break
    
    if not script_path:
        return False, "YouTube transcript script not found"
    
    try:
        result = subprocess.run(
            [sys.executable, str(script_path), "--url", "dQw4w9WgXcQ"],
            capture_output=True,
            text=True,
            timeout=60,
            env=env
        )
        
        try:
            output = json.loads(result.stdout)
            if "error" in output:
                return False, output["error"]
            if "transcript" in output:
                transcript_len = len(output["transcript"])
                return True, f"Success! Got {transcript_len} characters"
        except json.JSONDecodeError:
            if "transcript" in result.stdout.lower():
                return True, "Transcript received (partial parse)"
            return False, f"Invalid response: {result.stdout[:100]}"
            
    except subprocess.TimeoutExpired:
        return False, "Request timed out (60s)"
    except Exception as e:
        return False, str(e)
    
    return False, "Unknown error"


# ============================================================================
# CONFIGURATION MANAGEMENT
# ============================================================================

def save_config(proxy: Optional[ProxyConfig], working_proxies: List[ProxyConfig] = None):
    """Save configuration for use by Fabric GUI."""
    config = {
        "active_proxy": asdict(proxy) if proxy else None,
        "backup_proxies": [asdict(p) for p in (working_proxies or [])[:5]],
        "last_updated": datetime.now().isoformat(),
        "auto_configured": True
    }
    
    # Save to NetworkBypass folder
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)
    
    # Also save to Fabric GUI folder if it exists
    if FABRIC_GUI_CONFIG.parent.exists():
        with open(FABRIC_GUI_CONFIG, 'w') as f:
            json.dump(config, f, indent=2)
    
    print(f"   Configuration saved to: {CONFIG_FILE}")


def load_config() -> Tuple[Optional[ProxyConfig], List[ProxyConfig]]:
    """Load saved configuration."""
    if not CONFIG_FILE.exists():
        return None, []
    
    try:
        with open(CONFIG_FILE) as f:
            config = json.load(f)
        
        active = None
        if config.get("active_proxy"):
            p = config["active_proxy"]
            active = ProxyConfig(**p)
        
        backups = []
        for p in config.get("backup_proxies", []):
            backups.append(ProxyConfig(**p))
        
        return active, backups
    except:
        return None, []


def export_for_youtube_script():
    """Export proxy settings as environment variables for the YouTube script."""
    active, _ = load_config()
    
    if active:
        # Create a batch/ps1 file to set environment variables
        env_file = Path(__file__).parent / "set_proxy.ps1"
        with open(env_file, 'w') as f:
            f.write(f'$env:HTTP_PROXY = "{active.to_url()}"\n')
            f.write(f'$env:HTTPS_PROXY = "{active.to_url()}"\n')
            f.write(f'Write-Host "Proxy set to: {active.to_url()}"\n')
        
        print(f"   Created: {env_file}")
        print(f"   Run with: . .\\set_proxy.ps1")


# ============================================================================
# MAIN WORKFLOW
# ============================================================================

def auto_configure():
    """Main auto-configuration workflow."""
    print()
    print("=" * 60)
    print("   FABRIC AUTO-BYPASS - YouTube Rate Limit Fixer")
    print("=" * 60)
    print()
    
    # Step 1: Check if direct connection works
    print("Step 1: Testing direct connection...")
    success, msg = test_youtube_transcript(None)
    if success:
        print(f"   ✅ Direct connection works! No proxy needed.")
        print(f"   {msg}")
        save_config(None, [])
        return True
    else:
        print(f"   ❌ Direct connection failed: {msg}")
        print("   Will try to find a working proxy...")
    
    print()
    
    # Step 2: Fetch proxies
    print("Step 2: Fetching free proxies...")
    proxies = fetch_proxies()
    
    if not proxies:
        print("   ❌ Could not fetch any proxies. Check your internet connection.")
        return False
    
    print()
    
    # Step 3: Test proxies
    print("Step 3: Testing proxies for YouTube access...")
    working = test_proxies_parallel(proxies)
    
    if not working:
        print("   ❌ No working proxies found.")
        print("   Suggestions:")
        print("   - Wait 15-30 minutes and try again")
        print("   - Use a VPN manually")
        print("   - Try from a different network")
        return False
    
    print()
    
    # Step 4: Test best proxy with YouTube transcript
    print("Step 4: Testing best proxies with YouTube transcript...")
    
    for proxy in working[:5]:  # Try top 5
        print(f"   Trying: {proxy.host}:{proxy.port}...")
        success, msg = test_youtube_transcript(proxy)
        
        if success:
            print(f"   ✅ SUCCESS with {proxy.host}:{proxy.port}")
            print(f"   {msg}")
            
            # Save this as the active proxy
            save_config(proxy, working)
            export_for_youtube_script()
            
            print()
            print("=" * 60)
            print("   ✅ AUTO-CONFIGURATION COMPLETE!")
            print("=" * 60)
            print(f"   Active Proxy: {proxy.to_url()}")
            print(f"   Latency: {proxy.latency_ms:.0f}ms")
            print(f"   Backup proxies saved: {len(working[:5])}")
            print()
            print("   Your Fabric GUI YouTube feature should now work!")
            print("=" * 60)
            return True
        else:
            print(f"   ❌ Failed: {msg}")
    
    print()
    print("   ❌ All tested proxies failed YouTube transcript test.")
    print("   Saving best proxy anyway for manual testing...")
    save_config(working[0], working)
    return False


def quick_test():
    """Quick test with current configuration."""
    print()
    print("Quick Test - Using saved configuration...")
    print()
    
    active, backups = load_config()
    
    if active:
        print(f"Saved proxy: {active.to_url()}")
        success, msg = test_youtube_transcript(active)
        print(f"Result: {'✅ ' + msg if success else '❌ ' + msg}")
        
        if not success and backups:
            print("\nTrying backup proxies...")
            for proxy in backups:
                success, msg = test_youtube_transcript(proxy)
                if success:
                    print(f"✅ Backup proxy works: {proxy.to_url()}")
                    save_config(proxy, backups)
                    return True
    else:
        print("No proxy configured. Testing direct connection...")
        success, msg = test_youtube_transcript(None)
        print(f"Result: {'✅ ' + msg if success else '❌ ' + msg}")
        return success
    
    return False


def reset_config():
    """Reset to direct connection."""
    print("Resetting configuration to direct connection...")
    save_config(None, [])
    
    # Clear environment variables file
    env_file = Path(__file__).parent / "set_proxy.ps1"
    if env_file.exists():
        env_file.unlink()
    
    print("✅ Configuration reset. Using direct connection.")


# ============================================================================
# CLI ENTRY POINT
# ============================================================================

def main():
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg in ("--test", "-t"):
            quick_test()
        elif arg in ("--reset", "-r"):
            reset_config()
        elif arg in ("--help", "-h"):
            print(__doc__)
        else:
            print(f"Unknown argument: {arg}")
            print("Use --help for usage information")
    else:
        auto_configure()


if __name__ == "__main__":
    main()
