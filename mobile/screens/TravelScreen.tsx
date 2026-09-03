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
  ProviderLogo,
  Screen,
  SectionHeader,
  Title,
} from '../components/ui';
import { ProviderHealthPanel } from '../components/ProviderHealthPanel';
import TravelInput from '../components/inputs/TravelInput';
import { TC, formatCurrency } from '../design/tokens';
import { useUserLocation } from '../location/LocationContext';

const TRAVEL_PROVIDERS = [
  { id: 'makemytrip', name: 'MakeMyTrip', tag: 'Zero conv. fee bank offers', color: '#E8132A' },
  { id: 'goibibo', name: 'Goibibo', tag: 'Instant discounts', color: '#E8132A' },
  { id: 'ixigo', name: 'Ixigo', tag: 'Free cancellation options', color: '#FF7900' },
  { id: 'cleartrip', name: 'Cleartrip', tag: 'SuperCoin cashbacks', color: '#FF4F17' },
];

const POPULAR_FLIGHTS = [
  { from: 'DEL', to: 'BOM', originName: 'Delhi', destName: 'Mumbai', estFare: 3899, duration: '2h 15m', airline: 'IndiGo / Air India' },
  { from: 'BLR', to: 'DEL', originName: 'Bengaluru', destName: 'Delhi', estFare: 4899, duration: '2h 45m', airline: 'IndiGo / Vistara' },
  { from: 'BOM', to: 'GOI', originName: 'Mumbai', destName: 'Goa', estFare: 2499, duration: '1h 15m', airline: 'IndiGo / Akasa Air' },
  { from: 'BLR', to: 'HYD', originName: 'Bengaluru', destName: 'Hyderabad', estFare: 2199, duration: '1h 10m', airline: 'IndiGo / Star Air' },
];

export default function TravelScreen({ navigation, route }: any) {
  const { location } = useUserLocation();

  const userLocation = location ? {
    latitude: location.latitude,
    longitude: location.longitude,
  } : undefined;

  const handleFlightSearch = (origin: string, destination: string) => {
    navigation.navigate('AgentSearch', {
      category: 'Travel',
      color: '#1E88E5',
      initialQuery: `${origin} to ${destination}`,
      userLocation,
    });
  };

  return (
    <Screen scroll={true}>
      {/* ── App Header ───────────────────────────────────────────────────── */}
      <AppHeader
        title="Flights TrueCost"
        subtitle="Compare MakeMyTrip, Goibibo, Ixigo & Cleartrip"
        onBack={() => navigation.goBack()}
        onNotifications={() => navigation.navigate('Notifications')}
        onProfile={() => navigation.navigate('Profile')}
      />

      {/* ── Hero Banner ──────────────────────────────────────────────────── */}
      <CategoryHeroBanner
        category="Travel"
        title="Find the flight. Reveal the final fare."
        subtitle="Convenience fees, seat charges, and meal add-ons compared side-by-side across all Indian flight portals."
        icon="send"
        gradientColors={['#EBF2FF', '#FAFAF8']}
      />

      {/* ── Live OTAs Strip ──────────────────────────────────────────────── */}
      <View style={styles.storesStrip}>
        <View style={styles.storesHeader}>
          <Feather name="shield" size={13} color={TC.color.travel} />
          <Text style={styles.storesTitle}>OBSERVED TRAVEL PORTALS</Text>
        </View>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.storesRow}>
          {TRAVEL_PROVIDERS.map(p => (
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

      {/* ── Flight Search Cockpit ────────────────────────────────────────── */}
      <SectionHeader title="Search flight routes" />
      <Card style={styles.inputCard}>
        <TravelInput
          isLoading={false}
          userLocation={userLocation}
          onSearch={handleFlightSearch}
        />
      </Card>

      {/* ── Popular Flight Routes ────────────────────────────────────────── */}
      <SectionHeader title="Popular domestic sectors" />
      <View style={styles.sectorsList}>
        {POPULAR_FLIGHTS.map((f, idx) => (
          <Pressable
            key={idx}
            onPress={() => handleFlightSearch(f.originName, f.destName)}
            style={({ pressed }) => [styles.sectorCard, pressed && styles.pressed]}
          >
            <View style={styles.sectorCodes}>
              <Text style={styles.sectorCodeText}>{f.from}</Text>
              <View style={styles.flightLine}>
                <View style={styles.flightDot} />
                <Feather name="send" size={12} color={TC.color.travel} />
                <View style={styles.flightDot} />
              </View>
              <Text style={styles.sectorCodeText}>{f.to}</Text>
            </View>

            <View style={styles.sectorNames}>
              <Text style={styles.sectorNameText}>{f.originName} to {f.destName}</Text>
              <Text style={styles.sectorMetaText}>{f.duration} · {f.airline}</Text>
            </View>

            <View style={styles.sectorPriceGroup}>
              <Text style={styles.sectorPriceLabel}>From</Text>
              <Text style={styles.sectorPrice}>{formatCurrency(f.estFare)}</Text>
            </View>
          </Pressable>
        ))}
      </View>

      {/* ── Provider Readiness Health Panel ──────────────────────────────── */}
      <View style={{ marginTop: TC.space.xl, marginBottom: TC.space.xl }}>
        <ProviderHealthPanel categoryId="travel" title="Flight network status" />
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

  // Flight Sectors
  sectorsList: {
    gap: TC.space.sm,
    marginBottom: TC.space.md,
  },
  sectorCard: {
    backgroundColor: TC.color.surfaceCard,
    borderRadius: TC.radius.card,
    padding: TC.space.base,
    borderWidth: 1,
    borderColor: TC.color.line,
    gap: TC.space.xs,
  },
  sectorCodes: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  sectorCodeText: {
    fontSize: 18,
    fontWeight: '800',
    color: TC.color.ink,
    letterSpacing: 0.5,
  },
  flightLine: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    flex: 1,
    marginHorizontal: TC.space.md,
    justifyContent: 'center',
  },
  flightDot: {
    width: 4,
    height: 4,
    borderRadius: 2,
    backgroundColor: TC.color.travel,
    opacity: 0.5,
  },
  sectorNames: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  sectorNameText: {
    ...TC.type.caption,
    color: TC.color.inkSoft,
    fontWeight: '600',
  },
  sectorMetaText: {
    ...TC.type.micro,
    color: TC.color.muted,
  },
  sectorPriceGroup: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: TC.space.xs,
    paddingTop: TC.space.xs,
    borderTopWidth: 1,
    borderTopColor: TC.color.line,
  },
  sectorPriceLabel: {
    ...TC.type.caption,
    color: TC.color.muted,
  },
  sectorPrice: {
    ...TC.type.priceMain,
    color: TC.color.travel,
    fontWeight: '800',
  },
});
