import { useRef, useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Copy, Save, Maximize2, Check, Play } from "lucide-react";
import { useAIStore } from "../stores/ai";
import { cn } from "../lib/utils";

export function OutputPanel() {
    const { output, isStreaming, error } = useAIStore();
    const [copied, setCopied] = useState(false);
    const scrollRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (isStreaming && scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [output, isStreaming]);

    const copyToClipboard = () => {
        navigator.clipboard.writeText(output);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    return (
        <div className="flex flex-col h-full border border-border rounded-xl bg-card/30 overflow-hidden glass">
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
                        className="p-1.5 rounded-md hover:bg-accent text-muted-foreground hover:text-foreground transition-all"
                        title="Save to file"
                    >
                        <Save className="w-4 h-4" />
                    </button>
                    <button
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
    );
}
