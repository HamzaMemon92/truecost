import Constants from 'expo-constants';

const appEnvironment = process.env.EXPO_PUBLIC_APP_ENV || (__DEV__ ? 'development' : 'production');

function inferDevBackendUrl() {
  const constants = Constants as any;
  const hostUri =
    constants.expoConfig?.hostUri ||
    constants.manifest?.hostUri ||
    constants.debuggerHost ||
    constants.manifest?.debuggerHost ||
    constants.manifest2?.extra?.expoClient?.hostUri ||
    constants.manifest2?.extra?.expoClient?.debuggerHost ||
    constants.manifest2?.extra?.expoGo?.hostUri ||
    constants.manifest2?.extra?.expoGo?.debuggerHost ||
    constants.linkingUri ||
    '';
  const withoutScheme = String(hostUri).replace(/^[a-z][a-z0-9+.-]*:\/\//i, '');
  const host = withoutScheme.split(':')[0].split('/')[0].trim();
  if (host) return `http://${host}:8000`;
  return 'http://127.0.0.1:8000';
}

const configuredBackendUrl = process.env.EXPO_PUBLIC_API_URL;
export const BACKEND_URL = configuredBackendUrl && configuredBackendUrl !== 'auto'
  ? configuredBackendUrl
  : inferDevBackendUrl();
export const EAS_PROJECT_ID = process.env.EXPO_PUBLIC_EAS_PROJECT_ID || '';
export const API_BASE = `${BACKEND_URL}/api/v1/aggregator`;

export { PROVIDERS } from './catalog/providerManifest.generated';
import { PROVIDERS } from './catalog/providerManifest.generated';
export type Provider = typeof PROVIDERS[number];

export const CACHE_TTL_MS = 15 * 60 * 1000;

export default { environment: appEnvironment, apiOrigin: BACKEND_URL };
