import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { Deal, DealsResponse, getDeals } from '../api/deals';
import { ProviderHealthPanel } from '../components/ProviderHealthPanel';
import { AppHeader, Body, Card, Field, PrimaryButton, Screen, SectionHeader } from '../components/ui';
import { SystemState } from '../components/SystemState';
import { CategoryHero, SelectionRow, SourceBadge } from '../features/categories/components';
import { tc } from '../design/tokens';

export default function FinanceScreen({ navigation, route }: any) {
  const [purchase, setPurchase] = useState(route.params?.initialQuery || ''); const [method, setMethod] = useState('Any method'); const [data, setData] = useState<DealsResponse | null>(null); const [loading, setLoading] = useState(true); const [error, setError] = useState(false);
  const load = useCallback(async () => { setLoading(true); setError(false); try { setData(await getDeals('Finance')); } catch { setError(true); } finally { setLoading(false); } }, []);
  useEffect(() => { void load(); }, [load]);
  const offers = useMemo(() => (data?.deals || []).filter(item => { const queryMatch = !purchase.trim() || `${item.title} ${item.provider}`.toLowerCase().includes(purchase.trim().toLowerCase()); const methodMatch = method === 'Any method' || item.payment_method?.toLowerCase().includes(method.toLowerCase()); return queryMatch && methodMatch; }), [data, method, purchase]);
  return <Screen>
    <AppHeader
      title="Finance TrueCost"
      subtitle="Observed payment offers & card discounts"
      onBack={() => navigation.goBack()}
      onNotifications={() => navigation.navigate('Notifications')}
      onProfile={() => navigation.navigate('Profile')}
    />
    <CategoryHero eyebrow="FINANCE / PAYMENT INTELLIGENCE" title="Pay with context, not guesswork." body="This surface uses the existing Deals client for observed finance offers. No full card number, CVV, bank password, or UPI PIN is requested." icon="credit-card" />
    <ProviderHealthPanel categoryId="finance" title="Finance provider readiness" />
    <View style={styles.metrics}><Card tone="mint" style={styles.metric}><Text style={styles.metricLabel}>OBSERVED OFFERS</Text><Text style={styles.metricValue}>{data?.total ?? '—'}</Text><Body muted>From persisted results</Body></Card><Card tone="iris" style={styles.metric}><Text style={styles.metricLabel}>VERIFIED SAVINGS</Text><Text style={styles.metricValue}>—</Text><Body muted>No ledger endpoint</Body></Card></View>
    <Card style={styles.form}><Field label="Filter by purchase or provider" value={purchase} onChangeText={setPurchase} icon="shopping-bag" placeholder="Flight, grocery, provider…" /></Card>
    <SectionHeader title="Preferred method" /><SelectionRow values={['Any method', 'Card', 'UPI', 'Wallet', 'Net banking']} selected={method} onSelect={setMethod} />
    {loading ? <SystemState kind="checking_offers" compact /> : error ? <SystemState kind="offline" actionLabel="Try again" onAction={() => void load()} /> : <><SourceBadge source={data?.deals[0]?.data_source || 'ingested_provider_result'} generatedAt={data?.generated_at} /><SectionHeader title="Observed finance offers" />{offers.length ? offers.map(deal => <FinanceOffer key={deal.id} deal={deal} onPress={() => navigation.navigate('DealDetail', { deal, disclaimer: data?.disclaimer, generatedAt: data?.generated_at })} />) : <SystemState kind="empty" actionLabel="Clear filters" onAction={() => { setPurchase(''); setMethod('Any method'); }} />}</>}
    <SectionHeader title="Payment methods & benefits" /><Card><Method icon="credit-card" title="Cards" body="Only issuer, network, and masked last four digits may be retained when supported." /><Method icon="smartphone" title="UPI" body="Recommendations never require a UPI PIN or bank credential." /><Method icon="pocket" title="Wallets & net banking" body="Eligibility is confirmed at provider checkout." /></Card>
    <Card tone="amber" style={styles.safety}><Feather name="shield" size={19} color={tc.color.amber} /><View style={styles.grow}><Text style={styles.safetyTitle}>Capability boundary</Text><Body muted>The repository has no typed payment-ranking or savings-ledger API yet. TrueCost therefore shows observed finance deals without inventing a best card or effective savings.</Body></View></Card>
  </Screen>;
}
function FinanceOffer({ deal, onPress }: { deal: Deal; onPress(): void }) { return <PrimaryButton label={`${deal.provider}: ${deal.title}`} variant="outline" onPress={onPress} style={styles.offer} />; }
function Method({ icon, title, body }: { icon: React.ComponentProps<typeof Feather>['name']; title: string; body: string }) { return <View style={styles.method}><View style={styles.methodIcon}><Feather name={icon} size={18} color={tc.color.iris} /></View><View style={styles.grow}><Text style={styles.methodTitle}>{title}</Text><Body muted>{body}</Body></View></View>; }
const styles = StyleSheet.create({ metrics: { flexDirection: 'row', gap: tc.space.sm, marginTop: tc.space.lg }, metric: { flex: 1 }, metricLabel: { ...tc.type.eyebrow, color: tc.color.muted }, metricValue: { ...tc.type.price, color: tc.color.ink, marginVertical: 2 }, form: { marginTop: tc.space.md }, offer: { marginTop: tc.space.xs, justifyContent: 'flex-start' }, method: { flexDirection: 'row', gap: tc.space.sm, paddingVertical: tc.space.sm, borderBottomWidth: 1, borderBottomColor: tc.color.line }, methodIcon: { width: 42, height: 42, borderRadius: 14, backgroundColor: tc.color.irisSoft, alignItems: 'center', justifyContent: 'center' }, methodTitle: { ...tc.type.label, color: tc.color.ink, marginBottom: 2 }, grow: { flex: 1 }, safety: { marginTop: tc.space.md, flexDirection: 'row', gap: tc.space.sm }, safetyTitle: { ...tc.type.label, color: tc.color.ink, marginBottom: 2 } });
