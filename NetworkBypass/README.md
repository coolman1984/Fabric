# Fabric Network Bypass

Automatically fixes YouTube rate limiting issues for Fabric GUI.

## Quick Start

Just double-click `RUN_ME.bat` or run:

```powershell
python bypass_gui.py
```

The tool will automatically:

1. Fetch free proxies from multiple sources
2. Test them for YouTube access
3. Configure the best working one
4. Save settings for Fabric GUI

## Files

- `bypass_gui.py` - GUI launcher (recommended)
- `auto_bypass.py` - Command-line version
- `bypass_config.json` - Saved configuration (auto-generated)

## Command Line Usage

```powershell
python auto_bypass.py          # Full auto-configure
python auto_bypass.py --test   # Quick test current config
python auto_bypass.py --reset  # Reset to direct connection
```

## How It Works

1. **Fetches proxies** from 5+ public proxy lists
2. **Tests in parallel** - checks 100 proxies simultaneously
3. **Verifies YouTube access** - ensures proxy works with YouTube
4. **Auto-configures** - saves the best proxy for Fabric GUI
