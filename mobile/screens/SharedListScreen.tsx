import React from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { publicApi } from '../api/client';
import { Card, Screen, SectionHeader } from '../components/ui';
import { RetentionHeader } from '../components/RetentionPrimitives';
import { SystemState } from '../components/SystemState';
import { formatCurrency, tc } from '../design/tokens';
import { useEffect, useState } from 'react';
import type { SavedCollection } from '../types/commerce';

export default function SharedListScreen({ navigation, route }: { navigation: any; route: any }) {
  const token = String(route.params?.shareToken || ''); const [data, setData] = useState<SavedCollection | null>(null); const [failed, setFailed] = useState(false);
  useEffect(() => { if (!token) { setFailed(true); return; } void publicApi<SavedCollection>(`/commerce/shared-lists/${token}`).then(setData).catch(() => setFailed(true)); }, [token]);
  if (!data && !failed) return <Screen><RetentionHeader eyebrow="Shared with you" title="Opening shortlist" onBack={() => navigation.goBack()} /><SystemState kind="loading" /></Screen>;
  if (!data) return <Screen><RetentionHeader eyebrow="Shared with you" title="Link unavailable" onBack={() => navigation.goBack()} /><SystemState kind="unavailable" /></Screen>;
  return <Screen><RetentionHeader eyebrow="Shared TrueCost list" title={data.name} subtitle={data.description || 'A shortlist shared from TrueCost.'} onBack={() => navigation.goBack()} /><Card tone="mint" style={styles.trust}><Feather name="shield" size={20} color={tc.color.mint} /><Text style={styles.trustText}>Read-only view · prices are saved observations and may have changed.</Text></Card><SectionHeader title={`${data.item_count} saved ${data.item_count === 1 ? 'item' : 'items'}`} />{data.items.map(link => <Card key={link.id} style={styles.item}><View style={styles.icon}><Feather name="bookmark" size={18} color={tc.color.iris} /></View><View style={styles.copy}><Text style={styles.title}>{link.item.title}</Text><Text style={styles.meta}>{link.item.provider || 'Provider not supplied'} · {formatCurrency(link.item.price, link.item.currency)}</Text>{link.note ? <Text style={styles.note}>“{link.note}”</Text> : null}</View></Card>)}</Screen>;
}
const styles = StyleSheet.create({ trust: { flexDirection: 'row', alignItems: 'center', gap: tc.space.sm }, trustText: { ...tc.type.bodySmall, color: tc.color.mint, flex: 1 }, item: { flexDirection: 'row', alignItems: 'center', gap: tc.space.sm, marginBottom: tc.space.sm, padding: tc.space.sm }, icon: { width: 44, height: 44, borderRadius: 15, alignItems: 'center', justifyContent: 'center', backgroundColor: tc.color.irisSoft }, copy: { flex: 1 }, title: { ...tc.type.h3, fontSize: 15, color: tc.color.ink }, meta: { ...tc.type.bodySmall, fontSize: 11, color: tc.color.muted }, note: { ...tc.type.bodySmall, color: tc.color.iris, marginTop: 3 } });
