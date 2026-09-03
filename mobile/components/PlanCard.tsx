import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet, Linking } from 'react-native';
import { tc } from '../design/tokens';

export interface PlanCardProps {
  id: string;
  name: string;
  brand: string;
  price: number;
  weightVolume?: string;
  deliveryTime?: string;   // features or highlights
  deepLink?: string;
}

const BRAND_COLORS: Record<string, string> = {
  Notion: '#000000',
  Figma: '#A259FF',
  Slack: '#4A154B',
  Canva: '#00C4CC',
};

const FREE_THRESHOLD = 0.01;

export default function PlanCard({ name, brand, price, weightVolume, deliveryTime, deepLink }: PlanCardProps) {
  const brandColor = BRAND_COLORS[brand] || tc.color.iris;
  const isFree = price < FREE_THRESHOLD;
  const isEnterprise = !isFree && !price;

  const handlePress = () => deepLink && Linking.openURL(deepLink);

  return (
    <TouchableOpacity style={styles.card} onPress={handlePress} activeOpacity={0.8}>
      {/* Left accent bar */}
      <View style={[styles.accentBar, { backgroundColor: brandColor }]} />

      <View style={styles.body}>
        <View style={styles.topRow}>
          <View style={styles.nameGroup}>
            <View style={[styles.brandChip, { backgroundColor: brandColor + '18' }]}>
              <Text style={[styles.brandText, { color: brandColor }]}>{brand}</Text>
            </View>
            <Text style={styles.planName}>{name}</Text>
          </View>

          <View style={styles.priceGroup}>
            {isFree ? (
              <View style={styles.freeBadge}>
                <Text style={styles.freeText}>FREE</Text>
              </View>
            ) : isEnterprise ? (
              <Text style={styles.customPrice}>Custom</Text>
            ) : (
              <>
                <Text style={styles.price}>₹{Math.round(price)}</Text>
                <Text style={styles.pricePeriod}>{weightVolume || '/mo'}</Text>
              </>
            )}
          </View>
        </View>

        {/* Features highlight */}
        {deliveryTime ? (
          <Text style={styles.features} numberOfLines={2}>{deliveryTime}</Text>
        ) : null}
      </View>

      <View style={styles.arrow}>
        <Text style={[styles.arrowText, { color: brandColor }]}>›</Text>
      </View>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  card: {
    flexDirection: 'row',
    backgroundColor: tc.color.surface,
    borderRadius: tc.radius.lg,
    marginBottom: tc.space.sm,
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.06,
    shadowRadius: 6,
    overflow: 'hidden',
    alignItems: 'center',
  },
  accentBar: {
    width: 4,
    alignSelf: 'stretch',
  },
  body: {
    flex: 1,
    padding: tc.space.md,
    paddingLeft: tc.space.sm + 4,
  },
  topRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    justifyContent: 'space-between',
  },
  nameGroup: {
    flex: 1,
    gap: 4,
  },
  brandChip: {
    alignSelf: 'flex-start',
    borderRadius: tc.radius.sm,
    paddingHorizontal: 6,
    paddingVertical: 2,
  },
  brandText: {
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 0.5,
  },
  planName: {
    fontSize: 15,
    fontWeight: '700',
    color: tc.color.ink,
    letterSpacing: -0.2,
  },
  priceGroup: {
    alignItems: 'flex-end',
    paddingLeft: tc.space.sm,
  },
  freeBadge: {
    backgroundColor: tc.color.mint + '20',
    borderRadius: tc.radius.sm,
    paddingHorizontal: 8,
    paddingVertical: 4,
  },
  freeText: {
    fontSize: 11,
    fontWeight: '800',
    color: tc.color.mint,
    letterSpacing: 1,
  },
  customPrice: {
    fontSize: 13,
    fontWeight: '600',
    color: tc.color.muted,
  },
  price: {
    fontSize: 20,
    fontWeight: '800',
    color: tc.color.iris,
    letterSpacing: -0.5,
  },
  pricePeriod: {
    fontSize: 10,
    color: tc.color.muted,
    marginTop: 1,
  },
  features: {
    fontSize: 12,
    color: tc.color.muted,
    marginTop: 6,
    lineHeight: 17,
  },
  arrow: {
    paddingRight: tc.space.md,
  },
  arrowText: {
    fontSize: 22,
    fontWeight: '300',
  },
});
