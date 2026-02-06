"""
Fullscreen Output Viewer

An elegant fullscreen window for reading AI output with professional styling.
"""

import customtkinter as ctk
from typing import Optional
import os
from datetime import datetime


class FullscreenViewer(ctk.CTkToplevel):
    """
    Professional fullscreen viewer for output content.
    Features clean typography, dark/light mode, and quick actions.
    """
    
    def __init__(self, parent, content: str, title: str = "Output"):
        super().__init__(parent)
        
        self.content = content
        
        # Configure window
        self.title(f"📖 {title}")
        
        # Get screen dimensions and go fullscreen
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        self.geometry(f"{screen_width}x{screen_height}+0+0")
        
        # Make it look fullscreen
        self.attributes("-topmost", True)
        self.after(100, lambda: self.attributes("-topmost", False))
        
        # Theme state
        self.is_dark = False
        
        # Setup UI
        self._setup_ui()
        
        # Keyboard shortcuts
        self.bind("<Escape>", lambda e: self.destroy())
        self.bind("<F11>", lambda e: self._toggle_fullscreen())
        self.bind("<Control-plus>", lambda e: self._increase_font())
        self.bind("<Control-minus>", lambda e: self._decrease_font())
        self.bind("<Control-d>", lambda e: self._toggle_theme())
        self.bind("<Control-c>", lambda e: self._copy_content())
        
        self.font_size = 16
        self._is_fullscreen = False
    
    def _setup_ui(self):
        """Create the elegant UI."""
        # Main container with subtle gradient effect
        self.main_container = ctk.CTkFrame(self, corner_radius=0)
        self.main_container.pack(fill="both", expand=True)
        
        # Top toolbar
        toolbar = ctk.CTkFrame(self.main_container, height=50, corner_radius=0)
        toolbar.pack(fill="x", padx=0, pady=0)
        toolbar.pack_propagate(False)
        
        # Left side - title
        title_label = ctk.CTkLabel(
            toolbar,
            text="📖 Output Viewer",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title_label.pack(side="left", padx=20, pady=10)
        
        # Right side - buttons
        btn_frame = ctk.CTkFrame(toolbar, fg_color="transparent")
        btn_frame.pack(side="right", padx=10)
        
        # Theme toggle
        self.theme_btn = ctk.CTkButton(
            btn_frame,
            text="🌙 Dark",
            width=80,
            height=32,
            command=self._toggle_theme,
            fg_color=("#374151", "#1f2937"),
            hover_color=("#1f2937", "#111827")
        )
        self.theme_btn.pack(side="left", padx=3)
        
        # Font size controls
        ctk.CTkButton(
            btn_frame,
            text="A-",
            width=40,
            height=32,
            command=self._decrease_font,
            fg_color=("#6b7280", "#4b5563"),
            hover_color=("#4b5563", "#374151")
        ).pack(side="left", padx=3)
        
        ctk.CTkButton(
            btn_frame,
            text="A+",
            width=40,
            height=32,
            command=self._increase_font,
            fg_color=("#6b7280", "#4b5563"),
            hover_color=("#4b5563", "#374151")
        ).pack(side="left", padx=3)
        
        # Copy button
        ctk.CTkButton(
            btn_frame,
            text="📋 Copy",
            width=80,
            height=32,
            command=self._copy_content,
            fg_color=("#10b981", "#059669"),
            hover_color=("#059669", "#047857")
        ).pack(side="left", padx=3)
        
        # Save button
        ctk.CTkButton(
            btn_frame,
            text="💾 Save",
            width=80,
            height=32,
            command=self._save_content,
            fg_color=("#3b82f6", "#2563eb"),
            hover_color=("#2563eb", "#1d4ed8")
        ).pack(side="left", padx=3)
        
        # Close button
        ctk.CTkButton(
            btn_frame,
            text="✕ Close",
            width=80,
            height=32,
            command=self.destroy,
            fg_color=("#dc2626", "#b91c1c"),
            hover_color=("#b91c1c", "#991b1b")
        ).pack(side="left", padx=3)
        
        # Content area with nice padding
        content_frame = ctk.CTkFrame(
            self.main_container,
            corner_radius=0,
            fg_color=("gray98", "gray10")
        )
        content_frame.pack(fill="both", expand=True, padx=0, pady=0)
        
        # Centered reading container (max width for readability)
        reading_container = ctk.CTkFrame(
            content_frame,
            fg_color="transparent"
        )
        reading_container.pack(fill="both", expand=True, padx=100, pady=30)
        
        # Text widget with elegant styling
        self.text_widget = ctk.CTkTextbox(
            reading_container,
            font=ctk.CTkFont(family="Georgia", size=16),
            wrap="word",
            corner_radius=12,
            fg_color=("white", "gray15"),
            text_color=("gray15", "gray90"),
            scrollbar_button_color=("gray70", "gray40"),
            scrollbar_button_hover_color=("gray60", "gray50")
        )
        self.text_widget.pack(fill="both", expand=True)
        
        # Insert content
        self.text_widget.insert("1.0", self.content)
        self.text_widget.configure(state="disabled")
        
        # Bottom status bar
        status_bar = ctk.CTkFrame(
            self.main_container,
            height=30,
            corner_radius=0,
            fg_color=("gray90", "gray20")
        )
        status_bar.pack(fill="x")
        status_bar.pack_propagate(False)
        
        # Stats
        chars = len(self.content)
        words = len(self.content.split())
        lines = self.content.count('\n') + 1
        
        self.status_label = ctk.CTkLabel(
            status_bar,
            text=f"📊 {chars:,} characters • {words:,} words • {lines:,} lines  |  Esc to close • Ctrl+D toggle theme • Ctrl+/- font size",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        self.status_label.pack(side="left", padx=15, pady=5)
    
    def _toggle_theme(self):
        """Toggle between light and dark mode."""
        self.is_dark = not self.is_dark
        
        if self.is_dark:
            self.theme_btn.configure(text="☀️ Light")
            self.text_widget.configure(
                fg_color="gray15",
                text_color="gray90"
            )
        else:
            self.theme_btn.configure(text="🌙 Dark")
            self.text_widget.configure(
                fg_color="white",
                text_color="gray15"
            )
    
    def _increase_font(self):
        """Increase font size."""
        self.font_size = min(self.font_size + 2, 32)
        self.text_widget.configure(font=ctk.CTkFont(family="Georgia", size=self.font_size))
    
    def _decrease_font(self):
        """Decrease font size."""
        self.font_size = max(self.font_size - 2, 10)
        self.text_widget.configure(font=ctk.CTkFont(family="Georgia", size=self.font_size))
    
    def _toggle_fullscreen(self):
        """Toggle fullscreen mode."""
        self._is_fullscreen = not self._is_fullscreen
        self.attributes("-fullscreen", self._is_fullscreen)
    
    def _copy_content(self):
        """Copy content to clipboard."""
        self.clipboard_clear()
        self.clipboard_append(self.content)
        
        original = self.status_label.cget("text")
        self.status_label.configure(text="✓ Copied to clipboard!")
        self.after(2000, lambda: self.status_label.configure(text=original))
    
    def _save_content(self):
        """Save content to file."""
        from tkinter import filedialog
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = f"fabric_output_{timestamp}.md"
        
        filepath = filedialog.asksaveasfilename(
            defaultextension=".md",
            filetypes=[
                ("Markdown", "*.md"),
                ("Text", "*.txt"),
                ("All files", "*.*")
            ],
            initialfile=default_name
        )
        
        if filepath:
            try:
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(self.content)
                
                original = self.status_label.cget("text")
                self.status_label.configure(text=f"✓ Saved to {os.path.basename(filepath)}")
                self.after(3000, lambda: self.status_label.configure(text=original))
            except Exception as e:
                self.status_label.configure(text=f"❌ Save failed: {str(e)}")
