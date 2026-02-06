import { create } from "zustand";
import { persist } from "zustand/middleware";

interface Pattern {
    name: string;
    description?: string;
}

interface PatternStore {
    patterns: Pattern[];
    favorites: string[];
    selectedPattern: string | null;
    searchQuery: string;

    setPatterns: (patterns: Pattern[]) => void;
    setSelectedPattern: (name: string | null) => void;
    setSearchQuery: (query: string) => void;
    toggleFavorite: (name: string) => void;
    isFavorite: (name: string) => boolean;
}

export const usePatternStore = create<PatternStore>()(
    persist(
        (set, get) => ({
            patterns: [],
            favorites: [],
            selectedPattern: null,
            searchQuery: "",

            setPatterns: (patterns) => set({ patterns }),
            setSelectedPattern: (name) => set({ selectedPattern: name }),
            setSearchQuery: (query) => set({ searchQuery: query }),

            toggleFavorite: (name) => {
                const { favorites } = get();
                if (favorites.includes(name)) {
                    set({ favorites: favorites.filter((f) => f !== name) });
                } else {
                    set({ favorites: [...favorites, name] });
                }
            },

            isFavorite: (name) => get().favorites.includes(name),
        }),
        {
            name: "fabric-patterns",
            partialize: (state) => ({ favorites: state.favorites }),
        }
    )
);
