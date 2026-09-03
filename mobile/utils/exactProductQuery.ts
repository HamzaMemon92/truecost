const SPEC_PATTERNS = [
  /\b\d+\s*(?:h|hr|hrs|hour|hours|mm|cm|mah|w|hz|khz)\b/gi,
  /\b(?:battery|driver|drivers|deep bass|eq modes?|dual pairing|bluetooth|wireless|headphones?|earphones?|earbuds?|neckband|tws)\b/gi,
  /\b(?:with|and|for|in|by|new|latest)\b/gi,
];

const MODEL_BOUNDARY_WORDS = new Set([
  'bluetooth', 'wireless', 'headphone', 'headphones', 'earphone', 'earphones',
  'earbud', 'earbuds', 'neckband', 'tws', 'with', 'battery', 'driver', 'deep',
  'bass', 'eq', 'modes', 'dual', 'pairing',
]);

function normalizeSpaces(value: string) {
  return value.replace(/[^\w\s]/g, ' ').replace(/\s+/g, ' ').trim();
}

export function buildExactProviderQuery(title: string, brand?: string) {
  return buildExactProviderQueries(title, brand)[0] || normalizeSpaces(title);
}

export function buildExactProviderQueries(title: string, brand?: string) {
  const raw = normalizeSpaces(title);
  const tokens = raw.split(' ').filter(Boolean);
  const modelTokens: string[] = [];
  for (const token of tokens) {
    if (modelTokens.length >= 6) break;
    if (MODEL_BOUNDARY_WORDS.has(token.toLowerCase())) {
      if (modelTokens.length >= 3) break;
      continue;
    }
    modelTokens.push(token);
  }
  const compact = modelTokens.join(' ');
  const stripped = SPEC_PATTERNS.reduce((value, pattern) => value.replace(pattern, ' '), raw);
  const strippedTokens = normalizeSpaces(stripped).split(' ').filter(Boolean);
  const fallback = strippedTokens.slice(0, 8).join(' ');
  const brandValue = brand?.trim();
  const brandPrefixedCompact = brandValue && compact && !compact.toLowerCase().includes(brandValue.toLowerCase())
    ? `${brandValue} ${compact}`
    : compact;
  const compactWithFamily = (() => {
    if (!compact) return '';
    const family = tokens.find(token => MODEL_BOUNDARY_WORDS.has(token.toLowerCase()));
    return family ? `${compact} ${family}` : compact;
  })();
  const originalShort = tokens.slice(0, 10).join(' ');
  const candidates = [
    brandPrefixedCompact,
    compactWithFamily,
    fallback,
    originalShort,
    raw,
  ].map(normalizeSpaces).filter(value => value.length >= 3);

  const seen = new Set<string>();
  return candidates.filter(value => {
    const key = value.toLowerCase();
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  }).slice(0, 4);
}
