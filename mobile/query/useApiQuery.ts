import { useCallback, useEffect, useState } from 'react';
import { api } from '../api/client';
import { useAuth } from '../auth/AuthContext';
import { useQueryClient } from './QueryClient';

export function useApiQuery<T>(key: string, path: string, options: { enabled?: boolean; maxAge?: number } = {}) {
  const { session, updateSession } = useAuth();
  const client = useQueryClient();
  const [data, setData] = useState<T | undefined>(() => client.peek<T>(key));
  const [error, setError] = useState<Error | null>(null);
  const [loading, setLoading] = useState(!data);
  const enabled = (options.enabled ?? true) && !!session;
  const refetch = useCallback(async () => {
    if (!session || !enabled) return;
    setLoading(true); setError(null);
    try {
      const result = await client.load<T>(key, () => api<T>(session, updateSession, path), options.maxAge);
      setData(result);
    } catch (cause) {
      setError(cause instanceof Error ? cause : new Error('Request failed'));
    } finally {
      setLoading(false);
    }
  }, [client, enabled, key, options.maxAge, path, session, updateSession]);
  useEffect(() => { void refetch(); }, [refetch, client.revision]);
  return { data, error, loading, refetch, invalidate: () => client.invalidate(key) };
}
