import React, { useEffect, useRef } from 'react';
import {
  ActivityIndicator,
  Animated,
  Easing,
  Image,
  Pressable,
  PressableProps,
  ScrollView,
  ScrollViewProps,
  StyleProp,
  StyleSheet,
  Text,
  TextStyle,
  useWindowDimensions,
  View,
  ViewStyle,
} from 'react-native';
import { Feather } from '@expo/vector-icons';
import { SafeAreaView } from 'react-native-safe-area-context';
import { LinearGradient } from 'expo-linear-gradient';
import { TC, formatCurrency, getCategoryTheme } from '../design/tokens';

// â”€â”€â”€ PROVIDER BRAND REGISTRY â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
const PROVIDER_BRANDS: Record<string, { color: string; bg: string; initials: string }> = {
  blinkit:    { color: '#fff', bg: '#F8C800', initials: 'BK' },
  zepto:      { color: '#fff', bg: '#8B2FC9', initials: 'ZP' },
  bigbasket:  { color: '#fff', bg: '#8CC63F', initials: 'BB' },
  swiggy:     { color: '#fff', bg: '#FC8019', initials: 'SW' },
  zomato:     { color: '#fff', bg: '#E23744', initials: 'ZO' },
  amazon:     { color: '#fff', bg: '#FF9900', initials: 'AM' },
  flipkart:   { color: '#fff', bg: '#2874F0', initials: 'FK' },
  meesho:     { color: '#fff', bg: '#9B2D9B', initials: 'ME' },
  myntra:     { color: '#fff', bg: '#FF3F6C', initials: 'MN' },
  uber:       { color: '#fff', bg: '#000000', initials: 'UB' },
  ola:        { color: '#fff', bg: '#3AC663', initials: 'OL' },
  rapido:     { color: '#000', bg: '#FFD700', initials: 'RA' },
  namma_yatri:{ color: '#fff', bg: '#7B61FF', initials: 'NY' },
  makemytrip: { color: '#fff', bg: '#E8132A', initials: 'MM' },
  goibibo:    { color: '#fff', bg: '#E8132A', initials: 'GO' },
  ixigo:      { color: '#fff', bg: '#FF7900', initials: 'IX' },
  cleartrip:  { color: '#fff', bg: '#FF4F17', initials: 'CT' },
  tata1mg:    { color: '#fff', bg: '#E40000', initials: '1M' },
  pharmeasy:  { color: '#fff', bg: '#00A651', initials: 'PE' },
  apollo247:  { color: '#fff', bg: '#0067B2', initials: 'AP' },
  netmeds:    { color: '#fff', bg: '#E60000', initials: 'NM' },
  bankbazaar: { color: '#fff', bg: '#F26522', initials: 'BB' },
  notion:     { color: '#fff', bg: '#000000', initials: 'NO' },
  figma:      { color: '#fff', bg: '#F24E1E', initials: 'FG' },
  slack:      { color: '#fff', bg: '#4A154B', initials: 'SL' },
  canva:      { color: '#fff', bg: '#00C4CC', initials: 'CA' },
};

const getBrand = (provider: string) =>
  PROVIDER_BRANDS[provider.toLowerCase().replace(/\s+/g, '_')] ??
  PROVIDER_BRANDS[provider.toLowerCase()] ??
  { color: TC.color.white, bg: TC.color.iris, initials: provider.slice(0,2).toUpperCase() };

// â”€â”€â”€ SCREEN â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
export function Screen({
  children, scroll = true, contentStyle, padBottom = true, ...props
}: ScrollViewProps & { children: React.ReactNode; scroll?: boolean; contentStyle?: StyleProp<ViewStyle>; padBottom?: boolean }) {
  const { width } = useWindowDimensions();
  const pad = width < 360 ? TC.space.base : TC.space.lg;
  const base: ViewStyle = { paddingHorizontal: pad, paddingBottom: padBottom ? 100 : TC.space.xl };
  if (scroll) {
    return (
      <SafeAreaView edges={['top']} style={ss.safe}>
        <ScrollView
          keyboardShouldPersistTaps="handled"
          keyboardDismissMode="on-drag"
          showsVerticalScrollIndicator={false}
          contentContainerStyle={[base, contentStyle]}
          {...props}
        >
          {children}
        </ScrollView>
      </SafeAreaView>
    );
  }
  return (
    <SafeAreaView edges={['top']} style={ss.safe}>
      <View style={[ss.flex, base, contentStyle]}>{children}</View>
    </SafeAreaView>
  );
}

// ─── TRUECOST BRAND LOGO ───────────────────────────────────────────────────────
export function TrueCostLogo({
  variant = 'full', height = 32, style,
}: { variant?: 'full' | 'mark' | 'favicon'; height?: number; style?: StyleProp<ViewStyle> }) {
  const logoSource = variant === 'mark'
    ? require('../assets/branding/truecost-logo.png')
    : variant === 'favicon'
    ? require('../assets/branding/truecost-favicon.png')
    : require('../assets/branding/truecost-logo-full.png');

  // Aspect ratios: full logo ~ 3.8:1, mark ~ 1:1
  const width = variant === 'mark' || variant === 'favicon' ? height : height * 3.8;

  return (
    <View style={[{ height, width, justifyContent: 'center' }, style]}>
      <Image
        source={logoSource}
        style={{ width: '100%', height: '100%' }}
        resizeMode="contain"
      />
    </View>
  );
}

