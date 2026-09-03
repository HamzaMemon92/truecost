import React from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { FlightOption, FlightSearchResult } from '../api/travel';
import { AppHeader, Body, Card, PrimaryButton, Screen, SectionHeader, Title } from '../components/ui';
import { BreakdownRow, SourceBadge } from '../features/categories/components';
import { SystemState } from '../components/SystemState';
import { formatCurrency, tc } from '../design/tokens';

const trusted = (source?: string) => !!source && !/mock|preview|generated/i.test(source);
const verifiedFlight = (option: FlightOption) => option.authoritative === true && option.freshness_state === 'verified' && trusted(option.data_source);

export default function FlightResultsScreen({ route, navigation }: any) {
  const result = route.params?.result as FlightSearchResult | undefined;
  if (!result) return <Screen><SystemState kind="empty" actionLabel="Return to flight search" onAction={() => navigation.goBack()} /></Screen>;
  const verifiedOptions = result.options.filter(verifiedFlight);
  if (!result.options.length) return <Screen><AppHeader subtitle="Flight comparison" onBack={() => navigation.goBack()} /><SystemState kind="unavailable" actionLabel="Return to flight search" onAction={() => navigation.goBack()} /></Screen>;
  if (!verifiedOptions.length) return <FlightPreviewState result={result} onBack={() => navigation.goBack()} />;
  const source = result.options[0]?.data_source;
  return <Screen>
    <AppHeader subtitle="Verified flight comparison" onBack={() => navigation.goBack()} />
    <Text style={styles.kicker}>FLIGHT RESULTS</Text>
    <Title style={styles.title}>{result.origin} to {result.destination}</Title>
    <Body muted>{result.departure_date} {'\u00B7'} {result.passengers} traveller{result.passengers === 1 ? '' : 's'} {'\u00B7'} {result.cabin_class}</Body>
    <SourceBadge source={source} generatedAt={result.generated_at} />
    {result.cheapest_option ? <Card tone="mint" style={styles.recommendation}><View style={styles.recommendIcon}><Feather name="star" size={20} color={tc.color.mint} /></View><View style={styles.grow}><Text style={styles.bestLabel}>BEST VERIFIED TOTAL</Text><Title size="h2">{result.cheapest_option.provider}</Title><Body muted>{result.recommendation_reason}</Body></View></Card> : null}
    <SectionHeader title={`Available flights (${result.options.length})`} />
    {verifiedOptions.map(option => <FlightCard key={`${option.provider}:${option.flight_number}`} option={option} recommended={option.provider === result.cheapest_option?.provider} onHandoff={() => navigation.navigate('CheckoutHandoff', { product: { name: `${option.origin} to ${option.destination} flight` }, offer: { provider: option.provider, price: option.total_fare, deepLink: option.deep_link, delivery: `${option.departure_time}-${option.arrival_time}`, observed_at: result.generated_at }, destination: result.destination, reason: result.recommendation_reason })} />)}
    <Card tone="amber" style={styles.disclaimer}><Body muted>{result.disclaimer}</Body></Card>
    <PrimaryButton label="Change flight search" variant="outline" onPress={() => navigation.goBack()} style={styles.cta} />
  </Screen>;
}

function FlightPreviewState({ result, onBack }: { result: FlightSearchResult; onBack(): void }) {
  return <Screen>
    <AppHeader subtitle="Flight comparison" onBack={onBack} />
    <Text style={styles.kicker}>NON-AUTHORITATIVE PREVIEW</Text>
    <Title style={styles.title}>{result.origin} to {result.destination}</Title>
    <Body muted>{result.departure_date} {'\u00B7'} {result.passengers} traveller{result.passengers === 1 ? '' : 's'} {'\u00B7'} {result.cabin_class}</Body>
    <Card tone="amber" style={styles.previewCard}>
      <View style={styles.evidenceHeader}><Feather name="shield-off" size={18} color={tc.color.amber} /><Text style={styles.previewTitle}>Verified flight prices are not enabled yet</Text></View>
      <Body muted>TrueCost can show this as a development preview only. We will not rank, badge, or hand off flights until a verified provider contract returns route, fare, baggage, refundability, deep link, and freshness evidence.</Body>
      <View style={styles.evidenceGrid}>
        <View style={styles.metric}><Text style={styles.metricValue}>{result.options.length}</Text><Text style={styles.metricLabel}>preview rows</Text></View>
        <View style={styles.metric}><Text style={styles.metricValue}>0</Text><Text style={styles.metricLabel}>verified fares</Text></View>
      </View>
    </Card>
    <SectionHeader title="Preview evidence - not compared" />
    {result.options.slice(0, 5).map(option => <Card key={`${option.provider}:${option.flight_number}`} style={styles.previewOption}>
      <View style={styles.head}><View style={styles.providerBadge}><Feather name="send" size={16} color={tc.color.iris} /></View><View style={styles.grow}><Text style={styles.provider}>{option.provider}</Text><Body muted>{option.flight_number} {'\u00B7'} {option.origin}-{option.destination} {'\u00B7'} {option.freshness_state || 'preview'}</Body></View><Text style={styles.previewPill}>PREVIEW</Text></View>
      <Body muted style={styles.policy}>Not used for an authoritative recommendation. Source: {option.source_freshness || option.data_source}</Body>
    </Card>)}
    <Card tone="amber" style={styles.disclaimer}><Body muted>{result.disclaimer}</Body></Card>
    <PrimaryButton label="Change flight search" variant="outline" onPress={onBack} style={styles.cta} />
  </Screen>;
}

