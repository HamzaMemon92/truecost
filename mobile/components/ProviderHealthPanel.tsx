import React, { useEffect, useMemo, useState } from 'react';
import { ActivityIndicator, StyleSheet, Text, View } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { Body, Card, SectionHeader } from './ui';
import { getProviderHealth, ProviderHealth } from '../api/providers';
import { tc } from '../design/tokens';

type Props = {
  categoryId?: string;
  title?: string;
  compact?: boolean;
  limit?: number;
  showTitle?: boolean;
};

const capabilityCopy: Record<string, string> = {
  live: 'Verified live observations are available.',
  preview: 'Preview-only. TrueCost will not show authoritative prices here yet.',
  degraded: 'Some provider data may be stale or partially unavailable.',
  unavailable: 'No verified provider observations are available right now.',
};

export function ProviderHealthPanel({ categoryId, title = 'Provider health', compact = false, limit = 4, showTitle = true }: Props) {
  const [providers, setProviders] = useState<ProviderHealth[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let active = true;
    setLoading(true);
    getProviderHealth()
      .then(response => { if (active) { setProviders(response.providers || []); setError(''); } })
      .catch(next => { if (active) setError(next instanceof Error ? next.message : 'Provider health is unavailable.'); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, []);

  const visible = useMemo(() => {
    const scoped = categoryId ? providers.filter(item => item.category_id === categoryId) : providers;
    return scoped.slice().sort((a, b) => Number(b.live) - Number(a.live) || b.ingested_observations - a.ingested_observations);
  }, [categoryId, providers]);

  const summary = useMemo(() => {
    const counts = { live: 0, preview: 0, degraded: 0, unavailable: 0 };
    for (const provider of visible) {
      if (provider.current_capability === 'live') counts.live += 1;
      else if (provider.current_capability === 'preview') counts.preview += 1;
      else if (provider.current_capability === 'degraded') counts.degraded += 1;
      else counts.unavailable += 1;
    }
    return counts;
  }, [visible]);

  if (loading) {
    return <>
      {showTitle ? <SectionHeader title={title} /> : null}
      <Card style={[styles.card, compact && styles.compactCard]}><ActivityIndicator size="small" color={tc.color.iris} /><Body muted>Checking provider capability…</Body></Card>
    </>;
  }

  if (error) {
    return <>
      {showTitle ? <SectionHeader title={title} /> : null}
      <Card tone="amber" style={[styles.card, compact && styles.compactCard]}><Feather name="wifi-off" size={17} color={tc.color.amber} /><Body muted>{error}</Body></Card>
    </>;
  }

  if (!visible.length) {
    return <>
      {showTitle ? <SectionHeader title={title} /> : null}
      <Card tone="amber" style={[styles.block, compact && styles.compactCard]}>
        <View style={styles.header}><Feather name="shield-off" size={18} color={tc.color.amber} /><Text style={styles.heading}>No providers configured for this category</Text></View>
        <Body muted>Search can still open where supported, but TrueCost will not claim a live comparison without verified provider observations.</Body>
      </Card>
    </>;
  }

  const leading = visible[0]?.current_capability || 'unavailable';
  const tone = summary.live ? 'mint' : summary.degraded ? 'amber' : 'default';

  return <>
    {showTitle ? <SectionHeader title={title} /> : null}
    <Card tone={tone} style={[styles.block, compact && styles.compactCard]}>
      <View style={styles.header}>
        <View style={[styles.healthIcon, summary.live ? styles.liveIcon : styles.previewIcon]}><Feather name={summary.live ? 'shield' : 'shield-off'} size={17} color={summary.live ? tc.color.mint : tc.color.amber} /></View>
        <View style={styles.grow}>
          <Text style={styles.heading}>{summary.live ? `${summary.live} live provider${summary.live === 1 ? '' : 's'}` : 'Live comparison not verified yet'}</Text>
          <Body muted>{capabilityCopy[leading] || capabilityCopy.unavailable}</Body>
        </View>
      </View>
      <View style={styles.stats}>
        <Stat label="Live" value={summary.live} />
        <Stat label="Preview" value={summary.preview} />
        <Stat label="Degraded" value={summary.degraded} />
        <Stat label="Unavailable" value={summary.unavailable} />
      </View>
      {!compact ? <View style={styles.rows}>
        {visible.slice(0, limit).map(provider => <ProviderRow key={provider.provider_id} provider={provider} />)}
      </View> : null}
    </Card>
  </>;
}

function Stat({ label, value }: { label: string; value: number }) {
  return <View style={styles.stat}><Text style={styles.statValue}>{value}</Text><Text style={styles.statLabel}>{label}</Text></View>;
}

function ProviderRow({ provider }: { provider: ProviderHealth }) {
  const live = provider.current_capability === 'live';
  const degraded = provider.current_capability === 'degraded';
  const color = live ? tc.color.mint : degraded ? tc.color.amber : tc.color.muted;
  const last = provider.last_ingested_at ? new Date(provider.last_ingested_at).toLocaleString() : 'No recent observation';
  return <View style={styles.row}>
    <Feather name={live ? 'check-circle' : degraded ? 'alert-circle' : 'clock'} size={15} color={color} />
    <View style={styles.grow}>
      <Text style={styles.provider}>{provider.name || provider.provider_id}</Text>
      <Text style={styles.meta}>{provider.current_capability} · {provider.ingested_observations} observations · {last}</Text>
    </View>
  </View>;
}

const styles = StyleSheet.create({
  card: { marginTop: tc.space.sm, minHeight: 58, flexDirection: 'row', alignItems: 'center', gap: tc.space.sm },
  block: { marginTop: tc.space.sm, gap: tc.space.sm },
  compactCard: { marginTop: tc.space.sm },
  header: { flexDirection: 'row', alignItems: 'center', gap: tc.space.sm },
  healthIcon: { width: 38, height: 38, borderRadius: 13, alignItems: 'center', justifyContent: 'center' },
  liveIcon: { backgroundColor: tc.color.mintSoft },
  previewIcon: { backgroundColor: tc.color.amberSoft },
  grow: { flex: 1, minWidth: 0 },
  heading: { ...tc.type.label, color: tc.color.ink },
  stats: { flexDirection: 'row', gap: tc.space.xs },
  stat: { flex: 1, borderRadius: tc.radius.sm, backgroundColor: 'rgba(255,255,255,0.62)', paddingVertical: 8, alignItems: 'center' },
  statValue: { ...tc.type.h3, color: tc.color.ink, fontVariant: ['tabular-nums'] },
  statLabel: { ...tc.type.bodySmall, color: tc.color.muted, fontSize: 10 },
  rows: { gap: 8 },
  row: { minHeight: 44, flexDirection: 'row', alignItems: 'center', gap: tc.space.xs, borderTopWidth: 1, borderTopColor: tc.color.line, paddingTop: 8 },
  provider: { ...tc.type.label, color: tc.color.ink, textTransform: 'capitalize' },
  meta: { ...tc.type.bodySmall, color: tc.color.muted, fontSize: 11, marginTop: 1 },
});
