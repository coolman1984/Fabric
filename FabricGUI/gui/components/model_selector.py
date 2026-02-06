"""
Model Selector Component

Dropdown selectors for AI vendor, model, and prompting strategy.
Includes helpful strategy descriptions and tooltips.
"""

import customtkinter as ctk
from typing import Callable, Optional


# Prompting strategies with descriptions
STRATEGIES = {
    "None": {
        "description": "No special prompting strategy",
        "prompt": ""
    },
    "Chain of Thought (CoT)": {
        "description": "Think step-by-step before answering",
        "prompt": "Let's think through this step by step, then provide the final answer."
    },
    "Tree of Thought (ToT)": {
        "description": "Explore multiple reasoning paths",
        "prompt": "Consider multiple approaches, briefly evaluate each, then select the best solution."
    },
    "Self-Consistency": {
        "description": "Generate multiple answers and pick most common",
        "prompt": "Generate several independent answers, then determine the most consistent response."
    },
    "ReAct": {
        "description": "Reason and Act - interleave thinking with actions",
        "prompt": "Think about what to do, take an action, observe the result, and repeat until done."
    },
    "Expert Persona": {
        "description": "Respond as a domain expert",
        "prompt": "You are a world-class expert in this domain. Provide authoritative, detailed insights."
    },
    "Structured Output": {
        "description": "Format response with clear sections",
        "prompt": "Organize your response with clear headings, bullet points, and structured sections."
    },
    "Socratic Method": {
        "description": "Ask clarifying questions first",
        "prompt": "Before answering, consider what clarifying questions would help. Then provide a thorough response."
    },
}


