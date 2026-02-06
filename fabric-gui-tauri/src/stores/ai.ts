import { create } from "zustand";

type InputMode = "text" | "url" | "youtube";

interface AIStore {
    // Input
    inputMode: InputMode;
    inputText: string;

    // Output
    output: string;
    isStreaming: boolean;
    error: string | null;

    // Actions
    setInputMode: (mode: InputMode) => void;
    setInputText: (text: string) => void;
    appendOutput: (chunk: string) => void;
    clearOutput: () => void;
    setStreaming: (streaming: boolean) => void;
    setError: (error: string | null) => void;
}

export const useAIStore = create<AIStore>((set) => ({
    inputMode: "text",
    inputText: "",
    output: "",
    isStreaming: false,
    error: null,

    setInputMode: (mode) => set({ inputMode: mode }),
    setInputText: (text) => set({ inputText: text }),
    appendOutput: (chunk) => set((state) => ({ output: state.output + chunk })),
    clearOutput: () => set({ output: "", error: null }),
    setStreaming: (streaming) => set({ isStreaming: streaming }),
    setError: (error) => set({ error, isStreaming: false }),
}));
