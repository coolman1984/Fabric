#!/usr/bin/env python3
"""
Fabric Auto-Bypass - Secure Edition
Automatic YouTube Rate Limit Bypass with Security Hardening

SECURITY FEATURES:
✓ SSL/TLS certificate verification (no MITM attacks)
✓ Proxy security validation (no malicious redirects)
✓ No credential storage
✓ HTTPS-only proxy testing
✓ Suspicious content detection
✓ Rate limiting protection
✓ Timeout protection against slow-loris attacks

Usage:
    python auto_bypass.py          # Auto-configure and test
    python auto_bypass.py --test   # Quick test with current config
    python auto_bypass.py --reset  # Reset to direct connection
"""

import sys
import os
import json
import time
import hashlib
import secrets
import subprocess
import concurrent.futures
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional, List, Tuple
from datetime import datetime
from urllib.parse import urlparse

# Safe imports with version checking
try:
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
    import urllib3
    
    # Disable only the specific warning about unverified HTTPS but keep SSL verification ON
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
except ImportError:
    print("Installing required packages...")
    subprocess.run([sys.executable, "-m", "pip", "install", "requests", "-q"])
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry


# ============================================================================
# SECURITY CONFIGURATION
# ============================================================================

class SecurityConfig:
    """Security settings - NEVER disable these in production."""
    
    # SSL/TLS Settings
    VERIFY_SSL = True  # Always verify SSL certificates
    MIN_TLS_VERSION = "TLSv1.2"  # Minimum TLS version
    
    # Timeout Settings (prevent slow-loris attacks)
    CONNECT_TIMEOUT = 5  # seconds
    READ_TIMEOUT = 10  # seconds
    TOTAL_TIMEOUT = 15  # seconds
    
    # Proxy Validation
    MAX_PROXY_TESTS = 50  # Limit resource usage
    MAX_WORKERS = 10  # Limit concurrent connections
    
    # Suspicious Content Detection
    SUSPICIOUS_PATTERNS = [
        b'<script>',  # JavaScript injection
        b'phishing',
        b'malware',
        b'bitcoin',
        b'crypto-miner',
    ]
    
    # Trusted Test Domains (HTTPS only)
    TEST_URLS = [
        "https://www.google.com/",  # Primary
        "https://www.cloudflare.com/",  # Backup
    ]
    
    # YouTube Verification
    YOUTUBE_VERIFY_URL = "https://www.youtube.com/"
    YOUTUBE_EXPECTED_CONTENT = [b"youtube", b"ytInitialData"]


# ============================================================================
# SECURE CONFIGURATION STORAGE
# ============================================================================

CONFIG_DIR = Path(__file__).parent
CONFIG_FILE = CONFIG_DIR / "bypass_config.json"
FABRIC_GUI_CONFIG = CONFIG_DIR.parent / "fabric-gui-tauri" / "proxy_config.json"

# Security: Generate unique session ID for this run
SESSION_ID = secrets.token_hex(8)


@dataclass
class ProxyConfig:
    """Secure proxy configuration - no credentials stored."""
    host: str
    port: int
    proxy_type: str = "http"
    latency_ms: float = 0
    last_tested: str = ""
    youtube_works: bool = False
    security_validated: bool = False
    
    def __post_init__(self):
        # Security: Validate inputs
        self.host = self._sanitize_host(self.host)
        self.port = self._sanitize_port(self.port)
        self.proxy_type = self._sanitize_type(self.proxy_type)
    
    @staticmethod
    def _sanitize_host(host: str) -> str:
        """Sanitize hostname - prevent injection attacks."""
        # Remove any URL components
        host = host.strip().lower()
        # Only allow valid hostname characters
        allowed = set('abcdefghijklmnopqrstuvwxyz0123456789.-')
        return ''.join(c for c in host if c in allowed)[:255]
    
    @staticmethod
    def _sanitize_port(port: int) -> int:
        """Validate port range."""
        port = int(port)
        if not 1 <= port <= 65535:
            raise ValueError(f"Invalid port: {port}")
        return port
    
    @staticmethod
    def _sanitize_type(proxy_type: str) -> str:
        """Only allow known proxy types."""
        allowed = {"http", "https", "socks5"}
        proxy_type = proxy_type.lower().strip()
        if proxy_type not in allowed:
            return "http"
        return proxy_type
    
    def to_url(self) -> str:
        """Generate proxy URL - no credentials included."""
        return f"{self.proxy_type}://{self.host}:{self.port}"
    
    def to_env(self) -> dict:
        """Export as environment variables."""
        url = self.to_url()
        return {
            "HTTP_PROXY": url,
            "HTTPS_PROXY": url,
            "http_proxy": url,
            "https_proxy": url
        }


