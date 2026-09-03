import React from 'react';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { AppHeader, Body, IconButton, Title } from './ui';
import { tc } from '../design/tokens';

export function RetentionHeader({ eyebrow, title, subtitle, onBack, actionIcon, actionLabel, onAction }: { eyebrow: string; title: string; subtitle?: string; onBack?: () => void; actionIcon?: React.ComponentProps<typeof Feather>['name']; actionLabel?: string; onAction?: () => void }) {
  return <View style={styles.header}>
    <AppHeader subtitle={eyebrow} onBack={onBack} />
    <View style={styles.titleRow}><View style={styles.titleCopy}><Text style={styles.eyebrow}>{eyebrow.toUpperCase()}</Text><Title size="h1">{title}</Title></View>{actionIcon && actionLabel && onAction ? <IconButton icon={actionIcon} label={actionLabel} onPress={onAction} /> : null}</View>
    {subtitle ? <Body muted style={styles.subtitle}>{subtitle}</Body> : null}
  </View>;
}

export function FilterRail({ values, selected, onChange }: { values: { key: string; label: string; count?: number }[]; selected: string; onChange: (key: string) => void }) {
  return <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.filters}>{values.map(value => <Pressable key={value.key} accessibilityRole="button" accessibilityState={{ selected: selected === value.key }} onPress={() => onChange(value.key)} style={({ pressed }) => [styles.filter, selected === value.key && styles.filterActive, pressed && styles.pressed]}><Text style={[styles.filterText, selected === value.key && styles.filterTextActive]}>{value.label}{value.count === undefined ? '' : ` ${value.count}`}</Text></Pressable>)}</ScrollView>;
}

export function Metric({ icon, value, label, tone = 'iris' }: { icon: React.ComponentProps<typeof Feather>['name']; value: string | number; label: string; tone?: 'iris' | 'mint' | 'amber' }) {
  const colors = tone === 'mint' ? [tc.color.mintSoft, tc.color.mint] : tone === 'amber' ? [tc.color.amberSoft, tc.color.amber] : [tc.color.irisSoft, tc.color.iris];
  return <View style={styles.metric}><View style={[styles.metricIcon, { backgroundColor: colors[0] }]}><Feather name={icon} size={18} color={colors[1]} /></View><Text style={styles.metricValue}>{value}</Text><Text style={styles.metricLabel}>{label}</Text></View>;
}

export function RowChevron() { return <View style={styles.chevron}><Feather name="chevron-right" size={18} color={tc.color.muted} /></View>; }

const styles = StyleSheet.create({
  header: { marginBottom: tc.space.md }, titleRow: { flexDirection: 'row', alignItems: 'center', gap: tc.space.sm, marginTop: tc.space.md }, titleCopy: { flex: 1 },
  eyebrow: { ...tc.type.eyebrow, color: tc.color.iris, marginBottom: 3 }, subtitle: { marginTop: 3, maxWidth: 560 },
  filters: { gap: tc.space.xs, paddingVertical: tc.space.sm, paddingRight: tc.space.lg }, filter: { minHeight: 42, borderRadius: tc.radius.pill, borderWidth: 1, borderColor: tc.color.lineStrong, backgroundColor: tc.color.surface, justifyContent: 'center', paddingHorizontal: tc.space.md }, filterActive: { backgroundColor: tc.color.iris, borderColor: tc.color.iris }, filterText: { ...tc.type.label, color: tc.color.inkSoft }, filterTextActive: { color: tc.color.white },
  metric: { flex: 1, minWidth: 88, minHeight: 94, borderRadius: tc.radius.md, borderWidth: 1, borderColor: tc.color.line, backgroundColor: tc.color.surface, padding: 10 }, metricIcon: { width: 31, height: 31, borderRadius: 11, alignItems: 'center', justifyContent: 'center' }, metricValue: { ...tc.type.h3, color: tc.color.ink, marginTop: 7 }, metricLabel: { ...tc.type.bodySmall, fontSize: 10, lineHeight: 14, color: tc.color.muted, marginTop: 1 },
  chevron: { width: 32, alignItems: 'flex-end' }, pressed: { opacity: 0.72 },
});
