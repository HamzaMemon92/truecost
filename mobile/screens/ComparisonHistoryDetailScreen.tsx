import React from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { Card, PrimaryButton, Screen, SectionHeader } from '../components/ui';
import { Metric, RetentionHeader } from '../components/RetentionPrimitives';
import { SystemState } from '../components/SystemState';
import { formatCurrency, tc } from '../design/tokens';
import { useApiQuery } from '../query/useApiQuery';
import type { ComparisonDetail } from '../types/commerce';

export default function ComparisonHistoryDetailScreen({ navigation, route }: { navigation: any; route: any }) {
  const id = String(route.params?.comparisonId || '');
  const { data, loading, error, refetch } = useApiQuery<ComparisonDetail>(`comparison:${id}`, `/commerce/comparisons/${id}`, { enabled: !!id, maxAge: 30_000 });
  if (loading && !data) return <Screen><RetentionHeader eyebrow="Comparison snapshot" title="Loading evidence" onBack={() => navigation.goBack()} /><SystemState kind="loading" /></Screen>;
  if (error || !data) return <Screen><RetentionHeader eyebrow="Comparison snapshot" title="Evidence unavailable" onBack={() => navigation.goBack()} /><SystemState kind="unavailable" actionLabel="Try again" onAction={() => void refetch()} /></Screen>;
  return <Screen><RetentionHeader eyebrow={data.category} title={data.query} subtitle={`Captured ${new Date(data.created_at).toLocaleString()}. Prices and availability are historical observations.`} onBack={() => navigation.goBack()} />
    <View style={styles.metrics}><Metric icon="layers" value={data.provider_count} label="Providers" /><Metric icon="package" value={data.result_count} label="Results" tone="mint" /></View>
    <SectionHeader title="Provider evidence" />
    <View style={styles.list}>{data.observations.map(row => { const product = row.product || {}; const title = String(product.title || product.name || row.product_id); const price = typeof product.price === 'number' ? product.price : typeof product.totalPrice === 'number' ? product.totalPrice : null; return <Card key={row.id} style={styles.observation}><View style={styles.obsHead}><View style={styles.providerIcon}><Feather name="database" size={17} color={tc.color.iris} /></View><View style={styles.obsCopy}><Text style={styles.provider}>{row.provider}</Text><Text style={styles.title}>{title}</Text></View>{price != null ? <Text style={styles.price}>{formatCurrency(price, String(product.currency || 'INR'))}</Text> : null}</View><View style={styles.evidence}><Feather name="clock" size={14} color={tc.color.muted} /><Text style={styles.evidenceText}>Observed {new Date(row.observed_at).toLocaleString()}</Text></View></Card>; })}</View>
    <Card tone="amber" style={styles.disclaimer}><Feather name="info" size={18} color={tc.color.amber} /><Text style={styles.disclaimerText}>This is a provenance record, not a current-price promise. Rerun the search to request fresh observations.</Text></Card>
    <PrimaryButton label="Rerun this comparison" icon="refresh-cw" onPress={() => navigation.navigate('AgentSearch', { initialQuery: data.query, category: data.category })} style={styles.cta} />
  </Screen>;
}
const styles = StyleSheet.create({ metrics: { flexDirection: 'row', gap: tc.space.sm, maxWidth: 420 }, list: { gap: tc.space.sm }, observation: { padding: tc.space.sm }, obsHead: { flexDirection: 'row', gap: tc.space.sm, alignItems: 'center' }, providerIcon: { width: 42, height: 42, borderRadius: 14, backgroundColor: tc.color.irisSoft, alignItems: 'center', justifyContent: 'center' }, obsCopy: { flex: 1 }, provider: { ...tc.type.eyebrow, color: tc.color.mint }, title: { ...tc.type.h3, color: tc.color.ink, marginTop: 2 }, price: { ...tc.type.h3, color: tc.color.ink }, evidence: { flexDirection: 'row', gap: 6, marginTop: tc.space.sm, paddingTop: tc.space.sm, borderTopWidth: 1, borderTopColor: tc.color.line }, evidenceText: { ...tc.type.bodySmall, fontSize: 11, color: tc.color.muted }, disclaimer: { marginTop: tc.space.md, flexDirection: 'row', gap: tc.space.sm, alignItems: 'flex-start' }, disclaimerText: { ...tc.type.bodySmall, color: tc.color.amber, flex: 1 }, cta: { marginTop: tc.space.md } });
