import React, { useMemo, useState } from 'react';
import { Image, Pressable, StyleSheet, Text, View } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { useNavigation } from '@react-navigation/native';
import { api } from '../api/client';
import { useAuth } from '../auth/AuthContext';
import { Card, PrimaryButton, ProviderLogo } from './ui';
import { TC, formatCurrency } from '../design/tokens';
import { useQueryClient } from '../query/QueryClient';

export interface ProviderPrice {
  provider: string;
  price: number;
  originalPrice?: number;
  original_price?: number;
  deliveryTime?: string;
  delivery_time?: string;
  isBest?: boolean;
  is_best?: boolean;
  deepLink?: string;
  deep_link?: string;
  productUrl?: string;
  product_url?: string;
  appDeepLink?: string;
  app_deep_link?: string;
  fallbackSearchUrl?: string;
  fallback_search_url?: string;
  handoffConfidence?: string;
  handoff_confidence?: string;
  inStock?: boolean | null;
  in_stock?: boolean | null;
  serviceable?: boolean | null;
}

export interface ProductProps {
  id: string;
  name: string;
  brand?: string;
  weightVolume?: string;
  imageUrl?: string;
  category: string;
  prices: ProviderPrice[];
  weight?: string;
  image_url?: string;
  weight_volume?: string;
  matchScore?: number;
  matchTier?: 'primary' | 'related' | 'discard';
  queryRelevance?: 'EXACT_INTENT' | 'SUBSTITUTE' | 'COMPLEMENT' | 'IRRELEVANT';
}

type Cart = { id: string };

function normalizedOffer(offer: ProviderPrice) {
  return {
    provider: offer.provider,
    price: offer.price,
    originalPrice: offer.originalPrice ?? offer.original_price,
    deliveryTime: offer.deliveryTime ?? offer.delivery_time ?? '',
    isBest: offer.isBest ?? offer.is_best ?? false,
    deepLink: offer.deepLink ?? offer.deep_link,
    productUrl: offer.productUrl ?? offer.product_url,
    appDeepLink: offer.appDeepLink ?? offer.app_deep_link,
    fallbackSearchUrl: offer.fallbackSearchUrl ?? offer.fallback_search_url,
    handoffConfidence: offer.handoffConfidence ?? offer.handoff_confidence,
  };
}

