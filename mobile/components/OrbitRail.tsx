import React, { useRef, useEffect } from 'react';
import { Animated, Easing, Pressable, StyleSheet, Text, View } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { LinearGradient } from 'expo-linear-gradient';
import { TC } from '../design/tokens';

const NAV_ITEMS = [
  { name: 'Home',    icon: 'home'     as const },
  { name: 'Explore', icon: 'compass'  as const },
  { name: 'Compare', icon: 'search'   as const },
  { name: 'Saved',   icon: 'bookmark' as const },
  { name: 'Profile', icon: 'user'     as const },
];

export function OrbitRail({ state, navigation }: any) {
  const insets = useSafeAreaInsets();
  const scaleAnims = useRef(NAV_ITEMS.map(() => new Animated.Value(1))).current;
  const opacityAnims = useRef(NAV_ITEMS.map(() => new Animated.Value(0))).current;

  useEffect(() => {
    NAV_ITEMS.forEach((_, i) => {
      Animated.spring(opacityAnims[i], {
        toValue: i === state.index ? 1 : 0,
        useNativeDriver: true,
        damping: 18,
        stiffness: 280,
      }).start();
    });
  }, [state.index]);

  const handlePress = (route: any, index: number) => {
    // Press scale animation
    Animated.sequence([
      Animated.timing(scaleAnims[index], { toValue: 0.88, duration: 80, useNativeDriver: true, easing: Easing.out(Easing.quad) }),
      Animated.spring(scaleAnims[index], { toValue: 1, useNativeDriver: true, damping: 14, stiffness: 320 }),
    ]).start();
    const event = navigation.emit({ type: 'tabPress', target: route.key, canPreventDefault: true });
    if (state.index !== index && !event.defaultPrevented) navigation.navigate(route.name);
  };

  return (
    <View pointerEvents="box-none" style={[styles.layer, { bottom: Math.max(insets.bottom, 12) }]}>
      <View style={styles.rail}>
        {state.routes.map((route: any, index: number) => {
          const active = state.index === index;
          const isCentral = route.name === 'Compare';
          const item = NAV_ITEMS.find(n => n.name === route.name) ?? NAV_ITEMS[0];

          return (
            <Animated.View
              key={route.key}
              style={[styles.itemWrap, { transform: [{ scale: scaleAnims[index] }] }]}
            >
              <Pressable
                accessibilityRole="tab"
                accessibilityLabel={isCentral ? 'Start a comparison' : route.name}
                accessibilityState={{ selected: active }}
                onPress={() => handlePress(route, index)}
                style={styles.item}
              >
                {isCentral ? (
                  <LinearGradient
                    colors={[TC.color.iris, TC.color.irisBright]}
                    style={[styles.orb, active && styles.orbActive]}
                  >
                    <Feather name={item.icon} size={22} color={TC.color.white} />
                  </LinearGradient>
                ) : (
                  <View style={styles.iconSlot}>
                    {/* Active pill background */}
                    <Animated.View
                      style={[styles.activePill, { opacity: opacityAnims[index] }]}
                    />
                    <Feather
                      name={item.icon}
                      size={19}
                      color={active ? TC.color.iris : TC.color.muted}
                    />
                  </View>
                )}
                <Text
                  maxFontSizeMultiplier={1.1}
                  numberOfLines={1}
                  style={[
                    styles.label,
                    active && styles.labelActive,
                    isCentral && styles.centralLabel,
                  ]}
                >
                  {route.name}
                </Text>
              </Pressable>
            </Animated.View>
          );
        })}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  layer: {
    position: 'absolute', left: 10, right: 10, zIndex: 100,
  },
  rail: {
    height: TC.size.navRail,
    borderRadius: TC.size.navRailRadius,
    backgroundColor: TC.color.surface,
    borderWidth: 1,
    borderColor: TC.color.line,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-around',
    paddingHorizontal: 6,
    ...TC.shadow.rail,
  },
  itemWrap: { flex: 1, alignItems: 'center' },
  item: {
    minWidth: 54, height: 62,
    alignItems: 'center', justifyContent: 'center',
    gap: 2,
  },
  iconSlot: {
    width: 40, height: 32,
    alignItems: 'center', justifyContent: 'center',
    borderRadius: TC.radius.sm,
    overflow: 'hidden',
  },
  activePill: {
    position: 'absolute', top: 0, left: 0, right: 0, bottom: 0,
    backgroundColor: TC.color.irisSoft,
    borderRadius: TC.radius.sm,
  },
  orb: {
    width: TC.size.orbSize,
    height: TC.size.orbSize,
    marginTop: -20,
    borderRadius: TC.size.orbSize / 2,
    borderWidth: 4,
    borderColor: TC.color.bg,
    alignItems: 'center',
    justifyContent: 'center',
    ...TC.shadow.iris,
  },
  orbActive: { borderColor: '#E8E3FF' },
  label: {
    fontSize: 9, fontWeight: '600', letterSpacing: 0.1,
    color: TC.color.muted, lineHeight: 12,
  },
  labelActive: { color: TC.color.iris, fontWeight: '800' },
  centralLabel: { marginTop: 2, color: TC.color.iris, fontWeight: '800' },
});
