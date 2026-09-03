import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { ActivityIndicator, Image, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { Feather } from '@expo/vector-icons';
import ScraperManager from '../components/core/ScraperManager';
import { AppHeader, Body, Card, Chip, PrimaryButton, Screen, SectionHeader, Title } from '../components/ui';
import { useAuth } from '../auth/AuthContext';
import { API_BASE } from '../config';
import { formatCurrency, tc } from '../design/tokens';
import { useUserLocation } from '../location/LocationContext';
import { buildExactProviderQueries } from '../utils/exactProductQuery';

type Offer = {
  provider?: string;
  price?: number;
  originalPrice?: number;
  original_price?: number;
  deliveryTime?: string;
  delivery_time?: string;
  deepLink?: string;
  deep_link?: string;
  isBest?: boolean;
  is_best?: boolean;
};

type ProductResult = {
  id?: string;
  name?: string;
  title?: string;
  brand?: string;
  category?: string;
  imageUrl?: string;
  image_url?: string;
  weightVolume?: string;
  weight_volume?: string;
  matchScore?: number;
  matchTier?: string;
  prices?: Offer[];
};

type CanonicalOfferGroup = {
  group_id?: string;
  title?: string;
  image_url?: string;
  offers?: Array<{
    offer_id?: string;
    provider?: string;
    price?: number;
    original_price?: number;
    delivery_time?: string;
    deep_link?: string;
    product?: ProductResult;
    evidence?: {
      product_id?: string;
      product_name?: string;
      brand?: string;
      match_score?: number;
    };
  }>;
  best_offer?: {
    provider?: string;
    price?: number;
    product?: ProductResult;
  };
  evidence_summary?: {
    providers_checked?: number;
    exact_offers?: number;
    probable_offers?: number;
    related_results?: number;
    rejected_results?: number;
    authoritative?: boolean;
    resolution_mode?: string;
  };
  explanation?: string;
};

const SHOPPING_PROVIDERS = ['Amazon', 'Flipkart', 'Meesho', 'Myntra'];
const ATTEMPT_TIMEOUT_MS = 12000;

function createSearchSessionId() {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, token => {
    const value = Math.floor(Math.random() * 16);
    const nibble = token === 'x' ? value : (value & 0x3) | 0x8;
    return nibble.toString(16);
  });
}

function normalizeOffer(offer: Offer) {
  return {
    provider: offer.provider || 'Provider',
    price: offer.price,
    originalPrice: offer.originalPrice ?? offer.original_price,
    deliveryTime: offer.deliveryTime ?? offer.delivery_time,
    deepLink: offer.deepLink ?? offer.deep_link,
    isBest: offer.isBest ?? offer.is_best,
  };
}

