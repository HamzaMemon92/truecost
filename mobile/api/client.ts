import { BACKEND_URL } from '../config';

export type SessionTokens = { access_token: string; refresh_token: string; user_id: string; token_type?: string };
export type TokenWriter = (value: SessionTokens) => Promise<void>;

export class ApiError extends Error {
  constructor(message: string, public readonly status: number, public readonly code?: string) {
    super(message);
    this.name = 'ApiError';
  }
}

let refreshInFlight: Promise<SessionTokens> | null = null;
const REQUEST_TIMEOUT_MS = 15_000;

async function fetchWithTimeout(url: string, init: RequestInit = {}): Promise<Response> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
  try {
    return await fetch(url, { ...init, signal: controller.signal });
  } catch (error) {
    if (controller.signal.aborted) {
      throw new ApiError('TrueCost could not reach the server in time. Check that your phone and computer are on the same Wi-Fi, then try again.', 0, 'timeout');
    }
    throw error;
  } finally {
    clearTimeout(timeout);
  }
}

async function parseError(response: Response) {
  const body = await response.json().catch(() => ({}));
  const detail = typeof body?.detail === 'string' ? body.detail : typeof body?.error?.message === 'string' ? body.error.message : undefined;
  return new ApiError(detail || (response.status >= 500 ? 'TrueCost is temporarily unavailable.' : 'Request could not be completed.'), response.status, body?.error?.code || body?.code);
}

async function refreshTokens(tokens: SessionTokens, writeTokens: TokenWriter) {
  if (!refreshInFlight) {
    refreshInFlight = fetchWithTimeout(`${BACKEND_URL}/api/v1/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
      body: JSON.stringify({ refresh_token: tokens.refresh_token }),
    }).then(async response => {
      if (!response.ok) throw await parseError(response);
      const next = await response.json() as SessionTokens;
      await writeTokens(next);
      return next;
    }).finally(() => { refreshInFlight = null; });
  }
  return refreshInFlight;
}

export async function api<T>(tokens: SessionTokens, writeTokens: TokenWriter, path: string, init: RequestInit = {}): Promise<T> {
  const run = (accessToken: string) => fetchWithTimeout(`${BACKEND_URL}/api/v1${path}`, {
    ...init,
    headers: {
      Accept: 'application/json',
      ...(init.body ? { 'Content-Type': 'application/json' } : {}),
      ...(init.headers || {}),
      Authorization: `Bearer ${accessToken}`,
    },
  });
  let response: Response;
  try {
    response = await run(tokens.access_token);
    if (response.status === 401) {
      const next = await refreshTokens(tokens, writeTokens);
      response = await run(next.access_token);
    }
  } catch (error) {
    if (error instanceof ApiError) throw error;
    throw new ApiError('Check your connection and try again.', 0, 'network_error');
  }
  if (!response.ok) throw await parseError(response);
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export async function publicApi<T>(path: string, init: RequestInit = {}): Promise<T> {
  let response: Response;
  try {
    response = await fetchWithTimeout(`${BACKEND_URL}/api/v1${path}`, {
      ...init,
      headers: { Accept: 'application/json', ...(init.body ? { 'Content-Type': 'application/json' } : {}), ...(init.headers || {}) },
    });
  } catch (error) {
    if (error instanceof ApiError) throw error;
    throw new ApiError('Check your connection and try again.', 0, 'network_error');
  }
  if (!response.ok) throw await parseError(response);
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}
