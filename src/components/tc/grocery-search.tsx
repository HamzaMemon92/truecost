import React, { useState, useEffect, useRef } from "react";
import { Search, History, Sparkles, Box, Tag, Layers, Flame, ArrowRight } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { fetchAutocomplete, parseMultiItemIntent, AutocompleteSuggestion, ParsedItem } from "@/lib/grocery-utils";
import { cn } from "@/lib/utils";

interface GrocerySearchProps {
  onSelectItem: (item: string) => void;
  onSelectMultiple: (items: ParsedItem[]) => void;
}

export function GrocerySearch({ onSelectItem, onSelectMultiple }: GrocerySearchProps) {
  const [query, setQuery] = useState("");
  const [isOpen, setIsOpen] = useState(false);
  const [suggestions, setSuggestions] = useState<AutocompleteSuggestion[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const [multiItems, setMultiItems] = useState<ParsedItem[]>([]);
  
  const containerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Debounce search
  useEffect(() => {
    if (!isOpen) return;

    const parsed = parseMultiItemIntent(query);
    setMultiItems(parsed);

    let isMounted = true;
    setIsLoading(true);

    const timeoutId = setTimeout(async () => {
      try {
        const results = await fetchAutocomplete(query);
        if (isMounted) {
          setSuggestions(results);
          setSelectedIndex(-1);
        }
      } finally {
        if (isMounted) setIsLoading(false);
      }
    }, 150);

    return () => {
      isMounted = false;
      clearTimeout(timeoutId);
    };
  }, [query, isOpen]);

  // Click outside listener
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!isOpen) return;

    if (e.key === "ArrowDown") {
      e.preventDefault();
      setSelectedIndex(prev => (prev < suggestions.length - 1 ? prev + 1 : prev));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setSelectedIndex(prev => (prev > 0 ? prev - 1 : -1));
    } else if (e.key === "Enter") {
      e.preventDefault();
      
      if (multiItems.length > 1 && selectedIndex === -1) {
        // User typed a multi-item intent and hit enter without selecting a specific suggestion
        handleAddMultiple();
      } else if (selectedIndex >= 0 && selectedIndex < suggestions.length) {
        handleSelectSuggestion(suggestions[selectedIndex]!);
      } else if (query.trim()) {
        // Fallback: just add whatever they typed if no suggestions selected
        onSelectItem(query.trim());
        reset();
      }
    } else if (e.key === "Escape") {
      setIsOpen(false);
    }
  };

  const handleSelectSuggestion = (s: AutocompleteSuggestion) => {
    if (s.type === "SMART") {
      // Just an example: a smart bundle could add multiple
      onSelectMultiple([
        { qty: 1, name: "Milk" },
        { qty: 1, name: "Eggs" },
        { qty: 1, name: "Bread" }
      ]);
    } else {
      onSelectItem(s.title);
    }
    reset();
  };

  const handleAddMultiple = () => {
    onSelectMultiple(multiItems);
    reset();
  };

  const reset = () => {
    setQuery("");
    setIsOpen(false);
    inputRef.current?.focus();
  };

  return (
    <div className="relative w-full z-50" ref={containerRef}>
      <div className={cn(
        "relative flex items-center w-full transition-all duration-200",
        "bg-surface border shadow-[var(--shadow-glow)]",
        isOpen ? "rounded-t-2xl border-brand ring-1 ring-brand/30" : "rounded-2xl border-border hover:border-brand/50"
      )}>
        <Search className="absolute left-4 h-5 w-5 text-muted-foreground" />
        <input
          ref={inputRef}
          type="text"
          value={query}
          onChange={(e) => {
            setQuery(e.target.value);
            if (!isOpen) setIsOpen(true);
          }}
          onFocus={() => setIsOpen(true)}
          onKeyDown={handleKeyDown}
          placeholder="Search items: milk, eggs, bread..."
          className="w-full bg-transparent py-4 pl-12 pr-4 text-base outline-none placeholder:text-muted-foreground"
          autoComplete="off"
          spellCheck="false"
        />
        {isLoading && (
          <div className="absolute right-4 top-1/2 -translate-y-1/2">
            <div className="h-4 w-4 animate-spin rounded-full border-2 border-brand border-t-transparent" />
          </div>
        )}
      </div>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.15, ease: "easeOut" }}
            className="absolute top-full left-0 right-0 overflow-hidden rounded-b-2xl border-x border-b border-brand/30 bg-surface/95 backdrop-blur-xl shadow-2xl"
          >
            <div className="max-h-[400px] overflow-y-auto p-2 scrollbar-thin">
              
              {/* Multi-Item Intent Banner */}
              {multiItems.length > 1 && (
                <div 
                  onClick={handleAddMultiple}
                  className={cn(
                    "mb-2 flex cursor-pointer flex-col gap-2 rounded-xl p-3 transition-colors",
                    selectedIndex === -1 ? "bg-brand/10 border border-brand/20" : "bg-brand/5 border border-transparent hover:bg-brand/10"
                  )}
                >
                  <div className="flex items-center gap-2 font-medium text-brand">
                    <Sparkles className="h-4 w-4" />
                    <span>We found {multiItems.length} items</span>
                  </div>
                  <div className="flex flex-wrap gap-2 text-sm text-foreground">
                    {multiItems.map((item, idx) => (
                      <span key={idx} className="flex items-center gap-1 rounded-md bg-surface-2 px-2 py-1 border border-border">
                        <CheckIcon className="h-3 w-3 text-positive" />
                        {item.name} <span className="text-muted-foreground ml-1">×{item.qty}</span>
                      </span>
                    ))}
                  </div>
                  <div className="mt-1 flex items-center gap-1 text-xs font-semibold text-brand hover:underline">
                    Press Enter to add all <ArrowRight className="h-3 w-3" />
                  </div>
                </div>
              )}

              {/* Suggestions List */}
              {suggestions.length > 0 ? (
                <div className="flex flex-col">
                  {suggestions.map((s, index) => {
                    const isSelected = selectedIndex === index;
                    return (
                      <div
                        key={s.id}
                        onMouseEnter={() => setSelectedIndex(index)}
                        onClick={() => handleSelectSuggestion(s)}
                        className={cn(
                          "flex cursor-pointer items-center gap-3 rounded-xl px-3 py-2.5 transition-colors",
                          isSelected ? "bg-surface-2/80" : "hover:bg-surface-2/50"
                        )}
                      >
                        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-surface-3 text-muted-foreground">
                          {s.type === "PRODUCT" && <Box className="h-4 w-4" />}
                          {s.type === "CATEGORY" && (s.icon ? <s.icon className="h-4 w-4" /> : <Layers className="h-4 w-4" />)}
                          {s.type === "BRAND" && <Tag className="h-4 w-4" />}
                          {s.type === "RECENT" && <History className="h-4 w-4" />}
                          {s.type === "POPULAR" && <Flame className="h-4 w-4 text-orange-500" />}
                          {s.type === "SMART" && <Sparkles className="h-4 w-4 text-brand" />}
                        </div>
                        <div className="flex flex-col overflow-hidden">
                          <span className="truncate text-sm font-medium text-foreground">
                            {s.title}
                          </span>
                          {s.subtitle && (
                            <span className="truncate text-xs text-muted-foreground">
                              {s.subtitle}
                            </span>
                          )}
                        </div>
                        {s.type === "RECENT" && <span className="ml-auto text-[10px] uppercase tracking-wider text-muted-foreground">Recent</span>}
                      </div>
                    );
                  })}
                </div>
              ) : (
                !isLoading && multiItems.length <= 1 && (
                  <div className="py-8 text-center text-sm text-muted-foreground">
                    No exact matches found. Press Enter to search.
                  </div>
                )
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

function CheckIcon(props: any) {
  return (
    <svg
      {...props}
      fill="none"
      strokeWidth="2"
      stroke="currentColor"
      viewBox="0 0 24 24"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7"></path>
    </svg>
  );
}