// ─── APP HEADER ───────────────────────────────────────────────────────────────
export function AppHeader({
  subtitle, onNotifications, onProfile, title, onBack, showLogo = false,
}: { title?: string; subtitle?: string; onNotifications?: () => void; onProfile?: () => void; onBack?: () => void; showLogo?: boolean }) {
  return (
    <View style={ss.header}>
      {onBack && (
        <Pressable onPress={onBack} style={({ pressed }) => [ss.iconBtn, pressed && ss.pressed, { marginRight: TC.space.sm }]}>
          <Feather name="arrow-left" size={TC.icon.md} color={TC.color.inkSoft} />
        </Pressable>
      )}
      <View style={ss.flex}>
        {showLogo ? (
          <TrueCostLogo height={28} />
        ) : (
          <Text style={ss.headerTitle}>{title || 'TrueCost'}</Text>
        )}
        {subtitle ? (
          <View style={ss.locationRow}>
            <Feather name="map-pin" size={11} color={TC.color.iris} style={{ marginTop: 1 }} />
            <Text numberOfLines={1} style={ss.headerSub}>{subtitle}</Text>
          </View>
        ) : null}
      </View>
      <View style={ss.headerActions}>
        {onNotifications && (
          <Pressable
            accessibilityLabel="Notifications"
            onPress={onNotifications}
            style={({ pressed }) => [ss.iconBtn, pressed && ss.pressed]}
          >
            <Feather name="bell" size={TC.icon.md} color={TC.color.inkSoft} />
          </Pressable>
        )}
        {onProfile && (
          <Pressable
            accessibilityLabel="Profile"
            onPress={onProfile}
            style={({ pressed }) => [ss.iconBtn, pressed && ss.pressed]}
          >
            <Feather name="user" size={TC.icon.md} color={TC.color.inkSoft} />
          </Pressable>
        )}
      </View>
    </View>
  );
}

// â”€â”€â”€ TYPOGRAPHY â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
export function Title({
  children, size = 'h1', style, color,
}: { children: React.ReactNode; size?: 'display'|'h1'|'h2'|'h3'; style?: StyleProp<TextStyle>; color?: string }) {
  return (
    <Text
      accessibilityRole="header"
      maxFontSizeMultiplier={1.3}
      style={[TC.type[size], { color: color ?? TC.color.ink }, style]}
    >
      {children}
    </Text>
  );
}

export function Eyebrow({ children, style }: { children: React.ReactNode; style?: StyleProp<TextStyle> }) {
  return (
    <Text maxFontSizeMultiplier={1.2} style={[ss.eyebrow, style]}>{children}</Text>
  );
}

export function Body({
  children, muted = false, size = 'body', style,
}: { children: React.ReactNode; muted?: boolean; size?: 'body'|'bodySmall'; style?: StyleProp<TextStyle> }) {
  return (
    <Text maxFontSizeMultiplier={1.5} style={[TC.type[size], { color: muted ? TC.color.muted : TC.color.inkSoft }, style]}>
      {children}
    </Text>
  );
}

export function SectionHeader({
  title, action, onAction, style,
}: { title: string; action?: string; onAction?: () => void; style?: StyleProp<ViewStyle> }) {
  return (
    <View style={[ss.sectionHeader, style]}>
      <Text style={ss.sectionTitle}>{title}</Text>
      {action && onAction ? (
        <Pressable onPress={onAction} hitSlop={8}>
          <Text style={ss.sectionAction}>{action}</Text>
        </Pressable>
      ) : null}
    </View>
  );
}

// â”€â”€â”€ CARD â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
const CARD_TONES: Record<string, ViewStyle> = {
  default: { backgroundColor: TC.color.surfaceCard },
  iris:    { backgroundColor: TC.color.irisSoft },
  mint:    { backgroundColor: TC.color.mintSoft },
  amber:   { backgroundColor: TC.color.amberSoft },
  danger:  { backgroundColor: TC.color.dangerSoft },
  dark:    { backgroundColor: TC.color.ink },
};

export function Card({
  children, tone = 'default', style, elevated = false,
}: { children: React.ReactNode; tone?: 'default'|'iris'|'mint'|'amber'|'danger'|'dark'; style?: StyleProp<ViewStyle>; elevated?: boolean }) {
  return (
    <View style={[ss.card, CARD_TONES[tone], elevated && TC.shadow.md, style]}>
      {children}
    </View>
  );
}

