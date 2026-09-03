import React, { useState, useCallback, useEffect, useRef, useMemo } from 'react';
import {
  View, Text, StyleSheet, ScrollView, TouchableOpacity,
  SafeAreaView, KeyboardAvoidingView, Platform, ActivityIndicator,
  LayoutAnimation
} from 'react-native';
import { Feather } from '@expo/vector-icons';
import ScraperManager from '../components/core/ScraperManager';
import ProductCard from '../components/ProductCard';
import type { ProductProps, ProviderPrice } from '../components/ProductCard';
import SkeletonCard from '../components/SkeletonCard';
import RideCompareCard, { RideOffer } from '../components/RideCompareCard';
import RestaurantCard from '../components/RestaurantCard';
import FlightCard from '../components/FlightCard';
import PlanCard from '../components/PlanCard';
import InlineComparisonCard, {
  InlineComparisonGroup,
  InlineProviderOffer,
  ProviderCoverageStrip,
  ProviderState,
} from '../components/InlineComparisonCard';
import { IntentEngine, Category } from '../utils/IntentEngine';
import MobilityInput from '../components/inputs/MobilityInput';
import TravelInput from '../components/inputs/TravelInput';
import UniversalInput from '../components/inputs/UniversalInput';
import { API_BASE } from '../config';
import { useAuth } from '../auth/AuthContext';
import { tc } from '../design/tokens';

// ─── Types ───────────────────────────────────────────────────────────────────

interface SearchIntelligence {
  raw_query: string;
  corrected_query: string;
  specificity: string;
  correction_confidence: 'HIGH' | 'MEDIUM' | 'LOW';
  show_correction_banner: boolean;
  correction_banner_text: string;   // "Showing results for Noise Airwave Max 6"
  correction_alt_text: string;      // "Search instead for 'noise airmax 6'"
  parsed: {
    brand: string | null;
    product_family: string | null;
    model: string | null;
    product_type: string | null;
    features: string[];
    price_constraint: { min?: number; max?: number } | null;
  };
  hypotheses: string[];
  corrections: Array<{ original: string; corrected: string; confidence: number; type: string }>;
}

interface CanonicalOffer {
  offer_id?: string;
  provider: string;
  price?: number | null;
  original_price?: number | null;
  currency?: string;
  delivery_time?: string | null;
  deep_link?: string | null;
  product_url?: string | null;
  app_deep_link?: string | null;
  fallback_search_url?: string | null;
  handoff_confidence?: string | null;
  image_url?: string | null;
  raw_image_url?: string | null;
  image_match_status?: string | null;
  image_source_provider?: string | null;
  image_source_product_id?: string | null;
  image_source_variant_id?: string | null;
  in_stock?: boolean | null;
  serviceable?: boolean | null;
  freshness?: string | Record<string, any> | null;
  product?: ProductProps | Record<string, any> | null;
  evidence?: Record<string, any>;
}

interface CanonicalOfferGroup {
  group_id: string;
  title: string;
  image_url?: string | null;
  category?: string;
  offers?: CanonicalOffer[];
  provider_status?: Record<string, ProviderState>;
  explanation?: string | null;
  evidence_summary?: InlineComparisonGroup['evidenceSummary'];
}

interface DiscoveryReport {
  canonical_offer_groups?: CanonicalOfferGroup[];
}

interface SearchState {
  primary: ProductProps[];
  probable: ProductProps[];
  recommendations: ProductProps[];
  providersResponded: string[];
  providersPending: string[];
  sessionId: string | null;
  searchIntelligence: SearchIntelligence | null;
  discoveryReport: DiscoveryReport | null;
  diagnostics: Record<string, any> | null;
}

const EMPTY_STATE: SearchState = {
  primary: [],
  probable: [],
  recommendations: [],
  providersResponded: [],
  providersPending: [],
  sessionId: null,
  searchIntelligence: null,
  discoveryReport: null,
  diagnostics: null,
};

const CATEGORY_RESULT_LABELS: Record<string, { primary: string; unit: string }> = {
  Grocery: { primary: 'Decision feed', unit: 'products' },
  Shopping: { primary: 'Decision feed', unit: 'products' },
  Pharmacy: { primary: 'Decision feed', unit: 'medicines' },
  Mobility: { primary: 'Ride options', unit: 'ride classes' },
  Food: { primary: 'Dish and restaurant options', unit: 'options' },
  Travel: { primary: 'Itinerary options', unit: 'fares' },
  Finance: { primary: 'Plan and rate options', unit: 'offers' },
  Productivity: { primary: 'Plan options', unit: 'plans' },
};

function createSearchSessionId() {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, token => {
    const value = Math.floor(Math.random() * 16);
    const nibble = token === 'x' ? value : (value & 0x3) | 0x8;
    return nibble.toString(16);
  });
}

function normalizeText(value?: string | null) {
  return (value || '').trim();
}

function canonicalName(product: ProductProps) {
  return normalizeText(product.name).toLowerCase();
}

function productVariant(product: ProductProps) {
  return normalizeText(product.weightVolume || product.weight_volume || product.weight).toLowerCase();
}

function productImage(product: ProductProps) {
  return product.imageUrl || product.image_url || null;
}

function productSubtitle(product: ProductProps) {
  const bits = [product.brand, product.weightVolume || product.weight_volume || product.weight].filter(Boolean);
  return bits.join(' | ');
}

function groupKey(product: ProductProps) {
  return [canonicalName(product), productVariant(product), normalizeText(product.brand).toLowerCase()].join('|');
}

function offerPrice(offer: ProviderPrice) {
  return typeof offer.price === 'number' && Number.isFinite(offer.price) ? offer.price : null;
}

