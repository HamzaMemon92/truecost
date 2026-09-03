import React, { useMemo, useState } from 'react';
import { Alert, Linking, Pressable, StyleSheet, Switch, Text, View } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { api } from '../api/client';
import { useAuth } from '../auth/AuthContext';
import { Card, Field, PrimaryButton, Screen, SectionHeader, Title } from '../components/ui';
import { FilterRail, Metric, RetentionHeader } from '../components/RetentionPrimitives';
import { SystemState } from '../components/SystemState';
import { formatCurrency, tc } from '../design/tokens';
import { useApiQuery } from '../query/useApiQuery';
import { useQueryClient } from '../query/QueryClient';
import type { PriceWatch } from '../types/commerce';

type Draft = { title: string; target: string; current: string; provider: string };
const blank: Draft = { title: '', target: '', current: '', provider: '' };

export default function WatchlistScreen({ navigation }: { navigation: any }) {
  const { session, updateSession } = useAuth();
  const cache = useQueryClient();
  const { data, loading, error, refetch } = useApiQuery<PriceWatch[]>('watchlist', '/commerce/price-watches', { maxAge: 8_000 });
  const [filter, setFilter] = useState('all');
  const [editor, setEditor] = useState(false);
  const [editing, setEditing] = useState<PriceWatch | null>(null);
  const [draft, setDraft] = useState<Draft>(blank);
  const [busy, setBusy] = useState(false);
  const items = data || [];
  const reached = (item: PriceWatch) => item.current_price != null && item.current_price <= item.target_price;
  const visible = useMemo(() => items.filter(item => filter === 'all' || (filter === 'active' && item.active) || (filter === 'reached' && reached(item)) || (filter === 'paused' && !item.active)), [items, filter]);

  const openEditor = (item?: PriceWatch) => {
    setEditing(item || null);
    setDraft(item ? { title: item.title, target: String(item.target_price), current: item.current_price == null ? '' : String(item.current_price), provider: item.provider || '' } : blank);
    setEditor(true);
  };
  const reload = async () => { cache.invalidate('watchlist'); cache.invalidate('dashboard'); await refetch(); };
  const save = async () => {
    if (!session || !draft.title.trim() || !Number.isFinite(Number(draft.target)) || Number(draft.target) < 0) return;
    setBusy(true);
    try {
      const payload = { title: draft.title.trim(), target_price: Number(draft.target), current_price: draft.current.trim() ? Number(draft.current) : null, currency: editing?.currency || 'INR', provider: draft.provider.trim() || null, source_url: editing?.source_url || null, active: editing?.active ?? true };
      await api(session, updateSession, editing ? `/commerce/price-watches/${editing.id}` : '/commerce/price-watches', { method: editing ? 'PATCH' : 'POST', body: JSON.stringify(payload) });
      setEditor(false); setEditing(null); setDraft(blank); await reload();
    } finally { setBusy(false); }
  };
  const update = async (item: PriceWatch, changes: Partial<PriceWatch>) => {
    if (!session) return;
    await api(session, updateSession, `/commerce/price-watches/${item.id}`, { method: 'PATCH', body: JSON.stringify({ title: item.title, target_price: item.target_price, current_price: item.current_price, currency: item.currency, source_url: item.source_url, provider: item.provider, active: item.active, ...changes }) });
    await reload();
  };
  const remove = (item: PriceWatch) => Alert.alert('Remove price alert?', `TrueCost will stop monitoring ${item.title}.`, [{ text: 'Keep alert', style: 'cancel' }, { text: 'Remove', style: 'destructive', onPress: () => { if (session) void api(session, updateSession, `/commerce/price-watches/${item.id}`, { method: 'DELETE' }).then(reload); } }]);

  return <Screen>
    <RetentionHeader eyebrow="Price intelligence" title="Watchlist" subtitle="Set the price that makes a decision worthwhile. Alerts use newly observed provider data—not a price guarantee." onBack={() => navigation.goBack()} actionIcon="plus" actionLabel="Create a price alert" onAction={() => openEditor()} />
    <View style={styles.metrics}><Metric icon="target" value={items.filter(item => item.active).length} label="Active" /><Metric icon="trending-down" value={items.filter(reached).length} label="At target" tone="mint" /><Metric icon="pause-circle" value={items.filter(item => !item.active).length} label="Paused" tone="amber" /></View>
    <FilterRail values={[{ key: 'all', label: 'All', count: items.length }, { key: 'active', label: 'Active' }, { key: 'reached', label: 'At target' }, { key: 'paused', label: 'Paused' }]} selected={filter} onChange={setFilter} />
    {editor ? <Card tone="iris" style={styles.editor}><View style={styles.editorHead}><View><Text style={styles.editorEyebrow}>{editing ? 'UPDATE ALERT' : 'NEW ALERT'}</Text><Title size="h3">{editing ? 'Tune your target' : 'What price should we watch?'}</Title></View><Pressable accessibilityRole="button" accessibilityLabel="Close alert editor" onPress={() => setEditor(false)} style={styles.close}><Feather name="x" size={20} color={tc.color.ink} /></Pressable></View><Field label="Item or trip" value={draft.title} onChangeText={title => setDraft(value => ({ ...value, title }))} placeholder="e.g. Noise-cancelling headphones" /><View style={styles.fieldGap} /><View style={styles.fieldRow}><Field label="Target price" value={draft.target} onChangeText={target => setDraft(value => ({ ...value, target }))} keyboardType="decimal-pad" placeholder="5000" containerStyle={styles.fieldFlex} /><Field label="Observed price (optional)" value={draft.current} onChangeText={current => setDraft(value => ({ ...value, current }))} keyboardType="decimal-pad" placeholder="5499" containerStyle={styles.fieldFlex} /></View><View style={styles.fieldGap} /><Field label="Provider label (optional)" value={draft.provider} onChangeText={provider => setDraft(value => ({ ...value, provider }))} placeholder="Observed provider or category" /><PrimaryButton label={editing ? 'Save alert' : 'Create alert'} icon="bell" loading={busy} disabled={!draft.title.trim() || !draft.target.trim()} onPress={() => void save()} style={styles.save} /></Card> : null}
    <SectionHeader title="Your alerts" action="Comparison history" onAction={() => navigation.navigate('ComparisonHistory')} />
    {loading && !data ? <SystemState kind="loading" /> : error ? <SystemState kind="offline" actionLabel="Try again" onAction={() => void refetch()} /> : !visible.length ? <SystemState kind="empty_saved" actionLabel="Create alert" onAction={() => openEditor()} /> : <View style={styles.list}>{visible.map(item => { const hit = reached(item); return <Card key={item.id} style={styles.watch}><View style={styles.watchTop}><View style={[styles.watchIcon, hit && styles.watchIconHit]}><Feather name={hit ? 'check' : 'bell'} size={19} color={hit ? tc.color.mint : tc.color.iris} /></View><View style={styles.watchCopy}><Text style={styles.watchTitle}>{item.title}</Text><Text style={styles.watchProvider}>{item.provider || 'All observed providers'}</Text></View><Switch accessibilityLabel={`${item.active ? 'Pause' : 'Resume'} ${item.title}`} value={item.active} onValueChange={active => void update(item, { active })} trackColor={{ false: tc.color.lineStrong, true: '#BDE8D9' }} thumbColor={item.active ? tc.color.mint : tc.color.muted} /></View><View style={styles.priceRow}><View><Text style={styles.priceLabel}>TARGET</Text><Text style={styles.price}>{formatCurrency(item.target_price, item.currency)}</Text></View><View style={styles.priceRight}><Text style={styles.priceLabel}>LAST OBSERVED</Text><Text style={[styles.price, hit && styles.hit]}>{formatCurrency(item.current_price, item.currency)}</Text></View></View><View style={styles.rule} /><View style={styles.actions}><Pressable accessibilityRole="button" onPress={() => openEditor(item)} style={styles.textAction}><Feather name="edit-3" size={16} color={tc.color.iris} /><Text style={styles.actionText}>Edit target</Text></Pressable>{item.source_url ? <Pressable accessibilityRole="link" onPress={() => void Linking.openURL(item.source_url!)} style={styles.textAction}><Feather name="external-link" size={16} color={tc.color.iris} /><Text style={styles.actionText}>Open source</Text></Pressable> : null}<Pressable accessibilityRole="button" accessibilityLabel={`Remove ${item.title}`} onPress={() => remove(item)} style={styles.delete}><Feather name="trash-2" size={17} color={tc.color.danger} /></Pressable></View></Card>; })}</View>}
  </Screen>;
}

