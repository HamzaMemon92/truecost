import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import * as SecureStore from 'expo-secure-store';
import { publicApi, SessionTokens } from '../api/client';
import { clearProviderConnectionsCache } from '../api/providerConnections';
import { clearAccountLocationCache } from '../location/LocationContext';

type AuthContextValue = {
  session: SessionTokens | null;
  ready: boolean;
  isGuest: boolean;
  signIn(email: string, password: string, register?: boolean): Promise<void>;
  signOut(): Promise<void>;
  updateSession(next: SessionTokens): Promise<void>;
  continueAsGuest(): Promise<void>;
  leaveGuest(): Promise<void>;
};
const SESSION_KEY = 'truecost.session.v1';
const GUEST_KEY = 'truecost.guest.v1';
const STORE_OPTIONS: SecureStore.SecureStoreOptions = { keychainAccessible: SecureStore.WHEN_UNLOCKED };
const AuthContext = createContext<AuthContextValue | null>(null);

async function storeAvailable() {
  return SecureStore.isAvailableAsync().catch(() => false);
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [session, setSession] = useState<SessionTokens | null>(null);
  const [isGuest, setIsGuest] = useState(false);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    (async () => {
      if (!await storeAvailable()) return;
      const [rawSession, rawGuest] = await Promise.all([
        SecureStore.getItemAsync(SESSION_KEY, STORE_OPTIONS),
        SecureStore.getItemAsync(GUEST_KEY, STORE_OPTIONS),
      ]);
      if (rawSession) {
        try {
          const parsed = JSON.parse(rawSession) as SessionTokens;
          if (parsed.access_token && parsed.refresh_token) setSession(parsed);
        } catch {
          await SecureStore.deleteItemAsync(SESSION_KEY, STORE_OPTIONS);
        }
      } else if (rawGuest === 'true') setIsGuest(true);
    })().catch(() => {}).finally(() => setReady(true));
  }, []);

  const updateSession = useCallback(async (next: SessionTokens) => {
    if (session?.user_id && session.user_id !== next.user_id) await clearProviderConnectionsCache(session.user_id);
    if (await storeAvailable()) {
      await SecureStore.setItemAsync(SESSION_KEY, JSON.stringify(next), STORE_OPTIONS);
      await SecureStore.deleteItemAsync(GUEST_KEY, STORE_OPTIONS);
    }
    setIsGuest(false);
    setSession(next);
  }, [session?.user_id]);

  const signIn = useCallback(async (email: string, password: string, register = false) => {
    const next = await publicApi<SessionTokens>(`/auth/${register ? 'register' : 'login'}`, {
      method: 'POST',
      body: JSON.stringify({ email: email.trim(), password }),
    });
    await updateSession(next);
  }, [updateSession]);

  const signOut = useCallback(async () => {
    const current = session;
    if (current) {
      await publicApi('/auth/logout', { method: 'POST', body: JSON.stringify({ refresh_token: current.refresh_token }) }).catch(() => {});
    }
    if (await storeAvailable()) {
      await Promise.all([SecureStore.deleteItemAsync(SESSION_KEY, STORE_OPTIONS), SecureStore.deleteItemAsync(GUEST_KEY, STORE_OPTIONS), clearProviderConnectionsCache(current?.user_id), clearAccountLocationCache(current?.user_id)]);
    }
    setSession(null); setIsGuest(false);
  }, [session]);

  const continueAsGuest = useCallback(async () => {
    if (await storeAvailable()) await SecureStore.setItemAsync(GUEST_KEY, 'true', STORE_OPTIONS);
    setSession(null); setIsGuest(true);
  }, []);
  const leaveGuest = useCallback(async () => {
    if (await storeAvailable()) await SecureStore.deleteItemAsync(GUEST_KEY, STORE_OPTIONS);
    setIsGuest(false);
  }, []);

  const value = useMemo<AuthContextValue>(() => ({ session, ready, isGuest, signIn, signOut, updateSession, continueAsGuest, leaveGuest }), [session, ready, isGuest, signIn, signOut, updateSession, continueAsGuest, leaveGuest]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const value = useContext(AuthContext);
  if (!value) throw new Error('useAuth must be used within AuthProvider');
  return value;
}
