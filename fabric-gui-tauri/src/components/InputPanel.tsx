import { FileText, Link, Youtube } from "lucide-react";
import { useAIStore } from "../stores/ai";
import { cn } from "../lib/utils";

export function InputPanel() {
    const { inputMode, setInputMode, inputText, setInputText, includeTimestamps, setIncludeTimestamps } = useAIStore();

    const tabs = [
        { id: "text", label: "Text", icon: FileText },
        { id: "url", label: "URL", icon: Link },
        { id: "youtube", label: "YouTube", icon: Youtube },
    ] as const;

    return (
        <div className="flex flex-col h-full border border-border rounded-xl bg-card/30 overflow-hidden glass">
            <div className="flex items-center gap-1 p-1 bg-muted/30 border-b border-border">
                {tabs.map((tab) => {
                    const Icon = tab.icon;
                    const isActive = inputMode === tab.id;
                    return (
                        <button
                            key={tab.id}
                            title={`Switch to ${tab.label} mode`}
                            onClick={() => setInputMode(tab.id)}
                            className={cn(
                                "flex items-center gap-2 px-4 py-1.5 rounded-lg text-sm transition-all",
                                isActive
                                    ? "bg-background shadow-sm text-foreground font-medium"
                                    : "text-muted-foreground hover:bg-muted/50 hover:text-foreground"
                            )}
                        >
                            <Icon className="w-4 h-4" />
                            {tab.label}
                        </button>
                    );
                })}
            </div>

            <div className="flex-1 p-3">
                {inputMode === "text" ? (
                    <textarea
                        value={inputText}
                        onChange={(e) => setInputText(e.target.value)}
                        placeholder="Enter text to analyze..."
                        title="Input text area"
                        className="w-full h-full bg-transparent resize-none outline-none text-sm placeholder:text-muted-foreground"
                    />
                ) : (
                    <div className="flex flex-col gap-4 mt-2">
                        <div>
                            <label className="text-xs font-medium text-muted-foreground block mb-2">
                                {inputMode === "url" ? "Enter URL to scrape:" : "Enter YouTube URL:"}
                            </label>
                            <input
                                type="text"
                                value={inputText}
                                onChange={(e) => setInputText(e.target.value)}
                                placeholder={
                                    inputMode === "url"
                                        ? "https://example.com/article"
                                        : "https://youtube.com/watch?v=..."
                                }
                                title={inputMode === "url" ? "Enter URL" : "Enter YouTube URL"}
                                className={cn(
                                    "w-full bg-background border border-input rounded-lg py-2.5 px-4 text-sm outline-none transition-all",
                                    "focus:ring-2 focus:ring-primary/20 focus:border-primary"
                                )}
                            />
                        </div>

                        {inputMode === "youtube" && (
                            <label className="flex items-center gap-2 cursor-pointer no-select mt-1 group">
                                <input
                                    type="checkbox"
                                    checked={includeTimestamps}
                                    onChange={(e) => setIncludeTimestamps(e.target.checked)}
                                    className="accent-primary w-4 h-4 rounded"
                                />
                                <span className="text-sm font-medium text-muted-foreground group-hover:text-foreground transition-colors">
                                    Include timestamps in transcript
                                </span>
                            </label>
                        )}

                        <p className="text-xs text-muted-foreground italic">
                            {inputMode === "url"
                                ? "💡 Content will be extracted and converted to markdown."
                                : "💡 Video transcript will be automatically fetched."}
                        </p>
                    </div>
                )}
            </div>

            <div className="px-3 py-1.5 bg-muted/20 border-t border-border flex justify-between items-center">
                <span className="text-[10px] text-muted-foreground uppercase tracking-widest font-bold">
                    Input Source: {inputMode}
                </span>
                <span className="text-[10px] text-muted-foreground">
                    {inputText.length.toLocaleString()} characters
                </span>
            </div>
        </div>
    );
}
