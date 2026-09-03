import React from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { AppHeader, Body, Card, Eyebrow, Screen, SectionHeader, Title } from '../components/ui';
import { SystemState } from '../components/SystemState';
import { formatCurrency, tc } from '../design/tokens';

export default function DecisionExplanationScreen({ route, navigation }: any) {
  const decision = route.params?.decision;
  if (!decision) return <Screen><AppHeader subtitle="Decision explained" onBack={() => navigation.goBack()} /><SystemState kind="empty" actionLabel="Back to comparison" onAction={() => navigation.goBack()} /></Screen>;
  const assumptions: string[] = decision.assumptions || []; const changes: string[] = decision.what_would_change || decision.sensitivity || []; const evidence: string[] = decision.evidence || decision.verified_facts || [];
  const total = decision.total ?? decision.total_cost; const savings = decision.savings ?? decision.savings_vs_single_provider;
  return <Screen>
    <AppHeader subtitle="Decision explained" onBack={() => navigation.goBack()} />
    <Eyebrow style={styles.eyebrow}>DECISION EXPLAINED</Eyebrow><Title size="h1">{decision.title || decision.winner || decision.provider || 'Why this option won'}</Title>
    <Card tone="mint" style={styles.hero}><View style={styles.heroIcon}><Feather name="award" size={25} color={tc.color.mint} /></View><View style={styles.heroCopy}><Text style={styles.heroLabel}>DETERMINISTIC RESULT</Text>{total !== undefined ? <Text style={styles.total}>{formatCurrency(Number(total), decision.currency || 'INR')}</Text> : null}{savings !== undefined ? <Body style={styles.savings}>Estimated savings {formatCurrency(Number(savings), decision.currency || 'INR')}</Body> : <Body muted>No savings value was supplied.</Body>}</View></Card>
    <SectionHeader title="Why it won" /><Card><Body>{decision.explanation || decision.reason || 'The backend did not supply an explanation for this result.'}</Body></Card>
    {decision.confidence !== undefined ? <><SectionHeader title="Confidence and evidence" /><Card tone="iris"><View style={styles.confidence}><Text style={styles.confidenceValue}>{Math.round(Number(decision.confidence) * (Number(decision.confidence) <= 1 ? 100 : 1))}%</Text><Body muted>Confidence supplied by the decision response</Body></View></Card></> : null}
    {evidence.length ? <List title="Verified facts" icon="check-circle" items={evidence} /> : null}
    {assumptions.length ? <List title="Assumptions" icon="info" items={assumptions} /> : null}
    {changes.length ? <List title="What would change this recommendation" icon="refresh-cw" items={changes} /> : null}
    <Card tone="amber" style={styles.disclosure}><Feather name="shield" size={21} color={tc.color.amber} /><Body style={styles.disclosureCopy}>Explanation text never recalculates totals or rankings. Provider checkout remains the source of final availability and payable amount.</Body></Card>
  </Screen>;
}
function List({ title, icon, items }: { title: string; icon: React.ComponentProps<typeof Feather>['name']; items: string[] }) {
  return <><SectionHeader title={title} /><Card style={styles.list}>{items.map((item, index) => <View key={item + index} style={styles.listRow}><Feather name={icon} size={17} color={tc.color.iris} /><Body style={styles.listCopy}>{item}</Body></View>)}</Card></>;
}
const styles = StyleSheet.create({
  eyebrow: { marginTop: tc.space.md, marginBottom: tc.space.xs }, hero: { marginTop: tc.space.md, flexDirection: 'row', alignItems: 'center', gap: tc.space.md }, heroIcon: { width: 52, height: 52, borderRadius: 18, backgroundColor: tc.color.surface, alignItems: 'center', justifyContent: 'center' }, heroCopy: { flex: 1 }, heroLabel: { ...tc.type.eyebrow, color: tc.color.mint }, total: { ...tc.type.price, color: tc.color.ink, marginTop: 2 }, savings: { color: tc.color.mint, fontWeight: '700' },
  confidence: { gap: 3 }, confidenceValue: { ...tc.type.price, color: tc.color.iris }, list: { gap: tc.space.sm }, listRow: { flexDirection: 'row', alignItems: 'flex-start', gap: tc.space.sm }, listCopy: { flex: 1 }, disclosure: { marginTop: tc.space.lg, flexDirection: 'row', alignItems: 'flex-start', gap: tc.space.sm }, disclosureCopy: { flex: 1 },
});
