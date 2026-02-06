"""
Settings Manager

Handles saving/loading API keys and user preferences.
"""

import json
import os
from typing import Optional
from dataclasses import dataclass, asdict


@dataclass
class AppSettings:
    """Application settings including API keys."""
    # API Keys
    google_api_key: str = ""
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    
    # Preferred settings
    default_vendor: str = "Google Gemini"
    default_model: str = "gemini-2.0-flash"
    default_temperature: float = 0.7
    default_top_p: float = 0.9
    
    # Ollama settings
    ollama_url: str = "http://localhost:11434"


class SettingsManager:
    """
    Manages application settings and API keys.
    Stores settings in user's config directory.
    """
    
    def __init__(self):
        self.config_dir = os.path.join(
            os.path.expanduser("~"), ".config", "fabric-gui"
        )
        self.settings_file = os.path.join(self.config_dir, "settings.json")
        self._settings: Optional[AppSettings] = None
    
    def load(self) -> AppSettings:
        """Load settings from file or return defaults."""
        if self._settings is not None:
            return self._settings
        
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._settings = AppSettings(**data)
            else:
                self._settings = AppSettings()
        except Exception:
            self._settings = AppSettings()
        
        return self._settings
    
    def save(self, settings: AppSettings):
        """Save settings to file."""
        self._settings = settings
        
        try:
            os.makedirs(self.config_dir, exist_ok=True)
            with open(self.settings_file, "w", encoding="utf-8") as f:
                json.dump(asdict(settings), f, indent=2)
        except Exception as e:
            print(f"Error saving settings: {e}")
    
    def get_api_key(self, vendor: str) -> str:
        """Get API key for a specific vendor."""
        settings = self.load()
        
        if vendor == "Google Gemini":
            return settings.google_api_key
        elif vendor == "OpenAI":
            return settings.openai_api_key
        elif vendor == "Anthropic":
            return settings.anthropic_api_key
        elif vendor == "Ollama (Local)":
            return ""  # Ollama doesn't need API key
        
        return ""
    
    def has_api_key(self, vendor: str) -> bool:
        """Check if API key is configured for vendor."""
        if vendor == "Ollama (Local)":
            return True  # Ollama doesn't need key
        return bool(self.get_api_key(vendor))
