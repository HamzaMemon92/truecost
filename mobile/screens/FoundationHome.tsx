import React, { useEffect, useRef } from 'react';
import {
  Animated,
  Easing,
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
  Screen,
  SectionHeader,
  SkeletonBox,
} from '../components/ui';
import { TC, formatCurrency, getCategoryTheme } from '../design/tokens';
import { useUserLocation } from '../location/LocationContext';
import { useApiQuery } from '../query/useApiQuery';
import { CATEGORY_CATALOG } from '../catalog/categories';
import { useSearchHistory } from '../search/SearchHistoryContext';
import type { Profile } from '../types/personalization';

type Summary = {
  saved_item_count: number;
  active_price_watch_count: number;
  cart_count: number;
  cart_item_count: number;
  estimated_cart_total: number;
  recent_activity: Array<{ id: string; title: string; event_type: string; created_at: string }>;
};

const visibleCategoryIds = ['grocery', 'shopping', 'food', 'mobility', 'travel', 'hotels', 'deals', 'finance'];

// ─── TrueCost Lens — signature intelligence animation object ─────────────────
// States: IDLE (slow breathing rings) / UNDERSTANDING / COMPARING / DECIDED
// Built with pure Animated API — no external dependencies required
function TrueCostLens({ size = 72, state = 'IDLE' }: { size?: number; state?: 'IDLE' | 'UNDERSTANDING' | 'COMPARING' | 'DECIDED' }) {
  const pulse = useRef(new Animated.Value(0)).current;
  const ringOpacity = useRef(new Animated.Value(0.35)).current;
  const innerScale = useRef(new Animated.Value(1)).current;

  useEffect(() => {
    // Slow, elegant breathing animation for IDLE state
    const breathe = Animated.loop(
      Animated.sequence([
        Animated.parallel([
          Animated.timing(pulse, { toValue: 1, duration: 2400, easing: Easing.inOut(Easing.sin), useNativeDriver: true }),
          Animated.timing(ringOpacity, { toValue: 0.12, duration: 2400, easing: Easing.inOut(Easing.sin), useNativeDriver: true }),
          Animated.timing(innerScale, { toValue: 1.06, duration: 2400, easing: Easing.inOut(Easing.sin), useNativeDriver: true }),
        ]),
        Animated.parallel([
          Animated.timing(pulse, { toValue: 0, duration: 2400, easing: Easing.inOut(Easing.sin), useNativeDriver: true }),
          Animated.timing(ringOpacity, { toValue: 0.35, duration: 2400, easing: Easing.inOut(Easing.sin), useNativeDriver: true }),
          Animated.timing(innerScale, { toValue: 1, duration: 2400, easing: Easing.inOut(Easing.sin), useNativeDriver: true }),
        ]),
      ])
    );
    breathe.start();
    return () => breathe.stop();
  }, []);

  const outerRingScale = pulse.interpolate({ inputRange: [0, 1], outputRange: [1, 1.18] });

  return (
    <View style={{ width: size, height: size, alignItems: 'center', justifyContent: 'center' }}>
      {/* Outer breathing ring */}
      <Animated.View style={{
        position: 'absolute',
        width: size,
        height: size,
        borderRadius: size / 2,
        backgroundColor: TC.color.iris,
        opacity: ringOpacity,
        transform: [{ scale: outerRingScale }],
      }} />
      {/* Mid ring */}
      <View style={{
        position: 'absolute',
        width: size * 0.74,
        height: size * 0.74,
        borderRadius: (size * 0.74) / 2,
        borderWidth: 1.5,
        borderColor: `${TC.color.iris}40`,
      }} />
      {/* Inner core */}
      <Animated.View style={{
        width: size * 0.5,
        height: size * 0.5,
        borderRadius: (size * 0.5) / 2,
        backgroundColor: TC.color.iris,
        alignItems: 'center',
        justifyContent: 'center',
        transform: [{ scale: innerScale }],
        shadowColor: TC.color.iris,
        shadowOffset: { width: 0, height: 4 },
        shadowOpacity: 0.45,
        shadowRadius: 10,
        elevation: 8,
      }}>
        <Feather name="zap" size={size * 0.22} color="#FFFFFF" />
      </Animated.View>
    </View>
  );
}

