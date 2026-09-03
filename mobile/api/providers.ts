import { publicApi } from './client';

export type ProviderCapability = {
  id: string;
  name: string;
  category_id: string;
  display_name?: string;
  category?: string;
  aliases: string[];
  handoff_capability: 'app' | 'web' | 'none' | string;
  freshness_sla_seconds: number;
  source_mode: 'live' | 'preview' | 'manual' | 'disabled' | string;
  rollout_state: 'catalogued' | 'testing' | 'verified' | 'degraded' | 'disabled' | string;
  account_connection_state?: 'pending_approval' | 'enabled' | 'connected' | 'disabled' | string;
  connection_state?: 'pending_approval' | 'enabled' | 'connected' | 'disabled' | string;
  connection_available?: boolean;
  live?: boolean;
  last_ingested_at?: string | null;
};

export type ProviderHealth = {
  provider_id: string;
  name: string;
  category_id: string;
  display_name?: string;
  category?: string;
  rollout_state: string;
  current_capability: 'live' | 'preview' | 'degraded' | 'unavailable' | string;
  live?: boolean;
  last_ingested_at?: string | null;
  freshness_sla_seconds: number;
  stale: boolean;
  ingested_observations: number;
  parser_success_rate: number;
  timeout_rate: number | null;
  exact_match_success_rate: number | null;
  failure_reason?: string | null;
};

export type ProviderCatalogResponse = {
  providers: ProviderCapability[];
  categories: Array<{
    id: string;
    name: string;
    engine_category: string;
    capability: string;
    [key: string]: unknown;
  }>;
  version?: string;
};

export type ProviderHealthResponse = {
  providers: ProviderHealth[];
  generated_at: string;
};

export async function getProviderCatalog() {
  return publicApi<ProviderCatalogResponse>('/providers');
}

export async function getProviderHealth() {
  return publicApi<ProviderHealthResponse>('/providers/health');
}
