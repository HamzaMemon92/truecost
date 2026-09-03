import Constants from 'expo-constants';

/**
 * Android remote notifications are intentionally unavailable in Expo Go as of
 * SDK 53. Keep this check in a module that never imports expo-notifications so
 * the native package is not evaluated before we can choose the safe path.
 */
export const isExpoGo =
  Constants.appOwnership === 'expo' ||
  Constants.executionEnvironment === 'storeClient';

