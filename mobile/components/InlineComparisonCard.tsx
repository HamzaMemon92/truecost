import React, { useMemo } from 'react';
import {
  Image,
  Linking,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { Feather } from '@expo/vector-icons';
import { Badge, FreshnessTag, PrimaryButton, ProviderLogo } from './ui';
import { formatCurrency, tc } from '../design/tokens';
import type { ProductProps } from './ProductCard';

export type MatchConfidence = 'exact' | 'probable' | 'related';

export type ProviderState = {
  state?: 'responded' | 'pending' | 'timeout' | 'blocked' | 'unavailable' | string;
  exact_matches?: number;
  probable?: number;
  related?: number;
  rejected?: number;
  observed?: number;
  available_matches?: number;
  sold_out?: number;
  match_status?: 'exact' | 'close_variant' | 'related' | 'no_match' | 'unknown' | string;
};

export type InlineProviderOffer = {
  id: string;
  provider: string;
  price?: number | null;
  originalPrice?: number | null;
  currency?: string;
  deliveryTime?: string | null;
  deepLink?: string | null;
  freshness?: string | Record<string, any> | null;
  unitPrice?: string | null;
  weightVolume?: string | null;
  meta?: string | null;
  isBest?: boolean;
  productUrl?: string | null;
  appDeepLink?: string | null;
  fallbackSearchUrl?: string | null;
  handoffConfidence?: 'exact_product' | 'search' | 'app_home' | string | null;
  inStock?: boolean | null;
  serviceable?: boolean | null;
  imageUrl?: string | null;
  imageMatchStatus?: 'EXACT_SKU_IMAGE' | 'COMPATIBLE_SKU_IMAGE' | 'UNVERIFIED_IMAGE' | 'INCOMPATIBLE_IMAGE' | 'NO_IMAGE' | string | null;
  imageSourceProvider?: string | null;
  imageSourceProductId?: string | null;
  imageSourceVariantId?: string | null;
  product?: ProductProps | Record<string, any> | null;
};

export type InlineComparisonGroup = {
  id: string;
  title: string;
  subtitle?: string | null;
  category: string;
  imageUrl?: string | null;
  offers: InlineProviderOffer[];
  providerStatus?: Record<string, ProviderState>;
  explanation?: string | null;
  confidence?: MatchConfidence;
  evidenceSummary?: {
    exact_count?: number;
    providers_compared?: number;
    price_range?: { min?: number | null; max?: number | null };
  } | null;
};

type CoverageInput = {
  providerStatus?: Record<string, ProviderState>;
  providersResponded?: string[];
  providersPending?: string[];
  compact?: boolean;
};

const CATEGORY_COPY: Record<string, { best: string; single: string; note: string; action: string }> = {
  Grocery: {
    best: 'Best observed grocery price',
    single: 'Only exact grocery source',
    note: 'Pack size is kept separate before ranking.',
    action: 'Open best offer',
  },
  Shopping: {
    best: 'Best observed shopping price',
    single: 'Only exact shopping source',
    note: 'Variants are not mixed into one winner.',
    action: 'Open best offer',
  },
  Pharmacy: {
    best: 'Best observed pharmacy price',
    single: 'Only exact pharmacy source',
    note: 'Confirm dosage and seller in the provider app.',
    action: 'Open offer',
  },
  Mobility: {
    best: 'Cheapest fare observed',
    single: 'Only fare returned',
    note: 'ETA and final fare can change before booking.',
    action: 'Open ride',
  },
  Food: {
    best: 'Best observed menu price',
    single: 'Only menu source found',
    note: 'Confirm taxes, packing and delivery fee in the provider app.',
    action: 'Open menu',
  },
  Travel: {
    best: 'Lowest observed fare',
    single: 'Only itinerary source',
    note: 'Fare rules and seats can change at checkout.',
    action: 'Open fare',
  },
  Finance: {
    best: 'Lowest effective cost',
    single: 'Only provider returned',
    note: 'Eligibility and final terms depend on provider checks.',
    action: 'Open provider',
  },
  Productivity: {
    best: 'Lowest plan cost',
    single: 'Only plan source',
    note: 'Feature limits may vary by workspace and billing term.',
    action: 'Open plan',
  },
};

const confidenceMeta: Record<MatchConfidence, { label: string; tone: 'iris' | 'mint' | 'amber' | 'muted'; copy: string }> = {
  exact: {
    label: 'Exact match',
    tone: 'mint',
    copy: 'This card only ranks offers the backend classified as exact matches.',
  },
  probable: {
    label: 'Review match',
    tone: 'amber',
    copy: 'This looks close, but it is not counted as the best price until confirmed.',
  },
  related: {
    label: 'Related',
    tone: 'muted',
    copy: 'Similar result. Kept separate so it does not affect the winner.',
  },
};

function finitePrice(value?: number | null) {
  return typeof value === 'number' && Number.isFinite(value) ? value : null;
}

function sortedOffers(offers: InlineProviderOffer[]) {
  return [...offers].sort((a, b) => {
    const aa = a.inStock !== false && a.serviceable !== false;
    const ba = b.inStock !== false && b.serviceable !== false;
    if (aa !== ba) return aa ? -1 : 1;
    const ap = finitePrice(a.price);
    const bp = finitePrice(b.price);
    if (ap === null && bp === null) return a.provider.localeCompare(b.provider);
    if (ap === null) return 1;
    if (bp === null) return -1;
    return ap - bp;
  });
}

function bestOfferFrom(offers: InlineProviderOffer[]) {
  return offers.find(offer => offer.isBest) || sortedOffers(offers)[0];
}

function savingsFrom(offers: InlineProviderOffer[]) {
  const prices = offers.map(offer => finitePrice(offer.price)).filter((price): price is number => price !== null);
  if (prices.length < 2) return 0;
  return Math.max(...prices) - Math.min(...prices);
}

function copyFor(category: string) {
  return CATEGORY_COPY[category] || CATEGORY_COPY.Shopping;
}

function freshnessLabel(value?: InlineProviderOffer['freshness']) {
  if (!value) return null;
  if (typeof value === 'string') return value;
  const observedAt = typeof value.observed_at === 'string' ? value.observed_at : '';
  const source = typeof value.source === 'string' ? value.source : '';
  if (observedAt && source) return `${source} observed`;
  if (source) return `${source} observed`;
  if (observedAt) return 'Recently observed';
  return null;
}

function providerStateLabel(provider: string, state: ProviderState) {
  if (state.state === 'timeout') return `${provider} check failed`;
  if (state.state === 'blocked') return `${provider} check blocked`;
  if (state.state === 'network_failure') return `${provider} check failed`;
  if (state.state === 'parser_failure') return `${provider} check failed`;
  if (state.state === 'provider_unavailable') return `${provider} could not check`;
  if (state.state === 'location_unavailable') return `${provider} location needed`;
  if (state.state === 'rate_limited') return `${provider} rate limited`;
  if (state.state === 'pending') return `${provider} not returned yet`;
  if ((state.exact_matches || 0) > 0) return `${provider} exact`;
  if ((state.sold_out || 0) > 0) return `${provider} sold out`;
  if (state.match_status === 'no_match') return `${provider} not available`;
  if ((state.probable || state.related || 0) > 0) return `${provider} not available`;
  if (state.state === 'responded') return `${provider} checked`;
  return `${provider} unavailable`;
}

function chipTone(state: ProviderState) {
  if (state.state === 'pending') return styles.coverageChipPending;
  if (['timeout', 'blocked', 'network_failure', 'parser_failure', 'provider_unavailable', 'location_unavailable', 'rate_limited'].includes(String(state.state))) return styles.coverageChipPending;
  if ((state.exact_matches || 0) > 0) return styles.coverageChipExact;
  if (state.state === 'responded') return styles.coverageChipChecked;
  return styles.coverageChipMuted;
}

async function openLink(url?: string | null) {
  if (!url) return false;
  try {
    const supported = await Linking.canOpenURL(url);
    if (supported) {
      await Linking.openURL(url);
      return true;
    }
  } catch {
    return false;
  }
  return false;
}

function productNameForOffer(offer?: InlineProviderOffer | null) {
  const product = offer?.product as Record<string, any> | null | undefined;
  return String(product?.name || product?.title || offer?.meta || '').trim();
}

function slugify(value: string) {
  return value.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '') || 'product';
}

