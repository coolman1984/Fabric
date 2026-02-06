"""
Pattern Loader

Loads patterns directly from the filesystem without needing Fabric server.
"""

import os
from typing import Optional


class PatternLoader:
    """
    Loads Fabric patterns directly from the filesystem.
    """
    
    def __init__(self, patterns_dir: str = None):
        """
        Initialize pattern loader.
        
        Args:
            patterns_dir: Path to patterns directory.
                         Defaults to Fabric's data/patterns location.
        """
        if patterns_dir is None:
            # Try to find patterns in common locations
            possible_paths = [
                # Current repo
                os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "patterns"),
                # Home directory fabric config
                os.path.join(os.path.expanduser("~"), ".config", "fabric", "patterns"),
                # Windows AppData
                os.path.join(os.environ.get("APPDATA", ""), "fabric", "patterns"),
            ]
            
            for path in possible_paths:
                if os.path.isdir(path):
                    patterns_dir = path
                    break
        
        self.patterns_dir = patterns_dir
        self._pattern_cache: dict[str, str] = {}
    
    def get_patterns_dir(self) -> Optional[str]:
        """Get the patterns directory path."""
        return self.patterns_dir
    
    def list_patterns(self) -> list[str]:
        """
        Get list of all available pattern names.
        
        Returns:
            Sorted list of pattern names
        """
        if not self.patterns_dir or not os.path.isdir(self.patterns_dir):
            return []
        
        patterns = []
        try:
            for name in os.listdir(self.patterns_dir):
                pattern_path = os.path.join(self.patterns_dir, name)
                system_file = os.path.join(pattern_path, "system.md")
                
                if os.path.isdir(pattern_path) and os.path.isfile(system_file):
                    patterns.append(name)
        except Exception:
            pass
        
        return sorted(patterns)
    
    def get_pattern_content(self, name: str) -> str:
        """
        Get the content of a pattern's system.md file.
        
        Args:
            name: Pattern name
            
        Returns:
            Pattern content or empty string if not found
        """
        # Check cache
        if name in self._pattern_cache:
            return self._pattern_cache[name]
        
        if not self.patterns_dir:
            return ""
        
        system_file = os.path.join(self.patterns_dir, name, "system.md")
        
        try:
            if os.path.isfile(system_file):
                with open(system_file, "r", encoding="utf-8") as f:
                    content = f.read()
                    self._pattern_cache[name] = content
                    return content
        except Exception:
            pass
        
        return ""
    
    def pattern_exists(self, name: str) -> bool:
        """Check if a pattern exists."""
        if not self.patterns_dir:
            return False
        
        system_file = os.path.join(self.patterns_dir, name, "system.md")
        return os.path.isfile(system_file)