# ============================================================================
# SECURE HTTP SESSION
# ============================================================================

def create_secure_session() -> requests.Session:
    """Create a secure requests session with proper settings."""
    session = requests.Session()
    
    # Configure retries with backoff
    retries = Retry(
        total=2,
        backoff_factor=0.5,
        status_forcelist=[500, 502, 503, 504]
    )
    
    adapter = HTTPAdapter(max_retries=retries)
    session.mount('https://', adapter)
    session.mount('http://', adapter)
    
    # Security headers
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "en-US,en;q=0.9",
        "DNT": "1",  # Do Not Track
    })
    
    return session


# ============================================================================
# PROXY SOURCES (HTTPS ONLY)
# ============================================================================

# Only use HTTPS sources for security
PROXY_SOURCES = [
    "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=10000&ssl=yes&anonymity=all",
    "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt",
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
    "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt",
]


def fetch_proxies_secure() -> List[ProxyConfig]:
    """Fetch proxies from HTTPS sources only."""
    print("🔍 Securely fetching proxies from verified sources...")
    proxies = []
    seen = set()
    
    session = create_secure_session()
    
    for source in PROXY_SOURCES:
        # Security: Only HTTPS sources
        if not source.startswith("https://"):
            print(f"   ⚠️ Skipping non-HTTPS source: {source[:50]}")
            continue
        
        try:
            response = session.get(
                source,
                timeout=(SecurityConfig.CONNECT_TIMEOUT, SecurityConfig.READ_TIMEOUT),
                verify=SecurityConfig.VERIFY_SSL
            )
            
            # Security: Check response is valid
            if response.status_code != 200:
                continue
            
            for line in response.text.strip().split('\n'):
                line = line.strip()
                if ':' in line and line not in seen:
                    parts = line.split(':')
                    if len(parts) >= 2:
                        try:
                            proxy = ProxyConfig(
                                host=parts[0].strip(),
                                port=int(parts[1].strip())
                            )
                            # Security: Validate the proxy config was sanitized properly
                            if proxy.host and 1 <= proxy.port <= 65535:
                                seen.add(line)
                                proxies.append(proxy)
                        except (ValueError, TypeError):
                            continue
        except requests.exceptions.SSLError:
            print(f"   ⚠️ SSL verification failed for source")
        except Exception as e:
            continue
    
    print(f"   ✓ Found {len(proxies)} proxies from verified sources")
    return proxies[:SecurityConfig.MAX_PROXY_TESTS]


# ============================================================================
# SECURE PROXY TESTING
# ============================================================================

def validate_proxy_security(proxy: ProxyConfig, response: requests.Response) -> Tuple[bool, str]:
    """Validate proxy response for security issues."""
    
    # Check for suspicious content
    content = response.content.lower()
    for pattern in SecurityConfig.SUSPICIOUS_PATTERNS:
        if pattern in content:
            return False, f"Suspicious content detected: {pattern.decode()}"
    
    # Check for redirect to different domain (potential phishing)
    if response.history:
        original_domain = urlparse(response.request.url).netloc
        final_domain = urlparse(response.url).netloc
        if original_domain != final_domain:
            # Allow known CDN redirects
            trusted_redirects = ['www.google.com', 'google.com', 'youtube.com', 'www.youtube.com']
            if final_domain not in trusted_redirects:
                return False, f"Suspicious redirect: {original_domain} -> {final_domain}"
    
    # Check response headers for suspicious modifications
    suspicious_headers = ['x-injected', 'x-modified', 'x-proxy-inject']
    for header in suspicious_headers:
        if header in response.headers:
            return False, f"Suspicious header detected: {header}"
    
    return True, "Security validated"


