import React, { useEffect, useMemo, useState } from 'react';
import { ActivityIndicator, Image, Pressable, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { AppHeader, Body, Screen, SectionHeader } from '../components/ui';
import { ProviderHealthPanel } from '../components/ProviderHealthPanel';
import { tc } from '../design/tokens';
import { useUserLocation } from '../location/LocationContext';
import { useSearchHistory } from '../search/SearchHistoryContext';
import { CATEGORY_CATALOG, categoryByName } from '../catalog/categories';
import { getObservedSuggestions, ObservedSearchSuggestion } from '../api/search';

export default function ExploreHub({ navigation, route }: any) {
  const requested = route.params?.category;
  const [category, setCategory] = useState(categoryByName(requested).name);
  const [query, setQuery] = useState(route.params?.initialQuery || '');
  const [observedSuggestions, setObservedSuggestions] = useState<ObservedSearchSuggestion[]>([]);
  const [suggestionsLoading, setSuggestionsLoading] = useState(false);
  const { location } = useUserLocation();
  const { recent, remember, clear } = useSearchHistory();
  useEffect(() => { if (requested) setCategory(categoryByName(requested).name); }, [requested]);
  useEffect(() => { if (route.params?.initialQuery) setQuery(route.params.initialQuery); }, [route.params?.initialQuery]);
  const selected = categoryByName(category);
  const promptSuggestions = useMemo(() => selected.prompts.filter(value => !query || value.toLowerCase().includes(query.toLowerCase())), [selected, query]);
  useEffect(() => {
    const normalized = query.trim();
    if (normalized.length < 2 || selected.mode !== 'search') { setObservedSuggestions([]); setSuggestionsLoading(false); return; }
    let active = true;
    setSuggestionsLoading(true);
    const timer = setTimeout(() => {
      getObservedSuggestions(normalized, selected.engineCategory)
        .then(items => { if (active) setObservedSuggestions(items); })
        .catch(() => { if (active) setObservedSuggestions([]); })
        .finally(() => { if (active) setSuggestionsLoading(false); });
    }, 250);
    return () => { active = false; clearTimeout(timer); };
  }, [query, selected.engineCategory, selected.mode]);

  const openCategory = (item: (typeof CATEGORY_CATALOG)[number]) => {
    const params = { category: item.engineCategory, userLocation: location };
    if (item.route) navigation.navigate(item.route, params);
    else { setCategory(item.name); setQuery(''); }
  };

  const submit = (value = query) => {
    const normalized = value.trim();
    if (!normalized) return;
    remember(normalized, selected.name);
    // Bug #5 fix: Map each category to its proper brand color
    const categoryColor: Record<string, string> = {
      Grocery: '#4CAF50', Shopping: '#FF9900', Food: '#FF5252',
      Pharmacy: '#00BFA5', Mobility: '#222222', Travel: '#1E88E5',
      Finance: '#3F51B5', Productivity: '#673AB7', Hotels: '#9C27B0', Deals: '#F57C00',
    };
    const color = categoryColor[selected.name] || tc.color.iris;
    if (selected.mode === 'decision') navigation.navigate(selected.route || 'CategoryDecision', { category: selected.engineCategory, initialQuery: normalized, userLocation: location });
    else navigation.navigate('AgentSearch', { category: selected.engineCategory, color, initialQuery: normalized, userLocation: location });
  };

  return <Screen>
    <AppHeader subtitle="Search once. Compare clearly." onNotifications={() => navigation.navigate('Notifications')} onProfile={() => navigation.navigate('Profile')} />
    <View style={styles.headingRow}><View style={styles.flex}><Text style={styles.title}>What do you want to compare?</Text><Body muted>Choose a category or describe exactly what you need.</Body></View><View style={styles.spark}><Feather name="zap" size={20} color={tc.color.iris} /></View></View>

    <View style={styles.search}>
      <Feather name="search" size={19} color={tc.color.muted} />
      <TextInput accessibilityLabel="Search TrueCost" value={query} onChangeText={setQuery} onSubmitEditing={() => submit()} placeholder="Product, basket, ride, flight..." placeholderTextColor={tc.color.muted} returnKeyType="search" style={styles.field} />
      {query ? <Pressable accessibilityRole="button" accessibilityLabel="Clear search" hitSlop={8} onPress={() => setQuery('')} style={styles.smallButton}><Feather name="x" size={16} color={tc.color.muted} /></Pressable> : null}
      <Pressable accessibilityRole="button" accessibilityLabel="Run search" disabled={!query.trim()} onPress={() => submit()} style={({ pressed }) => [styles.go, !query.trim() && styles.disabled, pressed && styles.pressed]}><Feather name="arrow-right" size={18} color={tc.color.white} /></Pressable>
    </View>

    <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.chips}>
      {CATEGORY_CATALOG.map(item => <Pressable key={item.id} accessibilityRole="button" accessibilityState={{ selected: item.name === category }} onPress={() => setCategory(item.name)} style={({ pressed }) => [styles.chip, item.name === category && styles.chipSelected, pressed && styles.pressed]}><Feather name={item.icon} size={14} color={item.name === category ? tc.color.white : tc.color.iris} /><Text style={[styles.chipText, item.name === category && styles.chipTextSelected]}>{item.name}</Text></Pressable>)}
    </ScrollView>
    <ProviderHealthPanel categoryId={selected.id} title={`${selected.name} provider readiness`} compact />

    {query ? <><SectionHeader title="Observed suggestions" />{suggestionsLoading ? <View style={styles.message}><ActivityIndicator size="small" color={tc.color.iris} /><Body muted>Matching trusted product observations…</Body></View> : observedSuggestions.length ? <View style={styles.listCard}>{observedSuggestions.map((item, index) => <ProductSuggestion key={`${item.product_id || item.query}:${index}`} item={item} bordered={index > 0} onPress={() => { setQuery(item.query); submit(item.query); }} />)}</View> : promptSuggestions.length ? <View style={styles.listCard}>{promptSuggestions.map((value, index) => <Suggestion key={value} value={value} meta="Search idea" icon="corner-down-right" bordered={index > 0} onPress={() => { setQuery(value); submit(value); }} />)}</View> : <View style={styles.message}><Feather name="search" size={17} color={tc.color.muted} /><Body muted>No observed product matches yet. Search your exact wording to request fresh provider results.</Body></View>}</> : recent.length ? <><SectionHeader title="Recent searches" action="Clear" onAction={clear} /><View style={styles.listCard}>{recent.slice(0, 4).map((item, index) => <Suggestion key={`${item.category}:${item.query}`} value={item.query} meta={item.category} icon="clock" bordered={index > 0} onPress={() => { setCategory(item.category); setQuery(item.query); }} />)}</View></> : <><SectionHeader title={`Search ideas for ${selected.name}`} /><View style={styles.promptRow}>{selected.prompts.map(value => <Pressable key={value} onPress={() => { setQuery(value); submit(value); }} style={({ pressed }) => [styles.prompt, pressed && styles.pressed]}><Feather name="zap" size={14} color={tc.color.iris} /><Text style={styles.promptText}>{value}</Text><Feather name="arrow-up-right" size={14} color={tc.color.muted} /></Pressable>)}</View></>}

    <SectionHeader title="All categories" />
    <View style={styles.grid}>{CATEGORY_CATALOG.map(item => <Pressable key={item.id} accessibilityRole="button" accessibilityLabel={`Open ${item.name}`} onPress={() => openCategory(item)} style={({ pressed }) => [styles.card, pressed && styles.pressed]}>
      <View style={styles.cardTop}><View style={[styles.icon, { backgroundColor: categoryTone(item.id) }]}><Feather name={item.icon} size={19} color={tc.color.iris} /></View><Feather name="arrow-up-right" size={15} color={tc.color.muted} /></View>
      <Text style={styles.cardText}>{item.name}</Text><Text numberOfLines={2} style={styles.description}>{item.description}</Text>
    </Pressable>)}</View>
  </Screen>;
}