function productOffer(product: ProductProps, offer: ProviderPrice, index: number): InlineProviderOffer {
  return {
    id: `${product.id}-${offer.provider || 'provider'}-${index}`,
    provider: offer.provider || product.brand || 'Provider',
    price: offerPrice(offer),
    originalPrice: offer.originalPrice ?? offer.original_price ?? null,
    deliveryTime: offer.deliveryTime ?? offer.delivery_time ?? null,
    deepLink: offer.deepLink ?? offer.deep_link ?? null,
    productUrl: offer.productUrl ?? offer.product_url ?? null,
    appDeepLink: offer.appDeepLink ?? offer.app_deep_link ?? null,
    fallbackSearchUrl: offer.fallbackSearchUrl ?? offer.fallback_search_url ?? null,
    handoffConfidence: offer.handoffConfidence ?? offer.handoff_confidence ?? null,
    weightVolume: product.weightVolume || product.weight_volume || product.weight || null,
    isBest: offer.isBest ?? offer.is_best ?? false,
    inStock: offer.inStock ?? offer.in_stock ?? null,
    serviceable: offer.serviceable ?? null,
    imageUrl: productImage(product),
    product,
  };
}

function groupsFromProducts(
  products: ProductProps[],
  category: Category | 'All',
  confidence: 'exact' | 'probable' | 'related'
): InlineComparisonGroup[] {
  const map = new Map<string, InlineComparisonGroup>();

  products.forEach(product => {
    const key = groupKey(product) || product.id;
    const existing = map.get(key);
    const offers = (product.prices || []).map((offer, index) => productOffer(product, offer, index));
    const providerStatus = offers.reduce<Record<string, ProviderState>>((acc, offer) => {
      acc[offer.provider] = { state: 'responded', exact_matches: confidence === 'exact' ? 1 : 0 };
      return acc;
    }, {});

    if (existing) {
      const seen = new Set(existing.offers.map(offer => `${offer.provider}|${offer.price}|${offer.weightVolume}`));
      offers.forEach(offer => {
        const offerKey = `${offer.provider}|${offer.price}|${offer.weightVolume}`;
        if (!seen.has(offerKey)) existing.offers.push(offer);
      });
      existing.providerStatus = { ...existing.providerStatus, ...providerStatus };
      return;
    }

    map.set(key, {
      id: key || product.id,
      title: product.name,
      subtitle: productSubtitle(product),
      category: product.category || (category === 'All' ? 'Shopping' : category),
      imageUrl: productImage(product),
      offers,
      providerStatus,
      confidence,
      explanation:
        confidence === 'exact'
          ? 'Exact provider matches are ranked here. Probable and related items stay below.'
          : undefined,
    });
  });

  return Array.from(map.values());
}

function groupsFromCanonical(
  discoveryReport: DiscoveryReport | null,
  category: Category | 'All'
): InlineComparisonGroup[] {
  const canonicalGroups = discoveryReport?.canonical_offer_groups || [];
  return canonicalGroups.map(group => ({
    id: group.group_id,
    title: group.title,
    category: group.category || (category === 'All' ? 'Shopping' : category),
    imageUrl: group.image_url || null,
    offers: (group.offers || []).map((offer, index) => ({
      id: offer.offer_id || `${group.group_id}-${offer.provider}-${index}`,
      provider: offer.provider,
      price: offer.price ?? null,
      originalPrice: offer.original_price ?? null,
      currency: offer.currency || 'INR',
      deliveryTime: offer.delivery_time ?? null,
      deepLink: offer.deep_link ?? null,
      productUrl: offer.product_url ?? null,
      appDeepLink: offer.app_deep_link ?? null,
      fallbackSearchUrl: offer.fallback_search_url ?? null,
      handoffConfidence: offer.handoff_confidence ?? null,
      imageUrl: offer.image_url ?? null,
      imageMatchStatus: offer.image_match_status ?? null,
      imageSourceProvider: offer.image_source_provider ?? null,
      imageSourceProductId: offer.image_source_product_id ?? null,
      imageSourceVariantId: offer.image_source_variant_id ?? null,
      inStock: offer.in_stock ?? null,
      serviceable: offer.serviceable ?? null,
      freshness: offer.freshness ?? null,
      weightVolume:
        normalizeText((offer.product as any)?.weightVolume || (offer.product as any)?.weight_volume || (offer.product as any)?.weight) || null,
      unitPrice: normalizeText(offer.evidence?.unit_price || offer.evidence?.unitPrice) || null,
      product: offer.product || null,
    })),
    providerStatus: group.provider_status,
    explanation: group.explanation,
    confidence: 'exact',
    evidenceSummary: group.evidence_summary || null,
  }));
}

function uniqueRecommendations(primary: ProductProps[], probable: ProductProps[], recommendations: ProductProps[]) {
  const blocked = new Set([...primary, ...probable].map(item => groupKey(item)));
  return recommendations.filter(item => !blocked.has(groupKey(item)));
}

function providerKey(provider: string) {
  const key = provider.toLowerCase().trim();
  if (key.includes('swiggy')) return 'swiggy';
  if (key.includes('blinkit')) return 'blinkit';
  if (key.includes('zepto')) return 'zepto';
  if (key.includes('bigbasket') || key.includes('big basket')) return 'bigbasket';
  return key;
}

