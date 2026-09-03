import { useEffect } from 'react';
import { useAuth } from '../auth/AuthContext';
import { registerPushNotifications } from './pushRegistration';

export default function PushRegistrationSync() {
  const { session, updateSession } = useAuth();
  useEffect(() => {
    if (session) void registerPushNotifications(session, updateSession, false).catch(() => {});
  }, [session, updateSession]);
  return null;
}