// â”€â”€â”€ WINNER CARD (most important component) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
export function WinnerCard({
  provider, productName, price, savings, reason, providerCount, onPress, freshnessLabel,
}: {
  provider: string;
  productName: string;
  price: number;
  savings?: number;
  reason?: string;
  providerCount?: { compared: number; total: number };
  onPress?: () => void;
  freshnessLabel?: string;
}) {
  const brand = getBrand(provider);
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={`Best option: ${provider} at ${formatCurrency(price)}`}
      onPress={onPress}
      style={({ pressed }) => [ss.winnerCard, pressed && ss.pressed]}
    >
      {/* Subtle mint gradient top bar */}
      <LinearGradient
        colors={['#E4F9F4', '#FAFAF8']}
        style={ss.winnerGradient}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
      />
      <View style={ss.winnerInner}>
        {/* Best Overall badge */}
        <View style={ss.winnerBadge}>
          <Feather name="award" size={11} color={TC.color.mint} />
          <Text style={ss.winnerBadgeText}>BEST OVERALL</Text>
        </View>

        <View style={ss.winnerBody}>
          {/* Provider identity */}
          <View style={[ss.providerDot, { backgroundColor: brand.bg }]}>
            <Text style={[ss.providerDotText, { color: brand.color }]}>{brand.initials}</Text>
          </View>
          <View style={ss.flex}>
            <Text style={ss.winnerProvider}>{provider}</Text>
            <Text numberOfLines={2} style={ss.winnerProduct}>{productName}</Text>
          </View>
          {/* Hero price */}
          <View style={ss.winnerPriceCol}>
            <Text style={ss.winnerPrice}>{formatCurrency(price)}</Text>
            {savings && savings > 0 ? (
              <View style={ss.savingsBadge}>
                <Text style={ss.savingsText}>Save {formatCurrency(savings)}</Text>
              </View>
            ) : null}
          </View>
        </View>

        {/* Reason */}
        {reason ? (
          <Text numberOfLines={2} style={ss.winnerReason}>{reason}</Text>
        ) : null}

        {/* Footer: coverage + freshness */}
        <View style={ss.winnerFooter}>
          {providerCount && providerCount.total > 1 ? (
            <Text style={ss.coverageNote}>
              Compared {providerCount.compared} of {providerCount.total} providers
            </Text>
          ) : null}
          {freshnessLabel ? (
            <View style={ss.freshnessRow}>
              <View style={ss.freshnessDot} />
              <Text style={ss.freshnessText}>{freshnessLabel}</Text>
            </View>
          ) : null}
        </View>
      </View>
    </Pressable>
  );
}

// â”€â”€â”€ PROVIDER LOGO â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
export function ProviderLogo({
  provider, size = 'md',
}: { provider: string; size?: 'sm'|'md'|'lg' }) {
  const brand = getBrand(provider);
  const dim = size === 'sm' ? 28 : size === 'lg' ? 52 : 40;
  const fontSize = size === 'sm' ? 10 : size === 'lg' ? 17 : 13;
  const radius = dim / 2.4;
  return (
    <View style={[
      ss.providerLogo,
      { width: dim, height: dim, borderRadius: radius, backgroundColor: brand.bg },
    ]}>
      <Text style={[ss.providerLogoText, { color: brand.color, fontSize }]}>
        {brand.initials}
      </Text>
    </View>
  );
}

// â”€â”€â”€ PROVIDER OFFER ROW â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
export function ProviderOfferRow({
  provider, price, originalPrice, deliveryTime, isWinner, isBlocked, onPress,
}: {
  provider: string;
  price?: number | null;
  originalPrice?: number | null;
  deliveryTime?: string | null;
  isWinner?: boolean;
  isBlocked?: boolean;
  onPress?: () => void;
}) {
  const brand = getBrand(provider);
  return (
    <Pressable
      onPress={onPress}
      style={({ pressed }) => [
        ss.offerRow,
        isWinner && ss.offerRowWinner,
        pressed && ss.pressed,
      ]}
    >
      <ProviderLogo provider={provider} size="sm" />
      <Text style={ss.offerProvider} numberOfLines={1}>{provider}</Text>
      <View style={ss.flex} />
      {isBlocked ? (
        <Text style={ss.offerBlocked}>Unavailable</Text>
      ) : price != null ? (
        <View style={ss.offerPriceGroup}>
          {originalPrice && originalPrice > price ? (
            <Text style={ss.offerOriginalPrice}>{formatCurrency(originalPrice)}</Text>
          ) : null}
          <Text style={[ss.offerPrice, isWinner && ss.offerPriceWinner]}>
            {formatCurrency(price)}
          </Text>
          {deliveryTime ? (
            <Text style={ss.offerEta}>{deliveryTime}</Text>
          ) : null}
        </View>
      ) : (
        <Text style={ss.offerBlocked}>Price unknown</Text>
      )}
      {isWinner ? (
        <View style={ss.winnerDot}>
          <Feather name="check" size={10} color={TC.color.white} />
        </View>
      ) : null}
    </Pressable>
  );
}

