import { useState } from "react";
import { X, Key, Shield, Info, Cpu } from "lucide-react";
import { useSettingsStore, Vendor } from "../stores/settings";
import { cn } from "../lib/utils";

interface SettingsDialogProps {
    open: boolean;
    onClose: () => void;
}

export function SettingsDialog({ open, onClose }: SettingsDialogProps) {
    const {
        googleApiKey, openaiApiKey, anthropicApiKey, ollamaUrl,
        setApiKey, setTheme, theme
    } = useSettingsStore();

    if (!open) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            {/* Backdrop */}
            <div
                className="absolute inset-0 bg-black/60 backdrop-blur-sm animate-fade-in"
                onClick={onClose}
            />

            {/* Dialog */}
            <div className="relative w-full max-w-md bg-background border border-border shadow-2xl rounded-2xl flex flex-col animate-slide-in overflow-hidden">
                {/* Header */}
                <div className="flex items-center justify-between px-6 py-4 border-b border-border bg-muted/30">
                    <div className="flex items-center gap-2">
                        <Shield className="w-5 h-5 text-primary" />
                        <h2 className="text-lg font-semibold font-sans">Settings & API Keys</h2>
                    </div>
                    <button
                        onClick={onClose}
                        title="Close Settings"
                        className="p-2 rounded-full hover:bg-accent transition-colors"
                    >
                        <X className="w-5 h-5" />
                    </button>
                </div>

                {/* Content */}
                <div className="flex-1 overflow-y-auto p-6 space-y-8">
                    {/* API Keys */}
                    <section className="space-y-4">
                        <h3 className="text-xs font-bold text-muted-foreground uppercase tracking-widest flex items-center gap-2">
                            <Key className="w-3.5 h-3.5" />
                            API Credentials
                        </h3>

                        <div className="space-y-4">
                            <ApiKeyInput
                                label="Google Gemini API Key"
                                value={googleApiKey}
                                onChange={(val) => setApiKey("google", val)}
                                placeholder="AIzaSy..."
                            />
                            <ApiKeyInput
                                label="OpenAI API Key"
                                value={openaiApiKey}
                                onChange={(val) => setApiKey("openai", val)}
                                placeholder="sk-..."
                            />
                            <ApiKeyInput
                                label="Anthropic API Key"
                                value={anthropicApiKey}
                                onChange={(val) => setApiKey("anthropic", val)}
                                placeholder="sk-ant-..."
                            />
                            <ApiKeyInput
                                label="Ollama Server URL"
                                value={ollamaUrl}
                                onChange={(val) => useSettingsStore.setState({ ollamaUrl: val })}
                                placeholder="http://localhost:11434"
                                isKey={false}
                            />
                        </div>
                    </section>

                    {/* Preferences */}
                    <section className="space-y-4">
                        <h3 className="text-xs font-bold text-muted-foreground uppercase tracking-widest flex items-center gap-2">
                            <Cpu className="w-3.5 h-3.5" />
                            Preferences
                        </h3>

                        <div className="flex items-center justify-between">
                            <span className="text-sm font-medium">Appearance</span>
                            <div className="flex bg-muted rounded-lg p-1">
                                {(["light", "dark", "system"] as const).map((t) => (
                                    <button
                                        key={t}
                                        onClick={() => setTheme(t)}
                                        className={cn(
                                            "px-3 py-1 text-xs rounded-md transition-all capitalize",
                                            theme === t ? "bg-background shadow-sm font-medium" : "text-muted-foreground hover:text-foreground"
                                        )}
                                    >
                                        {t}
                                    </button>
                                ))}
                            </div>
                        </div>
                    </section>

                    {/* Info */}
                    <div className="p-4 bg-muted/50 rounded-xl flex gap-3 border border-border">
                        <Info className="w-5 h-5 text-primary flex-shrink-0 mt-0.5" />
                        <p className="text-sm text-muted-foreground leading-relaxed">
                            API keys are stored locally on your machine in the Tauri application storage. They are never sent to any server except the respective AI provider.
                        </p>
                    </div>
                </div>

                {/* Footer */}
                <div className="p-6 border-t border-border flex justify-end">
                    <button
                        onClick={onClose}
                        className="px-6 py-2 bg-primary text-primary-foreground rounded-lg font-medium hover:bg-primary/90 transition-all shadow-lg shadow-primary/20"
                    >
                        Save & Finish
                    </button>
                </div>
            </div>
        </div>
    );
}

function ApiKeyInput({
    label, value, onChange, placeholder, isKey = true
}: {
    label: string;
    value: string;
    onChange: (v: string) => void;
    placeholder: string;
    isKey?: boolean;
}) {
    const [show, setShow] = useState(!isKey);

    return (
        <div className="space-y-2">
            <label className="text-sm font-medium">{label}</label>
            <div className="relative">
                <input
                    type={show ? "text" : "password"}
                    value={value}
                    onChange={(e) => onChange(e.target.value)}
                    placeholder={placeholder}
                    className={cn(
                        "w-full bg-background border border-input rounded-lg py-2 px-4 pr-10 text-sm outline-none transition-all",
                        "focus:ring-2 focus:ring-primary/20 focus:border-primary"
                    )}
                />
                {isKey && (
                    <button
                        type="button"
                        onClick={() => setShow(!show)}
                        className="absolute right-3 top-2.5 text-muted-foreground hover:text-foreground"
                    >
                        {show ? <X className="w-4 h-4" /> : <Shield className="w-4 h-4" />}
                    </button>
                )}
            </div>
        </div>
    );
}
