import { create } from "zustand";
import { persist } from "zustand/middleware";

export type Vendor = "google" | "openai" | "anthropic" | "ollama";

interface Settings {
    // API Keys
    googleApiKey: string;
    openaiApiKey: string;
    anthropicApiKey: string;
    ollamaUrl: string;

    // Preferences
    vendor: Vendor;
    model: string;
    temperature: number;
    topP: number;
    strategy: string;
    thinkingLevel: number; // 0 (off), 1 (normal), 2 (deep)

    // Theme
    theme: "light" | "dark" | "system";
}

interface SettingsStore extends Settings {
    setApiKey: (vendor: Vendor, key: string) => void;
    setVendor: (vendor: Vendor) => void;
    setModel: (model: string) => void;
    setTemperature: (temp: number) => void;
    setTopP: (topP: number) => void;
    setStrategy: (strategy: string) => void;
    setThinkingLevel: (level: number) => void;
    setTheme: (theme: "light" | "dark" | "system") => void;
    getApiKey: (vendor: Vendor) => string;
}

export const useSettingsStore = create<SettingsStore>()(
    persist(
        (set, get) => ({
            // Default values
            googleApiKey: "",
            openaiApiKey: "",
            anthropicApiKey: "",
            ollamaUrl: "http://localhost:11434",
            vendor: "google",
            model: "gemini-2.0-flash",
            temperature: 0.7,
            topP: 0.9,
            strategy: "none",
            thinkingLevel: 0,
            theme: "dark",

            setApiKey: (vendor, key) => {
                switch (vendor) {
                    case "google":
                        set({ googleApiKey: key });
                        break;
                    case "openai":
                        set({ openaiApiKey: key });
                        break;
                    case "anthropic":
                        set({ anthropicApiKey: key });
                        break;
                }
            },

            setVendor: (vendor) => set({ vendor }),
            setModel: (model) => set({ model }),
            setTemperature: (temperature) => set({ temperature }),
            setTopP: (topP) => set({ topP }),
            setStrategy: (strategy) => set({ strategy }),
            setThinkingLevel: (thinkingLevel) => set({ thinkingLevel }),
            setTheme: (theme) => set({ theme }),

            getApiKey: (vendor) => {
                const state = get();
                switch (vendor) {
                    case "google":
                        return state.googleApiKey;
                    case "openai":
                        return state.openaiApiKey;
                    case "anthropic":
                        return state.anthropicApiKey;
                    default:
                        return "";
                }
            },
        }),
        {
            name: "fabric-settings",
        }
    )
);
