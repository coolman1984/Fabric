# 🧵 Fabric GUI

A beautiful, professional-grade desktop interface for the [Fabric](https://github.com/danielmiessler/fabric) AI framework.

![Fabric GUI](../docs/images/fabric-gui-preview.png)

## Features

- 🎨 **Pattern Browser** - Search and favorite 242+ patterns
- 🤖 **Multi-Vendor Support** - OpenAI, Anthropic, Gemini, Ollama, and 16+ more
- 📺 **YouTube Integration** - Extract transcripts directly
- 🌐 **URL Scraping** - Process web pages with a single click
- ⚡ **Streaming Output** - Watch AI responses in real-time
- 🎛️ **Full Control** - Temperature, Top-P, strategies, and more
- 🌙 **Dark Theme** - Easy on the eyes

## Prerequisites

1. **Python 3.10+** installed
2. **Fabric** installed and configured ([Installation Guide](../README.md#installation))
3. **Fabric server** running:

   ```bash
   fabric --serve
   ```

## Installation

```bash
# Navigate to the GUI directory
cd FabricGUI

# Install dependencies
pip install -r requirements.txt
```

## Usage

1. **Start the Fabric server** (in a separate terminal):

   ```bash
   fabric --serve
   ```

2. **Launch the GUI**:

   ```bash
   python main.py
   ```

3. **Use the GUI**:
   - Select a pattern from the sidebar
   - Choose your AI vendor and model
   - Enter text, paste a URL, or enter a YouTube link
   - Click **Run Pattern** or press `Ctrl+Enter`

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+Enter` | Run pattern |
| `Escape` | Stop execution |
| `Ctrl+L` | Clear output |

## Project Structure

```
FabricGUI/
├── main.py                 # Application entry point
├── requirements.txt        # Python dependencies
├── api/
│   ├── __init__.py
│   └── fabric_client.py    # REST API client
├── gui/
│   ├── __init__.py
│   ├── app.py              # Main application window
│   └── components/
│       ├── __init__.py
│       ├── pattern_browser.py
│       ├── model_selector.py
│       ├── input_panel.py
│       ├── output_panel.py
│       └── settings_panel.py
└── utils/
    ├── __init__.py
    └── clipboard.py        # Cross-platform clipboard
```

## Troubleshooting

### "Cannot connect to Fabric API"

Make sure the Fabric server is running:

```bash
fabric --serve
```

### "No patterns found"

Run Fabric setup to update patterns:

```bash
fabric --setup
```

### Missing dependencies

Install requirements:

```bash
pip install -r requirements.txt
```

## Contributing

This GUI is part of the Fabric project. See the main [CONTRIBUTING.md](../docs/CONTRIBUTING.md) for guidelines.

## License

MIT License - Same as the main Fabric project.
