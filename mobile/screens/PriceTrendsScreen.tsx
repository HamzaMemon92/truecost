import React, { useMemo, useState } from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { Body, Card, Chip, Eyebrow, IconButton, Screen, Title } from '../components/ui';
import { SystemState } from '../components/SystemState';
import { formatCurrency, tc } from '../design/tokens';

type Observation = { price: number; observed_at?: string; date?: string; provider?: string };
const windows = [30, 90, 180, 365] as const;
export default function PriceTrendsScreen({ route, navigation }: any) {
  const product = route.params?.product || {}; const source: Observation[] = Array.isArray(route.params?.observations) ? route.params.observations : [];
  const [days, setDays] = useState<number>(90);
  const observations = useMemo(() => {
    const cutoff = Date.now() - days * 86_400_000;
    return source.filter(item => Number.isFinite(item.price) && (!item.observed_at && !item.date || new Date(item.observed_at || item.date || 0).getTime() >= cutoff)).sort((a, b) => new Date(a.observed_at || a.date || 0).getTime() - new Date(b.observed_at || b.date || 0).getTime());
  }, [source, days]);
  const prices = observations.map(item => item.price); const min = prices.length ? Math.min(...prices) : 0; const max = prices.length ? Math.max(...prices) : 0; const spread = Math.max(max - min, 1);
  return <Screen>
    <IconButton icon="arrow-left" label="Back" onPress={() => navigation.goBack()} /><Eyebrow style={styles.eyebrow}>OBSERVED PRICE HISTORY</Eyebrow><Title size="h1">{product.name || product.title || 'Price trends'}</Title>
    <Body muted style={styles.lede}>This view summarizes stored observations. It does not predict future prices.</Body>
    <View style={styles.windows}>{windows.map(value => <Chip key={value} label={value === 365 ? '1 year' : value + ' days'} selected={days === value} onPress={() => setDays(value)} />)}</View>
    {!observations.length ? <SystemState kind="empty" actionLabel="Back to product" onAction={() => navigation.goBack()} /> : <>
      <View style={styles.metrics}><Card tone="mint" style={styles.metric}><Text style={styles.metricLabel}>LOWEST OBSERVED</Text><Text style={styles.metricValue}>{formatCurrency(min, product.currency || 'INR')}</Text></Card><Card tone="amber" style={styles.metric}><Text style={styles.metricLabel}>HIGHEST OBSERVED</Text><Text style={styles.metricValue}>{formatCurrency(max, product.currency || 'INR')}</Text></Card></View>
      <Card style={styles.chart}><View accessibilityLabel={'Price history with ' + observations.length + ' observations'} style={styles.bars}>{observations.map((item, index) => {
        const height = 28 + ((item.price - min) / spread) * 112;
        return <View key={(item.observed_at || item.date || '') + index} style={styles.barColumn}><View style={[styles.bar, { height }]} /><Text numberOfLines={1} style={styles.barLabel}>{formatCurrency(item.price)}</Text></View>;
      })}</View><View style={styles.rule} /><Body muted>{observations.length} observation{observations.length === 1 ? '' : 's'} in this window. Tap-friendly detailed chart interaction can be added when the API supplies a stable observation identifier.</Body></Card>
    </>}
  </Screen>;
}
const styles = StyleSheet.create({
  eyebrow: { marginTop: tc.space.lg, marginBottom: tc.space.xs }, lede: { marginTop: tc.space.sm }, windows: { flexDirection: 'row', flexWrap: 'wrap', gap: tc.space.xs, marginTop: tc.space.lg }, metrics: { flexDirection: 'row', gap: tc.space.sm, marginTop: tc.space.lg }, metric: { flex: 1, padding: tc.space.sm }, metricLabel: { ...tc.type.eyebrow, fontSize: 9, color: tc.color.muted }, metricValue: { ...tc.type.h3, color: tc.color.ink, marginTop: 5, fontVariant: ['tabular-nums'] },
  chart: { marginTop: tc.space.md }, bars: { minHeight: 170, flexDirection: 'row', alignItems: 'flex-end', gap: 5, overflow: 'hidden' }, barColumn: { flex: 1, alignItems: 'center', justifyContent: 'flex-end', minWidth: 18 }, bar: { width: '72%', minWidth: 8, maxWidth: 26, borderRadius: 7, backgroundColor: tc.color.iris }, barLabel: { ...tc.type.bodySmall, fontSize: 8, color: tc.color.muted, marginTop: 5, maxWidth: 54 }, rule: { height: 1, backgroundColor: tc.color.line, marginVertical: tc.space.md },
});
