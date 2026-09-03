import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { Deal, DealsResponse, getDeals } from '../api/deals';
import { ProviderHealthPanel } from '../components/ProviderHealthPanel';
import { AppHeader, Body, Card, Field, PrimaryButton, Screen, SectionHeader } from '../components/ui';
import { SystemState } from '../components/SystemState';
import { CategoryHero, SelectionRow, SourceBadge } from '../features/categories/components';
import { tc } from '../design/tokens';

export default function DealsScreen({ navigation, route }: any) {
  const [query, setQuery] = useState(route.params?.initialQuery || ''); const [category, setCategory] = useState('All'); const [lens, setLens] = useState('All observed');
  const [data, setData] = useState<DealsResponse | null>(null); const [loading, setLoading] = useState(true); const [error, setError] = useState(false);
  const load = useCallback(async () => { setLoading(true); setError(false); try { setData(await getDeals(category === 'All' ? undefined : category)); } catch { setError(true); } finally { setLoading(false); } }, [category]);
  useEffect(() => { void load(); }, [load]);
  const deals = useMemo(() => (data?.deals || []).filter(deal => {
    const matchesQuery = !query.trim() || `${deal.title} ${deal.provider}`.toLowerCase().includes(query.trim().toLowerCase());
    const matchesLens = lens === 'All observed' || (lens === 'Cashback' && !!(deal.cashback_pct || deal.cashback_amount)) || (lens === 'Expiring soon' && deal.is_expiring_soon);
    return matchesQuery && matchesLens;
  }), [data, lens, query]);
  return <Screen>
    <AppHeader
      title="Deals TrueCost"
      subtitle="Verified price drops & cashbacks"
      onBack={() => navigation.goBack()}
      onNotifications={() => navigation.navigate('Notifications')}
      onProfile={() => navigation.navigate('Profile')}
    />
    <CategoryHero eyebrow="DEALS / OBSERVED OFFERS" title="Worth it, not just discounted." body="Deals come from persisted provider observations. The client no longer contains fabricated promotional cards." icon="tag" />
    <ProviderHealthPanel categoryId="deals" title="Deals provider readiness" />
    <Card tone="iris" style={styles.search}><Field label="Filter observed deals" value={query} onChangeText={setQuery} icon="search" placeholder="Product or provider" /></Card>
    <SectionHeader title="Category" /><SelectionRow values={['All', 'Grocery', 'Shopping', 'Mobility', 'Travel', 'Finance']} selected={category} onSelect={setCategory} />
    <SectionHeader title="Offer lens" /><SelectionRow values={['All observed', 'Cashback', 'Expiring soon']} selected={lens} onSelect={setLens} />
    {loading ? <SystemState kind="checking_offers" compact /> : error ? <SystemState kind="offline" actionLabel="Try again" onAction={() => void load()} /> : <>
      <SourceBadge source={data?.deals[0]?.data_source || 'ingested_provider_result'} generatedAt={data?.generated_at} />
      <SectionHeader title="Observed offers" />
      {deals.length ? deals.map(deal => <DealCard key={deal.id} deal={deal} onPress={() => navigation.navigate('DealDetail', { deal, disclaimer: data?.disclaimer, generatedAt: data?.generated_at })} />) : (
        // Bug #8 fix: Show an explicit empty state when the filter yields no results
        query.trim() || lens !== 'All observed' || category !== 'All'
          ? <SystemState kind="empty" actionLabel="Clear filters" onAction={() => { setQuery(''); setCategory('All'); setLens('All observed'); }} />
          : <SystemState kind="empty" actionLabel="Refresh" onAction={() => void load()} />
      )}
      {data?.disclaimer ? <Card tone="amber" style={styles.disclaimer}><Body muted>{data.disclaimer}</Body></Card> : null}
    </>}
    <SectionHeader title="Personalized deals" /><Card><Body muted>Personalization remains empty until the backend returns an authenticated eligibility contract. No offer is inferred from private financial information.</Body></Card>
  </Screen>;
}
function DealCard({ deal, onPress }: { deal: Deal; onPress(): void }) { const value = deal.discount_pct != null ? `${deal.discount_pct}% observed discount` : deal.cashback_pct != null ? `${deal.cashback_pct}% cashback` : deal.cashback_amount != null ? `₹${deal.cashback_amount} cashback` : 'Observed offer'; return <Pressable accessibilityRole="button" accessibilityLabel={`Open ${deal.title}`} style={({ pressed }) => [styles.dealPress, pressed && styles.pressed]} onPress={onPress}><Card style={styles.deal}><View style={styles.dealIcon}><Feather name="tag" size={18} color={tc.color.iris} /></View><View style={styles.grow}><Text style={styles.provider}>{deal.provider}</Text><Text style={styles.dealTitle}>{deal.title}</Text><Text style={styles.value}>{value}</Text>{deal.is_expiring_soon ? <Text style={styles.expiring}>EXPIRING SOON</Text> : null}</View><Feather name="chevron-right" size={20} color={tc.color.muted} /></Card></Pressable>; }
const styles = StyleSheet.create({ search: { marginTop: tc.space.lg }, dealPress: { marginTop: tc.space.sm }, deal: { flexDirection: 'row', alignItems: 'center', gap: tc.space.sm }, dealIcon: { width: 44, height: 44, borderRadius: 15, backgroundColor: tc.color.irisSoft, alignItems: 'center', justifyContent: 'center' }, grow: { flex: 1 }, provider: { ...tc.type.eyebrow, color: tc.color.mint }, dealTitle: { ...tc.type.h3, color: tc.color.ink, marginTop: 2 }, value: { ...tc.type.label, color: tc.color.iris, marginTop: 4 }, expiring: { ...tc.type.eyebrow, color: tc.color.amber, marginTop: 5 }, disclaimer: { marginTop: tc.space.md }, pressed: { opacity: .74 } });
