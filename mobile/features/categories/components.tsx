import React from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { useNavigation } from '@react-navigation/native';
import { AppHeader, Body, Card, Chip, Eyebrow, Title } from '../../components/ui';
import { tc } from '../../design/tokens';

export function CategoryHero({ eyebrow, title, body, icon }: { eyebrow: string; title: string; body: string; icon: React.ComponentProps<typeof Feather>['name'] }) {
  const navigation = useNavigation<any>();
  return <><AppHeader subtitle={eyebrow.replace(/\s*\/\s*/g, ' · ')} onBack={navigation.canGoBack() ? () => navigation.goBack() : undefined} /><View style={styles.hero}>
    <View style={styles.heroIcon}><Feather name={icon} size={24} color={tc.color.iris} /></View>
    <View style={styles.heroCopy}><Eyebrow>{eyebrow}</Eyebrow><Title size="h1" style={styles.heroTitle}>{title}</Title><Body muted style={styles.heroBody}>{body}</Body></View>
  </View></>;
}

export function SelectionRow({ values, selected, onSelect }: { values: string[]; selected: string; onSelect(value: string): void }) {
  return <View style={styles.chips}>{values.map(value => <Chip key={value} label={value} selected={selected === value} onPress={() => onSelect(value)} />)}</View>;
}

export function SourceBadge({ source, generatedAt }: { source?: string; generatedAt?: string }) {
  const preview = !source || source.includes('mock') || source.includes('estimated') || source.includes('formula');
  return <Card tone={preview ? 'amber' : 'mint'} style={styles.source}>
    <Feather name={preview ? 'alert-circle' : 'check-circle'} size={18} color={preview ? tc.color.amber : tc.color.mint} />
    <View style={styles.sourceCopy}><Text style={styles.sourceTitle}>{preview ? 'Estimate / development preview' : 'Observed provider data'}</Text><Body muted>{source ? `Source: ${source.replace(/_/g, ' ')}` : 'The API did not supply provenance.'}{generatedAt ? ` · Generated ${new Date(generatedAt).toLocaleString()}` : ''}</Body></View>
  </Card>;
}

export function BreakdownRow({ label, value, strong = false }: { label: string; value: string; strong?: boolean }) {
  return <View style={styles.row}><Text style={styles.rowLabel}>{label}</Text><Text style={[styles.rowValue, strong && styles.rowStrong]}>{value}</Text></View>;
}

const styles = StyleSheet.create({
  hero: { flexDirection: 'row', gap: tc.space.sm, alignItems: 'flex-start', marginTop: tc.space.md }, heroIcon: { width: 48, height: 48, borderRadius: 16, backgroundColor: tc.color.irisSoft, alignItems: 'center', justifyContent: 'center' }, heroCopy: { flex: 1 }, heroTitle: { marginTop: 2 }, heroBody: { marginTop: 3, fontSize: 13, lineHeight: 19 },
  chips: { flexDirection: 'row', flexWrap: 'wrap', gap: tc.space.xs, marginTop: tc.space.sm },
  source: { flexDirection: 'row', alignItems: 'flex-start', gap: tc.space.sm, marginTop: tc.space.md }, sourceCopy: { flex: 1 }, sourceTitle: { ...tc.type.label, color: tc.color.ink, marginBottom: tc.space.xxs },
  row: { minHeight: 38, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: tc.space.md }, rowLabel: { ...tc.type.bodySmall, color: tc.color.muted, flex: 1 }, rowValue: { ...tc.type.label, color: tc.color.ink, textAlign: 'right', fontVariant: ['tabular-nums'] }, rowStrong: { ...tc.type.h2 },
});
