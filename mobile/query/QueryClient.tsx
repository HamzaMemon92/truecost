import React, { createContext, useCallback, useContext, useMemo, useRef, useState } from 'react';

type Entry = { data?: unknown; updatedAt: number; promise?: Promise<unknown> };
type QueryContextValue = {
  load<T>(key: string, request: () => Promise<T>, maxAge?: number): Promise<T>;
  peek<T>(key: string): T | undefined;
  invalidate(prefix?: string): void;
  revision: number;
};

const QueryContext = createContext<QueryContextValue | null>(null);

export function QueryProvider({ children }: { children: React.ReactNode }) {
  const cache = useRef(new Map<string, Entry>());
  const [revision, setRevision] = useState(0);
  const load = useCallback(async <T,>(key: string, request: () => Promise<T>, maxAge = 30_000) => {
    const current = cache.current.get(key);
    if (current?.data !== undefined && Date.now() - current.updatedAt < maxAge) return current.data as T;
    if (current?.promise) return current.promise as Promise<T>;
    const promise = request().then(data => {
      cache.current.set(key, { data, updatedAt: Date.now() });
      setRevision(value => value + 1);
      return data;
    }).catch(error => {
      cache.current.delete(key);
      throw error;
    });
    cache.current.set(key, { ...current, updatedAt: current?.updatedAt || 0, promise });
    return promise;
  }, []);
  const peek = useCallback(<T,>(key: string) => cache.current.get(key)?.data as T | undefined, []);
  const invalidate = useCallback((prefix = '') => {
    for (const key of cache.current.keys()) if (!prefix || key.startsWith(prefix)) cache.current.delete(key);
    setRevision(value => value + 1);
  }, []);
  const value = useMemo(() => ({ load, peek, invalidate, revision }), [load, peek, invalidate, revision]);
  return <QueryContext.Provider value={value}>{children}</QueryContext.Provider>;
}

export function useQueryClient() {
  const value = useContext(QueryContext);
  if (!value) throw new Error('useQueryClient must be used within QueryProvider');
  return value;
}
