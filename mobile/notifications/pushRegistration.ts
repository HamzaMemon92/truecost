import { Platform } from 'react-native';
import * as Device from 'expo-device';
import Constants from 'expo-constants';
import { api, SessionTokens, TokenWriter } from '../api/client';
import { EAS_PROJECT_ID } from '../config';
import { isExpoGo } from './runtime';

export type PushRegistrationResult =
  | { status: 'registered' }
  | { status: 'denied' | 'simulator' | 'not-configured' | 'unsupported' };

export async function registerPushNotifications(
  tokens: SessionTokens,
  writeTokens: TokenWriter,
  requestPermission: boolean,
): Promise<PushRegistrationResult> {
  if (Platform.OS === 'web') return { status: 'unsupported' };
  if (!Device.isDevice) return { status: 'simulator' };
  if (isExpoGo) return { status: 'unsupported' };

  // Import only after the Expo Go guard. Importing expo-notifications itself
  // initializes Android push APIs that no longer exist in Expo Go (SDK 53+).
  const Notifications = await import('expo-notifications');

  if (Platform.OS === 'android') {
    await Notifications.setNotificationChannelAsync('truecost-alerts', {
      name: 'Price and savings alerts',
      importance: Notifications.AndroidImportance.HIGH,
      vibrationPattern: [0, 220, 180, 220],
      lightColor: '#6254E8',
    });
  }

  let permission = await Notifications.getPermissionsAsync();
  if (permission.status !== 'granted' && requestPermission) permission = await Notifications.requestPermissionsAsync();
  if (permission.status !== 'granted') return { status: 'denied' };
  const projectId = EAS_PROJECT_ID || Constants.easConfig?.projectId || (Constants.expoConfig?.extra?.eas?.projectId as string | undefined);
  if (!projectId) return { status: 'not-configured' };

  const token = await Notifications.getExpoPushTokenAsync({ projectId });
  await api(tokens, writeTokens, '/auth/push-tokens', {
    method: 'POST',
    body: JSON.stringify({
      expo_push_token: token.data,
      platform: Platform.OS,
      device_name: Device.deviceName || undefined,
    }),
  });
  return { status: 'registered' };
}