function providerSearchUrl(provider: string, query: string) {
  const q = encodeURIComponent(query);
  const key = provider.toLowerCase();
  if (key.includes('blinkit')) return `https://blinkit.com/s/?q=${q}`;
  if (key.includes('zepto')) return `https://www.zepto.com/search?query=${q}`;
  if (key.includes('bigbasket') || key.includes('big basket')) return `https://www.bigbasket.com/ps/?q=${q}`;
  if (key.includes('swiggy') || key.includes('instamart')) return `https://www.swiggy.com/instamart/search?custom_back=true&query=${q}`;
  if (key.includes('flipkart')) return `https://www.flipkart.com/search?q=${q}`;
  if (key.includes('amazon')) return `https://www.amazon.in/s?k=${q}`;
  return null;
}

function webProductUrlFromScheme(provider: string, url: string, query: string) {
  const key = provider.toLowerCase();
  const decoded = decodeURIComponent(url);
  const id = decoded.split('/').filter(Boolean).pop();
  if (!id) return null;
  if (key.includes('blinkit') && /^\d+$/.test(id)) {
    return `https://blinkit.com/prn/${slugify(query)}/prid/${id}`;
  }
  if (key.includes('swiggy') || key.includes('instamart')) {
    return `https://www.swiggy.com/instamart/item/${encodeURIComponent(id)}`;
  }
  if (key.includes('bigbasket') || key.includes('big basket')) {
    return `https://www.bigbasket.com/pd/${encodeURIComponent(id)}/${slugify(query)}/`;
  }
  return null;
}

