import React, { useState } from 'react';
import {
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { Feather } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { useAuth } from '../auth/AuthContext';
import {
  AppHeader,
  Body,
  Card,
  CategoryHeroBanner,
  DecisionHalo,
  GlassCard,
  PrimaryButton,
  ProviderLogo,
  Screen,
  SectionHeader,
  Title,
  WinnerCard,
} from '../components/ui';
import { SystemState } from '../components/SystemState';
import { ProviderHealthPanel } from '../components/ProviderHealthPanel';
import { TC, formatCurrency, getCategoryTheme } from '../design/tokens';
import { useUserLocation } from '../location/LocationContext';
import { useApiQuery } from '../query/useApiQuery';

type Cart = {
  id: string;
  name: string;
  item_count: number;
  estimated_total: number;
  items: unknown[];
};

// ─── Grocery Stores Config ───────────────────────────────────────────────────
const GROCERY_PROVIDERS = [
  { id: 'blinkit', name: 'Blinkit', eta: '9 mins', color: '#F8C800', tag: 'Fastest near you' },
  { id: 'zepto', name: 'Zepto', eta: '10 mins', color: '#8B2FC9', tag: 'Top offers' },
  { id: 'swiggy', name: 'Instamart', eta: '12 mins', color: '#FC8019', tag: 'Max availability' },
  { id: 'bigbasket', name: 'BigBasket', eta: '15 mins', color: '#8CC63F', tag: 'Best bulk prices' },
];

// ─── Quick Aisles ─────────────────────────────────────────────────────────────
const GROCERY_AISLES = [
  { id: 'dairy', label: 'Dairy & Bread', query: 'milk bread butter eggs', icon: 'coffee' as const, color: '#3B82F6', items: 'Milk, Curd, Paneer' },
  { id: 'produce', label: 'Fresh Produce', query: 'fresh vegetables fruits', icon: 'sun' as const, color: '#10B981', items: 'Onions, Tomatoes, Bananas' },
  { id: 'snacks', label: 'Munchies & Drinks', query: 'chips cold drink snacks', icon: 'zap' as const, color: '#F59E0B', items: 'Chips, Soda, Biscuits' },
  { id: 'staples', label: 'Atta, Rice & Dal', query: 'atta rice dal oil', icon: 'shopping-bag' as const, color: '#EC4899', items: 'Basmati, Toor Dal, Oil' },
  { id: 'instant', label: 'Instant & Frozen', query: 'instant noodles frozen food', icon: 'clock' as const, color: '#8B5CF6', items: 'Maggi, Nuggets, Oats' },
  { id: 'household', label: 'Home & Hygiene', query: 'detergent dishwash soap', icon: 'home' as const, color: '#06B6D4', items: 'Surf, Vim, Dettol' },
];

// ─── Curated Baskets ──────────────────────────────────────────────────────────
const CURATED_BASKETS = [
  {
    title: 'Morning Breakfast Pack',
    items: 'Taaza Milk (1L) + Brown Bread + 6 Eggs + Amul Butter',
    itemCount: 4,
    winnerStore: 'blinkit',
    bestPrice: 184,
    altPrice: 212,
    savings: 28,
    eta: '9 mins',
  },
  {
    title: 'Daily Veggie Essentials',
    items: 'Onion (1kg) + Potato (1kg) + Tomato (1kg) + Coriander',
    itemCount: 4,
    winnerStore: 'zepto',
    bestPrice: 139,
    altPrice: 168,
    savings: 29,
    eta: '10 mins',
  },
  {
    title: 'Chai & Snacks Refill',
    items: 'Red Label Tea (500g) + Sugar (1kg) + Good Day (Pack of 3)',
    itemCount: 3,
    winnerStore: 'bigbasket',
    bestPrice: 289,
    altPrice: 325,
    savings: 36,
    eta: '15 mins',
  },
];

export default function GroceryHubScreen({ navigation }: any) {
  const { session } = useAuth();
  const { location } = useUserLocation();
  const [selectedObjective, setSelectedObjective] = useState<'cheapest' | 'fastest' | 'balanced'>('cheapest');

  const { data: carts, loading, error, refetch } = useApiQuery<Cart[]>(
    'carts', '/commerce/carts', { enabled: !!session }
  );
  const current = carts?.[0];

  const search = (query = '') => {
    if (query) {
      navigation.navigate('AgentSearch', {
        category: 'Grocery',
        color: TC.color.grocery,
        initialQuery: query,
        userLocation: location,
      });
    } else {
      navigation.navigate('MainTabs', { screen: 'Compare', params: { category: 'Grocery' } });
    }
  };

  return (
    <Screen scroll={true}>
      {/* ── App Header ───────────────────────────────────────────────────── */}
      <AppHeader
        title="Grocery TrueCost"
        subtitle={location?.display || location?.city || 'Detecting nearby dark stores…'}
        onBack={() => navigation.goBack()}
        onNotifications={() => navigation.navigate('Notifications')}
        onProfile={() => navigation.navigate('Profile')}
      />

      {/* ── Category Hero Banner ─────────────────────────────────────────── */}
      <CategoryHeroBanner
        category="Grocery"
        title="Build the basket. Compare the total."
        subtitle="Item prices, delivery fees, and platform surcharges compared in real time across all 4 quick-commerce apps."
        icon="shopping-bag"
        gradientColors={['#E8F8F1', '#FAFAF8']}
        onSearchPress={() => search()}
        searchPlaceholder="Search milk, veggies, atta, snacks…"
      />

      {/* ── Live Quick-Commerce Stores Strip ──────────────────────────────── */}
      <View style={styles.storesStrip}>
        <View style={styles.storesHeader}>
          <View style={styles.liveDot} />
          <Text style={styles.storesTitle}>LIVE DARK STORES NEAR YOU</Text>
        </View>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.storesRow}>
          {GROCERY_PROVIDERS.map(p => (
            <Pressable
              key={p.id}
              onPress={() => search(p.name)}
              style={({ pressed }) => [styles.storeCard, pressed && styles.pressed]}
            >
              <ProviderLogo provider={p.id} size="sm" />
              <View style={styles.storeInfo}>
                <Text style={styles.storeName}>{p.name}</Text>
                <View style={styles.storeEtaRow}>
                  <Feather name="zap" size={10} color={TC.color.mint} />
                  <Text style={styles.storeEta}>{p.eta}</Text>
                </View>
              </View>
            </Pressable>
          ))}
        </ScrollView>
      </View>

      {/* ── Active Smart Cart / Basket Section ───────────────────────────── */}
      {session && loading && <SystemState kind="loading" compact />}
      {session && error && (
        <SystemState kind="offline" actionLabel="Retry" onAction={() => void refetch()} compact />
      )}

      {current ? (
        <DecisionHalo tone="mint" active={true}>
          <Card tone="mint" style={styles.currentBasketCard}>
            <View style={styles.basketTop}>
              <View style={{ flex: 1 }}>
                <View style={styles.basketBadge}>
                  <Feather name="check-circle" size={12} color={TC.color.mint} />
                  <Text style={styles.basketBadgeText}>ACTIVE BASKET</Text>
                </View>
                <Title size="h2" style={styles.basketTitle}>{current.name}</Title>
              </View>
              <View style={styles.basketCountPill}>
                <Text style={styles.basketCountValue}>{current.item_count}</Text>
                <Text style={styles.basketCountLabel}>items</Text>
              </View>
            </View>

            <View style={styles.divider} />

            <View style={styles.basketTotalRow}>
              <View>
                <Text style={styles.basketTotalLabel}>Estimated Total</Text>
                <Text style={styles.basketTotalHint}>Includes delivery + bag fees</Text>
              </View>
              <Text style={styles.basketTotalValue}>{formatCurrency(current.estimated_total)}</Text>
            </View>

            <PrimaryButton
              label="Open Smart Cart & Compare"
              icon="shopping-bag"
              variant="mint"
              onPress={() => navigation.navigate('Cart')}
              style={{ marginTop: TC.space.md }}
            />
          </Card>
        </DecisionHalo>
      ) : (
        <GlassCard style={styles.basketStarterCard} onPress={() => navigation.navigate('Cart')}>
          <View style={styles.basketStarterIcon}>
            <Feather name="shopping-cart" size={22} color={TC.color.grocery} />
          </View>
          <View style={styles.flex}>
            <Text style={styles.basketStarterTitle}>Smart Basket Optimizer</Text>
            <Text style={styles.basketStarterBody}>
              Add multiple items. TrueCost finds which store delivers your entire list for the lowest total cost.
            </Text>
          </View>
          <Feather name="arrow-right" size={18} color={TC.color.grocery} />
        </GlassCard>
      )}

      {/* ── Quick Aisles Grid ────────────────────────────────────────────── */}
      <SectionHeader
        title="Shop by aisle"
        action="Explore all"
        onAction={() => search('groceries')}
      />
      <View style={styles.aislesGrid}>
        {GROCERY_AISLES.map(aisle => (
          <Pressable
            key={aisle.id}
            accessibilityRole="button"
            accessibilityLabel={`Shop ${aisle.label}`}
            onPress={() => search(aisle.query)}
            style={({ pressed }) => [styles.aisleTile, pressed && styles.pressed]}
          >
            <View style={[styles.aisleIconWrap, { backgroundColor: `${aisle.color}15` }]}>
              <Feather name={aisle.icon} size={20} color={aisle.color} />
            </View>
            <Text style={styles.aisleTitle} numberOfLines={1}>{aisle.label}</Text>
            <Text style={styles.aisleItems} numberOfLines={1}>{aisle.items}</Text>
          </Pressable>
        ))}
      </View>

      {/* ── Curated Daily Baskets ────────────────────────────────────────── */}
      <SectionHeader
        title="Popular price-compared baskets"
        action="See more"
        onAction={() => search('essentials')}
      />
      <View style={styles.curatedList}>
        {CURATED_BASKETS.map((basket, idx) => (
          <Card key={idx} style={styles.curatedCard}>
            <View style={styles.curatedTop}>
              <View style={styles.flex}>
                <Text style={styles.curatedTitle}>{basket.title}</Text>
                <Text style={styles.curatedItems}>{basket.items}</Text>
              </View>
              <View style={styles.savingsPill}>
                <Feather name="trending-down" size={11} color={TC.color.mintDeep} />
                <Text style={styles.savingsPillText}>Save {formatCurrency(basket.savings)}</Text>
              </View>
            </View>

            <View style={styles.curatedDivider} />

            <View style={styles.curatedBottom}>
              <View style={styles.curatedWinner}>
                <ProviderLogo provider={basket.winnerStore} size="sm" />
                <View style={{ marginLeft: TC.space.xs }}>
                  <Text style={styles.curatedWinnerName}>Cheapest on {basket.winnerStore.toUpperCase()}</Text>
                  <Text style={styles.curatedEta}>⚡ {basket.eta} delivery</Text>
                </View>
              </View>

              <View style={styles.curatedPriceGroup}>
                <Text style={styles.curatedAltPrice}>{formatCurrency(basket.altPrice)}</Text>
                <Text style={styles.curatedBestPrice}>{formatCurrency(basket.bestPrice)}</Text>
              </View>
            </View>

            <PrimaryButton
              label="Compare this basket"
              size="sm"
              variant="outline"
              onPress={() => search(basket.items)}
              style={{ marginTop: TC.space.sm }}
            />
          </Card>
        ))}
      </View>

      {/* ── Quick Intent Shortcuts ───────────────────────────────────────── */}
      <SectionHeader title="Frequently compared items" />
      <View style={styles.intentsRow}>
        {[
          'Amul Taaza Milk 500ml',
          'Aashirvaad Shudh Chakki Atta 5kg',
          'Tata Salt 1kg',
          'Maggi 2-Minute Noodles 420g',
          'Fortune Sunlite Sunflower Oil 1L',
          'Fresh Farm Eggs 6 Pack',
        ].map(item => (
          <Pressable
            key={item}
            onPress={() => search(item)}
            style={({ pressed }) => [styles.intentChip, pressed && styles.pressed]}
          >
            <Feather name="search" size={12} color={TC.color.grocery} />
            <Text style={styles.intentChipText}>{item}</Text>
          </Pressable>
        ))}
      </View>

      {/* ── Provider Readiness Health Panel ──────────────────────────────── */}
      <View style={{ marginTop: TC.space.xl, marginBottom: TC.space.xl }}>
        <ProviderHealthPanel categoryId="grocery" title="Grocery network status" />
      </View>
    </Screen>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1 },
  pressed: { opacity: 0.76 },

  // Stores Strip
  storesStrip: {
    marginBottom: TC.space.base,
  },
  storesHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginBottom: TC.space.sm,
    paddingHorizontal: 2,
  },
  liveDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: TC.color.mint,
  },
  storesTitle: {
    ...TC.type.micro,
    color: TC.color.muted,
    fontWeight: '700',
    letterSpacing: 0.8,
  },
  storesRow: {
    flexDirection: 'row',
    gap: TC.space.sm,
    paddingRight: TC.space.base,
  },
  storeCard: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: TC.space.sm,
    backgroundColor: TC.color.surface,
    paddingVertical: TC.space.sm,
    paddingHorizontal: TC.space.md,
    borderRadius: TC.radius.md,
    borderWidth: 1,
    borderColor: TC.color.line,
    minWidth: 130,
    shadowColor: '#000',
    shadowOpacity: 0.03,
    shadowRadius: 4,
    shadowOffset: { width: 0, height: 1 },
    elevation: 1,
  },
  storeInfo: { gap: 1 },
  storeName: { ...TC.type.label, color: TC.color.ink, fontWeight: '700' },
  storeEtaRow: { flexDirection: 'row', alignItems: 'center', gap: 3 },
  storeEta: { ...TC.type.caption, color: TC.color.mintDeep, fontWeight: '600', fontSize: 11 },

  // Active Basket Card
  currentBasketCard: {
    marginTop: TC.space.xs,
    marginBottom: TC.space.md,
  },
  basketTop: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    justifyContent: 'space-between',
  },
  basketBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: TC.color.surface,
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: TC.radius.pill,
    alignSelf: 'flex-start',
    marginBottom: 4,
  },
  basketBadgeText: { ...TC.type.micro, color: TC.color.mintDeep, fontWeight: '700' },
  basketTitle: { color: TC.color.ink },
  basketCountPill: {
    backgroundColor: TC.color.surface,
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: TC.radius.md,
    alignItems: 'center',
  },
  basketCountValue: { ...TC.type.h2, color: TC.color.mintDeep, fontWeight: '800' },
  basketCountLabel: { ...TC.type.micro, color: TC.color.muted },
  divider: { height: 1, backgroundColor: '#C8EFE3', marginVertical: TC.space.md },
  basketTotalRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  basketTotalLabel: { ...TC.type.label, color: TC.color.inkSoft },
  basketTotalHint: { ...TC.type.caption, color: TC.color.muted },
  basketTotalValue: { ...TC.type.priceHero, color: TC.color.ink },

  // Basket Starter Card
  basketStarterCard: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: TC.space.md,
    marginBottom: TC.space.md,
    backgroundColor: TC.color.surface,
    borderColor: `${TC.color.grocery}30`,
  },
  basketStarterIcon: {
    width: 46,
    height: 46,
    borderRadius: 14,
    backgroundColor: `${TC.color.grocery}15`,
    alignItems: 'center',
    justifyContent: 'center',
  },
  basketStarterTitle: { ...TC.type.label, color: TC.color.ink, fontWeight: '700' },
  basketStarterBody: { ...TC.type.caption, color: TC.color.muted, lineHeight: 16, marginTop: 2 },

  // Aisles Grid
  aislesGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: TC.space.sm,
    marginBottom: TC.space.md,
  },
  aisleTile: {
    width: '48%',
    backgroundColor: TC.color.surfaceCard,
    borderRadius: TC.radius.card,
    padding: TC.space.base,
    borderWidth: 1,
    borderColor: TC.color.line,
    gap: TC.space.xs,
    shadowColor: '#1A0F3C',
    shadowOpacity: 0.03,
    shadowRadius: 6,
    shadowOffset: { width: 0, height: 2 },
    elevation: 1,
  },
  aisleIconWrap: {
    width: 40,
    height: 40,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 4,
  },
  aisleTitle: { ...TC.type.label, color: TC.color.ink, fontWeight: '700' },
  aisleItems: { ...TC.type.caption, color: TC.color.muted, fontSize: 11 },

  // Curated Baskets
  curatedList: {
    gap: TC.space.md,
    marginBottom: TC.space.md,
  },
  curatedCard: {
    padding: TC.space.base,
    gap: TC.space.sm,
  },
  curatedTop: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    justifyContent: 'space-between',
    gap: TC.space.sm,
  },
  curatedTitle: { ...TC.type.label, color: TC.color.ink, fontWeight: '700' },
  curatedItems: { ...TC.type.caption, color: TC.color.muted, marginTop: 2, lineHeight: 16 },
  savingsPill: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: TC.color.mintSoft,
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: TC.radius.pill,
  },
  savingsPillText: { ...TC.type.micro, color: TC.color.mintDeep, fontWeight: '700' },
  curatedDivider: { height: 1, backgroundColor: TC.color.line, marginVertical: 2 },
  curatedBottom: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  curatedWinner: { flexDirection: 'row', alignItems: 'center' },
  curatedWinnerName: { ...TC.type.caption, color: TC.color.inkSoft, fontWeight: '700' },
  curatedEta: { ...TC.type.micro, color: TC.color.muted },
  curatedPriceGroup: { alignItems: 'flex-end' },
  curatedAltPrice: { ...TC.type.caption, color: TC.color.muted, textDecorationLine: 'line-through' },
  curatedBestPrice: { ...TC.type.priceMain, color: TC.color.mintDeep },

  // Intent Chips
  intentsRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: TC.space.xs,
    marginBottom: TC.space.base,
  },
  intentChip: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: TC.color.surfaceAlt,
    borderWidth: 1,
    borderColor: TC.color.line,
    borderRadius: TC.radius.pill,
    paddingHorizontal: TC.space.md,
    paddingVertical: TC.space.sm,
  },
  intentChipText: { ...TC.type.caption, color: TC.color.inkSoft, fontWeight: '600' },
});
