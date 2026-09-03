import { publicApi } from './client';

export type ObservedSearchSuggestion = {
  query: string;
  category: string;
  kind: 'observed_product';
  product_id?: string;
  brand?: string;
  image_url?: string;
  provider_count: number;
};

export type SearchCacheState = {
  cache_hits: Record<string, unknown[]>;
  cache_misses: string[];
};

export function getObservedSuggestions(query: string, category: string) {
  const params = new URLSearchParams({ q: query, category, limit: '6' });
  return publicApi<ObservedSearchSuggestion[]>(`/aggregator/suggestions?${params.toString()}`);
}

export function getSearchCacheState(query: string, category: string) {
  const params = new URLSearchParams({ q: query, category });
  return publicApi<SearchCacheState>(`/aggregator/search?${params.toString()}`);
}
