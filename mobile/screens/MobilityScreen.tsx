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
  ProviderLogo,
  Screen,
  SectionHeader,
  Title,
} from '../components/ui';
import { ProviderHealthPanel } from '../components/ProviderHealthPanel';
import MobilityInput from '../components/inputs/MobilityInput';
import { TC, formatCurrency } from '../design/tokens';
import { useUserLocation } from '../location/LocationContext';

const MOBILITY_PROVIDERS = [
  { id: 'uber', name: 'Uber', tag: 'Fastest dispatch', color: '#000000' },
  { id: 'ola', name: 'Ola', tag: 'Wide fleet', color: '#3AC663' },
  { id: 'rapido', name: 'Rapido', tag: 'Lowest bike fares', color: '#FFD700' },
  { id: 'namma_yatri', name: 'Namma Yatri', tag: 'Zero commission auto', color: '#7B61FF' },
];

const RIDE_TYPES = [
  { id: 'auto', label: 'Auto Rickshaw', icon: 'navigation' as const, color: '#F59E0B', desc: 'Direct meter & app autos', providers: 'Namma Yatri · Uber · Ola · Rapido' },
  { id: 'bike', label: 'Bike Taxi', icon: 'zap' as const, color: '#10B981', desc: 'Beat peak traffic', providers: 'Rapido · Uber Moto · Ola Bike' },
  { id: 'cab_mini', label: 'Cab Mini / Go', icon: 'disc' as const, color: '#3B82F6', desc: 'Budget AC hatchbacks', providers: 'Uber Go · Ola Mini' },
  { id: 'cab_sedan', label: 'Prime Sedan', icon: 'shield' as const, color: '#8B5CF6', desc: 'Comfort & top rated drivers', providers: 'Uber Premier · Ola Prime' },
];

const POPULAR_ROUTES = [
  { title: 'To Airport (Terminal 1/2)', pickup: 'Current Location', dropoff: 'Kempegowda Int. Airport', estFare: '₹649 - ₹890', estTime: '45 mins' },
  { title: 'To Central Railway Station', pickup: 'Current Location', dropoff: 'KSR Bengaluru Station', estFare: '₹149 - ₹210', estTime: '22 mins' },
  { title: 'To Tech Park / Work', pickup: 'Current Location', dropoff: 'Manyata / Ecospace Tech Park', estFare: '₹220 - ₹340', estTime: '30 mins' },
];