function Suggestion({ value, meta, icon, bordered, onPress }: { value: string; meta?: string; icon: React.ComponentProps<typeof Feather>['name']; bordered?: boolean; onPress: () => void }) {
  return <Pressable accessibilityRole="button" style={({ pressed }) => [styles.suggestion, bordered && styles.bordered, pressed && styles.pressed]} onPress={onPress}><View style={styles.suggestionIcon}><Feather name={icon} size={15} color={tc.color.iris} /></View><View style={styles.flex}><Text style={styles.suggestionText}>{value}</Text>{meta ? <Text style={styles.suggestionMeta}>{meta}</Text> : null}</View><Feather name="arrow-up-left" size={15} color={tc.color.muted} /></Pressable>;
}

function ProductSuggestion({ item, bordered, onPress }: { item: ObservedSearchSuggestion; bordered?: boolean; onPress: () => void }) {
  return <Pressable accessibilityRole="button" accessibilityLabel={`Search ${item.query}`} style={({ pressed }) => [styles.productSuggestion, bordered && styles.bordered, pressed && styles.pressed]} onPress={onPress}>
    {item.image_url ? <Image source={{ uri: item.image_url }} resizeMode="contain" style={styles.suggestionImage} /> : <View style={styles.suggestionImageFallback}><Feather name="package" size={18} color={tc.color.iris} /></View>}
    <View style={styles.flex}><Text numberOfLines={2} style={styles.suggestionText}>{item.query}</Text><Text style={styles.suggestionMeta}>{[item.brand, item.provider_count ? `${item.provider_count} observed provider${item.provider_count === 1 ? '' : 's'}` : 'Observed product'].filter(Boolean).join(' · ')}</Text></View>
    <Feather name="arrow-up-left" size={15} color={tc.color.muted} />
  </Pressable>;
}

