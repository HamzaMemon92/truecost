import React, { useMemo, useState } from 'react';
import { Linking, StyleSheet, Text, View } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { AppHeader, Body, Card, Eyebrow, PrimaryButton, Screen, Title } from '../components/ui';
import { formatCurrency, tc } from '../design/tokens';
import { api } from '../api/client';
import { useAuth } from '../auth/AuthContext';

export default function CheckoutHandoffScreen({ route, navigation }: any) {
  const { session, updateSession } = useAuth();
  const { cart, product, offer, destination: requestedDestination } = route.params || {}; const [error, setError] = useState('');
  const item = cart?.items?.find((value: any) => value.source_url); const selected = offer || item || product || {};
  const destination = selected.source_url || selected.deepLink || null; const provider = selected.provider || 'Selected provider';
  const expected = offer?.price ?? cart?.estimated_total ?? product?.price ?? null;
  const observedAt = selected.observed_at || product?.observed_at || null;
  const disclosure = useMemo(() => cart ? 'This total includes stored item prices. Any provider fees, taxes, availability and payment offers are confirmed on the provider checkout.' : 'This is the latest supplied observation. Availability, fees and payment eligibility are confirmed by the provider.', [cart]);
  const openProvider = async () => {
    setError(''); if (!destination) return setError('No provider destination was supplied for this result.');
    try { const supported = await Linking.canOpenURL(destination); if (!supported) return setError('This provider link cannot be opened on this device.');
      if (session) await api(session, updateSession, '/commerce/handoffs', { method: 'POST', body: JSON.stringify({ provider, destination_url: destination, expected_total: expected, currency: cart?.currency || product?.currency || 'INR', source: route.params?.optimizationId ? 'cart_optimization' : 'comparison', reference_id: route.params?.optimizationId || product?.id || null }) });
      await Linking.openURL(destination); }
    catch { setError('The provider could not be opened. Try again from the comparison.'); }
  };
  return <Screen>
    <AppHeader subtitle="Final provider handoff" onBack={() => navigation.goBack()} />
    <Eyebrow style={styles.eyebrow}>FINAL PROVIDER HANDOFF</Eyebrow><Title size="h1">Review before you leave.</Title>
    <Card tone="iris" style={styles.hero}><View style={styles.providerIcon}><Feather name="external-link" size={24} color={tc.color.iris} /></View><View style={styles.heroCopy}><Text style={styles.heroLabel}>SELECTED PROVIDER</Text><Title size="h2">{provider}</Title></View></Card>
    <Card style={styles.breakdown}>
      <Row label={cart ? 'Observed item total' : 'Observed price'} value={formatCurrency(expected, cart?.currency || product?.currency || 'INR')} strong />
      {cart ? <Row label="Items" value={String(cart.item_count || cart.items?.length || 0)} /> : null}
      {selected.delivery ? <Row label="Delivery" value={String(selected.delivery)} /> : null}
      {requestedDestination ? <Row label="Destination" value={String(requestedDestination)} /> : null}
      {selected.payment_benefit ? <Row label="Payment benefit" value={String(selected.payment_benefit)} /> : null}
      <View style={styles.rule} /><Body muted>{disclosure}</Body>
    </Card>
    <Card tone={observedAt ? 'mint' : 'amber'} style={styles.freshness}><Feather name={observedAt ? 'clock' : 'alert-circle'} size={20} color={observedAt ? tc.color.mint : tc.color.amber} /><View style={styles.freshnessCopy}><Text style={styles.freshnessTitle}>{observedAt ? 'Observation timestamp supplied' : 'Freshness unavailable'}</Text><Body muted>{observedAt ? new Date(observedAt).toLocaleString() : 'Confirm the current price after opening the provider.'}</Body></View></Card>
    <Card tone="mint" style={styles.why}><Eyebrow>WHY THIS HANDOFF</Eyebrow><Body style={styles.whyBody}>{route.params?.reason || 'You selected this provider or offer from the available comparison. TrueCost does not guarantee the provider checkout price.'}</Body></Card>
    {error ? <Card tone="danger" style={styles.error}><Body style={styles.errorText}>{error}</Body></Card> : null}
    {/* Bug #9 fix: Warn the user when they've selected a non-recommended option */}
    {route.params?.notRecommended ? <Card tone="amber" style={styles.freshness}><Feather name="alert-triangle" size={20} color={tc.color.amber} /><View style={styles.freshnessCopy}><Text style={styles.freshnessTitle}>This is not the recommended option</Text><Body muted>Our analysis suggested a different provider offers better value. You can still proceed if you prefer.</Body></View></Card> : null}
    <PrimaryButton label={destination ? 'Open ' + provider : 'Provider link unavailable'} icon="external-link" disabled={!destination} onPress={() => void openProvider()} style={styles.primary} />
    <PrimaryButton label="Back to comparison" variant="outline" onPress={() => navigation.goBack()} style={styles.secondary} />
  </Screen>;
}
function Row({ label, value, strong }: { label: string; value: string; strong?: boolean }) { return <View style={styles.row}><Text style={styles.rowLabel}>{label}</Text><Text style={[styles.rowValue, strong && styles.rowStrong]}>{value}</Text></View>; }
const styles = StyleSheet.create({
  eyebrow: { marginTop: tc.space.md, marginBottom: tc.space.xs }, hero: { marginTop: tc.space.md, flexDirection: 'row', alignItems: 'center', gap: tc.space.md }, providerIcon: { width: 52, height: 52, borderRadius: 18, backgroundColor: tc.color.surface, alignItems: 'center', justifyContent: 'center' }, heroCopy: { flex: 1 }, heroLabel: { ...tc.type.eyebrow, color: tc.color.iris, marginBottom: 3 },
  breakdown: { marginTop: tc.space.md, gap: tc.space.sm }, row: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: tc.space.md }, rowLabel: { ...tc.type.bodySmall, color: tc.color.muted, flex: 1 }, rowValue: { ...tc.type.label, color: tc.color.ink, textAlign: 'right', fontVariant: ['tabular-nums'] }, rowStrong: { ...tc.type.h2 }, rule: { height: 1, backgroundColor: tc.color.line, marginVertical: tc.space.xs },
  freshness: { marginTop: tc.space.md, flexDirection: 'row', alignItems: 'center', gap: tc.space.sm }, freshnessCopy: { flex: 1 }, freshnessTitle: { ...tc.type.label, color: tc.color.ink }, why: { marginTop: tc.space.md }, whyBody: { marginTop: tc.space.xs }, error: { marginTop: tc.space.md }, errorText: { color: tc.color.danger }, primary: { marginTop: tc.space.lg }, secondary: { marginTop: tc.space.sm },
});
