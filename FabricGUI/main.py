#!/usr/bin/env python3
"""
Fabric GUI - Professional Interface for Fabric AI Framework

A beautiful, user-friendly desktop application for running Fabric patterns
without needing to use the command line.

Requirements:
    - Python 3.10+
    - Fabric server running (fabric --serve)
    - Dependencies from requirements.txt

Usage:
    python main.py
"""

import sys

# Check Python version
if sys.version_info < (3, 10):
    print("Error: Fabric GUI requires Python 3.10 or higher.")
    print(f"You are running Python {sys.version_info.major}.{sys.version_info.minor}")
    sys.exit(1)

# Check for required packages
try:
    import customtkinter
except ImportError:
    print("Error: CustomTkinter not found.")
    print("Please install dependencies: pip install -r requirements.txt")
    sys.exit(1)

try:
    import httpx
except ImportError:
    print("Error: httpx not found.")
    print("Please install dependencies: pip install -r requirements.txt")
    sys.exit(1)


def main():
    """Launch the Fabric GUI application."""
    try:
        from gui.app import FabricApp
        
        print("🧵 Starting Fabric GUI...")
        print("💡 Configure your API keys in Settings to get started")
        print()
        
        app = FabricApp()
        app.mainloop()
        
    except Exception as e:
        print(f"Error starting Fabric GUI: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