// â”€â”€â”€ PRIMARY BUTTON â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
export function PrimaryButton({
  label, icon, loading, disabled, variant = 'iris', size = 'md', style, ...props
}: PressableProps & {
  label: string;
  icon?: React.ComponentProps<typeof Feather>['name'];
  loading?: boolean;
  variant?: 'iris'|'mint'|'outline'|'danger'|'ghost';
  size?: 'md'|'sm';
  style?: StyleProp<ViewStyle>;
}) {
  const isDisabled = disabled || loading;
  const height = size === 'sm' ? TC.size.buttonSmall : TC.size.buttonHeight;
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityState={{ disabled: isDisabled, busy: !!loading }}
      disabled={isDisabled}
      style={({ pressed }) => [
        ss.btn, { height },
        variant === 'outline' && ss.btnOutline,
        variant === 'ghost' && ss.btnGhost,
        variant === 'danger' && ss.btnDanger,
        variant === 'mint' && ss.btnMint,
        isDisabled && ss.btnDisabled,
        pressed && !isDisabled && ss.pressed,
        style,
      ]}
      {...props}
    >
      {(variant === 'iris') && !isDisabled ? (
        <LinearGradient
          colors={[TC.color.iris, TC.color.irisBright]}
          start={{ x: 0, y: 0.5 }} end={{ x: 1, y: 0.5 }}
          style={StyleSheet.absoluteFill}
        />
      ) : null}
      {(variant === 'mint') && !isDisabled ? (
        <LinearGradient
          colors={[TC.color.mint, TC.color.mintBright]}
          start={{ x: 0, y: 0.5 }} end={{ x: 1, y: 0.5 }}
          style={StyleSheet.absoluteFill}
        />
      ) : null}
      {loading ? (
        <ActivityIndicator color={variant === 'outline' || variant === 'ghost' ? TC.color.iris : TC.color.white} />
      ) : (
        <View style={ss.btnInner}>
          {icon ? <Feather name={icon} size={TC.icon.sm} color={variant === 'outline' || variant === 'ghost' ? TC.color.iris : TC.color.white} /> : null}
          <Text style={[ss.btnLabel, (variant === 'outline' || variant === 'ghost') && ss.btnLabelDark]}>
            {label}
          </Text>
        </View>
      )}
    </Pressable>
  );
}

// â”€â”€â”€ CHIP â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
export function Chip({
  label, selected, onPress, icon,
}: { label: string; selected?: boolean; onPress?: () => void; icon?: React.ComponentProps<typeof Feather>['name'] }) {
  return (
    <Pressable
      onPress={onPress}
      style={({ pressed }) => [
        ss.chip,
        selected && ss.chipSelected,
        pressed && ss.pressed,
      ]}
    >
      {icon ? <Feather name={icon} size={12} color={selected ? TC.color.iris : TC.color.muted} /> : null}
      <Text style={[ss.chipLabel, selected && ss.chipLabelSelected]}>{label}</Text>
    </Pressable>
  );
}

// â”€â”€â”€ SEARCH BAR â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
export function SearchBar({
  placeholder = 'Search products, rides, groceriesâ€¦', onPress,
}: { placeholder?: string; onPress?: () => void }) {
  return (
    <Pressable
      accessibilityRole="search"
      accessibilityLabel="Search and compare"
      onPress={onPress}
      style={({ pressed }) => [ss.searchBar, pressed && ss.pressed]}
    >
      <View style={ss.searchIcon}>
        <Feather name="search" size={16} color={TC.color.iris} />
      </View>
      <Text style={ss.searchPlaceholder} numberOfLines={1}>{placeholder}</Text>
      <Feather name="mic" size={16} color={TC.color.muted} />
    </Pressable>
  );
}

// â”€â”€â”€ SKELETON â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
export function SkeletonBox({ width, height, style, radius }: {
  width?: number | string; height?: number; style?: StyleProp<ViewStyle>; radius?: number;
}) {
  const shimmer = useRef(new Animated.Value(0)).current;
  useEffect(() => {
    Animated.loop(
      Animated.sequence([
        Animated.timing(shimmer, { toValue: 1, duration: 900, useNativeDriver: true, easing: Easing.inOut(Easing.ease) }),
        Animated.timing(shimmer, { toValue: 0, duration: 900, useNativeDriver: true, easing: Easing.inOut(Easing.ease) }),
      ])
    ).start();
    return () => shimmer.stopAnimation();
  }, []);
  const opacity = shimmer.interpolate({ inputRange: [0, 1], outputRange: [0.5, 0.85] });
  return (
    <Animated.View
      style={[ss.skeleton,
        { width: width ?? '100%', height: height ?? 18, borderRadius: radius ?? TC.radius.sm },
        { opacity } as any,
        style,
      ] as any}
    />
  );
}

// â”€â”€â”€ EMPTY STATE â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
export function EmptyState({
  icon = 'search', title, body, actionLabel, onAction,
}: { icon?: React.ComponentProps<typeof Feather>['name']; title: string; body?: string; actionLabel?: string; onAction?: () => void }) {
  return (
    <View style={ss.emptyState}>
      <View style={ss.emptyIcon}>
        <Feather name={icon} size={28} color={TC.color.iris} />
      </View>
      <Text style={ss.emptyTitle}>{title}</Text>
      {body ? <Text style={ss.emptyBody}>{body}</Text> : null}
      {actionLabel && onAction ? (
        <PrimaryButton label={actionLabel} onPress={onAction} variant="outline" size="sm" style={ss.emptyAction} />
      ) : null}
    </View>
  );
}

// ─── DECISION HALO ────────────────────────────────────────────────────────────
export function DecisionHalo({
  children, active = true, tone = 'iris', style,
}: { children: React.ReactNode; active?: boolean; tone?: 'iris' | 'mint' | 'amber'; style?: StyleProp<ViewStyle> }) {
  const glowColor = tone === 'mint' ? TC.color.mint : tone === 'amber' ? TC.color.amber : TC.color.iris;
  return (
    <View style={[
      active && {
        shadowColor: glowColor,
        shadowOffset: { width: 0, height: 6 },
        shadowOpacity: 0.18,
        shadowRadius: 18,
        elevation: 8,
      },
      style,
    ]}>
      {children}
    </View>
  );
}

