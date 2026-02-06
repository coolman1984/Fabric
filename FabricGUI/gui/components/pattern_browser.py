"""
Pattern Browser Component

A searchable tree view of all available Fabric patterns with favorites support.
"""

import customtkinter as ctk
from typing import Callable, Optional
import json
import os


class PatternBrowser(ctk.CTkFrame):
    """
    Sidebar component for browsing and selecting patterns.
    
    Features:
    - ⭐ Click star to add/remove favorites
    - Favorites pinned at top
    - Search filter
    - Double-click to run
    """
    
    def __init__(
        self,
        parent,
        on_pattern_selected: Callable[[str], None] = None,
        **kwargs
    ):
        super().__init__(parent, **kwargs)
        
        self.on_pattern_selected = on_pattern_selected
        self.all_patterns: list[str] = []
        self.favorites: set[str] = set()
        self.selected_pattern: Optional[str] = None
        self._favorites_file = os.path.join(
            os.path.expanduser("~"), ".config", "fabric-gui", "favorites.json"
        )
        
        self._load_favorites()
        self._setup_ui()
    
    def _load_favorites(self):
        """Load favorites from config file."""
        try:
            if os.path.exists(self._favorites_file):
                with open(self._favorites_file, "r") as f:
                    self.favorites = set(json.load(f))
        except Exception:
            self.favorites = set()
    
    def _save_favorites(self):
        """Save favorites to config file."""
        try:
            os.makedirs(os.path.dirname(self._favorites_file), exist_ok=True)
            with open(self._favorites_file, "w") as f:
                json.dump(list(self.favorites), f)
        except Exception:
            pass
    
    def _setup_ui(self):
        """Create the UI components."""
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        
        # Header with favorites toggle
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="ew")
        
        header = ctk.CTkLabel(
            header_frame,
            text="🎨 Patterns",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        header.pack(side="left")
        
        # Favorites count badge
        self.fav_badge = ctk.CTkLabel(
            header_frame,
            text="",
            font=ctk.CTkFont(size=11),
            text_color=("#f59e0b", "#fbbf24")
        )
        self.fav_badge.pack(side="right", padx=5)
        
        # Search entry
        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", self._on_search_change)
        
        self.search_entry = ctk.CTkEntry(
            self,
            placeholder_text="🔍 Search patterns...",
            textvariable=self.search_var,
            height=32
        )
        self.search_entry.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        
        # Pattern list frame with scrollbar
        self.list_frame = ctk.CTkScrollableFrame(
            self,
            label_text="",
            corner_radius=8
        )
        self.list_frame.grid(row=2, column=0, padx=5, pady=5, sticky="nsew")
        self.list_frame.grid_columnconfigure(1, weight=1)
        
        # Pattern count label
        self.count_label = ctk.CTkLabel(
            self,
            text="0 patterns",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        self.count_label.grid(row=3, column=0, padx=10, pady=5, sticky="w")
    
    def set_patterns(self, patterns: list[str]):
        """
        Set the list of available patterns.
        
        Args:
            patterns: List of pattern names
        """
        self.all_patterns = sorted(patterns)
        self._refresh_list()
    
    def _on_search_change(self, *args):
        """Handle search text changes."""
        self._refresh_list()
    
    def _refresh_list(self):
        """Refresh the pattern list based on search filter."""
        # Clear existing items
        for widget in self.list_frame.winfo_children():
            widget.destroy()
        
        search_text = self.search_var.get().lower().strip()
        
        # Filter patterns
        if search_text:
            filtered = [p for p in self.all_patterns if search_text in p.lower()]
        else:
            filtered = self.all_patterns
        
        # Separate favorites from rest
        fav_patterns = [p for p in filtered if p in self.favorites]
        other_patterns = [p for p in filtered if p not in self.favorites]
        
        row = 0
        
        # Update favorites badge
        fav_count = len(self.favorites)
        self.fav_badge.configure(text=f"⭐ {fav_count}" if fav_count > 0 else "")
        
        # Show favorites section if any
        if fav_patterns:
            fav_header = ctk.CTkLabel(
                self.list_frame,
                text="⭐ FAVORITES",
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=("#f59e0b", "#fbbf24"),
                anchor="w"
            )
            fav_header.grid(row=row, column=0, columnspan=2, padx=5, pady=(8, 4), sticky="w")
            row += 1
            
            for pattern in fav_patterns:
                self._create_pattern_item(pattern, row, is_favorite=True)
                row += 1
            
            # Separator
            sep = ctk.CTkFrame(self.list_frame, height=1, fg_color=("gray70", "gray40"))
            sep.grid(row=row, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
            row += 1
        
        # All patterns header (only if we have favorites)
        if fav_patterns and other_patterns:
            all_header = ctk.CTkLabel(
                self.list_frame,
                text="📁 ALL PATTERNS",
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color="gray",
                anchor="w"
            )
            all_header.grid(row=row, column=0, columnspan=2, padx=5, pady=(5, 4), sticky="w")
            row += 1
        
        # Show other patterns
        for pattern in other_patterns:
            self._create_pattern_item(pattern, row, is_favorite=False)
            row += 1
        
        # Update count
        total = len(fav_patterns) + len(other_patterns)
        self.count_label.configure(text=f"{total} pattern{'s' if total != 1 else ''}")
    
    def _create_pattern_item(self, pattern: str, row: int, is_favorite: bool):
        """Create a single pattern list item with star button."""
        # Star button (always visible)
        star_btn = ctk.CTkButton(
            self.list_frame,
            text="★" if is_favorite else "☆",
            width=28,
            height=28,
            font=ctk.CTkFont(size=14),
            fg_color="transparent",
            hover_color=("#fef3c7", "#78350f") if not is_favorite else ("#fef3c7", "#78350f"),
            text_color=("#f59e0b", "#fbbf24") if is_favorite else ("gray60", "gray50"),
            command=lambda p=pattern: self._toggle_favorite(p)
        )
        star_btn.grid(row=row, column=0, padx=(2, 0), pady=1, sticky="w")
        
        # Pattern name button
        is_selected = pattern == self.selected_pattern
        btn = ctk.CTkButton(
            self.list_frame,
            text=pattern,
            anchor="w",
            fg_color=("#3b82f6", "#1d4ed8") if is_selected else "transparent",
            hover_color=("gray80", "gray30"),
            text_color="white" if is_selected else ("gray20", "gray90"),
            font=ctk.CTkFont(size=12, weight="bold" if is_favorite else "normal"),
            height=28,
            command=lambda p=pattern: self._select_pattern(p)
        )
        btn.grid(row=row, column=1, padx=(0, 5), pady=1, sticky="ew")
    
    def _select_pattern(self, pattern: str):
        """Handle pattern selection."""
        self.selected_pattern = pattern
        self._refresh_list()
        
        if self.on_pattern_selected:
            self.on_pattern_selected(pattern)
    
    def _toggle_favorite(self, pattern: str):
        """Toggle pattern favorite status."""
        if pattern in self.favorites:
            self.favorites.remove(pattern)
        else:
            self.favorites.add(pattern)
        
        self._save_favorites()
        self._refresh_list()
    
    def get_selected_pattern(self) -> Optional[str]:
        """Get the currently selected pattern name."""
        return self.selected_pattern
    
    def get_favorites(self) -> list[str]:
        """Get list of favorite patterns."""
        return list(self.favorites)
