"""
Fabric GUI - Main Application (Standalone Mode)

A self-contained GUI that works without needing `fabric --serve`.
Directly calls AI APIs using user-provided API keys.
"""

import customtkinter as ctk
import threading
import queue
from typing import Optional

from gui.components.pattern_browser import PatternBrowser
from gui.components.model_selector import ModelSelector
from gui.components.input_panel import InputPanel
from gui.components.output_panel import OutputPanel
from gui.components.settings_panel import SettingsPanel
from gui.components.settings_dialog import SettingsDialog
from api.direct_client import DirectAIClient
from utils.settings_manager import SettingsManager
from utils.pattern_loader import PatternLoader


class FabricApp(ctk.CTk):
    """
    Main Fabric GUI Application - Standalone Mode.
    
    Calls AI APIs directly without needing Fabric server.
    """
    
    def __init__(self):
        super().__init__()
        
        # Configure window
        self.title("🧵 Fabric GUI - AI Pattern Runner")
        self.geometry("1400x900")
        self.minsize(1000, 700)
        
        # Set light theme
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")
        
        # Initialize components
        self.settings_manager = SettingsManager()
        self.pattern_loader = PatternLoader()
        self.ai_client = DirectAIClient()
        
        # State
        self.is_running = False
        self.output_queue = queue.Queue()
        
        # Setup UI
        self._setup_ui()
        self._setup_menu()
        
        # Load data after UI is ready
        self.after(100, self._load_initial_data)
        
        # Start output queue processor
        self._process_output_queue()
    
    def _setup_ui(self):
        """Create the main UI layout."""
        # Configure grid - make everything resizable
        self.grid_columnconfigure(0, weight=0, minsize=250)  # Sidebar - fixed width
        self.grid_columnconfigure(1, weight=1)  # Main area - expands
        self.grid_rowconfigure(0, weight=1)  # Main content row expands
        self.grid_rowconfigure(1, weight=0)  # Status bar fixed
        
        # === SIDEBAR (Pattern Browser) ===
        self.pattern_browser = PatternBrowser(
            self,
            on_pattern_selected=self._on_pattern_selected,
            corner_radius=0,
            fg_color=("gray95", "gray15")
        )
        self.pattern_browser.grid(row=0, column=0, sticky="nsew")
        
        # === MAIN AREA ===
        main_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        main_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        main_frame.grid_columnconfigure(0, weight=1)
        # All rows expand proportionally
        main_frame.grid_rowconfigure(0, weight=0)  # Top bar
        main_frame.grid_rowconfigure(1, weight=0)  # Model selector
        main_frame.grid_rowconfigure(2, weight=0)  # Settings panel
        main_frame.grid_rowconfigure(3, weight=2)  # Input - 2 parts
        main_frame.grid_rowconfigure(4, weight=0)  # Action buttons
        main_frame.grid_rowconfigure(5, weight=3)  # Output - 3 parts
        
        # Settings button row
        top_bar = ctk.CTkFrame(main_frame, fg_color="transparent")
        top_bar.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        
        self.settings_btn = ctk.CTkButton(
            top_bar,
            text="⚙️ Settings & API Keys",
            command=self._open_settings,
            fg_color=("#6366f1", "#4f46e5"),
            hover_color=("#4f46e5", "#4338ca"),
            height=35
        )
        self.settings_btn.pack(side="right")
        
        # API Status indicator
        self.api_indicator = ctk.CTkLabel(
            top_bar,
            text="",
            font=ctk.CTkFont(size=11)
        )
        self.api_indicator.pack(side="left", padx=5)
        
        # Model/Strategy selector
        self.model_selector = ModelSelector(
            main_frame,
            on_selection_changed=self._on_settings_changed
        )
        self.model_selector.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        
        # Settings panel (temperature, etc.)
        self.settings_panel = SettingsPanel(
            main_frame,
            on_settings_changed=self._on_settings_changed
        )
        self.settings_panel.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        
        # Input panel
        self.input_panel = InputPanel(
            main_frame,
            corner_radius=10,
            fg_color=("gray90", "gray20")
        )
        self.input_panel.grid(row=3, column=0, sticky="nsew", pady=(0, 10))
        
        # Action buttons
        action_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        action_frame.grid(row=4, column=0, sticky="ew", pady=10)
        
        self.run_button = ctk.CTkButton(
            action_frame,
            text="▶️ Run Pattern",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=40,
            command=self._run_pattern,
            fg_color=("#2563eb", "#1d4ed8"),
            hover_color=("#1d4ed8", "#1e40af")
        )
        self.run_button.pack(side="left", padx=(0, 10))
        
        self.stop_button = ctk.CTkButton(
            action_frame,
            text="⏹️ Stop",
            font=ctk.CTkFont(size=14),
            height=40,
            width=100,
            command=self._stop_execution,
            fg_color=("#dc2626", "#b91c1c"),
            hover_color=("#b91c1c", "#991b1b"),
            state="disabled"
        )
        self.stop_button.pack(side="left", padx=(0, 10))
        
        # Selected pattern display
        self.selected_pattern_label = ctk.CTkLabel(
            action_frame,
            text="No pattern selected",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.selected_pattern_label.pack(side="left", padx=20)
        
        # Output panel
        self.output_panel = OutputPanel(
            main_frame,
            corner_radius=10,
            fg_color=("gray90", "gray20")
        )
        self.output_panel.grid(row=5, column=0, sticky="nsew")
        
        # === STATUS BAR ===
        status_frame = ctk.CTkFrame(self, height=30, corner_radius=0, fg_color=("gray85", "gray20"))
        status_frame.grid(row=1, column=0, columnspan=2, sticky="ew")
        
        self.status_label = ctk.CTkLabel(
            status_frame,
            text="Ready - Configure your API keys in Settings",
            font=ctk.CTkFont(size=11)
        )
        self.status_label.pack(side="left", padx=10, pady=5)
    
    def _setup_menu(self):
        """Setup keyboard shortcuts."""
        self.bind("<Control-Return>", lambda e: self._run_pattern())
        self.bind("<Escape>", lambda e: self._stop_execution())
        self.bind("<Control-l>", lambda e: self.output_panel.clear_output())
        self.bind("<Control-comma>", lambda e: self._open_settings())
    
    def _load_initial_data(self):
        """Load patterns and configure model selector."""
        # Load patterns from filesystem
        patterns = self.pattern_loader.list_patterns()
        self.pattern_browser.set_patterns(patterns)
        
        # Configure model selector with available vendors
        models_data = {
            "models": [],
            "vendors": DirectAIClient.MODELS
        }
        self.model_selector.set_models_data(models_data)
        
        # Check API key status
        self._update_api_status()
        
        # Update status
        pattern_count = len(patterns)
        patterns_dir = self.pattern_loader.get_patterns_dir()
        if patterns_dir:
            self.status_label.configure(
                text=f"✓ Loaded {pattern_count} patterns from {patterns_dir}"
            )
        else:
            self.status_label.configure(
                text="⚠️ Patterns directory not found. Make sure Fabric is installed."
            )
    
    def _update_api_status(self):
        """Update the API key status indicator."""
        settings = self.settings_manager.load()
        
        configured = []
        if settings.google_api_key:
            configured.append("Gemini")
        if settings.openai_api_key:
            configured.append("OpenAI")
        if settings.anthropic_api_key:
            configured.append("Claude")
        
        if configured:
            self.api_indicator.configure(
                text=f"🔑 API Keys: {', '.join(configured)}",
                text_color=("#059669", "#10b981")
            )
        else:
            self.api_indicator.configure(
                text="⚠️ No API keys configured - click Settings",
                text_color=("#dc2626", "#ef4444")
            )
    
    def _open_settings(self):
        """Open settings dialog."""
        SettingsDialog(
            self,
            self.settings_manager,
            on_save=self._update_api_status
        )
    
    def _on_pattern_selected(self, pattern: str):
        """Handle pattern selection."""
        self.selected_pattern_label.configure(
            text=f"Pattern: {pattern}",
            text_color=("gray20", "gray90")
        )
    
    def _on_settings_changed(self):
        """Handle settings change."""
        pass
    
    def _run_pattern(self):
        """Execute the selected pattern."""
        pattern = self.pattern_browser.get_selected_pattern()
        input_mode = self.input_panel.get_mode()
        raw_input = self.input_panel.get_input_text()
        
        # Validation
        if not pattern:
            self.output_panel.set_error("Please select a pattern first.")
            return
        
        if not raw_input.strip():
            self.output_panel.set_error("Please enter some input text.")
            return
        
        # Get settings
        vendor = self.model_selector.get_vendor()
        model = self.model_selector.get_model()
        temperature = self.settings_panel.get_temperature()
        top_p = self.settings_panel.get_top_p()
        strategy_prompt = self.model_selector.get_strategy_prompt()
        
        # Check API key
        api_key = self.settings_manager.get_api_key(vendor)
        if not api_key and vendor != "Ollama (Local)":
            self.output_panel.set_error(
                f"No API key configured for {vendor}.\n\n"
                "Click the '⚙️ Settings & API Keys' button to add your API key."
            )
            return
        
        # Get pattern content
        system_prompt = self.pattern_loader.get_pattern_content(pattern)
        if not system_prompt:
            self.output_panel.set_error(f"Could not load pattern: {pattern}")
            return
        
        # Add strategy if selected
        if strategy_prompt:
            system_prompt = f"{system_prompt}\n\n---\nSTRATEGY: {strategy_prompt}"
        
        # Clear output and show loading
        self.output_panel.clear_output()
        self.output_panel.set_loading(f"Running {pattern} with {model}...")
        
        # Update UI state
        self.is_running = True
        self.run_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        
        def execute():
            input_text = raw_input
            
            try:
                # Handle YouTube mode - extract transcript
                if input_mode == "youtube":
                    self.output_queue.put(("status", "🎬 Fetching YouTube transcript..."))
                    
                    from utils.youtube import get_transcript, format_transcript_for_ai
                    transcript, error = get_transcript(raw_input)
                    
                    if error:
                        self.output_queue.put(("error", f"YouTube Error: {error}"))
                        return
                    
                    input_text = format_transcript_for_ai(transcript, raw_input)
                    self.output_queue.put(("status", f"📝 Transcript: {len(transcript):,} chars. Sending to {model}..."))
                
                # Handle URL mode - scrape content
                elif input_mode == "url":
                    self.output_queue.put(("status", "🌐 Scraping URL content..."))
                    
                    import httpx
                    # Use Jina AI reader for clean markdown extraction
                    jina_url = f"https://r.jina.ai/{raw_input}"
                    
                    with httpx.Client(timeout=30.0) as client:
                        response = client.get(jina_url)
                        response.raise_for_status()
                        input_text = response.text
                    
                    self.output_queue.put(("status", f"📄 Content: {len(input_text):,} chars. Sending to {model}..."))
                
                self.output_queue.put(("clear", None))
                
                for chunk in self.ai_client.chat(
                    vendor=vendor,
                    model=model,
                    api_key=api_key,
                    system_prompt=system_prompt,
                    user_input=input_text,
                    temperature=temperature,
                    top_p=top_p
                ):
                    if not self.is_running:
                        break
                    self.output_queue.put(("append", chunk))
                
                self.output_queue.put(("done", None))
                
            except Exception as e:
                error_msg = str(e)
                if "401" in error_msg or "403" in error_msg:
                    error_msg = f"Authentication failed. Please check your {vendor} API key in Settings."
                elif "404" in error_msg:
                    error_msg = f"Model '{model}' not found. Please select a different model."
                elif "connection" in error_msg.lower():
                    error_msg = f"Could not connect to {vendor}. Please check your internet connection."
                
                self.output_queue.put(("error", error_msg))
            finally:
                self.output_queue.put(("finished", None))
        
        # Run in background
        threading.Thread(target=execute, daemon=True).start()
    
    def _stop_execution(self):
        """Stop the current execution."""
        self.is_running = False
        self.run_button.configure(state="normal")
        self.stop_button.configure(state="disabled")
        self.output_panel.set_complete()
    
    def _process_output_queue(self):
        """Process queued output updates on the main thread."""
        try:
            while True:
                msg_type, content = self.output_queue.get_nowait()
                
                if msg_type == "append":
                    self.output_panel.append_text(content)
                elif msg_type == "clear":
                    self.output_panel.clear_output()
                elif msg_type == "error":
                    self.output_panel.set_error(content)
                elif msg_type == "status":
                    self.output_panel.set_loading(content)
                elif msg_type == "done":
                    self.output_panel.set_complete()
                elif msg_type == "finished":
                    self.is_running = False
                    self.run_button.configure(state="normal")
                    self.stop_button.configure(state="disabled")
                    
        except queue.Empty:
            pass
        
        # Schedule next check
        self.after(50, self._process_output_queue)


def main():
    """Application entry point."""
    app = FabricApp()
    app.mainloop()


if __name__ == "__main__":
    main()
