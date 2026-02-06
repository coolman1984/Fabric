import { useSettingsStore, Vendor } from "../stores/settings";
import { cn } from "../lib/utils";
import { Globe, Cpu, Zap, Cloud } from "lucide-react";

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

    const VendorIcon = {
        google: Globe,
        openai: Cloud,
        anthropic: Zap,
        ollama: Cpu,
    }[vendor] || Cpu;

    return (
        <div className="flex flex-wrap items-center gap-6">
            <div className="flex items-center gap-3">
                <div className="flex flex-col gap-1.5">
                    <label className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest pl-1">
                        AI Provider
                    </label>
                    <div className="relative group">
                        <div className="absolute left-3 top-2.5 text-primary pointer-events-none group-focus-within:scale-110 transition-transform">
                            <VendorIcon className="w-4 h-4" />
                        </div>
                        <select
                            value={vendor}
                            title="Select AI Vendor"
                            onChange={(e) => {
                                const newVendor = e.target.value as Vendor;
                                setVendor(newVendor);
                                setModel(MODELS[newVendor][0]);
                            }}
                            className={cn(
                                "bg-background border border-input rounded-lg pl-9 pr-8 h-10 text-sm outline-none transition-all appearance-none",
                                "focus:ring-2 focus:ring-primary/20 focus:border-primary min-w-[160px] cursor-pointer"
                            )}
                        >
                            {VENDORS.map((v) => (
                                <option key={v.id} value={v.id}>
                                    {v.name}
                                </option>
                            ))}
                        </select>
                        <div className="absolute right-3 top-3.5 w-0 h-0 border-l-[4px] border-l-transparent border-r-[4px] border-r-transparent border-t-[5px] border-t-muted-foreground pointer-events-none" />
                    </div>
                </div>
            </div>

            <div className="flex items-center gap-3">
                <div className="flex flex-col gap-1.5">
                    <label className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest pl-1">
                        Active Model
                    </label>
                    <div className="relative group">
                        <select
                            value={model}
                            title="Select AI Model"
                            onChange={(e) => setModel(e.target.value)}
                            className={cn(
                                "bg-background border border-input rounded-lg px-4 h-10 text-sm outline-none transition-all appearance-none pr-8",
                                "focus:ring-2 focus:ring-primary/20 focus:border-primary min-w-[200px] cursor-pointer"
                            )}
                        >
                            {MODELS[vendor].map((m) => (
                                <option key={m} value={m}>
                                    {m}
                                </option>
                            ))}
                        </select>
                        <div className="absolute right-3 top-3.5 w-0 h-0 border-l-[4px] border-l-transparent border-r-[4px] border-r-transparent border-t-[5px] border-t-muted-foreground pointer-events-none" />
                    </div>
                </div>
            </div>
        </div>
    );
}