class ModelSelector(ctk.CTkFrame):
    """
    Component for selecting AI vendor, model, and strategy.
    
    The model dropdown automatically filters based on selected vendor.
    Strategies include helpful descriptions.
    """
    
    def __init__(
        self,
        parent,
        on_selection_changed: Callable[[], None] = None,
        **kwargs
    ):
        super().__init__(parent, **kwargs)
        
        self.on_selection_changed = on_selection_changed
        
        # Data stores
        self.vendors_data: dict = {}  # vendor_name -> [model_names]
        self.all_models: list[str] = []
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Create the UI components."""
        self.grid_columnconfigure((0, 1, 2), weight=1)
        
        # Vendor selector
        vendor_frame = ctk.CTkFrame(self, fg_color="transparent")
        vendor_frame.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        
        ctk.CTkLabel(
            vendor_frame,
            text="Vendor",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        ).pack(anchor="w")
        
        self.vendor_var = ctk.StringVar(value="Select Vendor")
        self.vendor_dropdown = ctk.CTkComboBox(
            vendor_frame,
            variable=self.vendor_var,
            values=["Loading..."],
            command=self._on_vendor_changed,
            state="readonly",
            width=160
        )
        self.vendor_dropdown.pack(fill="x")
        
        # Model selector
        model_frame = ctk.CTkFrame(self, fg_color="transparent")
        model_frame.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        ctk.CTkLabel(
            model_frame,
            text="Model",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        ).pack(anchor="w")
        
        self.model_var = ctk.StringVar(value="Select Model")
        self.model_dropdown = ctk.CTkComboBox(
            model_frame,
            variable=self.model_var,
            values=["Loading..."],
            command=self._on_model_changed,
            state="readonly",
            width=200
        )
        self.model_dropdown.pack(fill="x")
        
        # Strategy selector with info
        strategy_frame = ctk.CTkFrame(self, fg_color="transparent")
        strategy_frame.grid(row=0, column=2, padx=5, pady=5, sticky="ew")
        
        strategy_label_frame = ctk.CTkFrame(strategy_frame, fg_color="transparent")
        strategy_label_frame.pack(fill="x")
        
        ctk.CTkLabel(
            strategy_label_frame,
            text="Strategy",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        ).pack(side="left")
        
        # Info button
        info_btn = ctk.CTkButton(
            strategy_label_frame,
            text="ℹ️",
            width=24,
            height=18,
            fg_color="transparent",
            hover_color=("gray80", "gray30"),
            command=self._show_strategy_info
        )
        info_btn.pack(side="left", padx=2)
        
        self.strategy_var = ctk.StringVar(value="None")
        self.strategy_dropdown = ctk.CTkComboBox(
            strategy_frame,
            variable=self.strategy_var,
            values=list(STRATEGIES.keys()),
            command=self._on_strategy_changed,
            state="readonly",
            width=180
        )
        self.strategy_dropdown.pack(fill="x")
        
        # Strategy description label
        self.strategy_desc = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(size=10),
            text_color="gray"
        )
        self.strategy_desc.grid(row=1, column=2, padx=5, sticky="w")
    
    def _show_strategy_info(self):
        """Show strategy information dialog."""
        info_window = ctk.CTkToplevel(self)
        info_window.title("📚 Prompting Strategies")
        info_window.geometry("500x400")
        info_window.transient(self.winfo_toplevel())
        
        # Content
        scroll = ctk.CTkScrollableFrame(info_window)
        scroll.pack(fill="both", expand=True, padx=15, pady=15)
        
        ctk.CTkLabel(
            scroll,
            text="🧠 Prompting Strategies",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(anchor="w", pady=(0, 10))
        
        ctk.CTkLabel(
            scroll,
            text="Strategies modify how the AI approaches your request.\nThey add special instructions to improve response quality.",
            font=ctk.CTkFont(size=12),
            text_color="gray",
            justify="left"
        ).pack(anchor="w", pady=(0, 15))
        
        for name, data in STRATEGIES.items():
            if name == "None":
                continue
                
            frame = ctk.CTkFrame(scroll, fg_color=("gray90", "gray20"))
            frame.pack(fill="x", pady=5)
            
            ctk.CTkLabel(
                frame,
                text=f"🔹 {name}",
                font=ctk.CTkFont(size=13, weight="bold")
            ).pack(anchor="w", padx=10, pady=(8, 2))
            
            ctk.CTkLabel(
                frame,
                text=data["description"],
                font=ctk.CTkFont(size=11),
                text_color="gray"
            ).pack(anchor="w", padx=10, pady=(0, 8))
        
        ctk.CTkButton(
            info_window,
            text="Close",
            command=info_window.destroy
        ).pack(pady=10)
    
    def set_models_data(self, data: dict):
        """
        Set available models data.
        
        Args:
            data: Dict with 'vendors' (dict of vendor_name -> [model_names])
        """
        self.vendors_data = data.get("vendors", {})
        
        # Flatten all models
        self.all_models = []
        for models in self.vendors_data.values():
            self.all_models.extend(models)
        
        # Update vendor dropdown
        vendor_names = sorted(self.vendors_data.keys())
        if vendor_names:
            self.vendor_dropdown.configure(values=vendor_names)
            
            # Auto-select first vendor (prefer Google Gemini for ease of use)
            preferred = ["Google Gemini", "OpenAI", "Anthropic"]
            selected = None
            for pref in preferred:
                if pref in vendor_names:
                    selected = pref
                    break
            
            if not selected:
                selected = vendor_names[0]
            
            self.vendor_var.set(selected)
            self._update_model_dropdown(selected)
        else:
            self.vendor_dropdown.configure(values=["No vendors"])
            self.model_dropdown.configure(values=["No models"])
    
    def _on_vendor_changed(self, vendor: str):
        """Handle vendor selection change."""
        self._update_model_dropdown(vendor)
        self._notify_change()
    
    def _update_model_dropdown(self, vendor: str):
        """Update model dropdown based on vendor."""
        models = self.vendors_data.get(vendor, [])
        
        if models:
            self.model_dropdown.configure(values=models)
            
            # Auto-select a good default model
            preferred_patterns = ["gpt-4o", "gpt-4", "claude-3", "claude-sonnet", "gemini"]
            selected = None
            
            for pattern in preferred_patterns:
                for model in models:
                    if pattern in model.lower():
                        selected = model
                        break
                if selected:
                    break
            
            if not selected:
                selected = models[0]
            
            self.model_var.set(selected)
        else:
            self.model_dropdown.configure(values=["No models"])
            self.model_var.set("No models")
    
    def _on_model_changed(self, model: str):
        """Handle model selection change."""
        self._notify_change()
    
    def _on_strategy_changed(self, strategy: str):
        """Handle strategy selection change."""
        # Update description
        desc = STRATEGIES.get(strategy, {}).get("description", "")
        self.strategy_desc.configure(text=desc if strategy != "None" else "")
        self._notify_change()
    
    def _notify_change(self):
        """Notify parent of selection change."""
        if self.on_selection_changed:
            self.on_selection_changed()
    
    def get_vendor(self) -> str:
        """Get selected vendor name."""
        return self.vendor_var.get()
    
    def get_model(self) -> str:
        """Get selected model name."""
        return self.model_var.get()
    
    def get_strategy(self) -> Optional[str]:
        """Get selected strategy name or None."""
        val = self.strategy_var.get()
        if val == "None" or not val:
            return ""
        return val
    
    def get_strategy_prompt(self) -> str:
        """Get the prompt text for the selected strategy."""
        strategy = self.strategy_var.get()
        return STRATEGIES.get(strategy, {}).get("prompt", "")