function FlightCard({ option, recommended, onHandoff }: { option: FlightOption; recommended: boolean; onHandoff(): void }) {
  return <Card tone={recommended ? 'mint' : 'default'} style={styles.option}>
    <View style={styles.head}><View style={styles.providerBadge}><Feather name="send" size={16} color={tc.color.iris} /></View><View style={styles.grow}><Text style={styles.provider}>{option.provider}</Text><Body muted>{option.flight_number} {'\u00B7'} {option.stops ? `${option.stops} stop` : 'Non-stop'} {'\u00B7'} {Math.floor(option.duration_minutes / 60)}h {option.duration_minutes % 60}m</Body></View>{recommended ? <Text style={styles.pick}>BEST TOTAL</Text> : null}</View>
    <View style={styles.schedule}><Text style={styles.time}>{option.departure_time}</Text><View style={styles.flightLine}><View style={styles.dot} /><View style={styles.line} /><Feather name="send" size={15} color={tc.color.iris} /></View><Text style={styles.time}>{option.arrival_time}</Text></View>
    <View style={styles.breakdown}><BreakdownRow label="Base fare" value={formatCurrency(option.base_fare)} /><BreakdownRow label="Taxes and fees" value={formatCurrency(option.taxes_fees)} /><BreakdownRow label="Expected total" value={formatCurrency(option.total_fare)} strong /></View>
    <Body muted style={styles.policy}>{option.baggage_included} {'\u00B7'} {option.cancellation_policy}</Body>
    <PrimaryButton label="Review provider handoff" variant="outline" onPress={onHandoff} style={styles.handoff} />
  </Card>;
}

const styles = StyleSheet.create({
  kicker: { ...tc.type.eyebrow, color: tc.color.iris, marginTop: 20 }, title: { marginTop: 4 }, recommendation: { marginTop: tc.space.md, flexDirection: 'row', gap: tc.space.sm, alignItems: 'center' }, recommendIcon: { width: 44, height: 44, borderRadius: 15, backgroundColor: tc.color.surface, alignItems: 'center', justifyContent: 'center' }, grow: { flex: 1 }, bestLabel: { ...tc.type.eyebrow, color: tc.color.mint, marginBottom: 3 },
  option: { marginTop: tc.space.sm }, head: { flexDirection: 'row', alignItems: 'center', gap: tc.space.sm }, providerBadge: { width: 36, height: 36, borderRadius: 12, backgroundColor: tc.color.irisSoft, alignItems: 'center', justifyContent: 'center' }, provider: { ...tc.type.h3, color: tc.color.ink }, pick: { ...tc.type.eyebrow, color: tc.color.mint, backgroundColor: tc.color.mintSoft, paddingHorizontal: 8, paddingVertical: 6, borderRadius: tc.radius.pill },
  schedule: { flexDirection: 'row', alignItems: 'center', gap: tc.space.sm, marginTop: tc.space.md }, time: { ...tc.type.h2, color: tc.color.ink, fontVariant: ['tabular-nums'] }, flightLine: { flex: 1, flexDirection: 'row', alignItems: 'center' }, dot: { width: 7, height: 7, borderRadius: 4, backgroundColor: tc.color.iris }, line: { height: 1, flex: 1, backgroundColor: tc.color.lineStrong }, breakdown: { marginTop: tc.space.md, paddingTop: tc.space.sm, borderTopWidth: 1, borderTopColor: tc.color.line }, policy: { marginTop: tc.space.sm }, handoff: { marginTop: tc.space.md }, disclaimer: { marginTop: tc.space.md }, cta: { marginTop: tc.space.md },
  previewCard: { marginTop: tc.space.lg, gap: tc.space.sm },
  evidenceHeader: { flexDirection: 'row', alignItems: 'center', gap: tc.space.xs },
  previewTitle: { ...tc.type.label, color: tc.color.ink },
  evidenceGrid: { flexDirection: 'row', gap: tc.space.sm, marginTop: tc.space.xs },
  metric: { flex: 1, borderRadius: tc.radius.sm, backgroundColor: tc.color.surfaceMuted, padding: tc.space.sm },
  metricValue: { ...tc.type.h2, color: tc.color.ink },
  metricLabel: { ...tc.type.bodySmall, color: tc.color.muted },
  previewOption: { marginTop: tc.space.sm },
  previewPill: { ...tc.type.eyebrow, color: tc.color.amber, backgroundColor: tc.color.amberSoft, paddingHorizontal: 8, paddingVertical: 6, borderRadius: tc.radius.pill },
});
