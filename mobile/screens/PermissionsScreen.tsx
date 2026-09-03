import React, { useEffect, useState } from 'react';
import { Linking, Platform, Pressable, StyleSheet, Text, View } from 'react-native';
import { Feather } from '@expo/vector-icons';
import * as Location from 'expo-location';
import { Camera } from 'expo-camera';
import { Body, Card, Eyebrow, IconButton, PrimaryButton, Screen, Title } from '../components/ui';
import { tc } from '../design/tokens';
import { useAuth } from '../auth/AuthContext';
import { registerPushNotifications } from '../notifications/pushRegistration';
import { isExpoGo } from '../notifications/runtime';

type State = 'granted' | 'denied' | 'undetermined' | 'unsupported';
export default function PermissionsScreen({ navigation }: any) {
  const { session, updateSession } = useAuth();
  const [states, setStates] = useState<Record<string, State>>({ location: 'undetermined', notifications: 'undetermined', camera: 'undetermined' });
  const [notice, setNotice] = useState('');
  const refresh = async () => {
    const notifications = isExpoGo
      ? { status: 'unsupported' as const }
      : await import('expo-notifications').then(module => module.getPermissionsAsync());
    const [location, camera] = await Promise.all([
      Location.getForegroundPermissionsAsync(),
      Camera.getCameraPermissionsAsync(),
    ]);
    setStates({ location: location.status as State, notifications: notifications.status as State, camera: camera.status as State });
  };
  useEffect(() => { void refresh(); }, []);
  const request = async (key: string) => {
    setNotice('');
    if (key === 'location') await Location.requestForegroundPermissionsAsync();
    else if (key === 'notifications') {
      if (isExpoGo) {
        setNotice('Remote push is unavailable in Expo Go. Use the TrueCost development build; in-app alerts remain available here.');
        return;
      }
      if (session) {
        const result = await registerPushNotifications(session, updateSession, true);
        if (result.status === 'not-configured') setNotice('Push delivery needs EXPO_PUBLIC_EAS_PROJECT_ID in the mobile environment.');
        else if (result.status === 'simulator') setNotice('Push tokens require a physical device.');
        else if (result.status === 'denied') setNotice('Notification permission was not allowed. You can change it in device settings.');
        else if (result.status === 'unsupported') setNotice('Remote push is unavailable in this runtime. In-app alerts remain available.');
      } else {
        const Notifications = await import('expo-notifications');
        await Notifications.requestPermissionsAsync();
      }
    } else await Camera.requestCameraPermissionsAsync();
    await refresh();
  };
  return <Screen><IconButton icon="arrow-left" label="Back" onPress={() => navigation.goBack()} /><Eyebrow style={styles.eyebrow}>PERMISSIONS</Eyebrow><Title size="display">You decide what the app can use.</Title><Body muted style={styles.intro}>Every capability is optional and requested in context. Search and comparison remain available with a manually entered location.</Body><View style={styles.list}><Permission icon="map-pin" title="Location" body="Find nearby serviceability and include your chosen area in relevant searches." state={states.location} onPress={() => void request('location')} /><Permission icon="bell" title="Notifications" body="Allow device alerts for watches and useful updates after backend observations." state={states.notifications} onPress={() => void request('notifications')} /><Permission icon="camera" title="Camera & scan" body="Scan barcodes only when you open Scan & Compare." state={states.camera} onPress={() => void request('camera')} /></View>{notice ? <Text accessibilityRole="alert" style={styles.notice}>{notice}</Text> : null}<Card tone="mint" style={styles.privacy}><Feather name="shield" size={21} color={tc.color.mint} /><View style={styles.privacyCopy}><Text style={styles.title}>Privacy by context</Text><Body muted>TrueCost does not need background location, full payment details, or continuous camera access.</Body></View></Card>{Platform.OS !== 'web' ? <PrimaryButton label="Open device settings" variant="outline" icon="settings" onPress={() => void Linking.openSettings()} style={styles.settings} /> : null}</Screen>;
}
function Permission({ icon, title, body, state, onPress }: { icon: React.ComponentProps<typeof Feather>['name']; title: string; body: string; state: State; onPress: () => void }) { const granted = state === 'granted'; const unsupported = state === 'unsupported'; return <Card style={styles.item}><View style={[styles.icon, granted && styles.iconGranted]}><Feather name={granted ? 'check' : icon} size={21} color={granted ? tc.color.mint : tc.color.iris} /></View><View style={styles.copy}><Text style={styles.title}>{title}</Text><Body muted>{body}</Body><Text style={[styles.status, granted && styles.statusGranted]}>{granted ? 'Allowed' : state === 'denied' ? 'Not allowed' : unsupported ? 'Development build required' : 'Not requested'}</Text></View><Pressable accessibilityRole="button" accessibilityLabel={`${granted ? 'Review' : unsupported ? 'About' : 'Allow'} ${title}`} onPress={onPress} style={styles.allow}><Text style={styles.allowText}>{granted ? 'Review' : unsupported ? 'About' : 'Allow'}</Text></Pressable></Card>; }
const styles = StyleSheet.create({ eyebrow: { marginTop: tc.space.lg, marginBottom: tc.space.xs }, intro: { marginTop: tc.space.sm }, list: { gap: tc.space.sm, marginTop: tc.space.lg }, item: { flexDirection: 'row', alignItems: 'center', gap: tc.space.sm }, icon: { width: 48, height: 48, borderRadius: 17, backgroundColor: tc.color.irisSoft, alignItems: 'center', justifyContent: 'center' }, iconGranted: { backgroundColor: tc.color.mintSoft }, copy: { flex: 1 }, title: { ...tc.type.label, color: tc.color.ink, marginBottom: 2 }, status: { ...tc.type.eyebrow, color: tc.color.amber, marginTop: 6 }, statusGranted: { color: tc.color.mint }, allow: { minWidth: 54, minHeight: 48, justifyContent: 'center', alignItems: 'center' }, allowText: { ...tc.type.label, color: tc.color.iris }, notice: { ...tc.type.bodySmall, color: tc.color.amber, marginTop: tc.space.sm }, privacy: { flexDirection: 'row', gap: tc.space.sm, marginTop: tc.space.lg }, privacyCopy: { flex: 1 }, settings: { marginTop: tc.space.md } });
