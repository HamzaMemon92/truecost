import React, { useMemo } from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { HotelOption, HotelSearchResult } from '../api/travel';
import { AppHeader, Body, Card, PrimaryButton, Screen, SectionHeader, Title } from '../components/ui';
import { BreakdownRow, SourceBadge } from '../features/categories/components';
import { SystemState } from '../components/SystemState';
import { formatCurrency, tc } from '../design/tokens';

const trusted = (source?: string) => !!source && !/mock|preview|generated/i.test(source);
const verifiedHotel = (option: HotelOption) => option.authoritative === true && option.freshness_state === 'verified' && trusted(option.data_source);

export default function HotelResultsScreen({ route, navigation }: any) {
  const result = route.params?.result as HotelSearchResult | undefined;
  const filter = route.params?.filter || 'Best value';
  const options = useMemo(() => !result ? [] : filter === 'Refundable' ? result.options.filter(item => item.cancellation_policy.toLowerCase().includes('free cancellation')) : result.options, [filter, result]);
  if (!result) return <Screen><SystemState kind="empty" actionLabel="Return to hotel search" onAction={() => navigation.goBack()} /></Screen>;
  const verifiedOptions = options.filter(verifiedHotel);
  if (!result.options.length) return <Screen><AppHeader subtitle="Hotel comparison" onBack={() => navigation.goBack()} /><SystemState kind="unavailable" actionLabel="Return to hotel search" onAction={() => navigation.goBack()} /></Screen>;
  if (!result.options.some(verifiedHotel)) return <HotelPreviewState result={result} filter={filter} onBack={() => navigation.goBack()} />;
  return <Screen>
    <AppHeader subtitle="Verified stay comparison" onBack={() => navigation.goBack()} />
    <Text style={styles.kicker}>HOTEL RESULTS</Text>
    <Title style={styles.title}>Stays in {result.destination}</Title>
    <Body muted>{result.checkin_date} to {result.checkout_date} {'\u00B7'} {result.nights} night{result.nights === 1 ? '' : 's'} {'\u00B7'} {result.guests} guests</Body>
    <SourceBadge source={result.options[0]?.data_source} generatedAt={result.generated_at} />
    {result.best_value_option ? <Card tone="mint" style={styles.recommendation}><View style={styles.recommendIcon}><Feather name="star" size={20} color={tc.color.mint} /></View><View style={styles.grow}><Text style={styles.bestLabel}>BEST VERIFIED VALUE</Text><Title size="h2">{result.best_value_option.hotel_name}</Title><Body muted>{result.recommendation_reason}</Body></View></Card> : null}
    <SectionHeader title={`${filter} (${options.length})`} />
    {verifiedOptions.length ? verifiedOptions.map(option => <HotelCard key={`${option.provider}:${option.hotel_name}`} option={option} recommended={option.provider === result.best_value_option?.provider && option.hotel_name === result.best_value_option?.hotel_name} onHandoff={() => navigation.navigate('CheckoutHandoff', { product: { name: option.hotel_name }, offer: { provider: option.provider, price: option.total_price, deepLink: option.deep_link, delivery: `${result.nights} night stay`, observed_at: result.generated_at }, destination: result.destination, reason: result.recommendation_reason })} />) : <SystemState kind="empty" actionLabel="Change filters" onAction={() => navigation.goBack()} />}
    <Card tone="amber" style={styles.disclaimer}><Body muted>{result.disclaimer}</Body></Card>
    <PrimaryButton label="Change stay search" variant="outline" onPress={() => navigation.goBack()} style={styles.cta} />
  </Screen>;
}

