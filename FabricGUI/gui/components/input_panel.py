"""
Input Panel Component

Tabbed input area for Text, URL scraping, and YouTube transcript extraction.
"""

import customtkinter as ctk
from typing import Callable, Optional


class InputPanel(ctk.CTkFrame):
    """
    Multi-mode input panel supporting:
    - Direct text input
    - URL for web scraping
    - YouTube URL for transcript extraction
    """
    
    def __init__(
        self,
        parent,
        on_input_changed: Callable[[], None] = None,
        **kwargs
    ):
        super().__init__(parent, **kwargs)
        
        self.on_input_changed = on_input_changed
        self.current_mode = "text"
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Create the UI components."""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Mode selector
        mode_frame = ctk.CTkFrame(self, fg_color="transparent")
        mode_frame.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="ew")
        
        ctk.CTkLabel(
            mode_frame,
            text="Input Source:",
            font=ctk.CTkFont(size=12)
        ).pack(side="left", padx=(0, 10))
        
        self.mode_var = ctk.StringVar(value="text")
        
        modes = [
            ("📝 Text", "text"),
            ("🌐 URL", "url"),
            ("▶️ YouTube", "youtube")
        ]
        
        for label, value in modes:
            rb = ctk.CTkRadioButton(
                mode_frame,
                text=label,
                variable=self.mode_var,
                value=value,
                command=self._on_mode_changed
            )
            rb.pack(side="left", padx=10)
        
        # Input container
        self.input_container = ctk.CTkFrame(self, fg_color="transparent")
        self.input_container.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")
        self.input_container.grid_columnconfigure(0, weight=1)
        self.input_container.grid_rowconfigure(0, weight=1)
        
        # Text input (default)
        self.text_input = ctk.CTkTextbox(
            self.input_container,
            wrap="word",
            font=ctk.CTkFont(size=13),
            corner_radius=8
        )
        self.text_input.grid(row=0, column=0, sticky="nsew")
        self.text_input.bind("<KeyRelease>", self._on_text_changed)
        
        # URL input (hidden initially)
        self.url_frame = ctk.CTkFrame(self.input_container, fg_color="transparent")
        
        ctk.CTkLabel(
            self.url_frame,
            text="Enter URL to scrape:",
            font=ctk.CTkFont(size=12),
            anchor="w"
        ).pack(fill="x", pady=(0, 5))
        
        self.url_entry = ctk.CTkEntry(
            self.url_frame,
            placeholder_text="https://example.com/article",
            height=40,
            font=ctk.CTkFont(size=13)
        )
        self.url_entry.pack(fill="x", pady=5)
        self.url_entry.bind("<KeyRelease>", self._on_text_changed)
        
        ctk.CTkLabel(
            self.url_frame,
            text="💡 The URL will be scraped to markdown using Jina AI before processing.",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        ).pack(fill="x", pady=5)
        
        # YouTube input (hidden initially)
        self.youtube_frame = ctk.CTkFrame(self.input_container, fg_color="transparent")
        
        ctk.CTkLabel(
            self.youtube_frame,
            text="Enter YouTube URL:",
            font=ctk.CTkFont(size=12),
            anchor="w"
        ).pack(fill="x", pady=(0, 5))
        
        self.youtube_entry = ctk.CTkEntry(
            self.youtube_frame,
            placeholder_text="https://youtube.com/watch?v=...",
            height=40,
            font=ctk.CTkFont(size=13)
        )
        self.youtube_entry.pack(fill="x", pady=5)
        self.youtube_entry.bind("<KeyRelease>", self._on_text_changed)
        
        # Timestamps toggle
        self.timestamps_var = ctk.BooleanVar(value=False)
        self.timestamps_check = ctk.CTkCheckBox(
            self.youtube_frame,
            text="Include timestamps in transcript",
            variable=self.timestamps_var
        )
        self.timestamps_check.pack(fill="x", pady=5)
        
        ctk.CTkLabel(
            self.youtube_frame,
            text="💡 Transcript will be fetched and sent to the selected pattern.",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        ).pack(fill="x", pady=5)
        
        # Character count
        self.char_count_label = ctk.CTkLabel(
            self,
            text="0 characters",
            font=ctk.CTkFont(size=10),
            text_color="gray"
        )
        self.char_count_label.grid(row=2, column=0, padx=10, pady=2, sticky="e")
    
    def _on_mode_changed(self):
        """Handle input mode change."""
        mode = self.mode_var.get()
        self.current_mode = mode
        
        # Hide all inputs
        self.text_input.grid_remove()
        self.url_frame.grid_remove()
        self.youtube_frame.grid_remove()
        
        # Show selected input
        if mode == "text":
            self.text_input.grid(row=0, column=0, sticky="nsew")
        elif mode == "url":
            self.url_frame.grid(row=0, column=0, sticky="new")
        elif mode == "youtube":
            self.youtube_frame.grid(row=0, column=0, sticky="new")
        
        self._update_char_count()
    
    def _on_text_changed(self, event=None):
        """Handle text input changes."""
        self._update_char_count()
        if self.on_input_changed:
            self.on_input_changed()
    
    def _update_char_count(self):
        """Update the character count display."""
        text = self.get_input_text()
        count = len(text)
        self.char_count_label.configure(text=f"{count:,} characters")
    
    def get_mode(self) -> str:
        """Get current input mode: 'text', 'url', or 'youtube'."""
        return self.current_mode
    
    def get_input_text(self) -> str:
        """Get the current input text based on mode."""
        mode = self.current_mode
        
        if mode == "text":
            return self.text_input.get("1.0", "end-1c")
        elif mode == "url":
            return self.url_entry.get().strip()
        elif mode == "youtube":
            return self.youtube_entry.get().strip()
        
        return ""
    
    def get_youtube_timestamps(self) -> bool:
        """Get whether YouTube timestamps are enabled."""
        return self.timestamps_var.get()
    
    def set_input_text(self, text: str):
        """Set the text input (only works in text mode)."""
        if self.current_mode == "text":
            self.text_input.delete("1.0", "end")
            self.text_input.insert("1.0", text)
            self._update_char_count()
    
    def clear_input(self):
        """Clear the current input."""
        mode = self.current_mode
        
        if mode == "text":
            self.text_input.delete("1.0", "end")
        elif mode == "url":
            self.url_entry.delete(0, "end")
        elif mode == "youtube":
            self.youtube_entry.delete(0, "end")
        
        self._update_char_count()
