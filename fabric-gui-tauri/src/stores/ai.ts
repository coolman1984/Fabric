import { create } from "zustand";

export type InputMode = "text" | "url" | "youtube";

interface AIStore {
    // Input
    inputMode: InputMode;
    inputText: string;
    includeTimestamps: boolean;

    // Output
    output: string;
    isStreaming: boolean;
    error: string | null;

    // Actions
    setInputMode: (mode: InputMode) => void;
    setInputText: (text: string) => void;
    setIncludeTimestamps: (include: boolean) => void;
    appendOutput: (chunk: string) => void;
    clearOutput: () => void;
    setStreaming: (streaming: boolean) => void;
    setError: (error: string | null) => void;
}

export const useAIStore = create<AIStore>((set) => ({
    inputMode: "text",
    inputText: "",
    includeTimestamps: false,
    output: "",
    isStreaming: false,
    error: null,

    setInputMode: (inputMode) => set({ inputMode }),
    setInputText: (inputText) => set({ inputText }),
    setIncludeTimestamps: (includeTimestamps) => set({ includeTimestamps }),
    appendOutput: (chunk) => set((state) => ({ output: state.output + chunk })),
    clearOutput: () => set({ output: "", error: null }),
    setStreaming: (isStreaming) => set({ isStreaming }),
    setError: (error) => set({ error }),
}));
