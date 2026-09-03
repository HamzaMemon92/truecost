import React from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { MobilityComparisonResult, ProviderFare } from '../api/mobility';
import {
  Body,
  PrimaryButton,
  ProviderLogo,
  Screen,
  SectionHeader,
  TrueCostBreakdown,
  WinnerCard,
} from '../components/ui';
import { TC, formatCurrency } from '../design/tokens';

export default function MobilityResultsScreen({ route, navigation }: any) {
  const result = route.params?.result as MobilityComparisonResult | undefined;
  const pickup = route.params?.pickup || 'Pickup';
  const drop = route.params?.drop || 'Destination';
  const departure = route.params?.departure || 'Leave now';

  if (!result) {
    return (
      <Screen>
        <View style={styles.emptyState}>
          <View style={styles.emptyIcon}>
            <Feather name="navigation" size={28} color={TC.color.iris} />
          </View>
          <Text style={styles.emptyTitle}>No comparison available</Text>
          <Body muted style={styles.center}>Return to Mobility and calculate again.</Body>
          <PrimaryButton
            label="Go back"
            variant="outline"
            onPress={() => navigation.goBack()}
            style={styles.emptyBtn}
          />
        </View>
      </Screen>
    );
  }

  const winner = result.provider_fares.find(f => f.provider === result.recommended_provider)
    ?? result.provider_fares[0];

  return (
    <Screen>
      {/* Route header */}
      <View style={styles.routeHeader}>
        <View style={styles.routePin}>
          <Feather name="map-pin" size={14} color={TC.color.iris} />
        </View>
        <View style={styles.routeLine} />
        <View style={styles.flex}>
          <Text style={styles.routeFrom} numberOfLines={1}>{pickup}</Text>
          <Text style={styles.routeTo} numberOfLines={1}>{drop}</Text>
        </View>
        <View style={styles.routeMeta}>
          <Text style={styles.routeDist}>{result.estimated_distance_km.toFixed(1)} km</Text>
          <Text style={styles.routeTime}>{result.estimated_duration_minutes} min</Text>
        </View>
      </View>

      {/* Winner card */}
      {winner && (
        <WinnerCard
          provider={winner.provider}
          productName={`${winner.ride_class} · ETA ~${winner.eta_minutes} min`}
          price={winner.total_fare}
          savings={result.provider_fares.length > 1
            ? Math.max(...result.provider_fares.map(f => f.total_fare)) - winner.total_fare
            : undefined}
          reason={result.recommendation_reason}
          providerCount={{ compared: result.provider_fares.length, total: result.provider_fares.length }}
          freshnessLabel="Formula-based estimate"
          onPress={() => navigation.navigate('CheckoutHandoff', {
            product: { name: `${winner.ride_class} ride` },
            offer: {
              provider: winner.provider,
              price: winner.total_fare,
              deepLink: winner.deep_link,
              delivery: `Estimated pickup ${winner.eta_minutes} min`,
              observed_at: result.generated_at,
            },
            destination: drop,
            reason: 'Confirm live fare in the provider app.',
          })}
        />
      )}

      {/* All provider fares */}
      <SectionHeader title="All providers" />

      {result.provider_fares.map(fare => (
        <FareCard
          key={`${fare.provider}:${fare.ride_class}`}
          fare={fare}
          isWinner={fare.provider === result.recommended_provider}
          onHandoff={() => navigation.navigate('CheckoutHandoff', {
            product: { name: `${fare.ride_class} ride` },
            offer: {
              provider: fare.provider,
              price: fare.total_fare,
              deepLink: fare.deep_link,
              delivery: `Estimated pickup ${fare.eta_minutes} min`,
              observed_at: result.generated_at,
            },
            destination: drop,
            reason: 'Confirm live fare in the provider app.',
          })}
        />
      ))}

      {/* Disclosure */}
      <View style={styles.disclosure}>
        <Feather name="alert-circle" size={13} color={TC.color.amber} />
        <Text style={styles.disclosureText}>
          Estimates based on publicly known fare formulas. Surge, promotions and final fare are confirmed at provider checkout.
        </Text>
      </View>

      <PrimaryButton
        label="Change trip"
        variant="outline"
        onPress={() => navigation.goBack()}
        style={styles.changeBtn}
      />
    </Screen>
  );
}

