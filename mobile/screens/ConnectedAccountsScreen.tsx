import React, { useEffect, useMemo, useState } from 'react';
import { Alert, Modal, Pressable, StyleSheet, Text, View } from 'react-native';
import { Feather } from '@expo/vector-icons';
import * as WebBrowser from 'expo-web-browser';
import { useAuth } from '../auth/AuthContext';
import { ApiError } from '../api/client';
import {
  cacheProviderConnections,
  completeProviderConnection,
  disconnectProvider,
  ProviderConnection,
  ProviderConnectionCallback,
  readCachedProviderConnections,
  startProviderConnection,
} from '../api/providerConnections';
import { Body, Card, Chip, IconButton, PrimaryButton, Screen, Title, Eyebrow } from '../components/ui';
import { SystemState } from '../components/SystemState';
import { tc } from '../design/tokens';
import { useApiQuery } from '../query/useApiQuery';
import { useQueryClient } from '../query/QueryClient';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

WebBrowser.maybeCompleteAuthSession();

type Filter = 'All' | 'Connected' | 'Shopping' | 'Grocery' | 'Food & Grocery' | 'Mobility';
const FILTERS: Filter[] = ['All', 'Connected', 'Shopping', 'Grocery', 'Food & Grocery', 'Mobility'];

export default function ConnectedAccountsScreen({ navigation }: { navigation: any }) {
  const { session, updateSession } = useAuth();
  const insets = useSafeAreaInsets();
  const cache = useQueryClient();
  const query = useApiQuery<ProviderConnection[]>('provider-connections', '/provider-connections', { enabled: !!session, maxAge: 8_000 });
  const [offlineCache, setOfflineCache] = useState<ProviderConnection[]>([]);
  const [filter, setFilter] = useState<Filter>('All');
  const [selected, setSelected] = useState<ProviderConnection | null>(null);
  const [connecting, setConnecting] = useState('');
  const [message, setMessage] = useState('');

  useEffect(() => { if (session?.user_id) void readCachedProviderConnections(session.user_id).then(setOfflineCache); }, [session?.user_id]);
  useEffect(() => { if (query.data && session?.user_id) { setOfflineCache(query.data); void cacheProviderConnections(session.user_id, query.data); } }, [query.data, session?.user_id]);
  const providers = query.data || offlineCache;
  const visible = useMemo(() => providers.filter(provider => filter === 'All' || (filter === 'Connected' ? provider.status === 'connected' : provider.category === filter)), [filter, providers]);
  const connectedCount = providers.filter(provider => provider.status === 'connected').length;

  const refresh = async () => { cache.invalidate('provider-connections'); await query.refetch(); };
  const beginConnection = async () => {
    if (!selected || !session || !selected.connection_supported) return;
    const provider = selected;
    setSelected(null); setConnecting(provider.id); setMessage('');
    try {
      const start = await startProviderConnection(session, updateSession, provider.id);
      const result = await WebBrowser.openAuthSessionAsync(start.authorization_url, start.callback_url, { showInRecents: true });
      if (result.type !== 'success' || !result.url) {
        setMessage(`${provider.name} connection was cancelled. No account data was saved.`);
        return;
      }
      const callbackUrl = new URL(result.url);
      const callback: ProviderConnectionCallback = {
        provider_id: callbackUrl.searchParams.get('provider_id') || callbackUrl.searchParams.get('provider') || '',
        state: callbackUrl.searchParams.get('state') || '',
        result: (callbackUrl.searchParams.get('result') || 'cancelled') as ProviderConnectionCallback['result'],
        account_label: callbackUrl.searchParams.get('account_label'),
        expires_at: callbackUrl.searchParams.get('expires_at'),
        signature: callbackUrl.searchParams.get('signature') || '',
      };
      if (callback.provider_id !== provider.id || !['connected', 'expired', 'cancelled'].includes(callback.result)) throw new Error('The provider returned an invalid connection result.');
      await completeProviderConnection(session, updateSession, callback);
      await refresh();
      setMessage(callback.result === 'connected' ? `${provider.name} is connected.` : callback.result === 'expired' ? `${provider.name} needs to be connected again.` : `${provider.name} connection was cancelled.`);
    } catch (cause) {
      setMessage(cause instanceof ApiError ? cause.message : cause instanceof Error ? cause.message : 'The provider connection could not be verified.');
    } finally { setConnecting(''); }
  };

  const remove = (provider: ProviderConnection) => Alert.alert(
    `Disconnect ${provider.name}?`,
    'This removes the TrueCost connection record. You can also revoke TrueCost from the provider’s own account-security page.',
    [{ text: 'Keep connected', style: 'cancel' }, { text: 'Disconnect', style: 'destructive', onPress: () => {
      if (!session) return;
      setConnecting(provider.id);
      void disconnectProvider(session, updateSession, provider.id).then(refresh).catch(cause => setMessage(cause instanceof Error ? cause.message : 'Could not disconnect provider.')).finally(() => setConnecting(''));
    } }],
  );

  return <>
    <Screen>
      <View style={styles.header}><IconButton icon="arrow-left" label="Back" onPress={() => navigation.goBack()} /><View style={styles.headerCopy}><Eyebrow>PERSONALIZED PROVIDERS</Eyebrow><Title size="h1">Connected accounts</Title></View></View>
      <Body muted style={styles.lede}>Connect only through an approved provider authorization flow. TrueCost never reads passwords, OTPs, browser cookies or full account sessions.</Body>
      <Card tone="mint" style={styles.summary}><View style={styles.summaryIcon}><Feather name="shield" size={22} color={tc.color.mint} /></View><View style={styles.summaryCopy}><Text style={styles.summaryValue}>{connectedCount} connected</Text><Body muted>Connection status is synchronized with your TrueCost account. This device caches non-secret status only.</Body></View></Card>
      <View style={styles.filters}>{FILTERS.map(value => <Chip key={value} label={value} selected={filter === value} onPress={() => setFilter(value)} />)}</View>
      {message ? <Card tone={message.includes('connected.') ? 'mint' : 'amber'} style={styles.message}><Feather name="info" size={18} color={message.includes('connected.') ? tc.color.mint : tc.color.amber} /><Body style={styles.messageText}>{message}</Body></Card> : null}
      {query.loading && !providers.length ? <SystemState kind="loading" /> : query.error && !providers.length ? <SystemState kind="offline" actionLabel="Try again" onAction={() => void refresh()} /> : !visible.length ? <SystemState kind="empty_saved" /> : <View style={styles.grid}>{visible.map(provider => <ProviderCard key={provider.id} provider={provider} connecting={connecting === provider.id} onConnect={() => setSelected(provider)} onDisconnect={() => remove(provider)} />)}</View>}
      <Card tone="amber" style={styles.boundary}><Feather name="lock" size={19} color={tc.color.amber} /><View style={styles.boundaryCopy}><Text style={styles.boundaryTitle}>What connection means</Text><Body muted>A connected badge appears only after a signed backend callback from an approved OAuth broker. Comparison availability does not imply account-login support.</Body></View></Card>
    </Screen>
    <Modal visible={!!selected} transparent animationType="fade" onRequestClose={() => setSelected(null)}>
      <View style={styles.modalRoot}><Pressable accessibilityRole="button" accessibilityLabel="Close connection dialog" style={styles.scrim} onPress={() => setSelected(null)} /><View accessibilityViewIsModal style={[styles.sheet, { paddingBottom: Math.max(insets.bottom, tc.space.lg) }]}>
        {selected ? <><View style={styles.sheetHandle} /><BrandMark provider={selected} large /><Title size="h2" style={styles.sheetTitle}>{selected.connection_supported ? `Continue to ${selected.name}` : `${selected.name} connection unavailable`}</Title>
          <Body muted style={styles.sheetBody}>{selected.connection_supported ? `A secure system browser will open ${selected.name}’s approved authorization flow. Sign-in details stay with the provider.` : 'This environment does not have an approved provider OAuth broker configured. Comparison can still work from observed provider data.'}</Body>
          <Card tone="mint" style={styles.disclosure}><Feather name="check-circle" size={18} color={tc.color.mint} /><Body style={styles.disclosureText}>TrueCost stores connection status and a masked account label only—never passwords, OTPs or reusable cookies.</Body></Card>
          {selected.connection_supported ? <PrimaryButton label={`Continue to ${selected.name}`} icon="external-link" onPress={() => void beginConnection()} style={styles.sheetAction} /> : <PrimaryButton label="Got it" onPress={() => setSelected(null)} style={styles.sheetAction} />}
          <PrimaryButton label="Cancel" variant="outline" onPress={() => setSelected(null)} style={styles.sheetCancel} /></> : null}
      </View></View>
    </Modal>
  </>;
}

