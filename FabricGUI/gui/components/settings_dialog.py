"""
Settings Dialog

Modal dialog for configuring API keys and preferences.
"""

import customtkinter as ctk
from typing import Callable, Optional
from utils.settings_manager import SettingsManager, AppSettings


class SettingsDialog(ctk.CTkToplevel):
    """
    Settings dialog for API key configuration.
    """
    
    def __init__(
        self,
        parent,
        settings_manager: SettingsManager,
        on_save: Callable[[], None] = None
    ):
        super().__init__(parent)
        
        self.settings_manager = settings_manager
        self.on_save = on_save
        
        # Configure window - make it taller
        self.title("⚙️ Settings - API Keys")
        self.geometry("600x650")
        self.resizable(True, True)
        self.minsize(500, 550)
        
        # Make modal
        self.transient(parent)
        self.grab_set()
        
        # Center on parent
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - 600) // 2
        y = parent.winfo_y() + (parent.winfo_height() - 650) // 2
        self.geometry(f"+{x}+{y}")
        
        self._setup_ui()
        self._load_settings()
    
    def _setup_ui(self):
        """Create the UI."""
        # Configure grid for the window
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)  # Scrollable area
        self.grid_rowconfigure(1, weight=0)  # Buttons (fixed at bottom)
        
        # Scrollable container for API keys
        scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=(20, 10))
        scroll_frame.grid_columnconfigure(0, weight=1)
        
        # Title
        ctk.CTkLabel(
            scroll_frame,
            text="🔑 API Key Configuration",
            font=ctk.CTkFont(size=20, weight="bold")
        ).grid(row=0, column=0, sticky="w", pady=(0, 10))
        
        # Info label
        ctk.CTkLabel(
            scroll_frame,
            text="Enter your API keys below. Keys are stored locally on your computer.",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        ).grid(row=1, column=0, sticky="w", pady=(0, 20))
        
        # === Google Gemini ===
        row = 2
        ctk.CTkLabel(
            scroll_frame,
            text="🌐 Google Gemini",
            font=ctk.CTkFont(size=15, weight="bold")
        ).grid(row=row, column=0, sticky="w", pady=(10, 0))
        row += 1
        
        ctk.CTkLabel(
            scroll_frame,
            text="Get key from: console.cloud.google.com/apis/credentials",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        ).grid(row=row, column=0, sticky="w")
        row += 1
        
        self.google_key_entry = ctk.CTkEntry(
            scroll_frame,
            placeholder_text="AIza...",
            show="•",
            height=40,
            font=ctk.CTkFont(size=13)
        )
        self.google_key_entry.grid(row=row, column=0, sticky="ew", pady=5)
        row += 1
        
        self.google_show_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            scroll_frame,
            text="Show key",
            variable=self.google_show_var,
            command=lambda: self._toggle_show(self.google_key_entry, self.google_show_var),
            font=ctk.CTkFont(size=11)
        ).grid(row=row, column=0, sticky="w")
        row += 1
        
        # === OpenAI ===
        ctk.CTkLabel(
            scroll_frame,
            text="🤖 OpenAI",
            font=ctk.CTkFont(size=15, weight="bold")
        ).grid(row=row, column=0, sticky="w", pady=(20, 0))
        row += 1
        
        ctk.CTkLabel(
            scroll_frame,
            text="Get key from: platform.openai.com/api-keys",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        ).grid(row=row, column=0, sticky="w")
        row += 1
        
        self.openai_key_entry = ctk.CTkEntry(
            scroll_frame,
            placeholder_text="sk-...",
            show="•",
            height=40,
            font=ctk.CTkFont(size=13)
        )
        self.openai_key_entry.grid(row=row, column=0, sticky="ew", pady=5)
        row += 1
        
        self.openai_show_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            scroll_frame,
            text="Show key",
            variable=self.openai_show_var,
            command=lambda: self._toggle_show(self.openai_key_entry, self.openai_show_var),
            font=ctk.CTkFont(size=11)
        ).grid(row=row, column=0, sticky="w")
        row += 1
        
        # === Anthropic ===
        ctk.CTkLabel(
            scroll_frame,
            text="🧠 Anthropic (Claude)",
            font=ctk.CTkFont(size=15, weight="bold")
        ).grid(row=row, column=0, sticky="w", pady=(20, 0))
        row += 1
        
        ctk.CTkLabel(
            scroll_frame,
            text="Get key from: console.anthropic.com/settings/keys",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        ).grid(row=row, column=0, sticky="w")
        row += 1
        
        self.anthropic_key_entry = ctk.CTkEntry(
            scroll_frame,
            placeholder_text="sk-ant-...",
            show="•",
            height=40,
            font=ctk.CTkFont(size=13)
        )
        self.anthropic_key_entry.grid(row=row, column=0, sticky="ew", pady=5)
        row += 1
        
        self.anthropic_show_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            scroll_frame,
            text="Show key",
            variable=self.anthropic_show_var,
            command=lambda: self._toggle_show(self.anthropic_key_entry, self.anthropic_show_var),
            font=ctk.CTkFont(size=11)
        ).grid(row=row, column=0, sticky="w")
        row += 1
        
        # Spacer
        ctk.CTkLabel(scroll_frame, text="").grid(row=row, column=0, pady=10)
        
        # === Buttons (fixed at bottom, outside scroll) ===
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=(10, 20))
        
        # Save button - prominent
        save_btn = ctk.CTkButton(
            button_frame,
            text="💾 Save API Keys",
            width=150,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#10b981",
            hover_color="#059669",
            command=self._save_settings
        )
        save_btn.pack(side="right", padx=5)
        
        # Cancel button
        cancel_btn = ctk.CTkButton(
            button_frame,
            text="Cancel",
            width=100,
            height=40,
            fg_color="#6b7280",
            hover_color="#4b5563",
            command=self.destroy
        )
        cancel_btn.pack(side="right", padx=5)
    
    def _toggle_show(self, entry: ctk.CTkEntry, var: ctk.BooleanVar):
        """Toggle password visibility."""
        entry.configure(show="" if var.get() else "•")
    
    def _load_settings(self):
        """Load current settings into form."""
        settings = self.settings_manager.load()
        
        if settings.google_api_key:
            self.google_key_entry.insert(0, settings.google_api_key)
        if settings.openai_api_key:
            self.openai_key_entry.insert(0, settings.openai_api_key)
        if settings.anthropic_api_key:
            self.anthropic_key_entry.insert(0, settings.anthropic_api_key)
    
    def _save_settings(self):
        """Save settings and close dialog."""
        settings = self.settings_manager.load()
        
        settings.google_api_key = self.google_key_entry.get().strip()
        settings.openai_api_key = self.openai_key_entry.get().strip()
        settings.anthropic_api_key = self.anthropic_key_entry.get().strip()
        
        self.settings_manager.save(settings)
        
        if self.on_save:
            self.on_save()
        
        self.destroy()
