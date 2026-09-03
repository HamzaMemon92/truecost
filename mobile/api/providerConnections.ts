import * as SecureStore from 'expo-secure-store';
import { api, SessionTokens, TokenWriter } from './client';

export type ProviderConnectionStatus = 'disconnected' | 'connecting' | 'connected' | 'expired';
export type ProviderConnection = {
  id: string;
  name: string;
  category: string;
  brand_color: string;
  mark: string;
  status: ProviderConnectionStatus;
  connection_supported: boolean;
  account_label?: string | null;
  connected_at?: string | null;
  expires_at?: string | null;
};
export type ProviderConnectionStart = { authorization_url: string; callback_url: string; expires_at: string };
export type ProviderConnectionCallback = {
  provider_id: string;
  state: string;
  result: 'connected' | 'expired' | 'cancelled';
  account_label?: string | null;
  expires_at?: string | null;
  signature: string;
};

const CACHE_PREFIX = 'truecost.provider-connections.v2';
const STORE_OPTIONS: SecureStore.SecureStoreOptions = { keychainAccessible: SecureStore.WHEN_UNLOCKED };

export async function listProviderConnections(tokens: SessionTokens, writeTokens: TokenWriter) {
  return api<ProviderConnection[]>(tokens, writeTokens, '/provider-connections');
}

export async function startProviderConnection(tokens: SessionTokens, writeTokens: TokenWriter, providerId: string) {
  return api<ProviderConnectionStart>(tokens, writeTokens, `/provider-connections/${encodeURIComponent(providerId)}/start`, { method: 'POST' });
}

export async function completeProviderConnection(tokens: SessionTokens, writeTokens: TokenWriter, callback: ProviderConnectionCallback) {
  return api<ProviderConnection>(tokens, writeTokens, '/provider-connections/complete', { method: 'POST', body: JSON.stringify(callback) });
}

export async function disconnectProvider(tokens: SessionTokens, writeTokens: TokenWriter, providerId: string) {
  return api<ProviderConnection>(tokens, writeTokens, `/provider-connections/${encodeURIComponent(providerId)}`, { method: 'DELETE' });
}

const cacheKey = (accountId: string) => `${CACHE_PREFIX}.${accountId}`;

export async function cacheProviderConnections(accountId: string, connections: ProviderConnection[]) {
  if (!await SecureStore.isAvailableAsync().catch(() => false)) return;
  const safe = connections.map(({ id, name, category, brand_color, mark, status, connection_supported, account_label, connected_at, expires_at }) => ({ id, name, category, brand_color, mark, status, connection_supported, account_label, connected_at, expires_at }));
  await SecureStore.setItemAsync(cacheKey(accountId), JSON.stringify(safe), STORE_OPTIONS);
}

export async function readCachedProviderConnections(accountId: string): Promise<ProviderConnection[]> {
  if (!await SecureStore.isAvailableAsync().catch(() => false)) return [];
  const raw = await SecureStore.getItemAsync(cacheKey(accountId), STORE_OPTIONS);
  if (!raw) return [];
  try {
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    await SecureStore.deleteItemAsync(cacheKey(accountId), STORE_OPTIONS);
    return [];
  }
}

export async function clearProviderConnectionsCache(accountId?: string) {
  if (accountId && await SecureStore.isAvailableAsync().catch(() => false)) await SecureStore.deleteItemAsync(cacheKey(accountId), STORE_OPTIONS);
}