const styles = StyleSheet.create({
  metrics: { flexDirection: 'row', gap: tc.space.xs }, editor: { marginTop: tc.space.md, gap: 0 }, editorHead: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: tc.space.md }, editorEyebrow: { ...tc.type.eyebrow, color: tc.color.iris, marginBottom: 3 }, close: { width: 44, height: 44, alignItems: 'center', justifyContent: 'center' }, fieldGap: { height: tc.space.sm }, fieldRow: { flexDirection: 'row', gap: tc.space.sm }, fieldFlex: { flex: 1 }, save: { marginTop: tc.space.md }, list: { gap: tc.space.sm }, watch: { padding: tc.space.md }, watchTop: { flexDirection: 'row', alignItems: 'center', gap: tc.space.sm }, watchIcon: { width: 44, height: 44, borderRadius: 15, backgroundColor: tc.color.irisSoft, alignItems: 'center', justifyContent: 'center' }, watchIconHit: { backgroundColor: tc.color.mintSoft }, watchCopy: { flex: 1 }, watchTitle: { ...tc.type.h3, color: tc.color.ink }, watchProvider: { ...tc.type.bodySmall, color: tc.color.muted, marginTop: 1 }, priceRow: { flexDirection: 'row', justifyContent: 'space-between', marginTop: tc.space.md }, priceRight: { alignItems: 'flex-end' }, priceLabel: { ...tc.type.eyebrow, color: tc.color.muted }, price: { ...tc.type.h3, color: tc.color.ink, marginTop: 3 }, hit: { color: tc.color.mint }, rule: { height: 1, backgroundColor: tc.color.line, marginTop: tc.space.md }, actions: { flexDirection: 'row', alignItems: 'center', gap: tc.space.sm, marginTop: tc.space.xs }, textAction: { minHeight: 44, flexDirection: 'row', alignItems: 'center', gap: 6 }, actionText: { ...tc.type.label, color: tc.color.iris }, delete: { width: 44, height: 44, marginLeft: 'auto', alignItems: 'center', justifyContent: 'center' },
});