function handoffCandidates(offer?: InlineProviderOffer | null) {
  if (!offer) return [];
  const query = productNameForOffer(offer);
  const candidates: string[] = [];
  const link = offer.deepLink?.trim();
  if (offer.productUrl?.startsWith('http')) candidates.push(offer.productUrl);
  if (link?.startsWith('http')) candidates.push(link);
  if (offer.appDeepLink && !offer.appDeepLink.startsWith('http')) candidates.push(offer.appDeepLink);
  if (link && !link.startsWith('http')) {
    const webProduct = webProductUrlFromScheme(offer.provider, link, query);
    if (webProduct) candidates.push(webProduct);
  }
  const search = offer.fallbackSearchUrl || (query ? providerSearchUrl(offer.provider, query) : null);
  if (search) candidates.push(search);
  if (link && !link.startsWith('http')) candidates.push(link);
  return candidates.filter((candidate, index, all) => candidate && all.indexOf(candidate) === index);
}

async function openProviderHandoff(offer?: InlineProviderOffer | null) {
  for (const candidate of handoffCandidates(offer)) {
    if (await openLink(candidate)) return true;
  }
  return false;
}

export function ProviderCoverageStrip({
  providerStatus,
  providersResponded = [],
  providersPending = [],
  compact = false,
}: CoverageInput) {
  const entries = useMemo(() => {
    const fromStatus = Object.entries(providerStatus || {});
    if (fromStatus.length > 0) return fromStatus;
    const responded = providersResponded.map(provider => [provider, { state: 'responded', exact_matches: 1 }] as [string, ProviderState]);
    const pending = providersPending.map(provider => [provider, { state: 'pending' }] as [string, ProviderState]);
    return [...responded, ...pending];
  }, [providerStatus, providersPending, providersResponded]);

  if (entries.length === 0) return null;

  return (
    <ScrollView
      horizontal
      showsHorizontalScrollIndicator={false}
      contentContainerStyle={[styles.coverageRow, compact && styles.coverageRowCompact]}
      accessibilityLabel="Provider coverage"
    >
      {entries.slice(0, 10).map(([provider, state]) => (
        <View key={`${provider}-${state.state || 'checked'}`} style={[styles.coverageChip, chipTone(state)]}>
          <Text style={styles.coverageText} numberOfLines={1}>
            {providerStateLabel(provider, state)}
          </Text>
        </View>
      ))}
    </ScrollView>
  );
}

export function MatchConfidenceBanner({
  confidence = 'exact',
  explanation,
}: {
  confidence?: MatchConfidence;
  explanation?: string | null;
}) {
  const meta = confidenceMeta[confidence];
  return (
    <View style={styles.confidenceRow}>
      <Badge label={meta.label} tone={meta.tone} />
      <Text style={styles.confidenceText} numberOfLines={2}>
        {explanation || meta.copy}
      </Text>
    </View>
  );
}

