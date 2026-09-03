import React, { createContext, useCallback, useContext, useMemo, useState } from 'react';

export type SearchIntent = { query: string; category: string; createdAt: number };
type SearchHistoryValue = { recent: SearchIntent[]; remember(query: string, category: string): void; clear(): void };
const SearchHistoryContext = createContext<SearchHistoryValue | null>(null);

export function SearchHistoryProvider({ children }: { children: React.ReactNode }) {
  const [recent, setRecent] = useState<SearchIntent[]>([]);
  const remember = useCallback((query: string, category: string) => {
    const normalized = query.trim();
    if (!normalized) return;
    setRecent(current => [{ query: normalized, category, createdAt: Date.now() }, ...current.filter(item => item.query.toLowerCase() !== normalized.toLowerCase() || item.category !== category)].slice(0, 8));
  }, []);
  const value = useMemo(() => ({ recent, remember, clear: () => setRecent([]) }), [recent, remember]);
  return <SearchHistoryContext.Provider value={value}>{children}</SearchHistoryContext.Provider>;
}

export function useSearchHistory() {
  const value = useContext(SearchHistoryContext);
  if (!value) throw new Error('useSearchHistory must be used within SearchHistoryProvider');
  return value;
}
