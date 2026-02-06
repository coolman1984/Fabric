import { Search, Folder, Star } from "lucide-react";
import { useState } from "react";
import { usePatternStore } from "../stores/patterns";
import { cn } from "../lib/utils";

export function PatternBrowser() {
    const { patterns, selectedPattern, setSelectedPattern, toggleFavorite, isFavorite } = usePatternStore();
    const [search, setSearch] = useState("");

    const filteredPatterns = patterns.filter((p) =>
        p.name.toLowerCase().includes(search.toLowerCase())
    );

    const favoritePatterns = filteredPatterns.filter(p => isFavorite(p.name));
    const normalPatterns = filteredPatterns.filter(p => !isFavorite(p.name));

    return (
        <div className="flex flex-col h-full overflow-hidden">
            <div className="p-4 space-y-4">
                <div className="flex items-center justify-between">
                    <h2 className="text-xs font-bold text-muted-foreground uppercase tracking-widest flex items-center gap-2">
                        <Folder className="w-4 h-4" />
                        Patterns
                    </h2>
                    <span className="text-[10px] bg-primary/10 text-primary px-1.5 py-0.5 rounded-full font-bold">
                        {filteredPatterns.length}
                    </span>
                </div>

                <div className="relative group">
                    <Search className="absolute left-3 top-2.5 w-4 h-4 text-muted-foreground group-focus-within:text-primary transition-colors" />
                    <input
                        type="text"
                        placeholder="Search patterns..."
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                        className={cn(
                            "w-full bg-muted/50 border border-transparent rounded-lg py-2 pl-9 pr-4 text-sm outline-none transition-all",
                            "focus:bg-background focus:border-primary/50 focus:ring-4 focus:ring-primary/5"
                        )}
                        title="Search patterns"
                    />
                </div>
            </div>

            <div className="flex-1 overflow-y-auto px-2 pb-4 style-scrollbar space-y-4">
                {/* Favorites Section */}
                {favoritePatterns.length > 0 && (
                    <div className="space-y-0.5">
                        <h3 className="px-3 text-[10px] font-bold text-amber-500 uppercase tracking-widest mb-1 flex items-center gap-1">
                            <Star className="w-3 h-3 fill-current" />
                            Favorites
                        </h3>
                        {favoritePatterns.map((pattern) => (
                            <PatternItem
                                key={pattern.name}
                                pattern={pattern}
                                isSelected={selectedPattern === pattern.name}
                                isFav={true}
                                onSelect={() => setSelectedPattern(pattern.name)}
                                onToggleFav={() => toggleFavorite(pattern.name)}
                            />
                        ))}
                    </div>
                )}

                {/* All Patterns Section */}
                <div className="space-y-0.5">
                    {favoritePatterns.length > 0 && (
                        <h3 className="px-3 text-[10px] font-bold text-muted-foreground uppercase tracking-widest mb-1">
                            All Patterns
                        </h3>
                    )}
                    {normalPatterns.map((pattern: any) => (
                        <PatternItem
                            key={pattern.name}
                            pattern={pattern}
                            isSelected={selectedPattern === pattern.name}
                            isFav={false}
                            onSelect={() => setSelectedPattern(pattern.name)}
                            onToggleFav={() => toggleFavorite(pattern.name)}
                        />
                    ))}
                </div>
            </div>

            <div className="p-4 border-t border-border bg-muted/20">
                <div className="flex items-center gap-2 text-[10px] text-muted-foreground uppercase font-bold">
                    <div className="w-1 h-4 bg-primary rounded-full" />
                    Total {patterns.length} available
                </div>
            </div>
        </div>
    );
}

function PatternItem({ pattern, isSelected, isFav, onSelect, onToggleFav }: {
    pattern: any,
    isSelected: boolean,
    isFav: boolean,
    onSelect: () => void,
    onToggleFav: () => void
}) {
    return (
        <div className="group relative">
            <button
                onClick={onSelect}
                title={`Select ${pattern.name}`}
                className={cn(
                    "w-full flex items-center px-3 py-2.5 rounded-lg text-sm transition-all",
                    isSelected
                        ? "bg-primary shadow-lg shadow-primary/20 text-primary-foreground font-medium"
                        : "hover:bg-accent/50 text-muted-foreground hover:text-foreground"
                )}
            >
                <span className={cn(
                    "flex-1 text-left truncate pr-8",
                    isSelected ? "text-white" : "group-hover:translate-x-1 transition-transform"
                )}>
                    {pattern.name.replace(/_/g, " ")}
                </span>
                {isSelected && <div className="w-1.5 h-1.5 rounded-full bg-white shadow-sm" />}
            </button>
            <button
                onClick={(e) => {
                    e.stopPropagation();
                    onToggleFav();
                }}
                title={isFav ? "Remove from favorites" : "Add to favorites"}
                className={cn(
                    "absolute right-2 top-1/2 -translate-y-1/2 p-2 rounded-md transition-all",
                    isFav ? "text-amber-500 opacity-100" : "text-muted-foreground opacity-0 group-hover:opacity-100 hover:text-amber-500 hover:bg-amber-500/10"
                )}
            >
                <Star className={cn("w-4 h-4", isFav && "fill-current")} />
            </button>
        </div>
    );
}