function HotelPreviewState({ result, filter, onBack }: { result: HotelSearchResult; filter: string; onBack(): void }) {
  return <Screen>
    <AppHeader subtitle="Hotel comparison" onBack={onBack} />
    <Text style={styles.kicker}>NON-AUTHORITATIVE PREVIEW</Text>
    <Title style={styles.title}>Stays in {result.destination}</Title>
    <Body muted>{result.checkin_date} to {result.checkout_date} {'\u00B7'} {result.nights} night{result.nights === 1 ? '' : 's'} {'\u00B7'} {result.guests} guests</Body>
    <Card tone="amber" style={styles.previewCard}>
      <View style={styles.evidenceHeader}><Feather name="shield-off" size={18} color={tc.color.amber} /><Text style={styles.previewTitle}>Verified stay prices are not enabled yet</Text></View>
      <Body muted>TrueCost can show stay rows as preview evidence only. We will not rank, badge, or send users to a hotel provider until a verified contract returns property identity, room type, taxes, refundability, deep link, and freshness.</Body>
      <View style={styles.evidenceGrid}>
        <View style={styles.metric}><Text style={styles.metricValue}>{result.options.length}</Text><Text style={styles.metricLabel}>preview rows</Text></View>
        <View style={styles.metric}><Text style={styles.metricValue}>0</Text><Text style={styles.metricLabel}>verified stays</Text></View>
      </View>
    </Card>
    <SectionHeader title={`${filter} preview evidence - not compared`} />
    {result.options.slice(0, 5).map(option => <Card key={`${option.provider}:${option.hotel_name}`} style={styles.previewOption}>
      <View style={styles.head}><View style={styles.providerBadge}><Feather name="home" size={17} color={tc.color.iris} /></View><View style={styles.grow}><Text style={styles.provider}>{option.hotel_name}</Text><Body muted>{option.provider} {'\u00B7'} {option.location} {'\u00B7'} {option.freshness_state || 'preview'}</Body></View><Text style={styles.previewPill}>PREVIEW</Text></View>
      <Body muted style={styles.policy}>Not used for an authoritative recommendation. Source: {option.source_freshness || option.data_source}</Body>
    </Card>)}
    <Card tone="amber" style={styles.disclaimer}><Body muted>{result.disclaimer}</Body></Card>
    <PrimaryButton label="Change stay search" variant="outline" onPress={onBack} style={styles.cta} />
  </Screen>;
}

function HotelCard({ option, recommended, onHandoff }: { option: HotelOption; recommended: boolean; onHandoff(): void }) {
  return <Card tone={recommended ? 'mint' : 'default'} style={styles.option}>
    <View style={styles.head}><View style={styles.providerBadge}><Feather name="home" size={17} color={tc.color.iris} /></View><View style={styles.grow}><Text style={styles.provider}>{option.hotel_name}</Text><Body muted>{option.provider} {'\u00B7'} {option.star_rating} star {'\u00B7'} {option.location}</Body></View>{recommended ? <Text style={styles.pick}>BEST VALUE</Text> : null}</View>
    <View style={styles.amenities}>{option.amenities.map(item => <Text key={item} style={styles.amenity}>{item}</Text>)}</View>
    <View style={styles.breakdown}><BreakdownRow label="Nightly room total" value={formatCurrency(option.price_per_night)} /><BreakdownRow label="Taxes and fees" value={formatCurrency(option.taxes_fees)} /><BreakdownRow label="Expected stay total" value={formatCurrency(option.total_price)} strong /></View>
    <Body muted style={styles.policy}>{option.breakfast_included ? `Breakfast included \u00B7 ` : ''}{option.cancellation_policy}</Body>
    <PrimaryButton label="Review provider handoff" variant="outline" onPress={onHandoff} style={styles.handoff} />
  </Card>;
}

const styles = StyleSheet.create({
  kicker: { ...tc.type.eyebrow, color: tc.color.iris, marginTop: 20 }, title: { marginTop: 4 }, recommendation: { marginTop: tc.space.md, flexDirection: 'row', gap: tc.space.sm, alignItems: 'center' }, recommendIcon: { width: 44, height: 44, borderRadius: 15, backgroundColor: tc.color.surface, alignItems: 'center', justifyContent: 'center' }, grow: { flex: 1 }, bestLabel: { ...tc.type.eyebrow, color: tc.color.mint, marginBottom: 3 },
  option: { marginTop: tc.space.sm }, head: { flexDirection: 'row', alignItems: 'center', gap: tc.space.sm }, providerBadge: { width: 36, height: 36, borderRadius: 12, backgroundColor: tc.color.irisSoft, alignItems: 'center', justifyContent: 'center' }, provider: { ...tc.type.h3, color: tc.color.ink }, pick: { ...tc.type.eyebrow, color: tc.color.mint, backgroundColor: tc.color.mintSoft, paddingHorizontal: 8, paddingVertical: 6, borderRadius: tc.radius.pill }, amenities: { flexDirection: 'row', flexWrap: 'wrap', gap: tc.space.xs, marginTop: tc.space.sm }, amenity: { ...tc.type.bodySmall, fontSize: 11, color: tc.color.iris, backgroundColor: tc.color.irisSoft, paddingHorizontal: 8, paddingVertical: 5, borderRadius: tc.radius.pill }, breakdown: { marginTop: tc.space.md, paddingTop: tc.space.sm, borderTopWidth: 1, borderTopColor: tc.color.line }, policy: { marginTop: tc.space.sm }, handoff: { marginTop: tc.space.md }, disclaimer: { marginTop: tc.space.md }, cta: { marginTop: tc.space.md },
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