// ─── Search Lens — the ownable universal entry point ─────────────────────────
function SearchLens({ onPress }: { onPress: () => void }) {
  const scale = useRef(new Animated.Value(1)).current;

  const onPressIn = () => Animated.spring(scale, { toValue: 0.98, useNativeDriver: true, friction: 8 }).start();
  const onPressOut = () => Animated.spring(scale, { toValue: 1, useNativeDriver: true, friction: 8 }).start();

  return (
    <Pressable
      onPress={onPress}
      onPressIn={onPressIn}
      onPressOut={onPressOut}
      accessibilityRole="search"
      accessibilityLabel="Search across all providers"
    >
      <Animated.View style={[styles.searchLens, { transform: [{ scale }] }]}>
        <View style={styles.searchLensLeft}>
          <View style={styles.searchLensIcon}>
            <Feather name="search" size={16} color={TC.color.iris} />
          </View>
          <Text style={styles.searchLensText}>
            Search groceries, phones, rides, flights…
          </Text>
        </View>
        <View style={styles.searchLensRight}>
          <Feather name="sliders" size={15} color={TC.color.muted} />
        </View>
      </Animated.View>
    </Pressable>
  );
}

// ─── Main Screen ─────────────────────────────────────────────────────────────
export default function FoundationHome({ navigation }: any) {
  const { session, isGuest } = useAuth();
  const { location } = useUserLocation();
  const { recent } = useSearchHistory();
  const { data, loading } = useApiQuery<Summary>(
    'dashboard', '/commerce/dashboard/summary', { enabled: !!session, maxAge: 20_000 }
  );
  const { data: profile } = useApiQuery<Profile>(
    'profile', '/profiles/me', { enabled: !!session, maxAge: 20_000 }
  );

  const interests = profile?.preferences?.privacy?.personalized_recommendations === false
    ? [] : (profile?.preferences?.preferred_categories || []);

  const categories = CATEGORY_CATALOG
    .filter(item => visibleCategoryIds.includes(item.id))
    .sort((a, b) => Number(interests.includes(b.name)) - Number(interests.includes(a.name)));

  const openCategory = (item: (typeof CATEGORY_CATALOG)[number]) => {
    const theme = getCategoryTheme(item.id);
    const params = { category: item.engineCategory, color: theme.accent, userLocation: location };
    if (item.route) navigation.navigate(item.route, params);
    else navigation.navigate('MainTabs', { screen: 'Compare', params: { category: item.name } });
  };

  const goToSearch = () => navigation.navigate('Compare');
  const goToSearchWith = (query: string, category?: string) =>
    navigation.navigate('Compare', { category, initialQuery: query });

  return (
    <Screen scroll={true}>
      {/* ── Header ───────────────────────────────────────────────────────── */}
      <AppHeader
        showLogo={true}
        subtitle={location?.display || location?.city || 'Set your location'}
        onNotifications={() => navigation.navigate('Notifications')}
        onProfile={() => navigation.navigate('Profile')}
      />

      {/* ── Hero — TrueCost Porcelain Intelligence ────────────────────────── */}
      <View style={styles.heroOuter}>
        {/* Gradient backdrop — subtle, not garish */}
        <LinearGradient
          colors={['#EDE9FF', '#F0FDF9', '#FAFAF8']}
          start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }}
          style={styles.heroGradient}
        />
        {/* Hero content */}
        <View style={styles.heroContent}>
          <View style={styles.heroLeft}>
            {/* Eyebrow — product identity */}
            <View style={styles.heroEyebrowRow}>
              <View style={styles.heroEyebrowDot} />
              <Text style={styles.heroEyebrow}>INTELLIGENT COMPARISON</Text>
            </View>
            {/* Display headline */}
            <Text style={styles.heroTitle}>
              Where should{'\n'}you get it?
            </Text>
            {/* Supporting */}
            <Text style={styles.heroSubtitle}>
              One search. Every provider.{'\n'}The actual cost.
            </Text>
          </View>
          {/* Lens — signature brand object */}
          <View style={styles.heroRight}>
            <TrueCostLens size={80} state="IDLE" />
          </View>
        </View>

        {/* Search Lens — the primary action */}
        <SearchLens onPress={goToSearch} />

        {/* Context label */}
        <Text style={styles.heroContext}>
          Grocery · Rides · Flights · Medicine · Shopping · Finance
        </Text>
      </View>

      {/* ── Recent searches ───────────────────────────────────────────────── */}
      {recent.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionEyebrow}>RECENT</Text>
          <ScrollView
            horizontal
            showsHorizontalScrollIndicator={false}
            contentContainerStyle={styles.recentRow}
          >
            {recent.slice(0, 7).map(item => (
              <Pressable
                key={`${item.category}:${item.query}`}
                onPress={() => goToSearchWith(item.query, item.category)}
                style={({ pressed }) => [styles.recentChip, pressed && styles.pressed]}
              >
                <Feather name="clock" size={10} color={TC.color.muted} />
                <Text numberOfLines={1} style={styles.recentText}>{item.query}</Text>
              </Pressable>
            ))}
          </ScrollView>
        </View>
      )}

      {/* ── Dashboard metrics ─────────────────────────────────────────────── */}
      {session && loading && !data && (
        <View style={[styles.section, styles.metricsRow]}>
          <SkeletonBox height={80} radius={TC.radius.card} style={{ flex: 1 }} />
          <SkeletonBox height={80} radius={TC.radius.card} style={{ flex: 1 }} />
          <SkeletonBox height={80} radius={TC.radius.card} style={{ flex: 1 }} />
        </View>
      )}

      {data && (
        <View style={[styles.section, styles.metricsRow]}>
          <MetricCard icon="bookmark" value={String(data.saved_item_count)} label="Saved" color={TC.color.iris} />
          <MetricCard icon="bell" value={String(data.active_price_watch_count)} label="Alerts" color={TC.color.amber} />
          {data.cart_item_count > 0 && (
            <MetricCard
              icon="shopping-bag"
              value={String(data.cart_item_count)}
              label="In cart"
              color={TC.color.mint}
              onPress={() => navigation.navigate('Cart')}
            />
          )}
        </View>
      )}

      {/* ── Guest onboarding nudge ────────────────────────────────────────── */}
      {isGuest && !session && (
        <View style={styles.guestCard}>
          <View style={styles.guestIconWrap}>
            <Feather name="shield" size={16} color={TC.color.iris} />
          </View>
          <View style={styles.flex}>
            <Text style={styles.guestTitle}>Browsing as guest</Text>
            <Text style={styles.guestBody}>
              Comparisons work — sign in to save results and set price alerts.
            </Text>
          </View>
          <Pressable
            onPress={() => navigation.navigate('Auth')}
            style={({ pressed }) => [styles.guestCta, pressed && styles.pressed]}
          >
            <Text style={styles.guestCtaText}>Sign in</Text>
          </Pressable>
        </View>
      )}

      {/* ── Categories ───────────────────────────────────────────────────── */}
      <SectionHeader
        title="Explore categories"
        action="See all"
        onAction={() => navigation.navigate('Explore')}
        style={styles.section}
      />

      <View style={styles.categoryGrid}>
        {categories.map(item => (
          <CategoryTile
            key={item.id}
            id={item.id}
            name={item.name}
            onPress={() => openCategory(item)}
          />
        ))}
      </View>
    </Screen>
  );
}

