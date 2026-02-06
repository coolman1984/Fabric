"""
Output Panel Component

Optimized scrollable output display with fast streaming and copy/save actions.
"""

import customtkinter as ctk
from typing import Optional
import os
from datetime import datetime


class OutputPanel(ctk.CTkFrame):
    """
    Output display panel with:
    - Fast streaming text area
    - Clear, copy, and save buttons
    - Optimized for performance
    """
    
    def __init__(
        self,
        parent,
        **kwargs
    ):
        super().__init__(parent, **kwargs)
        
        self.full_output = ""
        self._pending_text = ""  # Buffer for batching updates
        self._update_scheduled = False
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Create the UI components."""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Header with actions
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="ew")
        
        ctk.CTkLabel(
            header_frame,
            text="📄 Output",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(side="left")
        
        # Action buttons - with visible colors for light theme
        self.save_btn = ctk.CTkButton(
            header_frame,
            text="💾 Save",
            width=80,
            height=28,
            command=self._save_output,
            fg_color=("#3b82f6", "#2563eb"),
            hover_color=("#2563eb", "#1d4ed8"),
            text_color="white"
        )
        self.save_btn.pack(side="right", padx=2)
        
        self.copy_btn = ctk.CTkButton(
            header_frame,
            text="📋 Copy",
            width=80,
            height=28,
            command=self._copy_output,
            fg_color=("#10b981", "#059669"),
            hover_color=("#059669", "#047857"),
            text_color="white"
        )
        self.copy_btn.pack(side="right", padx=2)
        
        # Fullscreen button
        self.fullscreen_btn = ctk.CTkButton(
            header_frame,
            text="🔍 View",
            width=80,
            height=28,
            command=self._open_fullscreen,
            fg_color=("#8b5cf6", "#7c3aed"),
            hover_color=("#7c3aed", "#6d28d9"),
            text_color="white"
        )
        self.fullscreen_btn.pack(side="right", padx=2)
        
        self.clear_btn = ctk.CTkButton(
            header_frame,
            text="🗑️ Clear",
            width=80,
            height=28,
            command=self.clear_output,
            fg_color=("#6b7280", "#4b5563"),
            hover_color=("#4b5563", "#374151"),
            text_color="white"
        )
        self.clear_btn.pack(side="right", padx=2)
        
        # Output text area - optimized for performance
        self.output_text = ctk.CTkTextbox(
            self,
            wrap="word",
            font=ctk.CTkFont(family="Consolas", size=13),
            corner_radius=8,
            state="disabled"
        )
        self.output_text.grid(row=1, column=0, padx=10, pady=(5, 10), sticky="nsew")
        
        # Status bar
        self.status_label = ctk.CTkLabel(
            self,
            text="Ready",
            font=ctk.CTkFont(size=10),
            text_color="gray"
        )
        self.status_label.grid(row=2, column=0, padx=10, pady=2, sticky="w")
    
    def append_text(self, text: str):
        """Append text to the output (optimized for streaming)."""
        self.full_output += text
        self._pending_text += text
        
        # Batch updates for performance - update every 50ms
        if not self._update_scheduled:
            self._update_scheduled = True
            self.after(50, self._flush_pending_text)
    
    def _flush_pending_text(self):
        """Flush pending text to the display."""
        if self._pending_text:
            self.output_text.configure(state="normal")
            self.output_text.insert("end", self._pending_text)
            self.output_text.see("end")
            self.output_text.configure(state="disabled")
            self._pending_text = ""
        
        self._update_scheduled = False
        self._update_status()
    
    def set_output(self, text: str):
        """Set the complete output text."""
        self.full_output = text
        self._pending_text = ""
        
        self.output_text.configure(state="normal")
        self.output_text.delete("1.0", "end")
        self.output_text.insert("1.0", text)
        self.output_text.configure(state="disabled")
        
        self._update_status()
    
    def clear_output(self):
        """Clear the output."""
        self.full_output = ""
        self._pending_text = ""
        
        self.output_text.configure(state="normal")
        self.output_text.delete("1.0", "end")
        self.output_text.configure(state="disabled")
        
        self.status_label.configure(text="Ready")
    
    def set_loading(self, message: str = "Processing..."):
        """Show loading state."""
        self.status_label.configure(text=f"⏳ {message}")
    
    def set_error(self, error: str):
        """Display an error message."""
        self.full_output = f"❌ Error: {error}"
        
        self.output_text.configure(state="normal")
        self.output_text.delete("1.0", "end")
        self.output_text.insert("1.0", self.full_output)
        self.output_text.configure(state="disabled")
        
        self.status_label.configure(text="Error occurred")
    
    def set_complete(self):
        """Mark output as complete."""
        # Flush any remaining text
        if self._pending_text:
            self._flush_pending_text()
        self._update_status()
    
    def _update_status(self):
        """Update the status bar."""
        chars = len(self.full_output)
        words = len(self.full_output.split())
        lines = self.full_output.count('\n') + 1 if self.full_output else 0
        
        self.status_label.configure(
            text=f"✓ {chars:,} chars | {words:,} words | {lines:,} lines"
        )
    
    def _copy_output(self):
        """Copy output to clipboard."""
        if not self.full_output:
            return
        
        try:
            from utils.clipboard import copy_to_clipboard
            if copy_to_clipboard(self.full_output):
                original = self.status_label.cget("text")
                self.status_label.configure(text="✓ Copied to clipboard!")
                self.after(2000, lambda: self.status_label.configure(text=original))
        except ImportError:
            self.clipboard_clear()
            self.clipboard_append(self.full_output)
            
            original = self.status_label.cget("text")
            self.status_label.configure(text="✓ Copied to clipboard!")
            self.after(2000, lambda: self.status_label.configure(text=original))
    
    def _save_output(self):
        """Save output to a file."""
        if not self.full_output:
            return
        
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
                    f.write(self.full_output)
                
                original = self.status_label.cget("text")
                self.status_label.configure(text=f"✓ Saved to {os.path.basename(filepath)}")
                self.after(3000, lambda: self.status_label.configure(text=original))
            except Exception as e:
                self.status_label.configure(text=f"❌ Save failed: {str(e)}")
    
    def _open_fullscreen(self):
        """Open fullscreen viewer for output."""
        if not self.full_output:
            return
        
        from gui.components.fullscreen_viewer import FullscreenViewer
        FullscreenViewer(self.winfo_toplevel(), self.full_output, "Fabric Output")
    
    def get_output(self) -> str:
        """Get the current output text."""
        return self.full_output

