import React, { useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { api } from '../api/client';
import { useAuth } from '../auth/AuthContext';
import { Card, Screen } from '../components/ui';
import { FilterRail, Metric, RetentionHeader, RowChevron } from '../components/RetentionPrimitives';
import { SystemState } from '../components/SystemState';
import { tc } from '../design/tokens';
import { useApiQuery } from '../query/useApiQuery';
import { useQueryClient } from '../query/QueryClient';
import type { Notice, NotificationStats } from '../types/commerce';

const categories = [
  { key: 'all', label: 'All' }, { key: 'price', label: 'Price drops' }, { key: 'travel', label: 'Travel' },
  { key: 'savings', label: 'Savings' }, { key: 'deals', label: 'Deals' }, { key: 'updates', label: 'Updates' },
];
const safeRoutes = new Set(['Watchlist', 'Activity', 'ComparisonHistory', 'Deals', 'Travel', 'Hotels', 'Cart', 'Settings', 'SavedLists']);

function noticeIcon(category: string): React.ComponentProps<typeof Feather>['name'] {
  if (category === 'price') return 'trending-down';
  if (category === 'travel') return 'map-pin';
  if (category === 'savings') return 'pie-chart';
  if (category === 'deals') return 'tag';
  return 'bell';
}

export default function NotificationsScreen({ navigation }: { navigation: any }) {
  const { session, updateSession } = useAuth();
  const cache = useQueryClient();
  const [category, setCategory] = useState('all');
  const [unreadOnly, setUnreadOnly] = useState(false);
  const query = `${category === 'all' ? '' : `category=${encodeURIComponent(category)}&`}unread_only=${unreadOnly}`;
  const { data, loading, error, refetch } = useApiQuery<Notice[]>(`notifications:${query}`, `/commerce/notifications?${query}`, { maxAge: 5_000 });
  const { data: stats } = useApiQuery<NotificationStats>('notifications:stats', '/commerce/notifications/stats', { maxAge: 5_000 });
  const refresh = async () => { cache.invalidate('notifications:'); await refetch(); };
  const markRead = async (item: Notice) => {
    if (!session || item.read_at) return;
    await api(session, updateSession, `/commerce/notifications/${item.id}/read`, { method: 'POST' });
    await refresh();
  };
  const open = async (item: Notice) => {
    await markRead(item);
    const route = item.deep_link?.split('?')[0];
    if (!route) return;
    if (route === 'Saved') navigation.navigate('MainTabs', { screen: 'Saved' });
    else if (safeRoutes.has(route)) navigation.navigate(route);
  };
  const markAll = async () => {
    if (!session) return;
    const suffix = category === 'all' ? '' : `?category=${encodeURIComponent(category)}`;
    await api(session, updateSession, `/commerce/notifications/mark-all-read${suffix}`, { method: 'POST' });
    await refresh();
  };
  const items = data || [];

  return <Screen>
    <RetentionHeader eyebrow="Your signals" title="Notification center" subtitle="Only useful changes: observed price movement, travel updates, savings and account notices." onBack={() => navigation.goBack()} actionIcon="check-circle" actionLabel="Mark visible notifications read" onAction={() => void markAll()} />
    <View style={styles.metrics}><Metric icon="bell" value={stats?.unread ?? 0} label="Unread" /><Metric icon="inbox" value={stats?.total ?? 0} label="All signals" tone="mint" /><Metric icon="tag" value={stats?.categories?.deals ?? 0} label="Deals" tone="amber" /></View>
    <FilterRail values={categories.map(value => ({ ...value, count: value.key === 'all' ? stats?.total : stats?.categories?.[value.key] }))} selected={category} onChange={setCategory} />
    <Pressable accessibilityRole="button" accessibilityState={{ selected: unreadOnly }} onPress={() => setUnreadOnly(value => !value)} style={({ pressed }) => [styles.unreadToggle, unreadOnly && styles.unreadToggleActive, pressed && styles.pressed]}><Feather name={unreadOnly ? 'check-square' : 'square'} size={18} color={unreadOnly ? tc.color.iris : tc.color.muted} /><Text style={[styles.unreadText, unreadOnly && styles.unreadTextActive]}>Show unread only</Text></Pressable>
    {loading && !data ? <SystemState kind="loading" /> : error ? <SystemState kind="offline" actionLabel="Try again" onAction={() => void refetch()} /> : !items.length ? <SystemState kind="empty_notifications" /> : <View style={styles.list}>{items.map(item => { const unread = !item.read_at; return <Pressable key={item.id} accessibilityRole="button" accessibilityLabel={`${unread ? 'Unread. ' : ''}${item.title}`} onPress={() => void open(item)} style={({ pressed }) => [pressed && styles.pressed]}><Card style={[styles.notice, unread && styles.unread]}><View style={[styles.icon, unread && styles.iconUnread]}><Feather name={noticeIcon(item.category)} size={18} color={unread ? tc.color.iris : tc.color.muted} /></View><View style={styles.copy}><View style={styles.titleRow}><Text style={styles.itemTitle}>{item.title}</Text>{unread ? <View accessibilityLabel="Unread" style={styles.dot} /> : null}</View><Text style={styles.body}>{item.body}</Text><View style={styles.metaRow}><Text style={styles.category}>{item.category.toUpperCase()}</Text><Text style={styles.date}>{new Date(item.created_at).toLocaleDateString()}</Text>{item.deep_link ? <Text style={styles.openLabel}>OPEN</Text> : null}</View></View>{item.deep_link ? <RowChevron /> : null}</Card></Pressable>; })}</View>}
  </Screen>;
}

const styles = StyleSheet.create({
  metrics: { flexDirection: 'row', gap: tc.space.xs }, unreadToggle: { minHeight: 48, borderRadius: tc.radius.md, borderWidth: 1, borderColor: tc.color.line, backgroundColor: tc.color.surface, flexDirection: 'row', alignItems: 'center', gap: tc.space.xs, paddingHorizontal: tc.space.md, marginBottom: tc.space.sm }, unreadToggleActive: { borderColor: '#DAD2FF', backgroundColor: tc.color.irisSoft }, unreadText: { ...tc.type.label, color: tc.color.muted }, unreadTextActive: { color: tc.color.iris }, list: { gap: tc.space.sm }, notice: { flexDirection: 'row', alignItems: 'center', gap: tc.space.sm, padding: tc.space.sm }, unread: { borderColor: '#DAD2FF', backgroundColor: '#FCFBFF' }, icon: { width: 44, height: 44, borderRadius: 15, backgroundColor: tc.color.surfaceMuted, alignItems: 'center', justifyContent: 'center' }, iconUnread: { backgroundColor: tc.color.irisSoft }, copy: { flex: 1 }, titleRow: { flexDirection: 'row', alignItems: 'center', gap: tc.space.xs }, itemTitle: { ...tc.type.h3, color: tc.color.ink, flex: 1 }, dot: { width: 8, height: 8, borderRadius: 4, backgroundColor: tc.color.iris }, body: { ...tc.type.bodySmall, color: tc.color.muted, marginTop: 3 }, metaRow: { flexDirection: 'row', alignItems: 'center', gap: tc.space.xs, marginTop: tc.space.xs }, category: { ...tc.type.eyebrow, color: tc.color.mint }, date: { ...tc.type.bodySmall, fontSize: 11, color: tc.color.muted }, openLabel: { ...tc.type.eyebrow, color: tc.color.iris, marginLeft: 'auto' }, pressed: { opacity: 0.7 },
});