const categoryTone = (id: string) => ({ grocery: '#EEFAF2', shopping: '#F3EEFF', food: '#FFF3EA', pharmacy: '#EAF8F4', mobility: '#EAF6FF', travel: '#F2EEFF', hotels: '#F7EDFF', deals: '#FFF2E8', finance: '#EAF8F4', services: '#F2F3F9' }[id] || tc.color.irisSoft);

const styles = StyleSheet.create({
  flex: { flex: 1 }, pressed: { opacity: 0.7 }, disabled: { opacity: 0.35 },
  headingRow: { marginTop: 18, flexDirection: 'row', alignItems: 'center', gap: 12 }, title: { color: tc.color.ink, fontSize: 24, lineHeight: 30, fontWeight: '800', letterSpacing: -0.6, marginBottom: 4 }, spark: { width: 48, height: 48, borderRadius: 17, backgroundColor: tc.color.irisSoft, alignItems: 'center', justifyContent: 'center' },
  search: { minHeight: 54, marginTop: 16, borderRadius: tc.radius.sm, borderWidth: 1.5, borderColor: '#D8D1FA', backgroundColor: tc.color.surface, flexDirection: 'row', alignItems: 'center', paddingLeft: 14, paddingRight: 6, gap: 9, ...tc.shadow.card }, field: { flex: 1, minHeight: 50, color: tc.color.ink, fontSize: 14 }, smallButton: { width: 36, height: 40, alignItems: 'center', justifyContent: 'center' }, go: { width: 42, height: 42, borderRadius: 11, backgroundColor: tc.color.iris, alignItems: 'center', justifyContent: 'center' },
  chips: { gap: 7, paddingTop: 10, paddingBottom: 2, paddingRight: 18 }, chip: { minHeight: 38, paddingHorizontal: 12, borderRadius: tc.radius.pill, borderWidth: 1, borderColor: tc.color.line, backgroundColor: tc.color.surface, flexDirection: 'row', alignItems: 'center', gap: 6 }, chipSelected: { backgroundColor: tc.color.iris, borderColor: tc.color.iris }, chipText: { color: tc.color.inkSoft, fontSize: 11, fontWeight: '700' }, chipTextSelected: { color: tc.color.white },
  listCard: { borderRadius: tc.radius.md, borderWidth: 1, borderColor: tc.color.line, backgroundColor: tc.color.surface, paddingHorizontal: 12 }, suggestion: { minHeight: 57, flexDirection: 'row', alignItems: 'center', gap: 10 }, bordered: { borderTopWidth: 1, borderTopColor: tc.color.line }, suggestionIcon: { width: 32, height: 32, borderRadius: 11, backgroundColor: tc.color.irisSoft, alignItems: 'center', justifyContent: 'center' }, suggestionText: { color: tc.color.ink, fontSize: 12, lineHeight: 17, fontWeight: '700' }, suggestionMeta: { color: tc.color.muted, fontSize: 9, marginTop: 2 },
  productSuggestion: { minHeight: 68, flexDirection: 'row', alignItems: 'center', gap: 10, paddingVertical: 7 }, suggestionImage: { width: 48, height: 48, borderRadius: 12, backgroundColor: tc.color.surfaceMuted }, suggestionImageFallback: { width: 48, height: 48, borderRadius: 12, backgroundColor: tc.color.irisSoft, alignItems: 'center', justifyContent: 'center' },
  message: { minHeight: 58, paddingHorizontal: 14, borderRadius: tc.radius.md, borderWidth: 1, borderColor: tc.color.line, backgroundColor: tc.color.surface, flexDirection: 'row', alignItems: 'center', gap: 10 }, promptRow: { gap: 7 }, prompt: { minHeight: 47, paddingHorizontal: 13, borderRadius: tc.radius.sm, backgroundColor: tc.color.irisSoft, flexDirection: 'row', alignItems: 'center', gap: 9 }, promptText: { flex: 1, color: tc.color.inkSoft, fontSize: 12, fontWeight: '700' },
  grid: { flexDirection: 'row', flexWrap: 'wrap', justifyContent: 'space-between', rowGap: 10 }, card: { width: '48.5%', minHeight: 126, padding: 13, borderRadius: tc.radius.md, backgroundColor: tc.color.surface, borderWidth: 1, borderColor: tc.color.line, ...tc.shadow.card }, cardTop: { flexDirection: 'row', alignItems: 'flex-start', justifyContent: 'space-between' }, icon: { width: 40, height: 40, borderRadius: 14, alignItems: 'center', justifyContent: 'center' }, cardText: { color: tc.color.ink, fontSize: 13, lineHeight: 18, fontWeight: '800', marginTop: 9 }, description: { color: tc.color.muted, fontSize: 9, lineHeight: 13, marginTop: 2 },
});
