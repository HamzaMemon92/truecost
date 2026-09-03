import React from 'react';
import { Linking, Pressable, StyleSheet, Text, View } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { TC, formatCurrency } from '../design/tokens';
import { ProviderLogo, FreshnessTag } from './ui';

export interface RideOffer {
  id: string;
  name: string;
  brand: string;
  price: number;
  originalPrice?: number;
  deliveryTime?: string;
  deepLink?: string;
  weightVolume?: string;
}

interface RideCompareCardProps {
  rideName: string;
  offers: RideOffer[];
}

export default function RideCompareCard({ rideName, offers }: RideCompareCardProps) {
  if (!offers || offers.length === 0) return null;

  const sorted = [...offers].sort((a, b) => a.price - b.price);
  const winner = sorted[0];
  const priceDiff = sorted.length > 1 ? sorted[sorted.length - 1].price - sorted[0].price : 0;

  const openApp = (deepLink?: string) => {
    if (deepLink) Linking.openURL(deepLink).catch(() => {});
  };

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <View>
          <Text style={styles.eyebrow}>RIDE COMPARISON</Text>
          <Text style={styles.rideName}>{rideName}</Text>
        </View>
        {priceDiff >= 10 && (
          <View style={styles.savingsBadge}>
            <Feather name="trending-down" size={11} color={TC.color.mintDeep} />
            <Text style={styles.savingsText}>Save {formatCurrency(priceDiff)}</Text>
          </View>
        )}
      </View>

      {/* Winner card */}
      <Pressable
        onPress={() => openApp(winner.deepLink)}
        style={({ pressed }) => [styles.winnerCard, pressed && styles.pressed]}
      >
        <LinearGradient
          colors={['#E4F9F4', '#F8FFFD']}
          style={StyleSheet.absoluteFill}
          start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }}
        />
        <View style={styles.winnerBadge}>
          <Feather name="award" size={10} color={TC.color.mintDeep} />
          <Text style={styles.winnerBadgeText}>BEST PRICE</Text>
        </View>
        <View style={styles.winnerRow}>
          <ProviderLogo provider={winner.brand} size="md" />
          <View style={styles.flex}>
            <Text style={styles.winnerBrand}>{winner.brand}</Text>
            <Text style={styles.winnerName}>{winner.name}</Text>
            {winner.deliveryTime && (
              <View style={styles.etaRow}>
                <Feather name="clock" size={11} color={TC.color.muted} />
                <Text style={styles.etaText}>{winner.deliveryTime} ETA</Text>
              </View>
            )}
          </View>
          <View style={styles.winnerPriceCol}>
            <Text style={styles.winnerPrice}>{formatCurrency(winner.price)}</Text>
            {priceDiff >= 10 && <Text style={styles.winnerSaving}>cheapest</Text>}
          </View>
        </View>
        {winner.deepLink && (
          <View style={styles.openRow}>
            <Text style={styles.openText}>Open {winner.brand}</Text>
            <Feather name="external-link" size={13} color={TC.color.iris} />
          </View>
        )}
      </Pressable>

      {/* Other options */}
      {sorted.slice(1).map((offer, idx) => (
        <Pressable
          key={offer.id}
          onPress={() => openApp(offer.deepLink)}
          style={({ pressed }) => [styles.altRow, pressed && styles.pressed]}
        >
          <ProviderLogo provider={offer.brand} size="sm" />
          <View style={styles.flex}>
            <Text style={styles.altBrand}>{offer.brand}</Text>
            <Text style={styles.altName}>{offer.name}</Text>
          </View>
          <View style={styles.altRight}>
            <Text style={styles.altPrice}>{formatCurrency(offer.price)}</Text>
            {offer.deliveryTime && <Text style={styles.altEta}>{offer.deliveryTime}</Text>}
            {priceDiff >= 10 && idx === sorted.length - 2 && (
              <Text style={styles.altExtra}>+{formatCurrency(offer.price - winner.price)}</Text>
            )}
          </View>
          {offer.deepLink && <Feather name="chevron-right" size={14} color={TC.color.muted} />}
        </Pressable>
      ))}

      {/* Footer */}
      <View style={styles.footer}>
        <FreshnessTag label="Estimated fares · Confirm at checkout" />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: TC.color.surfaceCard,
    borderRadius: TC.radius.hero,
    borderWidth: 1,
    borderColor: TC.color.line,
    overflow: 'hidden',
    ...TC.shadow.md,
    marginBottom: TC.space.base,
  },
  pressed: { opacity: 0.75 },
  flex: { flex: 1 },

  // Header
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: TC.space.lg,
    paddingBottom: TC.space.md,
    borderBottomWidth: 1,
    borderBottomColor: TC.color.line,
  },
  eyebrow: {
    ...TC.type.micro, color: TC.color.muted,
    letterSpacing: 0.8, textTransform: 'uppercase',
  },
  rideName: { ...TC.type.h3, color: TC.color.ink, marginTop: 2 },
  savingsBadge: {
    flexDirection: 'row', alignItems: 'center', gap: 4,
    backgroundColor: TC.color.mintSoft,
    borderRadius: TC.radius.pill,
    paddingHorizontal: TC.space.sm, paddingVertical: 4,
  },
  savingsText: { ...TC.type.caption, color: TC.color.mintDeep, fontWeight: '700' },

  // Winner
  winnerCard: {
    margin: TC.space.md,
    borderRadius: TC.radius.card,
    borderWidth: 1.5,
    borderColor: TC.color.mint,
    padding: TC.space.base,
    gap: TC.space.sm,
    overflow: 'hidden',
    ...TC.shadow.winner,
  },
  winnerBadge: {
    flexDirection: 'row', alignItems: 'center', gap: 4,
    alignSelf: 'flex-start',
    backgroundColor: TC.color.mintSoft,
    borderRadius: TC.radius.pill,
    paddingHorizontal: 8, paddingVertical: 2,
  },
  winnerBadgeText: { ...TC.type.micro, color: TC.color.mintDeep, letterSpacing: 0.6 },
  winnerRow: { flexDirection: 'row', alignItems: 'center', gap: TC.space.md },
  winnerBrand: { ...TC.type.caption, color: TC.color.muted },
  winnerName: { ...TC.type.h3, color: TC.color.ink },
  etaRow: { flexDirection: 'row', alignItems: 'center', gap: 3, marginTop: 2 },
  etaText: { ...TC.type.caption, color: TC.color.muted },
  winnerPriceCol: { alignItems: 'flex-end' },
  winnerPrice: { ...TC.type.priceMain, color: TC.color.ink },
  winnerSaving: { ...TC.type.caption, color: TC.color.mint, fontWeight: '700' },
  openRow: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'center',
    gap: TC.space.xs, paddingTop: TC.space.sm,
    borderTopWidth: 1, borderTopColor: TC.color.line,
  },
  openText: { ...TC.type.label, color: TC.color.iris },

  // Alternatives
  altRow: {
    flexDirection: 'row', alignItems: 'center',
    gap: TC.space.md,
    paddingHorizontal: TC.space.lg,
    paddingVertical: TC.space.md,
    borderTopWidth: 1,
    borderTopColor: TC.color.line,
  },
  altBrand: { ...TC.type.caption, color: TC.color.muted },
  altName: { ...TC.type.label, color: TC.color.inkSoft },
  altRight: { alignItems: 'flex-end', gap: 2 },
  altPrice: { ...TC.type.priceSub, color: TC.color.ink },
  altEta: { ...TC.type.caption, color: TC.color.muted },
  altExtra: { ...TC.type.caption, color: TC.color.danger },

  // Footer
  footer: {
    paddingHorizontal: TC.space.lg,
    paddingBottom: TC.space.md,
    paddingTop: TC.space.xs,
    borderTopWidth: 1,
    borderTopColor: TC.color.line,
  },
});
