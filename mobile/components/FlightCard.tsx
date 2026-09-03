import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet, Linking } from 'react-native';
import { tc } from '../design/tokens';

export interface FlightCardProps {
  id: string;
  airlineName: string;
  price: number;
  duration?: string;
  brand: string;
  deepLink?: string;
}

const BRAND_COLORS: Record<string, string> = {
  MakeMyTrip: '#003580',
  Goibibo: '#E83E30',
  Ixigo: '#E84393',
  Cleartrip: '#E87722',
};

export default function FlightCard({ airlineName, price, duration, brand, deepLink }: FlightCardProps) {
  const brandColor = BRAND_COLORS[brand] || tc.color.iris;
  const handlePress = () => deepLink && Linking.openURL(deepLink);

  return (
    <TouchableOpacity style={styles.card} onPress={handlePress} activeOpacity={0.8}>
      <View style={styles.left}>
        <View style={styles.airlineIconWrapper}>
          <Text style={styles.airlineInitial}>{airlineName.slice(0, 2).toUpperCase()}</Text>
        </View>
        <View style={styles.airlineInfo}>
          <Text style={styles.airlineName} numberOfLines={1}>{airlineName}</Text>
          {duration ? <Text style={styles.duration}>{duration}</Text> : null}
        </View>
      </View>

      <View style={styles.right}>
        <Text style={styles.price}>₹{Math.round(price).toLocaleString('en-IN')}</Text>
        <View style={[styles.providerBadge, { backgroundColor: brandColor + '18' }]}>
          <Text style={[styles.providerText, { color: brandColor }]}>via {brand}</Text>
        </View>
      </View>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  card: {
    flexDirection: 'row',
    backgroundColor: tc.color.surface,
    borderRadius: tc.radius.lg,
    padding: tc.space.md,
    marginBottom: tc.space.sm,
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.06,
    shadowRadius: 6,
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  left: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: tc.space.sm,
    flex: 1,
  },
  airlineIconWrapper: {
    width: 44,
    height: 44,
    borderRadius: tc.radius.md,
    backgroundColor: tc.color.surfaceMuted,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: tc.color.line,
  },
  airlineInitial: {
    fontSize: 13,
    fontWeight: '800',
    color: tc.color.ink,
  },
  airlineInfo: {
    flex: 1,
  },
  airlineName: {
    fontSize: 15,
    fontWeight: '700',
    color: tc.color.ink,
    letterSpacing: -0.2,
  },
  duration: {
    fontSize: 12,
    color: tc.color.muted,
    marginTop: 2,
  },
  right: {
    alignItems: 'flex-end',
    gap: 4,
  },
  price: {
    fontSize: 18,
    fontWeight: '800',
    color: tc.color.mint,
    letterSpacing: -0.5,
  },
  providerBadge: {
    borderRadius: tc.radius.sm,
    paddingHorizontal: 6,
    paddingVertical: 2,
  },
  providerText: {
    fontSize: 10,
    fontWeight: '600',
  },
});