// ─── Category Tile — premium list row ────────────────────────────────────────
function CategoryTile({ id, name, onPress }: { id: string; name: string; onPress: () => void }) {
  const theme = getCategoryTheme(id);
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={`Open ${name}`}
      onPress={onPress}
      style={({ pressed }) => [styles.catTile, pressed && styles.pressed]}
    >
      {/* Color accent strip */}
      <View style={[styles.catAccentStrip, { backgroundColor: theme.accent }]} />
      <View style={[styles.catIconWrap, { backgroundColor: `${theme.accent}18` }]}>
        <Feather name={theme.icon as any} size={19} color={theme.accent} />
      </View>
      <View style={styles.catInfo}>
        <Text style={styles.catName} numberOfLines={1}>{name}</Text>
        <Text style={styles.catSub} numberOfLines={1}>
          {getCategoryTagline(id)}
        </Text>
      </View>
      <Feather name="chevron-right" size={15} color={TC.color.subtle} />
    </Pressable>
  );
}

function getCategoryTagline(id: string): string {
  const map: Record<string, string> = {
    grocery:     'Best basket price across apps',
    shopping:    'Compare every major store',
    food:        'Delivery + fees, all included',
    mobility:    'Uber · Ola · Rapido · Namma',
    travel:      'Flights, hotels & buses',
    hotels:      'Best room rate guaranteed',
    deals:       'Top verified offers today',
    finance:     'Cards, loans & insurance',
    pharmacy:    'Generic & branded options',
  };
  return map[id] ?? 'Compare all providers';
}