// ─── GLASS CARD ───────────────────────────────────────────────────────────────
export function GlassCard({
  children, style, onPress,
}: { children: React.ReactNode; style?: StyleProp<ViewStyle>; onPress?: () => void }) {
  const content = (
    <View style={[ss.glassCard, style]}>
      <LinearGradient
        colors={['rgba(255,255,255,0.92)', 'rgba(255,255,255,0.76)']}
        style={StyleSheet.absoluteFill}
      />
      {children}
    </View>
  );
  if (onPress) {
    return (
      <Pressable onPress={onPress} style={({ pressed }) => [pressed && ss.pressed]}>
        {content}
      </Pressable>
    );
  }
  return content;
}

// ─── CATEGORY HERO BANNER ─────────────────────────────────────────────────────
export function CategoryHeroBanner({
  category, title, subtitle, icon, gradientColors, onSearchPress, searchPlaceholder,
}: {
  category: string;
  title: string;
  subtitle: string;
  icon: React.ComponentProps<typeof Feather>['name'];
  gradientColors?: [string, string, ...string[]];
  onSearchPress?: () => void;
  searchPlaceholder?: string;
}) {
  const theme = getCategoryTheme(category);
  const colors = gradientColors ?? [theme.soft, '#FAFAF8'];

  return (
    <View style={ss.catHeroOuter}>
      <LinearGradient
        colors={colors}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
        style={StyleSheet.absoluteFill}
      />
      <View style={ss.catHeroContent}>
        <View style={ss.catHeroHeader}>
          <View style={ss.catHeroLeft}>
            <View style={ss.catHeroBadge}>
              <View style={[ss.catHeroBadgeDot, { backgroundColor: theme.accent }]} />
              <Text style={[ss.catHeroBadgeText, { color: theme.accent }]}>{category.toUpperCase()} TRUECOST</Text>
            </View>
            <Title size="h1" style={ss.catHeroTitle}>{title}</Title>
            <Body muted style={ss.catHeroSub}>{subtitle}</Body>
          </View>
          <View style={[ss.catHeroIconWrap, { backgroundColor: `${theme.accent}20` }]}>
            <Feather name={icon} size={28} color={theme.accent} />
          </View>
        </View>

        {onSearchPress && (
          <Pressable
            accessibilityRole="search"
            onPress={onSearchPress}
            style={({ pressed }) => [ss.catHeroSearch, pressed && ss.pressed]}
          >
            <Feather name="search" size={17} color={theme.accent} />
            <Text style={ss.catHeroSearchText}>{searchPlaceholder ?? `Search ${category.toLowerCase()}…`}</Text>
            <Feather name="arrow-right" size={16} color={TC.color.muted} />
          </Pressable>
        )}
      </View>
    </View>
  );
}

// ─── TRUECOST BREAKDOWN ───────────────────────────────────────────────────────
export function TrueCostBreakdown({
  items, total,
}: { items: Array<{ label: string; amount: number | null; negative?: boolean }>; total: number | null }) {
  return (
    <View style={ss.breakdown}>
      {items.map((item, i) => (
        <View key={i} style={ss.breakdownRow}>
          <Text style={ss.breakdownLabel}>{item.label}</Text>
          {item.amount !== null ? (
            <Text style={[ss.breakdownAmount, item.negative && ss.breakdownNeg]}>
              {item.negative ? '−' : ''}{formatCurrency(Math.abs(item.amount ?? 0))}
            </Text>
          ) : (
            <Text style={ss.breakdownUnknown}>Not verified</Text>
          )}
        </View>
      ))}
      <View style={ss.breakdownDivider} />
      <View style={ss.breakdownRow}>
        <Text style={ss.breakdownTotalLabel}>TrueCost</Text>
        <Text style={ss.breakdownTotal}>
          {total !== null ? formatCurrency(total) : '—'}
          {items.some(i => i.amount === null) ? ' + fees' : ''}
        </Text>
      </View>
    </View>
  );
}

// â”€â”€â”€ BADGE â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
export function Badge({
  label, tone = 'iris',
}: { label: string; tone?: 'iris'|'mint'|'amber'|'danger'|'muted' }) {
  const toneColors: Record<string, { bg: string; text: string }> = {
    iris:   { bg: TC.color.irisSoft,   text: TC.color.iris },
    mint:   { bg: TC.color.mintSoft,   text: TC.color.mintDeep },
    amber:  { bg: TC.color.amberSoft,  text: TC.color.amberDeep },
    danger: { bg: TC.color.dangerSoft, text: TC.color.danger },
    muted:  { bg: TC.color.surfaceAlt, text: TC.color.muted },
  };
  const t = toneColors[tone];
  return (
    <View style={[ss.badge, { backgroundColor: t.bg }]}>
      <Text style={[ss.badgeText, { color: t.text }]}>{label.toUpperCase()}</Text>
    </View>
  );
}

// â”€â”€â”€ DIVIDER â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
export function Divider({ style }: { style?: StyleProp<ViewStyle> }) {
  return <View style={[ss.divider, style]} />;
}