export function ProviderOfferRow({
  offer,
  isWinner,
  category,
  onOpenDetails,
}: {
  offer: InlineProviderOffer;
  isWinner?: boolean;
  category: string;
  onOpenDetails?: (product?: ProductProps | Record<string, any> | null) => void;
}) {
  const availability =
    offer.inStock === false ? 'Sold out' : offer.serviceable === false ? 'Not serviceable' : null;
  const metaBits = [availability, offer.deliveryTime, offer.unitPrice, offer.weightVolume, offer.meta].filter(Boolean);
  const price = finitePrice(offer.price);
  const original = finitePrice(offer.originalPrice);

  const handlePress = async () => {
    const opened = await openProviderHandoff(offer);
    if (!opened && onOpenDetails) onOpenDetails(offer.product);
  };

  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={`${offer.provider} ${price === null ? 'price unavailable' : formatCurrency(price, offer.currency || 'INR')}`}
      onPress={handlePress}
      style={({ pressed }) => [
        styles.offerRow,
        isWinner && styles.offerRowWinner,
        pressed && styles.pressed,
      ]}
    >
      <ProviderLogo provider={offer.provider} size="sm" />
      <View style={styles.offerMain}>
        <View style={styles.offerTitleRow}>
          <Text style={styles.offerProvider} numberOfLines={1}>{offer.provider}</Text>
          {isWinner ? (
            <View style={styles.bestPill}>
              <Feather name="check" size={10} color={tc.color.mintDeep} />
              <Text style={styles.bestPillText}>BEST</Text>
            </View>
          ) : null}
        </View>
        <Text style={styles.offerMeta} numberOfLines={1}>
          {metaBits.length > 0 ? metaBits.join('  |  ') : copyFor(category).note}
        </Text>
      </View>
      <View style={styles.priceBlock}>
        {original !== null && price !== null && original > price ? (
          <Text style={styles.originalPrice}>{formatCurrency(original, offer.currency || 'INR')}</Text>
        ) : null}
        <Text style={[styles.offerPrice, isWinner && styles.offerPriceWinner]} numberOfLines={1}>
          {formatCurrency(price, offer.currency || 'INR')}
        </Text>
      </View>
      <Feather name="external-link" size={16} color={tc.color.muted} />
    </Pressable>
  );
}

export function SingleProviderResultCard(props: InlineCardProps) {
  const { group, onOpenDetails, onDeepCompare, compact } = props;
  const offers = sortedOffers(group.offers);
  const onlyOffer = offers[0];
  const confidence = group.confidence || 'exact';
  const copy = copyFor(group.category);

  return (
    <View style={[styles.card, compact && styles.cardCompact]}>
      <MatchConfidenceBanner confidence={confidence} explanation={group.explanation} />
      <View style={styles.heroRow}>
        <View style={styles.titleColumn}>
          <Text style={styles.title} numberOfLines={compact ? 2 : 3}>{group.title}</Text>
          {group.subtitle ? <Text style={styles.subtitle} numberOfLines={1}>{group.subtitle}</Text> : null}
          <Text style={styles.singleSummary} numberOfLines={2}>
            {onlyOffer?.provider ? `Found on ${onlyOffer.provider} only` : copy.single}
          </Text>
        </View>
        {group.imageUrl ? (
          <Image source={{ uri: group.imageUrl }} style={styles.productImage} resizeMode="contain" />
        ) : (
          <View style={styles.imageFallback}>
            <Feather name="box" size={24} color={tc.color.iris} />
          </View>
        )}
      </View>
      {onlyOffer ? (
        <ProviderOfferRow offer={onlyOffer} isWinner category={group.category} onOpenDetails={onOpenDetails} />
      ) : null}
      <ProviderCoverageStrip providerStatus={group.providerStatus} compact />
      <View style={styles.actionRow}>
        <PrimaryButton
          label={copy.action}
          icon="external-link"
          size="sm"
          variant="iris"
          style={styles.actionButton}
          onPress={() => openProviderHandoff(onlyOffer)}
        />
        <Pressable
          accessibilityRole="button"
          onPress={() => onDeepCompare?.(group)}
          style={styles.secondaryAction}
        >
          <Feather name="layers" size={16} color={tc.color.iris} />
          <Text style={styles.secondaryActionText}>Deep check</Text>
        </Pressable>
      </View>
    </View>
  );
}