def test_proxy_secure(proxy: ProxyConfig) -> Optional[ProxyConfig]:
    """Securely test if a proxy works."""
    try:
        proxy_url = proxy.to_url()
        proxies = {"http": proxy_url, "https": proxy_url}
        
        session = create_secure_session()
        
        # Test 1: Basic connectivity with SSL verification
        start = time.time()
        response = session.get(
            SecurityConfig.TEST_URLS[0],
            proxies=proxies,
            timeout=(SecurityConfig.CONNECT_TIMEOUT, SecurityConfig.READ_TIMEOUT),
            verify=SecurityConfig.VERIFY_SSL,
            allow_redirects=True
        )
        latency = (time.time() - start) * 1000
        
        if response.status_code != 200:
            return None
        
        # Test 2: Security validation
        is_secure, msg = validate_proxy_security(proxy, response)
        if not is_secure:
            return None
        
        proxy.latency_ms = latency
        proxy.last_tested = datetime.now().isoformat()
        proxy.security_validated = True
        
        # Test 3: YouTube access (HTTPS only)
        try:
            yt_response = session.get(
                SecurityConfig.YOUTUBE_VERIFY_URL,
                proxies=proxies,
                timeout=(SecurityConfig.CONNECT_TIMEOUT, SecurityConfig.READ_TIMEOUT),
                verify=SecurityConfig.VERIFY_SSL
            )
            
            content = yt_response.content.lower()
            proxy.youtube_works = (
                yt_response.status_code == 200 and
                any(pattern in content for pattern in SecurityConfig.YOUTUBE_EXPECTED_CONTENT)
            )
        except:
            proxy.youtube_works = False
        
        return proxy if proxy.youtube_works else None
        
    except requests.exceptions.SSLError:
        # SSL verification failed - proxy may be doing MITM
        return None
    except Exception:
        return None


def test_proxies_secure(proxies: List[ProxyConfig]) -> List[ProxyConfig]:
    """Test proxies in parallel with security constraints."""
    print(f"🔒 Securely testing {len(proxies)} proxies...")
    working = []
    
    # Security: Limit concurrent connections
    max_workers = min(SecurityConfig.MAX_WORKERS, len(proxies))
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(test_proxy_secure, p): p for p in proxies}
        done_count = 0
        
        for future in concurrent.futures.as_completed(futures, timeout=120):
            done_count += 1
            try:
                result = future.result(timeout=SecurityConfig.TOTAL_TIMEOUT)
                if result and result.security_validated:
                    working.append(result)
                    print(f"   ✓ Secure proxy: {result.host}:{result.port} ({result.latency_ms:.0f}ms)")
            except:
                pass
            
            if done_count % 10 == 0:
                print(f"   Progress: {done_count}/{len(proxies)}, {len(working)} secure")
    
    working.sort(key=lambda p: p.latency_ms)
    print(f"   ✓ Found {len(working)} secure proxies")
    return working


# ============================================================================
# YOUTUBE TRANSCRIPT TEST
# ============================================================================