// â”€â”€â”€ PROVIDER COVERAGE NOTE â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
export function ProviderCoverageNote({
  compared, total, blockedProviders = [],
}: { compared: number; total: number; blockedProviders?: string[] }) {
  if (total <= 1) return null;
  const missing = total - compared;
  return (
    <Pressable style={ss.coverageCard}>
      <Feather name="info" size={13} color={TC.color.muted} />
      <Text style={ss.coverageText}>
        Compared {compared} of {total} providers
        {missing > 0 ? `. ${missing} currently unavailable.` : '.'}
      </Text>
      {blockedProviders.length > 0 ? (
        <Feather name="chevron-right" size={13} color={TC.color.muted} />
      ) : null}
    </Pressable>
  );
}

// â”€â”€â”€ FRESHNESS TAG â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
export function FreshnessTag({ label }: { label: string }) {
  return (
    <View style={ss.freshnessTag}>
      <View style={ss.freshDot} />
      <Text style={ss.freshLabel}>{label}</Text>
    </View>
  );
}

// â”€â”€â”€ STYLES â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
const ss = StyleSheet.create({
  safe:  { flex: 1, backgroundColor: TC.color.bg },
  flex:  { flex: 1 },
  pressed: { opacity: 0.72 },

  // Header
  header: { flexDirection: 'row', alignItems: 'center', paddingTop: TC.space.base, paddingBottom: TC.space.md },
  headerTitle: { ...TC.type.h2, color: TC.color.ink },
  headerSub: { ...TC.type.caption, color: TC.color.muted, marginLeft: 3 },
  locationRow: { flexDirection: 'row', alignItems: 'center', marginTop: 2 },
  headerActions: { flexDirection: 'row', gap: TC.space.xs },
  iconBtn: { width: 38, height: 38, borderRadius: 19, backgroundColor: TC.color.surfaceAlt, alignItems: 'center', justifyContent: 'center' },
  notifDot: { position: 'absolute', top: 9, right: 9, width: 7, height: 7, borderRadius: 3.5, backgroundColor: TC.color.iris, borderWidth: 1.5, borderColor: TC.color.surface },

  // Glass Card
  glassCard: {
    borderRadius: TC.radius.card,
    padding: TC.space.base,
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.7)',
    overflow: 'hidden',
    shadowColor: '#1A0F3C',
    shadowOpacity: 0.06,
    shadowRadius: 10,
    shadowOffset: { width: 0, height: 3 },
    elevation: 3,
  },

  // Category Hero
  catHeroOuter: {
    borderRadius: TC.radius.hero,
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: TC.color.line,
    marginBottom: TC.space.lg,
    marginTop: TC.space.xs,
  },
  catHeroContent: {
    padding: TC.space.lg,
    gap: TC.space.md,
  },
  catHeroHeader: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    justifyContent: 'space-between',
    gap: TC.space.md,
  },
  catHeroLeft: { flex: 1, gap: TC.space.xs },
  catHeroBadge: { flexDirection: 'row', alignItems: 'center', gap: 6, marginBottom: 2 },
  catHeroBadgeDot: { width: 6, height: 6, borderRadius: 3 },
  catHeroBadgeText: { ...TC.type.micro, fontWeight: '700', letterSpacing: 0.8 },
  catHeroTitle: { color: TC.color.ink, letterSpacing: -0.5 },
  catHeroSub: { ...TC.type.bodySmall, lineHeight: 19 },
  catHeroIconWrap: {
    width: 54,
    height: 54,
    borderRadius: 18,
    alignItems: 'center',
    justifyContent: 'center',
  },
  catHeroSearch: {
    height: 48,
    backgroundColor: TC.color.surface,
    borderRadius: TC.radius.md,
    borderWidth: 1,
    borderColor: TC.color.line,
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: TC.space.md,
    gap: TC.space.sm,
    shadowColor: '#1A0F3C',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
  },
  catHeroSearchText: {
    ...TC.type.bodySmall,
    color: TC.color.muted,
    flex: 1,
    fontWeight: '500',
  },

  // Eyebrow / section
  eyebrow: { ...TC.type.micro, color: TC.color.muted, letterSpacing: 1.2, textTransform: 'uppercase' },
  sectionHeader: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginBottom: TC.space.md, marginTop: TC.space.xl },
  sectionTitle: { ...TC.type.h3, color: TC.color.ink },
  sectionAction: { ...TC.type.label, color: TC.color.iris },

  // Card
  card: { borderRadius: TC.radius.card, padding: TC.space.base, borderWidth: 1, borderColor: TC.color.line },

  // Winner Card
  winnerCard: { borderRadius: TC.radius.hero, overflow: 'hidden', borderWidth: 1.5, borderColor: TC.color.mint, ...TC.shadow.winner, marginBottom: TC.space.base },
  winnerGradient: { ...StyleSheet.absoluteFill },
  winnerInner: { padding: TC.space.lg, gap: TC.space.md },
  winnerBadge: { flexDirection: 'row', alignItems: 'center', gap: TC.space.xs, alignSelf: 'flex-start', backgroundColor: TC.color.mintSoft, borderRadius: TC.radius.pill, paddingHorizontal: TC.space.sm, paddingVertical: 3 },
  winnerBadgeText: { ...TC.type.micro, color: TC.color.mintDeep, letterSpacing: 0.8 },
  winnerBody: { flexDirection: 'row', alignItems: 'center', gap: TC.space.md },
  providerDot: { width: 40, height: 40, borderRadius: TC.radius.md, alignItems: 'center', justifyContent: 'center' },
  providerDotText: { ...TC.type.label, fontWeight: '800' },
  winnerProvider: { ...TC.type.label, color: TC.color.muted },
  winnerProduct: { ...TC.type.h3, color: TC.color.ink, marginTop: 1 },
  winnerPriceCol: { alignItems: 'flex-end', gap: 3 },
  winnerPrice: { ...TC.type.priceMain, color: TC.color.ink },
  savingsBadge: { backgroundColor: TC.color.mintSoft, borderRadius: TC.radius.pill, paddingHorizontal: 8, paddingVertical: 2 },
  savingsText: { ...TC.type.caption, color: TC.color.mintDeep, fontWeight: '700' },
  winnerReason: { ...TC.type.bodySmall, color: TC.color.inkSoft, lineHeight: 18 },
  winnerFooter: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginTop: TC.space.xs },
  coverageNote: { ...TC.type.caption, color: TC.color.muted },
  freshnessRow: { flexDirection: 'row', alignItems: 'center', gap: 4 },
  freshnessDot: { width: 5, height: 5, borderRadius: 3, backgroundColor: TC.color.mint },
  freshnessText: { ...TC.type.caption, color: TC.color.muted },

  // Provider logo
  providerLogo: { alignItems: 'center', justifyContent: 'center', overflow: 'hidden' },
  providerLogoText: { fontWeight: '800', letterSpacing: 0.2 },

  // Offer row
  offerRow: { flexDirection: 'row', alignItems: 'center', gap: TC.space.md, padding: TC.space.md, borderRadius: TC.radius.md },
  offerRowWinner: { backgroundColor: TC.color.mintSoft },
  offerProvider: { ...TC.type.label, color: TC.color.inkSoft, flex: 1 },
  offerPriceGroup: { alignItems: 'flex-end', gap: 2 },
  offerPrice: { ...TC.type.priceSub, color: TC.color.ink },
  offerPriceWinner: { color: TC.color.mintDeep },
  offerOriginalPrice: { ...TC.type.caption, color: TC.color.muted, textDecorationLine: 'line-through' },
  offerEta: { ...TC.type.caption, color: TC.color.muted },
  offerBlocked: { ...TC.type.caption, color: TC.color.muted, fontStyle: 'italic' },
  winnerDot: { width: 18, height: 18, borderRadius: 9, backgroundColor: TC.color.mint, alignItems: 'center', justifyContent: 'center', marginLeft: TC.space.xs },

  // Buttons
  btn: { borderRadius: TC.radius.lg, alignItems: 'center', justifyContent: 'center', overflow: 'hidden', backgroundColor: TC.color.iris },
  btnOutline: { backgroundColor: 'transparent', borderWidth: 1.5, borderColor: TC.color.iris },
  btnGhost: { backgroundColor: 'transparent' },
  btnDanger: { backgroundColor: TC.color.danger },
  btnMint: { backgroundColor: TC.color.mint },
  btnDisabled: { backgroundColor: TC.color.surfaceAlt, borderWidth: 0 },
  btnInner: { flexDirection: 'row', alignItems: 'center', gap: TC.space.sm },
  btnLabel: { ...TC.type.label, color: TC.color.white, fontSize: 15, fontWeight: '700' },
  btnLabelDark: { color: TC.color.iris },

  // Chip
  chip: { flexDirection: 'row', alignItems: 'center', gap: 4, height: TC.size.chipHeight, paddingHorizontal: TC.space.md, borderRadius: TC.radius.pill, backgroundColor: TC.color.surfaceAlt, borderWidth: 1, borderColor: TC.color.line },
  chipSelected: { backgroundColor: TC.color.irisSoft, borderColor: TC.color.iris },
  chipLabel: { ...TC.type.caption, color: TC.color.muted },
  chipLabelSelected: { color: TC.color.iris, fontWeight: '700' },

  // Search bar
  searchBar: { height: TC.size.inputHeight, backgroundColor: TC.color.surfaceCard, borderRadius: TC.radius.lg, borderWidth: 1, borderColor: TC.color.line, flexDirection: 'row', alignItems: 'center', paddingHorizontal: TC.space.base, gap: TC.space.sm, ...TC.shadow.sm },
  searchIcon: { width: 30, height: 30, borderRadius: 15, backgroundColor: TC.color.irisSoft, alignItems: 'center', justifyContent: 'center' },
  searchPlaceholder: { flex: 1, ...TC.type.body, color: TC.color.muted },

  // Skeleton
  skeleton: { backgroundColor: TC.color.surfaceAlt },

  // Empty state
  emptyState: { alignItems: 'center', paddingVertical: TC.space.huge, paddingHorizontal: TC.space.xl, gap: TC.space.md },
  emptyIcon: { width: 64, height: 64, borderRadius: 32, backgroundColor: TC.color.irisSoft, alignItems: 'center', justifyContent: 'center' },
  emptyTitle: { ...TC.type.h3, color: TC.color.ink, textAlign: 'center' },
  emptyBody: { ...TC.type.bodySmall, color: TC.color.muted, textAlign: 'center', lineHeight: 20 },
  emptyAction: { marginTop: TC.space.sm, paddingHorizontal: TC.space.xl },

  // TrueCost breakdown
  breakdown: { gap: TC.space.sm },
  breakdownRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  breakdownLabel: { ...TC.type.bodySmall, color: TC.color.inkSoft },
  breakdownAmount: { ...TC.type.label, color: TC.color.ink },
  breakdownNeg: { color: TC.color.mint },
  breakdownUnknown: { ...TC.type.caption, color: TC.color.muted, fontStyle: 'italic' },
  breakdownDivider: { height: 1, backgroundColor: TC.color.line, marginVertical: TC.space.xs },
  breakdownTotalLabel: { ...TC.type.h3, color: TC.color.ink },
  breakdownTotal: { ...TC.type.priceMain, color: TC.color.ink },

  // Badge
  badge: { borderRadius: TC.radius.pill, paddingHorizontal: 8, paddingVertical: 3 },
  badgeText: { ...TC.type.micro, fontWeight: '700', letterSpacing: 0.6 },

  // Divider
  divider: { height: 1, backgroundColor: TC.color.line, marginVertical: TC.space.md },

  // Coverage note
  coverageCard: { flexDirection: 'row', alignItems: 'center', gap: TC.space.sm, backgroundColor: TC.color.surfaceAlt, borderRadius: TC.radius.md, padding: TC.space.md },
  coverageText: { flex: 1, ...TC.type.caption, color: TC.color.muted },

  // Freshness tag
  freshnessTag: { flexDirection: 'row', alignItems: 'center', gap: 4, alignSelf: 'flex-start' },
  freshDot: { width: 5, height: 5, borderRadius: 3, backgroundColor: TC.color.mint },
  freshLabel: { ...TC.type.caption, color: TC.color.muted },

  // Field / IconButton (back-compat)
  fieldWrap: { flexDirection: 'row', alignItems: 'center', borderWidth: 1, borderColor: TC.color.line, borderRadius: TC.radius.md, height: TC.size.inputHeight, paddingHorizontal: TC.space.base, gap: TC.space.sm, backgroundColor: TC.color.surfaceCard },
  fieldError: { borderColor: TC.color.danger },
  fieldLabel: { ...TC.type.caption, color: TC.color.muted, marginBottom: TC.space.xs },
  fieldInput: { flex: 1, ...TC.type.body, color: TC.color.ink },
});