function ProviderCard({ provider, connecting, onConnect, onDisconnect }: { provider: ProviderConnection; connecting: boolean; onConnect: () => void; onDisconnect: () => void }) {
  const status = connecting ? 'connecting' : provider.status;
  const label = status === 'connected' ? 'Connected' : status === 'expired' ? 'Session expired' : status === 'connecting' ? 'Connecting' : 'Disconnected';
  const tone = status === 'connected' ? styles.statusConnected : status === 'expired' ? styles.statusExpired : status === 'connecting' ? styles.statusConnecting : styles.statusDisconnected;
  return <Card style={[styles.provider, status === 'connected' && styles.providerConnected]}>
    <View style={styles.providerTop}><BrandMark provider={provider} /><View style={styles.providerCopy}><Text style={styles.providerName}>{provider.name}</Text><Text style={styles.providerCategory}>{provider.category}</Text></View><View accessibilityLabel={`${provider.name}: ${label}`} style={[styles.status, tone]}><View style={[styles.statusDot, status === 'connected' ? styles.dotConnected : status === 'expired' ? styles.dotExpired : styles.dotIdle]} /><Text style={[styles.statusText, status === 'connected' && styles.statusTextConnected, status === 'expired' && styles.statusTextExpired]}>{label}</Text></View></View>
    {provider.account_label && status === 'connected' ? <Text style={styles.accountLabel}>{provider.account_label}</Text> : null}
    <View style={styles.providerActions}>{status === 'connected' ? <><PrimaryButton label="Connected" icon="check" variant="mint" disabled style={styles.cardAction} /><Pressable accessibilityRole="button" accessibilityLabel={`Disconnect ${provider.name}`} onPress={onDisconnect} style={styles.moreButton}><Feather name="more-horizontal" size={20} color={tc.color.muted} /></Pressable></> : <PrimaryButton label={status === 'expired' ? 'Reconnect securely' : provider.connection_supported ? 'Connect securely' : 'Review availability'} icon={provider.connection_supported ? 'external-link' : 'info'} variant="outline" loading={connecting} onPress={onConnect} style={styles.cardAction} />}</View>
  </Card>;
}

