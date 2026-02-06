import { useState, useEffect } from "react";
import { invoke } from "@tauri-apps/api/core";
import { listen } from "@tauri-apps/api/event";
import { Settings, Play, Square, Moon, Sun, Copy } from "lucide-react";
import { PatternBrowser } from "./components/PatternBrowser";
import { ModelSelector } from "./components/ModelSelector";
import { InputPanel } from "./components/InputPanel";
import { OutputPanel } from "./components/OutputPanel";
import { SettingsDialog } from "./components/SettingsDialog";
import { usePatternStore } from "./stores/patterns";
import { useAIStore } from "./stores/ai";
import { useSettingsStore } from "./stores/settings";
import { cn } from "./lib/utils";

function App() {
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [darkMode, setDarkMode] = useState(true);

  const { selectedPattern, setPatterns } = usePatternStore();
  const {
    inputText,
    inputMode,
    includeTimestamps,
    output,
    isStreaming,
    clearOutput,
    setStreaming,
    appendOutput,
    setError
  } = useAIStore();
  const { vendor, model, temperature, topP, thinkingLevel, getApiKey } = useSettingsStore();

  // Load patterns on mount
  useEffect(() => {
    loadPatterns();

    // Set up AI chunk listener
    const unlistenPromise = listen("ai-chunk", (event: any) => {
      appendOutput(event.payload.chunk);
    });

    return () => {
      unlistenPromise.then((unlisten) => unlisten());
    };
  }, []);

  const loadPatterns = async () => {
    try {
      const patterns = await invoke<string[]>("list_patterns");
      setPatterns(patterns.map((name) => ({ name })));
    } catch (e: any) {
      console.error("Failed to load patterns:", e);
      setError("Failed to load patterns from local storage. Please check your Fabric installation.");
      // Fallback: set some demo patterns for development only if no patterns found
      setPatterns([
        { name: "summarize" },
        { name: "extract_wisdom" },
        { name: "improve_writing" },
        { name: "analyze_paper" },
        { name: "create_summary" },
      ]);
    }
  };

  const runPattern = async () => {
    if (!selectedPattern || (!inputText && inputMode !== "text")) {
      setError("Please select a pattern and provide input.");
      return;
    }

    clearOutput();
    setStreaming(true);
    let finalInput = inputText;

    try {
      const apiKey = getApiKey(vendor);
      if (!apiKey) {
        throw new Error(`API key for ${vendor} not found. Please check Settings.`);
      }

      // Pre-processing for URL and YouTube modes
      if (inputMode === "youtube") {
        appendOutput("> 🎬 Fetching YouTube transcript...\n\n");
        const response = await invoke<string>("get_youtube_transcript", {
          url: inputText,
          includeTimestamps: includeTimestamps
        });
        const data = JSON.parse(response);
        if (data.error) throw new Error(data.error);
        finalInput = data.transcript;
        clearOutput();
        appendOutput(`> 📝 Video: ${data.video_id}\n\n`);
      } else if (inputMode === "url") {
        appendOutput("> 🌐 Scraping URL content...\n\n");
        const jinaUrl = `https://r.jina.ai/${inputText}`;
        const response = await fetch(jinaUrl);
        if (!response.ok) throw new Error("Failed to scrape URL");
        finalInput = await response.text();
        clearOutput();
        appendOutput(`> 📄 Content from ${inputText}\n\n`);
      }

      const request = {
        vendor: vendor,
        model: model,
        api_key: apiKey,
        system_prompt: selectedPattern,
        user_input: finalInput,
        temperature: temperature,
        top_p: topP,
        thinking_level: thinkingLevel,
      };

      await invoke("run_pattern", { request });
    } catch (err: any) {
      setError(err.message || String(err));
    } finally {
      setStreaming(false);
    }
  };

  const toggleTheme = () => {
    setDarkMode(!darkMode);
    document.documentElement.classList.toggle("dark");
  };

  return (
    <div className="h-screen flex flex-col bg-background overflow-hidden text-foreground">
      {/* Top Professional Header & Settings Bar */}
      <header className="h-20 border-b border-border bg-card/50 backdrop-blur-md flex flex-col shrink-0">
        <div className="flex-1 flex items-center justify-between px-6 border-b border-border/50">
          <div className="flex items-center gap-4">
            <h1 className="text-lg font-bold tracking-tight text-primary flex items-center gap-2">
              <span className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center">
                <Settings className="w-5 h-5" />
              </span>
              Fabric GUI
            </h1>
            <div className="h-6 w-[1px] bg-border mx-2" />
            <ModelSelector />
          </div>

          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 bg-accent/50 p-1 rounded-lg border border-border">
              <button
                onClick={toggleTheme}
                className="p-1.5 rounded-md hover:bg-background transition-colors"
                title="Toggle theme"
              >
                {darkMode ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
              </button>
              <button
                onClick={() => setSettingsOpen(true)}
                className="p-1.5 rounded-md hover:bg-background transition-colors"
                title="API Keys & Settings"
              >
                <Settings className="w-4 h-4" />
              </button>
            </div>

            <button
              disabled={!selectedPattern || !inputText.trim() || isStreaming}
              onClick={runPattern}
              className={cn(
                "flex items-center gap-2 px-6 h-10 rounded-lg font-semibold transition-all shadow-lg",
                "bg-primary text-primary-foreground hover:shadow-primary/20",
                "disabled:opacity-50 disabled:grayscale"
              )}
            >
              {isStreaming ? (
                <><Square className="w-4 h-4 fill-current" /> Stop</>
              ) : (
                <><Play className="w-4 h-4 fill-current" /> Run Pattern</>
              )}
            </button>
          </div>
        </div>

        {/* Advanced Model Controls Sub-header */}
        <div className="h-10 bg-muted/30 flex items-center px-6 gap-8 overflow-x-auto no-scrollbar">
          <div className="flex items-center gap-6 text-sm">
            <div className="flex items-center gap-4">
              <span className="text-muted-foreground font-medium">Temp: {temperature}</span>
              <input
                type="range" min="0" max="2" step="0.1"
                title="Adjust temperature"
                value={temperature}
                onChange={(e) => useSettingsStore.getState().setTemperature(parseFloat(e.target.value))}
                className="w-24 h-1.5 bg-border rounded-lg appearance-none cursor-pointer accent-primary"
              />
            </div>
            <div className="flex items-center gap-4 border-l border-border pl-6">
              <label className="flex items-center gap-2 cursor-pointer no-select">
                <input
                  type="checkbox"
                  checked={useSettingsStore.getState().thinkingLevel > 0}
                  onChange={(e) => useSettingsStore.getState().setThinkingLevel(e.target.checked ? 1 : 0)}
                  className="accent-primary w-4 h-4"
                />
                <span className="font-medium">Enable Reasoning</span>
              </label>
            </div>
          </div>

          <div className="ml-auto text-sm">
            {selectedPattern ? (
              <span className="text-primary font-medium">Selected: {selectedPattern}</span>
            ) : (
              <span className="text-destructive font-medium italic">No pattern selected</span>
            )}
          </div>
        </div>
      </header>

      {/* Main Dashboard Body */}
      <div className="flex-1 flex overflow-hidden">
        {/* Sidebar Browser */}
        <aside className="w-80 border-r border-border bg-card/30 flex flex-col shrink-0">
          <PatternBrowser />
        </aside>

        {/* Content Area */}
        <main className="flex-1 flex flex-col min-w-0 bg-accent/5">
          <div className="flex-1 flex flex-col p-6 gap-6 overflow-hidden">
            {/* Input Section */}
            <div className="flex flex-col gap-3 shrink-0">
              <div className="flex items-center justify-between">
                <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">Input</h2>
                <div className="flex gap-2">
                  {/* Placeholder for source tabs */}
                  <span className="text-xs bg-primary/10 text-primary px-2 py-0.5 rounded border border-primary/20">Text Mode</span>
                </div>
              </div>
              <div className="h-48">
                <InputPanel />
              </div>
            </div>

            {/* Output Section */}
            <div className="flex-1 flex flex-col gap-3 min-h-0">
              <div className="flex items-center justify-between">
                <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">Output</h2>
                <div className="flex gap-4">
                  <button
                    onClick={clearOutput}
                    className="text-xs text-muted-foreground hover:text-primary transition-colors flex items-center gap-1"
                  >
                    <Square className="w-3 h-3" /> Clear
                  </button>
                  <button
                    onClick={() => {
                      navigator.clipboard.writeText(output);
                      // Add some toast or feedback here if needed
                    }}
                    className="text-xs text-muted-foreground hover:text-primary transition-colors flex items-center gap-1"
                  >
                    <Copy className="w-3 h-3" /> Copy
                  </button>
                </div>
              </div>
              <div className="flex-1 border border-border rounded-xl bg-card shadow-sm overflow-hidden">
                <OutputPanel />
              </div>
            </div>
          </div>
        </main>
      </div>

      {/* Settings Dialog */}
      <SettingsDialog open={settingsOpen} onClose={() => setSettingsOpen(false)} />
    </div>
  );
}

export default App;