function providerFailureState(error: string): ProviderState {
  const text = error.toLowerCase();
  const diagnostics = { message: error.slice(0, 900) };
  if (text.includes('challenge') || text.includes('http_403') || text.includes('blocked')) {
    return { state: 'blocked', match_status: 'unknown', ...diagnostics };
  }
  if (text.includes('rate_limited') || text.includes('429')) {
    return { state: 'rate_limited', match_status: 'unknown', ...diagnostics };
  }
  if (text.includes('location_failure')) {
    return { state: 'location_unavailable', match_status: 'unknown', ...diagnostics };
  }
  if (text.includes('parser_regression') || text.includes('dom_selector_mismatch') || text.includes('schema_changed')) {
    return { state: 'parser_failure', match_status: 'unknown', ...diagnostics };
  }
  if (text.includes('html_response_no_json') || text.includes('no_candidate_api_response') || text.includes('empty_provider_response')) {
    return { state: 'provider_unavailable', match_status: 'unknown', ...diagnostics };
  }
  if (text.includes('timeout') || text.includes('did not emit')) return { state: 'timeout', match_status: 'unknown', ...diagnostics };
  if (text.includes('parse')) return { state: 'parser_failure', match_status: 'unknown', ...diagnostics };
  if (text.includes('network') || text.includes('failed to load')) return { state: 'network_failure', match_status: 'unknown', ...diagnostics };
  return { state: 'unavailable', match_status: 'unknown', ...diagnostics };
}

function mergeProviderFailures(
  providerStatus: Record<string, ProviderState> | undefined,
  failures: Record<string, ProviderState>
) {
  const merged = { ...(providerStatus || {}) };
  Object.entries(failures).forEach(([provider, state]) => {
    const existingKey = Object.keys(merged).find(key => providerKey(key) === provider);
    const targetKey = existingKey || provider;
    const existing = merged[targetKey] || {};
    const existingState = String(existing.state || '').toLowerCase();
    const existingMatch = String(existing.match_status || '').toLowerCase();
    const providerAlreadyAnswered =
      existingState === 'responded' ||
      existingMatch === 'exact' ||
      existingMatch === 'no_match' ||
      (existing.observed || 0) > 0 ||
      (existing.exact_matches || 0) > 0;
    if (!providerAlreadyAnswered) {
      merged[targetKey] = { ...existing, ...state };
    }
  });
  return merged;
}

// ─── Component ────────────────────────────────────────────────────────────────