export default function ProductCard({
  product,
  onAddToCart,
}: {
  product: ProductProps;
  onAddToCart?: (product: ProductProps) => void;
}) {
  const navigation = useNavigation<any>();
  const { session, updateSession } = useAuth();
  const cache = useQueryClient();
  const [saving, setSaving] = useState(false);
  const [notice, setNotice] = useState('');

  const offers = useMemo(
    () => (product.prices || []).map(normalizedOffer).sort((a, b) => a.price - b.price),
    [product.prices]
  );
  const best = offers.find(offer => offer.isBest) || offers[0];
  const image = product.imageUrl || product.image_url || '';
  const weight = product.weightVolume || product.weight_volume || product.weight || '';
  const maxSaving =
    offers.length > 1
      ? Math.max(...offers.map(item => item.price)) - Math.min(...offers.map(item => item.price))
      : 0;

  const isExact = product.matchTier === 'primary' || product.queryRelevance === 'EXACT_INTENT';
  const detailProduct = { ...product, imageUrl: image, weightVolume: weight, offers, prices: offers };

  const openDetails = () =>
    navigation.navigate('ProductDetail', { product: detailProduct, provenance: 'observed_provider_result' });

  const focusedCompare = () =>
    navigation.navigate('FocusedCompare', {
      category: product.category || 'Shopping',
      color: product.category === 'Grocery' ? TC.color.grocery : TC.color.iris,
      query: product.name,
      initialQuery: product.name,
      product: detailProduct,
      focusProductId: product.id,
      provenance: 'user_selected_exact_product',
    });

  const providerCount = offers.length;
  const actionLabel = providerCount > 1 ? `Compare ${providerCount} offers` : 'View offer details';

  const addToCart = async () => {
    if (!session) {
      navigation.navigate('MainTabs', { screen: 'Profile' });
      return;
    }
    setSaving(true);
    setNotice('');
    try {
      const carts = await api<Cart[]>(session, updateSession, '/commerce/carts');
      const cart =
        carts[0] ||
        (await api<Cart>(session, updateSession, '/commerce/carts', {
          method: 'POST',
          body: JSON.stringify({ name: 'My smart basket', currency: 'INR' }),
        }));
      await api(session, updateSession, `/commerce/carts/${cart.id}/items`, {
        method: 'POST',
        body: JSON.stringify({
          title: product.name,
          quantity: 1,
          unit_price: best?.price ?? null,
          provider: best?.provider ?? null,
          source_url: best?.deepLink ?? null,
          metadata: {
            product_id: product.id,
            category: product.category,
            brand: product.brand || '',
            weight_volume: weight,
            image_url: image,
            offers,
            provenance: 'observed_provider_result',
          },
        }),
      });
      onAddToCart?.(product);
      cache.invalidate('carts');
      cache.invalidate('dashboard');
      setNotice('Added to your Smart Cart');
    } catch (error) {
      setNotice(error instanceof Error ? error.message : 'Could not add this item.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <Card style={[styles.card, isExact && styles.cardExact]}>
      {/* ── Top Badge Row ──────────────────────────────────────────────── */}
      <View style={styles.cardTop}>
        <View style={[styles.tierBadge, !isExact && styles.relatedBadge]}>
          <Feather
            name={isExact ? 'award' : 'layers'}
            size={11}
            color={isExact ? TC.color.mintDeep : TC.color.amberDeep}
          />
          <Text style={[styles.tierText, !isExact && styles.relatedText]}>
            {isExact ? 'BEST MATCH' : 'RELATED OPTION'}
          </Text>
        </View>

        <View style={styles.providerCountBadge}>
          <Text style={styles.providerCountText}>
            {providerCount > 1 ? `${providerCount} stores compared` : '1 store observed'}
          </Text>
        </View>
      </View>

      {/* ── Product Info & Image Row ────────────────────────────────────── */}
      <Pressable
        accessibilityRole="button"
        accessibilityLabel={`Open details for ${product.name}`}
        onPress={openDetails}
        style={({ pressed }) => [styles.header, pressed && styles.pressed]}
      >
        {image ? (
          <Image source={{ uri: image }} resizeMode="contain" style={styles.image} />
        ) : (
          <View style={styles.placeholder}>
            <Feather name="package" size={24} color={TC.color.iris} />
          </View>
        )}

        <View style={styles.copy}>
          {product.brand ? <Text style={styles.brand}>{product.brand.toUpperCase()}</Text> : null}
          <Text numberOfLines={2} style={styles.name}>{product.name}</Text>
          {weight ? <Text style={styles.weight}>{weight}</Text> : null}

          {/* Price Row */}
          <View style={styles.priceRow}>
            <Text style={styles.priceHero}>{formatCurrency(best?.price || 0)}</Text>
            {best?.originalPrice && best.originalPrice > best.price ? (
              <Text style={styles.originalPrice}>{formatCurrency(best.originalPrice)}</Text>
            ) : null}
          </View>

          {/* Best Provider Tag */}
          {best?.provider ? (
            <View style={styles.providerLine}>
              <ProviderLogo provider={best.provider} size="sm" />
              <Text style={styles.providerName}>{best.provider}</Text>
              {best.deliveryTime ? (
                <>
                  <Text style={styles.providerDot}>·</Text>
                  <Text style={styles.deliveryTime}>{best.deliveryTime}</Text>
                </>
              ) : null}
            </View>
          ) : null}
        </View>
      </Pressable>

      {/* ── Savings Callout ─────────────────────────────────────────────── */}
      {maxSaving >= 1 ? (
        <View style={styles.savingRow}>
          <Feather name="trending-down" size={13} color={TC.color.mintDeep} />
          <Text style={styles.savingText}>Save up to {formatCurrency(maxSaving)} across stores</Text>
        </View>
      ) : null}

      {notice ? <Text accessibilityLiveRegion="polite" style={styles.notice}>{notice}</Text> : null}

      {/* ── Action Buttons ──────────────────────────────────────────────── */}
      <View style={styles.actions}>
        <PrimaryButton
          label={actionLabel}
          icon={providerCount > 1 ? 'columns' : 'arrow-right'}
          onPress={focusedCompare}
          variant={isExact ? 'iris' : 'outline'}
          size="sm"
          style={styles.action}
        />
        <Pressable
          accessibilityRole="button"
          accessibilityLabel={`Open product details for ${product.name}`}
          onPress={openDetails}
          style={({ pressed }) => [styles.detailButton, pressed && styles.pressed]}
        >
          <Feather name="info" size={16} color={TC.color.inkSoft} />
        </Pressable>
      </View>
    </Card>
  );
}

const styles = StyleSheet.create({
  card: {
    padding: TC.space.base,
    overflow: 'hidden',
    marginBottom: TC.space.sm,
    backgroundColor: TC.color.surfaceCard,
    borderRadius: TC.radius.card,
    borderWidth: 1,
    borderColor: TC.color.line,
  },
  cardExact: {
    borderColor: `${TC.color.mint}60`,
    shadowColor: TC.color.mint,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.08,
    shadowRadius: 8,
    elevation: 2,
  },
  cardTop: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: TC.space.sm,
  },
  tierBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: TC.color.mintSoft,
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: TC.radius.pill,
  },
  relatedBadge: {
    backgroundColor: TC.color.amberSoft,
  },
  tierText: {
    ...TC.type.micro,
    color: TC.color.mintDeep,
    fontWeight: '700',
    letterSpacing: 0.6,
  },
  relatedText: {
    color: TC.color.amberDeep,
  },
  providerCountBadge: {
    paddingHorizontal: 6,
    paddingVertical: 2,
  },
  providerCountText: {
    ...TC.type.caption,
    color: TC.color.muted,
    fontWeight: '600',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: TC.space.md,
  },
  image: {
    width: 84,
    height: 84,
    borderRadius: TC.radius.md,
    backgroundColor: TC.color.surfaceAlt,
  },
  placeholder: {
    width: 84,
    height: 84,
    borderRadius: TC.radius.md,
    backgroundColor: TC.color.irisSoft,
    alignItems: 'center',
    justifyContent: 'center',
  },
  copy: {
    flex: 1,
    gap: 2,
  },
  brand: {
    ...TC.type.micro,
    color: TC.color.muted,
    letterSpacing: 0.8,
    fontWeight: '700',
  },
  name: {
    ...TC.type.label,
    color: TC.color.ink,
    lineHeight: 18,
    fontWeight: '700',
  },
  weight: {
    ...TC.type.caption,
    color: TC.color.muted,
  },
  priceRow: {
    flexDirection: 'row',
    alignItems: 'baseline',
    gap: 6,
    marginTop: 4,
  },
  priceHero: {
    ...TC.type.priceMain,
    color: TC.color.ink,
    fontWeight: '800',
  },
  originalPrice: {
    ...TC.type.caption,
    color: TC.color.muted,
    textDecorationLine: 'line-through',
  },
  providerLine: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginTop: 4,
  },
  providerName: {
    ...TC.type.caption,
    color: TC.color.inkSoft,
    fontWeight: '600',
  },
  providerDot: {
    color: TC.color.subtle,
  },
  deliveryTime: {
    ...TC.type.micro,
    color: TC.color.mintDeep,
    fontWeight: '600',
  },
  savingRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: TC.color.mintSoft,
    borderRadius: TC.radius.sm,
    paddingHorizontal: 10,
    paddingVertical: 6,
    marginTop: TC.space.sm,
  },
  savingText: {
    ...TC.type.caption,
    color: TC.color.mintDeep,
    fontWeight: '700',
  },
  notice: {
    ...TC.type.caption,
    color: TC.color.iris,
    marginTop: TC.space.xs,
  },
  actions: {
    flexDirection: 'row',
    gap: TC.space.xs,
    marginTop: TC.space.md,
    alignItems: 'center',
  },
  action: {
    flex: 1,
  },
  detailButton: {
    width: 40,
    height: 40,
    borderRadius: TC.radius.md,
    borderWidth: 1,
    borderColor: TC.color.line,
    backgroundColor: TC.color.surfaceAlt,
    alignItems: 'center',
    justifyContent: 'center',
  },
  pressed: {
    opacity: 0.76,
  },
});