function BrandMark({ provider, large = false }: { provider: ProviderConnection; large?: boolean }) {
  const lightBackground = provider.id === 'blinkit' || provider.id === 'rapido';
  return <View accessibilityLabel={`${provider.name} brand mark`} style={[styles.brand, large && styles.brandLarge, { backgroundColor: provider.brand_color }]}><Text style={[styles.brandText, large && styles.brandTextLarge, lightBackground && styles.brandTextDark]}>{provider.mark}</Text></View>;
}

const styles = StyleSheet.create({
  header: { flexDirection: 'row', alignItems: 'center', gap: tc.space.sm }, headerCopy: { flex: 1 }, lede: { marginTop: tc.space.md, fontSize: 15 },
  summary: { marginTop: tc.space.lg, flexDirection: 'row', alignItems: 'center', gap: tc.space.sm }, summaryIcon: { width: 48, height: 48, borderRadius: 16, backgroundColor: tc.color.surface, alignItems: 'center', justifyContent: 'center' }, summaryCopy: { flex: 1 }, summaryValue: { ...tc.type.h3, color: tc.color.ink },
  filters: { flexDirection: 'row', flexWrap: 'wrap', gap: tc.space.xs, marginTop: tc.space.lg }, message: { marginTop: tc.space.md, flexDirection: 'row', gap: tc.space.sm }, messageText: { flex: 1 }, grid: { gap: tc.space.sm, marginTop: tc.space.md },
  provider: { padding: tc.space.md }, providerConnected: { borderColor: '#BDE8D9' }, providerTop: { flexDirection: 'row', alignItems: 'center', gap: tc.space.sm }, providerCopy: { flex: 1 }, providerName: { ...tc.type.h3, color: tc.color.ink }, providerCategory: { ...tc.type.bodySmall, fontSize: 12, color: tc.color.muted },
  brand: { width: 48, height: 48, borderRadius: 16, alignItems: 'center', justifyContent: 'center' }, brandLarge: { width: 64, height: 64, borderRadius: 21, alignSelf: 'center' }, brandText: { fontSize: 23, lineHeight: 27, fontWeight: '900', color: tc.color.white }, brandTextLarge: { fontSize: 30, lineHeight: 34 }, brandTextDark: { color: tc.color.ink },
  status: { minHeight: 32, borderRadius: tc.radius.pill, paddingHorizontal: 9, flexDirection: 'row', alignItems: 'center', gap: 5, borderWidth: 1 }, statusConnected: { backgroundColor: tc.color.mintSoft, borderColor: '#BDE8D9' }, statusExpired: { backgroundColor: tc.color.amberSoft, borderColor: '#F4D5AF' }, statusConnecting: { backgroundColor: tc.color.irisSoft, borderColor: '#DAD2FF' }, statusDisconnected: { backgroundColor: tc.color.surfaceMuted, borderColor: tc.color.line }, statusDot: { width: 7, height: 7, borderRadius: 4 }, dotConnected: { backgroundColor: tc.color.mint }, dotExpired: { backgroundColor: tc.color.amber }, dotIdle: { backgroundColor: tc.color.muted }, statusText: { ...tc.type.eyebrow, letterSpacing: 0.4, color: tc.color.muted }, statusTextConnected: { color: tc.color.mint }, statusTextExpired: { color: tc.color.amber },
  accountLabel: { ...tc.type.bodySmall, color: tc.color.inkSoft, marginTop: tc.space.sm }, providerActions: { marginTop: tc.space.sm, flexDirection: 'row', alignItems: 'center', gap: tc.space.xs }, cardAction: { flex: 1, minHeight: 48 }, moreButton: { width: 48, height: 48, borderRadius: tc.radius.md, borderWidth: 1, borderColor: tc.color.line, alignItems: 'center', justifyContent: 'center' },
  boundary: { marginTop: tc.space.lg, flexDirection: 'row', gap: tc.space.sm }, boundaryCopy: { flex: 1 }, boundaryTitle: { ...tc.type.label, color: tc.color.ink },
  modalRoot: { flex: 1, justifyContent: 'flex-end' }, scrim: { position: 'absolute', top: 0, right: 0, bottom: 0, left: 0, backgroundColor: tc.color.scrim }, sheet: { backgroundColor: tc.color.surface, borderTopLeftRadius: tc.radius.xl, borderTopRightRadius: tc.radius.xl, paddingHorizontal: tc.space.lg, paddingTop: tc.space.sm, paddingBottom: tc.space.xl }, sheetHandle: { width: 42, height: 4, borderRadius: 2, backgroundColor: tc.color.lineStrong, alignSelf: 'center', marginBottom: tc.space.lg }, sheetTitle: { textAlign: 'center', marginTop: tc.space.md }, sheetBody: { textAlign: 'center', marginTop: tc.space.sm }, disclosure: { flexDirection: 'row', gap: tc.space.sm, marginTop: tc.space.lg }, disclosureText: { color: tc.color.mint, flex: 1 }, sheetAction: { marginTop: tc.space.lg }, sheetCancel: { marginTop: tc.space.xs },
});
