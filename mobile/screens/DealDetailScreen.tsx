import React from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { Deal } from '../api/deals';
import { Body, Card, Eyebrow, PrimaryButton, Screen, SectionHeader, Title } from '../components/ui';
import { SourceBadge } from '../features/categories/components';
import { tc } from '../design/tokens';

export default function DealDetailScreen({ route, navigation }: any) {
  const deal = route.params?.deal as Deal | undefined;
  if (!deal) return <Screen><Title>Offer unavailable</Title><Body muted style={styles.body}>Return to Deals and load observed offers again.</Body></Screen>;
  const value = deal.discount_pct != null ? `${deal.discount_pct}%` : deal.cashback_pct != null ? `${deal.cashback_pct}% cashback` : deal.cashback_amount != null ? `₹${deal.cashback_amount} cashback` : 'Terms supplied';
  return <Screen>
    <Eyebrow>DEAL / OBSERVED DETAIL</Eyebrow><Title style={styles.title}>{deal.title}</Title><Body muted style={styles.body}>Observed under {deal.provider}. Eligibility and final value remain subject to provider checkout.</Body>
    <SourceBadge source={deal.data_source} generatedAt={route.params?.generatedAt} />
    <Card tone="mint" style={styles.hero}><View style={styles.icon}><Feather name="tag" size={22} color={tc.color.mint} /></View><View style={styles.grow}><Text style={styles.label}>SUPPLIED VALUE</Text><Text style={styles.value}>{value}</Text></View></Card>
    <SectionHeader title="Eligibility signals" /><Card><Fact title="Category" value={deal.category} /><Fact title="Payment method" value={deal.payment_method || 'Not supplied'} /><Fact title="Minimum order" value={deal.min_order != null ? `₹${deal.min_order}` : 'Not supplied'} /><Fact title="Maximum cashback" value={deal.max_cashback != null ? `₹${deal.max_cashback}` : 'Not supplied'} /><Fact title="Valid until" value={deal.valid_until || 'Not supplied'} /></Card>
    <SectionHeader title="Terms and fine print" /><Card tone="amber"><Body muted>{deal.terms}</Body></Card>
    {route.params?.disclaimer ? <Body muted style={styles.disclaimer}>{route.params.disclaimer}</Body> : null}
    <PrimaryButton label={deal.deep_link ? 'Review provider handoff' : 'Provider link unavailable'} disabled={!deal.deep_link} icon="arrow-right" onPress={() => navigation.navigate('CheckoutHandoff', { product: { name: deal.title }, offer: { provider: deal.provider, deepLink: deal.deep_link, observed_at: route.params?.generatedAt }, reason: 'This offer was derived from a persisted provider observation. Confirm all terms and final value with the provider.' })} style={styles.cta} />
  </Screen>;
}
function Fact({ title, value }: { title: string; value: string }) { return <View style={styles.fact}><Text style={styles.factTitle}>{title}</Text><Text style={styles.factValue}>{value}</Text></View>; }
const styles = StyleSheet.create({ title: { marginTop: tc.space.xs }, body: { marginTop: tc.space.xs }, hero: { marginTop: tc.space.md, flexDirection: 'row', alignItems: 'center', gap: tc.space.md }, icon: { width: 48, height: 48, borderRadius: 16, backgroundColor: tc.color.surface, alignItems: 'center', justifyContent: 'center' }, grow: { flex: 1 }, label: { ...tc.type.eyebrow, color: tc.color.mint }, value: { ...tc.type.price, color: tc.color.ink, marginTop: 2 }, fact: { minHeight: 42, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: tc.space.sm, borderBottomWidth: 1, borderBottomColor: tc.color.line }, factTitle: { ...tc.type.bodySmall, color: tc.color.muted }, factValue: { ...tc.type.label, color: tc.color.ink, textAlign: 'right', flex: 1 }, disclaimer: { marginTop: tc.space.md }, cta: { marginTop: tc.space.lg } });