// ─── FIELD (back-compat for auth/form screens) ────────────────────────────────
import { TextInput, TextInputProps } from 'react-native';
export function Field({
  label, error, icon, containerStyle, ...props
}: TextInputProps & { label: string; error?: string; icon?: React.ComponentProps<typeof Feather>['name']; containerStyle?: StyleProp<ViewStyle> }) {
  return (
    <View style={containerStyle}>
      <Text style={fieldSs.label}>{label}</Text>
      <View style={[fieldSs.wrap, error ? fieldSs.errWrap : undefined]}>
        {icon ? <Feather name={icon} size={TC.icon.md} color={error ? TC.color.danger : TC.color.muted} /> : null}
        <TextInput
          accessibilityLabel={label}
          placeholderTextColor={TC.color.muted}
          style={fieldSs.input}
          {...props}
        />
      </View>
      {error ? <Text style={fieldSs.err}>{error}</Text> : null}
    </View>
  );
}

const fieldSs = StyleSheet.create({
  label: { ...TC.type.caption, color: TC.color.muted, marginBottom: TC.space.xs },
  wrap: { flexDirection: 'row', alignItems: 'center', borderWidth: 1, borderColor: TC.color.line, borderRadius: TC.radius.md, height: TC.size.inputHeight, paddingHorizontal: TC.space.base, gap: TC.space.sm, backgroundColor: TC.color.surfaceCard },
  errWrap: { borderColor: TC.color.danger },
  input: { flex: 1, ...TC.type.body, color: TC.color.ink },
  err: { ...TC.type.caption, color: TC.color.danger, marginTop: TC.space.xs },
});

