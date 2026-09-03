import React, { createContext, useContext, useEffect, useMemo, useState } from 'react';
import { AccessibilityInfo } from 'react-native';
import { api } from '../api/client';
import { useAuth } from '../auth/AuthContext';

type Experience = { reduceMotion: boolean; largerText: boolean; highContrast: boolean; screenReader: boolean };
const Context = createContext<Experience>({ reduceMotion: false, largerText: false, highContrast: false, screenReader: false });

export function ExperienceProvider({ children }: { children: React.ReactNode }) {
  const { session, updateSession } = useAuth(); const [systemReduce, setSystemReduce] = useState(false); const [screenReader, setScreenReader] = useState(false);
  const [preferences, setPreferences] = useState({ reduced_motion: false, larger_text: false, high_contrast: false });
  useEffect(() => { void AccessibilityInfo.isReduceMotionEnabled().then(setSystemReduce); void AccessibilityInfo.isScreenReaderEnabled().then(setScreenReader); const motion = AccessibilityInfo.addEventListener('reduceMotionChanged', setSystemReduce); const reader = AccessibilityInfo.addEventListener('screenReaderChanged', setScreenReader); return () => { motion.remove(); reader.remove(); }; }, []);
  useEffect(() => { if (!session) { setPreferences({ reduced_motion: false, larger_text: false, high_contrast: false }); return; } api<{ preferences?: { accessibility?: typeof preferences } }>(session, updateSession, '/profiles/me').then(profile => setPreferences(value => ({ ...value, ...(profile.preferences?.accessibility || {}) }))).catch(() => {}); }, [session?.access_token]);
  const value = useMemo(() => ({ reduceMotion: systemReduce || preferences.reduced_motion, largerText: preferences.larger_text, highContrast: preferences.high_contrast, screenReader }), [systemReduce, preferences, screenReader]);
  return <Context.Provider value={value}>{children}</Context.Provider>;
}
export const useExperience = () => useContext(Context);
