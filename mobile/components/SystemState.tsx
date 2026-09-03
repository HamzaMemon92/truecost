import React, { useEffect, useRef } from 'react';
import { ActivityIndicator, Animated, StyleSheet, Text, View } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { PrimaryButton } from './ui';
import { tc } from '../design/tokens';
import { useExperience } from '../accessibility/ExperienceContext';
import { ApiError } from '../api/client';

export type SystemStateKind =
  | 'loading' | 'searching' | 'checking_offers' | 'calculating' | 'empty' | 'empty_cart'
  | 'empty_saved' | 'empty_notifications' | 'empty_activity' | 'offline' | 'timeout'
  | 'rate_limited' | 'quota_exhausted' | 'unavailable' | 'partial' | 'price_changed'
  | 'unsupported_location' | 'success' | 'saved' | 'alert_created' | 'shared';

const copy: Record<SystemStateKind, { icon: React.ComponentProps<typeof Feather>['name']; title: string; body: string }> = {
  loading: { icon: 'loader', title: 'Working on your decision', body: 'We are checking the information available to TrueCost.' },
  searching: { icon: 'search', title: 'Searching available providers', body: 'Results appear as they are received.' },
  checking_offers: { icon: 'tag', title: 'Checking observed offers', body: 'Eligibility and final value are confirmed at provider checkout.' },
  calculating: { icon: 'cpu', title: 'Calculating TrueCost', body: 'Observed prices and known fees are being evaluated separately.' },
  empty: { icon: 'search', title: 'Nothing to show yet', body: 'Try a more specific search or begin a new comparison.' },
  empty_cart: { icon: 'shopping-bag', title: 'Your cart is ready for a first item', body: 'Add products from a comparison to build a basket.' },
  empty_saved: { icon: 'bookmark', title: 'No saved decisions yet', body: 'Save a product or comparison to find it here.' },
  empty_notifications: { icon: 'bell', title: 'You are all caught up', body: 'Price watches and useful updates will appear here.' },
  empty_activity: { icon: 'clock', title: 'No activity yet', body: 'Completed searches, saves and handoffs will appear here.' },
  offline: { icon: 'wifi-off', title: 'TrueCost cannot be reached', body: 'Check your connection, then retry to refresh observed prices and availability.' },
  timeout: { icon: 'clock', title: 'This is taking longer than expected', body: 'Try again without losing your search details.' },
  rate_limited: { icon: 'pause-circle', title: 'Please wait a moment', body: 'Too many requests arrived together. Your existing results are still available.' },
  quota_exhausted: { icon: 'alert-triangle', title: 'Comparison limit reached', body: 'Try again later or continue with already observed results.' },
  unavailable: { icon: 'slash', title: 'Provider temporarily unavailable', body: 'Other available options remain visible when supported.' },
  partial: { icon: 'alert-circle', title: 'Some results are unavailable', body: 'This decision uses only the providers that responded.' },
  price_changed: { icon: 'trending-up', title: 'Price changed', body: 'Review the latest observed total before opening the provider.' },
  unsupported_location: { icon: 'map-pin', title: 'Not available in this location', body: 'Choose another location to continue.' },
  success: { icon: 'check', title: 'Done', body: 'Your action completed successfully.' },
  saved: { icon: 'bookmark', title: 'Saved successfully', body: 'This decision is now available from Saved.' },
  alert_created: { icon: 'bell', title: 'Alert created', body: 'We will use your target when new observations arrive.' },
  shared: { icon: 'share-2', title: 'Comparison shared', body: 'The available comparison details are ready to send.' },
};

export function SystemState({ kind, actionLabel, onAction, compact = false }: { kind: SystemStateKind; actionLabel?: string; onAction?: () => void; compact?: boolean }) {
  const { reduceMotion } = useExperience(); const opacity = useRef(new Animated.Value(1)).current;
  const item = copy[kind];
  const loading = ['loading', 'searching', 'checking_offers', 'calculating'].includes(kind);
  useEffect(() => { if (!loading || reduceMotion) { opacity.setValue(1); return; } const loop = Animated.loop(Animated.sequence([Animated.timing(opacity, { toValue: .55, duration: tc.motion.standard, useNativeDriver: true }), Animated.timing(opacity, { toValue: 1, duration: tc.motion.standard, useNativeDriver: true })])); loop.start(); return () => loop.stop(); }, [loading, reduceMotion, opacity]);
  return <View accessibilityRole="alert" style={[styles.wrap, compact && styles.compact]}>
    <Animated.View style={[styles.icon, { opacity }]}>{loading ? <ActivityIndicator color={tc.color.iris} /> : <Feather name={item.icon} size={25} color={tc.color.iris} />}</Animated.View>
    <Text style={styles.title}>{item.title}</Text><Text style={styles.body}>{item.body}</Text>
    {actionLabel && onAction ? <PrimaryButton label={actionLabel} onPress={onAction} style={styles.action} /> : null}
  </View>;
}

export function stateKindForError(error: unknown): SystemStateKind {
  if (!(error instanceof ApiError)) return 'unavailable';
  if (error.status === 0) return 'offline';
  if (error.status === 408 || error.status === 504) return 'timeout';
  if (error.status === 429) return error.code === 'quota_exhausted' ? 'quota_exhausted' : 'rate_limited';
  if (error.status === 503) return 'unavailable';
  return 'unavailable';
}
const styles = StyleSheet.create({
  wrap: { alignItems: 'center', padding: 28, borderRadius: tc.radius.lg, backgroundColor: tc.color.surface, borderWidth: 1, borderColor: tc.color.line, marginTop: tc.space.md },
  compact: { padding: tc.space.md }, icon: { width: 54, height: 54, borderRadius: 19, backgroundColor: tc.color.irisSoft, alignItems: 'center', justifyContent: 'center' },
  title: { ...tc.type.h3, color: tc.color.ink, marginTop: tc.space.md, textAlign: 'center' },
  body: { ...tc.type.bodySmall, color: tc.color.muted, textAlign: 'center', marginTop: tc.space.xs },
  action: { minWidth: 140, marginTop: tc.space.md },
});
