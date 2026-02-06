"""
Settings Panel Component

AI parameter controls including temperature, top-p, and advanced options.
"""

import customtkinter as ctk
from typing import Callable


class SettingsPanel(ctk.CTkFrame):
    """
    Panel for AI generation settings:
    - Temperature slider
    - Top-P slider
    - Thinking mode toggle
    """
    
    def __init__(
        self,
        parent,
        on_settings_changed: Callable[[], None] = None,
        **kwargs
    ):
        super().__init__(parent, **kwargs)
        
        self.on_settings_changed = on_settings_changed
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Create the UI components."""
        self.grid_columnconfigure((0, 1, 2), weight=1)
        
        # Temperature slider
        temp_frame = ctk.CTkFrame(self, fg_color="transparent")
        temp_frame.grid(row=0, column=0, padx=10, pady=5, sticky="ew")
        
        self.temp_label = ctk.CTkLabel(
            temp_frame,
            text="🌡️ Temperature: 0.7",
            font=ctk.CTkFont(size=11)
        )
        self.temp_label.pack(anchor="w")
        
        self.temp_slider = ctk.CTkSlider(
            temp_frame,
            from_=0,
            to=1,
            number_of_steps=20,
            command=self._on_temp_changed,
            width=180
        )
        self.temp_slider.set(0.7)
        self.temp_slider.pack(fill="x", pady=2)
        
        # Top-P slider
        topp_frame = ctk.CTkFrame(self, fg_color="transparent")
        topp_frame.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        
        self.topp_label = ctk.CTkLabel(
            topp_frame,
            text="🎯 Top-P: 0.9",
            font=ctk.CTkFont(size=11)
        )
        self.topp_label.pack(anchor="w")
        
        self.topp_slider = ctk.CTkSlider(
            topp_frame,
            from_=0,
            to=1,
            number_of_steps=20,
            command=self._on_topp_changed,
            width=180
        )
        self.topp_slider.set(0.9)
        self.topp_slider.pack(fill="x", pady=2)
        
        # Thinking mode toggle
        think_frame = ctk.CTkFrame(self, fg_color="transparent")
        think_frame.grid(row=0, column=2, padx=10, pady=5, sticky="ew")
        
        ctk.CTkLabel(
            think_frame,
            text="🧠 Reasoning",
            font=ctk.CTkFont(size=11)
        ).pack(anchor="w")
        
        self.thinking_var = ctk.BooleanVar(value=False)
        self.thinking_switch = ctk.CTkSwitch(
            think_frame,
            text="Enable deep thinking",
            variable=self.thinking_var,
            command=self._on_thinking_changed,
            font=ctk.CTkFont(size=10)
        )
        self.thinking_switch.pack(anchor="w", pady=2)
    
    def _on_temp_changed(self, value):
        """Handle temperature change."""
        self.temp_label.configure(text=f"🌡️ Temperature: {value:.2f}")
        self._notify_change()
    
    def _on_topp_changed(self, value):
        """Handle top-p change."""
        self.topp_label.configure(text=f"🎯 Top-P: {value:.2f}")
        self._notify_change()
    
    def _on_thinking_changed(self):
        """Handle thinking mode toggle."""
        self._notify_change()
    
    def _notify_change(self):
        """Notify parent of settings change."""
        if self.on_settings_changed:
            self.on_settings_changed()
    
    def get_temperature(self) -> float:
        """Get current temperature value."""
        return round(self.temp_slider.get(), 2)
    
    def get_top_p(self) -> float:
        """Get current top-p value."""
        return round(self.topp_slider.get(), 2)
    
    def get_thinking(self) -> int:
        """Get thinking mode (0 or token count)."""
        if self.thinking_var.get():
            return 8000  # Default thinking token budget
        return 0
    
    def set_temperature(self, value: float):
        """Set temperature value."""
        self.temp_slider.set(value)
        self.temp_label.configure(text=f"🌡️ Temperature: {value:.2f}")
    
    def set_top_p(self, value: float):
        """Set top-p value."""
        self.topp_slider.set(value)
        self.topp_label.configure(text=f"🎯 Top-P: {value:.2f}")
