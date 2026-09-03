import React from 'react';
import {
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { Feather } from '@expo/vector-icons';
import {
  AppHeader,
  Body,
  Card,
  CategoryHeroBanner,
  GlassCard,
  PrimaryButton,
  ProviderLogo,
  Screen,
  SectionHeader,
  Title,
} from '../components/ui';
import { ProviderHealthPanel } from '../components/ProviderHealthPanel';
import { TC, formatCurrency } from '../design/tokens';
import { useUserLocation } from '../location/LocationContext';

// ─── Shopping Stores ──────────────────────────────────────────────────────────
const SHOPPING_STORES = [
  { id: 'amazon', name: 'Amazon', badge: 'Prime Speed', color: '#FF9900' },
  { id: 'flipkart', name: 'Flipkart', badge: 'SuperCoins', color: '#2874F0' },
  { id: 'meesho', name: 'Meesho', badge: 'Factory Direct', color: '#9B2D9B' },
  { id: 'myntra', name: 'Myntra', badge: 'Verified Fashion', color: '#FF3F6C' },
];

// ─── Tech & Lifestyle Departments ─────────────────────────────────────────────
const SHOPPING_DEPARTMENTS = [
  { id: 'audio', label: 'Audio & ANC', query: 'wireless headphones ANC earbuds', icon: 'headphones' as const, color: '#6366F1', brands: 'Sony, boAt, Noise, Bose' },
  { id: 'smartphones', label: 'Mobiles & 5G', query: 'smartphone 5G mobile', icon: 'smartphone' as const, color: '#EC4899', brands: 'iPhone, Samsung, OnePlus' },
  { id: 'laptops', label: 'Laptops & Work', query: 'laptop ultrabook macbook', icon: 'monitor' as const, color: '#3B82F6', brands: 'Apple, Dell, HP, ASUS' },
  { id: 'wearables', label: 'Smartwatches', query: 'smartwatch fitness band', icon: 'watch' as const, color: '#10B981', brands: 'Apple Watch, Galaxy, Noise' },
  { id: 'appliances', label: 'Home & Kitchen', query: 'air fryer vacuum microwave', icon: 'home' as const, color: '#F59E0B', brands: 'Dyson, Philips, LG' },
  { id: 'gaming', label: 'Gaming Gear', query: 'gaming console controller ps5', icon: 'play' as const, color: '#8B5CF6', brands: 'PlayStation, Xbox, Logitech' },
];

// ─── Verified Deals Radar ─────────────────────────────────────────────────────
const VERIFIED_SHOPPING_DEALS = [
  {
    productName: 'Sony WH-1000XM5 Noise Cancelling Headphones',
    winnerStore: 'amazon',
    bestPrice: 26990,
    altPrice: 29990,
    savings: 3000,
    rating: '4.7 ★',
    query: 'Sony WH-1000XM5 headphones',
  },
  {
    productName: 'Apple iPhone 15 (128 GB, Black)',
    winnerStore: 'flipkart',
    bestPrice: 65499,
    altPrice: 69900,
    savings: 4401,
    rating: '4.8 ★',
    query: 'iPhone 15 128 GB',
  },
  {
    productName: 'Noise Airwave Max 6 Wireless Over-Ear Headphones',
    winnerStore: 'flipkart',
    bestPrice: 1499,
    altPrice: 1999,
    savings: 500,
    rating: '4.4 ★',
    query: 'Noise Airwave Max 6 headphones',
  },
];

export default function ShoppingHubScreen({ navigation }: any) {
  const { location } = useUserLocation();

  const search = (query = '') => {
    if (query) {
      navigation.navigate('AgentSearch', {
        category: 'Shopping',
        color: TC.color.shopping,
        initialQuery: query,
        userLocation: location,
      });
    } else {
      navigation.navigate('MainTabs', { screen: 'Compare', params: { category: 'Shopping' } });
    }
  };

  return (
    <Screen scroll={true}>
      {/* ── App Header ───────────────────────────────────────────────────── */}
      <AppHeader
        title="Shopping TrueCost"
        subtitle="Compare Amazon, Flipkart, Myntra & Meesho"
        onBack={() => navigation.goBack()}
        onNotifications={() => navigation.navigate('Notifications')}
        onProfile={() => navigation.navigate('Profile')}
      />

      {/* ── Category Hero Banner ─────────────────────────────────────────── */}
      <CategoryHeroBanner
        category="Shopping"
        title="Find the offer. Verify the real cost."
        subtitle="Cross-platform price comparison with genuine discount detection, delivery fees, and bank offer transparency."
        icon="package"
        gradientColors={['#FFF3E0', '#FAFAF8']}
        onSearchPress={() => search()}
        searchPlaceholder="Search phones, headphones, laptops, fashion…"
      />

      {/* ── Major E-Commerce Stores Strip ─────────────────────────────────── */}
      <View style={styles.storesStrip}>
        <View style={styles.storesHeader}>
          <Feather name="shield" size={13} color={TC.color.shopping} />
          <Text style={styles.storesTitle}>SUPPORTED SHOPPING PLATFORMS</Text>
        </View>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.storesRow}>
          {SHOPPING_STORES.map(s => (
            <Pressable
              key={s.id}
              onPress={() => search(s.name)}
              style={({ pressed }) => [styles.storeCard, pressed && styles.pressed]}
            >
              <ProviderLogo provider={s.id} size="sm" />
              <View style={styles.storeInfo}>
                <Text style={styles.storeName}>{s.name}</Text>
                <Text style={styles.storeBadge}>{s.badge}</Text>
              </View>
            </Pressable>
          ))}
        </ScrollView>
      </View>

      {/* ── Departments Grid ─────────────────────────────────────────────── */}
      <SectionHeader
        title="Popular departments"
        action="All categories"
        onAction={() => navigation.navigate('Explore')}
      />
      <View style={styles.departmentsGrid}>
        {SHOPPING_DEPARTMENTS.map(dept => (
          <Pressable
            key={dept.id}
            accessibilityRole="button"
            accessibilityLabel={`Explore ${dept.label}`}
            onPress={() => search(dept.query)}
            style={({ pressed }) => [styles.departmentCard, pressed && styles.pressed]}
          >
            <View style={[styles.deptIconWrap, { backgroundColor: `${dept.color}15` }]}>
              <Feather name={dept.icon} size={20} color={dept.color} />
            </View>
            <Text style={styles.deptTitle} numberOfLines={1}>{dept.label}</Text>
            <Text style={styles.deptBrands} numberOfLines={1}>{dept.brands}</Text>
          </Pressable>
        ))}
      </View>

      {/* ── Verified Live Deals Radar ─────────────────────────────────────── */}
      <SectionHeader
        title="Verified Price Drop Radar"
        action="View all deals"
        onAction={() => navigation.navigate('Deals')}
      />
      <View style={styles.dealsList}>
        {VERIFIED_SHOPPING_DEALS.map((deal, idx) => (
          <Card key={idx} style={styles.dealCard}>
            <View style={styles.dealTop}>
              <View style={{ flex: 1 }}>
                <Text style={styles.dealRating}>{deal.rating} Verified Rating</Text>
                <Text style={styles.dealName} numberOfLines={2}>{deal.productName}</Text>
              </View>
              <View style={styles.dealSavingsPill}>
                <Feather name="tag" size={11} color={TC.color.mintDeep} />
                <Text style={styles.dealSavingsText}>Save {formatCurrency(deal.savings)}</Text>
              </View>
            </View>

            <View style={styles.dealDivider} />

            <View style={styles.dealBottom}>
              <View style={styles.dealWinnerRow}>
                <ProviderLogo provider={deal.winnerStore} size="sm" />
                <View style={{ marginLeft: TC.space.xs }}>
                  <Text style={styles.dealStoreName}>Best price on {deal.winnerStore.toUpperCase()}</Text>
                  <Text style={styles.dealStoreLabel}>In stock & verified</Text>
                </View>
              </View>

              <View style={styles.dealPriceGroup}>
                <Text style={styles.dealAltPrice}>{formatCurrency(deal.altPrice)}</Text>
                <Text style={styles.dealBestPrice}>{formatCurrency(deal.bestPrice)}</Text>
              </View>
            </View>

            <PrimaryButton
              label="Compare live prices"
              size="sm"
              variant="iris"
              onPress={() => search(deal.query)}
              style={{ marginTop: TC.space.sm }}
            />
          </Card>
        ))}
      </View>

      {/* ── Quick Search Shortcuts ───────────────────────────────────────── */}
      <SectionHeader title="Trending searches" />
      <View style={styles.intentsRow}>
        {[
          'Best Noise Cancelling Headphones under 5000',
          'MacBook Air M2 vs M3',
          'Sony WH-1000XM5',
          'Samsung Galaxy S24 Ultra',
          'Nike Air Jordan 1',
          'Instant Pot 7-in-1 Duo',
        ].map(query => (
          <Pressable
            key={query}
            onPress={() => search(query)}
            style={({ pressed }) => [styles.intentChip, pressed && styles.pressed]}
          >
            <Feather name="trending-up" size={12} color={TC.color.shopping} />
            <Text style={styles.intentChipText}>{query}</Text>
          </Pressable>
        ))}
      </View>

      {/* ── Shopping Network Health ──────────────────────────────────────── */}
      <View style={{ marginTop: TC.space.xl, marginBottom: TC.space.xl }}>
        <ProviderHealthPanel categoryId="shopping" title="Shopping network status" />
      </View>
    </Screen>
  );
}

