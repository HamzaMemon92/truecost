import React, { useEffect, useRef } from 'react';
import { Animated, Easing, StyleSheet, View } from 'react-native';
import { TC } from '../design/tokens';

export function SkeletonCard({ compact = false }: { compact?: boolean }) {
  const shimmer = useRef(new Animated.Value(0)).current;
  useEffect(() => {
    Animated.loop(
      Animated.sequence([
        Animated.timing(shimmer, { toValue: 1, duration: 850, useNativeDriver: true, easing: Easing.inOut(Easing.ease) }),
        Animated.timing(shimmer, { toValue: 0, duration: 850, useNativeDriver: true, easing: Easing.inOut(Easing.ease) }),
      ])
    ).start();
    return () => shimmer.stopAnimation();
  }, []);
  const opacity = shimmer.interpolate({ inputRange: [0, 1], outputRange: [0.45, 0.8] });

  return (
    <Animated.View style={[styles.card, { opacity } as any]}>
      <View style={styles.imageArea} />
      <View style={styles.body}>
        <View style={[styles.line, { width: '70%' }]} />
        <View style={[styles.line, { width: '45%', height: 10, marginTop: 4 }]} />
        {!compact && <View style={[styles.line, { width: '55%', height: 20, marginTop: 10, borderRadius: 8 }]} />}
      </View>
    </Animated.View>
  );
}

export default SkeletonCard;

const styles = StyleSheet.create({
  card: {
    backgroundColor: TC.color.surfaceCard,
    borderRadius: TC.radius.card,
    borderWidth: 1,
    borderColor: TC.color.line,
    overflow: 'hidden',
    marginBottom: TC.space.md,
  },
  imageArea: { height: 110, backgroundColor: TC.color.surfaceAlt },
  body: { padding: TC.space.base, gap: TC.space.sm },
  line: { height: 14, backgroundColor: TC.color.surfaceAlt, borderRadius: TC.radius.xs },
});
