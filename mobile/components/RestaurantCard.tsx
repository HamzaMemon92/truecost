import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet, Image, Linking } from 'react-native';
import { tc } from '../design/tokens';

export interface RestaurantCardProps {
  id: string;
  name: string;
  brand: string;
  pricePerPerson: number;
  deliveryTime?: string;
  imageUrl?: string;
  deepLink?: string;
}

const BRAND_COLORS: Record<string, string> = {
  'Swiggy Food': '#FC8019',
  'Zomato': '#E23744',
  'MagicPin': '#7B61FF',
  'EatSure': '#00B8A9',
};

export default function RestaurantCard({ name, brand, pricePerPerson, deliveryTime, imageUrl, deepLink }: RestaurantCardProps) {
  const brandColor = BRAND_COLORS[brand] || tc.color.iris;
  const handlePress = () => deepLink && Linking.openURL(deepLink);

  return (
    <TouchableOpacity style={styles.card} onPress={handlePress} activeOpacity={0.8}>
      <View style={styles.imageWrapper}>
        {imageUrl ? (
          <Image
            source={{ uri: imageUrl.startsWith('http') ? imageUrl : `https://res.cloudinary.com/swiggy/image/upload/fl_lossy,f_auto,q_auto,w_120/${imageUrl}` }}
            style={styles.image}
            resizeMode="cover"
          />
        ) : (
          <View style={[styles.imageFallback, { backgroundColor: brandColor + '22' }]}>
            <Text style={[styles.imageFallbackText, { color: brandColor }]}>
              {name.slice(0, 2).toUpperCase()}
            </Text>
          </View>
        )}
      </View>

      <View style={styles.content}>
        <Text style={styles.name} numberOfLines={1}>{name}</Text>
        <View style={[styles.brandBadge, { backgroundColor: brandColor + '18' }]}>
          <Text style={[styles.brandText, { color: brandColor }]}>via {brand}</Text>
        </View>
        <View style={styles.footer}>
          <Text style={styles.price}>₹{Math.round(pricePerPerson)}<Text style={styles.perPerson}>/person</Text></Text>
          {deliveryTime ? (
            <Text style={styles.deliveryTime}>🕐 {deliveryTime}</Text>
          ) : null}
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
    gap: tc.space.md,
  },
  imageWrapper: {
    width: 60,
    height: 60,
    borderRadius: tc.radius.md,
    overflow: 'hidden',
    flexShrink: 0,
  },
  image: {
    width: 60,
    height: 60,
  },
  imageFallback: {
    width: 60,
    height: 60,
    alignItems: 'center',
    justifyContent: 'center',
  },
  imageFallbackText: {
    fontSize: 20,
    fontWeight: '800',
  },
  content: {
    flex: 1,
    gap: 4,
  },
  name: {
    fontSize: 15,
    fontWeight: '700',
    color: tc.color.ink,
    letterSpacing: -0.2,
  },
  brandBadge: {
    alignSelf: 'flex-start',
    borderRadius: tc.radius.sm,
    paddingHorizontal: 6,
    paddingVertical: 2,
  },
  brandText: {
    fontSize: 11,
    fontWeight: '600',
  },
  footer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginTop: 2,
  },
  price: {
    fontSize: 16,
    fontWeight: '700',
    color: tc.color.iris,
  },
  perPerson: {
    fontSize: 11,
    fontWeight: '400',
    color: tc.color.muted,
  },
  deliveryTime: {
    fontSize: 12,
    color: tc.color.muted,
  },
});