export default function FocusedCompareScreen({ route, navigation }: any) {
  const { session } = useAuth();
  const { location } = useUserLocation();
  const category = route.params?.category || 'Shopping';
  const initialProduct = route.params?.product || {};
  const query = String(route.params?.query || route.params?.initialQuery || initialProduct.name || initialProduct.title || '').trim();
  const providerQueries = useMemo(() => buildExactProviderQueries(query, initialProduct.brand), [initialProduct.brand, query]);
  const [attemptIndex, setAttemptIndex] = useState(0);
  const providerQuery = providerQueries[attemptIndex] || query;
  const [exactResults, setExactResults] = useState<ProductResult[]>([]);
  const [probableResults, setProbableResults] = useState<ProductResult[]>([]);
  const [relatedResults, setRelatedResults] = useState<ProductResult[]>([]);
  const [canonicalGroups, setCanonicalGroups] = useState<CanonicalOfferGroup[]>([]);
  const [providersResponded, setProvidersResponded] = useState<string[]>([]);
  const [attemptResponded, setAttemptResponded] = useState<string[]>([]);
  const [providersPending, setProvidersPending] = useState<string[]>(category === 'Shopping' ? SHOPPING_PROVIDERS.map(item => item.toLowerCase()) : []);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [attemptErrors, setAttemptErrors] = useState<Record<string, string>>({});
  const [diagnostics, setDiagnostics] = useState<any>(null);
  const [discoveryReport, setDiscoveryReport] = useState<any>(null);
  const [sessionId, setSessionId] = useState<string | null>(route.params?.searchSessionId || createSearchSessionId());
  const [loading, setLoading] = useState(Boolean(query));
  const [finished, setFinished] = useState(false);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);
  const sessionIdRef = useRef<string | null>(sessionId);

  useEffect(() => { sessionIdRef.current = sessionId; }, [sessionId]);

  const refreshResults = useCallback(async (activeSessionId?: string | null) => {
    const sid = activeSessionId || sessionIdRef.current;
    if (!sid || !query) return;
    const response = await fetch(`${API_BASE}/search?q=${encodeURIComponent(query)}&category=${encodeURIComponent(category)}&session_id=${encodeURIComponent(sid)}&exact_match=true`);
    if (!response.ok) return;
    const data = await response.json();
    setExactResults(data.primary_results || []);
    setProbableResults(data.probable_results || data.discovery_report?.probable_results || []);
    setRelatedResults(data.discovery_report?.related_results || data.recommendations || []);
    setCanonicalGroups(data.discovery_report?.canonical_offer_groups || []);
    setProvidersResponded(data.providers_responded || []);
    setProvidersPending(data.providers_pending || []);
    setDiagnostics(data.diagnostics || null);
    setDiscoveryReport(data.discovery_report || null);
  }, [category, query]);

  const handleResults = useCallback(async (provider: string, data: any) => {
    if (!data || (typeof data === 'object' && !Array.isArray(data) && Object.keys(data).length === 0)) return;
    const providerKey = provider.toLowerCase();
    setProvidersResponded(prev => [...new Set([...prev, providerKey])]);
    setAttemptResponded(prev => [...new Set([...prev, providerKey])]);
    try {
      const headers: Record<string, string> = { 'Content-Type': 'application/json' };
      if (session?.access_token) headers.Authorization = `Bearer ${session.access_token}`;
      const response = await fetch(`${API_BASE}/ingest`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ provider, query, category, raw_data: data, search_session_id: sessionIdRef.current, provider_query: providerQuery, exact_discovery_attempt: attemptIndex + 1 }),
      });
      if (!response.ok) throw new Error('Provider data could not be normalized');
      const nextSessionId = response.headers.get('X-Search-Session-Id') || sessionIdRef.current;
      if (nextSessionId && nextSessionId !== sessionIdRef.current) setSessionId(nextSessionId);
      await refreshResults(nextSessionId);
      setLoading(false);
    } catch (cause) {
      setErrors(prev => ({ ...prev, [provider]: cause instanceof Error ? cause.message : 'Provider failed' }));
    }
  }, [category, providerQuery, query, refreshResults, session?.access_token]);

  const handleError = useCallback((provider: string, error: string) => {
    const message = error || 'Unavailable';
    setErrors(prev => ({ ...prev, [provider]: message }));
    setAttemptErrors(prev => ({ ...prev, [provider.toLowerCase()]: message }));
  }, []);

  useEffect(() => {
    if (!query) return;
    setLoading(true);
    setFinished(false);
    setAttemptResponded([]);
    setAttemptErrors({});
    timeoutRef.current = setTimeout(() => {
      if (attemptIndex < providerQueries.length - 1 && !exactResults.length) {
        setAttemptIndex(value => value + 1);
        return;
      }
      setLoading(false);
      setFinished(true);
    }, ATTEMPT_TIMEOUT_MS);
    return () => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
    };
  }, [attemptIndex, exactResults.length, providerQueries.length, query]);

  useEffect(() => {
    if (!query || exactResults.length) return;
    const expected = category === 'Shopping' ? SHOPPING_PROVIDERS.length : 4;
    if (attemptResponded.length + Object.keys(attemptErrors).length < expected) return;
    if (attemptIndex < providerQueries.length - 1) {
      setAttemptIndex(value => value + 1);
      return;
    }
    setLoading(false);
    setFinished(true);
  }, [attemptErrors, attemptIndex, attemptResponded.length, category, exactResults.length, providerQueries.length, query]);

  const canonicalGroup = canonicalGroups[0];
  const best = useMemo(() => {
    const offers = exactResults.flatMap(product => (product.prices || []).map(offer => ({ product, offer: normalizeOffer(offer) }))).filter(item => Number.isFinite(item.offer.price));
    return offers.sort((a, b) => (a.offer.price || 0) - (b.offer.price || 0))[0];
  }, [exactResults]);
  const reportBest = canonicalGroup?.best_offer || discoveryReport?.best_observed?.offer;
  const selected = canonicalGroup?.best_offer?.product || exactResults[0] || initialProduct;
  const image = canonicalGroup?.image_url || selected.imageUrl || selected.image_url || initialProduct.imageUrl || initialProduct.image_url;
  const allOffers = useMemo(() => {
    if (canonicalGroup?.offers?.length) {
      return canonicalGroup.offers.map((offer, index) => ({
        product: offer.product || selected || initialProduct,
        offer: {
          provider: offer.provider || 'Provider',
          price: offer.price,
          originalPrice: offer.original_price,
          deliveryTime: offer.delivery_time,
          deepLink: offer.deep_link,
          isBest: index === 0,
        },
      }));
    }
    return exactResults.flatMap(product => (product.prices || []).map(offer => ({ product, offer: normalizeOffer(offer) }))).sort((a, b) => (a.offer.price || 0) - (b.offer.price || 0));
  }, [canonicalGroup, exactResults, initialProduct, selected]);
  const probableOffers = useMemo(() => probableResults.flatMap(product => (product.prices || []).map(offer => ({ product, offer: normalizeOffer(offer) }))).sort((a, b) => (a.offer.price || 0) - (b.offer.price || 0)), [probableResults]);
  const relatedOffers = useMemo(() => relatedResults.flatMap(product => (product.prices || []).map(offer => ({ product, offer: normalizeOffer(offer) }))).sort((a, b) => (a.offer.price || 0) - (b.offer.price || 0)), [relatedResults]);
  const providerSignal = providersResponded.length ? `${providersResponded.length} responded` : loading ? 'Checking providers' : 'No provider responded yet';
  const unresolvedCount = providersPending.length + Object.keys(errors).length;
  const triedQueries = providerQueries.slice(0, attemptIndex + 1);

  if (!query) {
    return <Screen><AppHeader subtitle="Exact comparison" onBack={() => navigation.goBack()} /><Card tone="danger"><Title size="h3">No product selected</Title><Body muted>Go back and select a product to compare exact prices.</Body></Card></Screen>;
  }

  return <Screen scroll={false} contentStyle={styles.screen}>
    <AppHeader subtitle="Exact comparison" onBack={() => navigation.goBack()} />
    <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={styles.content}>
      <Card tone="iris" style={styles.hero}>
        <View style={styles.heroRow}>
          {image ? <Image source={{ uri: image }} resizeMode="contain" style={styles.image} /> : <View style={styles.placeholder}><Feather name="headphones" size={26} color={tc.color.iris} /></View>}
          <View style={styles.heroCopy}>
            <Text style={styles.kicker}>EXACT PRODUCT CHECK</Text>
            <Title size="h2">{canonicalGroup?.title || query}</Title>
            <View style={styles.chips}><Chip label={category} /><Chip label={providerSignal} /></View>
            {providerQuery && providerQuery !== query ? <Text numberOfLines={1} style={styles.providerQuery}>Attempt {attemptIndex + 1}/{providerQueries.length}: {providerQuery}</Text> : null}
          </View>
        </View>
        <View style={styles.rule} />
        <View style={styles.summaryRow}>
          <View>
            <Text style={styles.summaryLabel}>Best observed</Text>
            <Text style={styles.bestPrice}>{formatCurrency(reportBest?.price ?? best?.offer.price, 'INR')}</Text>
          </View>
          <PrimaryButton label="Rerun" icon="refresh-cw" variant="outline" onPress={() => navigation.replace('FocusedCompare', { ...route.params, query })} style={styles.rerun} />
        </View>
        <Body muted style={styles.truth}>{canonicalGroup?.explanation || "Only exact product matches become provider prices here. Similar results are separated below and never counted as this model's best price."}</Body>
      </Card>

      {(discoveryReport?.decision_explanation || canonicalGroup?.evidence_summary) ? <Card style={styles.evidenceCard}>
        <View style={styles.evidenceHeader}>
          <Feather name="shield" size={18} color={tc.color.mint} />
          <Text style={styles.evidenceTitle}>Evidence-first decision</Text>
        </View>
        <Body muted>{discoveryReport?.decision_explanation || canonicalGroup?.explanation}</Body>
        <View style={styles.evidenceGrid}>
          <View style={styles.metric}><Text style={styles.metricValue}>{canonicalGroup?.evidence_summary?.exact_offers ?? discoveryReport?.exact_results?.length ?? 0}</Text><Text style={styles.metricLabel}>exact</Text></View>
          <View style={styles.metric}><Text style={styles.metricValue}>{canonicalGroup?.evidence_summary?.probable_offers ?? discoveryReport?.probable_results?.length ?? 0}</Text><Text style={styles.metricLabel}>probable</Text></View>
          <View style={styles.metric}><Text style={styles.metricValue}>{canonicalGroup?.evidence_summary?.related_results ?? discoveryReport?.related_results?.length ?? 0}</Text><Text style={styles.metricLabel}>related</Text></View>
          <View style={styles.metric}><Text style={styles.metricValue}>{canonicalGroup?.evidence_summary?.rejected_results ?? discoveryReport?.rejected_results?.length ?? 0}</Text><Text style={styles.metricLabel}>rejected</Text></View>
        </View>
      </Card> : null}

      {loading && !allOffers.length ? <View style={styles.loading}><ActivityIndicator color={tc.color.iris} /><Text style={styles.loadingText}>Checking live provider observations with exact discovery...</Text></View> : null}

      {allOffers.length ? <>
        <SectionHeader title={canonicalGroup ? "Exact provider prices" : "Provider prices"} />
        {allOffers.map(({ product, offer }, index) => <Pressable key={`${offer.provider}:${product.id || index}`} accessibilityRole="button" accessibilityLabel={`Open ${offer.provider} handoff`} style={({ pressed }) => [styles.offer, pressed && styles.pressed]} onPress={() => navigation.navigate('CheckoutHandoff', { product, offer })}>
          <View style={[styles.rank, index === 0 && styles.winnerRank]}><Text style={[styles.rankText, index === 0 && styles.winnerRankText]}>{index + 1}</Text></View>
          <View style={styles.offerCopy}>
            <Text style={styles.provider}>{offer.provider}</Text>
            <Text numberOfLines={1} style={styles.offerName}>{product.name || product.title || query}</Text>
            <Text style={styles.meta}>{offer.deliveryTime || 'Delivery details at handoff'}</Text>
          </View>
          <View style={styles.offerPrice}>
            {index === 0 ? <Text style={styles.winner}>BEST</Text> : null}
            <Text style={styles.price}>{formatCurrency(offer.price, 'INR')}</Text>
          </View>
        </Pressable>)}
      </> : !loading || finished ? <Card style={styles.empty}><Title size="h3">No exact prices yet</Title><Body muted>{unresolvedCount ? `${unresolvedCount} provider checks were unavailable or still pending.` : 'No provider returned a comparable result for this exact product.'}</Body>{triedQueries.length ? <Text style={styles.tried}>Tried: {triedQueries.join(' · ')}</Text> : null}<PrimaryButton label="Try broader search" icon="search" onPress={() => navigation.navigate('AgentSearch', { category, initialQuery: query })} style={styles.emptyAction} /></Card> : null}

      {probableOffers.length ? <>
        <SectionHeader title="Possible matches - not used for best price" />
        <Card tone="iris" style={styles.relatedNotice}><Body muted>These offers have partial evidence but are missing at least one identity-critical factor. They stay visible for review, but TrueCost does not use them for the winner.</Body></Card>
        {probableOffers.slice(0, 6).map(({ product, offer }, index) => <Pressable key={`probable:${offer.provider}:${product.id || index}`} accessibilityRole="button" accessibilityLabel={`Open possible match from ${offer.provider}`} style={({ pressed }) => [styles.offer, styles.probableOffer, pressed && styles.pressed]} onPress={() => navigation.navigate('ProductDetail', { product: { ...product, offers: product.prices, prices: product.prices } })}>
          <View style={styles.rank}><Feather name="help-circle" size={15} color={tc.color.iris} /></View>
          <View style={styles.offerCopy}>
            <Text style={styles.provider}>{offer.provider}</Text>
            <Text numberOfLines={1} style={styles.offerName}>{product.name || product.title || query}</Text>
            <Text style={styles.meta}>Possible match · non-authoritative</Text>
          </View>
          <View style={styles.offerPrice}><Text style={styles.price}>{formatCurrency(offer.price, 'INR')}</Text></View>
        </Pressable>)}
      </> : null}

      {relatedOffers.length ? <>
        <SectionHeader title="Similar results - not compared" />
        <Card tone="amber" style={styles.relatedNotice}><Body muted>These products share words with your selection, but they are different models or brands. They are not used for the best price above.</Body></Card>
        {relatedOffers.slice(0, 6).map(({ product, offer }, index) => <Pressable key={`related:${offer.provider}:${product.id || index}`} accessibilityRole="button" accessibilityLabel={`Open similar result from ${offer.provider}`} style={({ pressed }) => [styles.offer, styles.relatedOffer, pressed && styles.pressed]} onPress={() => navigation.navigate('ProductDetail', { product: { ...product, offers: product.prices, prices: product.prices } })}>
          <View style={styles.rank}><Feather name="layers" size={15} color={tc.color.amber} /></View>
          <View style={styles.offerCopy}>
            <Text style={styles.provider}>{offer.provider}</Text>
            <Text numberOfLines={1} style={styles.offerName}>{product.name || product.title || query}</Text>
            <Text style={styles.meta}>Similar product candidate</Text>
          </View>
          <View style={styles.offerPrice}><Text style={styles.price}>{formatCurrency(offer.price, 'INR')}</Text></View>
        </Pressable>)}
      </> : null}

      {Object.keys(errors).length ? <>
        <SectionHeader title="Provider status" />
        <Card tone="amber" style={styles.statusCard}>{Object.entries(errors).slice(0, 4).map(([provider, error]) => <View key={provider} style={styles.statusRow}><Feather name="alert-circle" size={16} color={tc.color.amber} /><Text style={styles.statusText}>{provider}: {error}</Text></View>)}</Card>
      </> : null}

      {discoveryReport?.provider_status ? <>
        <SectionHeader title="Provider coverage" />
        <Card style={styles.statusCard}>{Object.entries(discoveryReport.provider_status).slice(0, 8).map(([provider, info]: any) => {
          const responded = info.state === 'responded';
          const exact = info.exact_matches || 0;
          const tone = responded && exact > 0 ? tc.color.mint : responded ? tc.color.amber : tc.color.muted;
          return <View key={provider} style={styles.coverageRow}>
            <View style={styles.statusLeft}><Feather name={responded ? 'check-circle' : 'clock'} size={15} color={tone} /><Text style={styles.diagnosticProvider}>{provider}</Text></View>
            <Text style={styles.statusText}>{responded ? `${exact} exact · ${info.probable || 0} probable · ${info.related || 0} related · ${info.rejected || 0} rejected` : 'not returned yet'}</Text>
          </View>;
        })}</Card>
      </> : null}

      {diagnostics?.providers ? <>
        <SectionHeader title="Match diagnostics" />
        <Card style={styles.statusCard}>{Object.entries(diagnostics.providers).slice(0, 4).map(([provider, info]: any) => <View key={provider} style={styles.diagnosticRow}>
          <Text style={styles.diagnosticProvider}>{provider}</Text>
          <Text style={styles.statusText}>{info.exact_matches || 0} exact · {info.probable || 0} probable · {info.related || 0} related · {info.rejected || 0} rejected</Text>
        </View>)}</Card>
      </> : null}
    </ScrollView>

    <ScraperManager key={`${attemptIndex}:${providerQuery}`} category={category} query={providerQuery || query} userLocation={location || undefined} onResults={handleResults} onError={handleError} />
  </Screen>;
}