const styles = StyleSheet.create({
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
    minWidth: 135,
    shadowColor: '#000',
    shadowOpacity: 0.03,
    shadowRadius: 4,
    shadowOffset: { width: 0, height: 1 },
    elevation: 1,
  },
  storeInfo: { gap: 1 },
  storeName: { ...TC.type.label, color: TC.color.ink, fontWeight: '700' },
  storeBadge: { ...TC.type.micro, color: TC.color.muted },

  // Departments Grid
  departmentsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: TC.space.sm,
    marginBottom: TC.space.md,
  },
  departmentCard: {
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
  deptIconWrap: {
    width: 40,
    height: 40,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 4,
  },
  deptTitle: { ...TC.type.label, color: TC.color.ink, fontWeight: '700' },
  deptBrands: { ...TC.type.caption, color: TC.color.muted, fontSize: 11 },

  // Deals List
  dealsList: {
    gap: TC.space.md,
    marginBottom: TC.space.md,
  },
  dealCard: {
    padding: TC.space.base,
    gap: TC.space.sm,
  },
  dealTop: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    justifyContent: 'space-between',
    gap: TC.space.sm,
  },
  dealRating: { ...TC.type.micro, color: TC.color.amberDeep, fontWeight: '700', marginBottom: 2 },
  dealName: { ...TC.type.label, color: TC.color.ink, fontWeight: '700', lineHeight: 18 },
  dealSavingsPill: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: TC.color.mintSoft,
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: TC.radius.pill,
  },
  dealSavingsText: { ...TC.type.micro, color: TC.color.mintDeep, fontWeight: '700' },
  dealDivider: { height: 1, backgroundColor: TC.color.line, marginVertical: 2 },
  dealBottom: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  dealWinnerRow: { flexDirection: 'row', alignItems: 'center' },
  dealStoreName: { ...TC.type.caption, color: TC.color.inkSoft, fontWeight: '700' },
  dealStoreLabel: { ...TC.type.micro, color: TC.color.mintDeep },
  dealPriceGroup: { alignItems: 'flex-end' },
  dealAltPrice: { ...TC.type.caption, color: TC.color.muted, textDecorationLine: 'line-through' },
  dealBestPrice: { ...TC.type.priceMain, color: TC.color.ink, fontWeight: '800' },

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
