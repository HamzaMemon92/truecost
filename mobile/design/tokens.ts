import { Platform, StyleSheet, ViewStyle } from 'react-native';

// ─── TrueCost Design System v2 ─────────────────────────────────────────────
// Porcelain White base · Ink Navy primary · Electric Iris accent
// Sea-Glass Mint for savings · Amber for urgency
// ──────────────────────────────────────────────────────────────────────────

export const TC = {
  // ── Color Palette ─────────────────────────────────────────────────────
  color: {
    // Base surfaces
    bg:          '#FAFAF8',   // warm porcelain white
    surface:     '#FFFFFF',
    surfaceAlt:  '#F5F4F1',   // very subtle warm gray
    surfaceCard: '#FFFFFF',
    overlay:     'rgba(20,18,32,0.44)',

    // Ink (text / primary dark)
    ink:         '#0F0E17',   // near-black with warm blue undertone
    inkSoft:     '#2D2B3A',   // body text
    muted:       '#8B8898',   // supporting / captions
    subtle:      '#C4C1D0',   // disabled / placeholders

    // Brand — Electric Iris
    iris:        '#5B4FE9',   // primary CTA, selection, AI
    irisBright:  '#7B6FF5',   // gradient end
    irisSoft:    '#EDE9FF',   // iris tinted surface
    irisDeep:    '#3D32C4',   // pressed / emphasis

    // Savings — Sea-Glass Mint
    mint:        '#0DAF8A',   // savings, positive
    mintBright:  '#1DC9A0',
    mintSoft:    '#E4F9F4',
    mintDeep:    '#097A61',

    // Urgency — Amber
    amber:       '#F5A623',
    amberSoft:   '#FFF3DC',
    amberDeep:   '#C07D0A',

    // Danger
    danger:      '#E53935',
    dangerSoft:  '#FEECEC',

    // UI Structure
    line:        '#ECEAF2',   // borders, dividers
    lineStrong:  '#D8D5E5',
    white:       '#FFFFFF',
    black:       '#000000',

    // Category accent palette
    grocery:     '#1BAD6E',   // fresh green
    food:        '#E84545',   // warm appetite red
    pharmacy:    '#0099CC',   // clinical teal
    shopping:    '#FF8C00',   // energy orange
    mobility:    '#1A1A1A',   // dark precision
    travel:      '#2563EB',   // sky blue
    finance:     '#4338CA',   // deep indigo
    productivity:'#7C3AED',   // purple digital

    // Back-compat aliases (used across existing screens — do not remove)
    surfaceMuted:'#F5F4F1',   // alias for surfaceAlt
    irisDark:    '#3D32C4',   // alias for irisDeep
    scrim:       'rgba(20,18,32,0.44)', // alias for overlay — used in ConnectedAccountsScreen
  },

  // ── Typography Scale ──────────────────────────────────────────────────
  type: {
    display: { fontSize: 34, fontWeight: '800' as const, letterSpacing: -0.8, lineHeight: 40 },
    h1:      { fontSize: 26, fontWeight: '700' as const, letterSpacing: -0.4, lineHeight: 32 },
    h2:      { fontSize: 20, fontWeight: '700' as const, letterSpacing: -0.2, lineHeight: 26 },
    h3:      { fontSize: 16, fontWeight: '600' as const, letterSpacing: -0.1, lineHeight: 22 },
    label:   { fontSize: 13, fontWeight: '600' as const, letterSpacing: 0.2,  lineHeight: 18 },
    body:    { fontSize: 15, fontWeight: '400' as const, letterSpacing: 0,    lineHeight: 22 },
    bodySmall:{ fontSize:13, fontWeight: '400' as const, letterSpacing: 0,    lineHeight: 19 },
    caption: { fontSize: 11, fontWeight: '500' as const, letterSpacing: 0.3,  lineHeight: 15 },
    micro:   { fontSize: 10, fontWeight: '600' as const, letterSpacing: 0.6,  lineHeight: 13 },
    // Back-compat alias — many screens use tc.type.eyebrow
    eyebrow: { fontSize: 10, fontWeight: '700' as const, letterSpacing: 1.0,  lineHeight: 13, textTransform: 'uppercase' as const },
    // Price typography — deliberate and beautiful
    priceHero:{ fontSize: 32, fontWeight: '800' as const, letterSpacing: -1.0, lineHeight: 36 },
    priceMain:{ fontSize: 22, fontWeight: '700' as const, letterSpacing: -0.5, lineHeight: 26 },
    priceSub: { fontSize: 16, fontWeight: '600' as const, letterSpacing: -0.2, lineHeight: 20 },
    // Back-compat: some screens use tc.type.price
    price:    { fontSize: 22, fontWeight: '700' as const, letterSpacing: -0.5, lineHeight: 26 },
  },

  // ── Spacing Grid (4pt base) ───────────────────────────────────────────
  space: {
    xxs:  2,
    xs:   4,
    sm:   8,
    md:   12,
    base: 16,
    lg:   20,
    xl:   24,
    xxl:  32,
    xxxl: 40,
    huge: 48,
    hero: 64,
  },

  // ── Border Radius ─────────────────────────────────────────────────────
  radius: {
    xs:   6,
    sm:   10,
    md:   14,
    lg:   18,
    xl:   24,
    xxl:  32,
    pill: 999,
    card: 20,
    hero: 28,
  },

  // ── Shadows (premium soft depth) ──────────────────────────────────────
  shadow: {
    none: {},
    xs: Platform.select({
      ios: { shadowColor: '#1A0F3C', shadowOpacity: 0.06, shadowRadius: 4, shadowOffset: { width: 0, height: 1 } },
      android: { elevation: 1 },
      default: {},
    }) ?? {},
    sm: Platform.select({
      ios: { shadowColor: '#1A0F3C', shadowOpacity: 0.08, shadowRadius: 8, shadowOffset: { width: 0, height: 2 } },
      android: { elevation: 3 },
      default: {},
    }) ?? {},
    md: Platform.select({
      ios: { shadowColor: '#1A0F3C', shadowOpacity: 0.10, shadowRadius: 16, shadowOffset: { width: 0, height: 4 } },
      android: { elevation: 6 },
      default: {},
    }) ?? {},
    lg: Platform.select({
      ios: { shadowColor: '#312471', shadowOpacity: 0.13, shadowRadius: 24, shadowOffset: { width: 0, height: 8 } },
      android: { elevation: 10 },
      default: {},
    }) ?? {},
    rail: Platform.select({
      ios: { shadowColor: '#312471', shadowOpacity: 0.15, shadowRadius: 20, shadowOffset: { width: 0, height: 8 } },
      android: { elevation: 9 },
      default: {},
    }) ?? {},
    iris: Platform.select({
      ios: { shadowColor: '#5B4FE9', shadowOpacity: 0.28, shadowRadius: 16, shadowOffset: { width: 0, height: 6 } },
      android: { elevation: 8 },
      default: {},
    }) ?? {},
    winner: Platform.select({
      ios: { shadowColor: '#0DAF8A', shadowOpacity: 0.22, shadowRadius: 20, shadowOffset: { width: 0, height: 6 } },
      android: { elevation: 10 },
      default: {},
    }) ?? {},
    // Back-compat: ExploreHub uses tc.shadow.card
    card: Platform.select({
      ios: { shadowColor: '#1A0F3C', shadowOpacity: 0.10, shadowRadius: 16, shadowOffset: { width: 0, height: 4 } },
      android: { elevation: 6 },
      default: {},
    }) ?? {},
  },

  // ── Icon Sizes ────────────────────────────────────────────────────────
  icon: { xs: 12, sm: 16, md: 20, lg: 24, xl: 32 },

  // ── Motion (milliseconds) ─────────────────────────────────────────────
  motion: {
    instant:    80,
    quick:     160,
    standard:  240,
    deliberate:360,
    // Spring configs for Animated/Reanimated
    spring: {
      snappy:  { damping: 18, stiffness: 280, mass: 1 },
      smooth:  { damping: 22, stiffness: 200, mass: 1 },
      bouncy:  { damping: 14, stiffness: 320, mass: 0.8 },
    },
  },

  // ── Component sizing constants ────────────────────────────────────────
  size: {
    navRail:      66,
    navRailRadius:24,
    buttonHeight: 52,
    buttonSmall:  40,
    chipHeight:   34,
    avatarSm:     32,
    avatarMd:     44,
    providerLogo: 40,
    cardRadius:   20,
    heroRadius:   28,
    orbSize:      52,
    inputHeight:  52,
  },
} as const;

