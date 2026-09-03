import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import * as SecureStore from 'expo-secure-store';

export type UserLocation = { latitude: number; longitude: number; city?: string; display?: string; postalCode?: string; addressId?: string; source?: 'device' | 'saved' | 'manual' };
type LocationValue = { location: UserLocation | null; ready: boolean; persistenceEnabled: boolean; setPersistenceEnabled(value: boolean): void; setLocation(value: UserLocation): void; clearLocation(): void };
const LocationContext = createContext<LocationValue | null>(null);
const locationKey = (scope: string) => `truecost.active-location.v3.${scope}`;
const persistenceKey = (scope: string) => `truecost.location-persistence.v2.${scope}`;
const STORE_OPTIONS: SecureStore.SecureStoreOptions = { keychainAccessible: SecureStore.WHEN_UNLOCKED };

export async function clearAccountLocationCache(scope?: string) {
  if (!scope || !await SecureStore.isAvailableAsync().catch(() => false)) return;
  await Promise.all([SecureStore.deleteItemAsync(locationKey(scope), STORE_OPTIONS), SecureStore.deleteItemAsync(persistenceKey(scope), STORE_OPTIONS)]);
}

export function LocationProvider({ children, accountScope = 'guest' }: { children: React.ReactNode; accountScope?: string }) {
  const [location, setState] = useState<UserLocation | null>(null);
  const [ready, setReady] = useState(false);
  const [persistenceEnabled, setPersistenceState] = useState(false);
  useEffect(() => { (async () => {
    if (!await SecureStore.isAvailableAsync().catch(() => false)) return;
    const enabled = await SecureStore.getItemAsync(persistenceKey(accountScope), STORE_OPTIONS) === 'true';
    setPersistenceState(enabled);
    if (!enabled) { await SecureStore.deleteItemAsync(locationKey(accountScope), STORE_OPTIONS); return; }
    const raw = await SecureStore.getItemAsync(locationKey(accountScope), STORE_OPTIONS);
    if (!raw) return;
    try {
      const value = JSON.parse(raw) as UserLocation;
      if (Number.isFinite(value.latitude) && Number.isFinite(value.longitude)) setState(value);
    } catch { await SecureStore.deleteItemAsync(locationKey(accountScope), STORE_OPTIONS); }
  })().finally(() => setReady(true)); }, [accountScope]);
  const setLocation = useCallback((value: UserLocation) => {
    setState(value);
    void SecureStore.isAvailableAsync().then(available => available ? (persistenceEnabled ? SecureStore.setItemAsync(locationKey(accountScope), JSON.stringify(value), STORE_OPTIONS) : SecureStore.deleteItemAsync(locationKey(accountScope), STORE_OPTIONS)) : undefined).catch(() => undefined);
  }, [persistenceEnabled, accountScope]);
  const setPersistenceEnabled = useCallback((enabled: boolean) => {
    setPersistenceState(enabled);
    void SecureStore.isAvailableAsync().then(async available => { if (!available) return; await SecureStore.setItemAsync(persistenceKey(accountScope), String(enabled), STORE_OPTIONS); if (enabled && location) await SecureStore.setItemAsync(locationKey(accountScope), JSON.stringify(location), STORE_OPTIONS); else if (!enabled) await SecureStore.deleteItemAsync(locationKey(accountScope), STORE_OPTIONS); }).catch(() => undefined);
  }, [location, accountScope]);
  const clearLocation = useCallback(() => {
    setState(null);
    void SecureStore.isAvailableAsync().then(available => available ? SecureStore.deleteItemAsync(locationKey(accountScope), STORE_OPTIONS) : undefined).catch(() => undefined);
  }, [accountScope]);
  const value = useMemo(() => ({ location, ready, persistenceEnabled, setPersistenceEnabled, setLocation, clearLocation }), [location, ready, persistenceEnabled, setPersistenceEnabled, setLocation, clearLocation]);
  return <LocationContext.Provider value={value}>{children}</LocationContext.Provider>;
}

export function useUserLocation() {
  const value = useContext(LocationContext);
  if (!value) throw new Error('useUserLocation must be used within LocationProvider');
  return value;
}