const styles = StyleSheet.create({
  screen: { paddingHorizontal: tc.space.lg, paddingBottom: 0 },
  content: { paddingBottom: 112 },
  hero: { marginTop: tc.space.md },
  heroRow: { flexDirection: 'row', gap: tc.space.md, alignItems: 'center' },
  image: { width: 88, height: 88, borderRadius: tc.radius.md, backgroundColor: tc.color.surface },
  placeholder: { width: 88, height: 88, borderRadius: tc.radius.md, backgroundColor: tc.color.surface, alignItems: 'center', justifyContent: 'center' },
  heroCopy: { flex: 1, minWidth: 0 },
  kicker: { ...tc.type.eyebrow, color: tc.color.iris, marginBottom: 5 },
  chips: { flexDirection: 'row', flexWrap: 'wrap', gap: tc.space.xs, marginTop: tc.space.sm },
  providerQuery: { ...tc.type.bodySmall, color: tc.color.muted, marginTop: tc.space.xs },
  rule: { height: 1, backgroundColor: '#DAD2FF', marginVertical: tc.space.md },
  summaryRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: tc.space.md },
  summaryLabel: { ...tc.type.eyebrow, color: tc.color.muted },
  bestPrice: { ...tc.type.price, color: tc.color.ink, marginTop: 3 },
  rerun: { minWidth: 108 },
  truth: { marginTop: tc.space.sm },
  evidenceCard: { marginTop: tc.space.md, gap: tc.space.sm },
  evidenceHeader: { flexDirection: 'row', alignItems: 'center', gap: tc.space.xs },
  evidenceTitle: { ...tc.type.label, color: tc.color.ink },
  evidenceGrid: { flexDirection: 'row', gap: tc.space.sm, marginTop: tc.space.xs },
  metric: { flex: 1, borderRadius: tc.radius.sm, backgroundColor: tc.color.surfaceMuted, padding: tc.space.sm },
  metricValue: { ...tc.type.h2, color: tc.color.ink },
  metricLabel: { ...tc.type.bodySmall, color: tc.color.muted },
  loading: { minHeight: 96, alignItems: 'center', justifyContent: 'center', gap: tc.space.sm },
  loadingText: { ...tc.type.bodySmall, color: tc.color.muted, fontWeight: '700' },
  offer: { minHeight: 84, borderRadius: tc.radius.md, borderWidth: 1, borderColor: tc.color.line, backgroundColor: tc.color.surface, marginBottom: tc.space.sm, padding: tc.space.md, flexDirection: 'row', alignItems: 'center', gap: tc.space.sm, ...tc.shadow.card },
  rank: { width: 32, height: 32, borderRadius: 16, backgroundColor: tc.color.surfaceMuted, alignItems: 'center', justifyContent: 'center' },
  winnerRank: { backgroundColor: tc.color.mintSoft },
  rankText: { ...tc.type.label, color: tc.color.muted },
  winnerRankText: { color: tc.color.mint },
  offerCopy: { flex: 1, minWidth: 0 },
  provider: { ...tc.type.h3, color: tc.color.ink },
  offerName: { ...tc.type.bodySmall, color: tc.color.muted, marginTop: 2 },
  meta: { ...tc.type.bodySmall, fontSize: 12, color: tc.color.muted, marginTop: 2 },
  offerPrice: { alignItems: 'flex-end' },
  winner: { ...tc.type.eyebrow, color: tc.color.mint, marginBottom: 2 },
  price: { ...tc.type.h3, color: tc.color.ink, fontVariant: ['tabular-nums'] },
  empty: { marginTop: tc.space.lg },
  emptyAction: { marginTop: tc.space.md },
  tried: { ...tc.type.bodySmall, color: tc.color.muted, marginTop: tc.space.sm },
  statusCard: { gap: tc.space.xs },
  statusRow: { flexDirection: 'row', gap: tc.space.xs, alignItems: 'center' },
  statusLeft: { flexDirection: 'row', gap: tc.space.xs, alignItems: 'center', flex: 1 },
  coverageRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: tc.space.sm },
  statusText: { ...tc.type.bodySmall, color: tc.color.inkSoft, flex: 1 },
  diagnosticRow: { gap: 2 },
  diagnosticProvider: { ...tc.type.label, color: tc.color.ink, textTransform: 'capitalize' },
  relatedNotice: { marginBottom: tc.space.sm },
  probableOffer: { borderColor: '#DAD2FF' },
  relatedOffer: { borderColor: '#F4D5AF' },
  pressed: { opacity: 0.72 },
});