// Back-compat alias — keep `tc` working so existing screens don't break
export const tc = TC;

// ── Currency formatter ────────────────────────────────────────────────────
export const formatCurrency = (value: number | null | undefined, currency = 'INR'): string => {
  if (value === null || value === undefined || !Number.isFinite(value)) return '—';
  // Beautiful Indian rupee formatting: ₹1,249  ₹12,450
  try {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency,
      maximumFractionDigits: 0, // no decimals for consumer prices
      minimumFractionDigits: 0,
    }).format(value);
  } catch {
    return `₹${Math.round(value).toLocaleString('en-IN')}`;
  }
};

// Format with decimals (for totals where precision matters)
export const formatCurrencyPrecise = (value: number | null | undefined): string => {
  if (value === null || value === undefined || !Number.isFinite(value)) return '—';
  try {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 2,
      minimumFractionDigits: 0,
    }).format(value);
  } catch {
    return `₹${value.toFixed(2)}`;
  }
};

// ── Category theming helper ────────────────────────────────────────────────
export const getCategoryTheme = (categoryId: string): { accent: string; soft: string; icon: string } => {
  const map: Record<string, { accent: string; soft: string; icon: string }> = {
    grocery:     { accent: TC.color.grocery,     soft: '#E8F8F1', icon: 'shopping-bag' },
    food:        { accent: TC.color.food,         soft: '#FEEAEA', icon: 'coffee' },
    pharmacy:    { accent: TC.color.pharmacy,     soft: '#E3F4FB', icon: 'activity' },
    shopping:    { accent: TC.color.shopping,     soft: '#FFF3E0', icon: 'package' },
    mobility:    { accent: TC.color.mobility,     soft: '#F0F0F0', icon: 'navigation' },
    travel:      { accent: TC.color.travel,       soft: '#EBF2FF', icon: 'send' },
    finance:     { accent: TC.color.finance,      soft: '#EDEAFF', icon: 'credit-card' },
    productivity:{ accent: TC.color.productivity, soft: '#F3EEFF', icon: 'zap' },
    hotels:      { accent: '#9C27B0',             soft: '#F5E8FF', icon: 'home' },
    deals:       { accent: TC.color.amber,        soft: TC.color.amberSoft, icon: 'tag' },
  };
  return map[categoryId.toLowerCase()] ?? { accent: TC.color.iris, soft: TC.color.irisSoft, icon: 'grid' };
};
