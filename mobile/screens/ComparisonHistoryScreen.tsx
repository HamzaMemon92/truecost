import React, { useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { Card, Screen } from '../components/ui';
import { FilterRail, RetentionHeader, RowChevron } from '../components/RetentionPrimitives';
import { SystemState } from '../components/SystemState';
import { tc } from '../design/tokens';
import { useApiQuery } from '../query/useApiQuery';
import type { ComparisonSummary } from '../types/commerce';

const categories = [{ key: 'all', label: 'All' }, { key: 'Grocery', label: 'Grocery' }, { key: 'Shopping', label: 'Shopping' }, { key: 'Mobility', label: 'Mobility' }, { key: 'Travel', label: 'Flights' }, { key: 'Hotels', label: 'Hotels' }];
export default function ComparisonHistoryScreen({ navigation }: { navigation: any }) {
  const [category, setCategory] = useState('all');
  const path = `/commerce/comparisons${category === 'all' ? '' : `?category=${encodeURIComponent(category)}`}`;
  const { data, loading, error, refetch } = useApiQuery<ComparisonSummary[]>(`comparisons:${category}`, path, { maxAge: 8_000 });
  return <Screen><RetentionHeader eyebrow="Observed evidence" title="Comparison history" subtitle="Revisit the exact provider observations associated with your authenticated searches." onBack={() => navigation.goBack()} />
    <FilterRail values={categories} selected={category} onChange={setCategory} />
    {loading && !data ? <SystemState kind="loading" /> : error ? <SystemState kind="offline" actionLabel="Try again" onAction={() => void refetch()} /> : !data?.length ? <SystemState kind="empty_activity" actionLabel="Start comparing" onAction={() => navigation.navigate('MainTabs', { screen: 'Compare' })} /> : <View style={styles.list}>{data.map(item => <Pressable key={item.id} accessibilityRole="button" onPress={() => navigation.navigate('ComparisonHistoryDetail', { comparisonId: item.id })} style={({ pressed }) => [pressed && styles.pressed]}><Card style={styles.item}><View style={styles.icon}><Feather name="repeat" size={19} color={tc.color.iris} /></View><View style={styles.copy}><Text style={styles.category}>{item.category.toUpperCase()}</Text><Text style={styles.title}>{item.query}</Text><Text style={styles.meta}>{item.provider_count} providers · {item.result_count} observed results · {new Date(item.created_at).toLocaleDateString()}</Text><Text numberOfLines={1} style={styles.providers}>{item.providers.join(' · ') || 'No provider label supplied'}</Text></View><RowChevron /></Card></Pressable>)}</View>}
  </Screen>;
}
const styles = StyleSheet.create({ list: { gap: tc.space.sm }, item: { flexDirection: 'row', alignItems: 'center', gap: tc.space.sm, padding: tc.space.sm }, icon: { width: 48, height: 48, borderRadius: 16, alignItems: 'center', justifyContent: 'center', backgroundColor: tc.color.irisSoft }, copy: { flex: 1 }, category: { ...tc.type.eyebrow, color: tc.color.mint }, title: { ...tc.type.h3, color: tc.color.ink, marginTop: 2 }, meta: { ...tc.type.bodySmall, fontSize: 11, color: tc.color.muted, marginTop: 3 }, providers: { ...tc.type.bodySmall, fontSize: 11, color: tc.color.iris, marginTop: 2 }, pressed: { opacity: 0.72 } });