// ─── FareCard ──────────────────────────────────────────────────────────────────
function FareCard({
  fare, isWinner, onHandoff,
}: { fare: ProviderFare; isWinner: boolean; onHandoff: () => void }) {
  return (
    <Pressable
      onPress={onHandoff}
      style={({ pressed }) => [styles.fareCard, isWinner && styles.fareCardWinner, pressed && styles.pressed]}
    >
      {isWinner && (
        <LinearGradient
          colors={['#E4F9F4', '#FAFAF8']}
          style={StyleSheet.absoluteFill}
          start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }}
        />
      )}

      {/* Header row */}
      <View style={styles.fareHead}>
        <ProviderLogo provider={fare.provider} size="sm" />
        <View style={styles.flex}>
          <Text style={styles.fareProvider}>{fare.provider}</Text>
          <Text style={styles.fareClass}>{fare.ride_class} · ~{fare.eta_minutes} min ETA</Text>
        </View>
        {isWinner && (
          <View style={styles.winnerPill}>
            <Text style={styles.winnerPillText}>BEST</Text>
          </View>
        )}
        <View style={styles.farePriceCol}>
          <Text style={[styles.fareTotal, isWinner && styles.fareTotalWinner]}>
            {formatCurrency(fare.total_fare)}
          </Text>
          {fare.is_surge && <Text style={styles.surgeLabel}>Surge active</Text>}
        </View>
      </View>

      {/* Breakdown */}
      <View style={styles.fareBreakdown}>
        <TrueCostBreakdown
          items={[
            { label: 'Base fare', amount: fare.base_fare },
            { label: 'Distance', amount: fare.distance_fare },
            { label: 'Time', amount: fare.time_fare },
            { label: 'Platform fee', amount: fare.platform_fee },
          ]}
          total={fare.total_fare}
        />
      </View>

      {/* CTA */}
      <View style={styles.fareAction}>
        <Text style={styles.fareActionText}>Open {fare.provider} →</Text>
      </View>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1 },
  pressed: { opacity: 0.75 },
  center: { textAlign: 'center' },

  // Route header
  routeHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: TC.space.md,
    backgroundColor: TC.color.surfaceCard,
    borderRadius: TC.radius.card,
    padding: TC.space.base,
    borderWidth: 1,
    borderColor: TC.color.line,
    marginBottom: TC.space.base,
    ...TC.shadow.xs,
  },
  routePin: {
    width: 32, height: 32, borderRadius: 16,
    backgroundColor: TC.color.irisSoft,
    alignItems: 'center', justifyContent: 'center',
  },
  routeLine: {
    width: 1, height: 32,
    backgroundColor: TC.color.line,
    marginHorizontal: TC.space.xs,
  },
  routeFrom: { ...TC.type.label, color: TC.color.muted },
  routeTo: { ...TC.type.h3, color: TC.color.ink, marginTop: 2 },
  routeMeta: { alignItems: 'flex-end', gap: 2 },
  routeDist: { ...TC.type.label, color: TC.color.iris },
  routeTime: { ...TC.type.caption, color: TC.color.muted },

  // Fare cards
  fareCard: {
    backgroundColor: TC.color.surfaceCard,
    borderRadius: TC.radius.card,
    borderWidth: 1,
    borderColor: TC.color.line,
    overflow: 'hidden',
    marginBottom: TC.space.sm,
    ...TC.shadow.xs,
  },
  fareCardWinner: {
    borderColor: TC.color.mint,
    borderWidth: 1.5,
    ...TC.shadow.winner,
  },
  fareHead: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: TC.space.md,
    padding: TC.space.base,
    paddingBottom: TC.space.sm,
  },
  fareProvider: { ...TC.type.h3, color: TC.color.ink },
  fareClass: { ...TC.type.caption, color: TC.color.muted, marginTop: 1 },
  winnerPill: {
    backgroundColor: TC.color.mintSoft,
    borderRadius: TC.radius.pill,
    paddingHorizontal: 8, paddingVertical: 2,
  },
  winnerPillText: { ...TC.type.micro, color: TC.color.mintDeep, fontWeight: '700' },
  farePriceCol: { alignItems: 'flex-end' },
  fareTotal: { ...TC.type.priceMain, color: TC.color.ink },
  fareTotalWinner: { color: TC.color.mintDeep },
  surgeLabel: { ...TC.type.caption, color: TC.color.amber, fontWeight: '600' },

  fareBreakdown: {
    paddingHorizontal: TC.space.base,
    paddingBottom: TC.space.sm,
    borderTopWidth: 1,
    borderTopColor: TC.color.line,
    paddingTop: TC.space.sm,
  },

  fareAction: {
    padding: TC.space.md,
    borderTopWidth: 1,
    borderTopColor: TC.color.line,
    alignItems: 'center',
  },
  fareActionText: { ...TC.type.label, color: TC.color.iris },

  // Disclosure
  disclosure: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: TC.space.sm,
    backgroundColor: TC.color.amberSoft,
    borderRadius: TC.radius.md,
    padding: TC.space.md,
    marginTop: TC.space.base,
  },
  disclosureText: { flex: 1, ...TC.type.caption, color: TC.color.amberDeep, lineHeight: 16 },

  changeBtn: { marginTop: TC.space.base },

  // Empty state
  emptyState: {
    flex: 1, alignItems: 'center', justifyContent: 'center',
    paddingHorizontal: TC.space.xl, gap: TC.space.md,
  },
  emptyIcon: {
    width: 64, height: 64, borderRadius: 32,
    backgroundColor: TC.color.irisSoft,
    alignItems: 'center', justifyContent: 'center',
  },
  emptyTitle: { ...TC.type.h2, color: TC.color.ink, textAlign: 'center' },
  emptyBtn: { marginTop: TC.space.sm, paddingHorizontal: TC.space.xl },
});