// ─── ICON BUTTON (back-compat for retention / detail screens) ─────────────────
export function IconButton({
  icon, onPress, label, size = 'md', variant = 'ghost',
}: {
  icon: React.ComponentProps<typeof Feather>['name'];
  onPress?: () => void;
  label?: string;
  size?: 'sm' | 'md' | 'lg';
  variant?: 'ghost' | 'filled' | 'outline';
}) {
  const dim = size === 'sm' ? 32 : size === 'lg' ? 48 : 38;
  const iconSz = size === 'sm' ? TC.icon.sm : size === 'lg' ? TC.icon.lg : TC.icon.md;
  const bg = variant === 'filled' ? TC.color.iris : variant === 'outline' ? 'transparent' : TC.color.surfaceAlt;
  const border = variant === 'outline' ? { borderWidth: 1, borderColor: TC.color.line } : {};
  const iconColor = variant === 'filled' ? TC.color.white : TC.color.inkSoft;
  return (
    <Pressable
      onPress={onPress}
      accessibilityLabel={label ?? icon}
      style={({ pressed }) => [{ width: dim, height: dim, borderRadius: dim / 2, backgroundColor: bg, alignItems: 'center', justifyContent: 'center', ...border }, pressed && { opacity: 0.7 }]}
    >
      <Feather name={icon} size={iconSz} color={iconColor} />
    </Pressable>
  );
}
