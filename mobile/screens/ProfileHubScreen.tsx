import React from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { useAuth } from '../auth/AuthContext';
import { AppHeader, Body, Card, Eyebrow, PrimaryButton, Screen, SectionHeader, Title } from '../components/ui';
import { SystemState } from '../components/SystemState';
import { tc } from '../design/tokens';
import { useUserLocation } from '../location/LocationContext';
import { useApiQuery } from '../query/useApiQuery';

type Profile = { email: string | null; phone_number?: string | null; display_name?: string | null; preferences?: Record<string, unknown> };
type Summary = { saved_item_count: number; active_price_watch_count: number; cart_count: number };
export default function ProfileHubScreen({ navigation }: any) {
  const { session, isGuest, leaveGuest } = useAuth(); const { location, clearLocation } = useUserLocation();
  const profile = useApiQuery<Profile>('profile', '/profiles/me', { enabled: !!session }); const summary = useApiQuery<Summary>('dashboard', '/commerce/dashboard/summary', { enabled: !!session });
  if (!session && isGuest) return <Screen><AppHeader subtitle="Guest profile" /><Eyebrow style={styles.profileEyebrow}>GUEST PROFILE</Eyebrow><Title size="h1" style={styles.title}>Explore now. Save when ready.</Title><Body muted style={styles.lede}>A TrueCost account unlocks persistent carts, saved decisions, price watches and activity.</Body><Card tone="iris" style={styles.guestCard}><View style={styles.guestIcon}><Feather name="shield" size={23} color={tc.color.iris} /></View><View style={styles.guestCopy}><Title size="h3">Your search remains user-controlled</Title><Body muted>Sign in only when you want persistence and personalization.</Body></View></Card><PrimaryButton label="Sign in or create account" icon="arrow-right" onPress={() => void leaveGuest()} style={styles.guestCta} /><PrimaryButton label="Change location" variant="outline" icon="map-pin" onPress={clearLocation} style={styles.secondary} /></Screen>;
  if (profile.loading && !profile.data) return <Screen><SystemState kind="loading" /></Screen>;
  if (profile.error) return <Screen><SystemState kind="offline" actionLabel="Try again" onAction={() => void profile.refetch()} /></Screen>;
  const name = profile.data?.display_name?.trim() || 'Your profile'; const initial = name.charAt(0).toUpperCase();
  return <Screen><AppHeader subtitle="Your account and preferences" onNotifications={() => navigation.navigate('Notifications')} /><Eyebrow style={styles.profileEyebrow}>TRUECOST ID</Eyebrow><View style={styles.identity}><View style={styles.avatar}><Text style={styles.initial}>{initial}</Text></View><View style={styles.identityCopy}><Title size="h1">{name}</Title><Body muted>{profile.data?.email || profile.data?.phone_number || 'Verified account'}</Body></View><Pressable accessibilityRole="button" accessibilityLabel="Edit profile" onPress={() => navigation.navigate('ProfileEdit')} style={styles.edit}><Feather name="edit-3" size={18} color={tc.color.iris} /></Pressable></View>
    {summary.data ? <View style={styles.metrics}><Metric value={summary.data.saved_item_count} label="saved" /><Metric value={summary.data.active_price_watch_count} label="watches" /><Metric value={summary.data.cart_count} label="carts" /></View> : null}
    <Card tone="mint" style={styles.location}><View style={styles.locationIcon}><Feather name="map-pin" size={19} color={tc.color.mint} /></View><View style={styles.locationCopy}><Text style={styles.locationTitle}>Active location</Text><Body muted>{location?.display || location?.city || 'Location available for this session'}</Body></View><Pressable accessibilityRole="button" accessibilityLabel="Manage locations" onPress={() => navigation.navigate('LocationManagement')} style={styles.change}><Text style={styles.changeText}>Manage</Text></Pressable></Card>
    <SectionHeader title="Your decision tools" /><View style={styles.actions}>
      <Action icon="shopping-bag" title="Smart Cart" description="Edit quantities and compare again" onPress={() => navigation.navigate('Cart')} />
      <Action icon="bell" title="Notifications" description="Price-watch signals and updates" onPress={() => navigation.navigate('Notifications')} />
      <Action icon="heart" title="Watchlist" description="Targets and observed prices" onPress={() => navigation.navigate('Watchlist')} />
      <Action icon="clock" title="Activity" description="Your authenticated decision timeline" onPress={() => navigation.navigate('Activity')} />
      <Action icon="repeat" title="Comparison history" description="Provider evidence from past searches" onPress={() => navigation.navigate('ComparisonHistory')} />
      <Action icon="list" title="Saved lists" description="Private and shared shortlists" onPress={() => navigation.navigate('MainTabs', { screen: 'Saved' })} />
      <Action icon="map-pin" title="Saved locations" description="Addresses, active location and serviceability" onPress={() => navigation.navigate('LocationManagement')} />
      <Action icon="credit-card" title="Payment preferences" description="Masked method metadata only" onPress={() => navigation.navigate('PaymentPreferences')} />
      <Action icon="link" title="Connected accounts" description="Official provider connections and session status" onPress={() => navigation.navigate('ConnectedAccounts')} />
      <Action icon="camera" title="Scan & Compare" description="Barcode and user-confirmed package search" onPress={() => navigation.navigate('ScanCompare')} />
      <Action icon="shield" title="Privacy & security" description="Sessions, export and account controls" onPress={() => navigation.navigate('AccountSecurity')} />
      <Action icon="lock" title="App permissions" description="Location, alerts and camera consent" onPress={() => navigation.navigate('Permissions')} />
      <Action icon="help-circle" title="Help & support" description="Trust, FAQ and issue reporting" onPress={() => navigation.navigate('HelpSupport')} />
      <Action icon="settings" title="Settings" description="Preferences, privacy and session" onPress={() => navigation.navigate('Settings')} />
    </View>
  </Screen>;
}
function Metric({ value, label }: { value: number; label: string }) { return <Card style={styles.metric}><Text style={styles.metricValue}>{value}</Text><Text style={styles.metricLabel}>{label}</Text></Card>; }
function Action({ icon, title, description, onPress }: { icon: React.ComponentProps<typeof Feather>['name']; title: string; description: string; onPress: () => void }) { return <Pressable style={({ pressed }) => [styles.action, pressed && styles.pressed]} onPress={onPress}><View style={styles.actionIcon}><Feather name={icon} size={18} color={tc.color.iris} /></View><View style={styles.actionCopy}><Text style={styles.actionTitle}>{title}</Text><Text style={styles.actionDescription}>{description}</Text></View><Feather name="chevron-right" size={19} color={tc.color.muted} /></Pressable>; }
const styles = StyleSheet.create({
  profileEyebrow: { marginTop: tc.space.md }, title: { marginTop: 3 }, lede: { marginTop: tc.space.sm, fontSize: 14 }, guestCard: { marginTop: tc.space.lg, flexDirection: 'row', alignItems: 'center', gap: tc.space.md }, guestIcon: { width: 48, height: 48, borderRadius: 16, backgroundColor: tc.color.surface, alignItems: 'center', justifyContent: 'center' }, guestCopy: { flex: 1 }, guestCta: { marginTop: tc.space.lg }, secondary: { marginTop: tc.space.sm },
  identity: { flexDirection: 'row', alignItems: 'center', gap: tc.space.md, marginTop: tc.space.md }, avatar: { width: 58, height: 58, borderRadius: 20, backgroundColor: tc.color.iris, alignItems: 'center', justifyContent: 'center' }, initial: { color: tc.color.white, fontSize: 23, fontWeight: '800' }, identityCopy: { flex: 1 },
  edit: { width: 48, height: 48, borderRadius: tc.radius.md, borderWidth: 1, borderColor: tc.color.line, backgroundColor: tc.color.surface, alignItems: 'center', justifyContent: 'center' },
  metrics: { flexDirection: 'row', gap: tc.space.sm, marginTop: tc.space.lg }, metric: { flex: 1, padding: tc.space.sm }, metricValue: { ...tc.type.h2, color: tc.color.ink }, metricLabel: { ...tc.type.bodySmall, fontSize: 11, color: tc.color.muted },
  location: { marginTop: tc.space.md, flexDirection: 'row', alignItems: 'center', gap: tc.space.sm }, locationIcon: { width: 42, height: 42, borderRadius: 14, backgroundColor: tc.color.surface, alignItems: 'center', justifyContent: 'center' }, locationCopy: { flex: 1 }, locationTitle: { ...tc.type.label, color: tc.color.ink }, change: { minWidth: 52, minHeight: 44, alignItems: 'center', justifyContent: 'center' }, changeText: { ...tc.type.label, color: tc.color.mint },
  actions: { gap: tc.space.xs }, action: { minHeight: 72, flexDirection: 'row', alignItems: 'center', padding: tc.space.sm, gap: tc.space.sm, borderRadius: tc.radius.md, backgroundColor: tc.color.surface, borderWidth: 1, borderColor: tc.color.line }, actionIcon: { width: 42, height: 42, borderRadius: 14, backgroundColor: tc.color.irisSoft, alignItems: 'center', justifyContent: 'center' }, actionCopy: { flex: 1 }, actionTitle: { ...tc.type.label, color: tc.color.ink }, actionDescription: { ...tc.type.bodySmall, fontSize: 12, color: tc.color.muted }, pressed: { opacity: 0.72 },
});
