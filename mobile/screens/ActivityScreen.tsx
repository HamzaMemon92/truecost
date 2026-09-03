import React, { useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { Card, Screen, SectionHeader } from '../components/ui';
import { FilterRail, Metric, RetentionHeader, RowChevron } from '../components/RetentionPrimitives';
import { SystemState } from '../components/SystemState';
import { tc } from '../design/tokens';
import { useApiQuery } from '../query/useApiQuery';
import type { Activity, ActivitySummary } from '../types/commerce';

const groups = [{ key: 'all', label: 'All' }, { key: 'saved', label: 'Saved' }, { key: 'watches', label: 'Alerts' }, { key: 'carts', label: 'Carts' }, { key: 'lists', label: 'Lists' }, { key: 'handoffs', label: 'Handoffs' }];
function eventIcon(type: string): React.ComponentProps<typeof Feather>['name'] {
  if (type.startsWith('saved')) return 'bookmark'; if (type.startsWith('price_watch')) return 'bell';
  if (type.startsWith('cart')) return 'shopping-bag'; if (type.startsWith('collection')) return 'list';
  if (type.startsWith('handoff')) return 'external-link'; return 'clock';
}
function eventLabel(type: string) { return type.split('.').map(value => value.replace('_', ' ')).join(' · '); }

export default function ActivityScreen({ navigation }: { navigation: any }) {
  const [group, setGroup] = useState('all');
  const suffix = group === 'all' ? '' : `?group=${group}`;
  const { data, loading, error, refetch } = useApiQuery<Activity[]>(`activity:${group}`, `/commerce/activity${suffix}`, { maxAge: 6_000 });
  const { data: summary } = useApiQuery<ActivitySummary>('activity:summary', '/commerce/activity/summary', { maxAge: 6_000 });
  const openActivity = (item: Activity) => {
    if (item.event_type.startsWith('price_watch')) navigation.navigate('Watchlist');
    else if (item.event_type.startsWith('collection')) navigation.navigate('SavedLists', { collectionId: item.details.collection_id });
    else if (item.event_type.startsWith('cart')) navigation.navigate('Cart');
    else if (item.event_type.startsWith('saved')) navigation.navigate('MainTabs', { screen: 'Saved' });
  };
  return <Screen>
    <RetentionHeader eyebrow="Your decision trail" title="Activity" subtitle="A private timeline of the comparisons and choices you made in TrueCost." onBack={() => navigation.goBack()} actionIcon="search" actionLabel="Open comparison history" onAction={() => navigation.navigate('ComparisonHistory')} />
    <View style={styles.metrics}><Metric icon="clock" value={summary?.total_events ?? 0} label="Actions" /><Metric icon="repeat" value={summary?.comparison_count ?? 0} label="Comparisons" tone="mint" /><Metric icon="external-link" value={summary?.event_groups?.handoffs ?? 0} label="Handoffs" tone="amber" /></View>
    {summary?.recent_comparisons?.length ? <><SectionHeader title="Recent comparisons" action="See all" onAction={() => navigation.navigate('ComparisonHistory')} /><View style={styles.comparisonRail}>{summary.recent_comparisons.slice(0, 2).map(item => <Pressable key={item.id} accessibilityRole="button" onPress={() => navigation.navigate('ComparisonHistoryDetail', { comparisonId: item.id })} style={({ pressed }) => [styles.comparison, pressed && styles.pressed]}><Text style={styles.compCategory}>{item.category.toUpperCase()}</Text><Text numberOfLines={2} style={styles.compTitle}>{item.query}</Text><Text style={styles.compMeta}>{item.provider_count} providers · {item.result_count} results</Text><Feather name="arrow-up-right" size={18} color={tc.color.iris} /></Pressable>)}</View></> : null}
    <SectionHeader title="Timeline" />
    <FilterRail values={groups.map(value => ({ ...value, count: value.key === 'all' ? summary?.total_events : summary?.event_groups?.[value.key] }))} selected={group} onChange={setGroup} />
    {loading && !data ? <SystemState kind="loading" /> : error ? <SystemState kind="offline" actionLabel="Try again" onAction={() => void refetch()} /> : !data?.length ? <SystemState kind="empty_activity" /> : <View style={styles.timeline}>{data.map((item, index) => <Pressable key={item.id} accessibilityRole="button" onPress={() => openActivity(item)} style={({ pressed }) => [pressed && styles.pressed]}><Card style={styles.event}><View style={styles.eventTrack}><View style={styles.eventIcon}><Feather name={eventIcon(item.event_type)} size={17} color={tc.color.iris} /></View>{index < data.length - 1 ? <View style={styles.connector} /> : null}</View><View style={styles.eventCopy}><Text style={styles.eventTitle}>{item.title}</Text><Text style={styles.eventMeta}>{eventLabel(item.event_type)} · {new Date(item.created_at).toLocaleDateString()}</Text></View><RowChevron /></Card></Pressable>)}</View>}
  </Screen>;
}

const styles = StyleSheet.create({
  metrics: { flexDirection: 'row', gap: tc.space.xs }, comparisonRail: { flexDirection: 'row', gap: tc.space.sm }, comparison: { flex: 1, minHeight: 150, borderRadius: tc.radius.lg, padding: tc.space.md, backgroundColor: tc.color.ink }, compCategory: { ...tc.type.eyebrow, color: '#9DE3CC' }, compTitle: { ...tc.type.h3, color: tc.color.white, marginTop: tc.space.xs, flex: 1 }, compMeta: { ...tc.type.bodySmall, fontSize: 11, color: '#B8BED3', marginBottom: tc.space.xs }, timeline: { gap: tc.space.sm }, event: { flexDirection: 'row', padding: tc.space.sm, minHeight: 76, alignItems: 'center' }, eventTrack: { alignSelf: 'stretch', width: 44, alignItems: 'center' }, eventIcon: { width: 40, height: 40, borderRadius: 14, backgroundColor: tc.color.irisSoft, alignItems: 'center', justifyContent: 'center', zIndex: 1 }, connector: { position: 'absolute', top: 40, bottom: -26, width: 1, backgroundColor: tc.color.lineStrong }, eventCopy: { flex: 1, marginLeft: tc.space.xs }, eventTitle: { ...tc.type.h3, fontSize: 15, color: tc.color.ink }, eventMeta: { ...tc.type.bodySmall, fontSize: 11, color: tc.color.muted, marginTop: 3, textTransform: 'capitalize' }, pressed: { opacity: 0.72 },
});
