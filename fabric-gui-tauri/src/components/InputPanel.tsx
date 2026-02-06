import { useAIStore, InputMode } from "../stores/ai";
import { cn } from "../lib/utils";
import { Type, Link as LinkIcon, Youtube } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

export function InputPanel() {
    const { inputMode, setInputMode, inputText, setInputText, includeTimestamps, setIncludeTimestamps } = useAIStore();

    return (
        <div className="flex flex-col h-full border border-border rounded-xl bg-card/30 overflow-hidden glass">
            <div className="flex items-center gap-1 p-1 bg-muted/30 border-b border-border">
                <div className="flex gap-1 p-1 bg-muted/50 rounded-lg w-fit mb-4">
                    {(["text", "url", "youtube"] as const).map((mode) => {
                        const Icon = { text: Type, url: LinkIcon, youtube: Youtube }[mode];
                        const isActive = inputMode === mode;
                        return (
                            <button
                                key={mode}
                                onClick={() => setInputMode(mode)}
                                className={cn(
                                    "relative flex items-center gap-2 px-4 py-1.5 rounded-md text-sm font-medium transition-colors",
                                    isActive ? "text-foreground" : "text-muted-foreground hover:text-foreground"
                                )}
                                title={`${mode.charAt(0).toUpperCase() + mode.slice(1)} Mode`}
                            >
                                {isActive && (
                                    <motion.div
                                        layoutId="activeTab"
                                        className="absolute inset-0 bg-background shadow-sm rounded-md border border-border"
                                        transition={{ type: "spring", bounce: 0.2, duration: 0.6 }}
                                    />
                                )}
                                <Icon className="w-4 h-4 relative z-10" />
                                <span className="relative z-10 capitalize">{mode}</span>
                            </button>
                        );
                    })}
                </div>
            </div>

            <div className="flex-1 bg-background rounded-xl border border-border shadow-inner overflow-hidden flex flex-col min-h-0">
                <AnimatePresence mode="wait">
                    <motion.div
                        key={inputMode}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -10 }}
                        transition={{ duration: 0.2 }}
                        className="flex-1 overflow-y-auto style-scrollbar p-0"
                    >
                        <div className="p-4">
                            {inputMode === "text" ? (
                                <textarea
                                    value={inputText}
                                    onChange={(e) => setInputText(e.target.value)}
                                    placeholder="Paste your content or instructions here..."
                                    className="w-full h-full bg-transparent resize-none border-none outline-none text-sm placeholder:text-muted-foreground/50 min-h-[140px]"
                                />
                            ) : inputMode === "url" ? (
                                <div className="space-y-4">
                                    <div className="space-y-2">
                                        <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                                            Enter URL to process:
                                        </label>
                                        <input
                                            type="url"
                                            value={inputText}
                                            onChange={(e) => setInputText(e.target.value)}
                                            placeholder="https://example.com/article"
                                            className="w-full bg-muted/30 border border-input rounded-lg px-4 py-2.5 text-sm outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
                                        />
                                    </div>
                                    <div className="flex items-start gap-2 p-3 bg-primary/5 rounded-lg border border-primary/10">
                                        <span className="text-primary mt-0.5">💡</span>
                                        <p className="text-xs text-muted-foreground leading-relaxed">
                                            Content will be automatically scraped using Jina AI Reader.
                                        </p>
                                    </div>
                                </div>
                            ) : (
                                <div className="space-y-6">
                                    <div className="space-y-2">
                                        <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                                            Enter YouTube URL:
                                        </label>
                                        <input
                                            type="url"
                                            value={inputText}
                                            onChange={(e) => setInputText(e.target.value)}
                                            placeholder="https://www.youtube.com/watch?v=..."
                                            className="w-full bg-muted/30 border border-input rounded-lg px-4 py-2.5 text-sm outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
                                        />
                                    </div>

                                    <div className="space-y-4">
                                        <label className="flex items-center gap-3 cursor-pointer group no-select">
                                            <div className="relative">
                                                <input
                                                    type="checkbox"
                                                    checked={includeTimestamps}
                                                    onChange={(e) => useAIStore.getState().setIncludeTimestamps(e.target.checked)}
                                                    className="sr-only"
                                                />
                                                <div className={cn(
                                                    "w-10 h-5 rounded-full transition-colors",
                                                    includeTimestamps ? "bg-primary" : "bg-muted-foreground/30"
                                                )} />
                                                <div className={cn(
                                                    "absolute left-1 top-1 w-3 h-3 bg-white rounded-full transition-transform",
                                                    includeTimestamps ? "translate-x-5" : "translate-x-0"
                                                )} />
                                            </div>
                                            <span className="text-sm font-medium group-hover:text-primary transition-colors">Include timestamps in transcript</span>
                                        </label>

                                        <div className="flex items-start gap-2 p-3 bg-primary/5 rounded-lg border border-primary/10">
                                            <span className="text-primary mt-0.5">💡</span>
                                            <p className="text-xs text-muted-foreground leading-relaxed">
                                                Video transcript will be automatically fetched. Try to use videos with closed captions for best results.
                                            </p>
                                        </div>
                                    </div>
                                </div>
                            )}
                        </div>
                    </motion.div>
                </AnimatePresence>
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
