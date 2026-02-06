import { useSettingsStore, Vendor } from "../stores/settings";
import { cn } from "../lib/utils";

const VENDORS: { id: Vendor; name: string }[] = [
    { id: "google", name: "Google Gemini" },
    { id: "openai", name: "OpenAI" },
    { id: "anthropic", name: "Anthropic" },
    { id: "ollama", name: "Ollama (Local)" },
];

const MODELS: Record<Vendor, string[]> = {
    google: [
        "gemini-3-pro-preview",
        "gemini-3-flash-preview",
        "gemini-2.0-flash-thinking-exp",
        "gemini-2.0-flash",
        "gemini-1.5-pro",
        "gemini-2.0-pro-exp-02-05",
    ],
    openai: ["gpt-4o", "gpt-4o-mini", "o1-preview", "o1-mini"],
    anthropic: ["claude-3-5-sonnet-latest", "claude-3-5-haiku-latest", "claude-3-opus-latest"],
    ollama: ["llama3", "mistral", "phi3", "custom"],
};

export function ModelSelector() {
    const { vendor, model, setVendor, setModel } = useSettingsStore();

    return (
        <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
                <label className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest">
                    Vendor
                </label>
                <select
                    value={vendor}
                    title="Select AI Vendor"
                    onChange={(e) => {
                        const newVendor = e.target.value as Vendor;
                        setVendor(newVendor);
                        setModel(MODELS[newVendor][0]);
                    }}
                    className={cn(
                        "bg-background border border-input rounded-md px-3 py-1 text-sm outline-none transition-all",
                        "focus:ring-2 focus:ring-primary/20 h-9"
                    )}
                >
                    {VENDORS.map((v) => (
                        <option key={v.id} value={v.id}>
                            {v.name}
                        </option>
                    ))}
                </select>
            </div>

            <div className="flex items-center gap-2">
                <label className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest">
                    Model
                </label>
                <select
                    value={model}
                    title="Select AI Model"
                    onChange={(e) => setModel(e.target.value)}
                    className={cn(
                        "bg-background border border-input rounded-md px-3 py-1 text-sm outline-none transition-all",
                        "focus:ring-2 focus:ring-primary/20 h-9 min-w-[160px]"
                    )}
                >
                    {MODELS[vendor].map((m) => (
                        <option key={m} value={m}>
                            {m}
                        </option>
                    ))}
                </select>
            </div>
        </div>
    );
}
