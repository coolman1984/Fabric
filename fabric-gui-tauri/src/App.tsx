import { useState, useEffect } from "react";
import { invoke } from "@tauri-apps/api/core";
import { Settings, Play, Square, Moon, Sun } from "lucide-react";
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
  const { inputText, output, isStreaming, clearOutput, setStreaming, appendOutput, setError } = useAIStore();
  const { vendor, model, temperature, topP, getApiKey } = useSettingsStore();

  // Load patterns on mount
  useEffect(() => {
    loadPatterns();
  }, []);

  const loadPatterns = async () => {
    try {
      const patterns = await invoke<string[]>("list_patterns");
      setPatterns(patterns.map((name) => ({ name })));
    } catch (e) {
      console.error("Failed to load patterns:", e);
      // Fallback: set some demo patterns for development
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
    if (!selectedPattern || !inputText.trim()) return;

    clearOutput();
    setStreaming(true);

    try {
      const apiKey = getApiKey(vendor);
      await invoke("run_pattern", {
        pattern: selectedPattern,
        input: inputText,
        vendor,
        model,
        apiKey,
        temperature,
        topP,
      });
    } catch (e: any) {
      setError(e.message || "An error occurred");
    } finally {
      setStreaming(false);
    }
  };

  const toggleTheme = () => {
    setDarkMode(!darkMode);
    document.documentElement.classList.toggle("dark");
  };

  return (
    <div className="h-screen flex bg-background overflow-hidden">
      {/* Sidebar */}
      <aside className="w-72 border-r border-border flex flex-col">
        <PatternBrowser />
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col min-w-0">
        {/* Top Bar */}
        <header className="h-14 border-b border-border flex items-center justify-between px-4 glass">
          <ModelSelector />

          <div className="flex items-center gap-2">
            <button
              onClick={toggleTheme}
              className="p-2 rounded-lg hover:bg-accent transition-colors"
              title="Toggle theme"
            >
              {darkMode ? (
                <Sun className="w-5 h-5 text-muted-foreground" />
              ) : (
                <Moon className="w-5 h-5 text-muted-foreground" />
              )}
            </button>

            <button
              onClick={() => setSettingsOpen(true)}
              className="p-2 rounded-lg hover:bg-accent transition-colors"
              title="Settings"
            >
              <Settings className="w-5 h-5 text-muted-foreground" />
            </button>
          </div>
        </header>

        {/* Content Area */}
        <div className="flex-1 flex flex-col p-4 gap-4 overflow-hidden">
          {/* Input Panel */}
          <div className="h-1/3 min-h-[150px]">
            <InputPanel />
          </div>

          {/* Action Bar */}
          <div className="flex items-center gap-3">
            <button
              onClick={runPattern}
              disabled={!selectedPattern || !inputText.trim() || isStreaming}
              className={cn(
                "flex items-center gap-2 px-6 py-2.5 rounded-lg font-medium transition-all",
                "bg-primary text-primary-foreground hover:bg-primary/90",
                "disabled:opacity-50 disabled:cursor-not-allowed"
              )}
            >
              {isStreaming ? (
                <>
                  <Square className="w-4 h-4" />
                  Stop
                </>
              ) : (
                <>
                  <Play className="w-4 h-4" />
                  Run Pattern
                </>
              )}
            </button>

            {selectedPattern && (
              <span className="text-sm text-muted-foreground">
                Pattern: <span className="font-medium text-foreground">{selectedPattern}</span>
              </span>
            )}
          </div>

          {/* Output Panel */}
          <div className="flex-1 min-h-0">
            <OutputPanel />
          </div>
        </div>
      </main>

      {/* Settings Dialog */}
      <SettingsDialog open={settingsOpen} onClose={() => setSettingsOpen(false)} />
    </div>
  );
}

export default App;
