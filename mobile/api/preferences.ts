import { BACKEND_URL } from '../config';
import type { SessionTokens } from './client';

export interface UserPreferences {
  optimization_objective: 'cheapest' | 'balanced' | 'fastest';
  dietary_flags: string[];
  favorite_providers: string[];
  preferred_payment_methods: string[];
  notification_price_drops: boolean;
  notification_deals: boolean;
  notification_travel: boolean;
  notification_activity: boolean;
  accessibility_reduce_motion: boolean;
  accessibility_large_text: boolean;
  theme: 'light' | 'dark' | 'system';
  language: string;
}

export type PreferencesUpdate = Partial<UserPreferences>;

export async function getPreferences(tokens: SessionTokens): Promise<UserPreferences> {
  const res = await fetch(`${BACKEND_URL}/api/v1/preferences`, {
    headers: { Authorization: `Bearer ${tokens.access_token}` },
  });
  if (!res.ok) throw new Error('Failed to load preferences');
  return res.json();
}

export async function updatePreferences(
  tokens: SessionTokens,
  update: PreferencesUpdate
): Promise<UserPreferences> {
  const res = await fetch(`${BACKEND_URL}/api/v1/preferences`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${tokens.access_token}`,
    },
    body: JSON.stringify(update),
  });
  if (!res.ok) throw new Error('Failed to update preferences');
  return res.json();
}