export default function MobilityScreen({ navigation, route }: any) {
  const { location } = useUserLocation();

  const userLocation = location ? {
    latitude: location.latitude,
    longitude: location.longitude,
  } : undefined;

  const handleRouteSearch = (pickup: string, dropoff: string) => {
    navigation.navigate('AgentSearch', {
      category: 'Mobility',
      color: '#222222',
      initialQuery: `${pickup} to ${dropoff}`,
      userLocation,
    });
  };

  return (
    <Screen scroll={true}>
      {/* ── App Header ───────────────────────────────────────────────────── */}
      <AppHeader
        title="Rides TrueCost"
        subtitle={location?.display || location?.city || 'Locating nearby drivers…'}
        onBack={() => navigation.goBack()}
        onNotifications={() => navigation.navigate('Notifications')}
        onProfile={() => navigation.navigate('Profile')}
      />

      {/* ── Hero Banner ──────────────────────────────────────────────────── */}
      <CategoryHeroBanner
        category="Mobility"
        title="Compare every ride. Pay the honest fare."
        subtitle="Live surge detector & fare comparison across Uber, Ola, Rapido, and Namma Yatri."
        icon="navigation"
        gradientColors={['#F0F0F0', '#FAFAF8']}
      />

      {/* ── Live Ride Providers ───────────────────────────────────────────── */}
      <View style={styles.storesStrip}>
        <View style={styles.storesHeader}>
          <View style={styles.liveDot} />
          <Text style={styles.storesTitle}>LIVE RIDE NETWORKS</Text>
        </View>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.storesRow}>
          {MOBILITY_PROVIDERS.map(p => (
            <View key={p.id} style={styles.storeCard}>
              <ProviderLogo provider={p.id} size="sm" />
              <View style={styles.storeInfo}>
                <Text style={styles.storeName}>{p.name}</Text>
                <Text style={styles.storeTag}>{p.tag}</Text>
              </View>
            </View>
          ))}
        </ScrollView>
      </View>

      {/* ── Where to? Destination Search Card ────────────────────────────── */}
      <SectionHeader title="Book a ride" />
      <Card style={styles.inputCard}>
        <MobilityInput
          isLoading={false}
          userLocation={userLocation}
          onSearch={handleRouteSearch}
        />
      </Card>

      {/* ── Vehicle Classes ──────────────────────────────────────────────── */}
      <SectionHeader title="Ride categories" />
      <View style={styles.vehicleGrid}>
        {RIDE_TYPES.map(v => (
          <View key={v.id} style={styles.vehicleCard}>
            <View style={[styles.vehicleIcon, { backgroundColor: `${v.color}15` }]}>
              <Feather name={v.icon} size={20} color={v.color} />
            </View>
            <View style={styles.vehicleInfo}>
              <Text style={styles.vehicleTitle}>{v.label}</Text>
              <Text style={styles.vehicleDesc}>{v.desc}</Text>
              <Text style={styles.vehicleProviders}>{v.providers}</Text>
            </View>
          </View>
        ))}
      </View>

      {/* ── Popular Quick-Compare Routes ─────────────────────────────────── */}
      <SectionHeader title="Popular destinations" />
      <View style={styles.routesList}>
        {POPULAR_ROUTES.map((r, idx) => (
          <Pressable
            key={idx}
            onPress={() => handleRouteSearch(r.pickup, r.dropoff)}
            style={({ pressed }) => [styles.routeCard, pressed && styles.pressed]}
          >
            <View style={styles.routeIconWrap}>
              <Feather name="map-pin" size={18} color={TC.color.iris} />
            </View>
            <View style={styles.routeInfo}>
              <Text style={styles.routeTitle}>{r.title}</Text>
              <Text style={styles.routeSub}>{r.dropoff}</Text>
              <View style={styles.routeMeta}>
                <Text style={styles.routeFare}>Est. {r.estFare}</Text>
                <Text style={styles.routeDot}>·</Text>
                <Text style={styles.routeTime}>{r.estTime}</Text>
              </View>
            </View>
            <Feather name="arrow-right" size={16} color={TC.color.muted} />
          </Pressable>
        ))}
      </View>

      {/* ── Provider Readiness Health Panel ──────────────────────────────── */}
      <View style={{ marginTop: TC.space.xl, marginBottom: TC.space.xl }}>
        <ProviderHealthPanel categoryId="mobility" title="Mobility network status" />
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
    minWidth: 140,
    shadowColor: '#000',
    shadowOpacity: 0.03,
    shadowRadius: 4,
    shadowOffset: { width: 0, height: 1 },
    elevation: 1,
  },
  storeInfo: { gap: 1 },
  storeName: { ...TC.type.label, color: TC.color.ink, fontWeight: '700' },
  storeTag: { ...TC.type.micro, color: TC.color.muted },

  // Input Card
  inputCard: {
    padding: TC.space.base,
    marginBottom: TC.space.md,
    backgroundColor: TC.color.surfaceCard,
  },

  // Vehicle Classes
  vehicleGrid: {
    gap: TC.space.sm,
    marginBottom: TC.space.md,
  },
  vehicleCard: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: TC.space.md,
    backgroundColor: TC.color.surfaceCard,
    padding: TC.space.base,
    borderRadius: TC.radius.card,
    borderWidth: 1,
    borderColor: TC.color.line,
  },
  vehicleIcon: {
    width: 44,
    height: 44,
    borderRadius: 14,
    alignItems: 'center',
    justifyContent: 'center',
  },
  vehicleInfo: { flex: 1, gap: 2 },
  vehicleTitle: { ...TC.type.label, color: TC.color.ink, fontWeight: '700' },
  vehicleDesc: { ...TC.type.caption, color: TC.color.inkSoft },
  vehicleProviders: { ...TC.type.micro, color: TC.color.muted, marginTop: 1 },

  // Popular Routes
  routesList: {
    gap: TC.space.sm,
    marginBottom: TC.space.md,
  },
  routeCard: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: TC.space.md,
    backgroundColor: TC.color.surfaceCard,
    padding: TC.space.base,
    borderRadius: TC.radius.card,
    borderWidth: 1,
    borderColor: TC.color.line,
  },
  routeIconWrap: {
    width: 38,
    height: 38,
    borderRadius: 12,
    backgroundColor: TC.color.irisSoft,
    alignItems: 'center',
    justifyContent: 'center',
  },
  routeInfo: { flex: 1, gap: 1 },
  routeTitle: { ...TC.type.label, color: TC.color.ink, fontWeight: '700' },
  routeSub: { ...TC.type.caption, color: TC.color.muted },
  routeMeta: { flexDirection: 'row', alignItems: 'center', gap: 6, marginTop: 3 },
  routeFare: { ...TC.type.caption, color: TC.color.mintDeep, fontWeight: '700' },
  routeDot: { color: TC.color.subtle },
  routeTime: { ...TC.type.caption, color: TC.color.muted },
});