type InlineCardProps = {
  group: InlineComparisonGroup;
  compact?: boolean;
  onOpenDetails?: (product?: ProductProps | Record<string, any> | null) => void;
  onDeepCompare?: (group: InlineComparisonGroup) => void;
};

export default function InlineComparisonCard(props: InlineCardProps) {
  const { group, compact, onOpenDetails, onDeepCompare } = props;
  const offers = sortedOffers(group.offers);
  const best = bestOfferFrom(offers);
  const savings = savingsFrom(offers);
  const confidence = group.confidence || 'exact';
  const copy = copyFor(group.category);
  const bestFreshnessLabel = freshnessLabel(best?.freshness);

  if (offers.length <= 1) {
    return <SingleProviderResultCard {...props} />;
  }

  return (
    <View style={[styles.card, compact && styles.cardCompact]}>
      <MatchConfidenceBanner confidence={confidence} explanation={group.explanation} />
      <View style={styles.heroRow}>
        <View style={styles.titleColumn}>
          <Text style={styles.title} numberOfLines={compact ? 2 : 3}>{group.title}</Text>
          {group.subtitle ? <Text style={styles.subtitle} numberOfLines={1}>{group.subtitle}</Text> : null}
          <View style={styles.summaryPanel}>
            <Text style={styles.summaryLabel}>{copy.best}</Text>
            <Text style={styles.summaryPrice} numberOfLines={1}>
              {formatCurrency(best?.price, best?.currency || 'INR')}
            </Text>
            <Text style={styles.summaryMeta} numberOfLines={1}>
              {best?.provider ? `via ${best.provider}` : `${offers.length} exact offers`}
              {savings > 0 ? ` | save up to ${formatCurrency(savings)}` : ''}
            </Text>
          </View>
        </View>
        {group.imageUrl ? (
          <Image source={{ uri: group.imageUrl }} style={styles.productImage} resizeMode="contain" />
        ) : (
          <View style={styles.imageFallback}>
            <Feather name="box" size={24} color={tc.color.iris} />
          </View>
        )}
      </View>

      <View style={styles.offerStack}>
        {offers.slice(0, compact ? 2 : 5).map((offer, index) => (
          <ProviderOfferRow
            key={`${offer.id}-${offer.provider}-${index}`}
            offer={offer}
            isWinner={offer.id === best?.id}
            category={group.category}
            onOpenDetails={onOpenDetails}
          />
        ))}
      </View>

      <ProviderCoverageStrip providerStatus={group.providerStatus} compact />
      <View style={styles.actionRow}>
        <PrimaryButton
          label={copy.action}
          icon="external-link"
          size="sm"
          variant="iris"
          style={styles.actionButton}
          onPress={() => openProviderHandoff(best)}
        />
        <Pressable
          accessibilityRole="button"
          onPress={() => onDeepCompare?.(group)}
          style={styles.secondaryAction}
        >
          <Feather name="layers" size={16} color={tc.color.iris} />
          <Text style={styles.secondaryActionText}>Deep check</Text>
        </Pressable>
      </View>
      {bestFreshnessLabel ? <FreshnessTag label={bestFreshnessLabel} /> : null}
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: tc.color.surfaceCard,
    borderColor: tc.color.line,
    borderWidth: 1,
    borderRadius: 8,
    marginBottom: tc.space.base,
    padding: tc.space.base,
    ...tc.shadow.sm,
  },
  cardCompact: {
    padding: tc.space.md,
  },
  pressed: {
    opacity: 0.72,
  },
  confidenceRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: tc.space.sm,
    marginBottom: tc.space.md,
  },
  confidenceText: {
    flex: 1,
    ...tc.type.caption,
    color: tc.color.muted,
    letterSpacing: 0,
  },
  heroRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: tc.space.md,
  },
  titleColumn: {
    flex: 1,
    minWidth: 0,
  },
  title: {
    ...tc.type.h2,
    color: tc.color.ink,
    letterSpacing: 0,
  },
  subtitle: {
    ...tc.type.bodySmall,
    color: tc.color.muted,
    marginTop: 2,
  },
  productImage: {
    width: 84,
    height: 84,
    borderRadius: 8,
    backgroundColor: tc.color.surfaceAlt,
  },
  imageFallback: {
    width: 84,
    height: 84,
    borderRadius: 8,
    backgroundColor: tc.color.irisSoft,
    alignItems: 'center',
    justifyContent: 'center',
  },
  summaryPanel: {
    marginTop: tc.space.md,
    padding: tc.space.md,
    borderRadius: 8,
    backgroundColor: tc.color.mintSoft,
    borderWidth: 1,
    borderColor: '#C6F1E7',
  },
  summaryLabel: {
    ...tc.type.caption,
    color: tc.color.mintDeep,
    letterSpacing: 0,
    textTransform: 'uppercase',
  },
  summaryPrice: {
    ...tc.type.priceHero,
    color: tc.color.ink,
    letterSpacing: 0,
    marginTop: 2,
  },
  summaryMeta: {
    ...tc.type.bodySmall,
    color: tc.color.inkSoft,
    marginTop: 2,
  },
  singleSummary: {
    ...tc.type.body,
    color: tc.color.inkSoft,
    marginTop: tc.space.md,
  },
  offerStack: {
    marginTop: tc.space.md,
    gap: tc.space.sm,
  },
  offerRow: {
    minHeight: 56,
    flexDirection: 'row',
    alignItems: 'center',
    gap: tc.space.sm,
    borderWidth: 1,
    borderColor: tc.color.line,
    borderRadius: 8,
    backgroundColor: tc.color.surface,
    paddingHorizontal: tc.space.sm,
    paddingVertical: tc.space.sm,
  },
  offerRowWinner: {
    borderColor: '#B7ECDD',
    backgroundColor: '#F2FCF9',
  },
  offerMain: {
    flex: 1,
    minWidth: 0,
  },
  offerTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: tc.space.xs,
  },
  offerProvider: {
    ...tc.type.label,
    color: tc.color.ink,
    flexShrink: 1,
  },
  offerMeta: {
    ...tc.type.caption,
    color: tc.color.muted,
    marginTop: 1,
  },
  bestPill: {
    height: 20,
    borderRadius: 8,
    paddingHorizontal: 6,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 3,
    backgroundColor: tc.color.mintSoft,
  },
  bestPillText: {
    ...tc.type.micro,
    color: tc.color.mintDeep,
    letterSpacing: 0,
  },
  priceBlock: {
    alignItems: 'flex-end',
    minWidth: 76,
  },
  originalPrice: {
    ...tc.type.caption,
    color: tc.color.muted,
    textDecorationLine: 'line-through',
  },
  offerPrice: {
    ...tc.type.priceSub,
    color: tc.color.ink,
    letterSpacing: 0,
    fontVariant: ['tabular-nums'],
  },
  offerPriceWinner: {
    color: tc.color.mintDeep,
  },
  coverageRow: {
    gap: tc.space.xs,
    paddingTop: tc.space.md,
    paddingRight: tc.space.base,
  },
  coverageRowCompact: {
    paddingTop: tc.space.sm,
  },
  coverageChip: {
    minHeight: 30,
    maxWidth: 190,
    borderRadius: 8,
    paddingHorizontal: tc.space.sm,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
  },
  coverageChipExact: {
    backgroundColor: tc.color.mintSoft,
    borderColor: '#C6F1E7',
  },
  coverageChipChecked: {
    backgroundColor: tc.color.surfaceAlt,
    borderColor: tc.color.line,
  },
  coverageChipPending: {
    backgroundColor: tc.color.amberSoft,
    borderColor: '#F6D79B',
  },
  coverageChipMuted: {
    backgroundColor: tc.color.surfaceAlt,
    borderColor: tc.color.line,
  },
  coverageText: {
    ...tc.type.caption,
    color: tc.color.inkSoft,
  },
  actionRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: tc.space.sm,
    marginTop: tc.space.md,
  },
  actionButton: {
    flex: 1,
    borderRadius: 8,
  },
  secondaryAction: {
    minHeight: 40,
    borderRadius: 8,
    paddingHorizontal: tc.space.md,
    flexDirection: 'row',
    alignItems: 'center',
    gap: tc.space.xs,
    backgroundColor: tc.color.irisSoft,
  },
  secondaryActionText: {
    ...tc.type.label,
    color: tc.color.iris,
  },
});