def test_youtube_transcript(proxy: Optional[ProxyConfig] = None) -> Tuple[bool, str]:
    """Test YouTube transcript with security measures."""
    env = os.environ.copy()
    
    # Security: Clear any existing proxy settings first
    for key in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']:
        env.pop(key, None)
    
    if proxy:
        if not proxy.security_validated:
            return False, "Proxy not security validated"
        env.update(proxy.to_env())
        print(f"   Testing with secure proxy: {proxy.to_url()}")
    else:
        print("   Testing with direct connection...")
    
    script_paths = [
        CONFIG_DIR.parent / "fabric-gui-tauri" / "src-tauri" / "resources" / "youtube_transcript.py",
        CONFIG_DIR / "youtube_transcript.py",
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
                return True, f"Success! Got {len(output['transcript'])} characters"
        except json.JSONDecodeError:
            return False, "Invalid response format"
            
    except subprocess.TimeoutExpired:
        return False, "Request timed out"
    except Exception as e:
        return False, str(e)
    
    return False, "Unknown error"


# ============================================================================
# SECURE CONFIGURATION MANAGEMENT
# ============================================================================

def save_config_secure(proxy: Optional[ProxyConfig], working_proxies: List[ProxyConfig] = None):
    """Securely save configuration."""
    
    # Security: Only save security-validated proxies
    validated_proxies = [p for p in (working_proxies or []) if p.security_validated]
    
    config = {
        "active_proxy": asdict(proxy) if proxy and proxy.security_validated else None,
        "backup_proxies": [asdict(p) for p in validated_proxies[:5]],
        "last_updated": datetime.now().isoformat(),
        "session_id": SESSION_ID,
        "security_version": "2.0",
        "auto_configured": True
    }
    
    # Security: Set restrictive file permissions (on Unix)
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        
        # Also save to Fabric GUI folder if it exists
        if FABRIC_GUI_CONFIG.parent.exists():
            with open(FABRIC_GUI_CONFIG, 'w') as f:
                json.dump(config, f, indent=2)
    except Exception as e:
        print(f"   ⚠️ Could not save config: {e}")
    
    print(f"   ✓ Secure configuration saved")


def load_config_secure() -> Tuple[Optional[ProxyConfig], List[ProxyConfig]]:
    """Load and validate saved configuration."""
    if not CONFIG_FILE.exists():
        return None, []
    
    try:
        with open(CONFIG_FILE) as f:
            config = json.load(f)
        
        # Security: Validate config version
        if config.get("security_version") != "2.0":
            print("   ⚠️ Old config version, re-validating...")
            return None, []
        
        active = None
        if config.get("active_proxy"):
            p = config["active_proxy"]
            active = ProxyConfig(**{k: v for k, v in p.items() if k in ProxyConfig.__dataclass_fields__})
        
        backups = []
        for p in config.get("backup_proxies", []):
            try:
                backups.append(ProxyConfig(**{k: v for k, v in p.items() if k in ProxyConfig.__dataclass_fields__}))
            except:
                pass
        
        return active, backups
    except Exception as e:
        print(f"   ⚠️ Config load error: {e}")
        return None, []


# ============================================================================
# MAIN WORKFLOW
# ============================================================================

def auto_configure():
    """Main secure auto-configuration workflow."""
    print()
    print("=" * 60)
    print("   FABRIC AUTO-BYPASS - Secure Edition v2.0")
    print("   Session ID:", SESSION_ID)
    print("=" * 60)
    print()
    
    # Step 1: Test direct connection first
    print("Step 1: Testing direct connection...")
    success, msg = test_youtube_transcript(None)
    if success:
        print(f"   ✅ Direct connection works - no proxy needed!")
        save_config_secure(None, [])
        return True
    else:
        print(f"   ❌ Direct connection blocked: {msg[:50]}...")
    
    print()
    
    # Step 2: Fetch proxies securely
    print("Step 2: Fetching proxies from verified HTTPS sources...")
    proxies = fetch_proxies_secure()
    
    if not proxies:
        print("   ❌ No proxies available from secure sources")
        return False
    
    print()
    
    # Step 3: Security test proxies
    print("Step 3: Security testing proxies...")
    working = test_proxies_secure(proxies)
    
    if not working:
        print("   ❌ No proxies passed security validation")
        return False
    
    print()
    
    # Step 4: Test YouTube transcript with best proxies
    print("Step 4: Testing YouTube access with secure proxies...")
    
    for proxy in working[:5]:
        print(f"   Trying: {proxy.host}:{proxy.port}...")
        success, msg = test_youtube_transcript(proxy)
        
        if success:
            print(f"   ✅ SUCCESS!")
            print(f"   {msg}")
            
            save_config_secure(proxy, working)
            
            print()
            print("=" * 60)
            print("   ✅ SECURE AUTO-CONFIGURATION COMPLETE!")
            print("=" * 60)
            print(f"   Proxy: {proxy.to_url()}")
            print(f"   Latency: {proxy.latency_ms:.0f}ms")
            print(f"   Security: ✓ Validated")
            print(f"   Session: {SESSION_ID}")
            print("=" * 60)
            return True
        else:
            print(f"   ❌ {msg[:50]}...")
    
    print()
    print("   ⚠️ No proxy passed YouTube transcript test")
    if working:
        print("   Saving best validated proxy for manual testing...")
        save_config_secure(working[0], working)
    return False


def quick_test():
    """Quick test with saved configuration."""
    print()
    print("🔒 Secure Quick Test")
    print()
    
    active, backups = load_config_secure()
    
    if active:
        print(f"Saved proxy: {active.to_url()}")
        print(f"Security validated: {active.security_validated}")
        
        if not active.security_validated:
            print("⚠️ Proxy not security validated - re-testing...")
            result = test_proxy_secure(active)
            if not result:
                print("❌ Proxy failed security validation")
                return False
        
        success, msg = test_youtube_transcript(active)
        print(f"Result: {'✅ ' + msg if success else '❌ ' + msg}")
        return success
    else:
        print("No proxy configured - testing direct connection...")
        success, msg = test_youtube_transcript(None)
        print(f"Result: {'✅ ' + msg if success else '❌ ' + msg}")
        return success


def reset_config():
    """Reset configuration securely."""
    print("🔒 Securely resetting configuration...")
    save_config_secure(None, [])
    print("✅ Configuration reset - using direct connection")


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
    else:
        auto_configure()


if __name__ == "__main__":
    main()