// ─── Metric Card ─────────────────────────────────────────────────────────────
function MetricCard({
  icon, value, label, color, onPress,
}: { icon: any; value: string; label: string; color: string; onPress?: () => void }) {
  return (
    <Pressable
      onPress={onPress}
      style={({ pressed }) => [styles.metricCard, pressed && onPress && styles.pressed]}
    >
      <View style={[styles.metricIcon, { backgroundColor: `${color}18` }]}>
        <Feather name={icon} size={15} color={color} />
      </View>
      <Text style={[styles.metricValue, { color }]}>{value}</Text>
      <Text style={styles.metricLabel}>{label}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1 },
  pressed: { opacity: 0.74 },
  section: { marginTop: TC.space.lg },

  // ── Hero ──────────────────────────────────────────────────────────────────
  heroOuter: {
    marginTop: TC.space.sm,
    borderRadius: TC.radius.hero || 24,
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: `${TC.color.iris}22`,
    marginBottom: TC.space.sm,
  },
  heroGradient: {
    ...StyleSheet.absoluteFill,
  },
  heroContent: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingTop: TC.space.xl,
    paddingHorizontal: TC.space.xl,
    paddingBottom: TC.space.base,
    gap: TC.space.base,
  },
  heroLeft: { flex: 1, gap: TC.space.sm },
  heroRight: { alignItems: 'center', justifyContent: 'center', paddingTop: TC.space.xs },

  heroEyebrowRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: TC.space.xs,
  },
  heroEyebrowDot: {
    width: 5,
    height: 5,
    borderRadius: 2.5,
    backgroundColor: TC.color.iris,
  },
  heroEyebrow: {
    ...TC.type.micro,
    color: TC.color.iris,
    letterSpacing: 1.4,
    textTransform: 'uppercase',
    fontWeight: '700',
  },
  heroTitle: {
    fontSize: 28,
    fontWeight: '800',
    color: TC.color.ink,
    letterSpacing: -0.7,
    lineHeight: 33,
  },
  heroSubtitle: {
    ...TC.type.bodySmall,
    color: TC.color.muted,
    lineHeight: 19,
  },

  // Search Lens
  searchLens: {
    marginHorizontal: TC.space.xl,
    marginBottom: TC.space.sm,
    height: 50,
    backgroundColor: TC.color.surface,
    borderRadius: 14,
    borderWidth: 1.5,
    borderColor: `${TC.color.iris}30`,
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: TC.space.md,
    gap: TC.space.sm,
    shadowColor: TC.color.iris,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.10,
    shadowRadius: 8,
    elevation: 3,
  },
  searchLensLeft: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    gap: TC.space.sm,
  },
  searchLensIcon: {
    width: 28,
    height: 28,
    borderRadius: 8,
    backgroundColor: TC.color.irisSoft,
    alignItems: 'center',
    justifyContent: 'center',
  },
  searchLensText: {
    ...TC.type.body,
    color: TC.color.subtle,
    flex: 1,
  },
  searchLensRight: {
    width: 32,
    height: 32,
    borderRadius: 8,
    backgroundColor: TC.color.surfaceAlt,
    alignItems: 'center',
    justifyContent: 'center',
  },

  heroContext: {
    ...TC.type.micro,
    color: TC.color.muted,
    textAlign: 'center',
    paddingBottom: TC.space.base,
    letterSpacing: 0.4,
  },

  // ── Recent ────────────────────────────────────────────────────────────────
  sectionEyebrow: {
    ...TC.type.micro,
    color: TC.color.muted,
    letterSpacing: 1.0,
    textTransform: 'uppercase',
    marginBottom: TC.space.sm,
  },
  recentRow: {
    flexDirection: 'row',
    gap: TC.space.sm,
    paddingVertical: 2,
    paddingRight: TC.space.base,
  },
  recentChip: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
    height: 28,
    paddingHorizontal: TC.space.md,
    borderRadius: TC.radius.pill || 100,
    backgroundColor: TC.color.surfaceAlt,
    borderWidth: 1,
    borderColor: TC.color.line,
  },
  recentText: {
    ...TC.type.caption,
    color: TC.color.inkSoft,
    fontWeight: '500',
    maxWidth: 110,
  },

  // ── Metrics ───────────────────────────────────────────────────────────────
  metricsRow: { flexDirection: 'row', gap: TC.space.sm },
  metricCard: {
    flex: 1,
    backgroundColor: TC.color.surfaceCard,
    borderRadius: TC.radius.card,
    padding: TC.space.md,
    alignItems: 'center',
    gap: TC.space.xs,
    borderWidth: 1,
    borderColor: TC.color.line,
  },
  metricIcon: {
    width: 34,
    height: 34,
    borderRadius: 10,
    alignItems: 'center',
    justifyContent: 'center',
  },
  metricValue: {
    fontSize: 20,
    fontWeight: '800',
    letterSpacing: -0.4,
    lineHeight: 24,
  },
  metricLabel: {
    ...TC.type.caption,
    color: TC.color.muted,
    textAlign: 'center',
  },

  // ── Guest card ────────────────────────────────────────────────────────────
  guestCard: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: TC.space.md,
    backgroundColor: TC.color.irisSoft,
    borderRadius: TC.radius.card,
    padding: TC.space.base,
    marginTop: TC.space.lg,
    borderWidth: 1,
    borderColor: `${TC.color.iris}25`,
  },
  guestIconWrap: {
    width: 34,
    height: 34,
    borderRadius: 10,
    backgroundColor: `${TC.color.iris}18`,
    alignItems: 'center',
    justifyContent: 'center',
  },
  guestTitle: {
    ...TC.type.label,
    color: TC.color.ink,
    marginBottom: 2,
  },
  guestBody: {
    ...TC.type.caption,
    color: TC.color.muted,
    lineHeight: 16,
  },
  guestCta: {
    paddingHorizontal: TC.space.md,
    paddingVertical: TC.space.sm,
    borderRadius: 10,
    backgroundColor: TC.color.iris,
  },
  guestCtaText: {
    ...TC.type.label,
    color: TC.color.white,
  },

  // ── Category grid ─────────────────────────────────────────────────────────
  categoryGrid: {
    gap: TC.space.sm,
    marginBottom: TC.space.xl,
  },
  catTile: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: TC.space.md,
    backgroundColor: TC.color.surfaceCard,
    borderRadius: TC.radius.card,
    paddingVertical: TC.space.base,
    paddingRight: TC.space.base,
    paddingLeft: 0,
    borderWidth: 1,
    borderColor: TC.color.line,
    overflow: 'hidden',
    shadowColor: TC.color.ink,
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.04,
    shadowRadius: 4,
    elevation: 1,
  },
  catAccentStrip: {
    width: 4,
    alignSelf: 'stretch',
    borderRadius: 2,
    marginLeft: 0,
  },
  catIconWrap: {
    width: 40,
    height: 40,
    borderRadius: 11,
    alignItems: 'center',
    justifyContent: 'center',
  },
  catInfo: { flex: 1, gap: 2 },
  catName: {
    ...TC.type.h3,
    color: TC.color.ink,
    fontWeight: '700',
  },
  catSub: {
    ...TC.type.caption,
    color: TC.color.muted,
  },
});
