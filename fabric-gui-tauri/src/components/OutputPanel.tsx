import { useRef, useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Copy, Save, Maximize2, Minimize2, Check, Play, X } from "lucide-react";
import { useAIStore } from "../stores/ai";
import { cn } from "../lib/utils";

export function OutputPanel() {
    const { output, isStreaming, error } = useAIStore();
    const [copied, setCopied] = useState(false);
    const [isFullscreen, setIsFullscreen] = useState(false);
    const scrollRef = useRef<HTMLDivElement>(null);
    const panelRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (isStreaming && scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [output, isStreaming]);

    // Handle Escape key to exit fullscreen
    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            if (e.key === "Escape" && isFullscreen) {
                setIsFullscreen(false);
            }
        };
        window.addEventListener("keydown", handleKeyDown);
        return () => window.removeEventListener("keydown", handleKeyDown);
    }, [isFullscreen]);

    const copyToClipboard = () => {
        navigator.clipboard.writeText(output);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    const saveToFile = async () => {
        try {
            // Import plugins dynamically to avoid SSR/Initial load issues if any
            const { save } = await import("@tauri-apps/plugin-dialog");
            const { writeTextFile } = await import("@tauri-apps/plugin-fs");

            const path = await save({
                filters: [{
                    name: "Markdown",
                    extensions: ["md"]
                }],
                defaultPath: `fabric-output-${Date.now()}.md`
            });

            if (path) {
                await writeTextFile(path, output);
                // Optionally show a success toast or change icon
                setCopied(true);
                setTimeout(() => setCopied(false), 2000);
            }
        } catch (err) {
            console.error("Failed to save file:", err);
        }
    };

    const toggleFullscreen = () => {
        setIsFullscreen(!isFullscreen);
    };

    return (
        <>
            {/* Fullscreen Overlay */}
            {isFullscreen && (
                <div className="fixed inset-0 z-50 bg-background/95 backdrop-blur-sm flex flex-col">
                    {/* Fullscreen Header */}
                    <div className="flex items-center justify-between px-6 py-4 border-b border-border bg-card/50">
                        <div className="flex items-center gap-3">
                            <div className={cn(
                                "w-3 h-3 rounded-full",
                                isStreaming ? "bg-amber-500 animate-pulse" : "bg-emerald-500"
                            )} />
                            <span className="text-lg font-semibold">
                                {isStreaming ? "AI is thinking..." : "Output"}
                            </span>
                            <span className="text-sm text-muted-foreground">
                                ({output.split(/\s+/).filter(Boolean).length} words)
                            </span>
                        </div>

                        <div className="flex items-center gap-3">
                            <button
                                onClick={copyToClipboard}
                                className="flex items-center gap-2 px-4 py-2 rounded-lg bg-accent hover:bg-accent/80 text-foreground transition-all"
                                title="Copy to clipboard"
                            >
                                {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                                <span className="text-sm font-medium">{copied ? "Copied!" : "Copy"}</span>
                            </button>
                            <button
                                onClick={saveToFile}
                                className="flex items-center gap-2 px-4 py-2 rounded-lg bg-accent hover:bg-accent/80 text-foreground transition-all"
                                title="Save to file"
                            >
                                <Save className="w-4 h-4" />
                                <span className="text-sm font-medium">Save</span>
                            </button>
                            <button
                                onClick={toggleFullscreen}
                                className="flex items-center gap-2 px-4 py-2 rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 transition-all"
                                title="Exit fullscreen (Esc)"
                            >
                                <Minimize2 className="w-4 h-4" />
                                <span className="text-sm font-medium">Exit</span>
                            </button>
                        </div>
                    </div>

                    {/* Fullscreen Content */}
                    <div className="flex-1 overflow-y-auto p-8">
                        {error ? (
                            <div className="bg-destructive/10 border border-destructive/20 text-destructive p-6 rounded-lg text-base max-w-4xl mx-auto">
                                <strong>Error:</strong> {error}
                            </div>
                        ) : output ? (
                            <article className="prose prose-lg dark:prose-invert max-w-4xl mx-auto">
                                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                                    {output}
                                </ReactMarkdown>
                            </article>
                        ) : (
                            <div className="h-full flex flex-col items-center justify-center text-muted-foreground gap-4">
                                <div className="w-20 h-20 rounded-full bg-muted/50 flex items-center justify-center">
                                    <Play className="w-10 h-10 opacity-20" />
                                </div>
                                <p className="text-lg italic">Run a pattern to see output here...</p>
                            </div>
                        )}
                    </div>
                </div>
            )}

            {/* Normal Panel */}
            <div
                ref={panelRef}
                className="flex flex-col h-full border border-border rounded-xl bg-card/30 overflow-hidden glass"
            >
                {/* Toolbar */}
                <div className="flex items-center justify-between px-3 py-2 bg-muted/30 border-b border-border">
                    <div className="flex items-center gap-2">
                        <div className={cn(
                            "w-2 h-2 rounded-full",
                            isStreaming ? "bg-amber-500 animate-pulse" : "bg-emerald-500"
                        )} />
                        <span className="text-xs font-medium text-muted-foreground">
                            {isStreaming ? "AI is thinking..." : "Output"}
                        </span>
                    </div>

                    <div className="flex items-center gap-2">
                        <button
                            onClick={copyToClipboard}
                            className="p-1.5 rounded-md hover:bg-accent text-muted-foreground hover:text-foreground transition-all"
                            title="Copy to clipboard"
                        >
                            {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                        </button>
                        <button
                            onClick={saveToFile}
                            className="p-1.5 rounded-md hover:bg-accent text-muted-foreground hover:text-foreground transition-all"
                            title="Save to file"
                        >
                            <Save className="w-4 h-4" />
                        </button>
                        <button
                            onClick={toggleFullscreen}
                            className="p-1.5 rounded-md hover:bg-accent text-muted-foreground hover:text-foreground transition-all"
                            title="Full screen view"
                        >
                            <Maximize2 className="w-4 h-4" />
                        </button>
                    </div>
                </div>

                {/* Content Area */}
                <div
                    ref={scrollRef}
                    className="flex-1 overflow-y-auto p-6 scroll-smooth"
                >
                    {error ? (
                        <div className="bg-destructive/10 border border-destructive/20 text-destructive p-4 rounded-lg text-sm">
                            <strong>Error:</strong> {error}
                        </div>
                    ) : output ? (
                        <article className="prose prose-sm dark:prose-invert max-w-none">
                            <ReactMarkdown remarkPlugins={[remarkGfm]}>
                                {output}
                            </ReactMarkdown>
                        </article>
                    ) : (
                        <div className="h-full flex flex-col items-center justify-center text-muted-foreground gap-4">
                            <div className="w-16 h-16 rounded-full bg-muted/50 flex items-center justify-center">
                                <Play className="w-8 h-8 opacity-20" />
                            </div>
                            <p className="text-sm italic">Run a pattern to see output here...</p>
                        </div>
                    )}
                </div>

                {/* Status Bar */}
                <div className="px-3 py-1.5 bg-muted/20 border-t border-border flex justify-between items-center text-[10px] text-muted-foreground uppercase tracking-widest font-bold">
                    <span>Markdown Rendered</span>
                    <span>{output.split(/\s+/).filter(Boolean).length} words</span>
                </div>
            </div>
        </>
    );
}