export default function AgentSearchScreen({ route, navigation }: any) {
  const { category: initialCategory, color: initialColor, userLocation, initialQuery } = route.params;
  const { session } = useAuth();

  const [category, setCategory] = useState<Category | 'All'>(initialCategory || 'All');
  const [color, setColor] = useState(initialColor || tc.color.iris);

  const [searchQuery, setSearchQuery] = useState(initialQuery || '');
  const [searchTrigger, setSearchTrigger] = useState('');
  const [searchState, setSearchState] = useState<SearchState>(EMPTY_STATE);
  const [isLoading, setIsLoading] = useState(false);
  const [liveLog, setLiveLog] = useState('');
  const [providersChecked, setProvidersChecked] = useState<string[]>([]);
  const [providerFailures, setProviderFailures] = useState<Record<string, ProviderState>>({});

  // Ref to hold the live session_id so handleResults always has the latest value
  const sessionIdRef = useRef<string | null>(null);
  const activeQueryRef = useRef<string>('');
  const providersSucceededRef = useRef<Set<string>>(new Set());
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);

  // ─── Search: kick off scrapers ──────────────────────────────────────────────

  const handleSearch = useCallback(async (queryOverride?: string) => {
    const q = (queryOverride ?? searchQuery).trim();
    if (!q) return;

    // Detect Intent and switch category if needed
    let detectedCategory = IntentEngine.detectCategory(q);
    
    // If starting from 'All' and no intent detected, default to Shopping
    if (!detectedCategory && category === 'All') {
      detectedCategory = 'Shopping';
    }

    if (detectedCategory) {
      setCategory(detectedCategory);
      // Hardcode colors for now, ideally pull from a central theme map
      if (detectedCategory === 'Food') setColor('#FF5252');
      else if (detectedCategory === 'Mobility') setColor('#000000');
      else if (detectedCategory === 'Travel') setColor('#1E88E5');
      else if (detectedCategory === 'Shopping') setColor('#FF9900');
      else if (detectedCategory === 'Pharmacy') setColor('#00BFA5');
      else if (detectedCategory === 'Finance') setColor('#3F51B5');
      else if (detectedCategory === 'Productivity') setColor('#673AB7');
      else if (detectedCategory === 'Grocery') setColor('#4CAF50');
    }

    LayoutAnimation.configureNext(LayoutAnimation.Presets.easeInEaseOut);
    // Reset all state
    setSearchState(EMPTY_STATE);
    sessionIdRef.current = createSearchSessionId();
    activeQueryRef.current = q;
    providersSucceededRef.current = new Set();
    setIsLoading(true);
    setProvidersChecked([]);
    setProviderFailures({});
    setLiveLog('⚡ Connecting to live price sources...');
    setSearchTrigger(q);

    // Global Logical Timeout: Prevent infinite loading if scrapers hang or fail
    if (timeoutRef.current) clearTimeout(timeoutRef.current);
    timeoutRef.current = setTimeout(() => {
      setIsLoading(false);
      setLiveLog('Search completed or timed out.');
    }, 35000); // Wait long enough for the slowest grocery WebView terminal state.

  }, [searchQuery, category]);

  useEffect(() => {
    if (initialQuery) handleSearch(initialQuery);
    return () => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
    };
  }, [initialQuery]);

  // ─── Refresh search results from backend using session_id ───────────────────

  const refreshResults = useCallback(async () => {
    const sid = sessionIdRef.current;
    const q = activeQueryRef.current;
    if (!sid || !q) return;

    try {
      const res = await fetch(
        `${API_BASE}/search?q=${encodeURIComponent(q)}&category=${encodeURIComponent(category)}&session_id=${sid}`
      );
      if (!res.ok) return;
      const data = await res.json();
      (data.providers_responded || []).forEach((provider: string) => {
        providersSucceededRef.current.add(providerKey(provider));
      });

      LayoutAnimation.configureNext(LayoutAnimation.Presets.easeInEaseOut);
      setSearchState({
        primary: (data.primary_results || []) as ProductProps[],
        probable: (data.probable_results || []) as ProductProps[],
        recommendations: (data.recommendations || []) as ProductProps[],
        providersResponded: data.providers_responded || [],
        providersPending: data.providers_pending || [],
        sessionId: sid,
        searchIntelligence: data.search_intelligence || null,
        discoveryReport: data.discovery_report || null,
        diagnostics: data.diagnostics || null,
      });
    } catch (e) {
      console.log('[RefreshResults]', e);
    }
  }, [category]);

  // ─── Handle raw scraper data coming back ────────────────────────────────────

  const handleResults = useCallback(async (provider: string, data: any) => {
    if (!data || (typeof data === 'object' && !Array.isArray(data) && Object.keys(data).length === 0)) return;

    LayoutAnimation.configureNext(LayoutAnimation.Presets.easeInEaseOut);
    setLiveLog(`✅ ${provider} prices received!`);
    setProvidersChecked(prev => [...new Set([...prev, provider])]);
    providersSucceededRef.current.add(providerKey(provider));
    setProviderFailures(prev => {
      const next = { ...prev };
      delete next[providerKey(provider)];
      return next;
    });
    setIsLoading(false);
    // Bug #4 fix: Clear the live log after a brief moment so it doesn't linger with results
    setTimeout(() => setLiveLog(''), 2000);

    try {
      const headers: Record<string, string> = { 'Content-Type': 'application/json' };
      if (session?.access_token) headers['Authorization'] = `Bearer ${session.access_token}`;

      const res = await fetch(`${API_BASE}/ingest`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          provider,
          query: activeQueryRef.current,
          category,
          raw_data: data,
          search_session_id: sessionIdRef.current,
          selected_location: userLocation ? {
            latitude: userLocation.latitude,
            longitude: userLocation.longitude,
            postal_code: userLocation.postalCode,
            display: userLocation.display,
            source: userLocation.source,
          } : null,
        }),
      });

      if (!res.ok) {
        const body = await res.text().catch(() => '');
        throw new Error(`Ingest failed (${res.status}) ${body.slice(0, 300)}`);
      }

      // Capture the session_id from the response header on first ingest
      const newSessionId = res.headers.get('X-Search-Session-Id');
      if (newSessionId && !sessionIdRef.current) {
        sessionIdRef.current = newSessionId;
      }

      // After every ingest, re-query the backend for smart structured results
      await refreshResults();

    } catch (err: any) {
      console.log(`[Ingest Error - ${provider}]`, err.message);
    }
  }, [category, session, refreshResults, userLocation]);

  const handleScraperError = useCallback((provider: string, err: string) => {
    const key = providerKey(provider);
    if (providersSucceededRef.current.has(key)) return;
    console.log(`[Scraper] ${provider}: ${err}`);
    setProviderFailures(prev => ({
      ...prev,
      [key]: providerFailureState(err),
    }));
  }, []);

  // ─── Derived totals ─────────────────────────────────────────────────────────

  const comparisonGroups = useMemo(() => {
    const canonicalGroups = groupsFromCanonical(searchState.discoveryReport, category);
    return canonicalGroups.length > 0
      ? canonicalGroups
      : groupsFromProducts(searchState.primary, category, 'exact');
  }, [category, searchState.discoveryReport, searchState.primary]);

  const probableGroups = useMemo(
    () => groupsFromProducts(searchState.probable, category, 'probable'),
    [category, searchState.probable]
  );

  const relatedGroups = useMemo(
    () => groupsFromProducts(
      uniqueRecommendations(searchState.primary, searchState.probable, searchState.recommendations),
      category,
      'related'
    ),
    [category, searchState.primary, searchState.probable, searchState.recommendations]
  );

  const totalResults = comparisonGroups.length + probableGroups.length + relatedGroups.length;

  // ─── Render helpers ─────────────────────────────────────────────────────────

  const openProductDetails = useCallback((product?: ProductProps | Record<string, any> | null) => {
    if (!product) return;
    navigation.navigate('ProductDetail', {
      product,
      provenance: 'inline_comparison_result',
    });
  }, [navigation]);

  const openFocusedCompare = useCallback((group: InlineComparisonGroup) => {
    navigation.navigate('FocusedCompare', {
      category: group.category || category,
      color,
      query: group.title,
      initialQuery: group.title,
      product: group.offers[0]?.product || {
        id: group.id,
        name: group.title,
        category: group.category,
        imageUrl: group.imageUrl || undefined,
        prices: group.offers,
      },
      focusProductId: group.id,
      provenance: 'inline_comparison_deep_check',
    });
  }, [category, color, navigation]);

  const renderProviderBadges = () => {
    const providersResponded = [...new Set([...searchState.providersResponded, ...providersChecked])];
    if (providersResponded.length === 0 && searchState.providersPending.length === 0) return null;
    const providerStatus = mergeProviderFailures(
      Object.fromEntries([
        ...providersResponded.map(provider => [provider, { state: 'responded', exact_matches: 1 }] as [string, ProviderState]),
        ...searchState.providersPending.map(provider => [provider, { state: 'pending' }] as [string, ProviderState]),
      ]),
      providerFailures
    );

    return (
      <View style={styles.coverageWrap}>
        <ProviderCoverageStrip
          providerStatus={providerStatus}
          compact
        />
      </View>
    );
  };

  // ─── Category-aware helpers ──────────────────────────────────────────────────

  const getPrimaryLabel = () => {
    return CATEGORY_RESULT_LABELS[category]?.primary || 'Decision feed';
  };

  const getCategoryLayout = () => {
    switch (category) {
      case 'Mobility': return 'ride';
      case 'Food': return 'restaurant';
      case 'Travel': return 'travel';
      case 'Productivity': return 'plan';
      case 'Finance': return 'finance';
      default: return 'product';
    }
  };

  const getEmptyPrompt = () => {
    switch (category) {
      case 'Mobility': return 'Enter a destination to compare Uber, Ola & Rapido fares';
      case 'Food': return 'Search for a restaurant or dish to compare Zomato & Swiggy prices';
      case 'Travel': return 'Search for a flight route (e.g. "Delhi to Mumbai")';
      case 'Pharmacy': return 'Search for a medicine to compare prices across 1mg, PharmEasy & Apollo';
      case 'Shopping': return 'Search for any product to compare Amazon, Flipkart & Meesho prices';
      case 'Productivity': return 'Search for a tool (e.g. "Notion", "Figma") to compare plan prices';
      case 'Finance': return 'Search for a product (e.g. "Home Loan", "Term Insurance") to compare rates';
      default: return `Search any product to see the best price across all ${category} providers.`;
    }
  };

  const renderPrimarySection = () => {
    if (comparisonGroups.length === 0) return null;
    const unit = CATEGORY_RESULT_LABELS[category]?.unit || 'matches';

    return (
      <View>
        <View style={styles.sectionHeaderRow}>
          <View style={[styles.sectionAccent, { backgroundColor: color }]} />
          <Text style={styles.sectionTitle}>{getPrimaryLabel()}</Text>
          <Text style={styles.sectionCount}>{comparisonGroups.length} {unit}</Text>
        </View>
        {comparisonGroups.map((group, index) => (
          <InlineComparisonCard
            key={`${group.id}-exact-${index}`}
            group={{ ...group, providerStatus: mergeProviderFailures(group.providerStatus, providerFailures) }}
            onOpenDetails={openProductDetails}
            onDeepCompare={openFocusedCompare}
          />
        ))}
      </View>
    );
  };

  const renderRecommendationsSection = () => {
    if (probableGroups.length === 0 && relatedGroups.length === 0) return null;

    return (
      <View>
        {probableGroups.length > 0 ? (
          <View>
            <View style={[styles.sectionHeaderRow, { marginTop: tc.space.lg }]}>
              <View style={[styles.sectionAccent, { backgroundColor: tc.color.amber }]} />
              <Text style={styles.sectionTitle}>Review possible matches</Text>
              <Text style={styles.sectionCount}>{probableGroups.length} probable</Text>
            </View>
            {probableGroups.map((group, index) => (
              <InlineComparisonCard
                key={`${group.id}-probable-${index}`}
                group={{ ...group, providerStatus: mergeProviderFailures(group.providerStatus, providerFailures) }}
                compact
                onOpenDetails={openProductDetails}
                onDeepCompare={openFocusedCompare}
              />
            ))}
          </View>
        ) : null}

        {relatedGroups.length > 0 ? (
          <View>
            <View style={[styles.sectionHeaderRow, { marginTop: tc.space.lg }]}>
              <View style={[styles.sectionAccent, { backgroundColor: tc.color.lineStrong }]} />
              <Text style={styles.sectionTitle}>Similar, not compared</Text>
              <Text style={styles.sectionCount}>{relatedGroups.length} related</Text>
            </View>
            {relatedGroups.map((group, index) => (
              <InlineComparisonCard
                key={`${group.id}-related-${index}`}
                group={{ ...group, providerStatus: mergeProviderFailures(group.providerStatus, providerFailures) }}
                compact
                onOpenDetails={openProductDetails}
                onDeepCompare={openFocusedCompare}
              />
            ))}
          </View>
        ) : null}
      </View>
    );
  };

  const renderLegacyPrimarySection = () => {
    if (searchState.primary.length === 0) return null;
    const layout = getCategoryLayout();

    // ── Mobility: group by ride name, show provider comparison per group ──
    if (layout === 'ride') {
      const groups: Record<string, RideOffer[]> = {};
      searchState.primary.forEach(item => {
        const key = item.name;
        if (!groups[key]) groups[key] = [];
        const price = item.prices?.[0];
        groups[key].push({
          id: item.id,
          name: item.name,
          brand: price?.provider ?? item.brand ?? 'Unknown',
          price: price?.price ?? 0,
          originalPrice: price?.originalPrice ?? undefined,
          deliveryTime: price?.deliveryTime ?? '',
          deepLink: price?.deepLink ?? '',
          weightVolume: item.weightVolume ?? '',
        });
      });
      return (
        <View>
          <View style={styles.sectionHeaderRow}>
            <View style={[styles.sectionAccent, { backgroundColor: color }]} />
            <Text style={styles.sectionTitle}>{getPrimaryLabel()}</Text>
            <Text style={styles.sectionCount}>{Object.keys(groups).length} ride types</Text>
          </View>
          {Object.entries(groups).map(([rideName, offers]) => (
            <RideCompareCard key={rideName} rideName={rideName} offers={offers} />
          ))}
        </View>
      );
    }

    // ── Food: restaurant cards ──
    if (layout === 'restaurant') {
      return (
        <View>
          <View style={styles.sectionHeaderRow}>
            <View style={[styles.sectionAccent, { backgroundColor: color }]} />
            <Text style={styles.sectionTitle}>{getPrimaryLabel()}</Text>
            <Text style={styles.sectionCount}>{searchState.primary.length} restaurants</Text>
          </View>
          {searchState.primary.map(item => {
            const price = item.prices?.[0];
            return (
              <RestaurantCard
                key={item.id}
                id={item.id}
                name={item.name}
                brand={price?.provider ?? item.brand ?? 'Food'}
                pricePerPerson={price?.price ?? 0}
                deliveryTime={price?.deliveryTime ?? ''}
                imageUrl={item.imageUrl ?? ''}
                deepLink={price?.deepLink ?? ''}
              />
            );
          })}
        </View>
      );
    }

    // ── Travel: flight cards ──
    if (layout === 'travel') {
      return (
        <View>
          <View style={styles.sectionHeaderRow}>
            <View style={[styles.sectionAccent, { backgroundColor: color }]} />
            <Text style={styles.sectionTitle}>{getPrimaryLabel()}</Text>
            <Text style={styles.sectionCount}>{searchState.primary.length} flights</Text>
          </View>
          {searchState.primary.map(item => {
            const price = item.prices?.[0];
            return (
              <FlightCard
                key={item.id}
                id={item.id}
                airlineName={item.name}
                price={price?.price ?? 0}
                duration={item.weightVolume ?? price?.deliveryTime ?? ''}
                brand={price?.provider ?? item.brand ?? 'Travel'}
                deepLink={price?.deepLink ?? ''}
              />
            );
          })}
        </View>
      );
    }

    // ── Productivity: plan comparison cards ──
    if (layout === 'plan' || layout === 'finance') {
      const sectionLabel = layout === 'plan' ? 'Plans Available' : 'Products Found';
      return (
        <View>
          <View style={styles.sectionHeaderRow}>
            <View style={[styles.sectionAccent, { backgroundColor: color }]} />
            <Text style={styles.sectionTitle}>{getPrimaryLabel()}</Text>
            <Text style={styles.sectionCount}>{searchState.primary.length} {sectionLabel}</Text>
          </View>
          {searchState.primary.map(item => {
            const price = item.prices?.[0];
            return (
              <PlanCard
                key={item.id}
                id={item.id}
                name={item.name}
                brand={price?.provider ?? item.brand ?? category}
                price={price?.price ?? 0}
                weightVolume={item.weightVolume ?? ''}
                deliveryTime={price?.deliveryTime ?? ''}
                deepLink={price?.deepLink ?? ''}
              />
            );
          })}
        </View>
      );
    }

    // ── Default: product cards (Grocery, Pharmacy, Shopping) ──
    return (
      <View>
        <View style={styles.sectionHeaderRow}>
          <View style={[styles.sectionAccent, { backgroundColor: color }]} />
          <Text style={styles.sectionTitle}>{getPrimaryLabel()}</Text>
          <Text style={styles.sectionCount}>{searchState.primary.length} products</Text>
        </View>
        {searchState.primary.map(item => (
          <ProductCard key={item.id} product={item} onAddToCart={() => {}} />
        ))}
      </View>
    );
  };

  const renderLegacyRecommendationsSection = () => {
    if (searchState.recommendations.length === 0) return null;
    const layout = getCategoryLayout();
    return (
      <View>
        <View style={[styles.sectionHeaderRow, { marginTop: tc.space.lg }]}>
          <View style={[styles.sectionAccent, { backgroundColor: tc.color.line }]} />
          <Text style={styles.sectionTitle}>You might also like</Text>
          <Text style={styles.sectionCount}>{searchState.recommendations.length} related</Text>
        </View>
        {searchState.recommendations.map(item => {
          if (layout === 'restaurant') {
            const price = item.prices?.[0];
            return (
              <RestaurantCard
                key={item.id}
                id={item.id}
                name={item.name}
                brand={price?.provider ?? item.brand ?? 'Food'}
                pricePerPerson={price?.price ?? 0}
                deliveryTime={price?.deliveryTime ?? ''}
                imageUrl={item.imageUrl ?? ''}
                deepLink={price?.deepLink ?? ''}
              />
            );
          }
          if (layout === 'travel') {
            const price = item.prices?.[0];
            return (
              <FlightCard
                key={item.id}
                id={item.id}
                airlineName={item.name}
                price={price?.price ?? 0}
                duration={item.weightVolume ?? ''}
                brand={price?.provider ?? item.brand ?? 'Travel'}
                deepLink={price?.deepLink ?? ''}
              />
            );
          }
          return <ProductCard key={item.id} product={item} onAddToCart={() => {}} />;
        })}
      </View>
    );
  };

  const renderEmptyState = () => {
    if (isLoading) {
      return (
        <>
          <SkeletonCard /><SkeletonCard /><SkeletonCard />
        </>
      );
    }
    if (searchTrigger && !isLoading && totalResults === 0) {
      const si = searchState.searchIntelligence;
      const correctedName = si?.show_correction_banner ? si.correction_banner_text.replace('Showing results for ', '') : null;
      return (
        <View style={styles.emptyWrap}>
          <Feather name="search" size={48} color={tc.color.muted} style={{marginBottom: 16}} />
          <Text style={styles.emptyTitle}>
            {correctedName ? `No results for ${correctedName}` : 'No exact match found'}
          </Text>
          <Text style={styles.emptyText}>
            {correctedName
              ? `We searched across ${providersChecked.length} providers for "${correctedName}" but couldn't find a live price. Try again shortly or check if the product is available.`
              : `We searched across ${providersChecked.length} providers for "${searchTrigger}" but couldn't find an exact match. Try a different search term.`
            }
          </Text>
        </View>
      );
    }
    return null;
  };



  // ─── Render ─────────────────────────────────────────────────────────────────

  return (
    <SafeAreaView style={styles.safeArea}>
      <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : 'height'} style={styles.flex}>

        {/* Header — Porcelain with category accent */}
        <View style={styles.header}>
          <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backBtn}>
            <Feather name="arrow-left" size={22} color={tc.color.ink} />
          </TouchableOpacity>
          <View style={{ flex: 1, marginLeft: tc.space.sm }}>
            <Text style={styles.title}>{category}</Text>
            <Text style={styles.subtitle}>
              {totalResults > 0
                ? `${comparisonGroups.length} exact | ${probableGroups.length + relatedGroups.length} review`
                : 'Search for best prices'}
            </Text>
          </View>
          {/* Category accent dot */}
          <View style={[styles.headerAccentDot, { backgroundColor: color }]} />
        </View>
        {/* Category accent line */}
        <View style={[styles.headerAccentLine, { backgroundColor: color }]} />

        {/* Search Inputs */}
        <View style={styles.searchWrap}>
          {category === 'Mobility' ? (
            <MobilityInput
              isLoading={isLoading}
              userLocation={userLocation}
              onSearch={(pickup, dropoff) => {
                const query = `${pickup} to ${dropoff}`;
                setSearchQuery(query);
                handleSearch(query);
              }}
            />
          ) : category === 'Travel' ? (
            <TravelInput
              isLoading={isLoading}
              userLocation={userLocation}
              onSearch={(origin, destination) => {
                const query = `${origin} to ${destination}`;
                setSearchQuery(query);
                handleSearch(query);
              }}
            />
          ) : (
            <UniversalInput
              category={category}
              isLoading={isLoading}
              onSearch={(query) => {
                setSearchQuery(query);
                handleSearch(query);
              }}
            />
          )}
        </View>

        {/* Live Log */}
        {liveLog !== '' && (
          <View style={styles.logWrap}>
            <ActivityIndicator size="small" color={color} style={{ marginRight: tc.space.xs }} />
            <Text style={styles.logText}>{liveLog}</Text>
          </View>
        )}

        {/* Provider Badges */}
        {renderProviderBadges()}

        {/* ── Search Intelligence Correction Banner ──────────────────────── */}
        {searchState.searchIntelligence?.show_correction_banner && (
          <View style={styles.siBannerHigh}>
            <View style={styles.siBannerLeft}>
              <Feather name="zap" size={13} color="#6366f1" style={{ marginTop: 1 }} />
              <View style={{ flex: 1 }}>
                <Text style={styles.siBannerTitle} numberOfLines={1}>
                  {searchState.searchIntelligence.correction_banner_text}
                </Text>
                {searchState.searchIntelligence.correction_alt_text ? (
                  <TouchableOpacity
                    onPress={() => {
                      const rawQ = searchState.searchIntelligence?.raw_query ?? searchTrigger;
                      setSearchQuery(rawQ);
                      handleSearch(rawQ);
                    }}
                    activeOpacity={0.7}
                  >
                    <Text style={styles.siBannerAlt}>
                      {searchState.searchIntelligence.correction_alt_text}
                    </Text>
                  </TouchableOpacity>
                ) : null}
              </View>
            </View>
          </View>
        )}

        {/* ── "Did you mean?" for MEDIUM confidence corrections ──────────── */}
        {searchState.searchIntelligence &&
          !searchState.searchIntelligence.show_correction_banner &&
          searchState.searchIntelligence.correction_confidence === 'MEDIUM' &&
          searchState.searchIntelligence.corrected_query !== searchState.searchIntelligence.raw_query && (
          <View style={styles.siBannerMedium}>
            <Feather name="help-circle" size={13} color="#d97706" style={{ marginTop: 1 }} />
            <View style={{ flex: 1 }}>
              <Text style={styles.siBannerMediumText}>
                {'Did you mean '}
                <Text
                  style={styles.siBannerMediumLink}
                  onPress={() => {
                    const corrected = searchState.searchIntelligence?.corrected_query ?? '';
                    if (corrected) { setSearchQuery(corrected); handleSearch(corrected); }
                  }}
                >
                  {searchState.searchIntelligence.corrected_query}
                </Text>
                {'?'}
              </Text>
            </View>
          </View>
        )}

        {/* Main Content */}
        <ScrollView contentContainerStyle={styles.listContent} showsVerticalScrollIndicator={false}>
          {searchTrigger ? (
            <>
              {renderEmptyState()}
              {renderPrimarySection()}
              {renderRecommendationsSection()}
            </>
          ) : (
            <View style={styles.emptyWrap}>
              {/* TrueCost Lens idle state */}
              <View style={styles.emptyLensWrap}>
                <View style={styles.emptyLensOuter} />
                <View style={styles.emptyLensMid} />
                <View style={[styles.emptyLensCore, { backgroundColor: color }]}>
                  <Feather name="zap" size={16} color="#FFFFFF" />
                </View>
              </View>
              <Text style={styles.emptyTitle}>Make the call.</Text>
              <Text style={styles.emptyText}>{getEmptyPrompt()}</Text>
              {/* Sample queries */}
              <View style={styles.emptyHintsRow}>
                {['cheapest basket', 'ride to airport', 'best ANC headphones'].map(hint => (
                  <View key={hint} style={styles.emptyHintChip}>
                    <Text style={styles.emptyHintText}>{hint}</Text>
                  </View>
                ))}
              </View>
            </View>
          )}
        </ScrollView>

        {/* Hidden Scraper Subsystem */}
        {searchTrigger ? (
          <ScraperManager
            category={category}
            query={searchTrigger}
            userLocation={userLocation}
            onResults={handleResults}
            onError={handleScraperError}
          />
        ) : null}

      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

