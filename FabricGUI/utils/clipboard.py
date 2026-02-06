"""
Clipboard utilities for cross-platform copy/paste operations.
"""

import platform
import subprocess
from typing import Optional


def copy_to_clipboard(text: str) -> bool:
    """
    Copy text to the system clipboard.
    
    Args:
        text: The text to copy
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Try pyperclip first (cross-platform)
        import pyperclip
        pyperclip.copy(text)
        return True
    except ImportError:
        pass
    
    # Fallback to platform-specific methods
    system = platform.system()
    
    try:
        if system == "Windows":
            # Use PowerShell's Set-Clipboard
            process = subprocess.Popen(
                ["powershell", "-Command", "Set-Clipboard", "-Value", text],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            process.communicate()
            return process.returncode == 0
            
        elif system == "Darwin":  # macOS
            process = subprocess.Popen(
                ["pbcopy"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            process.communicate(input=text.encode("utf-8"))
            return process.returncode == 0
            
        elif system == "Linux":
            # Try xclip first, then xsel
            for cmd in [["xclip", "-selection", "clipboard"], ["xsel", "--clipboard", "--input"]]:
                try:
                    process = subprocess.Popen(
                        cmd,
                        stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE
                    )
                    process.communicate(input=text.encode("utf-8"))
                    if process.returncode == 0:
                        return True
                except FileNotFoundError:
                    continue
            return False
            
    except Exception:
        return False
    
    return False


def get_from_clipboard() -> Optional[str]:
    """
    Get text from the system clipboard.
    
    Returns:
        Clipboard text or None if failed
    """
    try:
        # Try pyperclip first
        import pyperclip
        return pyperclip.paste()
    except ImportError:
        pass
    
    system = platform.system()
    
    try:
        if system == "Windows":
            process = subprocess.Popen(
                ["powershell", "-Command", "Get-Clipboard"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            stdout, _ = process.communicate()
            if process.returncode == 0:
                return stdout.decode("utf-8").strip()
                
        elif system == "Darwin":
            process = subprocess.Popen(
                ["pbpaste"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            stdout, _ = process.communicate()
            if process.returncode == 0:
                return stdout.decode("utf-8")
                
        elif system == "Linux":
            for cmd in [["xclip", "-selection", "clipboard", "-o"], ["xsel", "--clipboard", "--output"]]:
                try:
                    process = subprocess.Popen(
                        cmd,
                        stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE
                    )
                    stdout, _ = process.communicate()
                    if process.returncode == 0:
                        return stdout.decode("utf-8")
                except FileNotFoundError:
                    continue
                    
    except Exception:
        pass
    
    return None