// ─── Styles ───────────────────────────────────────────────────────────────────

const styles = StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: tc.color.bg },
  flex: { flex: 1 },

  // ── Header — Porcelain ──────────────────────────────────────────────────────
  header: {
    paddingHorizontal: tc.space.base,
    paddingVertical: tc.space.md,
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: tc.color.surface,
    paddingTop: Platform.OS === 'android' ? 40 : tc.space.md,
    borderBottomWidth: 1,
    borderBottomColor: tc.color.line,
  },
  headerAccentDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginRight: tc.space.xs,
  },
  headerAccentLine: {
    height: 2,
    width: 48,
    borderRadius: 1,
    marginHorizontal: tc.space.base,
    marginBottom: tc.space.xs,
    opacity: 0.75,
  },
  backBtn: { padding: tc.space.xs },
  title: { ...tc.type.h3, color: tc.color.ink, fontWeight: '700' },
  subtitle: { ...tc.type.caption, color: tc.color.muted, marginTop: 1 },

  // ── Search wrap ─────────────────────────────────────────────────────────────
  searchWrap: { backgroundColor: 'transparent', marginHorizontal: 0, marginVertical: 0 },
  searchInput: { flex: 1, marginLeft: 10, ...tc.type.body },

  // ── Live log ─────────────────────────────────────────────────────────────────
  logWrap: {
    flexDirection: 'row',
    alignItems: 'center',
    marginHorizontal: tc.space.base,
    marginBottom: tc.space.xs,
    paddingHorizontal: tc.space.md,
    paddingVertical: tc.space.xs,
    backgroundColor: tc.color.surfaceAlt,
    borderRadius: 8,
  },
  logText: { ...tc.type.caption, color: tc.color.muted, fontWeight: '600', flex: 1 },

  // ── Provider badges ──────────────────────────────────────────────────────────
  badgeScroll: { maxHeight: 40 },
  badgeWrap: {
    paddingHorizontal: tc.space.base,
    paddingBottom: tc.space.sm,
    gap: tc.space.xs,
    flexDirection: 'row',
  },
  coverageWrap: {
    paddingHorizontal: tc.space.base,
    paddingBottom: tc.space.sm,
  },
  providerBadge: {
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: tc.radius.pill,
    borderWidth: 1.5,
    backgroundColor: tc.color.surface,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
  },
  providerDot: { width: 6, height: 6, borderRadius: 3 },
  providerBadgeText: { ...tc.type.eyebrow, fontSize: 10 },
  providerPending: { borderColor: tc.color.line, backgroundColor: tc.color.surfaceMuted },
  providerPendingText: { ...tc.type.eyebrow, fontSize: 10, color: tc.color.muted },

  // ── Section headers ──────────────────────────────────────────────────────────
  sectionHeaderRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginHorizontal: tc.space.base,
    marginBottom: tc.space.sm,
    marginTop: tc.space.xs,
  },
  sectionAccent: { width: 3, height: 16, borderRadius: 2 },
  sectionTitle: { ...tc.type.h3, color: tc.color.ink, flex: 1, fontWeight: '700' },
  sectionCount: { ...tc.type.caption, color: tc.color.muted, fontWeight: '600' },
  listContent: { paddingBottom: 120 },

  // ── Empty state ──────────────────────────────────────────────────────────────
  emptyWrap: {
    alignItems: 'center',
    paddingTop: 56,
    paddingHorizontal: 32,
    paddingBottom: 24,
  },
  emptyTitle: {
    ...tc.type.h2,
    color: tc.color.ink,
    marginBottom: tc.space.sm,
    textAlign: 'center',
    letterSpacing: -0.4,
    fontWeight: '800',
  },
  emptyText: {
    ...tc.type.bodySmall,
    color: tc.color.muted,
    textAlign: 'center',
    lineHeight: 21,
  },

  // TrueCostLens idle visualization (static — no animation needed for empty state)
  emptyLensWrap: {
    width: 80,
    height: 80,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: tc.space.xl,
  },
  emptyLensOuter: {
    position: 'absolute',
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: tc.color.iris,
    opacity: 0.08,
  },
  emptyLensMid: {
    position: 'absolute',
    width: 58,
    height: 58,
    borderRadius: 29,
    borderWidth: 1.5,
    borderColor: `${tc.color.iris}35`,
  },
  emptyLensCore: {
    width: 40,
    height: 40,
    borderRadius: 20,
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: tc.color.iris,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.35,
    shadowRadius: 8,
    elevation: 6,
  },

  // Sample query hint chips
  emptyHintsRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: tc.space.sm,
    justifyContent: 'center',
    marginTop: tc.space.xl,
  },
  emptyHintChip: {
    paddingHorizontal: tc.space.md,
    paddingVertical: tc.space.xs + 2,
    borderRadius: tc.radius.pill,
    backgroundColor: tc.color.surfaceAlt,
    borderWidth: 1,
    borderColor: tc.color.line,
  },
  emptyHintText: {
    ...tc.type.caption,
    color: tc.color.muted,
    fontWeight: '500',
  },

  // ── Search Intelligence Banners ──────────────────────────────────────────────
  siBannerHigh: {
    marginHorizontal: tc.space.base,
    marginBottom: tc.space.sm,
    backgroundColor: '#eef2ff',
    borderRadius: 10,
    borderLeftWidth: 3,
    borderLeftColor: '#6366f1',
    paddingHorizontal: 12,
    paddingVertical: 10,
  },
  siBannerLeft: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 8,
  },
  siBannerTitle: {
    ...tc.type.bodySmall,
    color: '#3730a3',
    fontWeight: '600',
    lineHeight: 18,
  },
  siBannerAlt: {
    ...tc.type.bodySmall,
    color: '#6366f1',
    marginTop: 3,
    textDecorationLine: 'underline',
    fontSize: 11,
  },
  siBannerMedium: {
    marginHorizontal: tc.space.base,
    marginBottom: tc.space.sm,
    backgroundColor: '#fffbeb',
    borderRadius: 10,
    borderLeftWidth: 3,
    borderLeftColor: '#d97706',
    paddingHorizontal: 12,
    paddingVertical: 8,
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 8,
  },
  siBannerMediumText: {
    ...tc.type.bodySmall,
    color: '#92400e',
  },
  siBannerMediumLink: {
    ...tc.type.bodySmall,
    color: '#d97706',
    fontWeight: '600',
    textDecorationLine: 'underline',
  },
});
